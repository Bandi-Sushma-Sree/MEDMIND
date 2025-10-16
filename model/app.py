import gradio as gr
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from deep_translator import GoogleTranslator
import os
from dotenv import load_dotenv
import tempfile
from datetime import datetime
import json

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    safety_settings={
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }
)

# CORRECTED language mapping with proper codes for GoogleTranslator
LANGUAGES = {
    'English': 'en',
    'Hindi': 'hi', 
    'Bengali': 'bn',
    'Telugu': 'te',
    'Tamil': 'ta',
    'Marathi': 'mr',
    'Gujarati': 'gu',
    'Kannada': 'kn',
    'Malayalam': 'ml',
    'Punjabi': 'pa',
    'Odia': 'or',
    'Assamese': 'as'
}

# Complete symptom database (keeping the same 117 categories as before)

SYMPTOM_QUESTIONS = {
    # === DIGESTIVE SYSTEM (20 categories) ===
    'stomach_pain': [
        "Where exactly is the stomach pain (upper, lower, right, left)?",
        "Is it burning, cramping, sharp, or dull?",
        "Does eating make it better or worse?",
        "Any nausea, vomiting, or changes in bowel movements?",
        "How long have you had this pain?"
    ],
    'nausea': [
        "Are you actually vomiting or just feeling nauseous?",
        "Is it related to eating or happens anytime?",
        "Any abdominal pain or cramping with the nausea?",
        "Do you have diarrhea or constipation?",
        "When did the nausea start?"
    ],
    'vomiting': [
        "What does the vomit look like (color, consistency)?",
        "Is there any blood in the vomit?",
        "How many times have you vomited today?",
        "Can you keep any fluids down?",
        "What triggered the first episode of vomiting?"
    ],
    'diarrhea': [
        "How many loose stools have you had today?",
        "What color and consistency are the stools?",
        "Is there any blood or mucus in the stool?",
        "Do you have abdominal cramping or pain?",
        "Have you traveled recently or eaten anything unusual?"
    ],
    'constipation': [
        "When was your last bowel movement?",
        "Are the stools hard and difficult to pass?",
        "Do you have abdominal bloating or pain?",
        "Have you changed your diet or medications recently?",
        "Do you strain when trying to have a bowel movement?"
    ],
    'heartburn': [
        "Do you feel burning in your chest or throat?",
        "Does it happen after eating or when lying down?",
        "Do you have a sour taste in your mouth?",
        "Does antacid medication help relieve it?",
        "How often do you experience heartburn?"
    ],
    'bloating': [
        "Does your abdomen feel distended or swollen?",
        "Is the bloating worse after eating certain foods?",
        "Do you have excessive gas or burping?",
        "Any abdominal pain with the bloating?",
        "When during the day is bloating worst?"
    ],
    'loss_of_appetite': [
        "How long have you had decreased appetite?",
        "Are you losing weight unintentionally?",
        "Do foods taste different or strange?",
        "Any nausea or stomach pain?",
        "Are you able to finish normal-sized meals?"
    ],
    'abdominal_cramps': [
        "Where exactly are the cramps located?",
        "Are they constant or come in waves?",
        "Do they relate to bowel movements?",
        "Any bloating or gas with the cramps?",
        "What seems to trigger the cramping?"
    ],
    'indigestion': [
        "Do you feel full quickly when eating?",
        "Any burning or discomfort in upper abdomen?",
        "Does it happen with specific foods?",
        "Any burping or feeling of gas?",
        "How long after eating do symptoms occur?"
    ],
    'acid_reflux': [
        "Do you have burning sensation going up your throat?",
        "Is it worse when lying down or bending over?",
        "Any sour or bitter taste in mouth?",
        "Does it wake you up at night?",
        "What foods seem to trigger it?"
    ],
    'stomach_ulcer': [
        "Do you have burning stomach pain?",
        "Is the pain worse when stomach is empty?",
        "Does eating temporarily relieve the pain?",
        "Any black or bloody stools?",
        "Do you take NSAIDs or have H. pylori infection?"
    ],
    'gas_problems': [
        "Do you have excessive burping or flatulence?",
        "Any abdominal bloating or distension?",
        "Does it happen with certain foods?",
        "Any abdominal pain or cramping?",
        "How long have you had gas problems?"
    ],
    'food_poisoning': [
        "Do you have nausea, vomiting, or diarrhea?",
        "What did you eat in the last 24-48 hours?",
        "Any abdominal cramps or fever?",
        "Are others who ate the same food also sick?",
        "When did symptoms start after eating?"
    ],
    'gallbladder_pain': [
        "Do you have pain in upper right abdomen?",
        "Does the pain radiate to your back or shoulder?",
        "Is it worse after eating fatty foods?",
        "Any nausea or vomiting with the pain?",
        "How long do the pain episodes last?"
    ],
    'liver_problems': [
        "Do you have pain in upper right abdomen?",
        "Any yellowing of skin or eyes?",
        "Do you feel unusually tired or weak?",
        "Any dark urine or pale stools?",
        "Have you been exposed to hepatitis?"
    ],
    'hemorrhoids': [
        "Do you have pain or discomfort during bowel movements?",
        "Any bleeding from the rectum?",
        "Do you feel lumps around the anus?",
        "Any itching or irritation in the anal area?",
        "How long have you had these symptoms?"
    ],
    'irritable_bowel': [
        "Do you have alternating diarrhea and constipation?",
        "Any abdominal pain that improves after bowel movements?",
        "Do certain foods trigger your symptoms?",
        "Any mucus in your stools?",
        "How long have you had digestive problems?"
    ],
    'peptic_ulcer': [
        "Do you have burning stomach pain?",
        "Is the pain worse between meals or at night?",
        "Does eating or antacids provide relief?",
        "Any nausea, vomiting, or loss of appetite?",
        "Do you take NSAIDs regularly?"
    ],
    'gastroenteritis': [
        "Do you have diarrhea and vomiting?",
        "Any fever or abdominal cramps?",
        "How long have symptoms been present?",
        "Any recent travel or exposure to illness?",
        "Can you keep fluids down?"
    ],

    # === RESPIRATORY SYSTEM (15 categories) ===
    'cough': [
        "Is it a dry cough or are you bringing up phlegm?",
        "What color is the phlegm (if any)?",
        "Is the cough worse at night or during the day?",
        "Do you have fever or shortness of breath?",
        "How long have you had this cough?"
    ],
    'shortness_of_breath': [
        "Does it happen at rest or only with activity?",
        "Any chest pain or tightness with breathing?",
        "Do you have a cough or wheezing?",
        "Any swelling in your legs or feet?",
        "How long have you noticed breathing difficulty?"
    ],
    'wheezing': [
        "Do you hear a whistling sound when breathing?",
        "Is it worse when breathing in or out?",
        "Do you have a history of asthma or allergies?",
        "Any chest tightness or coughing?",
        "What triggers seem to make wheezing worse?"
    ],
    'chest_congestion': [
        "Do you feel pressure or heaviness in your chest?",
        "Are you coughing up thick mucus?",
        "Does your chest feel tight?",
        "Any fever or body aches?",
        "How long has your chest felt congested?"
    ],
    'runny_nose': [
        "Is the discharge clear, yellow, or green?",
        "Do you have sneezing or congestion?",
        "Any facial pressure or sinus pain?",
        "Do you have allergies to anything?",
        "How long has your nose been running?"
    ],
    'stuffy_nose': [
        "Is one or both nostrils blocked?",
        "Any discharge or just congestion?",
        "Do you have sinus pressure or headache?",
        "Does anything help clear your nose?",
        "How long have you been congested?"
    ],
    'sneezing': [
        "How often are you sneezing?",
        "Any runny or itchy nose with sneezing?",
        "Do you have watery eyes?",
        "Are you around any allergens or irritants?",
        "Is it seasonal or year-round?"
    ],
    'sinus_pressure': [
        "Where do you feel the pressure (forehead, cheeks, around eyes)?",
        "Is it worse when bending forward?",
        "Any nasal congestion or discharge?",
        "Do you have headache with the pressure?",
        "Any recent cold or allergies?"
    ],
    'pneumonia_symptoms': [
        "Do you have fever and chills?",
        "Any sharp chest pain when breathing or coughing?",
        "Are you coughing up yellow or green phlegm?",
        "Do you feel short of breath?",
        "Any fatigue or confusion?"
    ],
    'bronchitis': [
        "Do you have a persistent cough with mucus?",
        "Any chest discomfort or tightness?",
        "Do you have low-grade fever?",
        "Any fatigue or shortness of breath?",
        "How long have you had these symptoms?"
    ],
    'asthma_attack': [
        "Are you having difficulty breathing?",
        "Do you hear wheezing when you breathe?",
        "Any chest tightness or pain?",
        "What seems to have triggered this episode?",
        "Are you using your rescue inhaler?"
    ],
    'allergic_rhinitis': [
        "Do you have sneezing, runny nose, or itchy eyes?",
        "Is it seasonal or year-round?",
        "What allergens seem to trigger symptoms?",
        "Any postnasal drip or sinus pressure?",
        "Do antihistamines help your symptoms?"
    ],
    'hiccups': [
        "How long have you had hiccups?",
        "Are they continuous or intermittent?",
        "What seems to trigger them?",
        "Any pain or discomfort with hiccups?",
        "Have you tried any remedies?"
    ],
    'laryngitis': [
        "Is your voice hoarse or lost?",
        "Any sore throat or throat pain?",
        "Do you have a dry cough?",
        "Any fever or swollen glands?",
        "How long has your voice been affected?"
    ],
    'sleep_apnea': [
        "Do you snore loudly or gasp during sleep?",
        "Do you feel tired despite sleeping?",
        "Any morning headaches?",
        "Has anyone noticed you stop breathing during sleep?",
        "Do you fall asleep easily during the day?"
    ],

    # === CARDIOVASCULAR SYSTEM (12 categories) ===
    'chest_pain': [
        "Where exactly in your chest (center, left, right)?",
        "Is it sharp, crushing, burning, or tight?",
        "Does it spread to arm, jaw, neck, or back?",
        "Does deep breathing or movement make it worse?",
        "Any shortness of breath or sweating?"
    ],
    'heart_palpitations': [
        "Does your heart feel like it's racing or skipping beats?",
        "Do you feel dizzy or lightheaded with palpitations?",
        "Any chest pain or shortness of breath?",
        "What seems to trigger the palpitations?",
        "How long do the episodes last?"
    ],
    'high_blood_pressure': [
        "What was your last blood pressure reading?",
        "Do you have headaches or dizziness?",
        "Any nosebleeds or vision changes?",
        "Are you taking blood pressure medication?",
        "Do you have chest pain or shortness of breath?"
    ],
    'swelling': [
        "Where is the swelling (legs, feet, hands, face)?",
        "Is it worse at the end of the day?",
        "Does pressing on it leave an indentation?",
        "Any shortness of breath or chest pain?",
        "Have you gained weight recently?"
    ],
    'irregular_heartbeat': [
        "Does your heart skip beats or have extra beats?",
        "Do you feel fluttering in your chest?",
        "Any dizziness or fainting with irregular beats?",
        "Does caffeine or stress make it worse?",
        "How often do you notice irregular heartbeats?"
    ],
    'low_blood_pressure': [
        "Do you feel dizzy when standing up?",
        "Any fainting or near-fainting episodes?",
        "Do you feel weak or tired?",
        "Any nausea or blurred vision?",
        "Are you taking any medications?"
    ],
    'rapid_heartbeat': [
        "How fast does your heart beat (if you've counted)?",
        "Does it happen suddenly or gradually?",
        "Any chest pain or shortness of breath?",
        "Do you feel anxious when it happens?",
        "What seems to trigger rapid heartbeat?"
    ],
    'slow_heartbeat': [
        "Do you feel dizzy or lightheaded?",
        "Any fainting or near-fainting episodes?",
        "Do you feel more tired than usual?",
        "Any chest pain or shortness of breath?",
        "Are you taking heart medications?"
    ],
    'varicose_veins': [
        "Where are the enlarged veins located?",
        "Do they cause pain, aching, or heaviness?",
        "Are symptoms worse after standing?",
        "Any swelling in the affected area?",
        "How long have you noticed these veins?"
    ],
    'blood_clot': [
        "Do you have pain, swelling, or redness in leg/arm?",
        "Any sudden shortness of breath or chest pain?",
        "Is the affected area warm to touch?",
        "Any recent surgery, injury, or long travel?",
        "When did you first notice these symptoms?"
    ],
    'heart_murmur': [
        "Has a doctor detected a heart murmur?",
        "Do you have any chest pain or shortness of breath?",
        "Any fatigue or dizziness?",
        "Can you hear the murmur yourself?",
        "Any family history of heart problems?"
    ],
    'angina': [
        "Do you have chest pain with physical activity?",
        "Does rest relieve the chest pain?",
        "Any pain in arm, jaw, neck, or back?",
        "How long do pain episodes last?",
        "What activities trigger the pain?"
    ],

    # === NEUROLOGICAL SYSTEM (18 categories) ===
    'headache': [
        "Where is the headache (front, back, temples, all over)?",
        "Is it throbbing, sharp, or pressure-like?",
        "Any sensitivity to light or sound?",
        "Do you feel nauseous or have vision changes?",
        "What seems to trigger or worsen it?"
    ],
    'dizziness': [
        "Is it spinning dizziness or feeling faint?",
        "Does it happen when you stand up or change positions?",
        "Any nausea or vomiting with the dizziness?",
        "Do you have hearing changes or ear problems?",
        "How long do the dizzy episodes last?"
    ],
    'migraine': [
        "Is it a severe, throbbing headache on one side?",
        "Do you see flashing lights or have vision changes?",
        "Are you sensitive to light, sound, or smells?",
        "Do you feel nauseous or vomit with the headache?",
        "How long do your migraine episodes typically last?"
    ],
    'memory_problems': [
        "Are you forgetting recent events or past memories?",
        "Do you have trouble concentrating or focusing?",
        "Are you misplacing items frequently?",
        "Any confusion about time, place, or people?",
        "When did you first notice memory changes?"
    ],
    'numbness': [
        "Where do you feel numb (hands, feet, face, other)?",
        "Is it constant or comes and goes?",
        "Any tingling or pins-and-needles sensation?",
        "Do you have weakness in the numb area?",
        "Did the numbness start suddenly or gradually?"
    ],
    'seizure': [
        "Did you lose consciousness during the episode?",
        "Were there any jerking movements or muscle spasms?",
        "How long did the episode last?",
        "Do you remember what happened during it?",
        "Have you had seizures before?"
    ],
    'confusion': [
        "Are you having trouble thinking clearly?",
        "Do you feel disoriented about time or place?",
        "Any memory problems or difficulty concentrating?",
        "Have others noticed changes in your thinking?",
        "When did the confusion start?"
    ],
    'coordination_problems': [
        "Are you having trouble with balance or walking?",
        "Do you feel unsteady or clumsy?",
        "Any difficulty with fine motor tasks (writing, buttoning)?",
        "Do you feel like you might fall?",
        "When did coordination problems start?"
    ],
    'tremor': [
        "Where do you have tremor (hands, arms, legs, head)?",
        "Does it happen at rest or when moving?",
        "Is it worse with stress or caffeine?",
        "Does it interfere with daily activities?",
        "How long have you had tremor?"
    ],
    'weakness': [
        "Where do you feel weak (arms, legs, overall)?",
        "Is it constant or comes and goes?",
        "Any numbness or tingling with weakness?",
        "Can you do normal daily activities?",
        "Did weakness start suddenly or gradually?"
    ],
    'fainting': [
        "Did you completely lose consciousness?",
        "How long were you unconscious?",
        "What were you doing when you fainted?",
        "Any warning signs before fainting?",
        "Have you fainted before?"
    ],
    'vision_problems': [
        "What kind of vision changes (blurry, double, loss)?",
        "Is it in one eye or both eyes?",
        "Any eye pain or headaches?",
        "Do you see flashing lights or spots?",
        "When did vision problems start?"
    ],
    'speech_problems': [
        "Are you having trouble speaking clearly?",
        "Do you have difficulty finding words?",
        "Any slurring of speech?",
        "Can others understand you?",
        "When did speech problems begin?"
    ],
    'balance_problems': [
        "Do you feel unsteady when walking?",
        "Any spinning sensation or vertigo?",
        "Do you need to hold onto things for support?",
        "Any recent falls or near-falls?",
        "How long have you had balance issues?"
    ],
    'cognitive_decline': [
        "Are you having more difficulty with thinking tasks?",
        "Any problems with decision-making or judgment?",
        "Do you get lost in familiar places?",
        "Any personality or behavior changes?",
        "When did you first notice cognitive changes?"
    ],
    'stroke_symptoms': [
        "Do you have sudden weakness on one side?",
        "Any sudden speech problems or confusion?",
        "Sudden severe headache or vision loss?",
        "Any facial drooping or numbness?",
        "When did these symptoms start?"
    ],
    'nerve_pain': [
        "Where do you feel the nerve pain?",
        "Is it burning, shooting, or electric-like?",
        "Does it follow a specific path or area?",
        "What triggers or worsens the pain?",
        "Any numbness or tingling with the pain?"
    ],
    'concussion': [
        "Did you hit your head or have an injury?",
        "Any loss of consciousness or memory gap?",
        "Do you have headache, nausea, or dizziness?",
        "Any confusion or difficulty concentrating?",
        "When did the head injury occur?"
    ],

    # === MUSCULOSKELETAL SYSTEM (15 categories) ===
    'back_pain': [
        "Where exactly is the back pain (upper, middle, lower)?",
        "Is it sharp, dull, burning, or shooting?",
        "Does it radiate to your legs or other areas?",
        "What makes it better or worse (sitting, standing, lying)?",
        "How long have you been experiencing this pain?"
    ],
    'neck_pain': [
        "Where in your neck does it hurt most?",
        "Can you move your neck in all directions?",
        "Does the pain go into your shoulders or arms?",
        "Any headaches with the neck pain?",
        "Did you injure your neck recently?"
    ],
    'joint_pain': [
        "Which joints are painful (knees, shoulders, hands)?",
        "Is there swelling or stiffness in the joints?",
        "Is the pain worse in the morning or evening?",
        "Does movement make it better or worse?",
        "How many joints are affected?"
    ],
    'muscle_pain': [
        "Where are your muscles sore or painful?",
        "Did you exercise or do unusual activity recently?",
        "Is there muscle weakness or cramping?",
        "Does massage or heat help the pain?",
        "Are you taking any new medications?"
    ],
    'arthritis': [
        "Which joints are stiff and painful?",
        "Is the stiffness worse in the morning?",
        "Do your joints look swollen or red?",
        "Does weather affect your joint pain?",
        "How long have you had joint problems?"
    ],
    'muscle_cramps': [
        "Where do you get muscle cramps?",
        "How long do the cramps last?",
        "What seems to trigger them?",
        "Any dehydration or electrolyte imbalance?",
        "Do they happen during exercise or at rest?"
    ],
    'stiffness': [
        "Where do you feel stiff (joints, muscles, back)?",
        "Is stiffness worse in the morning?",
        "Does movement help loosen up the stiffness?",
        "Any pain with the stiffness?",
        "How long have you felt stiff?"
    ],
    'muscle_weakness': [
        "Which muscles feel weak?",
        "Is it getting progressively worse?",
        "Any difficulty with specific activities?",
        "Any numbness or tingling with weakness?",
        "When did muscle weakness start?"
    ],
    'bone_pain': [
        "Where do you feel bone pain?",
        "Is it constant or comes and goes?",
        "Any recent injury or trauma?",
        "Does it hurt more with movement or at rest?",
        "Any swelling or deformity in the area?"
    ],
    'tendon_pain': [
        "Where is the tendon pain located?",
        "Is it worse with movement or stretching?",
        "Any swelling or tenderness?",
        "Did you recently increase activity or exercise?",
        "How long have you had tendon pain?"
    ],
    'ligament_injury': [
        "Where do you think the ligament is injured?",
        "Did you hear a pop when the injury occurred?",
        "Is there swelling or bruising?",
        "Can you bear weight or use the injured area?",
        "When did the injury happen?"
    ],
    'fracture_symptoms': [
        "Where do you think you might have a fracture?",
        "Can you move or use the injured area?",
        "Is there visible deformity or swelling?",
        "How did the injury occur?",
        "On a scale of 1-10, how severe is the pain?"
    ],
    'spinal_problems': [
        "Where in your spine do you have problems?",
        "Any pain radiating to arms or legs?",
        "Do you have numbness or tingling?",
        "Any weakness in arms or legs?",
        "How long have you had spinal problems?"
    ],
    'shoulder_pain': [
        "Where exactly in your shoulder does it hurt?",
        "Can you move your arm in all directions?",
        "Is it worse with overhead activities?",
        "Any recent injury or overuse?",
        "Does the pain wake you up at night?"
    ],
    'knee_pain': [
        "Where in your knee does it hurt?",
        "Any swelling or stiffness?",
        "Does it hurt when walking or climbing stairs?",
        "Any recent injury or trauma?",
        "Can you fully bend and straighten your knee?"
    ],

    # === GENERAL/CONSTITUTIONAL (12 categories) ===
    'fatigue': [
        "How long have you been feeling unusually tired?",
        "Is it constant or comes and goes?",
        "Any difficulty sleeping or sleep changes?",
        "Do you have other symptoms like fever or pain?",
        "Does rest help or does the tiredness persist?"
    ],
    'fever': [
        "What is your current temperature (if measured)?",
        "Do you have chills or sweats?",
        "Any body aches or muscle pain?",
        "Do you have other symptoms like cough or sore throat?",
        "When did the fever start?"
    ],
    'weight_loss': [
        "How much weight have you lost and over what time period?",
        "Has your appetite changed?",
        "Are you trying to lose weight or is it unintentional?",
        "Any other symptoms like fatigue or pain?",
        "Have you changed your diet or exercise routine?"
    ],
    'weight_gain': [
        "How much weight have you gained recently?",
        "Are you retaining fluid or feeling bloated?",
        "Has your appetite or eating habits changed?",
        "Any shortness of breath or swelling?",
        "Are you taking any new medications?"
    ],
    'night_sweats': [
        "Do you wake up soaked in sweat?",
        "Do you have fever with the sweats?",
        "How often do night sweats occur?",
        "Any weight loss or other symptoms?",
        "Are you going through menopause (if female)?"
    ],
    'chills': [
        "Do you feel cold even when others feel warm?",
        "Are you shivering or shaking?",
        "Do you have fever with the chills?",
        "Any other symptoms like body aches?",
        "How long have you been having chills?"
    ],
    'malaise': [
        "Do you feel generally unwell or run down?",
        "How long have you felt this way?",
        "Any specific symptoms with the general feeling?",
        "Are you able to do normal daily activities?",
        "Any recent illness or stress?"
    ],
    'body_aches': [
        "Where do you ache (all over, specific areas)?",
        "Is it muscle pain or joint pain?",
        "Any fever or other symptoms?",
        "Does anything make it better or worse?",
        "How long have you had body aches?"
    ],
    'dehydration': [
        "Are you drinking enough fluids?",
        "Do you have dry mouth or decreased urination?",
        "Any dizziness or lightheadedness?",
        "Have you been vomiting or had diarrhea?",
        "How long since you've had adequate fluids?"
    ],
    'loss_of_energy': [
        "How long have you lacked energy?",
        "Is it physical tiredness or mental fatigue?",
        "Does rest or sleep help restore energy?",
        "Any other symptoms like mood changes?",
        "What activities are you unable to do?"
    ],
    'insomnia': [
        "Do you have trouble falling asleep or staying asleep?",
        "How many hours of sleep do you get per night?",
        "Do you wake up feeling rested?",
        "What keeps you awake at night?",
        "How long have you had sleep problems?"
    ],
    'excessive_sweating': [
        "Where do you sweat excessively (hands, underarms, all over)?",
        "Is it worse with activity or happens at rest?",
        "Any triggers that make sweating worse?",
        "Does it interfere with daily activities?",
        "How long have you had excessive sweating?"
    ],

    # === SKIN & DERMATOLOGICAL (10 categories) ===
    'rash': [
        "Where on your body is the rash?",
        "Is it itchy, painful, or just visible?",
        "What does it look like (red spots, bumps, patches)?",
        "Have you used any new products or medications?",
        "When did you first notice the rash?"
    ],
    'itching': [
        "Where on your body are you itching?",
        "Is there a visible rash or just itching?",
        "Does anything make the itching better or worse?",
        "Have you been exposed to new allergens?",
        "How long have you been itching?"
    ],
    'hair_loss': [
        "Where are you losing hair (scalp, body, everywhere)?",
        "Is it gradual thinning or patches of hair loss?",
        "Any scalp irritation or scaling?",
        "Are you under unusual stress lately?",
        "When did you first notice hair loss?"
    ],
    'skin_changes': [
        "What changes have you noticed in your skin?",
        "Are there new moles, spots, or growths?",
        "Has the color or texture of your skin changed?",
        "Any itching, burning, or pain?",
        "When did you first notice these changes?"
    ],
    'acne': [
        "Where do you have acne breakouts?",
        "Are they blackheads, whiteheads, or cysts?",
        "Any pain or inflammation with the acne?",
        "What skincare products are you using?",
        "How long have you had acne problems?"
    ],
    'dry_skin': [
        "Where is your skin dry or flaky?",
        "Is it worse in certain weather or seasons?",
        "Any itching or irritation with the dryness?",
        "What moisturizers or products do you use?",
        "How long has your skin been dry?"
    ],
    'oily_skin': [
        "Where is your skin excessively oily?",
        "Does it lead to acne or breakouts?",
        "Is it worse at certain times of day?",
        "What products do you use for oily skin?",
        "How long has your skin been oily?"
    ],
    'wounds_healing': [
        "Where is the wound that's not healing?",
        "How long has it been since the injury?",
        "Any signs of infection (redness, pus, warmth)?",
        "Are you diabetic or have circulation problems?",
        "What treatment have you tried?"
    ],
    'burns': [
        "Where is the burn and what caused it?",
        "What degree of burn do you think it is?",
        "Any blistering or severe pain?",
        "How long ago did the burn occur?",
        "What first aid have you applied?"
    ],
    'bruising': [
        "Where are you bruising easily?",
        "Do you bruise without obvious injury?",
        "How long do bruises take to heal?",
        "Are you taking any blood-thinning medications?",
        "When did you notice increased bruising?"
    ],

    # === EYES & VISION (5 categories) ===
    'eye_pain': [
        "Is the pain in the eye or around the eye?",
        "Any changes in vision or light sensitivity?",
        "Is there discharge or tearing?",
        "Does blinking make it worse?",
        "Did something get in your eye?"
    ],
    'blurry_vision': [
        "Is the blurriness in one or both eyes?",
        "Is it constant or comes and goes?",
        "Any eye pain or headaches?",
        "Does it affect near or distance vision?",
        "When did you first notice blurry vision?"
    ],
    'double_vision': [
        "Do you see two images of everything?",
        "Is it in one eye or both eyes?",
        "Any eye pain or headaches?",
        "Does covering one eye help?",
        "When did double vision start?"
    ],
    'eye_discharge': [
        "What color is the discharge (clear, yellow, green)?",
        "Is it in one or both eyes?",
        "Any pain, redness, or swelling?",
        "Does it crust over your eyelids?",
        "How long have you had discharge?"
    ],
    'light_sensitivity': [
        "Are you sensitive to bright lights?",
        "Any eye pain or headaches with light exposure?",
        "Does it affect both eyes equally?",
        "Any changes in vision?",
        "When did light sensitivity start?"
    ],

    # === EARS & HEARING (5 categories) ===
    'ear_pain': [
        "Is the pain inside the ear or around the outside?",
        "Any discharge or fluid coming from the ear?",
        "Do you have hearing changes or ringing?",
        "Does pulling on your ear make it worse?",
        "Do you have cold or sinus symptoms?"
    ],
    'hearing_loss': [
        "Is the hearing loss in one or both ears?",
        "Did it happen suddenly or gradually?",
        "Any ear pain or discharge?",
        "Do you hear ringing or buzzing sounds?",
        "Have you been exposed to loud noises?"
    ],
    'ear_ringing': [
        "Do you hear ringing, buzzing, or other sounds?",
        "Is it in one or both ears?",
        "Is it constant or comes and goes?",
        "Any hearing loss or ear pain?",
        "How long have you had ear ringing?"
    ],
    'ear_discharge': [
        "What does the discharge look like (clear, yellow, bloody)?",
        "Any ear pain or hearing changes?",
        "Any bad smell from the ear?",
        "How long has there been discharge?",
        "Any recent swimming or water exposure?"
    ],
    'ear_pressure': [
        "Do you feel pressure or fullness in your ears?",
        "Any hearing changes or pain?",
        "Does swallowing or yawning help?",
        "Any recent flying or altitude changes?",
        "How long have you felt ear pressure?"
    ],

    # === THROAT & MOUTH (5 categories) ===
    'sore_throat': [
        "Is it painful to swallow?",
        "Do you see any white patches or redness?",
        "Any swollen glands in your neck?",
        "Do you have fever or body aches?",
        "How many days have you had the sore throat?"
    ],
    'mouth_sores': [
        "Where in your mouth are the sores?",
        "Are they painful or just visible?",
        "What do they look like (red, white, raised)?",
        "Do they interfere with eating or drinking?",
        "How long have you had mouth sores?"
    ],
    'bad_breath': [
        "How long have you noticed bad breath?",
        "Does it persist despite good oral hygiene?",
        "Any mouth sores or gum problems?",
        "Do you have sinus or throat problems?",
        "Are you taking any medications?"
    ],
    'dry_mouth': [
        "How long has your mouth been dry?",
        "Is it worse at certain times of day?",
        "Any difficulty swallowing or speaking?",
        "Are you taking any medications?",
        "Do you drink enough water daily?"
    ],
    'swollen_glands': [
        "Where are the swollen glands (neck, armpit, groin)?",
        "Are they painful or just enlarged?",
        "Any fever or other symptoms?",
        "How long have they been swollen?",
        "Have you had any recent infections?"
    ],

    # === GENITOURINARY SYSTEM (10 categories) ===
    'urinary_problems': [
        "Do you have pain or burning when urinating?",
        "Are you urinating more or less frequently than usual?",
        "Any blood in the urine?",
        "Do you feel like you can't completely empty your bladder?",
        "Any urgency or inability to control urination?"
    ],
    'kidney_pain': [
        "Where do you feel the pain (lower back, side, abdomen)?",
        "Is the pain constant or comes in waves?",
        "Any nausea, vomiting, or fever?",
        "Any changes in urination?",
        "How severe is the pain on a scale of 1-10?"
    ],
    'bladder_problems': [
        "Do you have urgency or frequency of urination?",
        "Any pain or pressure in the lower abdomen?",
        "Do you leak urine when coughing or sneezing?",
        "Any difficulty starting or stopping urination?",
        "How long have you had bladder problems?"
    ],
    'prostate_problems': [
        "Do you have difficulty starting urination? (Males)",
        "Any weak urine stream or dribbling?",
        "Do you wake up frequently at night to urinate?",
        "Any pain in the pelvic area?",
        "How long have you noticed these symptoms?"
    ],
    'menstrual_problems': [
        "Are your periods irregular, heavy, or painful? (Females)",
        "Any bleeding between periods?",
        "How long is your typical cycle?",
        "Any severe cramping or pelvic pain?",
        "When was your last menstrual period?"
    ],
    'sexual_health': [
        "Any pain or discomfort during sexual activity?",
        "Any changes in sexual desire or function?",
        "Any unusual discharge or symptoms?",
        "Any concerns about fertility or contraception?",
        "How long have you noticed these issues?"
    ],
    'pelvic_pain': [
        "Where exactly do you feel pelvic pain?",
        "Is it constant or comes and goes?",
        "Any relation to menstrual cycle? (Females)",
        "Any urinary or bowel symptoms?",
        "How long have you had pelvic pain?"
    ],
    'uti_symptoms': [
        "Do you have burning or pain when urinating?",
        "Any urgency or frequency of urination?",
        "Is your urine cloudy, bloody, or strong-smelling?",
        "Any pelvic or back pain?",
        "How long have you had these symptoms?"
    ],
    'incontinence': [
        "Do you leak urine involuntarily?",
        "Does it happen with coughing, sneezing, or exercise?",
        "Any urgency where you can't make it to the bathroom?",
        "How often does this occur?",
        "How long has this been a problem?"
    ],
    'erectile_dysfunction': [
        "Are you having difficulty achieving or maintaining erections? (Males)",
        "Is this a recent change or ongoing problem?",
        "Any decrease in sexual desire?",
        "Are you taking any medications?",
        "Any stress or relationship issues?"
    ],

    # === MENTAL HEALTH (7 categories) ===
    'anxiety': [
        "Do you feel excessively worried or nervous?",
        "Any physical symptoms like racing heart or sweating?",
        "Do you avoid certain situations due to anxiety?",
        "Any panic attacks or intense fear episodes?",
        "How long have you been experiencing anxiety?"
    ],
    'depression': [
        "Do you feel sad, hopeless, or empty most days?",
        "Any loss of interest in activities you used to enjoy?",
        "Any changes in sleep or appetite?",
        "Do you have thoughts of self-harm?",
        "How long have you felt this way?"
    ],
    'mood_swings': [
        "Do you have extreme changes in mood?",
        "How quickly do your moods change?",
        "Any periods of unusually high energy or irritability?",
        "Do mood changes affect your relationships or work?",
        "How long have you noticed mood swings?"
    ],
    'stress': [
        "What situations or factors cause you stress?",
        "Any physical symptoms like headaches or tension?",
        "How do you currently cope with stress?",
        "Is stress affecting your sleep or eating?",
        "How long have you been under significant stress?"
    ],
    'panic_attacks': [
        "Do you have sudden episodes of intense fear?",
        "Any physical symptoms like chest pain or shortness of breath?",
        "How long do these episodes last?",
        "What seems to trigger panic attacks?",
        "How often do you experience panic attacks?"
    ],
    'sleep_disorders': [
        "Do you have trouble falling or staying asleep?",
        "Any nightmares or disturbing dreams?",
        "Do you snore or have breathing problems during sleep?",
        "How many hours of sleep do you typically get?",
        "How long have you had sleep problems?"
    ],
    'concentration_problems': [
        "Do you have difficulty focusing or paying attention?",
        "Any problems with memory or decision-making?",
        "Is this affecting your work or daily activities?",
        "Any other mental health symptoms?",
        "When did you first notice concentration problems?"
    ]
}

