# Email Reminder App - Demo Instructions

## Quick Start Demo

### 1. Test the Application Locally

```bash
cd email-reminder-app
node server.js
```

Visit `http://localhost:3000` to see the web interface.

### 2. Configure Gmail Credentials

To actually send emails, you'll need to set up Gmail credentials:

1. **Get Gmail App Password:**
   - Go to [Google Account Security](https://myaccount.google.com/security)
   - Enable 2-Factor Authentication
   - Generate an App Password for "Mail"
   - Copy the 16-character password

2. **Update .env file:**
   ```env
   EMAIL_USER=your-email@gmail.com
   EMAIL_PASS=your-16-character-app-password
   PORT=3000
   REMINDER_HOUR=9
   REMINDER_MINUTE=0
   ```

### 3. Test Email Functionality

1. **Set Email Address:** Enter your email on the homepage
2. **Send Test Email:** Click "Send Test Reminder" button
3. **Check Scheduling:** View cron scheduler status
4. **Update Email:** Use the update email page to change address

### 4. Example Flow

```bash
# 1. Start the app
node server.js

# 2. Visit http://localhost:3000
# 3. Enter email: test@example.com
# 4. Click "Save Email & Start Reminders"
# 5. Click "Send Test Reminder" to test immediately
# 6. Check console logs for email sending status
```

## Key Features Demonstrated

✅ **First-time email setup** - Prompts for email on first visit
✅ **Persistent storage** - Stores in emails.json file  
✅ **Update email route** - /update-email for changing address
✅ **Scheduled sending** - Daily at 9 AM using node-cron
✅ **Gmail integration** - Uses Nodemailer with Gmail service
✅ **Environment variables** - Secure .env credential storage
✅ **Console logging** - Clear logs when emails are sent
✅ **Beautiful UI** - Bootstrap-based responsive interface
✅ **Statistics** - Track sent emails and history

## Console Output Example

```
🚀 Daily Reminder App Started
================================
📡 Server running on http://localhost:3000
📧 Email service: Configured
⏰ Reminder time: 9:00
================================

⏰ Setting up daily reminder schedule:
   Time: 9:00 (24-hour format)
   Cron expression: 0 9 * * *
✅ Cron scheduler started successfully
📅 Next execution: 8/12/2025, 9:00:00 AM

✅ Reminder email sent successfully!
📧 To: user@example.com
📅 Date: Monday, August 12, 2025
🔢 Total reminders sent: 1
📮 Message ID: <abc123@gmail.com>
```

## Production Deployment

For production use:
1. Set NODE_ENV=production
2. Use process manager like PM2
3. Configure proper timezone in cronScheduler.js
4. Set up email monitoring and error handling
5. Consider using a dedicated SMTP service for higher volume