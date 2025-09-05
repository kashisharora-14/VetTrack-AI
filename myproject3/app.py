import os
import logging
import uuid
import sqlite3
import traceback
import random
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
import string
from flask_login import login_required, LoginManager, login_user, logout_user, current_user
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
import base64
import requests
from dotenv import load_dotenv

# Support both package and script execution contexts
try:
    from .models import db, User, PetProfile, HealthHistory, Reminder, Consultation
except ImportError:  # when run as a script (python app.py)
    from models import db, User, PetProfile, HealthHistory, Reminder, Consultation

try:
    from .gemini import (
        analyze_pet_symptoms,
        analyze_pet_image,
        get_diagnosis_explanation_from_gemini,
    )
except ImportError:  # when run as a script
    from gemini import (
        analyze_pet_symptoms,
        analyze_pet_image,
        get_diagnosis_explanation_from_gemini,
    )

# Setup logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Load .env so MURF_API_KEY and others are available locally
load_dotenv()

# Create Flask app
app = Flask(__name__)
# Upload folder (inside static) - ensure absolute path
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')

app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

instance_dir = os.path.join(os.path.dirname(__file__), "instance")
os.makedirs(instance_dir, exist_ok=True)


# app.config["UPLOAD_FOLDER"] = instance_dir
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # Limit uploads to 16MB


# Database configuration
# Prefer DATABASE_URL if set (for production), otherwise use local SQLite file with an absolute, OS-safe path
env_db = os.environ.get("DATABASE_URL")
if env_db and "memory" not in env_db:
    app.config["SQLALCHEMY_DATABASE_URI"] = env_db
else:
    abs_db_path = os.path.abspath(os.path.join(instance_dir, "pet_health.db"))
    # Normalize backslashes on Windows so SQLAlchemy parses correctly
    sqlite_uri = "sqlite:///" + abs_db_path.replace("\\", "/")
    app.config["SQLALCHEMY_DATABASE_URI"] = sqlite_uri

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_recycle": 300, "pool_pre_ping": True}

# Debug print (helpful for checking which DB is used)
print("=== DATABASE CONFIG ===")
print("Instance dir:", instance_dir)
print("SQLALCHEMY_DATABASE_URI:", app.config["SQLALCHEMY_DATABASE_URI"])
print("=======================")


# Initialize SQLAlchemy
db.init_app(app)

# Ensure tables exist without deleting existing data
with app.app_context():
    db.create_all()


# =====================
# ROUTES
# =====================
def get_current_user():
    """Helper function to get current logged in user"""
    if 'user_id' not in session:
        return None
    try:
        return User.query.get(session['user_id'])
    except:
        session.clear()  # Clear invalid session
        return None

@app.route("/")
def index():
    user = get_current_user()
    return render_template("index.html", user=user)


import json

@app.route('/dashboard')
def dashboard():
    user = get_current_user()
    if not user:
        flash("Please log in first", "danger")
        return redirect(url_for("login"))

    user_id = user.id

    pets = PetProfile.query.filter_by(user_id=user_id).all()
    pet_ids = [pet.id for pet in pets]

    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 5  # Show 5 records per page

    # Get paginated health history - ordered by most recent first (id desc for latest entries)
    health_history_query = HealthHistory.query.filter(
        HealthHistory.pet_id.in_(pet_ids)
    ).order_by(HealthHistory.id.desc(), HealthHistory.date.desc())

    pagination = health_history_query.paginate(
        page=page, per_page=per_page, error_out=False
    )

    health_history = pagination.items

    data = []
    for h in health_history:
        pet = next((p for p in pets if p.id == h.pet_id), None)

        # ✅ Ensure possible_causes is always a list
        causes = h.possible_causes
        if isinstance(causes, str):
            try:
                causes = json.loads(causes)  # If stored as JSON string
            except json.JSONDecodeError:
                causes = [c.strip() for c in causes.split(",") if c.strip()]

        # ✅ Ensure diagnosis is always a list
        diagnosis = h.diagnosis
        if isinstance(diagnosis, str):
            try:
                diagnosis = json.loads(diagnosis)  # If stored as JSON string
            except json.JSONDecodeError:
                diagnosis = [d.strip() for d in diagnosis.split(",") if d.strip()]

        data.append({
            'id': h.id,
            'pet_id': h.pet_id,
            'pet_name': pet.name if pet else "Unknown",
            'date': h.date,
            'symptoms': h.symptoms,
            'diagnosis': diagnosis,            # ✅ Fixed
            'recommendation': h.recommendation,
            'urgency_level': h.urgency_level,
            'possible_causes': causes          # ✅ Already fixed
        })

    return render_template('dashboard.html',
                           health_history=data,
                           pagination=pagination,
                           user=user)