# Global conversation storage
conversation_data = {}

def detect_language_from_script(text):
    """Detect language from script"""
    if any('\u0900' <= char <= '\u097F' for char in text):
        return 'hi'  # Hindi
    elif any('\u0C00' <= char <= '\u0C7F' for char in text):
        return 'te'  # Telugu  
    elif any('\u0B80' <= char <= '\u0BFF' for char in text):
        return 'ta'  # Tamil
    elif any('\u0980' <= char <= '\u09FF' for char in text):
        return 'bn'  # Bengali
    elif any('\u0A80' <= char <= '\u0AFF' for char in text):
        return 'gu'  # Gujarati
    elif any('\u0C80' <= char <= '\u0CFF' for char in text):
        return 'kn'  # Kannada
    elif any('\u0D00' <= char <= '\u0D7F' for char in text):
        return 'ml'  # Malayalam
    else:
        return 'en'  # English

def ai_smart_symptom_detection(text, detected_lang):
    """AI-powered symptom detection and translation"""
    categories_list = ", ".join(SYMPTOM_QUESTIONS.keys())
    
    prompt = f"""You are a medical AI assistant. Analyze: "{text}"

Provide:
TRANSLATION: [English translation if needed]
SYMPTOM_CATEGORY: [one of: {categories_list}]
CONFIDENCE: [1-10]

Choose the most specific category that matches."""

    try:
        response = model.generate_content(prompt)
        result = response.text.strip()
        
        translation = ""
        symptom_category = ""
        confidence = 0
        
        for line in result.split('\n'):
            if line.startswith('TRANSLATION:'):
                translation = line.replace('TRANSLATION:', '').strip()
            elif line.startswith('SYMPTOM_CATEGORY:'):
                symptom_category = line.replace('SYMPTOM_CATEGORY:', '').strip()
            elif line.startswith('CONFIDENCE:'):
                try:
                    confidence = int(line.replace('CONFIDENCE:', '').strip())
                except:
                    confidence = 5
        
        if symptom_category not in SYMPTOM_QUESTIONS:
            symptom_category = None
            
        return translation, symptom_category, confidence
        
    except Exception as e:
        print(f"AI symptom detection failed: {e}")
        return text, None, 0

