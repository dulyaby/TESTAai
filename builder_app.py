import os
import streamlit as st
from google import genai
from google.genai import types 
from io import BytesIO
import urllib.parse # Kwa ajili ya kuunda Link ya URL

# ----------------- CONFIGURATION -----------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error("🚨 GEMINI_API_KEY haipatikani kwenye Environment Variables. Tafadhali weka 'GEMINI_API_KEY'.")
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

def upload_file_to_gemini(uploaded_file):
    """Hupakia faili kwenye Gemini File API na kurejesha File Object."""
    st.info(f"⚡ Inapakia faili '{uploaded_file.name}' kwa ajili ya kuchambuliwa. Tafadhali subiri...")
    try:
        file_bytes = uploaded_file.read()
        gemini_file = client.files.upload(
            file=BytesIO(file_bytes),
            display_name=uploaded_file.name
        )
        return gemini_file
    except Exception as e:
        st.error(f"🚨 Kosa la Kupakia Faili: {e}")
        return None

def get_gemini_response(current_prompt, file_object, history):
    """Hutuma ombi la stateless kwa Gemini."""
    config = types.GenerateContentConfig(
        system_instruction=current_prompt
    )
    contents = []
    
    for role, text in history:
        gemini_role = 'user' if role == 'user' else 'model'
        contents.append(
            types.Content(role=gemini_role, parts=[types.Part.from_text(text)])
        )

    if file_object is not None and len(contents) > 0:
        last_user_content = contents[-1] 
        if file_object not in last_user_content.parts:
            # Tunahakikisha File Object inaongezwa kwenye content ya mwisho ya user
            last_user_content.parts.insert(0, file_object)
            contents[-1] = last_user_content 
        
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=contents,
        config=config
    )
    return response.text

def generate_final_ai_prompt(gemini_file):
    """Huzalisha Prompt ya mwisho ya AI kwa kutumia PDF iliyopakuliwa."""
    st.info("⚡ Inazalisha System Prompt ya mwisho ya AI kwa kutumia taarifa zote...")
    
    # Prompt Aura kutoa maelezo muhimu na kuzalisha Prompt
    analysis_prompt = (
        "Chambua kwa kina taarifa muhimu za biashara hii kutoka kwenye faili lililopakuliwa. "
        "Kisha, kwa kutumia taarifa hizo, **tengeneza System Prompt kamili (Final AI Prompt)** "
        "ambayo inaweza kutumiwa moja kwa moja kuendesha AI ya Huduma kwa Wateja. "
        "Prompt hii inapaswa kuwa fupi, kali, na ieleze JINA LA BIASHARA, ROLE YA AI, na MWELEKEO WA MAZUNGUMZO. "
        "Anza jibu lako na prompt hiyo kamili."
    )
    
    analysis_content = [
        types.Content(role="user", parts=[
            types.Part.from_text(analysis_prompt),
            gemini_file # Tuma faili kwa mara ya pili kwa ajili ya analysis ya mwisho
        ])
    ]

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=analysis_content
        )
        return response.text
    except Exception as e:
        st.error(f"Kosa la Kuzalisha Final Prompt: {e}")
        return "Imeshindwa kuzalisha Final Prompt."


# ----------------- STREAMLIT UI -----------------

st.set_page_config(page_title="Aura AI: Mjenzi wa AI", layout="wide")

# Angalia URL Parameter: Kama ni 'final_ai', onyesha AI pekee
query_params = st.query_params
if 'final_ai_mode' in query_params and query_params['final_ai_mode'] == 'true':
    st.session_state.app_state = 4
    if 'final_prompt' in query_params:
        # Pata final prompt kutoka kwenye URL (kwa usalama zaidi, tungefanya hivi tofauti)
        # Hapa tunarudisha prompt ya RAG kwa sababu hatuwezi hifadhi prompt ndefu kwenye URL
        st.session_state.current_prompt = RAG_PROMPT 
        st.title(f"🤖 AI Yako Iliyoundwa: {query_params.get('ai_name', 'Mchambuzi')}")
        st.subheader("Una chat na AI iliyoundwa kutokana na nyaraka za biashara yako.")
    
elif 'app_state' not in st.session_state:
    st.session_state.app_state = 1
    st.session_state.current_prompt = INTRO_PROMPT
    st.session_state.chat_title = "Aura - Msaidizi wa AI"
    st.session_state.intro_questions_count = 0
    st.title("✨ Aura AI: Jenga AI Yako Kutoka kwa Nyaraka")
    st.subheader("Utangulizi, Elimu, na Kujenga AI kwa Kutumia Nyaraka za Biashara.")


# Hali za Session (State Management)
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'gemini_file' not in st.session_state:
    st.session_state.gemini_file = None
if 'final_ai_prompt_text' not in st.session_state:
    st.session_state.final_ai_prompt_text = None


# --- KUANZISHA MAZUNGUMZO (INTRO GREETING) ---
if st.session_state.app_state == 1 and st.session_state.chat_history == []:
    intro_message = "Habari! Mimi naitwa **Aura**, na mimi ni msaidizi wako katika safari ya kujenga AI maalum kwa ajili ya biashara yako. Kwanza, unaweza kuniuliza maswali kuhusu **umuhimu wa kutumia AI** kwenye biashara yako."
    st.session_state.chat_history.append(("assistant", intro_message))


