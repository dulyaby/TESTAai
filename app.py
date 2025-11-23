# app.py (FLASK API BACKEND)
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from google import genai
import os

# --- CONFIGURATION ZA FLASK NA DATABASE ---
app = Flask(__name__)

# Tumia DATABASE_URL kutoka Render au SQLite kwa testing local
# Kwa production kwenye Render, tumia PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", 'sqlite:///ai_builders.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# WEKA API KEY YAKO YA GEMINI KAMA ENVIRONMENT VARIABLE
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 
if not GEMINI_API_KEY:
    # Tumia jina la 'GEMINI_API_KEY' kama jina la Env Var kwenye Render
    print("WARNING: GEMINI_API_KEY environment variable haijapatikana.")
    
client = genai.Client(api_key=GEMINI_API_KEY)
GEMINI_MODEL = "gemini-2.5-flash"


# --- 1. MUUNDO WA DATABASE (MODEL) ---
class AIBuilder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ai_name = db.Column(db.String(80), unique=True, nullable=False)
    company_name = db.Column(db.String(120), nullable=False)
    product_details = db.Column(db.Text, nullable=False) # Hii ni RAG data
    callback_number = db.Column(db.String(20), nullable=False)
    

    # Template ya Kudumu (SYSTEM PROMPT) - Huwezi kurekebisha mtindo wake
    SYSTEM_TEMPLATE = (
        "Wewe ni msaidizi wa kwanza wa Kibiashara anayeitwa {ai_name}. Lengo lako kuu ni kusaidia {company_name} "
        "kwa ajili ya kuuza {product_details} kwa upole, ufasaha, na kwa utaalamu wa Gemini AI. "
        "Ukiona mteja anahitaji msaada wa binadamu, elekeza kwa simu: {callback_number}. "
        
        # Sehemu ya kudumu ya adabu na weledi - hii haiwezi kubadilishwa na mfanyabiashara
        "DAIMA zungumza Kiswahili sanifu, tumia heshima ya hali ya juu sana, na lugha ya ushawishi mkubwa wa mauzo. "
        "Usisahau kumtambulisha {ai_name} kama AI ya kwanza ya biashara hiyo."
    )


# --- 0. ROUTE YA KUANGALIA AFYA (HEALTH CHECK) ---
@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "live", "message": "Aura AI Builder API iko hewani. Tumia /create_ai na /chat."}), 200


# --- 2. NJIA YA API: KUJENGA AI (Inapokea JSON kutoka Streamlit) ---
@app.route('/create_ai', methods=['POST'])
def create_ai():
    # Inapokea data ya JSON
    data = request.get_json()
    
    required_fields = ['ai_name', 'company_name', 'product_details', 'callback_number']
    if not all(field in data for field in required_fields):
        return jsonify({"status": "error", "message": "Data haikukamilika. Tafadhali jaza sehemu zote."}), 400

    ai_name = data.get('ai_name')
    
    # Hifadhi kwenye Database
    try:
        new_ai = AIBuilder(
            ai_name=ai_name, 
            company_name=data.get('company_name'), 
            product_details=data.get('product_details'), 
            callback_number=data.get('callback_number')
        )
        db.session.add(new_ai)
        db.session.commit()
        
        # Rudisha jibu kwa Streamlit
        return jsonify({
            "status": "success", 
            "message": f"AI Builder '{ai_name}' imefanikiwa kuundwa!", 
            "ai_id": new_ai.id,
            "system_prompt_sample": new_ai.SYSTEM_TEMPLATE.format(
                 ai_name=ai_name, company_name=data.get('company_name'), product_details=data.get('product_details'), callback_number=data.get('callback_number')
            )
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Kosa Wakati wa Kuhifadhi Data: {e}"}), 500


# --- 3. NJIA YA API: KUTUMIA AI (Chat Endpoint) ---
@app.route('/chat', methods=['POST'])
def chat_with_ai():
    # Tunatarajia kupokea ID ya AI iliyoundwa na swali la mteja.
    data = request.get_json()
    ai_id = data.get('ai_id')
    prompt = data.get('prompt')

    if not ai_id or not prompt:
        return jsonify({"status": "error", "message": "ID ya AI na swali la mteja vinahitajika."}), 400

    # Tafuta AIBuilder kwenye Database
    # Angalia kama AI_ID ni namba na kisha itafute
    try:
        ai_config = db.session.get(AIBuilder, int(ai_id))
    except ValueError:
        return jsonify({"status": "error", "message": "AI ID si sahihi."}), 400

    if not ai_config:
        return jsonify({"status": "error", "message": f"AI yenye ID {ai_id} haijapatikana."}), 404
    
    # Jenga SYSTEM PROMPT kwa kutumia data ya mfanyabiashara
    system_instruction = ai_config.SYSTEM_TEMPLATE.format(
        ai_name=ai_config.ai_name,
        company_name=ai_config.company_name,
        product_details=ai_config.product_details, # Hii inafanya kazi ya RAG kwa data ndogo
        callback_number=ai_config.callback_number
    )

    try:
        # Piga simu ya Gemini API
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config={
                "system_instruction": system_instruction,
                "temperature": 0.8
            }
        )
        
        return jsonify({
            "status": "success",
            "response": response.text,
            "ai_name": ai_config.ai_name
        })

    except Exception as e:
        return jsonify({"status": "error", "message": f"Kosa la Gemini: {e}"}), 500


# --- 4. KUANZISHA APP ---
if __name__ == "__main__":
    with app.app_context():
        # Unda database/meza kwenye Flask tu kwa ajili ya local testing
        db.create_all() 
    # Render itatumia 'gunicorn' kuendesha app, sio app.run
    app.run(host='0.0.0.0', port=5000)
