from telebot import types
from telebot.async_telebot import AsyncTeleBot
from config import Config
from database import get_db
from models.User import User
from sqlalchemy.orm import Session
import logging
from urllib.parse import quote
import time


# Validate BOT_TOKEN before creating a real AsyncTeleBot. If missing or malformed,
# provide a minimal dummy object with the same public methods used by the app so
# importing modules (like main.py) won't crash during development.
def _create_bot():
    token = getattr(Config, "BOT_TOKEN", "")
    # telebot expects a token containing a colon
    if isinstance(token, str) and ":" in token and token.strip():
        return AsyncTeleBot(token)

    logging.warning("BOT_TOKEN is missing or invalid; using dummy bot. Set BOT_TOKEN to enable real Telegram bot.")

    # Dummy bot implementation with required async API surface
    class DummyBot:
        def message_handler(self, *args, **kwargs):
            def _decorator(fn):
                # no-op decorator that preserves function
                return fn
            return _decorator

        async def send_message(self, chat_id, text, **kwargs):
            logging.info("DummyBot.send_message called: chat_id=%s text=%s", chat_id, text)

        async def process_new_updates(self, updates):
            logging.info("DummyBot.process_new_updates called: %s", updates)

    return DummyBot()


bot = _create_bot()

# In-memory allowlist for recently approved guest joins to avoid kicking them on join
# Key: (group_id, user_id) -> expiry timestamp
ALLOWED_GUESTS = {}


def format_error_message(error: Exception, context: str, user_action: str = None) -> str:
    """Format a user-friendly error message with actionable steps.
    
    Args:
        error: The exception that occurred
        context: Brief description of what was being done (e.g., "uploading receipt")
        user_action: Optional - what the user should do next
    
    Returns:
        Formatted HTML error message
    """
    error_str = str(error).lower()
    
    # Database errors
    if "database" in error_str or "connection" in error_str or "operational" in error_str:
        return (
            f"❌ <b>Database Connection Error</b>\n\n"
            f"We couldn't connect to our database while {context}.\n\n"
            f"<b>What you can do:</b>\n"
            f"• Wait a moment and try again\n"
            f"• Check your internet connection\n"
            f"• Contact support if this persists\n\n"
            f"Error code: DB_CONNECTION\n"
            f"Reference: {str(error)[:60]}"
        )
    
    # Timeout errors
    elif "timeout" in error_str:
        return (
            f"⏱ <b>Request Timed Out</b>\n\n"
            f"The operation took too long while {context}.\n\n"
            f"<b>What you can do:</b>\n"
            f"• Wait a few seconds and try again\n"
            f"• Check your internet connection\n"
            f"• The service might be busy - please be patient\n\n"
            f"Error code: TIMEOUT"
        )
    
    # Permission/access errors
    elif "forbidden" in error_str or "access denied" in error_str or "permission" in error_str:
        return (
            f"🚫 <b>Permission Error</b>\n\n"
            f"Access was denied while {context}.\n\n"
            f"<b>What you can do:</b>\n"
            f"• Make sure you have the right permissions\n"
            f"• Try /start to refresh your registration\n"
            f"• Contact an admin if you should have access\n\n"
            f"Error code: PERMISSION_DENIED"
        )
    
    # Not found errors
    elif "not found" in error_str or "404" in error_str:
        return (
            f"🔍 <b>Not Found</b>\n\n"
            f"The requested resource was not found while {context}.\n\n"
            f"<b>What you can do:</b>\n"
            f"• Check if the trip/record still exists\n"
            f"• Try refreshing with /trips or /mystatus\n"
            f"• Contact support if you think this is wrong\n\n"
            f"Error code: NOT_FOUND"
        )
    
    # File/upload errors
    elif "file" in error_str or "upload" in error_str or "photo" in error_str:
        return (
            f"📎 <b>File Upload Error</b>\n\n"
            f"There was a problem with the file while {context}.\n\n"
            f"<b>What you can do:</b>\n"
            f"• Make sure the file is a valid image (JPG, PNG) or PDF\n"
            f"• Keep file size under 20MB\n"
            f"• Try compressing or re-taking the photo\n\n"
            f"Error code: FILE_ERROR"
        )
    
    # Constraint/duplicate errors
    elif "unique" in error_str or "duplicate" in error_str or "constraint" in error_str:
        return (
            f"⚠️ <b>Duplicate Entry</b>\n\n"
            f"This action cannot be completed because a similar entry already exists.\n\n"
            f"<b>What you can do:</b>\n"
            f"• Check if you're already registered with /mystatus\n"
            f"• Contact support if you need to update your info\n\n"
            f"Error code: DUPLICATE_ENTRY"
        )
    
    # Generic error with custom action
    else:
        msg = (
            f"❌ <b>Unexpected Error</b>\n\n"
            f"Something went wrong while {context}.\n\n"
        )
        
        if user_action:
            msg += f"<b>What you can do:</b>\n{user_action}\n\n"
        else:
            msg += (
                f"<b>What you can do:</b>\n"
                f"• Try again in a moment\n"
                f"• Contact support if the issue persists\n\n"
            )
        
        msg += (
            f"Error code: UNEXPECTED\n"
            f"Details: {str(error)[:80]}"
        )
        
        return msg


