import json
import logging
import os
import requests
import traceback
from typing import List
from pydantic import BaseModel
from dotenv import load_dotenv
import base64
import mimetypes

load_dotenv()

# Get API key from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

class SymptomAnalysis(BaseModel):
    diagnosis:List[str]
    urgency_level: str
    recommendation: str
    possible_causes: List[str]


class ImageAnalysis(BaseModel):
    diagnosis: List[str]
    condition_likelihood: str
    recommendation: str
    severity: str
    possible_causes: List[str] = []  # ✅ match SymptomAnalysis


def analyze_pet_symptoms(pet, symptoms):
    """
    Analyze pet symptoms using Gemini API (direct HTTP requests).
    Returns a dict or a minimal safe dict, never None.
    """
    try:
        system_prompt = (
            "You are a veterinary AI assistant. Analyze the provided pet symptoms and provide "
            "a list of possible diagnoses (minimum 1, maximum 5), urgency level (Low, Medium, High, Emergency), "
            "recommendations, and possible causes. "
            "Be thorough but remember this is not a replacement for professional veterinary care. "
            "Always recommend consulting a veterinarian for serious concerns. "
            "Respond ONLY with JSON in this format: "
            '{"diagnosis": ["string1", "string2"], "urgency_level": "string", "recommendation": "string", "possible_causes": ["string1", "string2"]}'
        )

        user_prompt = f"""
        Pet Information:
        - Name: {pet.name}
        - Species: {pet.species}
        - Breed: {pet.breed}
        - Age: {pet.age} years
        - Medical Notes: {pet.medical_notes or 'None'}

        Current Symptoms: {symptoms}

        Please analyze these symptoms and provide your assessment.
        """

        payload = {
            "contents": [{
                "parts": [{
                    "text": f"{system_prompt}\n\n{user_prompt}"
                }]
            }],
            "generationConfig": {
                "response_mime_type": "application/json"
            }
        }

        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(
            f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code != 200:
            logging.error(f"Gemini API error: {response.status_code} - {response.text}")
            
            # Check if it's a quota exceeded error
            if response.status_code == 429:
                return {
                    "diagnosis": ["API quota exceeded - please try again later"],
                    "urgency_level": "Service Unavailable", 
                    "recommendation": "The AI service has reached its daily quota. Please try again later or contact support.",
                    "possible_causes": ["API quota limit reached"]
                }
            
            return {
                "diagnosis": [],
                "urgency_level": "Unknown",
                "recommendation": "",
                "possible_causes": []
            }

        result = response.json()

        # Extract text from Gemini response
        try:
            text_content = result["candidates"][0]["content"]["parts"][0]["text"]
            analysis = json.loads(text_content)
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logging.error(f"Error parsing Gemini response: {e}")
            return {
                "diagnosis": [],
                "urgency_level": "Unknown",
                "recommendation": "",
                "possible_causes": []
            }

        # Normalize diagnosis
        diagnosis = analysis.get("diagnosis", [])
        if isinstance(diagnosis, str):
            diagnosis = [diagnosis]
        elif not isinstance(diagnosis, list):
            diagnosis = []

        diagnosis = [
            str(d).strip() for d in diagnosis
            if str(d).strip() and str(d).strip().lower() != "unknown"
        ]

        if not diagnosis:
            logging.warning("Gemini returned no valid diagnosis; returning safe defaults.")
            return {
                "diagnosis": [],
                "urgency_level": analysis.get("urgency_level", "Unknown"),
                "recommendation": analysis.get("recommendation", ""),
                "possible_causes": analysis.get("possible_causes", []),
            }

        # Ensure required fields exist
        analysis["diagnosis"] = diagnosis
        analysis["urgency_level"] = analysis.get("urgency_level", "Unknown")
        analysis["recommendation"] = analysis.get("recommendation", "")
        analysis["possible_causes"] = analysis.get("possible_causes", [])

        return analysis

    except Exception as e:
        logging.error(f"Error in symptom analysis: {e}")
        logging.error(traceback.format_exc())
        return {
            "diagnosis": [],
            "urgency_level": "Unknown",
            "recommendation": "",
            "possible_causes": []
        }


def normalize_image_analysis(analysis: dict) -> dict:
    severity = analysis.get("severity", "Unknown")

    return {
        "diagnosis": analysis.get("diagnosis", []),
        "urgency_level": severity if severity != "Unknown" else analysis.get("urgency_level", "Unknown"),
        "severity": severity,  # ✅ keep severity for frontend
        "recommendation": analysis.get("recommendation", ""),
        "possible_causes": analysis.get("possible_causes", []),
        "condition_likelihood": analysis.get("condition_likelihood", "Unknown"),
    }


# Configure logging at the top of your file
logging.basicConfig(
    level=logging.INFO,  # Show INFO, WARNING, ERROR, CRITICAL
    format="%(asctime)s [%(levelname)s] %(message)s",
)

def analyze_pet_image(pet, image_path, description=""):
    """
    Analyze pet health image using Gemini API.
    Returns a normalized dictionary always (never None).
    """
    try:
        # Read and encode image
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')

        # Determine mime type
        mime_type = mimetypes.guess_type(image_path)[0] or "image/jpeg"

        system_prompt = (
            "You are a veterinary AI assistant specializing in visual health assessment. "
            "First, check if the animal in the image matches the provided species with age and breed. "
            "If there is a mismatch, include a short warning as the FIRST item in the 'diagnosis' list with 'Warning:' prefix. "
            "Then provide a concise list of possible diagnoses (ranked, just names). "
            "Do NOT include words like 'Most likely' inside the diagnosis list. "
            "Also provide a list of possible underlying causes (e.g., mites, infection, immune deficiency). "
            "Always include a clear recommendation. "
            "Respond ONLY with valid JSON in this exact format: "
            '{"diagnosis": ["string1", "string2"], "condition_likelihood": "string", "recommendation": "string", "urgency_level": "string", "possible_causes": ["string1", "string2"]}'
        )

        user_prompt = f"""
        Pet Information:
        - Name: {pet.name}
        - Species: {pet.species}
        - Breed: {pet.breed}
        - Age: {pet.age} years
        - Medical Notes: {pet.medical_notes or 'None'}

        Additional Description: {description if description else 'No additional description provided'}

        Please analyze the image and provide your assessment.
        """

        payload = {
            "contents": [{
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": image_data
                        }
                    },
                    {
                        "text": f"{system_prompt}\n\n{user_prompt}"
                    }
                ]
            }],
            "generationConfig": {
                "response_mime_type": "application/json"
            }
        }

        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(
            f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
            headers=headers,
            json=payload,
            timeout=60
        )

        if response.status_code != 200:
            logging.error(f"Gemini API error: {response.status_code} - {response.text}")
            
            # Check if it's a quota exceeded error
            if response.status_code == 429:
                return {
                    "diagnosis": ["API quota exceeded - please try again later"],
                    "urgency_level": "Service Unavailable",
                    "recommendation": "The AI service has reached its daily quota. Please try again later or contact support.",
                    "possible_causes": ["API quota limit reached"],
                    "condition_likelihood": "Cannot analyze due to quota limit"
                }
            
            return {
                "diagnosis": [],
                "urgency_level": "Unknown",
                "recommendation": "",
                "possible_causes": [],
                "condition_likelihood": "Unknown"
            }

        result = response.json()

        # Extract text from Gemini response
        try:
            text_content = result["candidates"][0]["content"]["parts"][0]["text"]
            analysis = json.loads(text_content)
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logging.error(f"Error parsing Gemini image response: {e}")
            return {
                "diagnosis": [],
                "urgency_level": "Unknown",
                "recommendation": "",
                "possible_causes": [],
                "condition_likelihood": "Unknown"
            }

        # Normalize fields
        diagnosis = analysis.get("diagnosis", [])
        if isinstance(diagnosis, str):
            diagnosis = [diagnosis]
        elif not isinstance(diagnosis, list):
            diagnosis = []

        # Clean invalid entries
        diagnosis = [
            str(d).strip()
            for d in diagnosis
            if str(d).strip().lower() not in ["", "unknown", "cannot determine"]
        ]

        # Check for various types of mismatches in diagnosis
        warning_item = ""
        diagnosis_text = " ".join(analysis.get("diagnosis", [])).lower()

        if any(warning in diagnosis_text for warning in ["species mismatch", "different species", "not a"]):
            warning_item = "⚠ The uploaded image does not appear to match your pet's species."
        elif "breed" in diagnosis_text and "mismatch" in diagnosis_text:
            warning_item = "⚠ The breed characteristics in the image don't match your pet's profile."
        elif "age" in diagnosis_text and ("mismatch" in diagnosis_text or "doesn't match" in diagnosis_text):
            warning_item = "⚠ The apparent age in the image doesn't align with your pet's profile."

        if warning_item and warning_item not in diagnosis:
            diagnosis.insert(0, warning_item)


        severity = analysis.get("severity", "Unknown")

        normalized = {
            "diagnosis": diagnosis,
            "urgency_level": severity if severity != "Unknown" else analysis.get("urgency_level", "Unknown"),
            "severity": severity,
            "recommendation": analysis.get("recommendation", ""),
            "possible_causes": analysis.get("possible_causes", []),
            "condition_likelihood": analysis.get("condition_likelihood", "Unknown"),
        }

        logging.info(f"Normalized image analysis: {normalized}")
        return normalized

    except Exception as e:
        logging.error(f"Error in image analysis: {e}")
        logging.error(traceback.format_exc())
        return {
            "diagnosis": [],
            "urgency_level": "Unknown",
            "recommendation": "",
            "possible_causes": [],
            "condition_likelihood": "Unknown"
        }