@app.route('/export_summary/<int:consultation_id>')
def export_summary(consultation_id):
    # Fetch consultation
    consultation = Consultation.query.get_or_404(consultation_id)
    pet = consultation.pet

    # Create text content
    lines = []
    lines.append("VETERINARY CONSULTATION SUMMARY\n")
    lines.append(f"Pet: {pet.name} ({pet.species} • {pet.breed} • {pet.age} years)")
    lines.append(f"Date: {consultation.date.strftime('%m/%d/%Y')}\n")

    # Consultation notes
    lines.append("CONSULTATION NOTES:")
    notes = consultation.summary if consultation.summary else "No notes recorded"
    lines.extend(notes.splitlines())
    lines.append("")  # blank line

    # Medical history
    lines.append("MEDICAL HISTORY:")
    if pet.health_history:
        for record in pet.health_history:
            lines.append(f"Date: {record.date.strftime('%m/%d/%Y')}")
            lines.append(f"Symptoms: {record.symptoms}")
            if record.diagnosis:
                lines.append(f"Diagnosis: {record.diagnosis}")
            if record.recommendation:
                lines.append(f"Recommendation: {record.recommendation}")
            lines.append("")  # space between records
    else:
        lines.append("No previous medical notes")

    lines.append("Generated by VetTrack Ai")

    # Convert to bytes
    content = "\n".join(lines)
    buffer = BytesIO()
    buffer.write(content.encode('utf-8'))
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"{pet.name}_consultation.txt",
        mimetype='text/plain'
    )



@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for("index"))




