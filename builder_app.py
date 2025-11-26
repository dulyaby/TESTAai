import os
import streamlit as st
from google import genai
from google.genai import types 
from io import BytesIO
import urllib.parse 
import time

# ----------------- CONFIGURATION -----------------
# Pata Gemini API Key kutoka kwenye Environment Variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 

if not GEMINI_API_KEY:
    # Tumia st.sidebar kwa ujumbe wa kosa
    st.sidebar.error("🚨 GEMINI_API_KEY haipatikani kwenye Environment Variables. Tafadhali weka 'GEMINI_API_KEY'.")
    st.stop()
    
# Initialize Gemini Client
try:
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    st.error(f"🚨 Imeshindwa kuunganisha Gemini Client: {e}")
    st.stop()

# ----------------- CHAT PROMPTS AND ROLES -----------------
INTRO_PROMPT = (
    "Wewe ni AI inayoitwa 'Aura', msaidizi wa kujenga AI za biashara. "
    "Jukumu lako kuu ni kumwelekeza mfanyabiashara umuhimu wa kujenga AI yake binafsi, "
    "kwa kutumia nyaraka zake za biashara. Ongea kwa Kiswahili fasaha, uwe na adabu, "
    "na mtaalamu. Jibu maswali yanayohusu faida za AI kwa biashara ndogo na za kati. "
    "Baada ya kujibu maswali mawili au matatu, au mtumiaji anapoelewa, unapaswa kumwomba "
    "apakie nyaraka zake za biashara (PDF, DOCX, n.k.) ili kuendelea na awamu ya ujenzi wa AI."
)

RAG_PROMPT = (
    "Wewe ni Mchambuzi Maalum wa Taarifa za Biashara. "
    "Jukumu lako ni kujibu maswali yote yanayohusu biashara ya mteja KWA KUTUMIA PEKEE "
    "taarifa zilizomo kwenye nyaraka zilizopakuliwa (PDF, n.k.). "
    "Kama taarifa haipatikani kwenye nyaraka, sema kwa adabu, 'Taarifa hiyo haipatikani kwenye nyaraka zilizopakuliwa.' "
    "Dumisha sauti ya mtaalamu na jibu kwa Kiswahili isipokuwa uombwe vingine."
)

# ----------------- HELPER FUNCTIONS -----------------

def cleanup_and_transition(new_state):
    """
    Hufuta historia ya chat na kuanzisha awamu mpya kwa usafi. 
    Hii inasaidia kuzuia makosa ya state management ya Streamlit.
    """
    st.session_state.app_state = new_state
    
    # Safisha chat history kabla ya kuanza awamu mpya (isipokuwa awamu ya 4)
    if new_state != 4:
        st.session_state.chat_history = []
        st.session_state.intro_questions_count = 0
    
    st.rerun()

def upload_file_to_gemini(uploaded_file):
    """Hupakia faili kwenye Gemini File API na kurejesha File Object kwa kutumia BytesIO."""
    st.info(f"⚡ Inapakia faili '{uploaded_file.name}' kwa ajili ya kuchambuliwa. Tafadhali subiri...")
    try:
        # Rudi mwanzo wa faili kwa ajili ya kusoma tena (muhimu kwa Streamlit)
        uploaded_file.seek(0)
        file_bytes = uploaded_file.read()
        
        # Jaribu tena mara 3
        for _ in range(3):
            try:
                gemini_file = client.files.upload(
                    file=BytesIO(file_bytes),
                    display_name=uploaded_file.name
                )
                return gemini_file
            except Exception as e:
                time.sleep(1) 
                if _ == 2:
                    raise e
                    
    except Exception as e:
        st.error(f"🚨 Kosa la Kupakia Faili: {e}")
        return None

def get_gemini_response(current_prompt, file_object, history):
    """
    Hutuma ombi la stateless kwa Gemini. Inajumuisha uhakiki wa jibu tupu (kuepusha list index out of range).
    """
    
    config = types.GenerateContentConfig(
        system_instruction=current_prompt
    )

    contents = []
    
    for role, text in history:
        gemini_role = 'user' if role == 'user' else 'model'
        contents.append(
            types.Content(role=gemini_role, parts=[types.Part.from_text(text)])
        )

    # Ikiwa kuna faili (State 3), ongeza kwenye content ya mwisho ya user
    if file_object is not None and len(contents) > 0:
        last_user_content =
