# rules.py - safety rules for the triage engine
# these are the hard-coded red flags that ALWAYS override the ML model
# i got these from NHS HES (Hospital Episode Statistics) 2024-25 data
# basically looked at which symptoms have the highest emergency admission rates
# and made sure those always get flagged properly regardless of what the model thinks
#
# the idea is: a ML model can be wrong sometimes, but if someone types
# "chest pain" we cant afford to miss that. so rules > model always.


# emergency red flags - these trigger 999/A&E immediately
# each group is mapped to an ICD-10 code from the NHS data
EMERGENCY_RED_FLAGS = [
    # I21 Heart Attack - 94% ER rate
    'chest pain', 'heart attack', 'cardiac arrest', 'crushing chest',
    'chest tightness', 'angina',

    # J18 Pneumonia - 97% ER rate
    'difficulty breathing', "can't breathe", 'cannot breathe',
    'shortness of breath at rest', 'choking', 'airway obstruction',

    # I63 Stroke - 90% ER rate
    'stroke', 'facial drooping', 'face drooping', 'slurred speech',
    'sudden weakness one side', 'loss of consciousness', 'unconscious',
    'unresponsive',

    # A41 Sepsis - 95% ER rate
    'sepsis', 'mottled skin',

    # R29 Collapse - 94% ER rate
    'collapsed', 'unresponsive',

    # S72 Hip Fracture - 94% ER rate
    'broken hip', 'fractured hip', 'hip fracture',

    # J44 COPD severe
    'blue lips', 'cyanosis',

    # Seizures
    'seizure', 'fitting', 'convulsion',

    # Anaphylaxis
    'anaphylaxis', 'anaphylactic', 'severe allergic reaction',
    'throat swelling', 'tongue swelling',

    # X60 Overdose/Self-harm - 100% ER rate
    'overdose', 'poisoning', 'taken too many tablets',
    'taken too many pills', 'self-harm', 'self harm',

    # Severe bleeding
    'severe bleeding', 'heavy bleeding', 'arterial bleed',
    'uncontrolled bleeding',

    # Meningitis
    'meningitis', 'stiff neck with fever', 'rash that does not fade',
    'non-blanching rash',

    # W19 Falls with injury - 94% ER rate
    'head injury', 'loss of consciousness',
    # W10 Falls on stairs - 90% ER rate
    'fell down stairs', 'fallen down stairs', "can't move my leg",
    'cannot move', 'unable to move',

    # V03 Road traffic accident - 93% ER rate
    'hit by a car', 'road traffic accident', 'run over',

    # Pregnancy emergencies
    'heavy bleeding pregnant', 'waters broken premature',

    # Paediatric emergencies
    'baby not breathing', 'child unresponsive', 'baby floppy',
]

# urgent flags - need same-day GP appointment
# these are conditions with 40-80% emergency admission rates
# serious but not immediately life-threatening
URGENT_FLAGS = [
    # R10 Abdominal Pain - 67% ER rate
    'severe abdominal pain', 'severe stomach pain',

    # N39 UTI with systemic symptoms
    'blood in urine', 'unable to urinate', 'urinary retention',

    # A09 Gastroenteritis severe - 77% ER rate
    'persistent vomiting', 'unable to keep fluids down',

    # L03 Cellulitis - 81% ER rate
    'spreading redness', 'cellulitis', 'red line tracking',

    # K80 Gallstones
    'pain under right ribs',

    # Infection signs
    'high fever', 'fever over 39', 'temperature over 39',
    'fever not responding to paracetamol',

    # Other urgent stuff
    'blood in stool', 'vomiting blood',
    'worst headache ever', 'thunderclap headache', 'sudden severe headache',
    'new confusion', 'sudden vision loss',
    'unable to bear weight', 'possible fracture', 'deformity after injury',
    'suicidal thoughts',
    'rash non blanching', 'non-blanching rash',
    'rapidly spreading rash', 'cellulitis spreading',

    # W54 Dog bite - 79% ER rate
    'dog bite', 'animal bite',
]


# routine indicators - stuff that can wait for a normal GP appointment
# used to prevent over-triaging minor conditions
ROUTINE_INDICATORS = [
    # H25 Cataracts - 0% ER rate, all waitlist
    'cloudy vision', 'blurry vision gradually',

    # M17 Knee arthritis
    'knee stiffness', 'knee arthritis',

    # M16 Hip arthritis
    'hip arthritis', 'hip stiffness',

    # D50 Iron deficiency
    'low iron', 'iron deficiency',

    # common minor stuff that doesnt need urgent attention
    'sore throat', 'common cold', 'runny nose', 'mild cough',
    'mild headache', 'hayfever', 'hay fever', 'acne', 'verruca',
    'mild back pain', 'minor rash', 'mild stomach ache',
    'ingrowing toenail', 'athletes foot', 'mild constipation',
    'repeat prescription', 'medication review', 'routine blood test',
    'travel vaccine', 'routine check', 'smear test',
    'contraception', 'pill check', 'ear wax',
]


# maps body part keywords to their medical body system
# used in the rationale to say things like "Body system: cardiovascular"
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
    checks the patient text against all the red flag rules.
    this is the safety net - runs before the ML model and always takes priority.
    returns the urgency dict if a flag is found, None otherwise.
    """
    text_lower = text.lower()

    # check emergency flags first - these are the most dangerous
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

    # then check urgent flags
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
    """checks if the text matches any of the routine/minor condition patterns"""
    text_lower = text.lower()
    return any(indicator in text_lower for indicator in ROUTINE_INDICATORS)
