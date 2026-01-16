import os
from dotenv import load_dotenv
import google.generativeai as genai

# 1. Load the environment variables
load_dotenv()

# 2. Configure the API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ Error: API Key not found in .env file.")
else:
    genai.configure(api_key=api_key)

    print("Fetching available models...\n")
    try:
        # 3. List all models
        for m in genai.list_models():
            # We are mostly interested in models that can generate content
            if 'generateContent' in m.supported_generation_methods:
                print(f"Model Name: {m.name}")
                print(f"Display Name: {m.display_name}")
                print(f"Methods: {m.supported_generation_methods}")
                print("-" * 30)
                
    except Exception as e:
        print(f"❌ Error fetching models: {e}")