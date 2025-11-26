import os
import streamlit as st
from google import genai
from google.genai import types 
from io import BytesIO

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
# Prompt ya Awamu ya Utangulizi (Aura)
INTRO_PROMPT = (
    "Wewe ni AI inayoitwa 'Aura', msaidizi wa kujenga AI za biashara. "
    "Jukumu lako kuu ni kumwelekeza mfanyabiashara umuhimu wa kujenga AI yake binafsi, "
    "kwa kutumia nyaraka zake za biashara. Ongea kwa Kiswahili fasaha, uwe na adabu, "
    "na mtaalamu. Jibu maswali yanayohusu faida za AI kwa biashara ndogo na za kati. "
    "Baada ya kujibu maswali mawili au matatu, au mtumiaji anapoelewa, unapaswa kumwomba "
    "apakie nyaraka zake za biashara (PDF, DOCX, n.k.) ili kuendelea na awamu ya ujenzi wa AI."
)

# Prompt ya Awamu ya Kuchambua Nyaraka (PDF RAG)
RAG_PROMPT = (
    "Wewe ni Mchambuzi Maalum wa Taarifa za Biashara. "
    "Jukumu lako ni kujibu maswali yote yanayohusu biashara ya mteja KWA KUTUMIA PEKEE "
    "taarifa zilizomo kwenye nyaraka zilizopakuliwa (PDF, n.k.). "
    "Kama taarifa haipatikani kwenye nyaraka, sema kwa adabu, 'Taarifa hiyo haipatikani kwenye nyaraka zilizopakuliwa.' "
    "Dumisha sauti ya mtaalamu na jibu kwa Kiswahili isipokuwa uombwe vingine."
)

# ----------------- HELPER FUNCTIONS (PDF) -----------------

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
    """
    Hutuma ombi la stateless kwa Gemini ikiwa na historia na File Object (kama inahitajika).
    """
    
    # Kuanzisha configuration yenye system instruction
    config = types.GenerateContentConfig(
        system_instruction=current_prompt
    )

    # Kuandaa historia ya mazungumzo kwa ajili ya Gemini
    contents = []
    
    for role, text in history:
        gemini_role = 'user' if role == 'user' else 'model'
        contents.append(
            types.Content(role=gemini_role, parts=[types.Part.from_text(text)])
        )

    # Ikiwa kuna faili, ongeza faili kwenye content ya mwisho ya user
    if file_object is not None and len(contents) > 0:
        last_user_content = contents[-1] 
        # Ongeza File Object kwenye parts za content ya mwisho ya user
        # Inatumika kwa RAG (PDF Analysis)
        if file_object not in last_user_content.parts:
            last_user_content.parts.insert(0, file_object)
            contents[-1] = last_user_content 
        
    
    # Piga simu ya generate_content
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=contents,
        config=config
    )
    return response.text


# ----------------- STREAMLIT UI -----------------

st.set_page_config(page_title="Aura AI Builder", layout="wide")

st.title("✨ Aura AI: Jenga AI Yako Kutoka kwa PDF")
st.subheader("Utangulizi, Elimu, na Kujenga AI kwa Kutumia Nyaraka za Biashara.")

# ----------------- HALI ZA SESSION (STATE MANAGEMENT) -----------------
# app_state: 1 = Utangulizi, 2 = PDF Uploader, 3 = PDF Chat
if 'app_state' not in st.session_state:
    st.session_state.app_state = 1
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'gemini_file' not in st.session_state:
    st.session_state.gemini_file = None
if 'current_prompt' not in st.session_state:
    st.session_state.current_prompt = INTRO_PROMPT
if 'chat_title' not in st.session_state:
    st.session_state.chat_title = "Aura - Msaidizi wa AI"
if 'intro_questions_count' not in st.session_state:
    st.session_state.intro_questions_count = 0