@bot.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    """Handle /start: ensure a User exists for the sender's telegram id.

    If the user already exists, send a welcome back message. Otherwise,
    create a new User record and greet them.
    
    Supports deep linking: /start agenda_TRIP_ID will open agenda directly.
    
    Only works in private chats.
    """
    # Ignore group messages
    if message.chat.type in ('group', 'supergroup'):
        return
    
    tg_id = message.from_user.id
    
    # Check for deep link parameters (e.g., /start agenda_1)
    start_param = None
    if message.text and len(message.text.split()) > 1:
        start_param = message.text.split()[1]
    
    logging.info("cmd.start from=%s chat=%s type=%s param=%s", tg_id, message.chat.id, message.chat.type, start_param)

    # get_db is a generator that yields a session; call it and get the session
    db_gen = get_db()
    db: Session = next(db_gen)
    try:
        user = db.query(User).filter(User.telegram_id == tg_id).first()
        
        # Handle deep link for agenda
        if start_param and start_param.startswith('agenda_'):
            from models.Trip import Trip, TripStatus
            try:
                trip_id = int(start_param.replace('agenda_', ''))
                trip = db.query(Trip).filter(Trip.id == trip_id, Trip.status == TripStatus.active).first()
                
                if trip:
                    # If user not registered, prompt registration first
                    if not user:
                        webapp_url = f"{Config.URL.rstrip('/')}/webapp/register"
                        keyboard = types.InlineKeyboardMarkup()
                        keyboard.add(
                            types.InlineKeyboardButton(
                                text="✨ Register with Google",
                                web_app=types.WebAppInfo(url=webapp_url)
                            )
                        )
                        await bot.send_message(
                            message.chat.id,
                            f"✈️ <b>Welcome to Travel Bot!</b>\n\n"
                            f"You're trying to view the agenda for <b>{trip.name}</b>. 📅\n\n"
                            f"Please register first to access trip information:\n\n"
                            f"Tap the button below to get started! 👇",
                            parse_mode='HTML',
                            reply_markup=keyboard
                        )
                        return
                    
                    # User is registered - show agenda
                    keyboard = types.InlineKeyboardMarkup()
                    keyboard.add(
                        types.InlineKeyboardButton(
                            text=f"📅 Open {trip.name} Agenda",
                            web_app=types.WebAppInfo(url=f"{Config.URL.rstrip('/')}/webapp/agenda?trip_id={trip.id}")
                        )
                    )
                    await bot.send_message(
                        message.chat.id,
                        f"📅 <b>Trip Agenda</b>\n\n"
                        f"View the detailed schedule for <b>{trip.name}</b>:\n\n"
                        f"Tap the button below to open the agenda! 👇",
                        parse_mode='HTML',
                        reply_markup=keyboard
                    )
                    logging.info("deeplink.agenda user=%s trip_id=%s", tg_id, trip_id)
                    return
            except (ValueError, AttributeError):
                # Invalid trip_id format - continue with normal flow
                pass
        
        if user:
            # Returning user - show friendly greeting with quick actions
            keyboard = types.InlineKeyboardMarkup()
            keyboard.row(
                types.InlineKeyboardButton(text="🗺 Browse Trips", callback_data="menu:trips"),
                types.InlineKeyboardButton(text="🧾 My Status", callback_data="menu:mystatus")
            )
            keyboard.row(
                types.InlineKeyboardButton(text="📊 View Stats", callback_data="menu:stats"),
                types.InlineKeyboardButton(text="📅 Trip Agenda", callback_data="menu:agenda")
            )
            keyboard.row(
                types.InlineKeyboardButton(text="❓ Help", callback_data="menu:help")
            )
            
            msg = (
                f"👋 <b>Welcome back, {message.from_user.first_name}!</b>\n\n"
                f"Ready to plan your next adventure? Here's what you can do:\n\n"
                f"🗺 Browse available trips\n"
                f"🧾 Check your registration status\n"
                f"📊 View trip statistics\n"
                f"📅 View trip schedules\n"
                f"❓ Get help and tips\n\n"
                f"Choose an option below or type /menu anytime!"
            )
            await bot.send_message(message.chat.id, msg, parse_mode='HTML', reply_markup=keyboard)
            logging.info("user.exists tg_id=%s", tg_id)
        else:
            # New user - registration flow
            webapp_url = f"{Config.URL.rstrip('/')}/webapp/register"
            keyboard = types.InlineKeyboardMarkup()
            webapp_button = types.InlineKeyboardButton(
                text="✨ Register with Google",
                web_app=types.WebAppInfo(url=webapp_url)
            )
            keyboard.add(webapp_button)

            msg = (
                f"✈️ <b>Welcome to Travel Bot, {message.from_user.first_name}!</b>\n\n"
                f"Plan and join group trips with your friends! 🌍\n\n"
                f"<b>To get started:</b>\n"
                f"• Tap the button below\n"
                f"• Sign in with your <b>@newuu.uz</b> student account\n"
                f"• That's it! You'll be ready to browse trips\n\n"
                f"🔒 <b>Secure:</b> We only access your basic profile info"
            )
            await bot.send_message(message.chat.id, msg, parse_mode='HTML', reply_markup=keyboard)
            logging.info("webapp.register prompt sent tg_id=%s", tg_id)
    except Exception as e:
        # best-effort: rollback and inform user
        logging.error(f"Error in /start handler for user {tg_id}: {e}", exc_info=True)
        try:
            db.rollback()
        except Exception:
            pass
        
        # Provide specific error message based on error type
        error_msg = "⚠️ <b>Oops! Something went wrong</b>\n\n"
        
        if "database" in str(e).lower() or "connection" in str(e).lower():
            error_msg += (
                "We're experiencing database connection issues. This is usually temporary.\n\n"
                "<b>What you can do:</b>\n"
                "• Wait a few moments and try /start again\n"
                "• If it persists, our team has been notified\n\n"
                "Error code: DB_CONNECTION_ERROR"
            )
        elif "timeout" in str(e).lower():
            error_msg += (
                "The request timed out. The service might be busy.\n\n"
                "<b>What you can do:</b>\n"
                "• Try again in a few seconds\n"
                "• Check your internet connection\n\n"
                "Error code: TIMEOUT_ERROR"
            )
        else:
            error_msg += (
                "An unexpected error occurred during registration.\n\n"
                "<b>What you can do:</b>\n"
                "• Try /start again\n"
                "• If the problem persists, contact support\n\n"
                f"Error code: UNKNOWN_ERROR\n"
                f"Reference: {str(e)[:100]}"
            )
        
        await bot.send_message(message.chat.id, error_msg, parse_mode='HTML')
    finally:
        # close the generator properly
        try:
            next(db_gen)
        except StopIteration:
            pass


@bot.message_handler(content_types=['new_chat_members'])
async def new_group_member_handler(message: types.Message):
    """Handle new members in groups.

    - If the bot was added: guide admins to grant permissions and notify app admins.
    - For other new users: allow only paid participants to stay. Others are removed and guided to use guest link.
    """
    bot_id = (await bot.get_me()).id
    new_members = message.new_chat_members or []
    group_id = message.chat.id
    group_name = message.chat.title

    # Case 1: Bot added -> admin setup guidance
    if any(member.id == bot_id for member in new_members):
        keyboard = types.InlineKeyboardMarkup()
        check_button = types.InlineKeyboardButton(
            text="✅ Verify Admin Status",
            callback_data=f"check_admin:{group_id}"
        )
        keyboard.add(check_button)
        msg = (
            f"👋 <b>Hello, {group_name}!</b>\n\n"
            f"Thanks for adding me! I'm your travel planning assistant. 🌍\n\n"
            f"<b>⚙️ Quick Setup Required:</b>\n"
            f"To manage trips and members, I need admin permissions:\n\n"
            f"<b>How to set up:</b>\n"
            f"1️⃣ Tap the group name at the top\n"
            f"2️⃣ Go to 'Administrators'\n"
            f"3️⃣ Select my name and grant these permissions:\n"
            f"   ✓ Delete messages\n"
            f"   ✓ Pin messages\n"
            f"   ✓ Invite users via link\n\n"
            f"4️⃣ Tap 'Verify Admin Status' below when ready!\n\n"
            f"💡 <i>This helps me manage trip participants and keep the group organized.</i>"
        )
        await bot.send_message(group_id, msg, parse_mode="HTML", reply_markup=keyboard)
        logging.info("group.bot_added group_id=%s", group_id)
        return

    # Case 2: Regular users joined -> ensure only participants can join with participant link
    from models.Trip import Trip, TripStatus
    from models.TripMember import TripMember, PaymentStatus

    db_gen = get_db()
    db: Session = next(db_gen)
    try:
        trip = db.query(Trip).filter(Trip.group_id == group_id, Trip.status == TripStatus.active).first()
        if not trip:
            return
        # Cleanup expired allowlist entries
        now = time.time()
        to_delete = [k for k, exp in ALLOWED_GUESTS.items() if exp < now]
        for k in to_delete:
            ALLOWED_GUESTS.pop(k, None)

        for member in new_members:
            if member.is_bot:
                continue
            # If this user was just approved via guest join request, allow them
            if ALLOWED_GUESTS.get((group_id, member.id)):
                continue
            # Lookup user and trip membership
            user = db.query(User).filter(User.telegram_id == member.id).first()
            is_participant = False
            if user:
                tm = db.query(TripMember).filter(TripMember.user_id == user.id, TripMember.trip_id == trip.id).first()
                if tm and tm.payment_status in (PaymentStatus.half_paid, PaymentStatus.full_paid):
                    is_participant = True

            if not is_participant:
                # Kick and DM guidance
                try:
                    await bot.ban_chat_member(group_id, member.id)
                    await bot.unban_chat_member(group_id, member.id, only_if_banned=True)
                except Exception as e:
                    logging.error(f"Failed to remove non-participant {member.id} from group {group_id}: {e}")

                try:
                    # Simply don't include guest link - they were just kicked!
                    msg = (
                        f"⛔ <b>Access Denied</b>\n\n"
                        f"Sorry! You can't join <b>{trip.name}</b> with the participant link.\n\n"
                        f"<b>Why?</b> That link is reserved for paid participants only.\n\n"
                        f"<b>Next steps:</b>\n"
                        f"• Register for this trip via /trips\n"
                        f"• Make at least 50% payment\n"
                        f"• Get the participant invite link\n\n"
                        f"Need help? Contact the trip organizer."
                    )
                    await bot.send_message(member.id, msg, parse_mode='HTML', disable_web_page_preview=True)
                except Exception as e:
                    logging.info(f"Could not DM removed user {member.id}: {e}")
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


