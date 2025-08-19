const cron = require('node-cron');
const EmailService = require('./emailService');
require('dotenv').config();

class CronScheduler {
    constructor() {
        this.emailService = new EmailService();
        this.scheduledTask = null;
        this.isRunning = false;
    }

    start() {
        if (this.isRunning) {
            console.log('⚠️  Cron scheduler is already running');
            return;
        }

        const hour = process.env.REMINDER_HOUR || 9;
        const minute = process.env.REMINDER_MINUTE || 0;
        
        // Create cron expression for daily execution
        // Format: minute hour * * * (every day at specified time)
        const cronExpression = `${minute} ${hour} * * *`;
        
        console.log(`⏰ Setting up daily reminder schedule:`);
        console.log(`   Time: ${hour}:${minute.toString().padStart(2, '0')} (24-hour format)`);
        console.log(`   Cron expression: ${cronExpression}`);
        
        // Validate cron expression
        if (!cron.validate(cronExpression)) {
            console.error('❌ Invalid cron expression:', cronExpression);
            return;
        }

        this.scheduledTask = cron.schedule(cronExpression, async () => {
            console.log(`\n🕐 Cron job triggered at ${new Date().toLocaleString()}`);
            console.log('📧 Attempting to send daily reminder email...');
            
            try {
                const success = await this.emailService.sendReminderEmail();
                if (success) {
                    console.log('✅ Daily reminder sent successfully!\n');
                } else {
                    console.log('❌ Failed to send daily reminder\n');
                }
            } catch (error) {
                console.error('❌ Error in cron job:', error.message, '\n');
            }
        }, {
            scheduled: false, // Don't start immediately
            timezone: "America/New_York" // Adjust timezone as needed
        });

        this.scheduledTask.start();
        this.isRunning = true;
        
        console.log('✅ Cron scheduler started successfully');
        console.log(`📅 Next execution: ${this.getNextExecutionTime()}`);
        
        // Optional: Send test email immediately in development
        if (process.env.NODE_ENV === 'development') {
            console.log('\n🧪 Development mode detected');
            this.sendTestReminder();
        }
    }

    stop() {
        if (this.scheduledTask) {
            this.scheduledTask.stop();
            this.isRunning = false;
            console.log('⏹️  Cron scheduler stopped');
        }
    }

    restart() {
        this.stop();
        setTimeout(() => {
            this.start();
        }, 1000);
    }

    getStatus() {
        return {
            isRunning: this.isRunning,
            nextExecution: this.isRunning ? this.getNextExecutionTime() : null,
            schedule: `${process.env.REMINDER_MINUTE || 0} ${process.env.REMINDER_HOUR || 9} * * *`
        };
    }

    getNextExecutionTime() {
        const now = new Date();
        const hour = parseInt(process.env.REMINDER_HOUR || 9);
        const minute = parseInt(process.env.REMINDER_MINUTE || 0);
        
        const nextExecution = new Date();
        nextExecution.setHours(hour, minute, 0, 0);
        
        // If the time has already passed today, schedule for tomorrow
        if (nextExecution <= now) {
            nextExecution.setDate(nextExecution.getDate() + 1);
        }
        
        return nextExecution.toLocaleString();
    }

    async sendTestReminder() {
        console.log('🧪 Sending test reminder email...');
        try {
            const success = await this.emailService.sendReminderEmail();
            if (success) {
                console.log('✅ Test reminder sent successfully!');
            } else {
                console.log('❌ Failed to send test reminder');
            }
        } catch (error) {
            console.error('❌ Error sending test reminder:', error.message);
        }
    }

    // Manual trigger for testing
    async triggerManual() {
        console.log('🔧 Manually triggering reminder email...');
        try {
            const success = await this.emailService.sendReminderEmail();
            if (success) {
                console.log('✅ Manual reminder sent successfully!');
            } else {
                console.log('❌ Failed to send manual reminder');
            }
            return success;
        } catch (error) {
            console.error('❌ Error in manual trigger:', error.message);
            return false;
        }
    }
}

module.exports = CronScheduler;