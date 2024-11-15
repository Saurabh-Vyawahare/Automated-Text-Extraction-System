# generate_response.py
import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAI API key from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Configure OpenAI client
openai.api_key = OPENAI_API_KEY

def ask_chatgpt(summary, question):
    """Send a question along with the context summary to ChatGPT and get the response."""
    try:
        # Formulate the prompt
        prompt = f"Context: {summary}\n\nQuestion: {question}"
        
        # Use the new ChatCompletion interface for ChatGPT-like responses
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Specify the model to use (e.g., gpt-3.5-turbo)
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )
        
        # Extract and return the assistant's message
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Error in generating response:\n\n{e}"