def get_diagnosis_explanation_from_gemini(diagnosis_name):
    """
    Get detailed explanation for a specific diagnosis using Gemini API.
    Returns a dictionary with description, causes, and symptoms to watch for.
    """
    try:
        system_prompt = (
            "You are a veterinary education assistant. Provide a detailed, educational explanation "
            "about the given pet health diagnosis. Be informative but remember this is for educational "
            "purposes only and should not replace professional veterinary care. "
            "Respond ONLY with JSON in this exact format: "
            '{"description": "string", "causes": ["string1", "string2", "string3"], "symptoms": ["string1", "string2", "string3"]}'
        )

        user_prompt = f"""
        Please provide a comprehensive explanation for the following pet health diagnosis: "{diagnosis_name}"

        Include:
        1. A clear description of what this condition is
        2. Common causes that lead to this condition (provide 3-5 causes)
        3. Symptoms and signs pet owners should watch out for (provide 3-5 symptoms)

        Make the explanation informative but accessible to pet owners.
        """

        payload = {
            "contents": [{
                "parts": [{
                    "text": f"{system_prompt}\n\n{user_prompt}"
                }]
            }],
            "generationConfig": {
                "response_mime_type": "application/json"
            }
        }

        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(
            f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code != 200:
            logging.error(f"Gemini API error for diagnosis explanation: {response.status_code} - {response.text}")
            return get_fallback_explanation(diagnosis_name)

        result = response.json()

        # Extract text from Gemini response
        try:
            text_content = result["candidates"][0]["content"]["parts"][0]["text"]
            explanation = json.loads(text_content)
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logging.error(f"Error parsing Gemini explanation response: {e}")
            return get_fallback_explanation(diagnosis_name)

        # Validate and clean the response
        description = explanation.get("description", "A medical condition that requires veterinary attention.")
        causes = explanation.get("causes", [])
        symptoms = explanation.get("symptoms", [])

        # Ensure we have lists
        if not isinstance(causes, list):
            causes = [str(causes)] if causes else []
        if not isinstance(symptoms, list):
            symptoms = [str(symptoms)] if symptoms else []

        # Clean empty entries
        causes = [str(c).strip() for c in causes if str(c).strip()]
        symptoms = [str(s).strip() for s in symptoms if str(s).strip()]

        # Ensure we have at least some content
        if not causes:
            causes = ["Various factors may contribute to this condition", "Environmental influences", "Genetic predisposition"]
        if not symptoms:
            symptoms = ["Changes in appetite or behavior", "Worsening symptoms", "Signs of discomfort"]

        return {
            "description": description,
            "causes": causes[:5],  # Limit to 5 items
            "symptoms": symptoms[:5]  # Limit to 5 items
        }

    except Exception as e:
        logging.error(f"Error getting diagnosis explanation from Gemini: {e}")
        return get_fallback_explanation(diagnosis_name)


def get_fallback_explanation(diagnosis_name):
    """Provide a comprehensive fallback explanation when AI is unavailable"""

    # Common conditions with specific information
    condition_info = {
        "alopecia": {
            "description": "Hair loss in pets that can be caused by various factors including allergies, parasites, infections, or hormonal imbalances.",
            "causes": ["Allergic reactions", "Parasitic infections (fleas, mites)", "Bacterial or fungal infections", "Hormonal imbalances", "Stress or anxiety", "Poor nutrition"],
            "symptoms": ["Patchy or complete hair loss", "Red or irritated skin", "Excessive scratching or licking", "Skin lesions or bumps", "Changes in skin color or texture"]
        },
        "skin infection": {
            "description": "Bacterial, fungal, or parasitic infections affecting the skin that require veterinary treatment.",
            "causes": ["Bacterial overgrowth", "Fungal infections", "Parasitic infestations", "Allergic reactions", "Poor hygiene", "Compromised immune system"],
            "symptoms": ["Red, inflamed skin", "Discharge or pus", "Foul odor", "Excessive scratching", "Hair loss around affected areas", "Crusty or scaly patches"]
        },
        "demodectic mange": {
            "description": "A skin condition caused by Demodex mites that naturally live on pets but can overpopulate when the immune system is compromised.",
            "causes": ["Weakened immune system", "Genetic predisposition", "Stress", "Poor nutrition", "Age (young or elderly pets)", "Underlying health conditions"],
            "symptoms": ["Hair loss in patches", "Red, inflamed skin", "Scaling or crusty areas", "Secondary bacterial infections", "Mild to no itching initially"]
        },
        "ringworm": {
            "description": "A fungal infection that affects the skin, hair, and sometimes nails, despite its name having nothing to do with worms.",
            "causes": ["Fungal spores in environment", "Contact with infected animals", "Contaminated objects", "Weakened immune system", "Poor hygiene", "Overcrowded conditions"],
            "symptoms": ["Circular patches of hair loss", "Red, scaly skin", "Broken or brittle hair", "Mild itching", "Crusty or inflamed areas", "Spreading lesions"]
        }
    }

    # Check if we have specific information for this condition
    clean_diagnosis = diagnosis_name.lower().strip()

    for condition, info in condition_info.items():
        if condition in clean_diagnosis:
            return info

    # Generic fallback for unknown conditions
    return {
        "description": f"{diagnosis_name} is a medical condition that may affect your pet's health. A thorough veterinary examination is recommended for proper diagnosis and treatment planning.",
        "causes": [
            "Various underlying health factors",
            "Environmental influences", 
            "Genetic predisposition",
            "Age-related changes",
            "Lifestyle factors",
            "Immune system factors"
        ],
        "symptoms": [
            "Changes in appetite or behavior",
            "Worsening of current symptoms", 
            "New or unusual symptoms",
            "Signs of pain or discomfort",
            "Any concerning changes in your pet's condition",
            "Monitor for progression of symptoms"
        ]
    }