
import json
import logging
import os
from dotenv import load_dotenv
import mimetypes
import traceback  # Make sure this is at the top of your file
from typing import List
from pydantic import BaseModel
from google import genai
import pprint

from google.genai import types
from pydantic import BaseModel

load_dotenv()
# print("DEBUG: GEMINI_API_KEY =", os.getenv("GEMINI_API_KEY"))

# Initialize Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


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
    Analyze pet symptoms using Gemini LLM (defensive parsing).
    Returns a dict or a minimal safe dict, never None.
    """
    try:
        system_prompt = (
            "You are a veterinary AI assistant. Analyze the provided pet symptoms and provide "
            "a list of possible diagnoses (minimum 1, maximum 5), urgency level (Low, Medium, High, Emergency), "
            "recommendations, and possible causes. "
            "Be thorough but remember this is not a replacement for professional veterinary care. "
            "Always recommend consulting a veterinarian for serious concerns. "
            "Respond ONLY with JSON matching the provided schema."
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

        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=[types.Content(role="user", parts=[types.Part(text=user_prompt)])],
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=SymptomAnalysis,
            ),
        )

        analysis = None

        # 1) Prefer parsed (pydantic v1/v2 safe)
        if hasattr(response, "parsed") and response.parsed:
            parsed_model = response.parsed
            if hasattr(parsed_model, "model_dump"):
                analysis = parsed_model.model_dump()      # pydantic v2
            elif hasattr(parsed_model, "dict"):
                analysis = parsed_model.dict()            # pydantic v1

        # 2) Try response.text (string JSON)
        if not analysis and hasattr(response, "text") and response.text:
            try:
                analysis = json.loads(response.text)
            except json.JSONDecodeError:
                logging.error("Symptom response.text was not valid JSON")

        # 3) Candidates fallback (aggregate parts.text)
        if not analysis and hasattr(response, "candidates") and response.candidates:
            raw = ""
            for c in response.candidates:
                if not getattr(c, "content", None): 
                    continue
                for p in getattr(c.content, "parts", []) or []:
                    if getattr(p, "text", None):
                        raw += p.text
            raw = raw.strip()
            if raw:
                try:
                    analysis = json.loads(raw)
                except json.JSONDecodeError:
                    logging.error(f"Candidates text not JSON: {raw[:200]}")

        logging.info(f"Gemini symptom analysis parsed response: {analysis}")

        # If still nothing, return a safe minimal dict (not None)
        if not analysis:
            logging.warning("Gemini returned an empty or invalid response; returning safe defaults.")
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

        # If model produced nothing useful, still return safe dict
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
        # Never return None
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

    

import logging
import traceback

# Configure logging at the top of your file
logging.basicConfig(
    level=logging.INFO,  # Show INFO, WARNING, ERROR, CRITICAL
    format="%(asctime)s [%(levelname)s] %(message)s",
)

def analyze_pet_image(pet, image_path, description=""):
    """
    Analyze pet health image using Gemini LLM.
    Returns a normalized dictionary always (never None), with diagnosis list, urgency_level, recommendation, etc.
    Prints full debug info to terminal.
    """
    try:
        system_prompt = (
            "You are a veterinary AI assistant specializing in visual health assessment. "
            "First, check if the animal in the image matches the provided species with age and breed. "
            "If there is a mismatch, include a short warning as the FIRST item in the 'diagnosis' list with warning : otherwise go with flat analysis. "
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

        import mimetypes
        mime_type = mimetypes.guess_type(image_path)[0] or "application/octet-stream"
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=[
                types.Content(role="user", parts=[
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                    types.Part(text=user_prompt)
                ])
            ],
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=ImageAnalysis,
            ),
        )
        print("\n=== RAW GEMINI RESPONSE ===")
        pprint.pprint(response.__dict__, indent=2, width=120)
        print("===========================\n")


        analysis = {}
        print("DEBUG: Raw Gemini response:", response)
        # Try parsed output first
        if hasattr(response, "parsed") and response.parsed:
            analysis = response.parsed.model_dump()
            logging.info(f"DEBUG: Parsed response from Gemini: {analysis}")
            print("DEBUG: Parsed response from Gemini:", analysis)

        # Then try response text
        elif hasattr(response, "text") and response.text:
            try:
                analysis = json.loads(response.text)
                logging.info(f"DEBUG: JSON from response.text: {analysis}")
                print("DEBUG: JSON from response.text:", analysis)
            except json.JSONDecodeError:
                logging.error("DEBUG: Response.text was not valid JSON")
                print("DEBUG: Response.text was not valid JSON:", response.text)

        # Then try candidates fallback
        if not analysis and hasattr(response, "candidates") and response.candidates:
            raw_text = ""
            for c in response.candidates:
                if not c or not getattr(c, "content", None):
                    continue
                if not getattr(c.content, "parts", None):
                    continue
                for part in c.content.parts:
                    if getattr(part, "text", None):
                        raw_text += part.text
            raw_text = raw_text.strip()
            if raw_text:
                try:
                    analysis = json.loads(raw_text)
                    logging.info(f"DEBUG: JSON from candidates fallback: {analysis}")
                    print("DEBUG: JSON from candidates fallback:", analysis)
                except json.JSONDecodeError:
                    logging.error(f"DEBUG: Candidate raw text not JSON: {raw_text[:200]}")
                    print("DEBUG: Candidate raw text not JSON:", raw_text[:200])

        # Normalize fields to safe defaults
        if not analysis:
            logging.warning("DEBUG: Gemini returned no usable analysis, using defaults.")
            print("DEBUG: Gemini returned no usable analysis, using defaults.")
            analysis = {}

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

        # ✅ Safeguard: inject mismatch warning if missing
        expected_species = pet.species.lower().strip()
        if diagnosis and not diagnosis[0].lower().startswith("warning:"):
            if expected_species not in user_prompt.lower():
                diagnosis.insert(0, f"Warning: Uploaded image may not match {pet.name}, a {pet.species} ({pet.breed}, {pet.age} yrs)")

        severity = analysis.get("severity", "Unknown")

        normalized = {
            "diagnosis": diagnosis,
            "urgency_level": severity if severity != "Unknown" else analysis.get("urgency_level", "Unknown"),
            "severity": severity,
            "recommendation": analysis.get("recommendation", ""),
            "possible_causes": analysis.get("possible_causes", []),
            "condition_likelihood": analysis.get("condition_likelihood", "Unknown"),
        }



        logging.info(f"DEBUG: Normalized analysis: {normalized}")
        print("DEBUG: Normalized analysis:", normalized)
        return normalized

    except Exception as e:
        logging.error(f"Error in image analysis: {e}")
        logging.error(traceback.format_exc())
        print("ERROR: Exception occurred in analyze_pet_image:", e)
        print(traceback.format_exc())
        # Always return a safe default even on exception
        return {
            "diagnosis": [],
            "urgency_level": "Unknown",
            "recommendation": "",
            "possible_causes": [],
            "condition_likelihood": "Unknown"
        }
