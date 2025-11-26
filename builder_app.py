import os
import streamlit as st
from google import genai
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
from sqlalchemy.exc import OperationalError

# ----------------- CONFIGURATION -----------------
# Tumia SQLite (database rahisi ya faili moja)
# Hii inarekebisha matatizo ya psycopg2 na matatizo ya CORS.
SQLALCHEMY_DATABASE_URI = "sqlite:///ai_builder.db"

# Pata Gemini API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error("GEMINI_API_KEY haipatikani kwenye Environment Variables. Tafadhali weka 'GEMINI_API_KEY'.")
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
# Inatengeneza meza za DB (kama hazipo)
Base.metadata.create_all(engine) 
Session = sessionmaker(bind=engine)

# Initialize Gemini Client
try:
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    st.error(f"Imeshindwa kuunganisha Gemini Client: {e}")
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
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    return response.text

# ----------------- STREAMLIT UI -----------------

st.set_page_config(page_title="Aura AI Builder", layout="wide")

st.title("✨ Aura AI Builder - Jenga AI Yako Kirahisi")
st.subheader("Jaza fomu hapa chini ili kujenga AI persona ya biashara yako. Data inahifadhiwa ndani.")

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
    # Tumia jina rahisi lisilo la phone ili kuepuka ugumu na twilio
    contact_info = st.text_input("Taarifa za Mawasiliano (Mfano: Namba ya Simu au Email)", placeholder="07XXXXXXX au email@mfano.com")

    submit_button = st.form_submit_button("Jenga AI Yangu Sasa!")

if submit_button:
    # 1. Thibitisha data zote zipo
    if not all([business_name, business_field, ai_role, contact_info]):
        st.error("Tafadhali jaza sehemu zote zilizo wazi kabla ya kuendelea.")
    else:
        st.info("⚡ Inatengeneza AI Prompt kwa kutumia Gemini...")
        
        # Data ya kutuma
        form_data = {
            "business_name": business_name,
            "business_field": business_field,
            "ai_role": ai_role,
            "contact_info": contact_info
        }

        try:
            # 2. Piga simu Gemini
            generated_prompt = generate_ai_role_prompt(form_data)

            # 3. Hifadhi kwenye Database (FIX YA ATTRIBUTEERROR IPO HAPA)
            with Session() as session: 
                new_ai = AIBuilder(
                    business_name=business_name,
                    business_field=business_field,
                    ai_role=ai_role,
                    ai_prompt=generated_prompt
                )
                session.add(new_ai)
                session.commit()
                # Pata ID KABLA session haijafungwa
                saved_ai_id = new_ai.id  
                
            # 4. Onyesha Matokeo
            st.success("🎉 AI Builder imetengenezwa na kuhifadhiwa kwa mafanikio!")
            
            with st.expander("Ona AI Prompt Iliyotengenezwa na Gemini"):
                st.code(generated_prompt, language='markdown')

            st.markdown(f"""
            ---
            **Hatua Inayofuata:** Tumia prompt hii kuweka AI yako kwenye jukwaa la Gumzo (Chatbot) unalolipenda.
            **ID ya Database:** **#{saved_ai_id}**
            """)
            
        except Exception as e:
            st.error(f"🚨 Kosa la Kujenga/Kuhifadhi AI: {e}")
            st.stop()


# ----------------- DISPLAY SAVED AIS (FIX YA ATTRIBUTEERROR IPO HAPA) -----------------
st.sidebar.title("AI Zilizohifadhiwa")

try:
    # Tumia Session tofauti kwa ajili ya Sidebar
    with Session() as session:
        saved_ais = session.query(AIBuilder).order_by(AIBuilder.creation_date.desc()).all()

        if saved_ais:
            st.sidebar.info(f"AI {len(saved_ais)} zimehifadhiwa.")
            for ai in saved_ais:
                st.sidebar.markdown(f"**{ai.business_name}** ({ai.business_field})")
                st.sidebar.markdown(f"*Role:* {ai.ai_role[:30]}...")
                st.sidebar.markdown("---")
        else:
            st.sidebar.markdown("Bado hakuna AI zilizohifadhiwa.")
except Exception as e:
    # Hii inazuia Streamlit kuanguka
    st.sidebar.warning("Imeshindwa kuonyesha AI zilizohifadhiwa. DB error.")
