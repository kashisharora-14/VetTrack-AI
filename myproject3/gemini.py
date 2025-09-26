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
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

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
                    "possible_causes": ["API quota limit reached"]
                }
            
            # Check if it's a service overload error
            elif response.status_code == 503:
                return {
                    "diagnosis": ["AI service temporarily overloaded - please try again in a few minutes"],
                    "urgency_level": "Service Temporarily Unavailable",
                    "recommendation": "The AI analysis service is currently experiencing high demand. Please wait a few minutes and try again.",
                    "possible_causes": ["High server load", "Temporary service congestion"]
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

    except requests.exceptions.Timeout:
        logging.error("Gemini API timeout - returning fallback response")
        return get_fallback_symptom_analysis(pet, symptoms)
    except Exception as e:
        logging.error(f"Error in symptom analysis: {e}")
        logging.error(traceback.format_exc())
        return get_fallback_symptom_analysis(pet, symptoms)


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

    except requests.exceptions.Timeout:
        logging.error("Gemini API timeout during image analysis - returning fallback response")
        return get_fallback_image_analysis(pet, description)
    except Exception as e:
        logging.error(f"Error in image analysis: {e}")
        return get_fallback_image_analysis(pet, description)


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
            timeout=60
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

    except requests.exceptions.Timeout:
        logging.error("Gemini API timeout for diagnosis explanation - returning fallback response")
        return get_fallback_explanation(diagnosis_name)
    except Exception as e:
        logging.error(f"Error getting diagnosis explanation from Gemini: {e}")
        return get_fallback_explanation(diagnosis_name)


def get_fallback_symptom_analysis(pet, symptoms):
    """Provide a basic fallback analysis when Gemini is unavailable"""
    return {
        "diagnosis": ["Veterinary consultation recommended"],
        "urgency_level": "Medium",
        "recommendation": f"Based on the symptoms described for {pet.name}, we recommend scheduling a consultation with your veterinarian for proper evaluation and diagnosis. The symptoms you've noted should be assessed by a professional.",
        "possible_causes": [
            "Multiple factors could contribute to these symptoms",
            "Professional evaluation needed for accurate assessment"
        ]
    }


def get_fallback_explanation(diagnosis_name):
    """Provide a basic fallback explanation when Gemini is unavailable"""
    return {
        "description": f"{diagnosis_name} is a condition that may affect your pet's health. It's important to monitor your pet closely and consult with a veterinarian for proper diagnosis and treatment.",
        "causes": [
            "Various environmental factors",
            "Genetic predisposition",
            "Age-related changes",
            "Dietary factors",
            "Stress or lifestyle changes"
        ],
        "symptoms": [
            "Changes in behavior or appetite",
            "Physical discomfort or unusual movements",
            "Altered energy levels",
            "Changes in normal routines"
        ]
    }


def get_fallback_image_analysis(pet, description):
    """Provide a basic fallback analysis when Gemini is unavailable for image analysis"""
    return {
        "diagnosis": ["Image analysis unavailable - veterinary consultation recommended"],
        "urgency_level": "Medium",
        "recommendation": f"We were unable to analyze the image for {pet.name} at this time. Please consult with your veterinarian to have the condition properly evaluated, especially if you notice any concerning changes.",
        "possible_causes": [
            "Professional evaluation needed for visual assessment",
            "Multiple factors could contribute to visible symptoms"
        ],
        "condition_likelihood": "Unable to assess"
    }