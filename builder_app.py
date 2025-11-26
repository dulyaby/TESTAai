import os
import streamlit as st
# Imports za Gemini zilizorekebishwa
from google import genai
from google.genai import types 
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

# ----------------- CONFIGURATION -----------------
# Tumia SQLite (database rahisi ya faili moja)
SQLALCHEMY_DATABASE_URI = "sqlite:///ai_builder.db"

# Pata Gemini API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error("🚨 GEMINI_API_KEY haipatikani kwenye Environment Variables. Tafadhali weka 'GEMINI_API_KEY'.")
    st.stop()
    
# ----------------- DATABASE SETUP -----------------
Base = declarative_base()

class AIBuilder(Base):
    __tablename__ = 'aibuilder'
    id = Column(Integer, primary_key=True)
    business_name = Column(String(100), nullable=False)
    business_field = Column(String(100), nullable=False)
    ai_role = Column(String(255), nullable=False)
    ai_prompt = Column(Text, nullable=False)
    creation_date = Column(DateTime, default=datetime.datetime.now)

# Initialize Engine na Session
engine = create_engine(SQLALCHEMY_DATABASE_URI)
Base.metadata.create_all(engine) 
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Initialize Gemini Client
try:
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    st.error(f"🚨 Imeshindwa kuunganisha Gemini Client: {e}")
    st.stop()


# ----------------- HELPER FUNCTIONS -----------------
def generate_ai_role_prompt(data):
    """Hutengeneza AI System Prompt kwa kutumia Gemini"""
    prompt = (
        f"You are building an AI persona for a business named '{data['business_name']}' "
        f"which operates in the field of '{data['business_field']}'. "
        f"Your main role is: {data['ai_role']}. "
        f"The primary goal of this AI is to communicate with customers of a {data['business_field']} business."
        f"Generate a detailed system prompt for this AI that includes its persona, rules, and conversational tone."
    )
    
    # Huu ni mfumo wa kawaida, hauhitaji config ya mfumo
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    return response.text

# ----------------- STREAMLIT UI -----------------

st.set_page_config(page_title="Aura AI Builder", layout="wide")

st.title("✨ Aura AI Builder - Jenga AI Yako Kirahisi")
st.subheader("Jaza fomu hapa chini ili kujenga AI persona ya biashara yako. Data inahifadhiwa ndani.")

# Hii inasaidia kufanya refresh ya chat session
if 'chat_session' not in st.session_state:
    st.session_state.chat_session = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'selected_ai_prompt' not in st.session_state:
    st.session_state.selected_ai_prompt = None
if 'last_saved_name' not in st.session_state:
    st.session_state.last_saved_name = None

# --- KUJENGA FORM ---
with st.form("ai_builder_form"):
    st.markdown("### Taarifa za Biashara")
    col1, col2 = st.columns(2)
    business_name = col1.text_input("Jina la Biashara", placeholder="Mfano: Mwananchi Shop")
    business_field = col2.text_input("Eneo la Biashara (Field)", placeholder="Mfano: Ujenzi, Vyakula, Huduma za Kisheria")

    st.markdown("### Jukumu la AI (AI Role)")
    ai_role = st.text_area("Lengo Kuu la AI Hii", 
                            placeholder="Mfano: Kuwa msaidizi wa mauzo, Kujibu maswali ya wateja kuhusu bidhaa, Kuelekeza wateja kwa watu sahihi.", 
                            height=100)

    st.markdown("### Mawasiliano")
    contact_info = st.text_input("Taarifa za Mawasiliano (Mfano: Namba ya Simu au Email)", placeholder="07XXXXXXX au email@mfano.com")

    submit_button = st.form_submit_button("Jenga AI Yangu Sasa!")

