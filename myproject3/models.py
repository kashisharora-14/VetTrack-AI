
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    pets = db.relationship('PetProfile', backref='owner', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class PetProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # <-- link to User
    name = db.Column(db.String(100), nullable=False)
    species = db.Column(db.String(50), nullable=False)
    breed = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    weight_kg = db.Column(db.Float, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    medical_notes = db.Column(db.Text)
    profile_picture = db.Column(db.String(255), nullable=True)  # store filename
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    health_history = db.relationship('HealthHistory', backref='pet', lazy=True, cascade='all, delete-orphan')
    reminders = db.relationship('Reminder', backref='pet', lazy=True, cascade='all, delete-orphan')
    consultations = db.relationship('Consultation', back_populates='pet', lazy=True, cascade='all, delete-orphan')

  
class Consultation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pet_id = db.Column(db.Integer, db.ForeignKey('pet_profile.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    summary = db.Column(db.Text, nullable=False)
    
    # Relationships
    pet = db.relationship('PetProfile', back_populates='consultations')
    user = db.relationship('User', backref='consultations')



class HealthHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pet_id = db.Column(db.Integer, db.ForeignKey('pet_profile.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    symptoms = db.Column(db.Text, nullable=False)
    diagnosis = db.Column(db.Text)
    recommendation = db.Column(db.Text)
    urgency_level = db.Column(db.String(50))  # e.g., Low, Medium, High
    possible_causes = db.Column(db.Text) 


class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pet_id = db.Column(db.Integer, db.ForeignKey('pet_profile.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    completed_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# Hardcoded Veterinary Clinics Data
VETERINARY_CLINICS = [
    {
        'id': 1,
        'name': 'The Paws Clinic & Spa',
        'address': '98 Willow Creek Rd • 1.2 miles',
        'phone': '+92 123-4567890',
        'rating': 4.7,
        'review_count': 89,
        'is_open': True,
        'image': 'clinic1.jpg'
    },
    {
        'id': 2,
        'name': 'City Veterinary Care',
        'address': '432 Metro Plaza, Suite 4 • 2.5 miles',
        'phone': '+92 123-4567891',
        'rating': 4.9,
        'review_count': 234,
        'is_open': False,
        'image': 'clinic2.jpg'
    },
    {
        'id': 3,
        'name': 'Healthy Tails 24/7',
        'address': 'Emergency Lane, Medical District • 3.1 miles',
        'phone': '+92 123-4567892',
        'rating': 4.8,
        'review_count': 342,
        'is_open': True,
        'image': 'clinic3.jpg'
    },
    {
        'id': 4,
        'name': 'Gentle Breeze Vet',
        'address': '19 Oak Avenue • 3.8 miles',
        'phone': '+92 123-4567893',
        'rating': 4.6,
        'review_count': 156,
        'is_open': True,
        'image': 'clinic4.jpg'
    }
]
