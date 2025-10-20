# 🔍 Error Codes Reference

Quick reference guide for all error codes in the Travel Bot system.

## 📊 Error Code Format

Format: `ERROR_XXXX` where XXXX is a 4-digit code

Example: `ERROR_0001` - Database connection failure

## 🗂️ Error Categories

### 1000-1999: Database Errors

| Code | Message | Cause | Solution |
|------|---------|-------|----------|
| 1001 | Database connection failed | Cannot connect to PostgreSQL | Check DATABASE_URL, verify database is running |
| 1002 | Database query timeout | Query took too long | Check database performance, review indexes |
| 1003 | Duplicate registration | User already registered for trip | User should check their status with `/mystatus` |
| 1004 | Record not found | Trip or user not found | Verify trip exists, user is registered |
| 1005 | Transaction rollback | Error during database operation | Check logs for specific cause, try again |

### 2000-2999: File Handling Errors

| Code | Message | Cause | Solution |
|------|---------|-------|----------|
| 2001 | Invalid file type | Receipt is not photo or PDF | Send photo or PDF file only |
| 2002 | File size too large | Receipt file exceeds limit | Compress image or reduce file size |
| 2003 | File download failed | Cannot download receipt from Telegram | Try uploading again |
| 2004 | File storage error | Cannot store receipt | Check server storage space |

### 3000-3999: Permission Errors

| Code | Message | Cause | Solution |
|------|---------|-------|----------|
| 3001 | Unauthorized access | User not admin | Only admins can access this feature |
| 3002 | Trip not accessible | User not member of trip | Register for trip first |
| 3003 | Action not allowed | Operation not permitted | Check your status and permissions |

### 4000-4999: Validation Errors

| Code | Message | Cause | Solution |
|------|---------|-------|----------|
| 4001 | Invalid trip data | Missing required trip information | Check all required fields are filled |
| 4002 | Trip capacity reached | No more seats available | Wait for admin to increase capacity or check other trips |
| 4003 | Invalid email domain | Email not from @newuu.uz | Register with your @newuu.uz account |
| 4004 | Invalid payment status | Status transition not allowed | Contact admin |
| 4005 | Trip not active | Trip is completed or cancelled | Cannot perform action on inactive trip |

### 5000-5999: Network/Timeout Errors

| Code | Message | Cause | Solution |
|------|---------|-------|----------|
| 5001 | Request timeout | Operation took too long | Try again, check internet connection |
| 5002 | Telegram API error | Cannot communicate with Telegram | Try again in a few moments |
| 5003 | OAuth callback failed | Google OAuth error | Try registration again, check browser |
| 5004 | Webhook delivery failed | Cannot receive updates | Contact support |

### 6000-6999: Business Logic Errors

| Code | Message | Cause | Solution |
|------|---------|-------|----------|
| 6001 | Payment already processed | Receipt already reviewed | Check payment status with `/mystatus` |
| 6002 | No receipt uploaded | Trying to approve but no receipt | User must upload receipt first |
| 6003 | User kicked from trip | User was removed by admin | Contact admin if you believe this is a mistake |
| 6004 | Trip full - payment not accepted | Capacity reached when uploading receipt | Trip is full, do not make payment |

### 9000-9999: System Errors

| Code | Message | Cause | Solution |
|------|---------|-------|----------|
| 9001 | Configuration error | Missing or invalid environment variable | Check .env file, restart application |
| 9002 | Unknown error | Unexpected error occurred | Contact support with error code |
| 9003 | Service unavailable | System maintenance or overload | Try again later |

## 🔧 How to Use Error Codes

### For Users
When you receive an error:
1. Note the error code (e.g., ERROR_1003)
2. Check this guide for the cause and solution
3. Try the suggested solution
4. If problem persists, contact support with the error code

### For Developers
When implementing new features:
1. Choose appropriate category (1000s, 2000s, etc.)
2. Assign next available code in category
3. Use `format_error_message()` utility:
   ```python
   from bot import format_error_message
   
   error_msg = format_error_message(
       error_type="database",
       error_code="1003",
       user_action="User tried to register for same trip twice",
       details=f"Trip: {trip.name}, User: {user.telegram_id}",
       suggested_action="Check your status with /mystatus"
   )
   ```
4. Update this reference guide

## 📋 Error Message Template

Standard error message format:
```
❌ Error: [Brief Description]

🔍 What happened:
[User-friendly explanation]

💡 What you can do:
[Actionable steps]

📞 Need help?
Contact support with error code: ERROR_XXXX
```

## 🛠️ Debugging Tips

### For Admins
1. **Check application logs:**
   ```bash
   sudo journalctl -u travelbot -n 100 | grep ERROR
   ```

2. **Check database:**
   ```bash
   sudo -u postgres psql -d travel_bot
   ```

3. **Check system resources:**
   ```bash
   htop
   df -h
   ```

### Common Issues

#### Database Connection (ERROR_1001)
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connection
psql -U travelbot -d travel_bot

# Check DATABASE_URL in .env
cat .env | grep DATABASE_URL
```

#### Trip Capacity (ERROR_4002 / ERROR_6004)
```sql
-- Check current capacity
SELECT 
    t.name,
    t.participant_limit,
    COUNT(tm.id) as current_participants
FROM trips t
LEFT JOIN trip_members tm ON t.id = tm.trip_id 
WHERE tm.payment_status IN ('half_paid', 'full_paid')
GROUP BY t.id;
```

#### Duplicate Registration (ERROR_1003)
```sql
-- Find duplicate attempts
SELECT user_id, trip_id, COUNT(*)
FROM trip_members
GROUP BY user_id, trip_id
HAVING COUNT(*) > 1;

-- Fix duplicates (keep earliest)
DELETE FROM trip_members
WHERE id NOT IN (
    SELECT MIN(id)
    FROM trip_members
    GROUP BY user_id, trip_id
);
```

## 📊 Error Statistics

Track error frequency to identify issues:

```sql
-- If you implement error logging table
SELECT 
    error_code,
    COUNT(*) as occurrences,
    MAX(created_at) as last_occurrence
FROM error_logs
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY error_code
ORDER BY occurrences DESC;
```

## 🔄 Error Recovery

### Automatic Recovery
- Database transactions rollback automatically
- Connection pools handle reconnection
- Webhook retries from Telegram (up to 24 hours)

### Manual Recovery
1. **Database issues:** Restore from backup
2. **File issues:** Request user to re-upload
3. **Permission issues:** Update admin list in .env
4. **Configuration issues:** Fix .env and restart service

## 📝 Error Reporting

When reporting errors, include:
- ✅ Error code
- ✅ Timestamp
- ✅ User action that caused error
- ✅ Expected vs actual behavior
- ✅ Relevant logs (last 20 lines)
- ✅ System environment (OS, Python version)

---

**Last Updated:** January 2025
**Version:** 1.0
