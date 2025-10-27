import os
from dotenv import load_dotenv

def load_config():
    """Load configuration from environment variables"""
    load_dotenv()
    
    config = {
        'taapi_api_key': os.getenv('TAAPI_API_KEY'),
        'llm_api_key': os.getenv('LLM_API_KEY'),
        'llm_model': os.getenv('LLM_MODEL', 'openai/gpt-3.5-turbo'),  # Default to OpenAI, but allow other models
        'llm_base_url': os.getenv('LLM_BASE_URL'),  # For local models like Ollama
        'simulation_mode': os.getenv('SIMULATION_MODE', 'true').lower() == 'true',
        'starting_funds': float(os.getenv('STARTING_FUNDS', '1000.0')),
        'risk_per_trade': float(os.getenv('RISK_PER_TRADE', '0.02')),  # 2% risk per trade
    }
    
    return config