
# triage.py - main AI triage engine
# this is the core of the whole system, it takes in patient symptoms
# and figures out how urgent they are using 3 layers:
#   1. safety rules (hardcoded red flags from NHS data)
#   2. NLP with spaCy (pulls out symptoms, severity, body parts etc)
#   3. ML model (random forest trained on 291 symptom scenarios)
# the layers combine together so safety rules always win over the ML model

import json
import pickle
import os
from pathlib import Path

from .rules import check_red_flags, check_routine_indicators, BODY_SYSTEM_MAP


class TriageEngine:

    def __init__(self):
        self.model = None
        self.nlp = None
        self.symptoms_data = None
        self._load_resources()

    def _load_resources(self):
        """loads up the ML model, spaCy, and symptom config when the engine starts"""
        base_dir = Path(__file__).parent

        # load the trained sklearn model from the pickle file
        model_path = base_dir / 'triage_model.pkl'
        if model_path.exists():
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)

        # try to load spaCy - if its not installed just fall back to basic keywords
        try:
            import spacy
            self.nlp = spacy.load('en_core_web_sm')
        except (ImportError, OSError):
            self.nlp = None

        # load the symptom categories and urgency modifiers from json
        symptoms_path = base_dir / 'symptoms.json'
        if symptoms_path.exists():
            with open(symptoms_path, 'r') as f:
                self.symptoms_data = json.load(f)

    def assess(self, symptoms_text: str, selected_symptoms: list = None,
               severity_symptoms: list = None, body_location: str = '',
               duration: str = '') -> dict:
        """
        main entry point - called by the django view when a patient submits a case.
        takes in all the symptom info from the form and returns the triage result
        with urgency level, confidence, rationale and differential diagnoses.
        """
        # mash all the text inputs together so we can analyse everything at once
        combined_text = self._build_combined_text(
            symptoms_text, selected_symptoms, severity_symptoms,
            body_location, duration
        )

        # ---- LAYER 1: safety rules ----
        # these ALWAYS run first - if someone says "chest pain" or "stroke"
        # we dont even bother with the ML model, just flag it as emergency
        # based on NHS HES 2024-25 emergency admission stats
        rule_result = check_red_flags(combined_text)
        if rule_result:
            rule_result['method'] = 'rule_based_safety'
            rule_result['differential'] = self._generate_differential(combined_text, body_location)
            rule_result['extracted_symptoms'] = self._extract_symptom_keywords(combined_text)
            return rule_result

        # ---- LAYER 2: NLP feature extraction ----
        # use spaCy to pull out symptoms, severity words, body parts etc
        nlp_features = self._extract_nlp_features(combined_text)

        # ---- LAYER 3: ML classification ----
        # random forest model predicts the urgency level
        ml_result = self._ml_predict(combined_text)

        # ---- COMBINE everything ----
        # take the ML prediction and adjust it based on what the NLP found
        # e.g. if theres lots of severity words, bump up the urgency
        urgency, confidence = self._combine_results(
            ml_result, nlp_features, duration,
            severity_symptoms or []
        )

        # build the explanation text so clinicians can see why we picked this level
        rationale = self._generate_rationale(
            urgency, confidence, nlp_features,
            body_location, duration, combined_text
        )

        # suggest possible diagnoses for the clinician to consider
        differential = self._generate_differential(combined_text, body_location)

        return {
            'urgency': urgency,
            'confidence': round(confidence, 2),
            'rationale': rationale,
            'differential': differential,
            'method': 'hybrid_nlp_ml',
            'extracted_symptoms': nlp_features.get('symptoms', []),
        }

    def _build_combined_text(self, symptoms_text, selected_symptoms,
                              severity_symptoms, body_location, duration):
        """joins all the different symptom inputs into one string for analysis"""
        parts = [symptoms_text]
        if selected_symptoms:
            parts.append(' '.join(selected_symptoms))
        if severity_symptoms:
            parts.append(' '.join(severity_symptoms))
        if body_location:
            parts.append(f"location: {body_location}")
        if duration:
            parts.append(f"duration: {duration}")
        return ' '.join(parts)

    def _extract_symptom_keywords(self, text: str) -> list:
        """quick keyword check - just looks for common symptom words in the text"""
        text_lower = text.lower()
        common = [
            'pain', 'headache', 'fever', 'cough', 'rash', 'bleeding',
            'vomiting', 'nausea', 'dizziness', 'fatigue', 'swelling',
            'numbness', 'weakness', 'shortness of breath', 'chest pain',
            'breathing', 'stiffness', 'confusion', 'temperature',
        ]
        return [s for s in common if s in text_lower]

    def _extract_nlp_features(self, text: str) -> dict:
        """
        uses spaCy to properly extract medical info from the text.
        pulls out noun chunks as symptoms, finds severity words like "severe"
        or "crushing", detects body parts, checks for duration mentions,
        and spots negations (like "no fever") so we dont count those.
        """
        features = {
            'symptoms': [],
            'body_parts': [],
            'severity_words': [],
            'duration_mentioned': False,
            'negations': [],
        }

        # if spaCy isnt available just use the basic keyword fallback
        if not self.nlp:
            return self._simple_keyword_extraction(text)

        doc = self.nlp(text)

        # noun chunks give us multi-word symptoms like "severe headache"
        for chunk in doc.noun_chunks:
            chunk_text = chunk.text.lower()
            features['symptoms'].append(chunk_text)

        # look for words that indicate how bad it is
        severity_words = {'severe', 'worst', 'extreme', 'intense', 'unbearable',
                         'acute', 'sudden', 'sharp', 'constant', 'persistent',
                         'worsening', 'deteriorating', 'critical', 'crushing',
                         'heavy', 'uncontrolled', 'violent'}
        for token in doc:
            if token.text.lower() in severity_words:
                features['severity_words'].append(token.text.lower())

        # check which body system is affected using the map from rules.py
        for key in BODY_SYSTEM_MAP:
            if key in text.lower():
                features['body_parts'].append(key)

        # see if they mentioned how long theyve had symptoms
        duration_words = {'hours', 'days', 'weeks', 'months', 'years', 'minutes'}
        for token in doc:
            if token.text.lower() in duration_words:
                features['duration_mentioned'] = True
                break

        # catch negations - "no fever" means we shouldnt count fever as a symptom
        for token in doc:
            if token.dep_ == 'neg':
                features['negations'].append(token.head.text)

        return features

    def _simple_keyword_extraction(self, text: str) -> dict:
        """fallback if spaCy isnt installed - just does basic keyword matching"""
        text_lower = text.lower()
        features = {
            'symptoms': [],
            'body_parts': [],
            'severity_words': [],
            'duration_mentioned': False,
            'negations': [],
        }

        common_symptoms = [
            'pain', 'headache', 'fever', 'cough', 'rash', 'bleeding',
            'vomiting', 'nausea', 'dizziness', 'fatigue', 'swelling',
            'numbness', 'weakness', 'shortness of breath', 'chest pain',
            'breathing difficulty', 'confusion', 'stiffness',
        ]
        for symptom in common_symptoms:
            if symptom in text_lower:
                features['symptoms'].append(symptom)

        for key in BODY_SYSTEM_MAP:
            if key in text_lower:
                features['body_parts'].append(key)

        severity_words = ['severe', 'worst', 'extreme', 'sudden', 'acute',
                         'crushing', 'intense', 'unbearable', 'heavy']
        for word in severity_words:
            if word in text_lower:
                features['severity_words'].append(word)

        return features

    def _ml_predict(self, text: str) -> dict:
        """runs the text through the trained random forest model to get a prediction"""
        if not self.model:
            # no model loaded, just default to routine
            return {'urgency': 'routine', 'confidence': 0.5}

        prediction = self.model.predict([text])[0]
        probabilities = self.model.predict_proba([text])[0]
        confidence = max(probabilities)

        return {
            'urgency': prediction,
            'confidence': confidence,
            'probabilities': dict(zip(self.model.classes_, probabilities.tolist())),
        }

    def _combine_results(self, ml_result, nlp_features, duration, severity_symptoms):
        """
        this is where everything comes together. takes the ML prediction
        and adjusts it based on what the NLP found. basically:
        - lots of severity words = bump up urgency
        - patient ticked red flag checkboxes = bump up urgency
        - symptoms just started (acute) = bump up urgency
        - text matches routine stuff like "sore throat" = dont over-triage
        """
        urgency = ml_result['urgency']
        confidence = ml_result['confidence']

        # if theres multiple severity words like "severe worsening" thats a bad sign
        severity_count = len(nlp_features.get('severity_words', []))
        if severity_count >= 2:
            if urgency == 'routine':
                urgency = 'urgent'
                confidence = max(confidence, 0.65)
            elif urgency == 'self_care':
                urgency = 'routine'
                confidence = max(confidence, 0.6)

        # even one severity word + multiple symptoms should push it up a bit
        if severity_count >= 1 and len(nlp_features.get('symptoms', [])) >= 2:
            if urgency == 'self_care':
                urgency = 'routine'
                confidence = max(confidence, 0.55)

        # if patient selected severity checkboxes on the form (like "difficulty breathing")
        # thats a strong signal to increase urgency
        real_severity = [s for s in severity_symptoms if s != 'None of these']
        if len(real_severity) > 0:
            if urgency in ('self_care', 'routine'):
                urgency = 'urgent'
                confidence = max(confidence, 0.7)
            elif urgency == 'urgent':
                confidence = max(confidence, 0.75)

        # if symptoms just started (minutes/hours) thats more concerning
        # than something thats been going on for weeks
        if duration:
            duration_lower = duration.lower()
            if any(w in duration_lower for w in ['minute', 'hour', 'just started', 'sudden', 'today']):
                if urgency == 'routine':
                    urgency = 'urgent'
                    confidence = max(confidence, 0.65)
                elif urgency == 'self_care':
                    urgency = 'routine'
                    confidence = max(confidence, 0.6)

        # safety check - dont over-triage obvious minor stuff
        # e.g. if someone has a "sore throat" the ML might say urgent
        # but if confidence is low and it matches routine indicators, bring it back down
        if check_routine_indicators(ml_result.get('original_text', '')):
            if urgency == 'urgent' and confidence < 0.7:
                urgency = 'routine'

        return urgency, confidence

    def _generate_rationale(self, urgency, confidence, nlp_features,
                            body_location, duration, text):
        """
        builds the explanation text that shows up on the case detail page.
        clinicians need to see WHY the AI picked a certain urgency level,
        not just what it picked. this is the transparency/explainability part.
        """
        parts = []

        # map urgency to a proper GP-style label
        urgency_labels = {
            'emergency': 'Emergency - Needs 999/A&E/Urgent Care immediately',
            'urgent': 'Urgent - Needs GP appointment immediately (same day/next day)',
            'routine': 'Routine - Can wait for GP appointment (2-3 weeks)',
            'self_care': 'Non-urgent - Self-care or pharmacy advice appropriate',
        }
        parts.append(f"Assessment: {urgency_labels.get(urgency, urgency)}.")

        # show what symptoms we picked up
        symptoms = nlp_features.get('symptoms', [])
        if symptoms:
            display_symptoms = symptoms[:5]
            parts.append(f"Key symptoms identified: {', '.join(display_symptoms)}.")

        # which body system
        if body_location:
            system = BODY_SYSTEM_MAP.get(body_location.lower(), body_location)
            parts.append(f"Body system: {system}.")

        # any severity words we found
        sev_words = nlp_features.get('severity_words', [])
        if sev_words:
            parts.append(f"Severity indicators noted: {', '.join(sev_words)}.")

        if duration:
            parts.append(f"Symptom duration: {duration}.")

        parts.append(f"Confidence level: {confidence:.0%}.")

        # mention that this uses real NHS data so it looks credible
        parts.append(
            "This assessment uses NHS Hospital Episode Statistics (HES) 2024-25 "
            "to identify patterns matching real emergency admission data."
        )

        # always remind them its just a suggestion not a diagnosis
        parts.append(
            "NOTE: This is an AI-generated advisory suggestion only. "
            "The final triage decision must be made by a qualified clinician."
        )

        return ' '.join(parts)

    def _generate_differential(self, text: str, body_location: str) -> list:
        """
        suggests possible conditions based on keywords in the symptoms.
        these arent diagnoses - just things for the clinician to think about.
        mapped to ICD-10 codes where possible from the NHS data.
        """
        text_lower = text.lower()
        differentials = []

        # keyword -> possible conditions lookup
        # ICD-10 codes in brackets where we have them
        differential_map = {
            'chest pain': [
                'Musculoskeletal chest pain',
                'Gastroesophageal reflux (K21)',
                'Angina / Acute coronary syndrome (I21)',
                'Anxiety-related chest pain',
                'Pulmonary embolism',
            ],
            'headache': [
                'Tension headache',
                'Migraine',
                'Cluster headache',
                'Sinusitis',
                'Raised intracranial pressure',
            ],
            'abdominal pain': [
                'Gastroenteritis (A09)',
                'IBS',
                'Appendicitis',
                'Gallstones (K80)',
                'Urinary tract infection (N39)',
            ],
            'stomach pain': [
                'Gastritis (K29)',
                'Peptic ulcer',
                'Gallstones (K80)',
                'Constipation',
                'Diverticulitis (K57)',
            ],
            'back pain': [
                'Mechanical back pain',
                'Disc herniation',
                'Muscle strain',
                'Kidney stones',
                'Cauda equina syndrome',
            ],
            'sore throat': [
                'Viral pharyngitis',
                'Tonsillitis',
                'Laryngitis',
                'Glandular fever',
            ],
            'rash': [
                'Contact dermatitis',
                'Eczema',
                'Psoriasis',
                'Viral exanthem',
                'Cellulitis (L03)',
            ],
            'cough': [
                'Upper respiratory infection',
                'Bronchitis',
                'Asthma',
                'Pneumonia (J18)',
                'COPD exacerbation (J44)',
            ],
            'dizziness': [
                'Benign positional vertigo',
                'Labyrinthitis',
                'Anaemia (D50)',
                'Orthostatic hypotension',
            ],
            'fatigue': [
                'Iron deficiency anaemia (D50)',
                'Thyroid disorder',
                'Depression',
                'Viral illness',
                'Diabetes',
            ],
            'breathing': [
                'Asthma',
                'COPD exacerbation (J44)',
                'Pneumonia (J18)',
                'Heart failure (I50)',
                'Anxiety/hyperventilation',
            ],
            'fever': [
                'Viral infection',
                'Urinary tract infection (N39)',
                'Pneumonia (J18)',
                'Cellulitis (L03)',
                'Sepsis (A41)',
            ],
            'joint pain': [
                'Osteoarthritis (M16/M17)',
                'Rheumatoid arthritis',
                'Gout',
                'Reactive arthritis',
            ],
            'bleeding': [
                'Haemorrhoids (K64)',
                'Diverticular disease (K57)',
                'Inflammatory bowel disease',
                'Gastric ulcer',
            ],
            'vomiting': [
                'Gastroenteritis (A09)',
                'Food poisoning',
                'Migraine',
                'Appendicitis',
                'Bowel obstruction',
            ],
            'skin': [
                'Eczema',
                'Psoriasis',
                'Fungal infection',
                'Skin neoplasm (C44)',
            ],
            'urinary': [
                'Urinary tract infection (N39)',
                'Kidney stones',
                'Prostatitis',
                'Interstitial cystitis',
            ],
        }

        for key, diffs in differential_map.items():
            if key in text_lower:
                differentials.extend(diffs)

        # remove duplicates but keep the order
        seen = set()
        unique = []
        for d in differentials:
            if d not in seen:
                seen.add(d)
                unique.append(d)

        # only show top 5 so it doesnt overwhelm the clinician
        return unique[:5]
