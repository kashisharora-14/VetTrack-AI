import json
import logging
import os

try:
    from google import genai
    from google.genai import types
except Exception:
    genai = None
    types = None


def _build_client():
    if genai is None:
        logging.warning("Gemini SDK is not installed; using fallback analysis.")
        return None
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logging.warning("GEMINI_API_KEY is missing; using fallback analysis.")
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        logging.warning(f"Gemini client init failed: {e}")
        return None


client = _build_client()
_MODEL_CACHE = None


def _preferred_models():
    env_model = os.environ.get("GEMINI_MODEL")
    defaults = [
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-2.5-flash",
        "gemini-2.5-pro",
    ]
    if env_model:
        return [env_model] + [m for m in defaults if m != env_model]
    return defaults


def _normalize_model_name(name):
    if not name:
        return name
    return name.split("/", 1)[1] if name.startswith("models/") else name


def _discover_available_generate_models():
    if client is None:
        return []
    names = []
    try:
        for model in client.models.list():
            raw_name = getattr(model, "name", "") or ""
            if not raw_name:
                continue
            methods = (
                getattr(model, "supported_actions", None)
                or getattr(model, "supported_generation_methods", None)
                or []
            )
            if methods and not any("generate" in str(m).lower() for m in methods):
                continue
            names.append(_normalize_model_name(raw_name))
    except Exception as e:
        logging.warning(f"Gemini model listing failed: {e}")
    return names


def _resolve_model():
    global _MODEL_CACHE
    if _MODEL_CACHE:
        return _MODEL_CACHE

    preferred = _preferred_models()
    available = _discover_available_generate_models()

    if available:
        for name in preferred:
            if name in available:
                _MODEL_CACHE = name
                return _MODEL_CACHE
        _MODEL_CACHE = available[0]
        return _MODEL_CACHE

    _MODEL_CACHE = preferred[0]
    return _MODEL_CACHE


def _generate_content_with_fallback(contents, config=None):
    global _MODEL_CACHE
    if client is None:
        raise RuntimeError("Gemini client unavailable")

    candidates = []
    primary = _resolve_model()
    if primary:
        candidates.append(primary)
    for m in _preferred_models():
        if m not in candidates:
            candidates.append(m)

    last_error = None
    for model_name in candidates:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config,
            )
            _MODEL_CACHE = model_name
            return response
        except Exception as e:
            last_error = e
            logging.warning(f"Gemini model '{model_name}' failed: {e}")

    raise last_error if last_error else RuntimeError("No Gemini model available")


def analyze_pet_symptoms(pet, symptoms):
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
        response = _generate_content_with_fallback(
            contents=prompt,
            config=(types.GenerateContentConfig(response_mime_type="application/json") if types else None),
        )
        return json.loads(response.text)
    except Exception as e:
        logging.error(f"AI Integration error: {e}")
        return get_fallback_symptom_analysis(pet, symptoms)


def analyze_pet_image(pet, image_path, description=""):
    try:
        with open(image_path, "rb") as f:
            image_data = f.read()

        prompt = f"""
        You are a veterinary AI assistant specializing in visual pet health assessment.
        First task: verify whether the uploaded image matches the selected pet profile.

        Selected Pet Profile:
        - Name: {pet.name}
        - Species: {pet.species}
        - Breed: {pet.breed}
        - Age: {pet.age} years
        - User description: {description}

        IMPORTANT DECISION RULE:
        - If species or visual context clearly does NOT match the selected pet, set image_match=false.
        - If breed appears inconsistent with the selected breed, set image_match=false.
        - If breed/species cannot be confirmed with high confidence, set image_match=false.
        - If image is not a pet/unclear/unusable, set image_match=false.
        - If image_match=false, return EMPTY analysis fields only:
          diagnosis=[], possible_causes=[], recommendation="", condition_likelihood="", urgency_level="Not Assessed".

        Return ONLY strict JSON with this exact schema:
        {{
          "image_match": true|false,
          "mismatch_reason": "string",
          "diagnosis": ["string"],
          "condition_likelihood": "string",
          "recommendation": "string",
          "urgency_level": "Low|Medium|High|Not Assessed",
          "possible_causes": ["string"]
        }}
        """

        response = _generate_content_with_fallback(
            contents=[
                prompt,
                (types.Part.from_bytes(data=image_data, mime_type="image/jpeg") if types else image_data),
            ],
            config=(types.GenerateContentConfig(response_mime_type="application/json") if types else None),
        )
        return json.loads(response.text)
    except Exception as e:
        logging.error(f"AI Integration error: {e}")
        return get_fallback_image_analysis(pet, description)


def get_diagnosis_explanation_from_gemini(diagnosis_name):
    prompt = (
        f'Provide a detailed educational explanation for the pet health diagnosis: "{diagnosis_name}". '
        'Respond ONLY with JSON: {"description": "string", "causes": ["string"], "symptoms": ["string"]}'
    )
    try:
        response = _generate_content_with_fallback(
            contents=prompt,
            config=(types.GenerateContentConfig(response_mime_type="application/json") if types else None),
        )
        return json.loads(response.text)
    except Exception as e:
        logging.error(f"AI Integration error: {e}")
        return get_fallback_explanation(diagnosis_name)


def get_fallback_symptom_analysis(pet, symptoms):
    return {
        "diagnosis": ["Veterinary consultation recommended"],
        "urgency_level": "Medium",
        "recommendation": "Please consult a vet.",
        "possible_causes": ["Unknown"],
    }


def get_fallback_explanation(diagnosis_name):
    return {
        "description": "Information unavailable.",
        "causes": ["Consult a professional"],
        "symptoms": ["Consult a professional"],
    }


def get_fallback_image_analysis(pet, description):
    return {
        "diagnosis": ["Image analysis unavailable"],
        "urgency_level": "Medium",
        "recommendation": "Consult a vet.",
        "possible_causes": ["Unknown"],
        "condition_likelihood": "Unknown",
    }
