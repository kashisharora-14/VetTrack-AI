# VetTrack AI - Replit Agent Guide

## Overview

VetTrack AI is a Flask-based web application for pet health management. It combines AI-powered symptom analysis and photo diagnosis with traditional health tracking features like pet profiles, health history, reminders, and virtual veterinary consultations.

The core value proposition is helping pet owners get preliminary health assessments using Google's Gemini AI before consulting professional veterinarians, with Murf TTS providing voice-based accessibility features.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Application Structure
- **Framework**: Flask 3.1.2 with Flask-Login for authentication and Flask-SQLAlchemy for database operations
- **Entry Points**: `app.py` contains the main Flask application; `main.py` serves as a simple runner script
- **Project Location**: Main application code lives in `myproject3/` directory

### Database Design
- **ORM**: SQLAlchemy 2.0 with SQLite as the default database
- **Models** (`models.py`):
  - `User` - Authentication with password hashing via Werkzeug
  - `PetProfile` - Pet information linked to users (one-to-many)
  - `HealthHistory` - Symptom/diagnosis records linked to pets
  - `Reminder` - Scheduled health tasks per pet
  - `Consultation` - Virtual vet consultation records
- **Relationships**: Users own multiple pets; pets have health history, reminders, and consultations with cascade delete

### AI Integration (`gemini.py`)
- **Symptom Analysis**: Sends pet info and symptoms to Gemini API, returns structured diagnosis with urgency levels
- **Image Analysis**: Processes uploaded pet photos for visual health assessment
- **Response Format**: Pydantic models (`SymptomAnalysis`, `ImageAnalysis`) define expected JSON structure from Gemini

### Frontend Architecture
- **Templating**: Jinja2 templates in `templates/` directory
- **Styling**: Bootstrap 5 with custom CSS (`static/css/style.css`)
- **JavaScript**: Shared utilities in `static/js/app.js` including TTS audio handling
- **Key Pages**: Dashboard, symptom checker, image analysis, wellness tracker, consultation (with Jitsi Meet integration), health history

### Authentication Flow
- Flask-Login manages user sessions
- Password hashing via Werkzeug security utilities
- Session-based authentication with login_required decorators

## External Dependencies

### AI Services
- **Google Gemini AI** (`gemini-2.5-flash`): Primary AI for symptom analysis and image diagnosis. Requires `GEMINI_API_KEY` environment variable.
- **Murf TTS API**: Text-to-speech for voice greetings and reminder announcements. Requires `MURF_API_KEY` environment variable.

### Video Conferencing
- **Jitsi Meet**: Embedded video consultations via external API script (`meet.jit.si/external_api.js`)

### Environment Variables
Required in `.env` file:
- `SECRET_KEY` - Flask session secret
- `GEMINI_API_KEY` - Google Gemini API access
- `MURF_API_KEY` - Murf TTS API access
- `DATABASE_URL` - Database connection (defaults to `sqlite:///pet_health.db`)

### PDF Generation
- **ReportLab**: Used for generating exportable health reports and consultation summaries