import os
import json
from flask import Flask, jsonify, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS  # MPYA: Kuondoa Kosa la 403
from google import genai
from sqlalchemy.exc import OperationalError

# ----------------- CONFIGURATION -----------------
# Pata URL ya Database kutoka Environment Variable
# Render inajaza DATABASE_URL kiotomatiki
database_url = os.getenv("DATABASE_URL")
if not database_url:
    # Tumia SQLite kwa local testing au kama mbadala
    SQLALCHEMY_DATABASE_URI = "sqlite:///ai_builder.db"
else:
    # Kwa Render, inabidi ubadilishe 'postgresql' kwenda 'postgresql+psycopg2'
    # kwa sababu ya matumizi ya psycopg2-binary
    SQLALCHEMY_DATABASE_URI = database_url.replace("postgres://", "postgresql+psycopg2://")
    
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ----------------- FLASK APP INITIALIZATION -----------------
app = Flask(__name__)
# MPYA: Huu mstari unaruhusu maombi ya POST/GET kutoka Streamlit UI (Frontend)
# Hii ndiyo inarekebisha kosa la 403 Forbidden
CORS(app) 
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ----------------- EXTENSIONS & CLIENTS -----------------
db = SQLAlchemy(app)

if not GEMINI_API_KEY:
    # Tupa kosa ikiwa key haipo, inazuia app kuanza bila API key
    raise ValueError("GEMINI_API_KEY environment variable not set.")

try:
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    # Tupa kosa ikiwa key haifanyi kazi vizuri
    raise Exception(f"Failed to initialize Gemini Client: {e}")

# ----------------- DATABASE MODEL -----------------
class AIBuilder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(100), nullable=False)
    business_field = db.Column(db.String(100), nullable=False)
    ai_role = db.Column(db.String(255), nullable=False)
    ai_prompt = db.Column(db.Text, nullable=False)
    creation_date = db.Column(db.DateTime, default=db.func.now())

# ----------------- HELPER FUNCTIONS -----------------
def generate_ai_role_prompt(data):
    # Logic ya kuunda prompt kwa kutumia Gemini
    # ... (Acha logic yako ya zamani hapa, nitaweka mfano mfupi tu)
    prompt = (
        f"You are building an AI persona for a business named '{data.get('business_name')}' "
        f"which operates in the field of '{data.get('business_field')}'. "
        f"Your main role is: {data.get('ai_role')}. "
        "Generate a detailed system prompt for this AI."
    )
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    return response.text

# ----------------- ROUTES -----------------

# 1. Health Check (Kuthibitisha API Iko Live)
@app.route('/health_check', methods=['GET'])
def health_check():
    return jsonify({
        "status": "live", 
        "message": "Aura AI Builder API iko hewani. Tumia /create_ai na /chat."
    }), 200

# 2. Create AI (POST request)
@app.route('/create_ai', methods=['POST'])
def create_ai():
    if not request.json:
        abort(400, description="Payload must be JSON")

    data = request.json
    required_fields = ['business_name', 'business_field', 'ai_role']
    for field in required_fields:
        if field not in data:
            abort(400, description=f"Missing required field: {field}")

    # Tengeneza Prompt na Gemini
    try:
        generated_prompt = generate_ai_role_prompt(data)
    except Exception as e:
        app.logger.error(f"Gemini generation failed: {e}")
        return jsonify({"message": "Gemini generation failed", "details": str(e)}), 500

    # Hifadhi kwenye Database
    new_ai = AIBuilder(
        business_name=data['business_name'],
        business_field=data['business_field'],
        ai_role=data['ai_role'],
        ai_prompt=generated_prompt
    )

    try:
        db.session.add(new_ai)
        db.session.commit()
    except OperationalError as e:
        app.logger.error(f"Database error: {e}")
        db.session.rollback()
        return jsonify({"message": "Database operation failed. Check logs.", "details": str(e)}), 500
    except Exception as e:
        app.logger.error(f"Failed to commit to DB: {e}")
        db.session.rollback()
        return jsonify({"message": "Server error while saving AI", "details": str(e)}), 500


    return jsonify({
        "message": "AI Builder amehifadhiwa kwa mafanikio!",
        "id": new_ai.id,
        "ai_prompt": generated_prompt
    }), 201

# ----------------- RUN APP -----------------
with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        # Hii ni muhimu kwa debug kwenye Render
        app.logger.error(f"Failed to create database tables: {e}")
        
if __name__ == '__main__':
    app.run(debug=True)
