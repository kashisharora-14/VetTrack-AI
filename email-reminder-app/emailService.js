const nodemailer = require('nodemailer');
const fs = require('fs').promises;
const path = require('path');
require('dotenv').config();

class EmailService {
    constructor() {
        this.transporter = null;
        this.emailsFilePath = path.join(__dirname, 'emails.json');
        this.initializeTransporter();
    }

    initializeTransporter() {
        try {
            this.transporter = nodemailer.createTransport({
                service: 'gmail',
                auth: {
                    user: process.env.EMAIL_USER,
                    pass: process.env.EMAIL_PASS
                },
                // Enable debugging
                debug: false,
                logger: false
            });

            // Verify connection configuration
            this.transporter.verify((error, success) => {
                if (error) {
                    console.error('❌ Email service configuration error:', error.message);
                    console.log('📧 Please check your EMAIL_USER and EMAIL_PASS in .env file');
                } else {
                    console.log('✅ Email service is ready to send messages');
                }
            });
        } catch (error) {
            console.error('❌ Failed to initialize email transporter:', error.message);
        }
    }

    async loadEmailData() {
        try {
            const data = await fs.readFile(this.emailsFilePath, 'utf8');
            return JSON.parse(data);
        } catch (error) {
            // If file doesn't exist or is corrupted, return default structure
            const defaultData = {
                userEmail: null,
                lastEmailSent: null,
                reminderCount: 0,
                createdAt: null,
                updatedAt: null
            };
            await this.saveEmailData(defaultData);
            return defaultData;
        }
    }

    async saveEmailData(data) {
        try {
            await fs.writeFile(this.emailsFilePath, JSON.stringify(data, null, 2));
        } catch (error) {
            console.error('❌ Failed to save email data:', error.message);
            throw error;
        }
    }

    async getUserEmail() {
        const data = await this.loadEmailData();
        return data.userEmail;
    }

    async setUserEmail(email) {
        const data = await this.loadEmailData();
        const now = new Date().toISOString();
        
        data.userEmail = email;
        data.updatedAt = now;
        
        if (!data.createdAt) {
            data.createdAt = now;
        }
        
        await this.saveEmailData(data);
        console.log(`📧 Email updated: ${email}`);
        return true;
    }

    async sendReminderEmail() {
        try {
            const userEmail = await this.getUserEmail();
            
            if (!userEmail) {
                console.log('⚠️  No user email configured. Skipping reminder.');
                return false;
            }

            if (!this.transporter) {
                console.error('❌ Email transporter not initialized');
                return false;
            }

            const now = new Date();
            const formattedDate = now.toLocaleDateString('en-US', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });

            const emailContent = this.generateReminderContent(formattedDate);

            const mailOptions = {
                from: {
                    name: 'Daily Reminder App',
                    address: process.env.EMAIL_USER
                },
                to: userEmail,
                subject: `Daily Reminder - ${formattedDate}`,
                html: emailContent,
                text: this.htmlToText(emailContent)
            };

            const info = await this.transporter.sendMail(mailOptions);
            
            // Update email data
            const data = await this.loadEmailData();
            data.lastEmailSent = now.toISOString();
            data.reminderCount += 1;
            data.updatedAt = now.toISOString();
            await this.saveEmailData(data);

            console.log(`✅ Reminder email sent successfully!`);
            console.log(`📧 To: ${userEmail}`);
            console.log(`📅 Date: ${formattedDate}`);
            console.log(`🔢 Total reminders sent: ${data.reminderCount}`);
            console.log(`📮 Message ID: ${info.messageId}`);
            
            return true;
        } catch (error) {
            console.error('❌ Failed to send reminder email:', error.message);
            return false;
        }
    }

    generateReminderContent(date) {
        return `
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Daily Reminder</title>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f9f9f9;
                }
                .container {
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                .header {
                    text-align: center;
                    color: #2c3e50;
                    border-bottom: 3px solid #3498db;
                    padding-bottom: 20px;
                    margin-bottom: 30px;
                }
                .content {
                    font-size: 16px;
                    line-height: 1.8;
                }
                .reminder-list {
                    background: #ecf0f1;
                    padding: 20px;
                    border-radius: 5px;
                    margin: 20px 0;
                }
                .reminder-list ul {
                    margin: 10px 0;
                    padding-left: 20px;
                }
                .reminder-list li {
                    margin: 8px 0;
                    color: #2c3e50;
                }
                .footer {
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #bdc3c7;
                    color: #7f8c8d;
                    font-size: 14px;
                }
                .quote {
                    font-style: italic;
                    color: #16a085;
                    text-align: center;
                    margin: 25px 0;
                    font-size: 18px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🌟 Daily Reminder</h1>
                    <p>${date}</p>
                </div>
                
                <div class="content">
                    <p>Good morning! 🌅</p>
                    
                    <p>This is your friendly daily reminder to help you stay on track with your goals and priorities.</p>
                    
                    <div class="reminder-list">
                        <h3>Today's Reminders:</h3>
                        <ul>
                            <li>💧 Drink at least 8 glasses of water</li>
                            <li>🏃‍♀️ Take a 30-minute walk or exercise</li>
                            <li>📚 Read for at least 20 minutes</li>
                            <li>🧘‍♀️ Practice mindfulness or meditation</li>
                            <li>📞 Connect with a friend or family member</li>
                            <li>📝 Write down 3 things you're grateful for</li>
                            <li>🎯 Work on your most important task first</li>
                        </ul>
                    </div>
                    
                    <div class="quote">
                        "The secret of getting ahead is getting started." - Mark Twain
                    </div>
                    
                    <p>Remember, small consistent actions lead to big results. You've got this! 💪</p>
                    
                    <p>Have a wonderful and productive day!</p>
                </div>
                
                <div class="footer">
                    <p>This is an automated reminder from your Daily Reminder App</p>
                    <p>Sent with ❤️ to help you achieve your goals</p>
                </div>
            </div>
        </body>
        </html>
        `;
    }

    htmlToText(html) {
        // Simple HTML to text conversion for email clients that don't support HTML
        return html
            .replace(/<[^>]*>/g, '')
            .replace(/&nbsp;/g, ' ')
            .replace(/&amp;/g, '&')
            .replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace(/\s+/g, ' ')
            .trim();
    }

    async getEmailStats() {
        const data = await this.loadEmailData();
        return {
            email: data.userEmail,
            lastSent: data.lastEmailSent,
            totalSent: data.reminderCount,
            createdAt: data.createdAt,
            updatedAt: data.updatedAt
        };
    }
}

module.exports = EmailService;