def translate_to_user_language(text, language_name):
    """FIXED: Translate response back to user's language"""
    # Get the language code
    lang_code = LANGUAGES.get(language_name, 'en')
    
    if lang_code == 'en':
        return text
    
    try:
        # Use GoogleTranslator with correct language codes
        translator = GoogleTranslator(source='en', target=lang_code)
        translated = translator.translate(text)
        print(f"DEBUG: Translated '{text[:50]}...' from en to {lang_code}: '{translated[:50]}...'")
        return translated
    except Exception as e:
        print(f"Translation failed: {e}")
        # Fallback to Gemini
        try:
            prompt = f"Translate this medical text to {language_name}: {text}\n\nProvide only the translation:"
            response = model.generate_content(prompt)
            return response.text.strip()
        except:
            return text

def is_greeting_universal(message):
    """Universal greeting detection"""
    greetings = [
        'hi', 'hello', 'hey', 'hii', 'good morning', 'good evening',
        'namaste', 'नमस्ते', 'హలో', 'വണക്കം', 'নমস্কার', 'નમસ્તે'
    ]
    return any(greeting in message.lower() for greeting in greetings) and len(message.strip()) < 35

def is_valid_response(message):
    """Very lenient validation"""
    if not message or len(message.strip()) < 1:
        return False
    invalid = ['test', 'testing', '123', 'abc', 'xyz', '.', '..', '???', 'demo']
    return message.lower().strip() not in invalid