# Handle guest join requests (created by guest invite link with creates_join_request=True)
@bot.chat_join_request_handler()
async def handle_chat_join_request(request: types.ChatJoinRequest):
    from models.Trip import Trip, TripStatus
    # Approve guest join requests for groups with an active trip
    group_id = request.chat.id
    user_id = request.from_user.id
    db_gen = get_db()
    db: Session = next(db_gen)
    try:
        trip = db.query(Trip).filter(Trip.group_id == group_id, Trip.status == TripStatus.active).first()
        if not trip:
            return
        try:
            await bot.approve_chat_join_request(group_id, user_id)
            # Allow this user not to be kicked when new_chat_members fires shortly after approval
            ALLOWED_GUESTS[(group_id, user_id)] = time.time() + 300  # 5 minutes grace
            logging.info("group.join_request approved group_id=%s user_id=%s", group_id, user_id)
            # Optionally send a DM to the user
            try:
                guest_msg = (
                    f"✅ <b>Request Approved!</b>\n\n"
                    f"Welcome to <b>{trip.name}</b>! 🎉\n\n"
                    f"You've been approved as a guest. Feel free to check out the trip details and chat with other members.\n\n"
                    f"💡 <b>Want to become a full participant?</b>\n"
                    f"Use /trips to register and reserve your seat!"
                )
                await bot.send_message(user_id, guest_msg, parse_mode='HTML')
            except Exception:
                pass
        except Exception as e:
            logging.error(f"Failed to approve join request for {user_id} in {group_id}: {e}")
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


@bot.callback_query_handler(func=lambda call: call.data.startswith('check_admin:'))
async def check_admin_status_callback(call: types.CallbackQuery):
    """Handle the check admin status button press.
    
    Verify if bot has admin rights in the group.
    If yes, notify bot admins to create a trip for this group.
    """
    try:
        # Extract group_id from callback data
        group_id = int(call.data.split(':')[1])
        
        # Get bot's member status in the group
        bot_member = await bot.get_chat_member(group_id, (await bot.get_me()).id)
        
        # Check if bot is admin
        is_admin = bot_member.status in ['administrator', 'creator']
        
        if is_admin:
            # Answer the callback with success
            await bot.answer_callback_query(
                call.id,
                text="✅ Great! I'm now an admin.",
                show_alert=False
            )
            
            # Update the message to show success
            group_info = await bot.get_chat(group_id)
            group_name = group_info.title
            
            success_msg = (
                f"✅ <b>Perfect! Setup Complete</b>\n\n"
                f"I'm now an administrator of <b>{group_name}</b>! 🎉\n\n"
                f"<b>What's next?</b>\n"
                f"• Trip organizers have been notified\n"
                f"• They'll create a trip for this group soon\n"
                f"• You'll be able to invite members and track registrations\n\n"
                f"Sit tight! Your trip will be ready shortly. 🚀"
            )
            
            await bot.edit_message_text(
                success_msg,
                group_id,
                call.message.message_id,
                parse_mode="HTML"
            )
            
            # Notify all bot admins to create a trip
            for admin_id in Config.ADMINS:
                try:
                    admin_keyboard = types.InlineKeyboardMarkup()
                    
                    # Create Web App button for trip creation (URL-encode group_name)
                    encoded_group_name = quote(group_name)
                    create_trip_button = types.InlineKeyboardButton(
                        text="📝 Create Trip",
                        web_app=types.WebAppInfo(
                            url=f"{Config.URL}/webapp/create-trip?group_id={group_id}&group_name={encoded_group_name}"
                        )
                    )
                    admin_keyboard.add(create_trip_button)
                    
                    admin_msg = (
                        f"🔔 <b>New Group Setup Complete!</b>\n\n"
                        f"📋 <b>Group Name:</b> {group_name}\n"
                        f"🆔 <b>Group ID:</b> <code>{group_id}</code>\n"
                        f"✅ <b>Status:</b> Bot verified as admin\n\n"
                        f"<b>Action Required:</b>\n"
                        f"Create a new trip for this group to activate trip management features.\n\n"
                        f"Tap the button below to get started! 👇"
                    )
                    
                    await bot.send_message(
                        admin_id,
                        admin_msg,
                        parse_mode="HTML",
                        reply_markup=admin_keyboard
                    )
                except Exception as e:
                    logging.error(f"Failed to notify admin {admin_id}: {e}")
        
        else:
            # Bot is not admin yet
            await bot.answer_callback_query(
                call.id,
                text="❌ I'm not an admin yet. Please make me an admin first.",
                show_alert=True
            )
    
    except Exception as e:
        logging.error(f"Error checking admin status for group {call.data}: {e}", exc_info=True)
        
        error_detail = "❌ <b>Admin Check Failed</b>\n\n"
        
        if "chat not found" in str(e).lower() or "forbidden" in str(e).lower():
            error_detail += (
                "I don't have access to this group anymore.\n\n"
                "<b>Possible reasons:</b>\n"
                "• Bot was removed from the group\n"
                "• Group was deleted\n"
                "• Bot lost permissions\n\n"
                "Error code: NO_GROUP_ACCESS"
            )
        elif "timeout" in str(e).lower():
            error_detail += (
                "Request timed out. Telegram might be slow.\n\n"
                "Please wait a moment and try the button again.\n\n"
                "Error code: TIMEOUT"
            )
        else:
            error_detail += (
                "An unexpected error occurred while checking admin status.\n\n"
                "Please try again in a moment.\n\n"
                f"Error code: CHECK_ADMIN_ERROR\n"
                f"Details: {str(e)[:80]}"
            )
        
        try:
            await bot.send_message(
                call.message.chat.id,
                error_detail,
                parse_mode='HTML'
            )
        except:
            pass
        
        await bot.answer_callback_query(
            call.id,
            text="❌ Error - check message for details",
            show_alert=True
        )


@bot.message_handler(commands=['trips'])
async def show_trips_handler(message: types.Message):
    """Show all active trips to registered users. Only works in private chats."""
    from models.Trip import Trip, TripStatus
    
    # Ignore group messages
    if message.chat.type in ('group', 'supergroup'):
        return
    
    tg_id = message.from_user.id
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        # Check if user is registered
        user = db.query(User).filter(User.telegram_id == tg_id).first()
        if not user:
            keyboard = types.InlineKeyboardMarkup()
            webapp_url = f"{Config.URL.rstrip('/')}/webapp/register"
            keyboard.add(
                types.InlineKeyboardButton(
                    text="✨ Register Now",
                    web_app=types.WebAppInfo(url=webapp_url)
                )
            )
            await bot.send_message(
                message.chat.id,
                "⚠️ <b>Registration Required</b>\n\n"
                "You need to register before browsing trips.\n\n"
                "Tap the button below to get started! 👇",
                parse_mode='HTML',
                reply_markup=keyboard
            )
            return
        
        # Get active trips
        active_trips = db.query(Trip).filter(Trip.status == TripStatus.active).all()
        
        if not active_trips:
            await bot.send_message(
                message.chat.id,
                "📭 <b>No Active Trips</b>\n\n"
                "There are no trips available right now. Check back soon! 🌍\n\n"
                "We'll notify you when new trips are added.",
                parse_mode='HTML'
            )
            return
        logging.info("cmd.trips from=%s count=%s", message.from_user.id, len(active_trips))
        
        # Create keyboard with trip buttons
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for trip in active_trips:
            keyboard.add(types.KeyboardButton(f"🎫 {trip.name}"))
        keyboard.add(types.KeyboardButton("❌ Cancel"))
        
        trip_count = len(active_trips)
        await bot.send_message(
            message.chat.id,
            f"🌍 <b>Available Trips</b> ({trip_count})\n\n"
            f"Select a trip below to:\n"
            f"• View details and terms\n"
            f"• Check availability\n"
            f"• Register and reserve your seat\n\n"
            f"Tap any trip to get started! 👇",
            parse_mode='HTML',
            reply_markup=keyboard
        )
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


