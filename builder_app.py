import os
import streamlit as st
from google import genai
from google.genai import types 
from io import BytesIO
import urllib.parse 
import time
import mimetypes # <<< IMEONGEZWA KWA AJILI YA MIMETYPE ERROR

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
    """
    st.session_state.app_state = new_state
    
    # Safisha chat history kabla ya kuanza awamu mpya (isipokuwa awamu ya 4)
    if new_state != 4:
        st.session_state.chat_history = []
        st.session_state.intro_questions_count = 0
    
def upload_file_to_gemini(uploaded_file):
    """Hupakia faili kwenye Gemini File API na kurejesha File Object kwa kutumia BytesIO."""
    st.info(f"⚡ Inapakia faili '{uploaded_file.name}' kwa ajili ya kuchambuliwa. Tafadhali subiri...")
    try:
        uploaded_file.seek(0)
        file_bytes = uploaded_file.read()

        # --- LOGIC YA MIMETYPE (KUREKEBISHA KOSA LA MIMETYPE) ---
        mime_type, _ = mimetypes.guess_type(uploaded_file.name)
        if mime_type is None:
            # Kutumia mime type mbadala kwa txt/docx ikiwa haiwezi kujua
            if uploaded_file.name.lower().endswith(('.txt', '.docx')):
                 mime_type = 'text/plain' 
            else:
                raise ValueError("Could not determine file type. Please try PDF, DOCX, or TXT.")

        # 2. Jaribu kupakia mara 3
        for _ in range(3):
            try:
                # --- HAKUNA display_name (KUREKEBISHA KOSA LA display_name) ---
                gemini_file = client.files.upload(
                    file=BytesIO(file_bytes),
                    mime_type=mime_type 
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
    Hutuma ombi la stateless kwa Gemini.
    """
    
    config = types.GenerateContentConfig(
        system_instruction=current_prompt
    )

    contents = []
    
    for role, text in history:
        gemini_role = 'user' if role == 'user' else 'model'
        # Kutumia types.Part(text=text) (KUREKEBISHA KOSA LA Part.from_text)
        contents.append(
            types.Content(role=gemini_role, parts=[types.Part(text=text)])
        )

    # Ikiwa kuna faili (State 3), ongeza kwenye content ya mwisho ya user
    if file_object is not None and len(contents) > 0:
        last_user_content = contents[-1] 
        if file_object not in last_user_content.parts:
            last_user_content.parts.insert(0, file_object)
            contents[-1] = last_user_content 
        
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
            config=config
        )
    except Exception as e:
        st.error(f"🚨 Kosa la API: Kushindwa kuwasiliana na Gemini. {e}")
        return "Samahani, AI imeshindwa kujibu swali hili kutokana na kosa la mawasiliano. Tafadhali jaribu tena."
    
    # ULINZI DHIDI YA RESPONSE TUPU/KOSA
    if response.text:
        return response.text
    else:
        st.error("🚨 Kosa la API: Gemini imerudisha jibu tupu. Huenda ombi lilikuwa refu au gumu sana.")
        return "Samahani, AI imeshindwa kujibu swali hili kwa sasa. Tafadhali jaribu tena."

def generate_final_ai_prompt(gemini_file):
    """Huzalisha Prompt ya mwisho ya AI kwa kutumia PDF iliyopakuliwa."""
    st.info("⚡ Inazalisha System Prompt ya mwisho ya AI kwa kutumia taarifa zote...")
    
    analysis_prompt = (
        "Chambua kwa kina taarifa muhimu za biashara hii kutoka kwenye faili lililopakuliwa. "
        "Kisha, kwa kutumia taarifa hizo, **tengeneza System Prompt kamili (Final AI Prompt)** "
        "ambayo inaweza kutumiwa moja kwa moja kuendesha AI ya Huduma kwa Wateja. "
        "Prompt hii inapaswa kuwa fupi, kali, na ieleze JINA LA BIASHARA, ROLE YA AI, na MWELEKEO WA MAZUNGUMZO. "
        "Anza jibu lako na prompt hiyo kamili."
    )
    
    text_part = types.Part(text=analysis_prompt)
    
    analysis_content = [
        types.Content(role="user", parts=[
            text_part,
            gemini_file 
        ])
    ]

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=analysis_content
        )
        
        if response.text:
            return response.text
        else:
            st.error("🚨 Kosa: Gemini imerudisha jibu tupu wakati wa kuzalisha Final Prompt.")
            return "Imeshindwa kuzalisha Final Prompt kwa sababu ya kosa la mawasiliano."
            
    except Exception as e:
        st.error(f"Kosa la Kuzalisha Final Prompt: {e}")
        return "Imeshindwa kuzalisha Final Prompt."

