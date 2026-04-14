# AI Triage System

An AI-powered patient triage system designed for GP surgeries. Patients submit their symptoms online, a hybrid AI engine assesses the urgency, and clinical staff review and action the cases.

Built as a Final Year Project for **6COSC023W - Computer Science Final Project 2025-26** at the **University of Westminster**.

## Features

- **AI-Powered Triage** - three-layer hybrid engine (safety rules, NLP, machine learning) classifies patient symptoms into four urgency levels: Emergency, Urgent, Routine, and Self-care
- **Role-Based Access** - four distinct user roles (Patient, Clinician, Care Navigator, Site Administrator) each with their own dashboard and permissions
- **Clinical Decision Support** - AI provides confidence scores, explainable rationale, and differential diagnosis suggestions for clinicians to review
- **Surgery Hours Enforcement** - configurable opening hours that restrict when patients can submit cases
- **Audit Trail** - complete logging of all actions on every case for clinical governance
- **Responsive UI** - works on desktop and mobile

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, Django, Django REST Framework |
| Frontend | React, Vite, Tailwind CSS |
| AI/ML | scikit-learn, spaCy, TF-IDF, Random Forest |
| Authentication | JWT (SimpleJWT) |
| Database | SQLite (dev) / PostgreSQL (prod) |

## AI Triage Engine

The system uses a three-layer hybrid approach to assess patient symptoms:

1. **Safety Rules** — hard-coded red-flag patterns derived from NHS Hospital Episode Statistics (HES) 2024-25 data. These always take priority to ensure dangerous symptoms like chest pain or stroke signs are never under-triaged.
2. **NLP Feature Extraction** — spaCy processes the free-text input to extract symptom entities, severity modifiers, body system mapping, duration context, and negation detection.
3. **ML Classification** — a Random Forest classifier (200 trees, TF-IDF vectorisation with trigrams) trained on 291 clinically-annotated symptom scenarios predicts the urgency level with a confidence score.

The layers combine so that safety rules override ML predictions, and NLP-derived features (severity, acuity, structured inputs) adjust the final output. Every assessment includes a human-readable rationale and up to five differential diagnosis suggestions mapped to ICD-10 codes.

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

## User Roles

| Role | Capabilities |
|------|-------------|
| **Patient** | Submit symptom forms, view own case history and status |
| **Clinician** | Review all cases, view AI suggestions, make triage decisions |
| **Care Navigator** | Close decided cases with action outcomes, view user list |
| **Site Administrator** | Configure surgery hours, manage users, full system access |

## License

This project was developed for academic purposes as part of a university final year project.
