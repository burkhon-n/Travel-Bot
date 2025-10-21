"""Email service for sending professional notifications to trip participants.

Uses SMTP to send styled HTML emails with the travel club branding.
"""

import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from pathlib import Path
from typing import Optional

from config import Config


class EmailService:
    """Service for sending branded emails to participants."""
    
    def __init__(self):
        # Use Config class which already loaded .env file
        self.email = Config.EMAIL
        self.password = Config.EMAIL_PASSWORD
        self.smtp_server = "smtp.gmail.com"  # Update if using different provider
        self.smtp_port = 587
        
    def _get_logo_data(self) -> Optional[bytes]:
        """Read logo image file."""
        logo_path = Path(__file__).parent / "static" / "logo.png"
        if logo_path.exists():
            with open(logo_path, "rb") as f:
                return f.read()
        return None
    
    def _create_email_template(self, recipient_name: str, trip_name: str, trip_price: int, status: str) -> str:
        """Create styled HTML email template.
        
        Args:
            recipient_name: Participant's full name
            trip_name: Name of the trip
            trip_price: Total price paid
            status: Payment status ('half_paid' or 'full_paid') - used internally for logic
        """
        # Pure congratulations message without status details
        title = "🎉 Congratulations! Payment Approved!"
        
        message = f"""
            <p style="font-size: 18px; color: #1F2937; margin: 20px 0;">
                Amazing news! Your payment for <strong>{trip_name}</strong> has been approved! 💙
            </p>
            <p style="font-size: 16px; color: #4B5563; margin: 15px 0;">
                We're absolutely thrilled to have you join us on this incredible adventure. 
                Your spot is confirmed and we can't wait to explore together!
            </p>
        """
        
        next_steps = """
            <li>Join the trip group using the link sent to your Telegram</li>
            <li>Check the group regularly for important updates</li>
            <li>Mark your calendar for the departure date</li>
            <li>Start preparing for an unforgettable experience! 🎒</li>
        """
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <link href="https://fonts.googleapis.com/css2?family=League+Gothic&family=Bree+Serif&display=swap" rel="stylesheet">
            <title>Payment Confirmation</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Bree Serif', serif; background-color: #F3F4F6;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #F3F4F6; padding: 40px 20px;">
                <tr>
                    <td align="center">
                        <table width="600" cellpadding="0" cellspacing="0" style="background-color: #FFFFFF; border-radius: 16px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); overflow: hidden;">
                            
                            <!-- Header with Logo -->
                            <tr>
                                <td style="background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%); padding: 40px; text-align: center;">
                                    <img src="cid:logo" alt="Travel Club Logo" style="width: 100px; height: 100px; margin-bottom: 20px; border-radius: 50%; background: white; padding: 10px;">
                                    <h1 style="font-family: 'League Gothic', sans-serif; color: #FFFFFF; font-size: 42px; margin: 0; letter-spacing: 2px; text-transform: uppercase;">
                                        {title}
                                    </h1>
                                </td>
                            </tr>
                            
                            <!-- Main Content -->
                            <tr>
                                <td style="padding: 40px 40px 30px 40px;">
                                    <p style="font-size: 20px; color: #1F2937; margin: 0 0 10px 0;">
                                        Dear <strong>{recipient_name}</strong>,
                                    </p>
                                    
                                    {message}
                                    
                                    <!-- Trip Details Box -->
                                    <div style="background: #F9FAFB; border-radius: 12px; padding: 25px; margin: 25px 0; border: 2px solid #E5E7EB;">
                                        <h2 style="font-family: 'League Gothic', sans-serif; color: #3B82F6; font-size: 28px; margin: 0 0 15px 0; letter-spacing: 1px;">
                                            📍 TRIP DETAILS
                                        </h2>
                                        <table width="100%" cellpadding="8" cellspacing="0">
                                            <tr>
                                                <td style="color: #6B7280; font-size: 14px; padding: 8px 0;">🎫 <strong>Trip:</strong></td>
                                                <td style="color: #1F2937; font-size: 14px; text-align: right; padding: 8px 0;">{trip_name}</td>
                                            </tr>
                                            <tr>
                                                <td style="color: #6B7280; font-size: 14px; padding: 8px 0;">💰 <strong>Total Price:</strong></td>
                                                <td style="color: #1F2937; font-size: 14px; text-align: right; padding: 8px 0;"><strong>{trip_price:,} UZS</strong></td>
                                            </tr>
                                        </table>
                                    </div>
                                    
                                    <!-- Next Steps -->
                                    <h3 style="font-family: 'League Gothic', sans-serif; color: #1F2937; font-size: 24px; margin: 30px 0 15px 0; letter-spacing: 1px;">
                                        📋 WHAT'S NEXT?
                                    </h3>
                                    <ul style="color: #4B5563; font-size: 15px; line-height: 1.8; padding-left: 20px;">
                                        {next_steps}
                                    </ul>
                                    
                                    <!-- Blue Heart Message -->
                                    <div style="background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%); border-radius: 12px; padding: 20px; margin: 30px 0; text-align: center; border: 2px solid #3B82F6;">
                                        <p style="font-size: 18px; color: #1E40AF; margin: 0; line-height: 1.6;">
                                            <strong>We can't wait to explore with you! 💙</strong><br>
                                            <span style="font-size: 15px;">Get ready for memories that will last a lifetime!</span>
                                        </p>
                                    </div>
                                    
                                    <!-- Contact Info -->
                                    <p style="font-size: 14px; color: #6B7280; margin: 25px 0 0 0; line-height: 1.6;">
                                        Questions? Reach out to us anytime on Telegram or via email.<br>
                                        We're here to make your trip unforgettable!
                                    </p>
                                </td>
                            </tr>
                            
                            <!-- Footer -->
                            <tr>
                                <td style="background: linear-gradient(135deg, #1E3A8A 0%, #1E40AF 100%); padding: 30px 40px; text-align: center;">
                                    <p style="color: #FFFFFF; font-size: 16px; margin: 0 0 10px 0; font-family: 'League Gothic', sans-serif; letter-spacing: 1px; font-size: 24px;">
                                        💙 TRAVEL CLUB
                                    </p>
                                    <p style="color: #BFDBFE; font-size: 13px; margin: 5px 0; line-height: 1.5;">
                                        Making every journey memorable<br>
                                        📧 travel@newuu.uz | 📱 @pu_travel
                                    </p>
                                    <p style="color: #93C5FD; font-size: 12px; margin: 15px 0 0 0;">
                                        © 2025 Travel Club. All rights reserved.
                                    </p>
                                </td>
                            </tr>
                            
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        return html
    
    def send_payment_confirmation_email(
        self, 
        recipient_email: str, 
        recipient_name: str, 
        trip_name: str, 
        trip_price: int,
        status: str
    ) -> bool:
        """Send payment confirmation email to participant.
        
        Args:
            recipient_email: Email address of the recipient
            recipient_name: Full name of the recipient
            trip_name: Name of the trip
            trip_price: Total trip price
            status: Payment status ('half_paid' or 'full_paid')
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.email or not self.password:
            logging.warning(f"Email credentials not configured. Email: {'SET' if self.email else 'NOT SET'}, Password: {'SET' if self.password else 'NOT SET'}")
            return False
        
        if not recipient_email:
            logging.warning("Recipient email not provided. Skipping email notification.")
            return False
        
        logging.info(f"Attempting to send email to {recipient_email} for trip '{trip_name}' using SMTP: {self.smtp_server}:{self.smtp_port}")
            
        try:
            # Create message
            msg = MIMEMultipart('related')
            msg['Subject'] = f"🎉 Payment Confirmed - {trip_name}"
            msg['From'] = f"Travel Club 💙 <{self.email}>"
            msg['To'] = recipient_email
            
            # Create HTML content
            html_content = self._create_email_template(recipient_name, trip_name, trip_price, status)
            msg_alternative = MIMEMultipart('alternative')
            msg.attach(msg_alternative)
            
            # Attach HTML
            msg_html = MIMEText(html_content, 'html')
            msg_alternative.attach(msg_html)
            
            # Attach logo
            logo_data = self._get_logo_data()
            if logo_data:
                msg_image = MIMEImage(logo_data)
                msg_image.add_header('Content-ID', '<logo>')
                msg_image.add_header('Content-Disposition', 'inline', filename='logo.png')
                msg.attach(msg_image)
            
            # Send email
            logging.debug(f"Connecting to SMTP server {self.smtp_server}:{self.smtp_port}...")
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                logging.debug("Starting TLS...")
                server.starttls()
                logging.debug(f"Logging in with email: {self.email}")
                server.login(self.email, self.password)
                logging.debug("Sending message...")
                server.send_message(msg)
            
            logging.info(f"✅ Payment confirmation email sent successfully to {recipient_email} for trip '{trip_name}' (status: {status})")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logging.error(f"❌ SMTP Authentication failed for {self.email}: {e}")
            logging.error("💡 Tip: If using Gmail, make sure 2FA is enabled and use an App Password")
            return False
        except smtplib.SMTPException as e:
            logging.error(f"❌ SMTP error when sending email to {recipient_email}: {e}")
            return False
        except Exception as e:
            logging.error(f"❌ Unexpected error sending email to {recipient_email}: {type(e).__name__}: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return False


# Singleton instance
_email_service = None

def get_email_service() -> EmailService:
    """Get or create the email service instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