@bot.message_handler(func=lambda message: message.text and message.text.startswith('🎫 '))
async def trip_selection_handler(message: types.Message):
    """Handle trip selection from keyboard. Only works in private chats."""
    from models.Trip import Trip, TripStatus
    from models.TripMember import TripMember, PaymentStatus
    
    # Ignore group messages
    if message.chat.type in ('group', 'supergroup'):
        return
    
    trip_name = message.text.replace('🎫 ', '').strip()
    tg_id = message.from_user.id
    
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        user = db.query(User).filter(User.telegram_id == tg_id).first()
        if not user:
            return
        
        trip = db.query(Trip).filter(
            Trip.name == trip_name,
            Trip.status == TripStatus.active
        ).first()
        
        if not trip:
            await bot.send_message(message.chat.id, "❌ Trip not found.")
            return
        
        # Check if already registered
        existing_member = db.query(TripMember).filter(
            TripMember.user_id == user.id,
            TripMember.trip_id == trip.id
        ).first()
        
        if existing_member:
            status_emoji = {
                PaymentStatus.not_paid: '⏳',
                PaymentStatus.half_paid: '🟡',
                PaymentStatus.full_paid: '🟢'
            }
            status_text = {
                PaymentStatus.not_paid: 'Awaiting Payment',
                PaymentStatus.half_paid: '50% Paid - Seat Reserved',
                PaymentStatus.full_paid: 'Fully Paid'
            }
            
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(
                types.InlineKeyboardButton(
                    text="📊 View Trip Stats",
                    web_app=types.WebAppInfo(url=f"{Config.URL.rstrip('/')}/webapp/trip-stats?trip_id={trip.id}")
                )
            )
            
            await bot.send_message(
                message.chat.id,
                f"✅ <b>Already Registered</b>\n\n"
                f"You're already signed up for <b>{trip.name}</b>!\n\n"
                f"{status_emoji.get(existing_member.payment_status, '•')} <b>Status:</b> {status_text.get(existing_member.payment_status, 'Unknown')}\n\n"
                f"Use /mystatus to see your full registration details.",
                parse_mode='HTML',
                reply_markup=keyboard
            )
            return
        
        # Show agreement + stats button
        if trip.agreement_text:
            keyboard = types.InlineKeyboardMarkup()
            confirm_btn = types.InlineKeyboardButton(
                text="✅ I Agree & Register",
                callback_data=f"confirm_trip:{trip.id}"
            )
            cancel_btn = types.InlineKeyboardButton(
                text="❌ Cancel",
                callback_data="cancel_registration"
            )
            stats_btn = types.InlineKeyboardButton(
                text="📊 View Stats",
                web_app=types.WebAppInfo(url=f"{Config.URL.rstrip('/')}/webapp/trip-stats?trip_id={trip.id}")
            )
            keyboard.row(confirm_btn, cancel_btn)
            keyboard.add(stats_btn)
            
            agreement_msg = (
                f"📋 <b>{trip.name}</b>\n\n"
                f"💰 <b>Price:</b> {trip.price:,} UZS\n\n"
                f"<b>Terms & Agreement:</b>\n{trip.agreement_text}\n\n"
            )
            
            if trip.card_info:
                agreement_msg += f"💳 <b>Payment Info:</b> {trip.card_info}\n\n"
            
            half_price = trip.price // 2
            agreement_msg += f"⚠️ <b>Important:</b> You must make at least <b>50% payment ({half_price:,} UZS)</b> to reserve your seat.\n\n"
            agreement_msg += "Please read the terms carefully and click confirm to proceed."
            
            await bot.send_message(
                message.chat.id,
                agreement_msg,
                parse_mode='HTML',
                reply_markup=keyboard
            )
        else:
            # No agreement, register directly
            keyboard = types.InlineKeyboardMarkup()
            confirm_btn = types.InlineKeyboardButton(
                text="✅ Register",
                callback_data=f"confirm_trip:{trip.id}"
            )
            stats_btn = types.InlineKeyboardButton(
                text="📊 View Stats",
                web_app=types.WebAppInfo(url=f"{Config.URL.rstrip('/')}/webapp/trip-stats?trip_id={trip.id}")
            )
            keyboard.add(confirm_btn)
            keyboard.add(stats_btn)
            
            await bot.send_message(
                message.chat.id,
                f"📋 <b>{trip.name}</b>\n\nClick to register:",
                parse_mode='HTML',
                reply_markup=keyboard
            )
        logging.info("trip.select user=%s trip_id=%s", message.from_user.id, trip.id)
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_trip:'))
async def confirm_trip_registration(call: types.CallbackQuery):
    """Handle trip registration confirmation."""
    from models.Trip import Trip
    from models.TripMember import TripMember, PaymentStatus
    
    trip_id = int(call.data.split(':')[1])
    tg_id = call.from_user.id
    
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        user = db.query(User).filter(User.telegram_id == tg_id).first()
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        
        if not user or not trip:
            await bot.answer_callback_query(call.id, "❌ Error: User or trip not found.")
            return
        
        # Check participant limit if specified (count half_paid + full_paid)
        if trip.participant_limit is not None:
            from models.TripMember import TripMember as TM, PaymentStatus as PS
            paid_count = db.query(TM).filter(
                TM.trip_id == trip.id,
                TM.payment_status.in_([PS.half_paid, PS.full_paid])
            ).count()
            if paid_count >= trip.participant_limit:
                await bot.answer_callback_query(call.id, "⚠️ This trip is full.", show_alert=True)
                return
        
        # Check if user is already registered for this trip
        existing_member = db.query(TripMember).filter(
            TripMember.user_id == user.id,
            TripMember.trip_id == trip.id
        ).first()
        
        if existing_member:
            await bot.answer_callback_query(call.id, "⚠️ You're already registered for this trip!", show_alert=True)
            return
        
        # Create trip member
        new_member = TripMember(
            user_id=user.id,
            trip_id=trip.id,
            payment_status=PaymentStatus.not_paid
        )
        db.add(new_member)
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            # Check if it's a unique constraint violation
            if "unique" in str(e).lower() or "duplicate" in str(e).lower():
                await bot.answer_callback_query(call.id, "⚠️ You're already registered for this trip!", show_alert=True)
                return
            raise
        
        # Remove keyboard
        await bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=None
        )
        
        # Ask for payment receipt
        half_price = trip.price // 2
        msg = (
            f"🎉 <b>Registration Successful!</b>\n\n"
            f"Welcome to <b>{trip.name}</b>! You're one step away from securing your spot.\n\n"
            f"💰 <b>Trip Price:</b> {trip.price:,} UZS\n"
            f"💵 <b>Minimum Payment (50%):</b> {half_price:,} UZS\n\n"
            f"<b>📋 Next Steps:</b>\n\n"
            f"<b>1️⃣ Make Payment (50% minimum)</b>\n"
        )
        
        if trip.card_info:
            msg += f"   💳 {trip.card_info}\n\n"
        else:
            msg += "   💳 Contact organizer for payment details\n\n"
        
        msg += (
            f"<b>2️⃣ Send Receipt</b>\n"
            f"   📸 Send your payment receipt here (photo or PDF)\n"
            f"   ⚡ We'll review it ASAP\n\n"
            f"<b>3️⃣ Get Confirmed</b>\n"
            f"   ✅ Once approved, your seat is reserved!\n"
            f"   🔗 You'll get the group invite link\n\n"
            f"⏰ <b>Don't wait!</b> Seats fill up quickly. Send your receipt now to reserve your spot!"
        )
        
        await bot.send_message(call.message.chat.id, msg, parse_mode='HTML')
        await bot.answer_callback_query(call.id, "✅ Registered successfully!")
        logging.info("trip.registered user=%s trip_id=%s", tg_id, trip.id)
        
    except Exception as e:
        logging.error(f"Error confirming trip registration for user {tg_id}, trip {trip_id}: {e}", exc_info=True)
        
        # Provide detailed error message
        error_detail = "❌ <b>Registration Failed</b>\n\n"
        
        if "database" in str(e).lower() or "connection" in str(e).lower():
            error_detail += (
                "Database connection error. Please try again in a moment.\n\n"
                "Error code: DB_ERROR"
            )
        elif "constraint" in str(e).lower() or "duplicate" in str(e).lower():
            error_detail += (
                "You may already be registered for this trip.\n\n"
                "Use /mystatus to check your current registrations.\n\n"
                "Error code: DUPLICATE_REGISTRATION"
            )
        else:
            error_detail += (
                "An unexpected error occurred.\n\n"
                "<b>What you can do:</b>\n"
                "• Try registering again\n"
                "• Check if you're already registered with /mystatus\n"
                "• Contact support if the issue persists\n\n"
                f"Error code: REGISTRATION_ERROR\n"
                f"Details: {str(e)[:80]}"
            )
        
        await bot.send_message(call.message.chat.id, error_detail, parse_mode='HTML')
        await bot.answer_callback_query(call.id, "❌ Registration error - check message for details")
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


