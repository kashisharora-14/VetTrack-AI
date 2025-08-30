# 🐾 VetTrack AI - AI-Powered Pet Health Management System

A comprehensive Flask-based web application that combines artificial intelligence with veterinary care management, featuring AI-powered symptom analysis, photo diagnosis, and intelligent health tracking for pets.

## ✨ Features

### 🤖 AI-Powered Analysis
- **AI Symptom Checker**: Advanced symptom analysis using Gemini AI for accurate preliminary diagnoses
- **Photo Analysis**: Upload pet photos for AI-powered visual health assessment
- **Smart Diagnosis**: Machine learning-based condition likelihood and urgency assessment
- **Voice Integration**: Murf TTS API for audio playback of analysis results

### 🏥 Health Management
- **Pet Profiles**: Comprehensive pet information management (species, breed, age, medical notes)
- **Health History**: Detailed tracking of symptoms, diagnoses, and treatments
- **Urgency Assessment**: AI-powered urgency level classification (Low/Medium/High/Emergency)
- **Medical Records**: Export consultation summaries and health reports

### 📱 User Experience
- **Personalized Dashboard**: User-specific pet overview and health statistics
- **Voice Greetings**: Personalized TTS welcome messages upon login
- **Voice Reminder Notifications**: Audio announcements for pending pet care tasks
- **Smart Audio Management**: Prevents duplicate announcements and ensures complete voice playback
- **Responsive Design**: Mobile-friendly interface with Bootstrap 5
- **Real-time Updates**: Live health history and reminder tracking

### 🔔 Smart Notifications
- **Health Reminders**: Vaccination, medication, and checkup scheduling
- **Voice Reminder Announcements**: Murf TTS-powered voice notifications for pending pet reminders
- **Automatic Announcements**: Voice alerts when visiting dashboard or wellness pages
- **Manual Announcement Controls**: On-demand voice reminders with auto-redirect to wellness page
- **Urgency Alerts**: Immediate notifications for high-priority health concerns
- **Progress Tracking**: Completion status for health tasks and appointments

### 💬 Consultation System
- **Virtual Consultations**: Jitsi Meet integration for video calls with veterinarians
- **Health Summaries**: AI-generated consultation notes and recommendations
- **Professional Integration**: Share health history with veterinary professionals

## 🚀 Technology Stack

### Backend
- **Flask 3.1.2**: Modern Python web framework
- **SQLAlchemy 2.0.43**: Database ORM and management
- **SQLite**: Lightweight database (configurable for production)
- **Python 3.11+**: Core programming language

### AI & External APIs
- **Google Gemini AI**: Advanced symptom analysis and diagnosis
- **Murf TTS API**: High-quality text-to-speech for accessibility
- **Jitsi Meet**: Video consultation platform integration

### Frontend
- **Bootstrap 5.3.0**: Responsive CSS framework
- **Font Awesome 6.0.0**: Icon library
- **Vanilla JavaScript**: Modern ES6+ features
- **HTML5**: Semantic markup

### Security & Authentication
- **Flask-Login**: User session management
- **Password Hashing**: Secure credential storage
- **Session Management**: Secure user authentication

## 📋 Prerequisites

- Python 3.11 or higher
- pip package manager
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Internet connection for AI APIs

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/vettrack-ai.git
cd vettrack-ai
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file in the project root:
```env
# Required API Keys
GOOGLE_API_KEY=your_gemini_api_key_here
MURF_API_KEY=your_murf_tts_api_key_here

# Optional: Database Configuration
DATABASE_URL=sqlite:///instance/pet_health.db

# Optional: Session Security
SESSION_SECRET=your_secure_session_secret_here
```

### 5. Initialize Database
```bash
python main.py
```
The database will be automatically created on first run.

## 🚀 Running the Application

### Development Mode
```bash
python main.py
```
The application will be available at `http://127.0.0.1:5000`