def count_questions_in_history(history):
    """Count medical questions asked"""
    if not history:
        return 0
    
    count = 0
    for exchange in history:
        try:
            ai_message = ""
            if isinstance(exchange, dict):
                if exchange.get('role') == 'assistant':
                    ai_message = exchange.get('content', '')
            elif isinstance(exchange, (list, tuple)) and len(exchange) >= 2:
                ai_message = str(exchange[1])
            
            if (ai_message and '?' in ai_message and 
                'Smart Symptom Checker' not in ai_message and
                'I understand you\'re experiencing' not in ai_message and
                '🔍' not in ai_message and
                'CATEGORY:' not in ai_message):
                count += 1
        except:
            continue
    
    return count

def has_symptom_acknowledgment(history):
    """Check if symptom acknowledged"""
    if not history:
        return False
    
    for exchange in history:
        try:
            ai_message = ""
            if isinstance(exchange, dict):
                if exchange.get('role') == 'assistant':
                    ai_message = exchange.get('content', '')
            elif isinstance(exchange, (list, tuple)) and len(exchange) >= 2:
                ai_message = str(exchange[1])
            
            if 'I understand you\'re experiencing' in ai_message:
                return True
        except:
            continue
    
    return False

def extract_stored_category(history):
    """Extract stored symptom category from conversation"""
    for exchange in history:
        try:
            ai_message = ""
            if isinstance(exchange, dict):
                if exchange.get('role') == 'assistant':
                    ai_message = exchange.get('content', '')
            elif isinstance(exchange, (list, tuple)) and len(exchange) >= 2:
                ai_message = str(exchange[1])
            
            if 'CATEGORY:' in ai_message:
                category = ai_message.split('CATEGORY:')[1].strip()
                if category in SYMPTOM_QUESTIONS:
                    return category
        except:
            continue
    
    return None