@bot.message_handler(commands=['mystatus'])
async def my_status_handler(message: types.Message):
    """Show the user's latest registration and payment status. Only works in private chats."""
    from models.TripMember import TripMember, PaymentStatus
    from models.Trip import Trip
    
    # Ignore group messages
    if message.chat.type in ('group', 'supergroup'):
        return
    
    tg_id = message.from_user.id
    db_gen = get_db()
    db: Session = next(db_gen)
    try:
        user = db.query(User).filter(User.telegram_id == tg_id).first()
        if not user:
            await bot.send_message(message.chat.id, "❌ You are not registered. Use /start to register.")
            return
        tm = db.query(TripMember).filter(TripMember.user_id == user.id).order_by(TripMember.joined_at.desc()).first()
        if not tm:
            await bot.send_message(message.chat.id, "ℹ️ You are not registered for any trip yet. Use /trips to join one.")
            return
        trip = db.query(Trip).filter(Trip.id == tm.trip_id).first()
        status_map = {
            PaymentStatus.not_paid: 'Not Paid',
            PaymentStatus.half_paid: '50% Paid',
            PaymentStatus.full_paid: 'Fully Paid',
        }
        status_text = status_map.get(tm.payment_status, str(tm.payment_status))
        receipt_info = 'Yes' if tm.payment_receipt_file_id else 'No'
        msg = (
            f"🧾 <b>Your Status</b>\n\n"
            f"🎭 <b>Trip:</b> {trip.name}\n"
            f"💳 <b>Payment Status:</b> {status_text}\n"
            f"📎 <b>Receipt Uploaded:</b> {receipt_info}"
        )
        await bot.send_message(message.chat.id, msg, parse_mode='HTML')
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


@bot.callback_query_handler(func=lambda call: call.data == 'cancel_registration')
async def cancel_registration_handler(call: types.CallbackQuery):
    """Handle registration cancellation."""
    await bot.edit_message_text(
        "❌ Registration cancelled.",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id
    )
    await bot.answer_callback_query(call.id)


@bot.message_handler(content_types=['photo', 'document'])
async def payment_receipt_handler(message: types.Message):
    """Handle payment receipt uploads (only in private chats)."""
    from models.TripMember import TripMember, PaymentStatus
    from models.Trip import Trip
    
    # Ignore photos/files sent in groups - only process in private chats
    if message.chat.type in ('group', 'supergroup'):
        return
    
    tg_id = message.from_user.id
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        user = db.query(User).filter(User.telegram_id == tg_id).first()
        if not user:
            return
        
        # Find the most recent trip member with not_paid status
        trip_member = db.query(TripMember).filter(
            TripMember.user_id == user.id,
            TripMember.payment_status == PaymentStatus.not_paid
        ).order_by(TripMember.joined_at.desc()).first()
        
        if not trip_member:
            await bot.send_message(
                message.chat.id,
                "❌ No pending payment found. Please register for a trip first using /trips"
            )
            return
        
        trip = db.query(Trip).filter(Trip.id == trip_member.trip_id).first()
        
        # Get file_id
        if message.content_type == 'photo':
            file_id = message.photo[-1].file_id
        else:
            file_id = message.document.file_id
        
        # Save file_id and automatically mark as half_paid
        trip_member.payment_receipt_file_id = file_id
        trip_member.payment_status = PaymentStatus.half_paid
        
        # Commit and then double-check capacity to prevent race conditions
        db.commit()
        
        # Re-check if trip is now over capacity (race condition protection)
        if trip.participant_limit is not None:
            paid_count = db.query(TripMember).filter(
                TripMember.trip_id == trip.id,
                TripMember.payment_status.in_([PaymentStatus.half_paid, PaymentStatus.full_paid])
            ).count()
            
            # If we exceeded capacity, rollback this user's payment
            if paid_count > trip.participant_limit:
                trip_member.payment_status = PaymentStatus.not_paid
                trip_member.payment_receipt_file_id = None
                db.commit()
                
                await bot.send_message(
                    message.chat.id,
                    "😔 <b>Trip Just Filled Up</b>\n\n"
                    f"Unfortunately, all seats for <b>{trip.name}</b> were just taken by other users.\n\n"
                    f"📊 <b>Capacity:</b> {trip.participant_limit}/{trip.participant_limit} seats taken\n\n"
                    f"⚠️ <b>IMPORTANT: Please DO NOT make payment for this trip!</b>\n\n"
                    f"<b>What you can do:</b>\n"
                    f"• Wait for a cancellation (you'll be notified if a spot opens)\n"
                    f"• Check out other available trips using /trips\n"
                    f"• Contact the organizer to be added to the waitlist\n\n"
                    f"Sorry for the inconvenience! 🙏",
                    parse_mode='HTML'
                )
                return
        
        # Check if trip just became full and notify remaining not_paid members
        if trip.participant_limit is not None:
            paid_count = db.query(TripMember).filter(
                TripMember.trip_id == trip.id,
                TripMember.payment_status.in_([PaymentStatus.half_paid, PaymentStatus.full_paid])
            ).count()
            
            if paid_count >= trip.participant_limit:
                # Notify all not_paid members that the trip is full
                not_paid_members = db.query(TripMember).filter(
                    TripMember.trip_id == trip.id,
                    TripMember.payment_status == PaymentStatus.not_paid
                ).all()
                
                for member in not_paid_members:
                    member_user = db.query(User).filter(User.id == member.user_id).first()
                    if member_user:
                        try:
                            await bot.send_message(
                                member_user.telegram_id,
                                f"😔 <b>Trip is Now Full</b>\n\n"
                                f"Unfortunately, all seats for <b>{trip.name}</b> have been filled.\n\n"
                                f"📊 <b>Capacity:</b> {paid_count}/{trip.participant_limit} seats taken\n\n"
                                f"Since you haven't submitted payment yet, we had to give priority to those who paid.\n\n"
                                f"⚠️ <b>IMPORTANT: Please DO NOT make payment for this trip!</b>\n\n"
                                f"<b>What you can do:</b>\n"
                                f"• Wait for a cancellation (you'll be notified if a spot opens)\n"
                                f"• Check out other available trips using /trips\n"
                                f"• Contact the organizer to be added to the waitlist\n\n"
                                f"We hope to see you on another trip! 🙏",
                                parse_mode='HTML'
                            )
                        except Exception as e:
                            logging.error(f"Failed to notify not_paid member {member_user.telegram_id}: {e}")
        
        await bot.send_message(
            message.chat.id,
            "✅ <b>Receipt Submitted Successfully!</b>\n\n"
            "Thank you! Your payment receipt has been received and you are now marked as <b>50% Paid</b>! 🎉\n\n"
            "<b>✨ Your Seat is Now RESERVED!</b>\n\n"
            "<b>What happens next?</b>\n"
            "• An admin will review your payment\n"
            "• If there's any issue, we'll notify you\n"
            "• Otherwise, you're all set! �\n\n"
            "<b>Important:</b>\n"
            "• Complete the remaining 50% payment before departure\n"
            "• Use /mystatus anytime to check your registration status\n\n"
            "Have an amazing trip! 🌍✈️",
            parse_mode='HTML'
        )
        
        # Notify admins
        for admin_id in Config.ADMINS:
            try:
                keyboard = types.InlineKeyboardMarkup()
                approve_btn = types.InlineKeyboardButton(
                    text="✅ Confirm Payment",
                    callback_data=f"approve_payment:{trip_member.id}"
                )
                decline_btn = types.InlineKeyboardButton(
                    text="❌ Reject & Reset to Not Paid",
                    callback_data=f"decline_payment:{trip_member.id}"
                )
                keyboard.row(approve_btn, decline_btn)
                
                admin_msg = (
                    f"💳 <b>New Payment Receipt</b>\n\n"
                    f"👤 <b>User:</b> {user.first_name} {user.last_name or ''}\n"
                    f"📧 <b>Email:</b> {user.email}\n"
                    f"🎫 <b>Trip:</b> {trip.name}\n"
                    f"💰 <b>Auto-marked as:</b> 50% Paid ✅\n\n"
                    f"Receipt:"
                )
                
                # Forward the receipt
                if message.content_type == 'photo':
                    await bot.send_photo(
                        admin_id,
                        file_id,
                        caption=admin_msg,
                        parse_mode='HTML',
                        reply_markup=keyboard
                    )
                else:
                    await bot.send_document(
                        admin_id,
                        file_id,
                        caption=admin_msg,
                        parse_mode='HTML',
                        reply_markup=keyboard
                    )
            except Exception as e:
                logging.error(f"Failed to notify admin {admin_id}: {e}")
        logging.info("receipt.submitted user=%s trip_id=%s", tg_id, trip.id)
                
    except Exception as e:
        logging.error(f"Error handling payment receipt from user {tg_id}: {e}", exc_info=True)
        try:
            db.rollback()
        except Exception:
            pass
        
        # Provide detailed error message
        error_msg = "❌ <b>Receipt Upload Failed</b>\n\n"
        
        if "database" in str(e).lower() or "connection" in str(e).lower():
            error_msg += (
                "Database connection issue. Your receipt was not saved.\n\n"
                "<b>What to do:</b>\n"
                "• Wait a moment and send your receipt again\n"
                "• The image/file must be clear and readable\n\n"
                "Error code: DB_CONNECTION_ERROR"
            )
        elif "file" in str(e).lower() or "photo" in str(e).lower():
            error_msg += (
                "There was a problem processing your image/file.\n\n"
                "<b>What to do:</b>\n"
                "• Make sure the file is a valid image (JPG, PNG) or PDF\n"
                "• File size should be under 20MB\n"
                "• Try sending it again\n\n"
                "Error code: FILE_PROCESSING_ERROR"
            )
        elif "trip_member" in str(e).lower() or "not found" in str(e).lower():
            error_msg += (
                "No pending payment found for your account.\n\n"
                "<b>What to do:</b>\n"
                "• Make sure you're registered for a trip first\n"
                "• Use /trips to browse and register\n"
                "• Use /mystatus to check your current status\n\n"
                "Error code: NO_PENDING_PAYMENT"
            )
        else:
            error_msg += (
                "An unexpected error occurred while processing your receipt.\n\n"
                "<b>What to do:</b>\n"
                "• Try sending the receipt again\n"
                "• Make sure you're registered for a trip (/trips)\n"
                "• Contact support if the problem continues\n\n"
                f"Error code: RECEIPT_ERROR\n"
                f"Details: {str(e)[:80]}"
            )
        
        await bot.send_message(message.chat.id, error_msg, parse_mode='HTML')
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