@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        full_name = request.form.get("fullName")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirmPassword")

        if not full_name or not email or not password:
            return render_template("signup.html", error="All fields are required",
                                   full_name=full_name, email=email)

        if password != confirm_password:
            return render_template("signup.html", error="Passwords do not match",
                                   full_name=full_name, email=email)

        if User.query.filter_by(email=email).first():
            return render_template("signup.html", error="Email already registered",
                                   full_name=full_name, email=email)

        try:
            new_user = User(full_name=full_name, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            return render_template("signup.html", success="Account created successfully")
        except Exception as e:
            db.session.rollback()
            return render_template("signup.html", error=f"Database error: {str(e)}",
                                   full_name=full_name, email=email)

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            # Store user name in session for TTS greeting
            session['user_name'] = user.full_name
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", login_error="Invalid email or password")

    return render_template("login.html")




@app.route('/symptom')
def symptom():
    if 'user_id' not in session:
        flash("Please log in to access the symptom checker", "warning")
        return redirect(url_for("login"))
    return render_template('symptom.html')


@app.route('/image')
def image():
    if 'user_id' not in session:
        flash("Please log in to access photo analysis", "warning")
        return redirect(url_for("login"))
    return render_template('image.html')


@app.route('/history')
def history():
    if 'user_id' not in session:
        flash("Please log in to access health history", "warning")
        return redirect(url_for("login"))

    user_id = session['user_id']
    user = User.query.get(user_id)
    pets = PetProfile.query.filter_by(user_id=user_id).all()

    return render_template('history.html', user=user, pets=pets)


@app.route('/wellness')
def wellness():
    if 'user_id' not in session:
        flash("Please log in to access wellness features", "warning")
        return redirect(url_for("login"))
    return render_template('wellness.html')


# @app.route('/consultation/<pet_id>')
# def consultation(pet_id):
#     pet = PetProfile.query.get_or_404(pet_id)
#     room_id = str(uuid.uuid4())
#     return render_template('consultation.html', pet=pet, room_id=room_id)

# =====================
# API ROUTES
# =====================

@app.route('/api/get_diagnosis_explanation', methods=['POST'])
def get_diagnosis_explanation():
    """Get detailed explanation for a specific diagnosis using Gemini AI"""
    try:
        data = request.get_json()
        diagnosis = data.get('diagnosis', '').strip()

        logging.info(f"Getting explanation for diagnosis: '{diagnosis}'")

        if not diagnosis:
            return jsonify({'success': False, 'error': 'Diagnosis name is required'})

        # Skip warning messages
        if diagnosis.lower().startswith('warning') or '⚠' in diagnosis:
            return jsonify({'success': False, 'error': 'Cannot explain warning messages'})

        explanation = get_diagnosis_explanation_from_gemini(diagnosis)

        logging.info(f"Generated explanation: {explanation}")

        # Ensure we always have valid content
        if not explanation or not explanation.get('description'):
            logging.warning("Empty explanation from Gemini, using fallback")
            from gemini import get_fallback_explanation
            explanation = get_fallback_explanation(diagnosis)

        return jsonify({
            'success': True,
            'explanation': explanation
        })

    except Exception as e:
        logging.error(f"Error getting diagnosis explanation: {e}")
        logging.error(traceback.format_exc())

        # Return fallback explanation instead of just error
        try:
            from gemini import get_fallback_explanation
            diagnosis_name = data.get('diagnosis', 'Unknown condition') if 'data' in locals() else 'Unknown condition'
            fallback_explanation = get_fallback_explanation(diagnosis_name)
            return jsonify({
                'success': True,
                'explanation': fallback_explanation
            })
        except Exception as fallback_error:
            logging.error(f"Fallback explanation also failed: {fallback_error}")
            # Return a basic fallback response instead of complete failure
            return jsonify({
                'success': True,
                'explanation': {
                    'description': f'{diagnosis_name} is a condition that may affect your pet. For accurate diagnosis and treatment, please consult with a qualified veterinarian.',
                    'causes': ['Various factors may contribute to this condition'],
                    'symptoms': ['Symptoms may vary depending on the severity and individual pet']
                }
            })


@app.route('/api/tts_generate', methods=['POST'])
def tts_generate():
    """Generate TTS audio using Murf API and return base64 audio for playback."""
    try:
        data = request.get_json(silent=True) or {}
        text = (data.get('text') or '').strip()
        voice_id = data.get('voice_id') or 'en-US-natalie'
        audio_format = data.get('format') or 'MP3'

        if not text:
            return jsonify({'success': False, 'error': 'Text is required'}), 400

        murf_api_key = os.environ.get('MURF_API_KEY')
        if not murf_api_key:
            return jsonify({'success': False, 'error': 'MURF_API_KEY not configured on server'}), 500

        murf_url = 'https://api.murf.ai/v1/speech/generate'
        headers = {
            'Content-Type': 'application/json',
            'api-key': murf_api_key
        }
        payload = {
            'text': text,
            'voiceId': voice_id,
            'format': audio_format,
            'sampleRate': 24000
        }

        murf_resp = requests.post(murf_url, headers=headers, json=payload, timeout=30)
        if murf_resp.status_code != 200:
            return jsonify({'success': False, 'error': f'Murf error: {murf_resp.text}'}), 502

        murf_json = murf_resp.json()
        audio_file_url = murf_json.get('audioFile') or murf_json.get('audio_file')
        if not audio_file_url:
            return jsonify({'success': False, 'error': 'No audio file URL returned by Murf'}), 502

        audio_resp = requests.get(audio_file_url, timeout=30)
        if audio_resp.status_code != 200:
            return jsonify({'success': False, 'error': 'Failed to download audio from Murf'}), 502

        audio_bytes = audio_resp.content
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

        mime = 'audio/mpeg' if audio_format.upper() in ['MP3', 'MPEG', 'MPG'] else 'audio/wav'
        return jsonify({'success': True, 'audio_b64': audio_b64, 'mime': mime})
    except Exception as e:
        logging.error(f"Error generating TTS: {e}")
        logging.error(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tts_status', methods=['GET'])
def tts_status():
    try:
        key_present = bool(os.environ.get('MURF_API_KEY'))
        return jsonify({'success': True, 'murf_key_present': key_present})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/clear_welcome_session', methods=['POST'])
def clear_welcome_session():
    """Clear the welcome session after TTS greeting"""
    try:
        if 'user_name' in session:
            del session['user_name']
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/api/pet/<int:pet_id>/recent-history", methods=["GET"])
def get_recent_history(pet_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'User not logged in'}), 401

    # ensure the pet belongs to the logged in user
    pet = PetProfile.query.filter_by(id=pet_id, user_id=session['user_id']).first()
    if not pet:
        return jsonify({'success': False, 'error': 'Pet not found'}), 404

    try:
        limit = request.args.get("limit", default=5, type=int)
        entries = (HealthHistory.query
                   .filter_by(pet_id=pet_id)
                   .order_by(HealthHistory.date.desc())
                   .limit(limit)
                   .all())

        data = [{
         'id': e.id,
         'date': e.date.isoformat(),
         'symptoms': e.symptoms,
         'diagnosis': e.diagnosis,
         'recommendation': e.recommendation,
         'urgency_level': e.urgency_level,
          'possible_causes': e.possible_causes.split(", ") if e.possible_causes else []
         } for e in entries]


        return jsonify({'success': True, 'health_history': data})
    except Exception as e:
        logging.exception("Error fetching recent history")
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route("/test_gemini")
def test_gemini():
    try:
        from google import genai
        # Ensure your Gemini API key is set as an environment variable
        # For local development, you can set it directly here or use a .env file
        # export GOOGLE_API_KEY='YOUR_API_KEY'
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return "Error: GEMINI_API_KEY not set. Please set it in your environment variables.", 500

        client = genai.Client(api_key=api_key)

        resp = client.models.generate_content(
            model="gemini-2.5-pro",
            contents="Hello Gemini, just reply with 'ok'."
        )

        return resp.text if hasattr(resp, "text") else str(resp)

    except Exception as e:
        logging.error(f"Error testing Gemini: {e}")
        return f"Error: {str(e)}", 500


@app.route('/api/get_history')
def get_history():
    pet_id = request.args.get('pet_id', type=int)
    if not pet_id:
        return jsonify({"success": False, "history": [], "error": "pet_id is required"}), 400

    history = HealthHistory.query.filter_by(pet_id=pet_id).all()

    if not history:
        return jsonify({"success": True, "history": []})  # return empty list if no history

    # Serialize history records
    history_list = []
    for h in history:
      history_list.append({
     "id": h.id,
     "date": h.date.isoformat(),
     "symptoms": h.symptoms,
     "diagnosis": h.diagnosis,
     "recommendation": h.recommendation,
     "urgency_level": h.urgency_level,
     "possible_causes": h.possible_causes.split(", ") if h.possible_causes else []

    })


    return jsonify({"success": True, "history": history_list})


    return jsonify([
        {
            "date": h.date.strftime("%Y-%m-%d"),
            "symptoms": h.symptoms,
            "diagnosis": h.diagnosis,
            "recommendation": h.recommendation
        } for h in history
    ])




@app.route('/api/add_pet', methods=['POST'])
def add_pet():
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'User not logged in'}), 401

        user_id = session['user_id']

        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
            profile_picture = None
        else:
            data = request.form.to_dict()
            profile_picture = request.files.get('profile_picture')

        # Handle profile picture upload
        profile_picture_filename = None
        if profile_picture and profile_picture.filename:
            filename = secure_filename(f"{uuid.uuid4()}_{profile_picture.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            profile_picture.save(filepath)          
            profile_picture_filename = f"static/uploads/{filename}"

        pet = PetProfile(
            user_id=user_id,
            name=data['name'],
            species=data['species'],
            breed=data['breed'],
            age=int(data['age']),
            medical_notes=data.get('medical_notes', ''),
            profile_picture=profile_picture_filename
        )
        db.session.add(pet)
        db.session.commit()

        return jsonify({'success': True, 'pet': {
            'id': pet.id,
            'name': pet.name,
            'species': pet.species,
            'breed': pet.breed,
            'age': pet.age,
            'medical_notes': pet.medical_notes,
            'profile_picture': pet.profile_picture
        }})
    except Exception as e:
        logging.error(f"Error adding pet: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/consultation/<pet_id>')
def consultation(pet_id):
    if 'user_id' not in session:
        flash("Please log in first", "danger")
        return redirect(url_for("login"))

    pet = PetProfile.query.filter_by(id=pet_id, user_id=session['user_id']).first_or_404()

    # Create a new consultation entry
    consultation = Consultation(pet_id=pet.id, user_id=session['user_id'], summary="")
    db.session.add(consultation)
    db.session.commit()

    room_id = str(uuid.uuid4())

    return render_template(
        'consultation.html',
        pet=pet,
        consultation=consultation,
        room_id=room_id
    )


@app.route('/api/get_pets', methods=['GET'])
def get_pets():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'User not logged in'}), 401

    user_id = session['user_id']
    pets = PetProfile.query.filter_by(user_id=user_id).all()
    pets_data = [{
        'id': pet.id,
        'name': pet.name,
        'species': pet.species,
        'breed': pet.breed,
        'age': pet.age,
        'medical_notes': pet.medical_notes,
        'profile_picture': pet.profile_picture
    } for pet in pets]

    return jsonify({'success': True, 'pets': pets_data})