# ----------------- STREAMLIT UI -----------------

st.set_page_config(page_title="Aura AI: Mjenzi wa AI", layout="wide")

# Angalia URL Parameter (Kwa AI Iliyoundwa - State 4)
query_params = st.query_params
if 'final_ai_mode' in query_params and query_params['final_ai_mode'] == 'true':
    st.session_state.app_state = 4
    st.session_state.current_prompt = RAG_PROMPT 
    st.session_state.gemini_file = None 
    
    ai_name = query_params.get('ai_name', 'Mchambuzi wa Biashara')
    
    if 'final_ai_chat_history' not in st.session_state:
        st.session_state.final_ai_chat_history = []
        st.session_state.final_ai_chat_history.append(("assistant", f"Karibu! Mimi ni **{ai_name}**, AI maalum niliyefunzwa kwa nyaraka za biashara yako. Unaweza kuanza kuuliza maswali yote kuhusu huduma/bidhaa zako."))
        
    st.session_state.chat_history = st.session_state.final_ai_chat_history
    st.title(f"🤖 AI Yako Iliyoundwa: {ai_name}")
    st.subheader("Una chat na AI iliyoundwa kutokana na maelezo ya PDF.")
    
# ----------------- HALI ZA MWANZO/DEFAULT -----------------
# Hakikisha keys zote zipo
if 'app_state' not in st.session_state: st.session_state.app_state = 1
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'gemini_file' not in st.session_state: st.session_state.gemini_file = None
if 'final_ai_prompt_text' not in st.session_state: st.session_state.final_ai_prompt_text = None
if 'current_prompt' not in st.session_state: st.session_state.current_prompt = INTRO_PROMPT
if 'chat_title' not in st.session_state: st.session_state.chat_title = "Aura - Msaidizi wa AI"
if 'intro_questions_count' not in st.session_state: st.session_state.intro_questions_count = 0
if 'file_display_name' not in st.session_state: st.session_state.file_display_name = None # <<< Kurekebisha AttributeError

if st.session_state.app_state != 4:
    st.title("✨ Aura AI: Jenga AI Yako Kutoka kwa Nyaraka")
    st.subheader("Utangulizi, Elimu, na Kujenga AI kwa Kutumia Nyaraka za Biashara.")


# --- KUANZISHA MAZUNGUMZO (INTRO GREETING) ---
if st.session_state.app_state == 1 and len(st.session_state.chat_history) == 0:
    intro_message = "Habari! Mimi naitwa **Aura**, na mimi ni msaidizi wako katika safari ya kujenga AI maalum kwa ajili ya biashara yako. Kwanza, unaweza kuniuliza maswali kuhusu **umuhimu wa kutumia AI** kwenye biashara yako."
    st.session_state.chat_history.append(("assistant", intro_message))


# ----------------------------------------------
# KIPENGELE KIKUU CHA CHAT
# ----------------------------------------------
st.markdown("---")
if st.session_state.app_state not in [4, 6]:
    st.header(f"💬 Chat na {st.session_state.chat_title}")

# 1. Onyesha Historia ya Chat
for role, text in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(text)


# 2. Kuingiza Ujumbe (Input)
if st.session_state.app_state in [1, 3, 4]: 
    user_prompt = st.chat_input("Tuma ujumbe kwa AI yako...")
    
    if user_prompt:
        
        with st.chat_message("user"):
            st.markdown(user_prompt)
        
        st.session_state.chat_history.append(("user", user_prompt))
        
        with st.spinner("AI inajibu..."):
            
            response_text = get_gemini_response(
                st.session_state.current_prompt,
                st.session_state.gemini_file,
                st.session_state.chat_history
            )
            
            # ----------------- LOGIC YA KUFUATA HATUA -----------------
            if st.session_state.app_state == 1:
                st.session_state.intro_questions_count += 1
                
                with st.chat_message("assistant"):
                    st.markdown(response_text)
                    
                st.session_state.chat_history.append(("assistant", response_text))
                
                # Badilisha awamu baada ya maswali 3
                if st.session_state.intro_questions_count >= 3 and not "Samahani, AI imeshindwa kujibu" in response_text:
                    final_intro = (
                        "\n\n**Asante kwa maswali mazuri!** Sasa kwa kuwa umeelewa umuhimu wa AI, "
                        "tuanze kuijenga AI yako maalum. Tafadhali **pakia faili la taarifa za biashara yako** (PDF, DOCX, n.k.) hapo chini."
                    )
                    st.session_state.chat_history.append(("assistant", final_intro))
                    cleanup_and_transition(2) 
                    st.rerun() 

            elif st.session_state.app_state == 3:
                
                with st.chat_message("assistant"):
                    st.markdown(response_text)
                st.session_state.chat_history.append(("assistant", response_text))

                # Badilisha awamu baada ya maswali 3 ya user (jumla ya messages 8 kwenye chat_history)
                if len(st.session_state.chat_history) >= 8 and not "Samahani, AI imeshindwa kujibu" in response_text: 
                    st.session_state.chat_history.append(("assistant", "Naona sasa nimechambua taarifa zako za msingi. Sasa naanza **kuzalisha AI Prompt yako ya mwisho!**"))
                    cleanup_and_transition(5) 
                    st.rerun() 

            elif st.session_state.app_state == 4:
                # Hali ya AI iliyoundwa (Final AI Mode)
                with st.chat_message("assistant"):
                    st.markdown(response_text)
                st.session_state.chat_history.append(("assistant", response_text))
                


