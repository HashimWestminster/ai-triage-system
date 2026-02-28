"""
Red-flag safety rules for the AI triage engine.
These rules ALWAYS override the ML model to ensure patient safety.

Based on NHS HES 2024-25 data 

"""

# =============================================================================
# Red-flag symptoms that ALWAYS trigger Emergency (999/A&E)
# Derived from ICD-10 codes 
# =============================================================================
EMERGENCY_RED_FLAGS = [
    # I21 Heart Attack 
    'chest pain', 'heart attack', 'cardiac arrest', 'crushing chest',
    'chest tightness', 'angina',

    # J18 Pneumonia 
    'difficulty breathing', "can't breathe", 'cannot breathe',
    'shortness of breath at rest', 'choking', 'airway obstruction',

    # I63 Stroke 
    'stroke', 'facial drooping', 'face drooping', 'slurred speech',
    'sudden weakness one side', 'loss of consciousness', 'unconscious',
    'unresponsive',

    # A41 Sepsis 
    'sepsis', 'mottled skin',

    # R29 Collapse 
    'collapsed', 'unresponsive',

    # S72 Hip Fracture 
    'broken hip', 'fractured hip', 'hip fracture',

    # J44 COPD severe 
    'blue lips', 'cyanosis',

    # Seizures
    'seizure', 'fitting', 'convulsion',

    # Anaphylaxis
    'anaphylaxis', 'anaphylactic', 'severe allergic reaction',
    'throat swelling', 'tongue swelling',

    # X60 Overdose/Self-harm 
    'overdose', 'poisoning', 'taken too many tablets',
    'taken too many pills', 'self-harm', 'self harm',

    # Severe bleeding
    'severe bleeding', 'heavy bleeding', 'arterial bleed',
    'uncontrolled bleeding',

    # Meningitis
    'meningitis', 'stiff neck with fever', 'rash that does not fade',
    'non-blanching rash',

    # W19 Falls with injury 
    'head injury', 'loss of consciousness',
    # W10 Falls on stairs 
    'fell down stairs', 'fallen down stairs', "can't move my leg",
    'cannot move', 'unable to move',

    # V03 Road traffic accident
    'hit by a car', 'road traffic accident', 'run over',

    # Pregnancy emergencies
    'heavy bleeding pregnant', 'waters broken premature',

    # Paediatric
    'baby not breathing', 'child unresponsive', 'baby floppy',
]

# =============================================================================
# Symptoms that trigger Urgent (same-day GP)
# Derived from ICD-10 codes with 40-80% emergency rate
# =============================================================================
URGENT_FLAGS = [
    # R10 Abdominal Pain 
    'severe abdominal pain', 'severe stomach pain',

    # N39 UTI with systemic symptoms 
    'blood in urine', 'unable to urinate', 'urinary retention',

    # A09 Gastroenteritis severe 
    'persistent vomiting', 'unable to keep fluids down',

    # L03 Cellulitis 
    'spreading redness', 'cellulitis', 'red line tracking',

    # K80 Gallstones 
    'pain under right ribs',

    # Infection signs
    'high fever', 'fever over 39', 'temperature over 39',
    'fever not responding to paracetamol',

    # Other urgent
    'blood in stool', 'vomiting blood',
    'worst headache ever', 'thunderclap headache', 'sudden severe headache',
    'new confusion', 'sudden vision loss',
    'unable to bear weight', 'possible fracture', 'deformity after injury',
    'suicidal thoughts',
    'rash non blanching', 'non-blanching rash',
    'rapidly spreading rash', 'cellulitis spreading',

    # W54 Dog bite 
    'dog bite', 'animal bite',
]


ROUTINE_INDICATORS = [
    # H25 Cataracts 
    'cloudy vision', 'blurry vision gradually',

    # M17 Knee arthritis 
    'knee stiffness', 'knee arthritis',

    # M16 Hip arthritis 
    'hip arthritis', 'hip stiffness',

    # D50 Iron deficiency 
    'low iron', 'iron deficiency',

    # Common minor conditions
    'sore throat', 'common cold', 'runny nose', 'mild cough',
    'mild headache', 'hayfever', 'hay fever', 'acne', 'verruca',
    'mild back pain', 'minor rash', 'mild stomach ache',
    'ingrowing toenail', 'athletes foot', 'mild constipation',
    'repeat prescription', 'medication review', 'routine blood test',
    'travel vaccine', 'routine check', 'smear test',
    'contraception', 'pill check', 'ear wax',
]


BODY_SYSTEM_MAP = {
    'chest': 'cardiovascular/respiratory',
    'head': 'neurological',
    'abdomen': 'gastrointestinal',
    'stomach': 'gastrointestinal',
    'throat': 'ENT/respiratory',
    'skin': 'dermatological',
    'back': 'musculoskeletal',
    'joint': 'musculoskeletal',
    'knee': 'musculoskeletal',
    'hip': 'musculoskeletal',
    'eye': 'ophthalmological',
    'ear': 'ENT',
    'urinary': 'urological',
    'urine': 'urological',
    'mental': 'psychological',
    'breathing': 'respiratory',
    'heart': 'cardiovascular',
    'leg': 'musculoskeletal/vascular',
}


def check_red_flags(text: str) -> dict | None:
    """
    Check text against red-flag rules. Returns urgency if a red flag is found.
    This is the SAFETY NET — it always takes priority over the ML model.

    Based on NHS HES 2024-25 emergency admission data.
    """
    text_lower = text.lower()

    # Check emergency flags first
    for flag in EMERGENCY_RED_FLAGS:
        if flag in text_lower:
            return {
                'urgency': 'emergency',
                'confidence': 0.95,
                'triggered_rule': flag,
                'rationale': (
                    f"SAFETY ALERT: The symptom description contains '{flag}' which is "
                    f"a clinical red flag requiring immediate medical attention. "
                    f"NHS data shows conditions matching this pattern have >80% "
                    f"emergency admission rates. "
                    f"This has been classified as Emergency based on clinical safety rules."
                ),
            }

    # Check urgent flags
    for flag in URGENT_FLAGS:
        if flag in text_lower:
            return {
                'urgency': 'urgent',
                'confidence': 0.85,
                'triggered_rule': flag,
                'rationale': (
                    f"The symptom description contains '{flag}' which indicates "
                    f"a condition requiring urgent medical review within 1-2 days. "
                    f"NHS admission data shows elevated emergency rates for this pattern."
                ),
            }

    return None


def check_routine_indicators(text: str) -> bool:
    """Check if text matches routine/self-care patterns."""
    text_lower = text.lower()
    return any(indicator in text_lower for indicator in ROUTINE_INDICATORS)