if submit_button:
    if not all([business_name, business_field, ai_role, contact_info]):
        st.error("Tafadhali jaza sehemu zote zilizo wazi kabla ya kuendelea.")
    else:
        st.info("⚡ Inatengeneza AI Prompt kwa kutumia Gemini...")
        
        form_data = {
            "business_name": business_name,
            "business_field": business_field,
            "ai_role": ai_role,
            "contact_info": contact_info
        }

        saved_ai_id = None
        generated_prompt = None

        try:
            generated_prompt = generate_ai_role_prompt(form_data)

            with SessionLocal() as session: 
                new_ai = AIBuilder(
                    business_name=business_name,
                    business_field=business_field,
                    ai_role=ai_role,
                    ai_prompt=generated_prompt
                )
                session.add(new_ai)
                session.commit()
                saved_ai_id = new_ai.id  
                
            st.success("🎉 AI Builder imetengenezwa na kuhifadhiwa kwa mafanikio!")
            st.session_state.selected_ai_prompt = generated_prompt 
            st.session_state.chat_session = None 
            st.session_state.chat_history = [] 
            st.session_state.last_saved_name = f"ID #{saved_ai_id}: {business_name} ({ai_role[:20]}...)" 
            
            with st.expander("Ona AI Prompt Iliyotengenezwa na Gemini"):
                st.code(generated_prompt, language='markdown')

            st.markdown(f"""
            ---
            **ID ya Database:** **#{saved_ai_id}** | **Sasa nenda chini uanze mazungumzo naye.**
            """)
            
        except Exception as e:
            st.error(f"🚨 Kosa la Kujenga/Kuhifadhi AI: {e}")
            # Futa hali ya sasa ili Streamlit iendelee
            st.session_state.chat_session = None
            st.stop()


# ----------------------------------------------
# KIPENGELE KIKUU CHA KUJARIBU AI (TEST CHAT)
# ----------------------------------------------
st.markdown("---")
st.header("💬 Jaribu AI Yako Sasa")

# Pata orodha ya AI zilizohifadhiwa kwa ajili ya kuchagua
ai_options = {}
try:
    with SessionLocal() as session:
        saved_ais = session.query(AIBuilder).order_by(AIBuilder.creation_date.desc()).all()
        for ai in saved_ais:
            option_name = f"ID #{ai.id}: {ai.business_name} ({ai.ai_role[:30]}...)"
            ai_options[option_name] = ai.ai_prompt
except Exception:
    pass 

# 1. Selector ya AI
default_index = 0
if 'last_saved_name' in st.session_state and st.session_state.last_saved_name in ai_options:
    default_index = list(ai_options.keys()).index(st.session_state.last_saved_name)
elif len(ai_options) == 0:
    st.info("Tafadhali unda AI kwanza kwa kujaza fomu hapo juu ili kuanzisha mazungumzo.")

if len(ai_options) > 0:
    selected_ai_name = st.selectbox(
        "Chagua AI unayetaka kuchat naye:", 
        list(ai_options.keys()), 
        key='ai_selector',
        index=default_index
    )

    if selected_ai_name:
        selected_prompt = ai_options[selected_ai_name]
        
        # Kuanzisha Chat Session mpya na System Prompt
        if st.session_state.chat_session is None or st.session_state.selected_ai_prompt != selected_prompt:
            
            st.session_state.selected_ai_prompt = selected_prompt
            
            # --- HII NDIO SEHEMU ILIYOREKEBISHWA KWA AJILI YA SYSTEM INSTRUCTION ---
            
            # Unda Configuration kwa ajili ya System Instruction
            config = types.GenerateContentConfig(
                system_instruction=selected_prompt
            )
            
            # Anzisha Chat kwa kutumia config
            st.session_state.chat_session = client.chats.create(
                model='gemini-2.5-flash',
                config=config # Tunatuma configuration badala ya system_instruction moja kwa moja
            )
            
            st.session_state.chat_history = [] 
            st.info(f"Chat Session mpya imeanzishwa na AI: **{selected_ai_name}**")

        # 2. Onyesha Historia ya Chat
        for role, text in st.session_state.chat_history:
            with st.chat_message(role):
                st.markdown(text)

        # 3. Kuingiza Ujumbe (Input)
        user_prompt = st.chat_input("Tuma ujumbe kwa AI yako...")
        
        if user_prompt:
            # Onyesha ujumbe wa user
            with st.chat_message("user"):
                st.markdown(user_prompt)
            
            # Tuma ujumbe kwa Gemini
            try:
                # Hakikisha tumetumia chat session iliyoundwa vizuri
                response = st.session_state.chat_session.send_message(user_prompt)
                
                # Onyesha jibu la AI
                with st.chat_message("assistant"):
                    st.markdown(response.text)
                    
                # Hifadhi Historia
                st.session_state.chat_history.append(("user", user_prompt))
                st.session_state.chat_history.append(("assistant", response.text))
                
            except Exception as e:
                st.error(f"🚨 Kosa la Gemini Chat: {e}")
