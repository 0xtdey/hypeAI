import random
import time
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_loader import load_config

# Global variables to track simulation state
simulation_state = {
    'portfolio_value': 1000.0,
    'positions': {},
    'trade_history': [],
    'initialized': False
}

def initialize_simulation(starting_funds=None):
    """Initialize the simulation environment"""
    global simulation_state
    
    if starting_funds is not None:
        simulation_state['portfolio_value'] = starting_funds
    else:
        config = load_config()
        simulation_state['portfolio_value'] = config['starting_funds']
    
    simulation_state['positions'] = {}
    simulation_state['trade_history'] = []
    simulation_state['initialized'] = True
    
    print(f"Simulation initialized with ${simulation_state['portfolio_value']:.2f}")

def get_portfolio_value():
    """Get the current simulated portfolio value"""
    return simulation_state['portfolio_value']

def execute_trade_simulation(asset, decision):
    """
    Execute a simulated trade based on the AI decision
    """
    global simulation_state
    
    if not simulation_state['initialized']:
        initialize_simulation()
    
    # Record initial state
    initial_portfolio = simulation_state['portfolio_value']
    
    # Simulate trade execution based on decision
    if decision.lower() in ['buy', 'long']:
        # Simulate buying: increase portfolio value based on market movement
        profit_factor = random.uniform(0.98, 1.03)  # -2% to +3% change
        simulation_state['portfolio_value'] *= profit_factor
        
    elif decision.lower() in ['sell', 'short']:
        # Simulate selling: portfolio changes based on market movement
        profit_factor = random.uniform(0.97, 1.02)  # -3% to +2% change
        simulation_state['portfolio_value'] *= profit_factor
        
    elif decision.lower() == 'hold':
        # Hold position: minimal change
        profit_factor = random.uniform(0.995, 1.005)  # -0.5% to +0.5% change
        simulation_state['portfolio_value'] *= profit_factor
    else:
        # Unknown decision, minimal change
        profit_factor = random.uniform(0.998, 1.002)  # -0.2% to +0.2% change
        simulation_state['portfolio_value'] *= profit_factor
    
    # Calculate PnL
    pnl = simulation_state['portfolio_value'] - initial_portfolio
    pnl_percentage = (pnl / initial_portfolio) * 100
    
    # Create trade record
    trade_record = {
        'timestamp': datetime.now().isoformat(),
        'asset': asset,
        'decision': decision,
        'initial_portfolio': initial_portfolio,
        'final_portfolio': simulation_state['portfolio_value'],
        'pnl': pnl,
        'pnl_percentage': pnl_percentage
    }
    
    simulation_state['trade_history'].append(trade_record)
    
    result = {
        'status': 'success',
        'executed_decision': decision,
        'initial_portfolio': initial_portfolio,
        'final_portfolio': simulation_state['portfolio_value'],
        'pnl': pnl,
        'pnl_percentage': pnl_percentage,
        'timestamp': trade_record['timestamp']
    }
    
    return result

def get_position(asset):
    """Get the current position for an asset"""
    return simulation_state['positions'].get(asset, {'size': 0, 'entry_price': 0})

def get_trade_history():
    """Get the history of all trades"""
    return simulation_state['trade_history']