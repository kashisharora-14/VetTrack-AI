# PetHealth Pro

## Overview

PetHealth Pro is a comprehensive web-based pet health management application built with Flask that helps pet owners track their animals' wellness, monitor symptoms, and connect with veterinary care. The application integrates AI-powered diagnostics using Google's Gemini LLM for symptom analysis and photo-based health assessments, along with telemedicine capabilities through Jitsi Meet integration.

The platform provides pet profile management, health history tracking, AI-powered symptom checking, photo upload analysis, wellness reminders, and mock telemedicine consultations. It serves as a centralized hub for pet owners to maintain comprehensive health records and get preliminary health insights before consulting with veterinary professionals.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Server-side rendered HTML templates using Jinja2 templating engine
- **UI Framework**: Bootstrap 5.3.0 for responsive design and component styling
- **Icon Library**: Font Awesome 6.0.0 for iconography
- **JavaScript**: Vanilla JavaScript with modular approach, no heavy frontend frameworks
- **Video Integration**: Jitsi Meet external API for telemedicine consultations
- **Styling**: Custom CSS with CSS variables for theming and design consistency

### Backend Architecture
- **Framework**: Python Flask with Blueprint-based organization potential
- **Database ORM**: SQLAlchemy with DeclarativeBase for modern SQLAlchemy usage
- **Model Design**: Three core models (PetProfile, HealthHistory, Reminder) with proper relationships and cascading deletes
- **File Handling**: Werkzeug utilities for secure file uploads with size limits (16MB)
- **Session Management**: Flask sessions with configurable secret keys
- **Logging**: Python logging module with debug-level configuration
- **Middleware**: ProxyFix for proper header handling in production deployments

### Data Storage
- **Primary Database**: SQLite for development with PostgreSQL migration path via DATABASE_URL environment variable
- **ORM Configuration**: Connection pooling with 300-second recycle time and pre-ping health checks
- **File Storage**: Local filesystem storage in static/uploads directory for uploaded pet photos
- **Schema Design**: Relational model with foreign key constraints and proper indexing on primary keys

### AI Integration
- **LLM Service**: Google Gemini API integration for symptom analysis and image analysis
- **Structured Responses**: Pydantic models (SymptomAnalysis, ImageAnalysis) for type-safe API responses
- **Analysis Types**: Text-based symptom analysis and image-based health condition assessment
- **Response Format**: JSON-structured responses with diagnosis, urgency levels, recommendations, and possible causes

### Authentication & Security
- **Session Security**: Configurable session secret with environment variable fallback
- **File Security**: Werkzeug secure_filename for upload safety
- **Environment Configuration**: Environment variables for sensitive data (API keys, database URLs)
- **CORS Handling**: ProxyFix middleware for proper proxy header handling

## External Dependencies

### Core Framework Dependencies
- **Flask**: Web framework with SQLAlchemy integration
- **SQLAlchemy**: Database ORM with modern DeclarativeBase approach
- **Werkzeug**: WSGI utilities for security and file handling

### AI & Machine Learning
- **Google Gemini API**: LLM service for symptom analysis and image processing
- **Pydantic**: Data validation and parsing for AI response structures

### Frontend Libraries (CDN)
- **Bootstrap 5.3.0**: CSS framework for responsive UI components
- **Font Awesome 6.0.0**: Icon library for user interface elements
- **Jitsi Meet API**: Video conferencing integration for telemedicine features

### Development & Production
- **Python Logging**: Built-in logging for application monitoring
- **Environment Variables**: Configuration management for deployment flexibility
- **SQLite/PostgreSQL**: Database flexibility with environment-based switching

### File Upload Handling
- **Local File System**: Static file serving for uploaded pet photos
- **Werkzeug Security**: Secure filename handling and file type validation