@app.route('/api/save_consultation_notes', methods=['POST'])
def save_consultation_notes():
    # Check login
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'User not logged in'}), 401

    # Safely parse incoming JSON
    data = request.get_json(silent=True) or {}
    consultation_id = data.get('consultation_id')
    notes = (data.get('notes') or '').strip()

    # Validate consultation_id
    if not consultation_id:
        return jsonify({'success': False, 'error': 'Missing consultation_id'}), 400

    consultation = Consultation.query.get(consultation_id)
    if not consultation:
        return jsonify({'success': False, 'error': 'Consultation not found'}), 404

    # Security: ensure the logged-in user owns this consultation
    if consultation.user_id != session['user_id']:
        return jsonify({'success': False, 'error': 'Not authorized to modify this consultation'}), 403

    # Invalid summary phrases
    invalid_phrases = {
        "unable to generate summary at this time"
    }

    # Strict checks: block if empty or matches any invalid phrase
    if not notes or notes.lower() in invalid_phrases:
        return jsonify({'success': False, 'error': 'Empty or invalid summary — not saved'}), 400

    # Save only valid notes
    consultation.summary = notes
    try:
        db.session.commit()
        return jsonify({'success': True, 'message': 'Summary saved successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Database error: {str(e)}'}), 500

@app.route('/api/check_symptoms', methods=['POST'])
def check_symptoms():
    try:
        data = request.get_json()
        pet_id = data['pet_id']
        symptoms = data['symptoms']

        pet = PetProfile.query.get(pet_id)
        if not pet:
            return jsonify({'success': False, 'error': 'Pet not found'}), 404

        # Call AI analysis
        analysis = analyze_pet_symptoms(pet, symptoms)

        # Ensure diagnosis is a list
        diagnosis = analysis.get("diagnosis")
        if isinstance(diagnosis, str):
            diagnosis = [diagnosis]
        elif not isinstance(diagnosis, list):
            diagnosis = []

        # Filter out empty or meaningless entries
        diagnosis = [
            str(d).strip() for d in diagnosis
            if str(d).strip().lower() not in ["unable to analyze symptoms", "unknown", ""]
        ]

        if not diagnosis:
            logging.warning("Empty or invalid AI diagnosis — not saving to DB.")
            return jsonify({'success': False, 'error': 'Empty or invalid AI analysis result'}), 400

        # Put cleaned diagnosis back into analysis
        analysis["diagnosis"] = diagnosis

        # Ensure possible_causes is a list
        possible_causes = analysis.get("possible_causes", [])
        if isinstance(possible_causes, str):
            possible_causes = [possible_causes]

        # Save to DB
        history_entry = HealthHistory(
            pet_id=pet_id,
            date=datetime.utcnow(),
            symptoms=symptoms,
            diagnosis=json.dumps(diagnosis),  # store list as JSON string
            recommendation=analysis.get('recommendation', "Please consult with a veterinarian"),
            urgency_level=analysis.get('urgency_level', "Unknown"),
            possible_causes=json.dumps(possible_causes) if possible_causes else None
        )

        db.session.add(history_entry)
        db.session.commit()

        # Return analysis to frontend
        return jsonify({
            'success': True,
            'analysis': {
                'diagnosis': diagnosis,
                'urgency_level': history_entry.urgency_level,
                'recommendation': history_entry.recommendation,
                'possible_causes': possible_causes
            }
        })

    except Exception as e:
        logging.error(f"Error checking symptoms: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

from datetime import datetime, timedelta

@app.route("/api/pet/<int:pet_id>/full-history", methods=["GET"])
def get_full_history(pet_id):
    pet = PetProfile.query.get_or_404(pet_id)
    today = datetime.utcnow()

    timeline = []

    # Health (last 30 days or urgent)
    for h in pet.health_history:
        if (h.date >= today - timedelta(days=30)) or (h.urgency_level and h.urgency_level.lower() == "high"):
            timeline.append({
                "type": "health",
                "id": h.id,
                "date": h.date.isoformat(),
                "symptoms": h.symptoms,
                "diagnosis": h.diagnosis,
                "recommendation": h.recommendation,
                "urgency_level": h.urgency_level,
                "possible_causes": h.possible_causes.split(", ") if h.possible_causes else [],
                "summary": None,
            })

    # Consultations (last 60 days)
    if hasattr(pet, "consultations"):
        for c in pet.consultations:
            if c.date >= today - timedelta(days=60):
                timeline.append({
                    "type": "consultation",
                    "id": c.id,
                    "date": c.date.isoformat(),
                    "summary": c.summary,
                })

    # Reminders (upcoming or completed in last 7 days)
    for r in pet.reminders:
        if (r.due_date >= today) or (r.completed and r.due_date >= today - timedelta(days=7)):
            timeline.append({
                "type": "reminder",
                "id": r.id,
                "date": r.due_date.isoformat(),
                "title": r.title,
                "completed": r.completed,
            })

    # Sort by date descending
    timeline.sort(key=lambda x: x["date"], reverse=True)

    return jsonify({
        "pet": {
            "id": pet.id,
            "name": pet.name,
            "species": pet.species,
            "breed": pet.breed,
            "age": pet.age
        },
        "timeline": timeline
    })





@app.route('/api/get_health_history')
def get_health_history():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'User not logged in'}), 401

    user_id = session['user_id']
    histories = HealthHistory.query.join(PetProfile).filter(PetProfile.user_id == user_id).order_by(HealthHistory.date.desc()).all()

    data = [{
    'id': h.id,
    'pet_id': h.pet_id,
    'date': h.date.isoformat(),
    'symptoms': h.symptoms,
    'diagnosis': h.diagnosis,
    'recommendation': h.recommendation,
    'urgency_level': h.urgency_level,
    'possible_causes': h.possible_causes.split(", ") if h.possible_causes else []
    } for h in histories]


    return jsonify({'success': True, 'health_history': data})


