import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    CHATBOT_DATA_PATH = os.path.join(os.path.dirname(__file__), "Chatbot.md")
    
    MODEL_NAME = "openai/gpt-4o-mini" 
    TEMPERATURE = 0.3
    
    LEADS_FILE = "leads.json"

config = Config()