@bot.callback_query_handler(func=lambda call: call.data.startswith('approve_payment:'))
async def approve_payment_handler(call: types.CallbackQuery):
    """Handle payment approval by admin."""
    from models.TripMember import TripMember, PaymentStatus
    from models.Trip import Trip
    
    member_id = int(call.data.split(':')[1])
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        trip_member = db.query(TripMember).filter(TripMember.id == member_id).first()
        if not trip_member:
            await bot.answer_callback_query(call.id, "❌ Member not found.")
            return
        
        user = db.query(User).filter(User.id == trip_member.user_id).first()
        trip = db.query(Trip).filter(Trip.id == trip_member.trip_id).first()
        
        # Status is already half_paid (automatically set when receipt uploaded)
        # This is just a confirmation
        db.commit()
        
        # Remove keyboard
        await bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=None
        )
        
        await bot.edit_message_caption(
            caption=call.message.caption + "\n\n✅ <b>CONFIRMED</b> by admin",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode='HTML'
        )
        
        # Notify user
        msg = (
            f"✅ <b>Payment Confirmed!</b>\n\n"
            f"Great news! Your payment for <b>{trip.name}</b> has been reviewed and confirmed by the admin! �\n\n"
        )
        if getattr(trip, 'participant_invite_link', None):
            msg += (
                f"<b>🔗 Join the Trip Group!</b>\n"
                f"Tap here to join: <a href=\"{trip.participant_invite_link}\">Join Group</a>\n\n"
                f"<i>This is your exclusive participant link. Keep it safe!</i>\n\n"
            )
        else:
            msg += "🔗 <b>Group Link:</b> Coming soon! You'll get it shortly.\n\n"
        
        msg += (
            f"<b>📋 Important Reminders:</b>\n"
            f"• Complete the remaining 50% payment before departure\n"
            f"• Stay active in the group for trip updates\n"
            f"• Use /mystatus to check your status anytime\n\n"
            f"Have an amazing trip! 🌍✈️"
        )

        await bot.send_message(user.telegram_id, msg, parse_mode='HTML', disable_web_page_preview=True)
        await bot.answer_callback_query(call.id, "✅ Payment confirmed!")
        logging.info("payment.confirmed member_id=%s user_id=%s trip_id=%s", member_id, user.id, trip.id)
        
    except Exception as e:
        logging.error(f"Error confirming payment for member {member_id}: {e}", exc_info=True)
        try:
            db.rollback()
        except Exception:
            pass
        
        error_msg = "❌ <b>Payment Confirmation Failed</b>\n\n"
        
        if "not found" in str(e).lower():
            error_msg += (
                "The member or trip record could not be found.\n\n"
                "This might be a temporary issue. Please try again.\n\n"
                "Error code: MEMBER_NOT_FOUND"
            )
        elif "database" in str(e).lower():
            error_msg += (
                "Database error occurred during confirmation.\n\n"
                "The payment status was not updated. Please try again.\n\n"
                "Error code: DB_UPDATE_ERROR"
            )
        else:
            error_msg += (
                "An unexpected error occurred.\n\n"
                f"Error code: CONFIRMATION_ERROR\n"
                f"Details: {str(e)[:80]}"
            )
        
        # Try to notify admin about the error
        try:
            await bot.send_message(
                call.message.chat.id,
                error_msg,
                parse_mode='HTML'
            )
        except:
            pass
        
        await bot.answer_callback_query(call.id, "❌ Error - check message for details")
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


@bot.callback_query_handler(func=lambda call: call.data.startswith('decline_payment:'))
async def decline_payment_handler(call: types.CallbackQuery):
    """Handle payment decline by admin."""
    from models.TripMember import TripMember, PaymentStatus
    from models.Trip import Trip
    
    member_id = int(call.data.split(':')[1])
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        trip_member = db.query(TripMember).filter(TripMember.id == member_id).first()
        if not trip_member:
            await bot.answer_callback_query(call.id, "❌ Member not found.")
            return
        
        user = db.query(User).filter(User.id == trip_member.user_id).first()
        trip = db.query(Trip).filter(Trip.id == trip_member.trip_id).first()
        
        # Change status back to not_paid and clear receipt
        trip_member.payment_status = PaymentStatus.not_paid
        trip_member.payment_receipt_file_id = None
        db.commit()
        
        # Remove keyboard
        await bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=None
        )
        
        await bot.edit_message_caption(
            caption=call.message.caption + "\n\n❌ <b>REJECTED - Reset to Not Paid</b>",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode='HTML'
        )
        
        # Notify user
        await bot.send_message(
            user.telegram_id,
            f"❌ <b>Payment Receipt Rejected</b>\n\n"
            f"We reviewed your payment receipt for <b>{trip.name}</b>, but unfortunately we couldn't accept it.\n\n"
            f"<b>⚠️ Your status has been changed back to Not Paid.</b>\n"
            f"<b>⚠️ Your seat is NO LONGER reserved.</b>\n\n"
            f"<b>Possible reasons:</b>\n"
            f"• Receipt is unclear or incomplete\n"
            f"• Payment amount doesn't match\n"
            f"• Wrong payment method used\n"
            f"• Duplicate or invalid receipt\n\n"
            f"<b>What to do now:</b>\n"
            f"1️⃣ Double-check the payment details\n"
            f"2️⃣ Make the correct payment (50% minimum)\n"
            f"3️⃣ Send a clear photo of your new receipt\n\n"
            f"💬 Need help? Contact the trip organizer for assistance.\n\n"
            f"Don't worry - you can submit a new receipt anytime!",
            parse_mode='HTML'
        )
        
        await bot.answer_callback_query(call.id, "❌ Payment rejected & reset to not paid!")
        logging.info("payment.rejected member_id=%s user_id=%s trip_id=%s", member_id, user.id, trip.id)
        
    except Exception as e:
        logging.error(f"Error rejecting payment for member {member_id}: {e}", exc_info=True)
        try:
            db.rollback()
        except Exception:
            pass
        
        error_msg = "❌ <b>Payment Rejection Failed</b>\n\n"
        
        if "not found" in str(e).lower():
            error_msg += (
                "The member or trip record could not be found.\n\n"
                "This might be a temporary issue. Please try again.\n\n"
                "Error code: MEMBER_NOT_FOUND"
            )
        elif "database" in str(e).lower():
            error_msg += (
                "Database error occurred during rejection.\n\n"
                "The payment status was not updated. Please try again.\n\n"
                "Error code: DB_UPDATE_ERROR"
            )
        else:
            error_msg += (
                "An unexpected error occurred.\n\n"
                f"Error code: REJECTION_ERROR\n"
                f"Details: {str(e)[:80]}"
            )
        
        # Try to notify admin about the error
        try:
            await bot.send_message(
                call.message.chat.id,
                error_msg,
                parse_mode='HTML'
            )
        except:
            pass
        
        await bot.answer_callback_query(call.id, "❌ Error - check message for details")
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


