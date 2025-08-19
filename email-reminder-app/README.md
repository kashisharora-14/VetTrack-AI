# Daily Email Reminder App

A Node.js application that sends automated daily reminder emails at scheduled times using Nodemailer and node-cron.

## Features

- ✅ **First-time email setup**: Prompts for email on first visit
- ✅ **Persistent storage**: Stores email in `emails.json` file
- ✅ **Update email**: `/update-email` route to change email address
- ✅ **Scheduled reminders**: Uses node-cron to send emails daily at 9 AM
- ✅ **Gmail integration**: Configured for Gmail using Nodemailer
- ✅ **Environment variables**: Secure credential storage via .env
- ✅ **Console logging**: Clear logs when emails are sent
- ✅ **Web interface**: Beautiful responsive UI for management
- ✅ **Statistics tracking**: Track sent emails and history
- ✅ **Test email feature**: Send test reminders manually

## Prerequisites

- Node.js 18+ installed
- Gmail account with App Password enabled

## Setup Instructions

### 1. Clone and Install Dependencies

```bash
cd email-reminder-app
npm install
```

### 2. Configure Gmail App Password

1. Go to your [Google Account settings](https://myaccount.google.com/)
2. Navigate to Security → 2-Step Verification
3. Scroll down to "App passwords"
4. Generate a new app password for "Mail"
5. Copy the 16-character password

### 3. Environment Configuration

Copy `.env.example` to `.env` and update with your credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```env
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-16-character-app-password
PORT=3000
REMINDER_HOUR=9
REMINDER_MINUTE=0
```

### 4. Run the Application

```bash
# Development mode with auto-restart
npm run dev

# Production mode
npm start
```

## Usage

### Web Interface

1. Visit `http://localhost:3000`
2. Enter your email address on first visit
3. The app will automatically start sending daily reminders at 9:00 AM
4. Use `/update-email` to change your email address anytime

### API Endpoints

- `GET /` - Main dashboard
- `POST /set-email` - Set initial email address
- `GET /update-email` - Update email page
- `POST /update-email` - Update email address
- `POST /send-test` - Send test reminder immediately
- `GET /stats` - Get email statistics
- `POST /cron/start` - Start cron scheduler
- `POST /cron/stop` - Stop cron scheduler

## File Structure

```
email-reminder-app/
├── package.json          # Dependencies and scripts
├── server.js             # Main Express server
├── emailService.js       # Email sending logic
├── cronScheduler.js      # Cron job management
├── emails.json           # User email storage
├── .env                  # Environment variables (create from .env.example)
├── .env.example          # Environment template
├── views/                # EJS templates
│   ├── layout.ejs        # Base layout
│   ├── index.ejs         # Home page
│   ├── update-email.ejs  # Update email page
│   └── 404.ejs           # Error page
└── README.md             # This file
```

## Example emails.json Structure

```json
{
  "userEmail": "user@example.com",
  "lastEmailSent": "2025-08-12T09:00:00.000Z",
  "reminderCount": 15,
  "createdAt": "2025-08-01T10:30:00.000Z",
  "updatedAt": "2025-08-12T09:00:00.000Z"
}
```

## Example Reminder Email

The app sends beautifully formatted HTML emails with:

- **Subject**: "Daily Reminder - [Date]"
- **Content**: Motivational reminders including:
  - Drink water goals
  - Exercise reminders
  - Reading suggestions
  - Mindfulness practices
  - Social connection prompts
  - Gratitude exercises
  - Productivity tips
- **Styling**: Professional HTML design with responsive layout

## Console Logs

When emails are sent, you'll see detailed logs:

```
✅ Reminder email sent successfully!
📧 To: user@example.com
📅 Date: Monday, August 12, 2025
🔢 Total reminders sent: 15
📮 Message ID: <message-id@gmail.com>
```

## Scheduling

- **Default time**: 9:00 AM daily
- **Timezone**: America/New_York (configurable in `cronScheduler.js`)
- **Cron expression**: `0 9 * * *` (minute hour * * *)
- **Customization**: Modify `REMINDER_HOUR` and `REMINDER_MINUTE` in `.env`

## Troubleshooting

### Email not sending
1. Check Gmail credentials in `.env`
2. Ensure App Password is correctly generated
3. Check console logs for specific error messages

### App Password issues
1. Enable 2-Factor Authentication first
2. Generate new App Password in Google Account settings
3. Use the 16-character password (without spaces)

### Cron not working
1. Check server timezone settings
2. Verify cron expression format
3. Check if scheduler is running in the web interface

## License

MIT License - feel free to use and modify for your needs.