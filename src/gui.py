import streamlit as st
import pandas as pd
import plotly.express as px
import json
from datetime import datetime
import os

st.title("AI Trading Agent - Portfolio Performance Dashboard")

# Load trade history from log file
def load_trade_history():
    if not os.path.exists('trades_log.jsonl'):
        return pd.DataFrame()
    
    trades = []
    with open('trades_log.jsonl', 'r') as f:
        for line in f:
            try:
                trade = json.loads(line.strip())
                trades.append(trade)
            except:
                continue  # Skip malformed lines
                
    if not trades:
        return pd.DataFrame()
    
    df = pd.DataFrame(trades)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    
    # Calculate cumulative portfolio value
    df['cumulative_portfolio'] = df['portfolio_value'].expanding().max()
    
    return df

# Load the trade history
df = load_trade_history()

if df.empty:
    st.warning("No trade data available. Please run the trading agent to generate data.")
else:
    # Create the main portfolio value chart
    st.subheader("Portfolio Value Over Time")
    
    fig = px.line(df, x='timestamp', y='portfolio_value', 
                 title='Simulated Portfolio Value Over Time',
                 labels={'portfolio_value': 'Portfolio Value ($)', 'timestamp': 'Time'})
    
    fig.update_layout(
        xaxis_title='Time',
        yaxis_title='Portfolio Value ($)',
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show latest portfolio value
    latest_value = df['portfolio_value'].iloc[-1]
    initial_value = df['portfolio_value'].iloc[0]
    pnl = latest_value - initial_value
    pnl_pct = (pnl / initial_value) * 100
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Latest Portfolio Value", f"${latest_value:.2f}")
    col2.metric("P&L", f"${pnl:.2f}", f"{pnl_pct:+.2f}%")
    col3.metric("Total Trades", len(df))
    
    # Show recent trades
    st.subheader("Recent Trades")
    recent_trades = df.tail(10)[['timestamp', 'asset', 'decision', 'portfolio_value']].copy()
    recent_trades = recent_trades.rename(columns={
        'portfolio_value': 'Portfolio Value ($)',
        'decision': 'Decision'
    })
    st.dataframe(recent_trades)
    
    # Show statistics
    st.subheader("Performance Statistics")
    total_return = ((df['portfolio_value'].iloc[-1] / df['portfolio_value'].iloc[0]) - 1) * 100
    max_value = df['portfolio_value'].max()
    min_value = df['portfolio_value'].min()
    
    stats_col1, stats_col2, stats_col3 = st.columns(3)
    stats_col1.metric("Total Return", f"{total_return:+.2f}%")
    stats_col2.metric("Max Value", f"${max_value:.2f}")
    stats_col3.metric("Min Value", f"${min_value:.2f}")

st.sidebar.header("Controls")
st.sidebar.info("Run the trading agent to generate data for this dashboard")