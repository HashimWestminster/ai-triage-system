
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
        """Load the ML model, spaCy NLP, and symptom mappings."""
        base_dir = Path(__file__).parent

        # Load ML model
        model_path = base_dir / 'triage_model.pkl'
        if model_path.exists():
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)

        # Load spaCy (graceful fallback if not available)
        try:
            import spacy
            self.nlp = spacy.load('en_core_web_sm')
        except (ImportError, OSError):
            self.nlp = None

        # Load symptom data
        symptoms_path = base_dir / 'symptoms.json'
        if symptoms_path.exists():
            with open(symptoms_path, 'r') as f:
                self.symptoms_data = json.load(f)

    def assess(self, symptoms_text: str, selected_symptoms: list = None,
               severity_symptoms: list = None, body_location: str = '',
               duration: str = '') -> dict:
        """
        Assess patient symptoms and return an advisory urgency suggestion.

        This is the main entry point called by the Django view when a patient
        submits a case.

        Args:
            symptoms_text: Free-text description of symptoms
            selected_symptoms: List of structured symptom selections from the form
            severity_symptoms: List of severity/red-flag symptoms selected
            body_location: Body area affected (from form selection)
            duration: How long symptoms have been present

        Returns:
            dict with urgency, confidence, rationale, differential, and method
        """
        # Combine all text inputs for analysis
        combined_text = self._build_combined_text(
            symptoms_text, selected_symptoms, severity_symptoms,
            body_location, duration
        )

        # =====================================================================
        # LAYER 1: Safety rules check (ALWAYS runs first)
        # Based on NHS HES 2024-25 emergency admission rates
        # =====================================================================
        rule_result = check_red_flags(combined_text)
        if rule_result:
            rule_result['method'] = 'rule_based_safety'
            rule_result['differential'] = self._generate_differential(combined_text, body_location)
            rule_result['extracted_symptoms'] = self._extract_symptom_keywords(combined_text)
            return rule_result

        # =====================================================================
        # LAYER 2: NLP feature extraction (spaCy)
        # =====================================================================
        nlp_features = self._extract_nlp_features(combined_text)

        # =====================================================================
        # LAYER 3: ML classification (scikit-learn)
        # =====================================================================
        ml_result = self._ml_predict(combined_text)

        # =====================================================================
        # COMBINE: Merge ML + NLP + duration modifiers
        # =====================================================================
        urgency, confidence = self._combine_results(
            ml_result, nlp_features, duration,
            severity_symptoms or []
        )

        # Generate explainable rationale
        rationale = self._generate_rationale(
            urgency, confidence, nlp_features,
            body_location, duration, combined_text
        )

        # Generate differential diagnosis suggestions
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
        """Combine all symptom information into a single text for analysis."""
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
        """Quick keyword extraction for display purposes."""
        text_lower = text.lower()
        common = [
            'pain', 'headache', 'fever', 'cough', 'rash', 'bleeding',
            'vomiting', 'nausea', 'dizziness', 'fatigue', 'swelling',
            'numbness', 'weakness', 'shortness of breath', 'chest pain',
            'breathing', 'stiffness', 'confusion', 'temperature',
        ]
        return [s for s in common if s in text_lower]

    def _extract_nlp_features(self, text: str) -> dict:
        """Use spaCy to extract medical entities and features from text."""
        features = {
            'symptoms': [],
            'body_parts': [],
            'severity_words': [],
            'duration_mentioned': False,
            'negations': [],
        }

        if not self.nlp:
            return self._simple_keyword_extraction(text)

        doc = self.nlp(text)

        # Extract noun phrases as potential symptoms
        for chunk in doc.noun_chunks:
            chunk_text = chunk.text.lower()
            features['symptoms'].append(chunk_text)

        # Look for severity modifiers
        severity_words = {'severe', 'worst', 'extreme', 'intense', 'unbearable',
                         'acute', 'sudden', 'sharp', 'constant', 'persistent',
                         'worsening', 'deteriorating', 'critical', 'crushing',
                         'heavy', 'uncontrolled', 'violent'}
        for token in doc:
            if token.text.lower() in severity_words:
                features['severity_words'].append(token.text.lower())

        # Check for body parts
        for key in BODY_SYSTEM_MAP:
            if key in text.lower():
                features['body_parts'].append(key)

        # Check for duration mentions
        duration_words = {'hours', 'days', 'weeks', 'months', 'years', 'minutes'}
        for token in doc:
            if token.text.lower() in duration_words:
                features['duration_mentioned'] = True
                break

        # Check for negations
        for token in doc:
            if token.dep_ == 'neg':
                features['negations'].append(token.head.text)

        return features

    def _simple_keyword_extraction(self, text: str) -> dict:
        """Fallback keyword extraction without spaCy."""
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
        """Use the trained ML model to predict urgency."""
        if not self.model:
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
        Combine ML prediction with NLP features and clinical modifiers.

        The combination logic ensures that:
        - Severity words increase urgency
        - Structured form severity selections increase urgency
        - Acute onset (minutes/hours) increases urgency
        - Chronic duration does not decrease below routine
        """
        urgency = ml_result['urgency']
        confidence = ml_result['confidence']

        # Severity modifier: multiple severity words = higher urgency
        severity_count = len(nlp_features.get('severity_words', []))
        if severity_count >= 2:
            if urgency == 'routine':
                urgency = 'urgent'
                confidence = max(confidence, 0.65)
            elif urgency == 'self_care':
                urgency = 'routine'
                confidence = max(confidence, 0.6)

        # Single strong severity word with relevant symptom
        if severity_count >= 1 and len(nlp_features.get('symptoms', [])) >= 2:
            if urgency == 'self_care':
                urgency = 'routine'
                confidence = max(confidence, 0.55)

        # Structured form severity symptoms increase urgency
        real_severity = [s for s in severity_symptoms if s != 'None of these']
        if len(real_severity) > 0:
            if urgency in ('self_care', 'routine'):
                urgency = 'urgent'
                confidence = max(confidence, 0.7)
            elif urgency == 'urgent':
                confidence = max(confidence, 0.75)

        # Duration modifier
        if duration:
            duration_lower = duration.lower()
            if any(w in duration_lower for w in ['minute', 'hour', 'just started', 'sudden', 'today']):
                # Acute onset -> increase urgency
                if urgency == 'routine':
                    urgency = 'urgent'
                    confidence = max(confidence, 0.65)
                elif urgency == 'self_care':
                    urgency = 'routine'
                    confidence = max(confidence, 0.6)

        # Routine indicators check — prevent over-triaging minor issues
        if check_routine_indicators(ml_result.get('original_text', '')):
            if urgency == 'urgent' and confidence < 0.7:
                urgency = 'routine'

        return urgency, confidence

    def _generate_rationale(self, urgency, confidence, nlp_features,
                            body_location, duration, text):
        """
        Generate an explainable rationale for the triage suggestion.
        This satisfies the project requirement for "transparent AI outputs" (NFR4).
        """
        parts = []

        # Urgency explanation with GP-specific labels
        urgency_labels = {
            'emergency': 'Emergency - Needs 999/A&E/Urgent Care immediately',
            'urgent': 'Urgent - Needs GP appointment immediately (same day/next day)',
            'routine': 'Routine - Can wait for GP appointment (2-3 weeks)',
            'self_care': 'Non-urgent - Self-care or pharmacy advice appropriate',
        }
        parts.append(f"Assessment: {urgency_labels.get(urgency, urgency)}.")

        # Symptoms identified
        symptoms = nlp_features.get('symptoms', [])
        if symptoms:
            display_symptoms = symptoms[:5]
            parts.append(f"Key symptoms identified: {', '.join(display_symptoms)}.")

        # Body system
        if body_location:
            system = BODY_SYSTEM_MAP.get(body_location.lower(), body_location)
            parts.append(f"Body system: {system}.")

        # Severity
        sev_words = nlp_features.get('severity_words', [])
        if sev_words:
            parts.append(f"Severity indicators noted: {', '.join(sev_words)}.")

        # Duration
        if duration:
            parts.append(f"Symptom duration: {duration}.")

        # Confidence
        parts.append(f"Confidence level: {confidence:.0%}.")

        # NHS data context
        parts.append(
            "This assessment uses NHS Hospital Episode Statistics (HES) 2024-25 "
            "to identify patterns matching real emergency admission data."
        )

        # Clinical safety disclaimer
        parts.append(
            "NOTE: This is an AI-generated advisory suggestion only. "
            "The final triage decision must be made by a qualified clinician."
        )

        return ' '.join(parts)

    def _generate_differential(self, text: str, body_location: str) -> list:
        """
        Generate possible differential diagnosis suggestions.
        These are NOT definitive diagnoses — they are possibilities for
        the clinician to consider during their review.
        """
        text_lower = text.lower()
        differentials = []

        # Keyword-based differential suggestions mapped to NHS data
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


        seen = set()
        unique = []
        for d in differentials:
            if d not in seen:
                seen.add(d)
                unique.append(d)

        return unique[:5]
