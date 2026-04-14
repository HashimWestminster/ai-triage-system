# AI Triage System - Westminster Surgery

This is my final year project for Computer Science at University of Westminster. Its an AI-powered triage system for GP surgeries - patients submit their symptoms through a form, the AI figures out how urgent it is, then clinicians review it and care navigators close the case.

**Hashim Khan - W1832028**  
**6COSC023W - Computer Science Final Project 2025-26**  
**University of Westminster**

---

## What its built with

| Layer | Tech |
|-------|------|
| Backend | Python 3.11, Django 4.2, Django REST Framework |
| Frontend | React 18, Vite, Tailwind CSS 4 |
| AI Engine | scikit-learn (Random Forest), spaCy (NLP) |
| Auth | JWT tokens (SimpleJWT) |
| Database | SQLite for dev, PostgreSQL for production |

---

## What you need before starting

- **Python 3.10+** - [python.org/downloads](https://www.python.org/downloads/)
- **Node.js 18+** - [nodejs.org](https://nodejs.org/)
- **Git** - [git-scm.com](https://git-scm.com/)

---

## How to set it up

### 1. Clone the repo

```bash
git clone <your-repo-url>
cd ai-triage-system
```

### 2. Backend

```bash
cd backend

# make a virtual environment
python -m venv venv

# activate it
# Windows (Command Prompt):
venv\Scripts\activate
# Windows (Git Bash / WSL):
source venv/Scripts/activate
# macOS / Linux:
source venv/bin/activate

# install everything
pip install -r requirements.txt

# set up the database
python manage.py migrate

# create the demo accounts and surgery hours
python manage.py seed_demo_data

# (optional) retrain the AI model - theres already a trained one included
# python ai_engine/train_model.py

# start the server
python manage.py runserver
```

Backend runs at **http://localhost:8000**.

### 3. Frontend

Open a **new terminal window**:

```bash
cd frontend

# install node packages
npm install

# start it up
npm run dev
```

Frontend runs at **http://localhost:5173**.

### 4. Use it

Go to **http://localhost:5173** in your browser and log in with one of the demo accounts below.

---

## Demo accounts

| Role | Email | Password |
|------|-------|----------|
| Patient | john.doe@email.com | patient123! |
| Patient | jane.smith@email.com | patient123! |
| Patient | adilkhan1969@hotmail.com | patient123! |
| Clinician | dr.smith@clinic.nhs.uk | clinician123! |
| Clinician | dr.jones@clinic.nhs.uk | clinician123! |
| Care Navigator | emily@clinic.nhs.uk | navigator123! |
| Care Navigator | reception@clinic.nhs.uk | navigator123! |
| Site Admin | admin@clinic.nhs.uk | superuser123! |

---

## The 4 roles

### Patient
- registers and logs in
- submits triage cases through a multi-step symptom form
- can see their own case history and whats happening with each one
- can only submit during surgery opening hours

### Clinician
- sees all the submitted cases
- can see the AI triage suggestion with confidence, rationale, and differential diagnoses
- makes their own clinical decision on each case
- can view dashboard stats and how often they agree with the AI

### Care Navigator
- sees all cases
- closes cases after the clinician has made their decision (picks a closure reason like "appointment booked" or "self-care advised")
- can view the user list and dashboard stats

### Site Admin (Superuser)
- can do everything a care navigator can
- can configure the surgery opening hours (patients get blocked outside these times)
- manages all users in the system

---

## Surgery hours

The system enforces opening hours so patients can only submit cases when the surgery is open. By default:

- **Mon-Fri:** 08:00 - 18:00
- **Saturday:** 09:00 - 12:00
- **Sunday:** Closed

The site admin can change these from the Surgery Hours page. When its closed, patients see a banner saying when it opens next and the submit button is greyed out.

---

## How the AI triage works

The AI uses a 3-layer approach:

1. **Safety rules** - hardcoded red flags from NHS HES 2024-25 data (e.g. "chest pain" always = Emergency). these always override the ML model so dangerous symptoms never get missed.
2. **NLP (spaCy)** - extracts symptoms, severity words like "severe" or "crushing", body parts, and duration mentions from the free text.
3. **ML model (Random Forest)** - trained on 291 symptom scenarios mapped to real NHS admission data. uses TF-IDF to turn text into numbers then 200 decision trees vote on the urgency.

The layers combine together - safety rules win first, then NLP features adjust the ML prediction (e.g. multiple severity words bump up urgency, acute onset increases urgency). The output is: urgency level, confidence score, explanation rationale, and up to 5 differential diagnoses for the clinician.

---

## File structure

```
ai-triage-system/
├── backend/
│   ├── accounts/          # user model, auth, surgery hours
│   ├── ai_engine/         # triage engine, safety rules, ML model
│   ├── cases/             # case model, API views, serializers
│   ├── triage_project/    # django settings and URL config
│   ├── manage.py
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/    # Layout wrapper with nav bar
│   │   ├── context/       # auth context (JWT tokens)
│   │   ├── pages/         # all the page components
│   │   ├── services/      # axios API client
│   │   ├── App.jsx        # routing
│   │   └── main.jsx       # entry point
│   ├── package.json
│   └── vite.config.js
│
├── .gitignore
└── README.md
```

---

## API endpoints

| Method | Endpoint | What it does | Who can use it |
|--------|----------|-------------|----------------|
| POST | `/api/accounts/register/` | register a new patient | anyone |
| POST | `/api/accounts/login/` | login with email + password | anyone |
| POST | `/api/accounts/token/refresh/` | refresh the JWT token | logged in users |
| GET | `/api/accounts/me/` | get current user profile | logged in users |
| GET | `/api/accounts/users/` | list all users | navigators / admin |
| GET | `/api/accounts/surgery-status/` | check if surgery is open | anyone |
| GET/PUT | `/api/accounts/surgery-hours/` | view / update hours | admin |
| POST | `/api/cases/submit/` | submit a triage case | patients |
| GET | `/api/cases/my-cases/` | get your own cases | patients |
| GET | `/api/cases/list/` | all cases (filterable) | staff |
| GET | `/api/cases/<id>/` | full case detail | case owner / staff |
| POST | `/api/cases/<id>/decide/` | clinician makes decision | clinicians |
| POST | `/api/cases/<id>/close/` | close a case | navigators / admin |
| GET | `/api/cases/dashboard/stats/` | dashboard analytics | staff |

---

## Troubleshooting

**"Module not found" when running Django:**  
make sure you activated the virtual environment first (`source venv/Scripts/activate` or `venv\Scripts\activate`).

**Frontend says "Unable to reach the server":**  
the django backend needs to be running on port 8000. the vite dev server proxies `/api` requests to it.

**"Surgery is currently closed" when submitting:**  
log in as the site admin (admin@clinic.nhs.uk) and change the surgery hours, or test during the configured opening times.

**"No active account found" on login:**  
run `python manage.py seed_demo_data` to create the demo accounts.
