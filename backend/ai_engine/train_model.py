# train_model.py - trains the ML model for the triage system
# uses scikit-learn with a TF-IDF + Random Forest pipeline
# the training data is 291 symptom scenarios that i mapped to NHS HES data
# each one has the ICD-10 code and real emergency admission rate
#
# to retrain just run: python ai_engine/train_model.py
# it saves the model as triage_model.pkl which the triage engine loads

import json
import os
import random
import pickle
from pathlib import Path


# training data - 291 samples across 4 urgency levels
# each sample is a (symptom text, urgency label) pair
# annotated with NHS HES ICD-10 codes and real ER admission rates
TRAINING_DATA = [


    # J18 Pneumonia (97% ER rate, 242,293 emergency admissions)
    ("severe pneumonia with high fever difficulty breathing and cough", "emergency"),
    ("coughing up blood and unable to breathe properly fever over 39", "emergency"),
    ("elderly patient very unwell with chest infection and confusion", "emergency"),
    ("breathing very fast shallow breaths and high temperature cough", "emergency"),

    # R07 Chest Pain (92% ER rate, 232,851 emergency admissions)
    ("severe crushing chest pain radiating to left arm with sweating", "emergency"),
    ("sudden onset chest tightness with jaw pain and nausea", "emergency"),
    ("sharp chest pain worse when breathing in and very short of breath", "emergency"),
    ("chest pain and tightness in centre of chest spreading to neck", "emergency"),

    # I21 Acute Heart Attack (94% ER rate, 75,962 emergency admissions)
    ("suspected heart attack crushing pain in chest arm and jaw", "emergency"),
    ("severe chest pain with cold sweats and feeling of doom", "emergency"),
    ("heavy pressure on chest with left arm numbness and nausea", "emergency"),

    # I63 Stroke (90% ER rate, 74,490 emergency admissions)
    ("suspected stroke face drooping one side cannot lift arm", "emergency"),
    ("sudden weakness on one side of body and slurred speech", "emergency"),
    ("sudden loss of vision in one eye and confusion", "emergency"),
    ("sudden severe headache with loss of balance and speech problems", "emergency"),

    # A41 Sepsis (95% ER rate, 94,200 emergency admissions)
    ("signs of sepsis high fever shivering extreme lethargy and confusion", "emergency"),
    ("very high temperature mottled skin feeling extremely unwell", "emergency"),
    ("suspected sepsis rapid heart rate low blood pressure confused", "emergency"),

    # J22 Lower Respiratory Infection (95% ER rate, 123,327 emergency admissions)
    ("severe chest infection difficulty breathing green phlegm very weak", "emergency"),
    ("breathing getting worse cannot speak full sentences with fever", "emergency"),
    ("difficulty breathing getting worse cannot speak full sentences", "emergency"),
    ("heavy uncontrolled bleeding from wound", "emergency"),
    ("serious fall down a flight of stairs unable to move limb", "emergency"),

    # J44 COPD Exacerbation (96% ER rate, 117,000 emergency admissions)
    ("copd flare up struggling to breathe inhaler not helping", "emergency"),
    ("severe worsening breathlessness in known copd patient blue lips", "emergency"),

    # I50 Heart Failure (84% ER rate, 87,212 emergency admissions)
    ("sudden severe breathlessness swollen ankles unable to lie flat", "emergency"),
    ("heart failure patient suddenly much worse gasping for air", "emergency"),

    # R29 Falls/Collapse (94% ER rate, 84,087 emergency admissions)
    ("patient collapsed and is unconscious not responding", "emergency"),
    ("elderly person found on floor unresponsive after fall", "emergency"),

    # S72 Hip/Femur Fracture (94% ER rate, 74,343 emergency admissions)
    ("fallen and unable to stand suspected broken hip severe pain", "emergency"),
    ("elderly fall with severe hip pain leg appears shortened rotated", "emergency"),
    ("fracture of the leg after a fall unable to bear any weight", "emergency"),

    # B34 Viral Infection severe (97% ER rate, 81,158 emergency admissions)
    ("severe viral illness high fever rigors cannot keep fluids down", "emergency"),

    # R51 Headache severe (87% ER rate, 63,834 emergency admissions)
    ("thunderclap headache worst headache of my life sudden onset", "emergency"),

    # R55 Syncope/Fainting (82% ER rate, 59,369 emergency admissions)
    ("collapsed and fainted hit head on the ground", "emergency"),

    # E87 Fluid/Electrolyte disorder (87% ER rate, 57,260 emergency admissions)
    ("severe dehydration confused very weak not passed urine for hours", "emergency"),

    # W19 Unspecified fall (94% ER rate, 152,307 emergency admissions)
    ("serious fall from height unable to move in severe pain", "emergency"),
    ("fall and hit head now drowsy and vomiting loss of consciousness", "emergency"),

    # W10 Fall on stairs (90% ER rate, 36,853 emergency admissions)
    ("fell down a flight of stairs unable to move possible fracture", "emergency"),

    # V03 Pedestrian hit by car (93% ER rate, 4,408 emergency admissions)
    ("pedestrian hit by a car with multiple injuries and bleeding", "emergency"),
    ("knocked down by vehicle in road traffic accident head injury", "emergency"),

    # X60 Intentional self-poisoning (100% ER rate, 24,335 emergency admissions)
    ("taken overdose of paracetamol tablets intentionally", "emergency"),
    ("deliberately taken too many pills feeling drowsy and sick", "emergency"),

    # X78 Intentional self-harm by sharp object (90% ER rate)
    ("deep self-inflicted cuts to arms heavy bleeding", "emergency"),

    # W54 Dog bite (79% ER rate, 8,489 emergency admissions)
    ("serious dog bite to face deep wound heavy bleeding", "emergency"),

    # other classic emergencies
    ("severe allergic reaction throat swelling difficulty breathing", "emergency"),
    ("seizure lasting more than 5 minutes", "emergency"),
    ("baby has stopped breathing and is unresponsive", "emergency"),
    ("choking on food cannot breathe properly turning blue", "emergency"),
    ("large burn covering arm and chest blistering", "emergency"),
    ("signs of meningitis rash fever stiff neck confused", "emergency"),
    ("anaphylactic reaction swollen throat lips tongue", "emergency"),
    ("severe breathing difficulty blue lips in child", "emergency"),
    ("head injury with loss of consciousness and vomiting", "emergency"),
    ("sudden severe abdominal pain with rigid abdomen", "emergency"),
    ("heavy uncontrolled bleeding that will not stop", "emergency"),
    ("electric shock and now having palpitations and chest pain", "emergency"),
    ("suicidal thoughts and planning to end life", "emergency"),


    # --- URGENT cases (need same-day/next-day GP) ---

    # R10 Abdominal Pain (67% ER rate, 217,731 emergency admissions)
    ("severe abdominal pain right side getting worse over hours", "urgent"),
    ("sharp stomach pain with nausea and loss of appetite", "urgent"),
    ("acute pain in lower abdomen with fever and vomiting", "urgent"),
    ("persistent abdominal pain and bloating not eating for 2 days", "urgent"),

    # N39 Urinary Tract Infection (83% ER rate but many manageable by GP)
    ("painful urination with blood high fever and back pain", "urgent"),
    ("painful urination with high temperature and back pain", "urgent"),
    ("burning when passing urine frequent urge and cloudy urine fever", "urgent"),
    ("severe UTI symptoms with high temperature and shivering", "urgent"),

    # L03 Cellulitis (81% ER rate, 82,216 emergency admissions)
    ("redness and swelling of lower leg spreading quickly warm to touch", "urgent"),
    ("redness and swelling of the lower leg spreading quickly", "urgent"),
    ("red hot swollen skin on arm with red line tracking up the arm", "urgent"),
    ("infected wound becoming red swollen hot and oozing pus", "urgent"),

    # A09 Gastroenteritis (77% ER rate, 81,209 emergency admissions)
    ("persistent vomiting and diarrhoea unable to keep any fluids down 24 hours", "urgent"),
    ("stomach flu symptoms very dehydrated sunken eyes dry mouth", "urgent"),
    ("food poisoning violent vomiting and bloody diarrhoea", "urgent"),

    # K80 Gallstones (47% ER rate, 73,887 emergency admissions)
    ("severe upper right abdominal pain after eating fatty food", "urgent"),
    ("intense pain under right ribs spreading to back with vomiting", "urgent"),

    # M79 Soft tissue disorder (69% ER rate, 85,135 emergency admissions)
    ("unable to bear weight on ankle after fall possible fracture", "urgent"),
    ("sudden severe muscle pain and swelling after injury", "urgent"),

    # other urgent presentations
    ("high fever 39.5 degrees not responding to paracetamol for 2 days", "urgent"),
    ("worst headache I have ever had came on suddenly", "urgent"),
    ("blood in stool for the past 3 days dark coloured", "urgent"),
    ("new confusion in elderly parent not recognising family", "urgent"),
    ("rapidly spreading red rash warm to touch with fever", "urgent"),
    ("blood in urine with back pain and fever", "urgent"),
    ("child has high fever rash that does not disappear when pressed", "urgent"),
    ("severe ear pain with discharge and hearing loss", "urgent"),
    ("sudden swelling of leg with pain and redness possible DVT", "urgent"),
    ("diabetic feeling very unwell blood sugar very high", "urgent"),
    ("asthma attack not improving with usual inhaler after 10 puffs", "urgent"),
    ("new lump in breast noticed this week", "urgent"),
    ("testicular pain and swelling sudden onset", "urgent"),
    ("dog bite wound on hand becoming red swollen and hot", "urgent"),
    ("severe back pain with numbness in legs and unable to pass urine", "urgent"),
    ("eye injury with pain blurred vision and sensitivity to light", "urgent"),
    ("panic attacks becoming very frequent and severe", "urgent"),
    ("wound from surgery becoming red hot and oozing discharge", "urgent"),
    ("toddler pulling at ear high temperature 39 very irritable refusing feeds", "urgent"),
    ("migraine not responding to usual medication lasting 3 days", "urgent"),
    ("chest infection with green phlegm and high temperature for 5 days", "urgent"),
    ("fall on outstretched hand wrist very swollen and painful", "urgent"),
    ("insect bite with spreading redness warmth and red streaks", "urgent"),
    ("sudden loss of hearing in one ear", "urgent"),
    ("child with barking cough and difficulty breathing at night", "urgent"),
    ("abdominal pain in pregnancy with vaginal bleeding", "urgent"),
    ("severe tooth infection face swelling and high temperature", "urgent"),



    # --- ROUTINE cases (can wait 2-3 weeks for GP) ---

    # H25 Cataracts (0% ER rate, 323,312 waitlist admissions)
    ("gradual blurring of vision over several months difficulty reading", "routine"),
    ("cloudy vision in both eyes getting worse over past year", "routine"),
    ("finding it harder to see at night and drive need eye check", "routine"),

    # D12 Benign Neoplasm of Colon (0% ER rate, 170,826 waitlist)
    ("follow up appointment after polyp removed during colonoscopy", "routine"),
    ("need to schedule repeat colonoscopy for polyp surveillance", "routine"),

    # C44 Skin Neoplasm (0% ER rate, 160,746 waitlist)
    ("skin lesion that has changed colour over a few months need review", "routine"),
    ("suspicious mole getting larger slowly need it looked at", "routine"),
    ("recurring skin growth that comes back after treatment", "routine"),

    # K29 Gastritis (16% ER rate, 125,370 waitlist)
    ("ongoing heartburn and acid reflux most days for several weeks", "routine"),
    ("heartburn happening most days want to discuss treatment", "routine"),
    ("persistent stomach irritation and indigestion after meals", "routine"),
    ("investigation for persistent heartburn not responding to antacids", "routine"),

    # D50 Iron Deficiency Anaemia (19% ER rate, 119,019 waitlist)
    ("feeling very tired pale and short of breath on exertion low iron", "routine"),
    ("follow up blood test for iron deficiency anaemia", "routine"),
    ("chronic fatigue and breathlessness on stairs need iron check", "routine"),

    # M17 Knee Osteoarthritis (3% ER rate, 117,975 waitlist)
    ("chronic knee pain and stiffness worse going up and down stairs", "routine"),
    ("ongoing knee pain from arthritis need to discuss treatment options", "routine"),
    ("knee giving way occasionally pain after walking need assessment", "routine"),

    # K64 Haemorrhoids (7% ER rate, 107,315 waitlist)
    ("bleeding from back passage when going to toilet no pain", "routine"),
    ("haemorrhoid problems ongoing for months need treatment review", "routine"),

    # C50 Breast Cancer screening (1% ER rate, 106,033 waitlist)
    ("recalled after routine mammogram for further investigation", "routine"),

    # M16 Hip Osteoarthritis (2% ER rate, 88,975 waitlist)
    ("persistent hip pain from known arthritis getting worse over months", "routine"),
    ("ongoing joint stiffness and pain in the hips from arthritis", "routine"),
    ("hip stiffness and pain making it difficult to walk and climb stairs", "routine"),
    ("chronic hip pain from osteoarthritis need joint review", "routine"),

    # K57 Diverticular disease (26% ER rate, 93,828 waitlist)
    ("recurring left-sided abdominal pain and bloating known diverticulitis", "routine"),
    ("need follow up after diverticulitis episode last month", "routine"),

    # other routine presentations
    ("mild sore throat and runny nose for 3 days feeling okay", "routine"),
    ("ongoing back pain for 2 months getting slightly worse", "routine"),
    ("mild headaches happening a few times a week tension type", "routine"),
    ("skin rash on arms not itchy been there for 2 weeks", "routine"),
    ("feeling more tired than usual for past month", "routine"),
    ("mild knee pain after running been going on for weeks", "routine"),
    ("mild anxiety affecting sleep would like to discuss options", "routine"),
    ("recurring urinary tract infections need investigation", "routine"),
    ("mole has changed shape slightly over past few months", "routine"),
    ("joint stiffness in hands worse in morning known arthritis", "routine"),
    ("stomach bloating and discomfort after meals ongoing", "routine"),
    ("mild eczema flare up need cream prescription", "routine"),
    ("recurrent headaches want to discuss prevention", "routine"),
    ("low mood for several weeks not suicidal but struggling", "routine"),
    ("tinnitus both ears getting gradually worse affecting sleep", "routine"),
    ("constipation ongoing for 3 weeks tried over counter remedies", "routine"),
    ("snoring very loudly partner concerned about breathing at night", "routine"),
    ("irregular periods for past 3 months need investigation", "routine"),
    ("numbness in fingers both hands happens occasionally", "routine"),
    ("difficulty swallowing food sometimes feels stuck need investigation", "routine"),
    ("chronic fatigue and muscle aches going on for months", "routine"),
    ("want to discuss weight management options", "routine"),
    ("mild dizziness when standing up quickly", "routine"),
    ("dry eyes causing discomfort at work", "routine"),
    ("worsening varicose veins in legs aching and unsightly", "routine"),
    ("need referral for physiotherapy for shoulder problem", "routine"),
    ("request for blood tests to check cholesterol and diabetes", "routine"),
    ("need to review asthma management plan annual review", "routine"),
    ("discussion about starting antidepressant medication", "routine"),
    ("follow up after recent blood test results", "routine"),



    # --- SELF CARE cases (pharmacy/home remedies, no GP needed) ---

    ("common cold symptoms runny nose mild cough sneezing", "self_care"),
    ("mild stomach ache after eating too much feeling bloated", "self_care"),
    ("small paper cut on finger stopped bleeding", "self_care"),
    ("hayfever symptoms itchy eyes runny nose seasonal", "self_care"),
    ("mild tension headache after long day at computer", "self_care"),
    ("minor sunburn on shoulders slightly pink and warm", "self_care"),
    ("cold sore on lip just appeared tingling", "self_care"),
    ("athletes foot between toes mild itching and peeling", "self_care"),
    ("insect bite small red itchy bump no spreading redness", "self_care"),
    ("mild muscle soreness after exercise", "self_care"),
    ("dandruff on scalp mild flaking", "self_care"),
    ("mouth ulcer small and painful eating is fine", "self_care"),
    ("mild constipation 2 days eating and drinking normally", "self_care"),
    ("need repeat prescription for regular medication", "self_care"),
    ("verruca on foot not painful", "self_care"),
    ("dry skin patches on hands in winter", "self_care"),
    ("slight earache after swimming no fever", "self_care"),
    ("hiccups that keep coming back today", "self_care"),
    ("travel vaccination enquiry going abroad in 3 months", "self_care"),
    ("mild indigestion after spicy food", "self_care"),
    ("mild blocked nose and sneezing for 2 days", "self_care"),
    ("small bruise on leg from bumping into furniture", "self_care"),
    ("dry tickly cough for a couple of days no fever", "self_care"),
    ("chapped lips in cold weather", "self_care"),
    ("stiff neck after sleeping in awkward position", "self_care"),
    ("mild period cramps normal period", "self_care"),
    ("blisters on feet from new shoes", "self_care"),
    ("mild nappy rash on baby bottom is a bit red", "self_care"),
    ("hangover feeling nauseous and headache after drinking", "self_care"),
    ("question about over the counter hay fever medication", "self_care"),
    ("want to know if I should take vitamin D supplements", "self_care"),
    ("minor graze on knee from tripping cleaned and covered", "self_care"),
    ("contact lens discomfort and dry eyes", "self_care"),
    ("mild cradle cap on baby scalp", "self_care"),
    ("threadworms in child noticed in poo", "self_care"),
]


