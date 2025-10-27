import os
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_loader import load_config
import openai
from datetime import datetime

def make_trading_decision(asset, indicators, portfolio_value):
    """
    Use AI to make a trading decision based on technical indicators and portfolio state
    Supports both OpenAI-compatible APIs and open source models
    """
    config = load_config()
    
    # Prepare the prompt for the LLM
    prompt = f"""
    You are an expert trading bot. Based on the following market data, make a trading decision.
    
    Current asset: {asset}
    Portfolio value: ${portfolio_value:,.2f}
    Current indicators:
    - RSI: {indicators['rsi']}
    - MACD value: {indicators['macd']['value']}
    - MACD signal: {indicators['macd']['signal']}
    - EMA: {indicators['ema']}
    - SMA: {indicators['sma']}
    - Bollinger Bands: Upper {indicators['bollinger_bands']['upper']}, 
                       Middle {indicators['bollinger_bands']['middle']}, 
                       Lower {indicators['bollinger_bands']['lower']}
    
    Current time: {datetime.now().isoformat()}
    
    Please respond with ONLY ONE of these three words:
    1. "BUY" - if the indicators suggest going long
    2. "SELL" - if the indicators suggest going short
    3. "HOLD" - if the indicators suggest maintaining current position or being neutral
    
    Be concise and only respond with the single word decision.
    """
    
    # Configure the LLM client
    if config['llm_base_url']:
        # Using a local model or OpenAI-compatible API (like Ollama) or OpenRouter
        client = openai.OpenAI(
            base_url=config['llm_base_url'],
            api_key=config['llm_api_key']
        )
    else:
        # Using a standard OpenAI-compatible API
        client = openai.OpenAI(
            base_url=config.get('llm_base_url', 'https://api.openai.com/v1'),
            api_key=config['llm_api_key']
        )
    
    try:
        response = client.chat.completions.create(
            model=config['llm_model'],
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
            temperature=0.1  # Low temperature for more consistent decisions
        )
        
        decision = response.choices[0].message.content.strip().upper()
        
        # Validate the decision
        if decision in ['BUY', 'SELL', 'HOLD', 'LONG', 'SHORT']:
            if decision == 'LONG':
                decision = 'BUY'
            elif decision == 'SHORT':
                decision = 'SELL'
            return decision
        else:
            # Fallback to HOLD if the response is not one of the expected values
            return 'HOLD'
            
    except Exception as e:
        print(f"Error getting AI decision: {e}")
        # Fallback to a simple heuristic if AI fails
        return simple_technical_decision(indicators)


def simple_technical_decision(indicators):
    """
    Fallback simple decision based on technical indicators
    """
    rsi = indicators['rsi']
    
    if rsi < 30:  # Oversold
        return 'BUY'
    elif rsi > 70:  # Overbought
        return 'SELL'
    else:  # Neutral
        return 'HOLD'