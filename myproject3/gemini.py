import os
from google import genai
from google.genai import types

response = client.models.generate_content(
    model="gemini-1.5-flash",
    contents=prompt,
    config=types.GenerateContentConfig(
        response_mime_type="application/json"
    )
)


def analyze_pet_symptoms(pet, symptoms):
    """Analyze pet symptoms using Replit AI Integrations."""
    prompt = f"""
    You are a veterinary AI assistant. Analyze the provided pet symptoms.
    Pet Information:
    - Name: {pet.name}
    - Species: {pet.species}
    - Breed: {pet.breed}
    - Age: {pet.age} years
    - Medical Notes: {pet.medical_notes or 'None'}

    Current Symptoms: {symptoms}

    Respond ONLY with JSON in this format:
    {{"diagnosis": ["string1", "string2"], "urgency_level": "string", "recommendation": "string", "possible_causes": ["string1", "string2"]}}
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        import json
        return json.loads(response.text)
    except Exception as e:
        import logging
        logging.error(f"AI Integration error: {e}")
        return get_fallback_symptom_analysis(pet, symptoms)

def analyze_pet_image(pet, image_path, description=""):
    """Analyze pet health image using Replit AI Integrations."""
    try:
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        prompt = f"""
        You are a veterinary AI assistant specializing in visual health assessment.
        Pet Information:
        - Name: {pet.name}
        - Species: {pet.species}
        - Breed: {pet.breed}
        - Age: {pet.age} years
        
        Description: {description}
        
        Respond ONLY with valid JSON:
        {{"diagnosis": ["string1"], "condition_likelihood": "string", "recommendation": "string", "urgency_level": "string", "possible_causes": ["string1"]}}
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                prompt,
                types.Part.from_bytes(data=image_data, mime_type="image/jpeg")
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        import json
        return json.loads(response.text)
    except Exception as e:
        import logging
        logging.error(f"AI Integration error: {e}")
        return get_fallback_image_analysis(pet, description)

def get_diagnosis_explanation_from_gemini(diagnosis_name):
    """Get detailed explanation using Replit AI Integrations."""
    prompt = f"Provide a detailed educational explanation for the pet health diagnosis: \"{diagnosis_name}\". Respond ONLY with JSON: {{\"description\": \"string\", \"causes\": [\"string\"], \"symptoms\": [\"string\"]}}"
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        import json
        return json.loads(response.text)
    except Exception as e:
        return get_fallback_explanation(diagnosis_name)

def get_fallback_symptom_analysis(pet, symptoms):
    return {
        "diagnosis": ["Veterinary consultation recommended"],
        "urgency_level": "Medium",
        "recommendation": "Please consult a vet.",
        "possible_causes": ["Unknown"]
    }

def get_fallback_explanation(diagnosis_name):
    return {
        "description": "Information unavailable.",
        "causes": ["Consult a professional"],
        "symptoms": ["Consult a professional"]
    }

def get_fallback_image_analysis(pet, description):
    return {
        "diagnosis": ["Image analysis unavailable"],
        "urgency_level": "Medium",
        "recommendation": "Consult a vet.",
        "possible_causes": ["Unknown"],
        "condition_likelihood": "Unknown"
    }
