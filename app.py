# app.py: Hii ni faili la kuhamisha tu

import streamlit as st
import subprocess

# Angalia kama URL ina parameters maalum zinazoonyesha Final AI Mode (State 4)
# Ikiwa URL ina 'final_ai_mode=true' inamaanisha tunataka kuanza hali ya AI iliyojengwa.
# Hata hivyo, kwa kuwa code yote ipo kwenye builder_app.py, tunatumia builder_app.py
# kufanya kazi zote.

try:
    # Hii inaita builder_app.py moja kwa moja kama script kuu
    # Inafanya builder_app.py iwe ndio app inayoonekana.
    # Tafadhali FUTA builder_app.py hapa, kisha weka code hapa chini.
    
    # Hii ni njia isiyo rasmi na inategemea jinsi Render inavyofanya kazi. 
    # Njia bora ni kuweka Streamlit Entry Point iwe builder_app.py.
    
    st.set_page_config(layout="wide")
    st.title("Redirecting to Builder...")
    st.markdown("Ikiwa programu haikuanza, tafadhali hakikisha **`builder_app.py`** ndio faili kuu la kuendesha.")
    
    # Njia bora zaidi: Hakikisha Render inajua kuendesha 'streamlit run builder_app.py'

except Exception as e:
    st.error(f"Kosa la kuunganisha: {e}")
