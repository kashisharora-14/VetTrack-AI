import math
import re
from collections import defaultdict


def _normalize_text(text):
    return re.sub(r"[^a-z0-9\s]", " ", (text or "").lower())


def _tokens(text):
    return [t for t in _normalize_text(text).split() if t]


def _contains_phrase(text, phrase):
    return phrase in _normalize_text(text)


CONDITIONS = [
    {
        "name": "Gastrointestinal upset",
        "species": ["dog", "cat"],
        "keywords": {
            "vomit": 2.0, "vomiting": 2.0, "diarrhea": 2.0, "loose stool": 1.6, "nausea": 1.4,
            "no appetite": 1.8, "dehydration": 1.6, "abdominal pain": 1.5,
        },
        "causes": ["Dietary change", "Mild infection", "Food intolerance", "Parasitic irritation"],
        "recommendation": "Offer fluids, bland diet, monitor stool/vomit frequency; seek vet care if persistent >24h.",
    },
    {
        "name": "Respiratory irritation/infection",
        "species": ["dog", "cat"],
        "keywords": {
            "cough": 2.0, "sneeze": 1.8, "sneezing": 1.8, "nasal discharge": 2.0, "wheeze": 1.8,
            "breathing": 1.6, "panting": 1.2, "congestion": 1.5, "fever": 1.3,
        },
        "causes": ["Upper respiratory infection", "Allergic irritation", "Airway inflammation"],
        "recommendation": "Keep environment calm and dust-free; monitor breathing effort; consult a vet if worsening.",
    },
    {
        "name": "Dermatitis / skin allergy",
        "species": ["dog", "cat"],
        "keywords": {
            "itch": 2.0, "itchy": 2.0, "scratch": 1.9, "rash": 1.8, "redness": 1.6,
            "hair loss": 1.9, "skin": 1.4, "hot spot": 1.8, "licking paws": 1.7,
        },
        "causes": ["Environmental allergy", "Flea sensitivity", "Contact dermatitis", "Secondary skin infection"],
        "recommendation": "Prevent self-trauma, check for fleas, and schedule dermatology-focused vet evaluation.",
    },
    {
        "name": "Urinary tract irritation",
        "species": ["dog", "cat"],
        "keywords": {
            "frequent urination": 2.0, "urinate": 1.8, "straining": 2.0, "blood urine": 2.0,
            "accidents": 1.5, "pain urination": 2.0, "litter box": 1.4,
        },
        "causes": ["Urinary infection", "Crystals/stones", "Bladder inflammation"],
        "recommendation": "Increase water access and seek prompt veterinary urinalysis.",
    },
    {
        "name": "Musculoskeletal pain/injury",
        "species": ["dog", "cat"],
        "keywords": {
            "limp": 2.0, "lameness": 2.0, "joint pain": 1.9, "stiff": 1.6, "not walking": 2.0,
            "swelling": 1.5, "injury": 1.8, "fracture": 2.0, "sprain": 1.6,
        },
        "causes": ["Soft tissue strain", "Joint inflammation", "Trauma"],
        "recommendation": "Restrict activity and arrange orthopedic exam, especially if non-weight-bearing.",
    },
]


RED_FLAG_PHRASES = [
    "not breathing", "breathing hard", "cannot stand", "seizure", "unconscious", "bloody stool",
    "blood in vomit", "severe lethargy", "collapsed", "poison", "toxin", "severe pain",
]


def _score_condition(text, token_set, condition, species):
    # Species prior: slight boost if condition supports the current pet species.
    species_boost = 1.1 if species in condition["species"] else 0.95
    score = 0.0

    for phrase, weight in condition["keywords"].items():
        p = phrase.lower()
        if " " in p:
            if _contains_phrase(text, p):
                score += weight
        else:
            if p in token_set:
                score += weight

    return score * species_boost


def _urgency_from_text(text, top_score):
    red_flags = sum(1 for p in RED_FLAG_PHRASES if _contains_phrase(text, p))
    if red_flags >= 1 or top_score >= 6.5:
        return "High"
    if top_score >= 3.2:
        return "Medium"
    return "Low"


def analyze_pet_symptoms_ml(pet, symptoms, k=3):
    """
    Lightweight KNN-style prototype classifier.
    It scores symptom text against condition prototypes and returns top-k matches.
    """
    text = _normalize_text(symptoms)
    toks = _tokens(text)
    token_set = set(toks)
    species = (getattr(pet, "species", "") or "").lower()

    scored = []
    for c in CONDITIONS:
        s = _score_condition(text, token_set, c, species)
        if s > 0:
            scored.append((s, c))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:k]

    if not top:
        return {
            "diagnosis": ["General non-specific symptoms"],
            "urgency_level": "Medium",
            "recommendation": "Monitor closely and consult a veterinarian if symptoms persist or worsen.",
            "possible_causes": ["Multiple possible causes; further clinical exam required"],
            "model_used": "KNN-Symptom-Prototype-v1",
        }

    diagnosis = [item[1]["name"] for item in top]
    cause_bucket = []
    for _, cond in top:
        cause_bucket.extend(cond["causes"])
    # preserve order + uniqueness
    possible_causes = list(dict.fromkeys(cause_bucket))[:6]

    top_score = top[0][0]
    urgency = _urgency_from_text(text, top_score)
    recommendation = top[0][1]["recommendation"]

    return {
        "diagnosis": diagnosis,
        "urgency_level": urgency,
        "recommendation": recommendation,
        "possible_causes": possible_causes,
        "model_used": "KNN-Symptom-Prototype-v1",
    }
