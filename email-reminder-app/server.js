const express = require('express');
const path = require('path');
const EmailService = require('./emailService');
const CronScheduler = require('./cronScheduler');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Initialize services
const emailService = new EmailService();
const cronScheduler = new CronScheduler();

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));

// Set EJS as template engine
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Routes
app.get('/', async (req, res) => {
    try {
        const userEmail = await emailService.getUserEmail();
        const stats = await emailService.getEmailStats();
        const cronStatus = cronScheduler.getStatus();
        
        res.render('index', { 
            userEmail, 
            stats,
            cronStatus,
            message: null 
        });
    } catch (error) {
        console.error('Error loading homepage:', error);
        res.render('index', { 
            userEmail: null, 
            stats: null,
            cronStatus: null,
            message: { type: 'error', text: 'Error loading data' }
        });
    }
});

app.post('/set-email', async (req, res) => {
    try {
        const { email } = req.body;
        
        if (!email || !isValidEmail(email)) {
            return res.json({ 
                success: false, 
                message: 'Please provide a valid email address' 
            });
        }
        
        await emailService.setUserEmail(email);
        
        res.json({ 
            success: true, 
            message: 'Email saved successfully! Daily reminders will be sent at the scheduled time.' 
        });
    } catch (error) {
        console.error('Error setting email:', error);
        res.json({ 
            success: false, 
            message: 'Failed to save email. Please try again.' 
        });
    }
});

app.post('/update-email', async (req, res) => {
    try {
        const { email } = req.body;
        
        if (!email || !isValidEmail(email)) {
            return res.json({ 
                success: false, 
                message: 'Please provide a valid email address' 
            });
        }
        
        await emailService.setUserEmail(email);
        
        res.json({ 
            success: true, 
            message: 'Email updated successfully!' 
        });
    } catch (error) {
        console.error('Error updating email:', error);
        res.json({ 
            success: false, 
            message: 'Failed to update email. Please try again.' 
        });
    }
});

app.get('/update-email', async (req, res) => {
    try {
        const userEmail = await emailService.getUserEmail();
        const stats = await emailService.getEmailStats();
        
        res.render('update-email', { 
            userEmail, 
            stats,
            message: null 
        });
    } catch (error) {
        console.error('Error loading update email page:', error);
        res.render('update-email', { 
            userEmail: null, 
            stats: null,
            message: { type: 'error', text: 'Error loading data' }
        });
    }
});

app.post('/send-test', async (req, res) => {
    try {
        const userEmail = await emailService.getUserEmail();
        
        if (!userEmail) {
            return res.json({ 
                success: false, 
                message: 'No email configured. Please set your email first.' 
            });
        }
        
        const success = await cronScheduler.triggerManual();
        
        if (success) {
            res.json({ 
                success: true, 
                message: 'Test reminder sent successfully! Check your email.' 
            });
        } else {
            res.json({ 
                success: false, 
                message: 'Failed to send test reminder. Check server logs for details.' 
            });
        }
    } catch (error) {
        console.error('Error sending test email:', error);
        res.json({ 
            success: false, 
            message: 'Error sending test email. Please try again.' 
        });
    }
});

app.get('/stats', async (req, res) => {
    try {
        const stats = await emailService.getEmailStats();
        const cronStatus = cronScheduler.getStatus();
        
        res.json({ 
            success: true, 
            stats,
            cronStatus
        });
    } catch (error) {
        console.error('Error getting stats:', error);
        res.json({ 
            success: false, 
            message: 'Error loading statistics' 
        });
    }
});

app.post('/cron/start', (req, res) => {
    try {
        cronScheduler.start();
        res.json({ 
            success: true, 
            message: 'Cron scheduler started successfully' 
        });
    } catch (error) {
        console.error('Error starting cron:', error);
        res.json({ 
            success: false, 
            message: 'Failed to start cron scheduler' 
        });
    }
});

app.post('/cron/stop', (req, res) => {
    try {
        cronScheduler.stop();
        res.json({ 
            success: true, 
            message: 'Cron scheduler stopped successfully' 
        });
    } catch (error) {
        console.error('Error stopping cron:', error);
        res.json({ 
            success: false, 
            message: 'Failed to stop cron scheduler' 
        });
    }
});

// Error handling middleware
app.use((err, req, res, next) => {
    console.error('Unhandled error:', err);
    res.status(500).json({ 
        success: false, 
        message: 'Internal server error' 
    });
});

// 404 handler
app.use((req, res) => {
    res.status(404).render('404');
});

// Helper functions
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('\n🛑 Received SIGINT. Shutting down gracefully...');
    cronScheduler.stop();
    process.exit(0);
});

process.on('SIGTERM', () => {
    console.log('\n🛑 Received SIGTERM. Shutting down gracefully...');
    cronScheduler.stop();
    process.exit(0);
});

// Start server
app.listen(PORT, () => {
    console.log('🚀 Daily Reminder App Started');
    console.log('================================');
    console.log(`📡 Server running on http://localhost:${PORT}`);
    console.log(`📧 Email service: ${process.env.EMAIL_USER ? 'Configured' : 'Not configured'}`);
    console.log(`⏰ Reminder time: ${process.env.REMINDER_HOUR || 9}:${(process.env.REMINDER_MINUTE || 0).toString().padStart(2, '0')}`);
    console.log('================================\n');
    
    // Start cron scheduler
    cronScheduler.start();
});