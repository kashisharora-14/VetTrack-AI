import random
import re
from collections import Counter

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.feature_extraction.text import TfidfVectorizer
except Exception:  # pragma: no cover
    RandomForestClassifier = None
    TfidfVectorizer = None


_RANDOM_SEED = 42
_MODEL_BUNDLE = None


CONDITION_PROFILES = {
    "Gastrointestinal upset": {
        "symptoms": [
            "vomiting", "diarrhea", "loose stool", "nausea", "no appetite",
            "abdominal pain", "dehydration", "lethargy",
        ],
        "urgency": "Medium",
        "causes": ["Dietary indiscretion", "Food intolerance", "Mild infection", "Parasites"],
        "recommendation": "Offer water, bland food, monitor stool/vomit. Visit vet if symptoms persist over 24 hours.",
    },
    "Respiratory irritation/infection": {
        "symptoms": [
            "cough", "sneezing", "nasal discharge", "wheezing", "fever",
            "rapid breathing", "congestion", "tired",
        ],
        "urgency": "Medium",
        "causes": ["Upper respiratory infection", "Allergy", "Airway inflammation"],
        "recommendation": "Keep pet warm and hydrated. Seek veterinary exam if breathing effort increases.",
    },
    "Dermatitis / skin allergy": {
        "symptoms": [
            "itchy skin", "scratching", "rash", "red patches", "hair loss",
            "licking paws", "hot spot", "skin irritation",
        ],
        "urgency": "Low",
        "causes": ["Flea allergy", "Food allergy", "Environmental allergy", "Skin infection"],
        "recommendation": "Prevent scratching, check for fleas, and schedule a skin-focused veterinary check.",
    },
    "Urinary tract irritation": {
        "symptoms": [
            "frequent urination", "straining to urinate", "blood in urine", "painful urination",
            "accidents indoors", "licking genitals", "small urine amounts",
        ],
        "urgency": "High",
        "causes": ["Urinary tract infection", "Bladder inflammation", "Urinary crystals"],
        "recommendation": "Increase water intake and consult a vet quickly for urinalysis.",
    },
    "Musculoskeletal pain/injury": {
        "symptoms": [
            "limping", "lameness", "joint pain", "stiffness", "difficulty walking",
            "swelling", "pain when touched", "reduced activity",
        ],
        "urgency": "Medium",
        "causes": ["Soft tissue strain", "Joint inflammation", "Trauma"],
        "recommendation": "Restrict movement and arrange orthopedic evaluation.",
    },
    "Fever / systemic infection risk": {
        "symptoms": [
            "high fever", "extreme lethargy", "not eating", "shivering", "weakness",
            "dehydration", "rapid heartbeat", "dull behavior",
        ],
        "urgency": "High",
        "causes": ["Systemic infection", "Inflammatory condition", "Vector-borne disease"],
        "recommendation": "High priority veterinary assessment is recommended as soon as possible.",
    },
}

NOISE_TERMS = [
    "since morning", "for two days", "after meal", "at night", "mild", "severe",
    "intermittent", "progressively worse", "sudden", "after walk",
]

SPECIES_OPTIONS = ["dog", "cat"]


def _clean_text(text):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", (text or "").lower())).strip()


def _generate_synthetic_dataset(n_rows=1400):
    random.seed(_RANDOM_SEED)
    rows = []
    labels_diag = []
    labels_urg = []

    condition_names = list(CONDITION_PROFILES.keys())
    for _ in range(n_rows):
        diagnosis = random.choice(condition_names)
        profile = CONDITION_PROFILES[diagnosis]
        base = random.sample(profile["symptoms"], k=min(4, len(profile["symptoms"])))
        extras = random.sample(NOISE_TERMS, k=random.randint(1, 3))

        # Inject mild cross-condition noise so the model learns separation.
        if random.random() < 0.2:
            other = random.choice([c for c in condition_names if c != diagnosis])
            base.append(random.choice(CONDITION_PROFILES[other]["symptoms"]))

        species = random.choice(SPECIES_OPTIONS)
        age = random.randint(1, 14)
        sentence = f"{species} age {age} has " + ", ".join(base + extras)
        rows.append(_clean_text(sentence))
        labels_diag.append(diagnosis)
        labels_urg.append(profile["urgency"])

    return rows, labels_diag, labels_urg


def _train_once():
    global _MODEL_BUNDLE
    if _MODEL_BUNDLE is not None:
        return _MODEL_BUNDLE

    if RandomForestClassifier is None or TfidfVectorizer is None:
        _MODEL_BUNDLE = None
        return None

    x_text, y_diag, y_urg = _generate_synthetic_dataset()
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=3500)
    x = vectorizer.fit_transform(x_text)

    diag_model = RandomForestClassifier(
        n_estimators=260,
        random_state=_RANDOM_SEED,
        class_weight="balanced_subsample",
        n_jobs=-1,
    )
    diag_model.fit(x, y_diag)

    urg_model = RandomForestClassifier(
        n_estimators=180,
        random_state=_RANDOM_SEED,
        class_weight="balanced_subsample",
        n_jobs=-1,
    )
    urg_model.fit(x, y_urg)

    _MODEL_BUNDLE = {
        "vectorizer": vectorizer,
        "diag_model": diag_model,
        "urg_model": urg_model,
    }
    return _MODEL_BUNDLE


def analyze_pet_symptoms_rf(pet, symptoms):
    bundle = _train_once()
    if bundle is None:
        raise RuntimeError("scikit-learn is not available for RandomForest symptom analysis")

    species = (getattr(pet, "species", "") or "").lower()
    age = getattr(pet, "age", "")
    input_text = _clean_text(f"{species} age {age} {symptoms}")

    x = bundle["vectorizer"].transform([input_text])
    diagnosis = bundle["diag_model"].predict(x)[0]
    urgency = bundle["urg_model"].predict(x)[0]

    # Top causes/reco from condition profile.
    profile = CONDITION_PROFILES.get(diagnosis, {})
    possible_causes = profile.get("causes", ["Unknown"])
    recommendation = profile.get(
        "recommendation",
        "Please consult a veterinarian for a full clinical examination.",
    )

    # Optional confidence proxy from class probabilities.
    confidence = None
    if hasattr(bundle["diag_model"], "predict_proba"):
        probs = bundle["diag_model"].predict_proba(x)[0]
        confidence = float(max(probs))

    result = {
        "diagnosis": [diagnosis],
        "urgency_level": urgency,
        "recommendation": recommendation,
        "possible_causes": possible_causes,
        "model_used": "RandomForest-Synthetic-v1",
    }
    if confidence is not None:
        result["confidence"] = round(confidence, 3)
    return result