@bot.message_handler(commands=['stats'])
async def stats_command_handler(message: types.Message):
    """Provide statistics access any time.

    - In groups: infer the group from chat.id and show stats for the group's trip if present.
    - In private: list active trips and provide WebApp buttons for each to view stats.
    """
    from models.Trip import Trip, TripStatus
    from models.TripMember import TripMember, PaymentStatus

    db_gen = get_db()
    db: Session = next(db_gen)
    try:
        # If used in a group/supergroup, try to find a trip by group_id
        if message.chat.type in ('group', 'supergroup'):
            trip = db.query(Trip).filter(Trip.group_id == message.chat.id, Trip.status == TripStatus.active).first()
            if not trip:
                await bot.send_message(message.chat.id, "ℹ️ No active trip found for this group.")
                return
            # Compose quick summary (counts only)
            half_paid = db.query(TripMember).filter(
                TripMember.trip_id == trip.id, 
                TripMember.payment_status == PaymentStatus.half_paid
            ).count()
            full_paid = db.query(TripMember).filter(
                TripMember.trip_id == trip.id, 
                TripMember.payment_status == PaymentStatus.full_paid
            ).count()
            total_registered = db.query(TripMember).filter(TripMember.trip_id == trip.id).count()
            # Half-paid and full-paid both reserve seats
            paid_count = half_paid + full_paid
            seats_available = None if trip.participant_limit is None else max(trip.participant_limit - paid_count, 0)

            text = (
                f"📊 <b>{trip.name}</b>\n\n"
                f"� <b>Price:</b> {trip.price:,} UZS\n\n"
                f"�👥 Registered: <b>{total_registered}</b>\n"
                f"🟡 Half Paid: <b>{half_paid}</b>\n"
                f"🟢 Full Paid: <b>{full_paid}</b>\n"
                f"✅ Participants (paid): <b>{paid_count}</b>\n"
            )
            if seats_available is not None:
                text += f"🪑 Seats Available: <b>{seats_available}</b>\n"

            kb = types.InlineKeyboardMarkup()
            kb.add(
                types.InlineKeyboardButton(
                    text="Open Live Stats",
                    web_app=types.WebAppInfo(url=f"{Config.URL.rstrip('/')}/webapp/trip-stats?trip_id={trip.id}")
                )
            )
            await bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=kb)
            logging.info("cmd.stats group_id=%s trip_id=%s", message.chat.id, trip.id)
            return

        # Private chat: list active trips with buttons
        active_trips = db.query(Trip).filter(Trip.status == TripStatus.active).all()
        if not active_trips:
            await bot.send_message(message.chat.id, "ℹ️ There are no active trips right now.")
            return
        msg_lines = ["📊 <b>Trip Statistics</b>", "Select a trip to view live stats:", ""]
        kb = types.InlineKeyboardMarkup()
        for t in active_trips:
            kb.add(
                types.InlineKeyboardButton(
                    text=f"📊 {t.name}",
                    web_app=types.WebAppInfo(url=f"{Config.URL.rstrip('/')}/webapp/trip-stats?trip_id={t.id}")
                )
            )
        await bot.send_message(message.chat.id, "\n".join(msg_lines), parse_mode='HTML', reply_markup=kb)
        logging.info("cmd.stats private from=%s trips=%s", message.from_user.id, len(active_trips))
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


@bot.message_handler(commands=['menu'])
async def menu_handler(message: types.Message):
    """Show a compact main menu for quick navigation. Only works in private chats."""
    
    # Ignore group messages
    if message.chat.type in ('group', 'supergroup'):
        return
    
    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton(text="🗺 Browse Trips", callback_data="menu:trips"),
        types.InlineKeyboardButton(text="🧾 My Status", callback_data="menu:mystatus"),
    )
    kb.row(
        types.InlineKeyboardButton(text="📊 View Stats", callback_data="menu:stats"),
        types.InlineKeyboardButton(text="📅 Trip Agenda", callback_data="menu:agenda"),
    )
    kb.row(
        types.InlineKeyboardButton(text="❓ Help Guide", callback_data="menu:help"),
    )
    await bot.send_message(
        message.chat.id,
        "🧭 <b>Main Menu</b>\n\n"
        "What would you like to do?",
        parse_mode='HTML',
        reply_markup=kb
    )
    logging.info("cmd.menu from=%s", message.from_user.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('menu:'))
async def menu_callback(call: types.CallbackQuery):
    action = call.data.split(':', 1)[1]
    if action == 'trips':
        # Re-use the /trips flow
        class DummyMessage:
            def __init__(self, chat):
                self.chat = chat
                self.from_user = call.from_user
                self.text = '/trips'
        await show_trips_handler(DummyMessage(call.message.chat))
        await bot.answer_callback_query(call.id)
    elif action == 'mystatus':
        class DummyMessage:
            def __init__(self, chat):
                self.chat = chat
                self.from_user = call.from_user
        await my_status_handler(DummyMessage(call.message.chat))
        await bot.answer_callback_query(call.id)
    elif action == 'stats':
        class DummyMessage:
            def __init__(self, chat):
                self.chat = chat
                self.from_user = call.from_user
        await stats_command_handler(DummyMessage(call.message.chat))
        await bot.answer_callback_query(call.id)
    elif action == 'agenda':
        class DummyMessage:
            def __init__(self, chat):
                self.chat = chat
                self.from_user = call.from_user
        await agenda_handler(DummyMessage(call.message.chat))
        await bot.answer_callback_query(call.id)
    elif action == 'help':
        await help_handler(call.message)
        await bot.answer_callback_query(call.id)


@bot.message_handler(commands=['help'])
async def help_handler(message: types.Message):
    """Show help guide. Only works in private chats."""
    
    # Ignore group messages
    if message.chat.type in ('group', 'supergroup'):
        return
    
    text = (
        "❓ <b>Travel Bot - Quick Guide</b>\n\n"
        "<b>🚀 Getting Started</b>\n"
        "1️⃣ <b>Register:</b> /start → Sign in with your @newuu.uz account\n"
        "2️⃣ <b>Browse trips:</b> /trips → See all available adventures\n"
        "3️⃣ <b>Join a trip:</b> Read terms → Tap 'I Agree'\n\n"
        "<b>💳 Payment Process</b>\n"
        "4️⃣ <b>Pay 50%:</b> Transfer minimum 50% to reserve your seat\n"
        "5️⃣ <b>Send receipt:</b> Photo or PDF of your payment proof\n"
        "6️⃣ <b>Get approved:</b> Admin reviews (usually within hours)\n"
        "7️⃣ <b>Join group:</b> Get exclusive participant link!\n\n"
        "<b>📱 Useful Commands</b>\n"
        "• /trips - Browse available trips\n"
        "• /mystatus - Check your registration\n"
        "• /stats - View trip statistics\n"
        "• /agenda - View trip schedule\n"
        "• /menu - Quick navigation menu\n"
        "• /help - Show this guide\n"
        "• /logout - Delete your account\n\n"
        "<b>💡 Pro Tips</b>\n"
        "• Pay early to secure your spot!\n"
        "• Keep your receipt clear and readable\n"
        "• Stay active in the group for updates\n"
        "• Complete full payment before departure\n\n"
        "Questions? Contact the trip organizer! 🌍"
    )
    await bot.send_message(message.chat.id, text, parse_mode='HTML')