@app.route('/api/get_reminders', methods=['GET'])
def get_reminders():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'User not logged in'}), 401

    user_id = session['user_id']
    pet_id = request.args.get('pet_id')

    if pet_id:
        pet = PetProfile.query.filter_by(id=pet_id, user_id=user_id).first()
        if not pet:
            return jsonify({'success': False, 'error': 'Pet not found'}), 404
        reminders = Reminder.query.filter_by(pet_id=pet_id).order_by(Reminder.due_date.asc()).all()
    else:
        reminders = Reminder.query.join(PetProfile).filter(PetProfile.user_id == user_id).order_by(Reminder.due_date.asc()).all()

    reminders_data = [{
        'id': r.id,
        'pet_id': r.pet_id,
        'title': r.title,
        'due_date': r.due_date.isoformat(),
        'completed': r.completed,
        'completed_date': r.completed_date.isoformat() if r.completed_date else None
    } for r in reminders]

    return jsonify({'success': True, 'reminders': reminders_data})


@app.route('/api/complete_reminder/<int:reminder_id>', methods=['POST'])
def complete_reminder(reminder_id):
    try:
        reminder = Reminder.query.get_or_404(reminder_id)
        reminder.completed = True
        reminder.completed_date = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        logging.error(f"Error completing reminder: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/add_reminder', methods=['POST'])
def add_reminder():
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'User not logged in'}), 401

        data = request.get_json()
        pet_id = data.get('pet_id')
        title = data.get('title')
        due_date = data.get('due_date')  # expect ISO string

        if not pet_id or not title or not due_date:
            return jsonify({'success': False, 'error': 'Pet ID, title, and due date are required'}), 400

        pet = PetProfile.query.get(pet_id)
        if not pet:
            return jsonify({'success': False, 'error': 'Pet not found'}), 404

        reminder = Reminder(
            pet_id=pet_id,
            title=title,
            due_date=datetime.fromisoformat(due_date),
            completed=False
        )
        db.session.add(reminder)
        db.session.commit()

        return jsonify({'success': True, 'reminder': {
            'id': reminder.id,
            'pet_id': reminder.pet_id,
            'title': reminder.title,
            'due_date': reminder.due_date.isoformat(),
            'completed': reminder.completed
        }})
    except Exception as e:
        logging.error(f"Error adding reminder: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/upload_image', methods=['POST'])
def upload_image():
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image file provided'}), 400

        file = request.files['image']
        pet_id = request.form.get('pet_id')
        description = request.form.get('description', '')

        if file.filename == '' or not pet_id:
            return jsonify({'success': False, 'error': 'File and Pet ID required'}), 400

        pet = PetProfile.query.get(pet_id)
        if not pet:
            return jsonify({'success': False, 'error': 'Pet not found'}), 404

        # Read file content for hashing
        file_content = file.read()
        file.seek(0)  # Reset file pointer for saving
        
        # Generate hash of the image content
        import hashlib
        image_hash = hashlib.md5(file_content).hexdigest()
        
        # Check if we've analyzed this exact image before
        existing_analysis = check_image_analysis_cache(image_hash, pet_id, description)
        if existing_analysis:
            # Save the image with a new filename but return cached analysis
            filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(filepath)
            
            # Create new health history entry with cached analysis
            create_health_history_entry(pet_id, description, existing_analysis, filename)
            
            return jsonify({
                'success': True,
                'analysis': existing_analysis,
                'image_url': f"static/uploads/{filename}",
                'cached': True
            })

        # Save uploaded image
        filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(filepath)

        # Analyze the image
        analysis = analyze_pet_image(pet, filepath, description)

        # Validate diagnosis
        if not analysis or not analysis.get("diagnosis") or not any(
            str(d).strip().lower() not in ["unable to analyze symptoms", "unknown", ""]
            for d in analysis["diagnosis"]
        ):
            logging.warning("Empty or invalid AI diagnosis — not saving to DB.")
            return jsonify({'success': False, 'error': 'Empty or invalid AI analysis result'}), 400

        # Cache the analysis result
        cache_image_analysis(image_hash, pet_id, description, analysis)
        
        # Create health history entry
        create_health_history_entry(pet_id, description, analysis, filename)


        condition_likelihood = (
            analysis.get("condition_likelihood")
            or analysis.get("conditionLikelihood")
            or "Unknown"
      )

        warning_item = ""

        # Check if diagnosis mentions species mismatch or wrong animal
        if any("not a dog" in d.lower() or "different species" in d.lower() for d in analysis.get("diagnosis", [])):
            warning_item = "⚠ The uploaded image does not appear to match your pet (species mismatch)."
        
        # Build response (⚡ alias severity = urgency_level)
        response_data = {
            "diagnosis": analysis.get("diagnosis", []),
            "urgency_level": analysis.get("urgency_level", "Not Assessed"),
            "severity": analysis.get("urgency_level", "Not Assessed"),  # 👈 alias
            "possible_causes": analysis.get("possible_causes", []),   # ✅ fixed
            "recommendation": analysis.get("recommendation", "No recommendation"),
             "conditionLikelihood": condition_likelihood,   # camelCase
             "condition_likelihood": condition_likelihood,   # snake_case
             "warningItem": warning_item
        }

        return jsonify({
            'success': True,
            'analysis': response_data,
            'image_url': f"static/uploads/{filename}"
        })

    except Exception as e:
        logging.error(f"Error uploading image: {e}")
        logging.error(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 400



@app.route('/api/start_consultation', methods=['POST'])
def start_consultation():
    try:
        data = request.get_json()
        pet_id = data.get('pet_id')
        if not pet_id:
            return jsonify({'success': False, 'error': 'Pet ID required'}), 400

        pet = PetProfile.query.get(pet_id)
        if not pet:
            return jsonify({'success': False, 'error': 'Pet not found'}), 404

        import time
        timestamp = int(time.time())
        room_id = f"PetHealth_{pet_id}_{timestamp}"

        history = HealthHistory.query.filter_by(pet_id=pet_id).order_by(HealthHistory.date.desc()).limit(10).all()
        health_history = [{
            'id': entry.id,
            'date': entry.date.isoformat(),
            'symptoms': entry.symptoms,
            'diagnosis': entry.diagnosis,
            'recommendation': entry.recommendation
        } for entry in history]

        consultation_url = f"https://meet.jit.si/{room_id}"

        return jsonify({
            'success': True,
            'room_id': room_id,
            'consultation_url': consultation_url,
            'pet': {
                'id': pet.id,
                'name': pet.name,
                'species': pet.species,
                'breed': pet.breed,
                'age': pet.age,
                'medical_notes': pet.medical_notes
            },
            'health_history': health_history
        })
    except Exception as e:
        logging.error(f"Error starting consultation: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400


# Helper functions for image analysis caching
def check_image_analysis_cache(image_hash, pet_id, description):
    """
    Check if we have a cached analysis for this exact image.
    Returns the cached analysis if found, None otherwise.
    """
    try:
        # Look for existing health history entries with the same image hash
        # We'll store the hash in the symptoms field for now (could be improved with a separate table)
        cache_key = f"ImageHash:{image_hash}"
        
        # Check if we have any recent analysis with this hash
        existing_entry = HealthHistory.query.filter(
            HealthHistory.symptoms.like(f"%{cache_key}%"),
            HealthHistory.pet_id == pet_id
        ).order_by(HealthHistory.date.desc()).first()
        
        if existing_entry:
            # Extract the cached analysis from the existing entry
            diagnosis = json.loads(existing_entry.diagnosis) if existing_entry.diagnosis else []
            possible_causes = json.loads(existing_entry.possible_causes) if existing_entry.possible_causes else []
            
            return {
                "diagnosis": diagnosis,
                "urgency_level": existing_entry.urgency_level,
                "severity": existing_entry.urgency_level,
                "recommendation": existing_entry.recommendation,
                "possible_causes": possible_causes,
                "condition_likelihood": "Cached Analysis"
            }
        
        return None
    except Exception as e:
        logging.error(f"Error checking image cache: {e}")
        return None


def cache_image_analysis(image_hash, pet_id, description, analysis):
    """
    Cache the analysis result for future use.
    """
    try:
        # Store the hash in the symptoms field for caching
        cache_key = f"ImageHash:{image_hash}"
        symptoms = f"Image analysis: {description} {cache_key}" if description else f"Image analysis {cache_key}"
        
        # Normalize diagnosis as a list
        diagnosis = analysis["diagnosis"]
        if isinstance(diagnosis, str):
            diagnosis = [diagnosis]

        possible_causes = analysis.get("possible_causes", [])
        
        # Save analysis to health history with cache key
        history_entry = HealthHistory(
            pet_id=pet_id,
            date=datetime.utcnow(),
            symptoms=symptoms,
            diagnosis=json.dumps(diagnosis),
            recommendation=analysis.get("recommendation", ""),
            urgency_level=analysis.get("urgency_level", "Not Assessed"),
            possible_causes=json.dumps(possible_causes)
        )

        db.session.add(history_entry)
        db.session.commit()
        
        logging.info(f"Cached image analysis for hash: {image_hash}")
    except Exception as e:
        logging.error(f"Error caching image analysis: {e}")


def create_health_history_entry(pet_id, description, analysis, filename):
    """
    Create a health history entry from analysis results.
    """
    try:
        # Normalize diagnosis as a list
        diagnosis = analysis["diagnosis"]
        if isinstance(diagnosis, str):
            diagnosis = [diagnosis]

        possible_causes = analysis.get("possible_causes", [])
        
        # Save analysis to health history
        history_entry = HealthHistory(
            pet_id=pet_id,
            date=datetime.utcnow(),
            symptoms=f"Image analysis: {description}" if description else "Image analysis",
            diagnosis=json.dumps(diagnosis),
            recommendation=analysis.get("recommendation", ""),
            urgency_level=analysis.get("urgency_level", "Not Assessed"),
            possible_causes=json.dumps(possible_causes)
        )

        db.session.add(history_entry)
        db.session.commit()
        
        logging.info(f"Created health history entry for pet {pet_id}")
    except Exception as e:
        logging.error(f"Error creating health history entry: {e}")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)