### Production Mode
```bash
# Set environment variables
export FLASK_ENV=production
export FLASK_APP=main.py

# Run with production server
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

## 📱 Usage Guide

### Getting Started
1. **Sign Up**: Create a new account with your email and password
2. **Add Pets**: Register your pets with species, breed, age, and medical notes
3. **Access Dashboard**: View your pets' health overview and quick actions

### AI Symptom Checker
1. Select a pet from your profile
2. Describe symptoms in detail (or use quick-select checkboxes)
3. Receive AI-powered analysis with:
   - Preliminary diagnosis
   - Urgency level assessment
   - Treatment recommendations
   - Possible causes
   - Audio playback of results

### Photo Analysis
1. Upload a clear photo of the health concern
2. Add optional description for context
3. Get AI visual analysis including:
   - Condition likelihood
   - Severity assessment
   - Urgency classification
   - Professional recommendations

### Health Management
- **Track History**: Monitor symptoms, treatments, and outcomes
- **Set Reminders**: Schedule vaccinations, medications, and checkups
- **Export Reports**: Generate consultation summaries for veterinarians

### Voice Reminder System
1. **Automatic Announcements**: 
   - Dashboard announces pending reminders 3 seconds after page load
   - Wellness page announces pending reminders 1 second after page load
   - Voice includes count of overdue and upcoming reminders with specific task details

2. **Manual Announcement Controls**:
   - Click "Announce & Go to Wellness" button on dashboard for immediate voice feedback
   - Button automatically redirects to wellness page after announcement completes
   - Visual feedback shows announcement progress and redirect status

3. **Voice Confirmations**:
   - Hear confirmation when completing reminders: "Reminder completed successfully!"
   - Hear confirmation when adding new reminders: "Reminder added successfully!"
   - Error handling with voice feedback for failed operations

4. **Smart Audio Management**:
   - Prevents duplicate announcements
   - Waits for complete voice playback before redirecting
   - Stops overlapping audio to ensure clear announcements

## 🔧 Configuration

### API Keys Setup

#### Google Gemini AI
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add to your `.env` file as `GOOGLE_API_KEY`

#### Murf TTS API
1. Sign up at [Murf AI](https://murf.ai/api)
2. Generate your API key
3. Add to your `.env` file as `MURF_API_KEY`

### Database Configuration
- **Default**: SQLite database in `instance/pet_health.db`
- **Production**: Set `DATABASE_URL` in `.env` for PostgreSQL/MySQL
- **Backup**: Database files are automatically created and managed

## 📊 Project Structure
```
vettrack-ai/
├── app.py                 # Main Flask application
├── main.py               # Application entry point
├── models.py             # Database models and schemas
├── gemini.py             # AI integration module
├── requirements.txt      # Python dependencies
├── .env                  # Environment configuration
├── static/               # Static assets
│   ├── css/             # Stylesheets
│   ├── js/              # JavaScript files
│   └── uploads/         # User-uploaded images
├── templates/            # HTML templates
│   ├── dashboard.html   # Main dashboard
│   ├── symptom.html     # Symptom checker
│   ├── image.html       # Photo analysis
│   └── ...              # Other pages
└── instance/            # Database and uploads
```

## 🔒 Security Features

- **Password Hashing**: Secure bcrypt-based password storage
- **Session Management**: Secure user authentication
- **Input Validation**: Comprehensive form validation and sanitization
- **File Upload Security**: Secure image handling with size limits
- **SQL Injection Protection**: Parameterized database queries

## 🌐 API Endpoints

### Authentication
- `POST /signup` - User registration
- `POST /login` - User authentication
- `GET /logout` - User logout

### Pet Management
- `GET /api/get_pets` - Retrieve user's pets
- `POST /api/add_pet` - Add new pet profile
- `GET /api/pet/<id>/recent-history` - Pet health history

### AI Analysis
- `POST /api/check_symptoms` - Symptom analysis
- `POST /api/upload_image` - Photo analysis
- `POST /api/get_diagnosis_explanation` - Detailed diagnosis info

### TTS Integration
- `POST /api/tts_generate` - Generate speech from text
- `GET /api/tts_status` - Check TTS service status

### Health Management
- `GET /api/get_health_history` - User's health records
- `GET /api/get_reminders` - User's health reminders
- `POST /api/add_reminder` - Create new health reminder
- `POST /api/complete_reminder/<id>` - Mark reminder as completed

## 🧪 Testing

### Manual Testing
1. **User Registration**: Test signup and login flows
2. **Pet Management**: Add, edit, and view pet profiles
3. **AI Features**: Test symptom checker and photo analysis
4. **TTS Integration**: Verify audio playback functionality
5. **Voice Reminders**: Test automatic and manual reminder announcements
6. **Reminder Management**: Test adding, completing, and voice confirmations

### API Testing
```bash
# Test TTS endpoint
curl -X POST http://localhost:5000/api/tts_generate \
  -H "Content-Type: application/json" \
  -d '{"text":"Test message"}'

# Test symptom checker
curl -X POST http://localhost:5000/api/check_symptoms \
  -H "Content-Type: application/json" \
  -d '{"pet_id":1,"symptoms":"lethargy, loss of appetite"}'
```

## 🚀 Deployment

### Local Development
```bash
python main.py
```

### Production Deployment
1. **Set Environment Variables**:
   ```bash
   export FLASK_ENV=production
   export DATABASE_URL=postgresql://user:pass@localhost/vettrack
   ```

2. **Use Production Server**:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 main:app
   ```

3. **Reverse Proxy** (Nginx):
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;
       
       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 Python style guidelines
- Add comprehensive docstrings for new functions
- Include error handling for all API endpoints
- Test new features thoroughly before submitting

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google Gemini AI** for advanced natural language processing
- **Murf AI** for high-quality text-to-speech capabilities
- **Bootstrap** for responsive UI components
- **Flask** community for the excellent web framework

## 📞 Support

- **Issues**: Report bugs and feature requests via GitHub Issues
- **Documentation**: Check this README and inline code comments
- **Community**: Join discussions in GitHub Discussions

## 🔮 Future Enhancements

- **Mobile App**: Native iOS/Android applications
- **Machine Learning**: Enhanced diagnosis accuracy with custom models
- **Telemedicine**: Direct integration with veterinary services
- **Health Monitoring**: IoT device integration for continuous monitoring
- **Multi-language Support**: Internationalization for global users
- **Advanced Analytics**: Health trend analysis and predictive insights
- **Voice Reminder Enhancements**: 
  - User-configurable voice preferences
  - Scheduled daily reminder announcements
  - Push notifications with voice support
  - Voice selection options for different languages

---

**VetTrack AI** - Empowering pet owners with AI-driven health insights 🐾✨

*Built with ❤️ for the pet care community* 