@bot.message_handler(commands=['agenda'])
async def agenda_handler(message: types.Message):
    """Show trip agenda/schedule. Only works in private chats."""
    from models.Trip import Trip, TripStatus
    
    # Ignore group messages
    if message.chat.type in ('group', 'supergroup'):
        return
    
    tg_id = message.from_user.id
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        # Check if user is registered
        user = db.query(User).filter(User.telegram_id == tg_id).first()
        if not user:
            keyboard = types.InlineKeyboardMarkup()
            webapp_url = f"{Config.URL.rstrip('/')}/webapp/register"
            keyboard.add(
                types.InlineKeyboardButton(
                    text="✨ Register Now",
                    web_app=types.WebAppInfo(url=webapp_url)
                )
            )
            await bot.send_message(
                message.chat.id,
                "⚠️ <b>Registration Required</b>\n\n"
                "You need to register before viewing trip agendas.\n\n"
                "Tap the button below to get started! 👇",
                parse_mode='HTML',
                reply_markup=keyboard
            )
            return
        
        # Get active trips
        active_trips = db.query(Trip).filter(Trip.status == TripStatus.active).all()
        
        if not active_trips:
            await bot.send_message(
                message.chat.id,
                "📭 <b>No Active Trips</b>\n\n"
                "There are no trips available right now. Check back soon! 🌍",
                parse_mode='HTML'
            )
            return
        
        # If there's only one trip, show its agenda directly
        if len(active_trips) == 1:
            trip = active_trips[0]
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(
                types.InlineKeyboardButton(
                    text=f"📅 View {trip.name} Agenda",
                    web_app=types.WebAppInfo(url=f"{Config.URL.rstrip('/')}/webapp/agenda?trip_id={trip.id}")
                )
            )
            await bot.send_message(
                message.chat.id,
                f"📅 <b>Trip Agenda</b>\n\n"
                f"View the detailed schedule for <b>{trip.name}</b>:",
                parse_mode='HTML',
                reply_markup=keyboard
            )
        else:
            # Multiple trips - let user choose
            keyboard = types.InlineKeyboardMarkup()
            for trip in active_trips:
                keyboard.add(
                    types.InlineKeyboardButton(
                        text=f"📅 {trip.name}",
                        web_app=types.WebAppInfo(url=f"{Config.URL.rstrip('/')}/webapp/agenda?trip_id={trip.id}")
                    )
                )
            await bot.send_message(
                message.chat.id,
                "📅 <b>Trip Agendas</b>\n\n"
                "Select a trip to view its detailed schedule:",
                parse_mode='HTML',
                reply_markup=keyboard
            )
        
        logging.info("cmd.agenda from=%s", tg_id)
        
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


@bot.message_handler(commands=['logout'])
async def logout_handler(message: types.Message):
    """Handle logout request with confirmation. Only works in private chats."""
    
    # Ignore group messages
    if message.chat.type in ('group', 'supergroup'):
        return
    
    tg_id = message.from_user.id
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        # Check if user exists
        user = db.query(User).filter(User.telegram_id == tg_id).first()
        if not user:
            await bot.send_message(
                message.chat.id,
                "ℹ️ <b>Not Registered</b>\n\n"
                "You don't have an account to delete.\n\n"
                "Use /start if you want to register.",
                parse_mode='HTML'
            )
            return
        
        # Check if user has active trip registrations
        from models.TripMember import TripMember, PaymentStatus
        active_registrations = db.query(TripMember).filter(
            TripMember.user_id == user.id,
            TripMember.payment_status.in_([PaymentStatus.half_paid, PaymentStatus.full_paid])
        ).count()
        
        # Create confirmation keyboard
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(
            types.InlineKeyboardButton(text="✅ Yes, Delete My Account", callback_data="confirm_logout"),
            types.InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_logout")
        )
        
        warning_msg = (
            f"⚠️ <b>Delete Account?</b>\n\n"
            f"Are you sure you want to delete your account?\n\n"
            f"<b>⚠️ This action cannot be undone!</b>\n\n"
            f"<b>What will be deleted:</b>\n"
            f"• Your profile information\n"
            f"• All trip registrations\n"
            f"• Payment records\n"
            f"• Access to trip groups\n\n"
        )
        
        if active_registrations > 0:
            warning_msg += (
                f"⚠️ <b>You have {active_registrations} active trip registration(s)!</b>\n"
                f"Deleting your account will remove you from these trips.\n\n"
            )
        
        warning_msg += "Think carefully before proceeding! 🤔"
        
        await bot.send_message(
            message.chat.id,
            warning_msg,
            parse_mode='HTML',
            reply_markup=keyboard
        )
        logging.info("cmd.logout requested from=%s", tg_id)
        
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


@bot.callback_query_handler(func=lambda call: call.data == 'confirm_logout')
async def confirm_logout_handler(call: types.CallbackQuery):
    """Handle logout confirmation - delete user account."""
    
    tg_id = call.from_user.id
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        user = db.query(User).filter(User.telegram_id == tg_id).first()
        if not user:
            await bot.answer_callback_query(call.id, "❌ User not found.")
            return
        
        # Get user info before deletion for logging
        user_email = user.email
        user_name = f"{user.first_name} {user.last_name or ''}".strip()
        
        # Delete user (cascade will handle trip_members due to foreign key)
        db.delete(user)
        db.commit()
        
        # Remove keyboard
        await bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=None
        )
        
        await bot.edit_message_text(
            "✅ <b>Account Deleted</b>\n\n"
            "Your account has been successfully deleted.\n\n"
            "All your data has been removed from our system.\n\n"
            "If you change your mind, you can always register again using /start.\n\n"
            "Thank you for using Travel Bot! We hope to see you again. 👋",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode='HTML'
        )
        
        await bot.answer_callback_query(call.id, "✅ Account deleted successfully")
        logging.info("user.deleted tg_id=%s email=%s name=%s", tg_id, user_email, user_name)
        
    except Exception as e:
        logging.error(f"Error deleting user account for {tg_id}: {e}", exc_info=True)
        try:
            db.rollback()
        except Exception:
            pass
        
        error_msg = "❌ <b>Deletion Failed</b>\n\n"
        
        if "foreign key" in str(e).lower() or "constraint" in str(e).lower():
            error_msg += (
                "Cannot delete account due to active dependencies.\n\n"
                "This might be a temporary issue. Please try again or contact support.\n\n"
                "Error code: FK_CONSTRAINT"
            )
        elif "database" in str(e).lower():
            error_msg += (
                "Database error occurred during deletion.\n\n"
                "Please try again in a moment.\n\n"
                "Error code: DB_ERROR"
            )
        else:
            error_msg += (
                "An unexpected error occurred.\n\n"
                "Please try again or contact support.\n\n"
                f"Error code: DELETE_ERROR\n"
                f"Details: {str(e)[:80]}"
            )
        
        await bot.send_message(call.message.chat.id, error_msg, parse_mode='HTML')
        await bot.answer_callback_query(call.id, "❌ Deletion failed - check message")
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


@bot.callback_query_handler(func=lambda call: call.data == 'cancel_logout')
async def cancel_logout_handler(call: types.CallbackQuery):
    """Handle logout cancellation."""
    
    await bot.edit_message_text(
        "✅ <b>Cancelled</b>\n\n"
        "Your account is safe! No changes were made.\n\n"
        "Use /menu to continue using the bot.",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode='HTML'
    )
    await bot.answer_callback_query(call.id, "✅ Logout cancelled")
    logging.info("logout.cancelled from=%s", call.from_user.id)


@bot.message_handler(commands=['admin'])
async def admin_handler(message: types.Message):
    """Open Admin dashboard for configured admins only. Only works in private chats."""
    
    # Ignore group messages
    if message.chat.type in ('group', 'supergroup'):
        return
    
    user_id = message.from_user.id
    if user_id not in set(Config.ADMINS or []):
        await bot.send_message(message.chat.id, "❌ You are not an admin.")
        return
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton(
            text="🛠 Open Admin Dashboard",
            web_app=types.WebAppInfo(url=f"{Config.URL.rstrip('/')}/admin")
        )
    )
    await bot.send_message(message.chat.id, "Admin tools:", reply_markup=kb)
    logging.info("cmd.admin open from=%s", user_id)