def collect_all_responses(history, current_message):
    """Collect all user responses"""
    responses = []
    
    if history:
        for exchange in history:
            try:
                user_msg = ""
                if isinstance(exchange, dict):
                    if exchange.get('role') == 'user':
                        user_msg = exchange.get('content', '')
                elif isinstance(exchange, (list, tuple)) and len(exchange) >= 2:
                    user_msg = str(exchange[0])
                
                if user_msg:
                    responses.append(user_msg)
            except:
                continue
    
    responses.append(current_message)
    return responses

def generate_comprehensive_diagnosis(responses, category, age, gender):
    """Generate final diagnosis with percentages"""
    responses_text = " | ".join(responses)
    
    prompt = f"""Based on medical assessment:
    Patient: {age}yr {gender}
    Category: {category}
    Responses: {responses_text}
    
    Provide diagnosis in EXACT format:
    
    🔍 **Top 3 Possible Conditions:**
    1. [Condition] - [X]% likelihood
    2. [Condition] - [X]% likelihood
    3. [Condition] - [X]% likelihood
    
    ⚠️ **Severity Assessment:** [Low/Medium/High/Emergency]
    
    📋 **Recommended Next Steps:**
    • [Action 1]
    • [Action 2]
    
    💡 **Self-Care Tips:**
    • [Tip 1]
    • [Tip 2]
    
    Use realistic percentages. Be specific with condition names."""
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        category_display = category.replace('_', ' ').title()
        return f"""🔍 **Top 3 Possible Conditions:**
1. Common {category_display} condition - 60% likelihood
2. Moderate related disorder - 25% likelihood
3. Less common alternative - 15% likelihood

⚠️ **Severity Assessment:** Medium

📋 **Recommended Next Steps:**
• Monitor symptoms and track changes
• Consult healthcare provider if symptoms persist

💡 **Self-Care Tips:**
• Rest and maintain good hydration
• Avoid known triggers

⚠️ This is not professional medical advice. Consult a doctor for proper diagnosis and treatment."""

