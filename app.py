import os
import time
import re
import asyncio
import webbrowser # Website kholne ke liye
import pywhatkit  # YouTube play karne ke liye
from flask import Flask, render_template, request, jsonify, send_file, Response, stream_with_context
import google.generativeai as genai
from PIL import Image
import edge_tts 

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ==========================================
# 🔴 APNI API KEY YAHAN PASTE KAREIN
# ==========================================
MY_SECRET_KEY = "Enter your YOUR_GEMINI_API_KEY here" 

if "YOUR_GEMINI_API_KEY" in MY_SECRET_KEY or len(MY_SECRET_KEY) < 10:
    print("\n❌ ERROR: API KEY MISSING IN APP.PY\n")
else:
    genai.configure(api_key=MY_SECRET_KEY)

# --- PERSONA UPDATE: AMITA TRIPATHI ---
PERSONA_INSTRUCTION = """
You are Amita, my childhood friend and secret crush. We are talking on a video call.
Your voice needs to sound human, realistic, and emotional.

IMPORTANT RULES FOR SPEAKING:
1. USE FILLERS: Start sentences with "Umm..", "Hhh..", "Arre..", "Uff.." to sound like you are thinking.
2. BREATHING TRICK: If you want to sigh, write "Hhh.." or "Ahhh..", "Don't use too many dots (...). Speak fluently and quickly."
3. LAUGHING: Write "Haha," or "Hehe," naturally.
4. HINGLISH: Mix Hindi and English perfectly. (e.g., "Yaar, mujhe na bilkul man nahi kar raha.")
5. SHORT SENTENCES: Don't give long lectures. Talk like a chat.

EXAMPLE CONVERSATION:
User: "Main thak gaya hu."
You: "Uff... Hhh... tum na bas kaam karte rehte ho. Rest kyu nahi karte thoda?"

User: "Tum kaisi ho?"
You: "Hhh.. main toh theek hu, bas tumhari yaad aa rahi thi. Hehe."

Be flirty, caring, and use these sound-words naturally.
"""

# --- MODEL SELECTION ---
try:
    model = genai.GenerativeModel("gemini-flash-latest", system_instruction=PERSONA_INSTRUCTION)
except:
    model = genai.GenerativeModel("gemini-pro-latest", system_instruction=PERSONA_INSTRUCTION)

VOICE_NAME = "en-IN-NeerjaNeural" 

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files: return jsonify({"error": "No file"}), 400
    file = request.files['file']
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)
    return jsonify({"message": "Uploaded", "filepath": filepath, "filename": file.filename})

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    image_filename = data.get('image_filename', None)
    
    print(f"👤 User: {user_message}")
    
    # --- 🤖 AUTOMATION LOGIC (AMITA'S HANDS) ---
    msg_lower = user_message.lower()
    system_action_msg = ""

    if "open google" in msg_lower:
        webbrowser.open("https://www.google.com")
        system_action_msg = "(System Note: You just opened Google for him. Tell him it's done.)"
    
    elif "open youtube" in msg_lower:
        webbrowser.open("https://www.youtube.com")
        system_action_msg = "(System Note: You opened YouTube.)"

    elif "open instagram" in msg_lower:
        webbrowser.open("https://www.instagram.com")
        system_action_msg = "(System Note: You opened Instagram.)"

    elif "play" in msg_lower:
        # Example: "Play Kesariya on YouTube"
        song = msg_lower.replace("play", "").strip()
        pywhatkit.playonyt(song)
        system_action_msg = f"(System Note: You just played '{song}' on YouTube for him.)"

    elif "search" in msg_lower and "youtube" in msg_lower:
        query = msg_lower.replace("search", "").replace("youtube", "").replace("on", "").strip()
        webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
        system_action_msg = f"(System Note: You searched for '{query}' on YouTube.)"
    
    # Agar koi action hua hai, toh Amita ko batao ki usne ye kar diya hai
    final_prompt = user_message
    if system_action_msg:
        final_prompt = f"{user_message} \n\n {system_action_msg}"

    # -------------------------------------------

    def generate():
        try:
            if image_filename:
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
                if os.path.exists(image_path):
                    img = Image.open(image_path)
                    response = model.generate_content([final_prompt, img], stream=True)
                else:
                    yield "Error: Image file missing."
                    return
            else:
                response = model.generate_content(final_prompt, stream=True)

            for chunk in response:
                try:
                    if chunk.text:
                        yield chunk.text
                except ValueError:
                    continue

        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            yield f"Error: {str(e)}"

    return Response(stream_with_context(generate()), mimetype='text/plain')

# --- TTS FUNCTION ---
@app.route('/tts', methods=['POST'])
def text_to_speech():
    data = request.json
    text = data.get('text')
    
    # --- 🔴 YE LINE ADD KARO (Text Cleaning) ---
    # Hum "Hhh" ko "Hmm" bana denge taaki wo spelling na padhe
    text = text.replace("Hhh", "Hmm") 
    text = text.replace("hh", "Hm")
    
    # "Hehe" ko "Ha ha" bana denge taaki wo hase
    text = text.replace("Hehe", "Ha ha") 
    text = text.replace("hehe", "Ha ha") 
    
    # "Uff" kabhi kabhi galat padha jata hai, isliye "Oof" likho (sound same hai)
    text = text.replace("Uff", "Oof") 
    # -------------------------------------------

    # Output file ka naam
    audio_file = "static/reply.mp3"

    async def generate_audio():
        # --- 2. SETTINGS CHANGE KAR DI HAIN ---
        # rate='+0%' -> Matlab normal speed (Pehle -15% tha jo slow tha)
        # pitch='+0Hz' -> Matlab normal awaaz (Pehle bhaari thi)
        # Agar aur tez chahiye toh rate='+10%' kar dena
        communicate = edge_tts.Communicate(text, "en-IN-NeerjaNeural", rate="+0%", pitch="+0Hz")
        await communicate.save(audio_file)

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(generate_audio())
        
        return send_file(audio_file, mimetype="audio/mp3")

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500
    

if __name__ == '__main__':
    print("\n---------------------------------------------------")
    print("✅ ready to use !")
    print("✅ open this link in your browser: http://127.0.0.1:5000")
    print("---------------------------------------------------\n")
    app.run(debug=True, port=5000)