def train_model():
    """trains the triage classifier and saves it as a pickle file"""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.pipeline import Pipeline
        from sklearn.model_selection import cross_val_score
        import numpy as np
    except ImportError:
        print("ERROR: scikit-learn not installed. Run: pip install scikit-learn")
        return

    texts = [item[0] for item in TRAINING_DATA]
    labels = [item[1] for item in TRAINING_DATA]

    print(f"Training data: {len(texts)} samples")
    print(f"  Emergency:  {labels.count('emergency')}")
    print(f"  Urgent:     {labels.count('urgent')}")
    print(f"  Routine:    {labels.count('routine')}")
    print(f"  Self-care:  {labels.count('self_care')}")

    # the pipeline: TF-IDF turns text into numbers, random forest classifies
    # ngram_range=(1,3) means it looks at single words AND phrases up to 3 words
    # so it can pick up on things like "chest pain" and "crushing chest pain"
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(
            max_features=2000,       # top 2000 most useful words/phrases
            ngram_range=(1, 3),      # unigrams, bigrams and trigrams
            stop_words='english',    # ignore common words like "the", "is"
            sublinear_tf=True,       # log scaling so common terms dont dominate
        )),
        ('clf', RandomForestClassifier(
            n_estimators=200,        # 200 decision trees vote on the answer
            random_state=42,         # fixed seed so results are reproducible
            class_weight='balanced', # handles imbalanced classes automatically
            min_samples_leaf=2,      # prevents overfitting to single examples
        )),
    ])

    # train it
    pipeline.fit(texts, labels)

    # 5-fold cross validation to check how well it generalises
    scores = cross_val_score(pipeline, texts, labels, cv=5, scoring='accuracy')
    print(f"\nCross-validation accuracy: {scores.mean():.2%} (+/- {scores.std():.2%})")

    # save the trained model
    model_path = Path(__file__).parent / 'triage_model.pkl'
    with open(model_path, 'wb') as f:
        pickle.dump(pipeline, f)

    print(f"Model saved to: {model_path}")

    # run some test predictions to make sure it looks right
    print("\n" + "="*70)
    print("AI TRIAGE ANALYSIS - Test Predictions")
    print("="*70)
    test_cases = [
        "I have a crushing pain in my chest and feel sweaty and sick",
        "my leg is red hot and the swelling is spreading up quickly",
        "I need a checkup for my long-term hip arthritis",
        "I just have a bit of a runny nose and sneezing",
        "my child has a very high fever and a rash that doesn't fade when pressed",
        "I took an overdose of tablets about an hour ago",
        "I've had a headache for 2 weeks on and off",
        "severe stomach pain on the right side getting worse",
        "I fell down the stairs and can't move my leg",
        "I have a cold sore on my lip",
        "blood in my urine and high temperature with back pain",
        "I need a repeat prescription for my blood pressure pills",
        "my vision has been getting cloudy over the past year",
        "sudden weakness on the left side of my body",
    ]

    print(f"\n{'Input':<65} {'Result':<12} {'Confidence'}")
    print("-" * 95)
    for case in test_cases:
        pred = pipeline.predict([case])[0]
        proba = pipeline.predict_proba([case])[0]
        confidence = max(proba)

        urgency_display = {
            'emergency': 'EMERGENCY',
            'urgent':    'URGENT',
            'routine':   'ROUTINE',
            'self_care': 'SELF-CARE',
        }

        display = urgency_display.get(pred, pred.upper())
        short_case = case[:62] + "..." if len(case) > 65 else case
        print(f"  {short_case:<63} {display:<14} {confidence:.0%}")

    print("\n" + "="*70)
    print("Training complete. Run your Django server to use the model.")
    print("="*70)


if __name__ == '__main__':
    train_model()