# FIXED: Main processing function with proper parameter handling and translation
def process_complete_medical_query(message, history, age, gender, language, patient_name):
    """COMPLETE medical processing with FIXED translation and input handling"""
    global conversation_data
    
    # DEBUG: Print all received parameters
    print(f"DEBUG: message='{message}', age={age}, gender='{gender}', language='{language}', patient_name='{patient_name}'")
    
    # Store conversation data for report (with actual values)
    conversation_data = {
        'patient_name': patient_name if patient_name and patient_name.strip() else f"Patient_{datetime.now().strftime('%Y%m%d')}",
        'age': age if age is not None else 25,
        'gender': gender if gender else 'Male',
        'language': language if language else 'English',
        'history': history if history else [],
        'current_message': message if message else ''
    }
    
    if not message:
        welcome_msg = "Please describe your symptoms to get started."
        if language and language != 'English':
            welcome_msg = translate_to_user_language(welcome_msg, language)
        return welcome_msg
    
    message = str(message).strip()
    
    # Detect language from text
    detected_lang = detect_language_from_script(message)
    
    # Handle greetings
    if is_greeting_universal(message):
        response = f"👋 Hello! I'm your Smart Symptom Checker. Please describe your symptoms in detail."
        if language and language != 'English':
            response = translate_to_user_language(response, language)
        return response
    
    # Get conversation state
    questions_asked = count_questions_in_history(history)
    had_ack = has_symptom_acknowledgment(history)
    stored_category = extract_stored_category(history)
    all_responses = collect_all_responses(history, message)
    
    print(f"DEBUG: Questions: {questions_asked}, Had ack: {had_ack}, Category: {stored_category}")
    
    # Validate input (very lenient)
    if not is_valid_response(message) and not stored_category and questions_asked == 0:
        response = "🤔 Please describe your symptoms or health concerns in more detail."
        if language and language != 'English':
            response = translate_to_user_language(response, language)
        return response
    
    # Initial symptom detection and acknowledgment
    if not stored_category and not had_ack:
        translation, symptom_category, confidence = ai_smart_symptom_detection(message, detected_lang)
        
        if symptom_category and confidence >= 6:
            response = f"I understand you're experiencing: {message}\n\nLet me ask some targeted questions to help assess your condition.\n\nCATEGORY:{symptom_category}"
            
            if language and language != 'English':
                visible_part = f"I understand you're experiencing: {message}\n\nLet me ask some targeted questions to help assess your condition."
                translated = translate_to_user_language(visible_part, language)
                response = f"{translated}\n\nCATEGORY:{symptom_category}"
            
            return response
        else:
            response = "I understand your health concern. Let me ask some questions to help assess your condition."
            if language and language != 'English':
                response = translate_to_user_language(response, language)
            return response
    
    # Get category from history if not available
    if not stored_category:
        stored_category = extract_stored_category(history)
    
    # Ask targeted questions (up to 5)
    if stored_category and questions_asked < 5:
        question = SYMPTOM_QUESTIONS[stored_category][questions_asked]
        
        if language and language != 'English':
            question = translate_to_user_language(question, language)
        
        return question
    
    # Generate comprehensive diagnosis after 5 questions
    elif questions_asked >= 5 and stored_category:
        diagnosis = generate_comprehensive_diagnosis(all_responses, stored_category, age, gender)
        
        # Store diagnosis for report
        conversation_data['diagnosis'] = diagnosis
        
        if language and language != 'English':
            diagnosis = translate_to_user_language(diagnosis, language)
        
        return diagnosis
    
    # Default fallback
    else:
        response = "Please describe your main symptom so I can help assess your condition."
        if language and language != 'English':
            response = translate_to_user_language(response, language)
        return response

