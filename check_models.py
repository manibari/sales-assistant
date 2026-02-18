"""
A diagnostic script to list all generative models available to the current API key
that support the 'generateContent' method.

This script helps debug issues where model names are not found (404 errors).

Instructions:
1. Make sure you have `google-generativeai` and `python-dotenv` installed
   (`pip install google-generativeai python-dotenv`).
2. Make sure your GOOGLE_API_KEY is set in the .env file.
3. Run this script from your terminal: `python check_models.py`
4. The script will print a list of model names that you can use.
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

def check_available_models():
    """
    Lists available generative models that support 'generateContent'.
    """
    try:
        load_dotenv()
        if not os.getenv("GOOGLE_API_KEY"):
            print("🔴 ERROR: GOOGLE_API_KEY environment variable not found.")
            print("Please create a .env file in the project root and add the following line:")
            print('GOOGLE_API_KEY="YOUR_API_KEY_HERE"')
            return

        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

        print("🔍 Searching for available models for your API key...")
        print("-" * 50)

        available_models = []
        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                available_models.append(model.name)

        if not available_models:
            print("🔴 No models supporting 'generateContent' found for your API key.")
            print("Please check the following in your Google Cloud Console:")
            print("1. Ensure the 'Generative Language API' or 'Vertex AI API' is enabled.")
            print("2. Ensure your API key has the correct permissions.")
        else:
            print("✅ Success! Found the following usable models:")
            for model_name in available_models:
                print(f"  - {model_name}")
            print("-" * 50)
            print("📋 Please copy one of the model names from the list above and provide it to me.")

    except Exception as e:
        print(f"🔴 An unexpected error occurred: {e}")
        print("This might be due to an invalid API key or network issues.")

if __name__ == "__main__":
    check_available_models()
