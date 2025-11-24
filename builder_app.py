# builder_app.py (STREAMLIT NO-CODE BUILDER)
import streamlit as st
import requests
import json
import os

# HII LAZIMA IWE ANWANI YA RENDER YA APP YAKO LIVE
# BADILISHA HII NA URL HALISI YA RENDER YA FLASK BACKEND YAKO
# HII INAWEZA KUWA TOFAUTI NA URL YA STREAMLIT YENYEWE
RENDER_API_URL = "https://testaai.onrender.com" # <--- BADILISHA HII
# Mfano: "https://your-flask-api.onrender.com"

st.set_page_config(page_title="Aura No-Code AI Builder", layout="centered")
st.title("🛠️ Aura No-Code AI Builder")
st.markdown("Jaza maelezo haya machache ili mfumo wetu wa Gemini ukutengenezee AI ya biashara yako. **Sifa za heshima/adabu ni za kudumu!**")


# Hii inatumika kuhifadhi AI ID iliyofanikiwa kuundwa
if 'latest_ai_id' not in st.session_state:
    st.session_state.latest_ai_id = None

# --- Fomu ya Kuunda AI ---
with st.form("ai_builder_form"):
    st.subheader("Maelezo ya Biashara Yako")
    ai_name = st.text_input("1. Jina la AI Yako (Mfano: Anna Bot):", max_chars=80)
    company_name = st.text_input("2. Jina la Kampuni/Biashara Yako:")
    # Hii ndio itatumika kama maarifa ya RAG
    product_details = st.text_area("3. Bidhaa au Huduma Zako (TAARIFA MUHIMU za FAQ na Bei):")
    callback_number = st.text_input("4. Namba ya Simu ya Kuelekeza Wateja (Mfano: 07XX XXX XXX):")
    
    submitted = st.form_submit_button("Jenga AI Yangu Sasa!")


if submitted:
    # 1. Kusanya data
    data = {
        "ai_name": ai_name,
        "company_name": company_name,
        "product_details": product_details,
        "callback_number": callback_number
    }

    # 2. Tuma data kama JSON kwa Render API
    try:
        st.info("⚡️ Tunatuma maombi kwenye server ya Render...")
        # Tumia /create_ai endpoint ya Flask API
        response = requests.post(f"{RENDER_API_URL}/create_ai", json=data) 
        
        if response.status_code == 201:
            st.balloons()
            st.success(f"🎉 Imefanikiwa! {response.json().get('message')} ID: {response.json().get('ai_id')}")
            # Hifadhi ID na SYSTEM PROMPT kwa ajili ya Testing
            st.session_state.latest_ai_id = response.json().get('ai_id')
            st.session_state.system_prompt = response.json().get('system_prompt_sample')
            st.markdown(f"**Mfumo Umefunzwa na Maelezo haya:**\n> {st.session_state.system_prompt}")

        else:
            st.error(f"❌ Kosa la Server: {response.status_code}. Angalia logs za Flask API.")
            st.json(response.json())
            st.session_state.latest_ai_id = None

    except requests.exceptions.RequestException as e:
        st.error(f"❌ Kosa la Muunganisho. Hakikisha URL ya Render API ({RENDER_API_URL}) ni sahihi na iko Online.")


# ----------------------------------------------------
# --- SEHEMU YA KUJARIBU AI YILIFANYA KAZI ---
# ----------------------------------------------------

if st.session_state.latest_ai_id:
    st.markdown("---")
    st.subheader(f"🗣️ Jaribu AI Yako Sasa (ID: {st.session_state.latest_ai_id})")
    
    test_prompt = st.text_input("Uliza swali lolote la biashara:", key="test_prompt")
    
    if st.button("Tuma Swali kwa AI"):
        if test_prompt:
            chat_url = f"{RENDER_API_URL}/chat"
            st.info("⚡️ AI yako mpya inajibu...")
            
            chat_data = {
                "ai_id": st.session_state.latest_ai_id,
                "prompt": test_prompt
            }
            
            try:
                chat_response = requests.post(chat_url, json=chat_data)
                
                if chat_response.status_code == 200:
                    ai_name = chat_response.json().get('ai_name')
                    response_text = chat_response.json().get('response')
                    st.success(f"**{ai_name} Anajibu:**")
                    st.markdown(response_text)
                else:
                    st.error(f"❌ Kosa la AI Chat: {chat_response.status_code}. Angalia logs za Flask API.")
                    st.json(chat_response.json())
                    
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Kosa la Muunganisho. Tafadhali hakikisha Flask API iko Live.")