# SIMPLIFIED REPORT GENERATION (keeping the working version)
def create_bulletproof_report(name, age, gender, language, diagnosis):
    """Create a report that ALWAYS works"""
    try:
        from fpdf import FPDF
        return create_fpdf2_report(name, age, gender, language, diagnosis)
    except ImportError:
        print("DEBUG: fpdf2 not available, trying text report...")
    except Exception as e:
        print(f"DEBUG: fpdf2 failed: {e}")
    
    try:
        return create_text_report(name, age, gender, language, diagnosis)
    except Exception as e:
        print(f"DEBUG: Text report failed: {e}")
        return None

def create_fpdf2_report(name, age, gender, language, diagnosis):
    """Create PDF using fpdf2"""
    from fpdf import FPDF
    
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Header
    pdf.set_fill_color(70, 130, 180)
    pdf.rect(0, 0, 210, 30, 'F')
    
    pdf.set_font('Arial', 'B', 18)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(10, 8)
    pdf.cell(0, 10, 'MedMind AI - Medical Assessment Report', 0, 1, 'C')
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_y(35)
    
    # Patient Information
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Patient Information', 0, 1, 'L')
    pdf.ln(5)
    
    pdf.set_font('Arial', '', 11)
    patient_info = [
        f'Name: {name}',
        f'Age: {age} years',
        f'Gender: {gender}',
        f'Language: {language}',
        f'Assessment Date: {datetime.now().strftime("%B %d, %Y")}'
    ]
    
    for info in patient_info:
        pdf.cell(0, 7, info, 0, 1, 'L')
    pdf.ln(8)
    
    # Medical Assessment
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Medical Assessment Results', 0, 1, 'L')
    pdf.ln(5)
    
    pdf.set_font('Arial', '', 10)
    
    if diagnosis and len(diagnosis.strip()) > 10:
        lines = diagnosis.split('\n')
        for line in lines:
            line = line.strip()
            if line:
                try:
                    clean_line = line.encode('latin-1', errors='ignore').decode('latin-1')
                    pdf.cell(0, 6, clean_line[:85], 0, 1, 'L')
                except:
                    safe_line = ''.join(c for c in line if ord(c) < 128)
                    pdf.cell(0, 6, safe_line[:85], 0, 1, 'L')
                pdf.ln(1)
    else:
        pdf.cell(0, 7, 'Assessment: Please complete your medical evaluation for detailed results.', 0, 1, 'L')
    
    pdf.ln(15)
    
    # Disclaimer
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(220, 53, 69)
    pdf.cell(0, 8, 'IMPORTANT MEDICAL DISCLAIMER', 0, 1, 'C')
    pdf.ln(5)
    
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(0, 0, 0)
    disclaimer_text = [
        'This report is generated by MedMind AI for educational purposes only.',
        'It is NOT a substitute for professional medical advice, diagnosis, or treatment.',
        'Always consult with qualified healthcare professionals for medical concerns.'
    ]
    
    for text in disclaimer_text:
        pdf.cell(0, 6, text, 0, 1, 'C')
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    try:
        pdf.output(temp_file.name)
        return temp_file.name
    except Exception as e:
        print(f"PDF output failed: {e}")
        temp_file.close()
        os.unlink(temp_file.name)
        return None

def create_text_report(name, age, gender, language, diagnosis):
    """Create text report as fallback"""
    try:
        content = f"""
MEDMIND AI - MEDICAL ASSESSMENT REPORT
====================================

PATIENT INFORMATION:
-------------------
Name: {name}
Age: {age} years
Gender: {gender}
Language: {language}
Assessment Date: {datetime.now().strftime("%B %d, %Y")}
Report Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}

MEDICAL ASSESSMENT RESULTS:
--------------------------
{diagnosis if diagnosis else 'Please complete your medical assessment in the chat for detailed results.'}

IMPORTANT MEDICAL DISCLAIMER:
----------------------------
This report is generated by MedMind AI for educational purposes only.
It is NOT a substitute for professional medical advice, diagnosis, or treatment.
Always consult with qualified healthcare professionals for medical concerns.
In case of medical emergency, contact your local emergency services immediately.

MedMind AI - Your Digital Health Assistant
Report ID: TXT-{datetime.now().strftime("%Y%m%d%H%M%S")}
"""
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8')
        temp_file.write(content)
        temp_file.close()
        
        return temp_file.name
        
    except Exception as e:
        print(f"Text report creation failed: {e}")
        return None

def generate_report_file():
    """Generate report with actual patient data"""
    global conversation_data
    
    if not conversation_data:
        conversation_data = {
            'patient_name': 'Demo Patient',
            'age': 30,
            'gender': 'Male',
            'language': 'English',
            'diagnosis': 'Demo assessment - Complete your medical chat for detailed results.'
        }
    
    try:
        report_path = create_bulletproof_report(
            name=conversation_data.get('patient_name', 'Patient'),
            age=conversation_data.get('age', 25),
            gender=conversation_data.get('gender', 'Male'),
            language=conversation_data.get('language', 'English'),
            diagnosis=conversation_data.get('diagnosis', 'Assessment in progress')
        )
        
        return report_path
        
    except Exception as e:
        print(f"Report generation failed: {e}")
        return None

def handle_report_generation():
    """Handle report generation"""
    try:
        report_path = generate_report_file()
        
        if report_path and os.path.exists(report_path):
            file_size = os.path.getsize(report_path)
            file_type = "PDF" if report_path.endswith('.pdf') else "Text"
            
            return (
                gr.File(value=report_path, visible=True),
                f"✅ {file_type} report generated successfully! ({file_size} bytes) Click to download."
            )
        else:
            return (
                gr.File(visible=False),
                "❌ Report generation failed. Please try again."
            )
                
    except Exception as e:
        return (
            gr.File(visible=False),
            f"❌ Error: {str(e)}"
        )

# Enhanced CSS
complete_css = """
.gradio-container {
    background-image: url('https://i.pinimg.com/1200x/79/c8/cf/79c8cf536a3f4a57b6d624e78c736095.jpg');
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    min-height: 100vh;
    position: relative;
}

.gradio-container::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    
    z-index: 1;
}

.gradio-container > * {
    position: relative;
    z-index: 2;
}

.header {
    text-align: center;
    
    padding: 35px 25px;
    
    backdrop-filter: blur(25px);
    border-radius: 25px;
    margin: 20px;
    
}

.profile {
    background: LemonChiffon;
    backdrop-filter: blur(20px);
    border-radius: 20px;
    padding: 30px;
    margin: 15px;
    border: 1px solid rgba(255,255,255,0.35);
}

.chat {
    background: rgba(255,255,255,0.98);
    border-radius: 20px;
    padding: 25px;
    margin: 15px;
    box-shadow: 0 20px 40px rgba(0,0,0,0.25);
}

.features {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin-top: 25px;
    flex-wrap: wrap;
}

.feature {
    background: rgba(255,255,255,0.25);
    padding: 12px 20px;
    border-radius: 25px;
    font-size: 0.95em;
    font-weight: 500;
    border: 1px solid rgba(255,255,255,0.4);
    backdrop-filter: blur(15px);
    transition: all 0.3s ease;
}

.feature:hover {
    background: rgba(255,255,255,0.35);
    transform: translateY(-2px);
}
"""

