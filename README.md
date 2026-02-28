# AI Triage System — Addison Road Medical Practice

An AI-powered patient triage system built for GP surgeries. Patients submit symptom forms online, a hybrid AI engine (safety rules + NLP + machine learning) triages them by urgency, and clinicians review the suggestions before care navigators close the case.

**Student:** Hashim Khan (W1832028)  
**Module:** 6COSC023W — Computer Science Final Project 2025-26  
**University of Westminster**

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, Django 4.2, Django REST Framework |
| Frontend | React 18, Vite, Tailwind CSS 4 |
| AI Engine | scikit-learn (Random Forest), spaCy (NLP) |
| Auth | JWT (SimpleJWT) |
| Database | SQLite (dev) / PostgreSQL (production) |

---

## Prerequisites

Make sure you have these installed before starting:

- **Python 3.10+** — [python.org/downloads](https://www.python.org/downloads/)
- **Node.js 18+** — [nodejs.org](https://nodejs.org/)
- **Git** — [git-scm.com](https://git-scm.com/)

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd ai-triage-system
```

### 2. Backend setup

```bash
cd backend

# Create a virtual environment
python -m venv venv

# Activate it
# Windows (Command Prompt):
venv\Scripts\activate
# Windows (Git Bash / WSL):
source venv/Scripts/activate
# macOS / Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Seed the database with demo users and surgery hours
python manage.py seed_demo_data

# (Optional) Train the AI model — a pre-trained model is included
# python ai_engine/train_model.py

# Start the backend server
python manage.py runserver
```

The backend API will be running at **http://localhost:8000**.

### 3. Frontend setup

Open a **second terminal**:

```bash
cd frontend

# Install Node dependencies
npm install

# Start the development server
npm run dev
```

The frontend will be running at **http://localhost:5173**.

### 4. Open the app

Go to **http://localhost:5173** in your browser.

---

## Demo Accounts

| Role | Email | Password |
|------|-------|----------|
| **Patient** | john.doe@email.com | patient123! |
| **Patient** | jane.smith@email.com | patient123! |
| **Patient** | adilkhan1969@hotmail.com | patient123! |
| **Clinician** | dr.smith@clinic.nhs.uk | clinician123! |
| **Clinician** | dr.jones@clinic.nhs.uk | clinician123! |
| **Care Navigator** | emily@clinic.nhs.uk | navigator123! |
| **Care Navigator** | reception@clinic.nhs.uk | navigator123! |
| **Site Administrator** | admin@clinic.nhs.uk | superuser123! |

---

## User Roles

### Patient
- Register an account and log in
- Submit triage cases through a multi-step symptom form
- View their own case history and status updates
- Can only submit cases during configured surgery hours

### Clinician
- View all submitted patient cases
- See the AI triage suggestion (urgency level, confidence, rationale, differential diagnoses)
- Make their own clinical assessment and submit a decision
- View dashboard statistics and AI agreement rates

### Care Navigator
- View all cases in the system
- Close cases that have been decided by a clinician (with a closure reason)
- View the user list
- View dashboard statistics

### Site Administrator (Superuser)
- Everything a care navigator can do
- Configure surgery opening hours (patients are blocked outside these times)
- Manage all users in the system

---

## Surgery Hours

The system enforces configurable opening hours. Patients can only submit new cases during these windows. By default:

- **Monday–Friday:** 08:00 – 18:00
- **Saturday:** 09:00 – 12:00
- **Sunday:** Closed

The Site Administrator can change these from the **Surgery Hours** page. Outside opening hours, patients see a banner explaining when the surgery opens next, and the submit button is disabled.

---

## AI Triage Engine

The AI uses a three-layer hybrid approach:

1. **Safety Rules** — Hard-coded red flags from NHS HES 2024-25 data (e.g. chest pain → Emergency). These always override the ML model.
2. **NLP Feature Extraction** — spaCy extracts symptom keywords, severity modifiers, body system, and duration from free text.
3. **ML Classification** — A Random Forest classifier (200 trees, TF-IDF features) trained on 291 symptom scenarios mapped to NHS admission data.

The layers are combined: safety rules take priority, then NLP modifiers adjust the ML prediction. The output includes an urgency level, confidence score, rationale, and differential diagnoses.

---

## Project Structure

```
ai-triage-system/
├── backend/
│   ├── accounts/          # User model, auth, surgery hours
│   ├── ai_engine/         # Triage engine, rules, ML model
│   ├── cases/             # Case model, views, serializers
│   ├── triage_project/    # Django settings, URLs
│   ├── manage.py
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/    # Layout wrapper
│   │   ├── context/       # Auth context (JWT)
│   │   ├── pages/         # All page components
│   │   ├── services/      # Axios API client
│   │   ├── App.jsx        # Routing
│   │   └── main.jsx       # Entry point
│   ├── package.json
│   └── vite.config.js
│
├── .gitignore
└── README.md
```

---

## API Endpoints

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| POST | `/api/accounts/register/` | Patient registration | Public |
| POST | `/api/accounts/login/` | Email + password login | Public |
| POST | `/api/accounts/token/refresh/` | Refresh JWT token | Authenticated |
| GET | `/api/accounts/me/` | Current user profile | Authenticated |
| GET | `/api/accounts/users/` | List users | Navigator / Admin |
| GET | `/api/accounts/surgery-status/` | Is surgery open now? | Public |
| GET/PUT | `/api/accounts/surgery-hours/` | View / update hours | Admin |
| POST | `/api/cases/submit/` | Submit a triage case | Patient |
| GET | `/api/cases/my-cases/` | Patient's own cases | Patient |
| GET | `/api/cases/list/` | All cases (filterable) | Staff |
| GET | `/api/cases/<id>/` | Case detail | Owner / Staff |
| POST | `/api/cases/<id>/decide/` | Clinician decision | Clinician |
| POST | `/api/cases/<id>/close/` | Close a case | Navigator / Admin |
| GET | `/api/cases/dashboard/stats/` | Dashboard analytics | Staff |

---

## Troubleshooting

**"Module not found" when running Django:**  
Make sure you activated the virtual environment (`source venv/Scripts/activate` or `venv\Scripts\activate`).

**Frontend shows "Unable to reach the server":**  
The backend must be running on port 8000. Vite proxies `/api` requests to it automatically.

**"Surgery is currently closed" when trying to submit a case:**  
Log in as the Site Administrator and change the surgery hours, or test during the configured opening times.

**Login returns "No active account found":**  
Run `python manage.py seed_demo_data` to create the demo accounts.
