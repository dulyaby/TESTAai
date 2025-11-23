# app.py (FLASK BACKEND NA DATABASE API)

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from google import genai
import os
from twilio.twiml.messaging_response import MessagingResponse

# --- CONFIGURATION ZA FLASK NA DATABASE ---
app = Flask(__name__)

# Tumia PostgreSQL kwa Render (Inapendekezwa kwa Production)
# Au tumia SQLite kwa testing: 'sqlite:///ai_builders.db'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", 'sqlite:///ai_builders.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# WEKA API KEY YAKO YA GEMINI HAPA AU KAMA ENV VAR
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "WEKA_API_KEY_YAKO_HAPA") 
client = genai.Client(api_key=GEMINI_API_KEY)

# Hifadhi ya Sessions (Inabaki hapa kwa ajili ya WhatsApp Logic baadaye)
chat_sessions = {}

# --- 1. MUUNDO WA DATABASE (MODEL) ---
class AIBuilder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ai_name = db.Column(db.String(80), unique=True, nullable=False)
    company_name = db.Column(db.String(120), nullable=False)
    product_details = db.Column(db.Text, nullable=False)
    callback_number = db.Column(db.String(20), nullable=False)
    
    # Template ya Kudumu (Sifa Kuu za Developer)
    SYSTEM_TEMPLATE = (
        "Wewe ni msaidizi wa kwanza wa Kibiashara anayeitwa {ai_name}. Lengo lako kuu ni kusaidia {company_name} "
        "kwa ajili ya kuuza {product_details} kwa upole, ufasaha, na kwa utaalamu wa Gemini AI. "
        "Ukiona mteja anahitaji msaada wa binadamu, elekeza kwa simu: {callback_number}. "
        # Sehemu ya kudumu ya adabu, ushawishi na weledi.
        "DAIMA zungumza Kiswahili sanifu, uliza jina la mteja, na tumia lugha ya ushawishi mkubwa wa mauzo. "
    )

# --- 2. NJIA YA API: KUJENGA AI (Inapokea JSON kutoka Streamlit) ---
@app.route('/create_ai', methods=['POST'])
def create_ai():
    # Inapokea data ya JSON
    data = request.get_json()
    
    if not data or 'ai_name' not in data:
        return jsonify({"status": "error", "message": "Data haikukamilika."}), 400

    ai_name = data.get('ai_name')
    company_name = data.get('company_name')
    product_details = data.get('product_details')
    callback_number = data.get('callback_number')
    
    # Hifadhi kwenye Database
    try:
        new_ai = AIBuilder(
            ai_name=ai_name, 
            company_name=company_name, 
            product_details=product_details, 
            callback_number=callback_number
        )
        db.session.add(new_ai)
        db.session.commit()
        
        # Rudisha jibu kwa Streamlit
        return jsonify({
            "status": "success", 
            "message": f"AI Builder '{ai_name}' imefanikiwa kuundwa!", 
            "ai_id": new_ai.id
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Kosa Wakati wa Kuhifadhi Data: {e}"}), 500

# --- 3. NJIA YA WHATSAPP (Imeachwa kwanza, inabaki kama placeholder) ---
@app.route("/webhook", methods=['POST'])
def webhook():
    # Logic ya WhatsApp itarekebishwa hapa baadaye ili kutumia AIBuilder Model.
    resp = MessagingResponse()
    resp.message("Mfumo wa AI Builder uko katika matengenezo, tafadhali tumia Builder App kujenga AI yako.")
    return str(resp)


if __name__ == "__main__":
    with app.app_context():
        # Unda database/meza kwenye Flask tu kwa ajili ya local testing
        db.create_all() 
    app.run(host='0.0.0.0', port=5000)