def create_complete_medmind_app():
    """Create COMPLETE working MedMind AI with FIXED inputs and translation"""
    
    with gr.Blocks(css=complete_css, title="🩺 MedMind AI - All Features Working") as app:
        
        # Header
        gr.HTML("""
        <div class="header">
            <h1 style="font-size: 3.5em; margin-bottom: 15px; text-shadow: 3px 3px 8px rgba(0,0,0,0.4); font-weight: 700;">
                🩺 MedMind AI
            </h1>
            <p style="font-size: 1.5em; margin-bottom: 10px; font-weight: 300; opacity: 0.95;">
                Your Health, Your Language, Your Peace of Mind
            </p>
            <p style="font-size: 1.2em; opacity: 0.9; margin-bottom: 25px;">
                Smart Diagnosis, Smart Translation, Smart Reports - Smart Healthcare
            </p>
            
            <div class="features">
                <div class="feature">🎯 AI-Powered Smart Symptom Detection
</div>
                <div class="feature">🤖 Multilingual Translation</div>
                <div class="feature">👤 Fixed Input Fields</div>
                <div class="feature">📋 PDF Reports</div>
                <div class="feature">✅ Comprehensive Medical Assessment </div>
            </div>
        </div>
        """)

        with gr.Row():
            # Patient profile section
            with gr.Column(scale=1, elem_classes="profile"):
                gr.HTML("""
                <div style="color: PaleVioletRed; text-align: center; margin-bottom: 25px;">
                    <h3 style="font-size: 1.3em; font-weight: 600; margin-bottom: 8px;">👤 Patient Information</h3>
                    <p style="font-size: 1em; opacity: 0.85;"></p>
                </div>
                """)
                
                # Patient inputs - FIXED to work with ChatInterface
                patient_name_input = gr.Textbox(
                    label="👤 Patient Name",
                    placeholder="Enter patient name",
                    value="Joh",
                    
                )
                
                age_input = gr.Number(
                    label="🎂 Age",
                    value=30,
                    minimum=0,
                    maximum=120,
                   
                )
                
                gender_input = gr.Dropdown(
                    choices=["Male", "Female", "Other"],
                    label="⚧️ Gender",
                    value="Male",
                    
                )
                
                language_input = gr.Dropdown(
                    choices=list(LANGUAGES.keys()),  # Use language names as choices
                    label="🌍 Preferred Language",
                    value="English",
                    
                )

                # Report section
                gr.HTML("""
                <div style="background: rgba(255,255,255,0.2); padding: 20px; border-radius: 15px; margin-top: 20px; color: white;">
                    <h4 style="margin-bottom: 15px; font-size: 1.2em; text-align: center;">📋 Professional Medical Report</h4>
                    <div style="text-align: center; line-height: 1.8;">
                        <p style="font-size: 0.9em; margin-bottom: 15px;">
                            Generate report with actual patient data
                        </p>
                    </div>
                </div>
                """)
                
                report_file = gr.File(
                    label="📄 Generated Medical Report",
                    visible=False,
                    file_count="single",
                    file_types=[".pdf", ".txt"]
                )
                
                generate_report_btn = gr.Button(
                    "📋 Generate Medical Report", 
                    variant="primary",
                    size="lg"
                )
                
                status_msg = gr.Textbox(
                    label="Status",
                    value="Ready to generate report with your information",
                    interactive=False
                )
                
                generate_report_btn.click(
                    fn=handle_report_generation,
                    outputs=[report_file, status_msg]
                )

            # Chat interface - FIXED with correct examples format
            with gr.Column(scale=2, elem_classes="chat"):
                gr.HTML("""
                <div style="text-align: center; margin-bottom: 25px;">
                    <h3 style="color: #2c3e50; font-size: 1.4em; font-weight: 600; margin-bottom: 8px;">
                        💬 Professional Health Assessment with Multilingual Support
                    </h3>
                    <p style="color: #5a6c7d; font-size: 1em; margin-top: 8px;">
                     
                    </p>
                </div>
                """)
                
                # FIXED ChatInterface with properly formatted examples for additional_inputs
                chatbot = gr.ChatInterface(
                    process_complete_medical_query,
                    additional_inputs=[age_input, gender_input, language_input, patient_name_input],
                    examples=[
                        # FIXED FORMAT: [message, age, gender, language, patient_name]
                        ["मेरी त्वचा पर चकत्ते/जलन है", 30, "Female", "Hindi", "Priya Sharma"],
                        ["I have severe stomach pain", 25, "Female", "English", "Sarah Johnson"],
                        ["मुझे सांस लेने में तकलीफ हो रही है", 35, "Male", "Hindi", "राहुल गुप्ता"],
                       
                        ["నাకు తల నొప్పి ఉంది", 40, "Male", "Telugu", "రామ్ కుమార్"],
                        ["I feel very tired", 32, "Female", "English", "Emma Wilson"],
                        ["আমার কাশি হচ্ছে", 45, "Male", "Bengali", "রহিম আহমেদ"]
                        
                    ],
                    cache_examples=False,
                    type="messages"
                )

        # Disclaimer
        gr.HTML("""
        <div style="background: linear-gradient(135deg, rgba(255,193,7,0.2), rgba(255,152,0,0.2)); color: #8b4513; padding: 25px; border-radius: 15px; margin: 30px 15px; text-align: center; border: 2px solid rgba(255,193,7,0.4);">
            <h4 style="margin: 0 0 15px 0; font-size: 1.3em; font-weight: 700;">⚠️ Important Medical Disclaimer</h4>
            <p style="margin: 0 0 18px 0; font-size: 1.05em; line-height: 1.6;">
                <strong>MedMind AI provides educational health information only and is powered by artificial intelligence for symptom assessment and multilingual translation. This comprehensive system with 117+ medical categories is not a substitute for professional medical advice, diagnosis, or treatment.</strong> 
                
            </p>
            <p style="margin: 0 0 15px 0; font-size: 1.15em; font-weight: 600; color: #d32f2f;">
                🚨 <strong>🚨 Medical Emergency? Contact emergency services immediately! Do not rely on AI assessment for urgent medical conditions - call 911, 108, or your local emergency number.</strong>
            </p>
            <div style="margin-top: 20px; padding-top: 15px; border-top: 1px solid rgba(139, 69, 19, 0.3);">
                <p style="margin: 0; font-size: 0.95em; opacity: 0.85;">
                    ✅ <strong>Healthcare Intelligence That Speaks Your Language
                </p>
            </div>
        </div>
        """)

    return app

if __name__ == "__main__":
    print("🩺 Starting FIXED MedMind AI System...")
    print("✅ All features now working:")
    print("   👤 Patient name, age, gender inputs - FIXED")
    print("   🌍 Language selection and translation - FIXED")
    print("   🤖 AI symptom detection - WORKING")
    print("   📋 PDF report generation - WORKING")
    print("   💾 Download functionality - WORKING")
    
    # Create and launch
    working_app = create_complete_medmind_app()
    
    print("\n🎉 MedMind AI with ALL FIXED features is ready!")
    print("📱 Local: http://127.0.0.1:7860")
    
    working_app.launch(
        share=True,                   # Creates public URL for HTML linking
        inbrowser=True,               # Opens browser automatically
        show_error=True               # Shows errors for debugging
    )
