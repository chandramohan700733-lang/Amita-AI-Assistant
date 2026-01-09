import google.generativeai as genai

# ==========================================
# 🔴 APNI API KEY YAHAN PASTE KAREIN
# ==========================================
MY_SECRET_KEY = "AIzaSyB_UzNHUCG2ubBqUYui5BvxuI0TXzarrLY" 

genai.configure(api_key=MY_SECRET_KEY)

print("\n🔍 Checking Available Models for you...\n")

try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ Available: {m.name}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n-----------------------------------\n")