# --- KUANZISHA MAZUNGUMZO (INTRO GREETING) ---
if st.session_state.app_state == 1 and st.session_state.chat_history == []:
    intro_message = "Habari! Mimi naitwa **Aura**, na mimi ni msaidizi wako katika safari ya kujenga AI maalum kwa ajili ya biashara yako. Jukumu langu ni kukupitisha hatua kwa hatua. Kwanza, unaweza kuniuliza maswali kuhusu **umuhimu wa kutumia AI** kwenye biashara yako."
    st.session_state.chat_history.append(("assistant", intro_message))


# ----------------------------------------------
# KIPENGELE KIKUU CHA CHAT
# ----------------------------------------------
st.markdown("---")
st.header(f"💬 Chat na {st.session_state.chat_title}")

# 1. Onyesha Historia ya Chat
for role, text in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(text)

# 2. Kuingiza Ujumbe (Input)
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
            # Tuma ombi kwa Gemini
            response_text = get_gemini_response(
                st.session_state.current_prompt,
                st.session_state.gemini_file,
                st.session_state.chat_history
            )
            
            # ----------------- LOGIC YA KUFUATA HATUA -----------------
            if st.session_state.app_state == 1:
                st.session_state.intro_questions_count += 1
                
                # Jibu la Aura
                with st.chat_message("assistant"):
                    st.markdown(response_text)
                    
                st.session_state.chat_history.append(("assistant", response_text))
                
                # Baada ya maswali 3, nenda kwenye awamu ya PDF
                if st.session_state.intro_questions_count >= 3:
                    final_intro = (
                        "\n\n**Asante kwa maswali mazuri!** Sasa kwa kuwa umeelewa umuhimu wa AI, "
                        "tuanze kuijenga AI yako maalum. Tafadhali **pakia faili la taarifa za biashara yako** (PDF, DOCX, n.k.) hapo chini. "
                        "Hili litaifunza AI yako kujibu maswali kulingana na nyaraka zako."
                    )
                    st.session_state.chat_history.append(("assistant", final_intro))
                    st.session_state.app_state = 2 # Nenda kwenye awamu ya PDF Uploader
                    
            elif st.session_state.app_state == 3:
                 # Jibu la RAG (PDF Analysis)
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
        # Faili jipya limepakuliwa, pakia kwa Gemini
        st.session_state.gemini_file = upload_file_to_gemini(uploaded_file)
        
        if st.session_state.gemini_file:
            st.session_state.chat_title = uploaded_file.name + " (Mchambuzi)"
            st.session_state.current_prompt = RAG_PROMPT # Badili prompt kuwa ya PDF Analysis
            
            # Tuma ujumbe wa utangulizi wa awamu ya PDF
            pdf_intro = f"✅ Hongera! Faili **{uploaded_file.name}** limepakuliwa na AI iko tayari kulichambua. Sasa unaweza **kuuliza maswali yote kuhusu taarifa zilizomo kwenye faili** hili hapa chini."
            st.session_state.chat_history.append(("assistant", pdf_intro))
            
            st.session_state.app_state = 3 # Nenda kwenye awamu ya Chat ya PDF
            st.rerun() # Fanya refresh ili kuonyesha chat interface mpya

# ----------------- KUFUNGA FAILII (CLEANUP) -----------------
# Hii ni muhimu kuhakikisha faili inafutwa kwenye Gemini API
# Unaweza kuweka kitufe hiki kwenye sidebar au chini
# def delete_file_on_session_end():
#     if st.session_state.gemini_file:
#         try:
#             client.files.delete(name=st.session_state.gemini_file.name)
#             st.session_state.gemini_file = None
#             st.session_state.app_state = 1
#             st.session_state.chat_history = []
#             st.success("Faili limefutwa na mfumo umerudi mwanzo.")
#             st.rerun()
#         except Exception as e:
#             st.error(f"Kosa la kufuta faili: {e}")

# st.sidebar.button("Funga Chat na Futa Faili", on_click=delete_file_on_session_end)