# ----------------- KIPENGELE CHA KUPAKIA FAILII (AWAMU YA 2) -----------------
if st.session_state.app_state == 2:
    st.markdown("---")
    st.header("Upload File (PDF)")
    
    uploaded_file = st.file_uploader(
        "Pakia Nyaraka za Biashara (PDF, DOCX, au TXT):", 
        type=["pdf", "txt", "docx", "pptx"],
        accept_multiple_files=False,
        key="file_uploader_key"
    )

    # Ukubwa wa Faili (Kuepuka API Errors)
    MAX_FILE_SIZE_MB = 90  
    
    if uploaded_file is not None and st.session_state.gemini_file is None:
        file_size_mb = uploaded_file.size / (1024 * 1024)
        
        if file_size_mb > MAX_FILE_SIZE_MB:
            st.error(f"🚨 Kosa: Ukubwa wa faili ({file_size_mb:.2f} MB) unazidi ukomo unaokubalika wa {MAX_FILE_SIZE_MB} MB. Tafadhali pakia faili dogo.")
            st.stop()
        
        # Endelea kupakia faili
        st.session_state.gemini_file = upload_file_to_gemini(uploaded_file)
        
        if st.session_state.gemini_file:
            # --- Hifadhi Jina la Faili Kwenye Session State (Kurekebisha AttributeError) ---
            st.session_state.file_display_name = uploaded_file.name # Jina la kuonyesha
            
            st.session_state.chat_title = st.session_state.file_display_name + " (Mchambuzi)"
            st.session_state.current_prompt = RAG_PROMPT 
            
            pdf_intro = f"✅ Hongera! Faili **{st.session_state.file_display_name}** limepakuliwa. Sasa unaweza **kuuliza maswali kuhusu taarifa zilizomo kwenye faili** ili kuhakikisha ninazielewa vizuri kabla ya ujenzi wa AI."
            st.session_state.chat_history.append(("assistant", pdf_intro))
            
            cleanup_and_transition(3) 
            st.rerun() 
            
# ----------------- KIPENGELE CHA KUZALISHA LINK (AWAMU YA 5) -----------------
if st.session_state.app_state == 5:
    st.markdown("---")
    st.header("🎉 AI Deployment Inakamilika!")

    if st.session_state.final_ai_prompt_text is None:
        final_prompt = generate_final_ai_prompt(st.session_state.gemini_file)
        st.session_state.final_ai_prompt_text = final_prompt
        
    st.success("🤖 Prompt ya AI Imeundwa kwa Mafanikio!")
    
    with st.expander("Ona Prompt Iliyoundwa (Final AI Prompt)"):
        st.code(st.session_state.final_ai_prompt_text, language='markdown')

    # --- KUTENGENEZA LINK YA AI ILIYOKAMILIKA ---
    ai_name = "AI ya Biashara Yako" 
    
    try:
        base_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}" 
        if not base_url or "None" in base_url:
            base_url = st.experimental_get_query_params().keys().__next__() if st.experimental_get_query_params() else "http://localhost:8501"
            base_url = base_url.split('?')[0]
    except Exception:
        base_url = "http://localhost:8501" 

    ai_link = base_url + "?" + urllib.parse.urlencode({
        'final_ai_mode': 'true', 
        'ai_name': ai_name,
        'chat_mode': 'final'
    })

    st.markdown(f"""
    ## **AI YAKO IMEKAMILIKA!**
    
    Aura amemaliza kuchambua nyaraka zako na kuunda AI maalum. Unaweza kuitumia kuanzia sasa!
    
    **Link ya AI Yako Hii Hapa:**
    ### **[{ai_name}]({ai_link})**
    
    Bonyeza link hiyo ili kuona AI yako mpya ikifanya kazi!
    """)
    st.session_state.app_state = 6 # Imekamilika