# ----------------------------------------------
# KIPENGELE KIKUU CHA CHAT
# ----------------------------------------------
st.markdown("---")
if st.session_state.app_state != 4:
    st.header(f"💬 Chat na {st.session_state.chat_title}")
else:
    st.header("💬 Anzisha Mazungumzo na AI Hii")

# 1. Onyesha Historia ya Chat
for role, text in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(text)


# 2. Kuingiza Ujumbe (Input)
if st.session_state.app_state in [1, 3, 4]: # Chat inawezekana kwenye state hizi
    user_prompt = st.chat_input("Tuma ujumbe kwa AI yako...")
    
    if user_prompt:
        
        # Onyesha ujumbe wa user mara moja
        with st.chat_message("user"):
            st.markdown(user_prompt)
        
        # Hifadhi ujumbe wa user kwenye historia kabla ya kutuma kwa Gemini
        st.session_state.chat_history.append(("user", user_prompt))
        
        # Tuma ujumbe kwa Gemini (Stateless Call)
        with st.spinner("AI inajibu..."):
            try:
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
                    
                    if st.session_state.intro_questions_count >= 3:
                        final_intro = (
                            "\n\n**Asante kwa maswali mazuri!** Sasa kwa kuwa umeelewa umuhimu wa AI, "
                            "tuanze kuijenga AI yako maalum. Tafadhali **pakia faili la taarifa za biashara yako** (PDF, DOCX, n.k.) hapo chini."
                        )
                        st.session_state.chat_history.append(("assistant", final_intro))
                        st.session_state.app_state = 2
                        
                elif st.session_state.app_state == 3:
                    # RAG inafanya kazi, baada ya maswali mawili, anza ujenzi wa AI
                    with st.chat_message("assistant"):
                        st.markdown(response_text)
                    st.session_state.chat_history.append(("assistant", response_text))

                    if len(st.session_state.chat_history) >= 10: # Baada ya jumla ya messages 5 za user na 5 za AI kwenye awamu ya 3
                        # Anza ujenzi wa AI
                        st.session_state.chat_history.append(("assistant", "Naona sasa nimechambua taarifa zako za msingi. Sasa naanza **kuzalisha AI Prompt yako ya mwisho!**"))
                        st.session_state.app_state = 5 # Nenda kwenye awamu ya Kuzalisha Link
                        st.rerun()

                elif st.session_state.app_state == 4:
                    # Hali ya AI iliyoundwa (Final AI Mode)
                    with st.chat_message("assistant"):
                        st.markdown(response_text)
                    st.session_state.chat_history.append(("assistant", response_text))
                    
            except Exception as e:
                st.error(f"🚨 Kosa la Gemini Chat: {e}. Tafadhali jaribu tena.")
                st.session_state.chat_history.pop()


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

    if uploaded_file is not None and st.session_state.gemini_file is None:
        st.session_state.gemini_file = upload_file_to_gemini(uploaded_file)
        
        if st.session_state.gemini_file:
            st.session_state.chat_title = uploaded_file.name + " (Mchambuzi)"
            st.session_state.current_prompt = RAG_PROMPT 
            
            pdf_intro = f"✅ Hongera! Faili **{uploaded_file.name}** limepakuliwa. Sasa unaweza **kuuliza maswali kuhusu taarifa zilizomo kwenye faili** ili kuhakikisha ninazielewa vizuri kabla ya ujenzi wa AI."
            st.session_state.chat_history.append(("assistant", pdf_intro))
            
            st.session_state.app_state = 3 
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
    # Jina la AI kwa ajili ya link
    ai_name = "AI ya Biashara Yako" 
    
    # Hii ndiyo link ya ukurasa huu, ikiwa na parameters
    base_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}" if os.getenv('RENDER_EXTERNAL_HOSTNAME') else "http://localhost:8501"
    
    # Tunatumia st.experimental_get_query_params ili kupata URL halisi, lakini kwa Render tunaweza tumia os.getenv
    # Kwa urahisi wa Streamlit, tunatumia URL ya sasa ya Streamlit
    try:
        # Jaribu kutumia URL ya sasa ya Streamlit
        current_url = st.runtime.get_instance().get_script_path()
        base_url = f"{current_url.split('?')[0]}"
    except Exception:
        pass # endelea na default URL

    ai_link = base_url + "?" + urllib.parse.urlencode({
        'final_ai_mode': 'true', 
        'ai_name': ai_name,
        # KUMBUKA: Hatuhifadhi prompt ndefu kwenye URL, tunatumia RAG mode pekee
    })

    st.markdown(f"""
    ## **AI YAKO IMEKAMILIKA!**
    
    Aura amemaliza kuchambua nyaraka zako na kuunda AI maalum. Unaweza kuitumia kuanzia sasa!
    
    **Link ya AI Yako Hii Hapa:**
    ### **[{ai_name}]({ai_link})**
    
    Bonyeza link hiyo ili kuona AI yako mpya ikifanya kazi! (Itakupeleka kwenye ukurasa wa chat pekee).
    """)
    st.session_state.app_state = 6 # Imekamilika
