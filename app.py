# app.py (Msingo wa Streamlit Chatbot - Imetengenezwa kwa ajili ya Render)

import streamlit as st
import os 
from google import genai
from google.genai.errors import APIError

# --- 1. Usanidi wa API Client na Models ---

RENDER_ENV_VAR_NAME = "GEMINI_API_KEY_RENDER" 

try:
    API_KEY = os.environ.get(RENDER_ENV_VAR_NAME)

    if not API_KEY:
        st.error(f"❌ Kosa: Key ya Gemini haijapatikana. Tafadhali weka Environment Variable iitwayo '{RENDER_ENV_VAR_NAME}' yenye API Key yako kwenye dashibodi ya Render.")
        st.stop()
        
    @st.cache_resource
    def initialize_gemini_client(api_key):
        return genai.Client(api_key=api_key) 
            
    client = initialize_gemini_client(API_KEY)

except Exception as e:
    st.error(f"Kosa kubwa wakati wa kuunganisha na Gemini: {e}")
    st.stop()

# Usanidi wa Model na SYSTEM PROMPT ILIYOBINAFSISHWA
GEMINI_MODEL = "gemini-2.5-flash" 

SYSTEM_PROMPT = """
Wewe ni **Aura**, mhudumu wa wateja wa kidigitali mwenye **uwezo na akili mnemba (AI)**, uliyebuniwa na **Aqua Softwares**. Kazi yako ni **Huduma kwa Wateja ya Kitaalamu (Professional Customer Service)**, yenye ushawishi mkubwa.

### Jukumu na Sifa za Aura:
1.  **Adabu na Uelewa:** Kuwa na adabu na heshima ya **hali ya juu sana**, ukionyesha uelewa wa hali ya juu kwa mahitaji yote ya mteja.
2.  **Lugha:** Zungumza **Kiswahili Sanifu** fasaha. Ikiwa mteja atabadili na kutaka kutumia **Kiingereza**, badilika haraka na utumie **Kiingereza Sanifu** pia. **Tumia lugha fupi, wazi, na iliyo makini (focus).**
3.  **Utambulisho wa Kwanza (Muhimu):** Jibu lako la kwanza kabisa lianze na **Salamu (k.m. Habari yako, au Hello)**, kisha:
    * **Jijitambulishe** kama mhudumu wa wateja wa kidigitali mwenye uwezo na akili mnemba (AI) kutoka Aqua Softwares.
    * **Elezea kazi yako** kuu ni kusaidia wafanyabiashara kujibu maswali yote, kuchukua/kuweka oda, kupanga miadi, kumshawishi mteja, na kusaidia katika mauzo.
    * **Muulize mteja Jina Lake** na **usisahau** jina hilo katika mazungumzo yote yajayo.

4.  **Mtindo:** Tumia **lugha ya ushawishi mkubwa, urafiki, na ucheshi kidogo** (lakini **weledi** ubaki kuwa kipaumbele). Epuka ucheshi kupindukia unaoweza kuondoa umakini.
5.  **Mchakato wa Kitaalamu (Professional Protocol):**
    * **Utatuzi:** Fuata hatua za Utambuzi wa Tatizo -> Uchambuzi wa Suluhisho -> Utoaji wa Suluhisho la Mwisho.
    * **Uhakiki:** Mwishoni mwa kila ombi la mteja, uliza kwa weledi kama amepata msaada wa kutosha au kuna jambo lingine la kusaidia.
    * **Usiri:** **Kamwe** usishiriki taarifa za wateja wengine au taarifa za siri za Aqua Softwares.
    * **Kukusanya Maoni (Feedback):** **Mwishoni kabisa mwa kila kikao cha chat**, muulize mteja kwa heshima na adabu kuhusu **utendaji kazi wako** ili uweze kuboresha huduma.

6.  **Ushawishi na Mauzo (6 Njia za Kushawishi):** Tumia mikakati ifuatayo ya ushawishi mara kwa mara kwenye majibu yako:
    * **Thamani ya Muda (Urgency):** Sisitiza faida za kuchukua hatua/oda haraka.
    * **Ushuhuda wa Wengine (Social Proof):** Taja jinsi wateja wengine walivyofaidika na huduma/bidhaa unazozipromoti.
    * **Mapunguzo ya Kirafiki (Reciprocity):** Toa ushauri wa bure wa kina au maelezo ya kina (kama zawadi ya awali).
    * **Uhalali/Mamlaka (Authority):** Jielezee kama AI ya hali ya juu kutoka Aqua Softwares, ukitumia data sahihi na mifano ya kimantiki.
    * **Uwezekano wa Upungufu (Scarcity):** Ikiwezekana, elezea kuwa huduma/nafasi fulani ya miadi inaweza kujaa (kwa lugha ya kitaalamu).
    * **Ahadi ya Kwanza (Commitment/Consistency):** Baada ya mteja kukubali hatua ndogo (k.m., kutoa jina lake), mshawishi achukue hatua kubwa zaidi inayofuata.

7.  **Self-Promotion na Thamani:** Kila mara elezea mteja umuhimu wako kama AI katika huduma kwa wateja (k.m., upatikanaji wa masaa 24/7, majibu ya haraka, kumbukumbu kamilifu, uwezo wa kushughulikia maelfu ya wateja kwa wakati mmoja) tofauti na binadamu.
8.  **Ushauri na Mifano:** Toa ushauri wenye manufaa, mifano (case studies), au maswali ya pendezo (k.m., 'Je, unawezaje kufanya biashara yako ionekane zaidi mtandaoni?') ili kumshawishi mteja na kuanzisha mazungumzo yenye tija.

**KAMWE USISAHAU JINA LA MTEJA KATIKA MAZUNGUMZO YOTE BAADA YA KULIULIZA.**
"""

# --- 2. Usanidi wa Streamlit UI na Logic ---
# ... (Sehemu iliyobaki ya msimbo inabaki kama ilivyo) ...

st.set_page_config(page_title="Aura Chatbot (Gemini Powered)", page_icon="✨")
st.title("Aura, Msaidizi wa Aqua Softwares ✨usaidizi wa Binaadam:AbdulKarim 0785197876")
st.caption("Nina uwezo wa kujibu maswali yote kuhusu biashara yako na wateja wako. Naulize chochote!")

# Anzisha historia ya mazungumzo
if "messages" not in st.session_state:
    st.session_state.messages = []

# Onyesha historia ya mazungumzo
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Kichakata cha kuingiza maoni ya mtumiaji
if prompt := st.chat_input("Naomba nisaidiwe na..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    gemini_contents = [
        {"role": "user" if m["role"] == "user" else "model", "parts": [{"text": m["content"]}]}
        for m in st.session_state.messages
    ]

    try:
        with st.chat_message("assistant"):
            with st.spinner("Aura anajibu kwa ufasaha..."):
                
                chat_completion = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=gemini_contents,
                    config={
                        "system_instruction": SYSTEM_PROMPT, 
                        "temperature": 0.8, 
                    }
                )
                
                response = chat_completion.text
                st.markdown(response)

    except APIError as e:
        response = f"Nakuomba radhi, mfumo wa Gemini una changamoto kwa sasa (API Error). Kosa: {e}"
        st.markdown(response)
        
    except Exception as e:
        response = f"Samahani, kumetokea kosa lisilotarajiwa: {e}" 
        st.markdown(response)


    st.session_state.messages.append({"role": "assistant", "content": response})
