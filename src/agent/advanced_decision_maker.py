"""
Advanced Trading Algorithm with Quantitative Finance Techniques
Implements sophisticated signals, ML-based predictions, and intelligent execution
"""
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_loader import load_config
from indicators.quant_indicator_calculator import QuantIndicatorCalculator
from datetime import datetime
import openai

# Import TA-Lib for technical analysis
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    print("Warning: talib not available. Some advanced indicators will use fallback calculations.")

class AdvancedTradingAlgorithm:
    """
    Advanced multi-layered trading algorithm implementing:
    - Technical analysis with adaptive thresholds
    - Machine learning predictions
    - Risk management with position sizing
    - Market regime detection
    - Momentum and mean reversion signals
    """
    
    def __init__(self):
        self.config = load_config()
        self.models = {}
        self.scaler = StandardScaler()
        self.lookback = 50  # Number of historical data points to use
        self.risk_manager = AdvancedRiskManager()
        self.regime_detector = MarketRegimeDetector()
        self.indicator_calculator = QuantIndicatorCalculator()
        
        # ML models for different purposes
        self.ml_models = {
            'trend_prediction': RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42),
            'volatility_prediction': RandomForestRegressor(n_estimators=50, max_depth=8, random_state=42),
            'momentum_prediction': RandomForestRegressor(n_estimators=75, max_depth=12, random_state=42)
        }
        
    def calculate_advanced_indicators(self, price_data: pd.DataFrame) -> dict:
        """
        Calculate sophisticated indicators beyond basic TA
        """
        if len(price_data) < 30:
            raise ValueError("Need at least 30 data points for advanced indicators")
        
        close = price_data['close'].values
        high = price_data['high'].values
        low = price_data['low'].values
        volume = price_data.get('volume', np.ones(len(close))).values
        
        # Momentum Indicators
        if TALIB_AVAILABLE:
            rsi = talib.RSI(close)
            macd, macd_signal, macd_hist = talib.MACD(close)
            cci = talib.CCI(high, low, close)
            roc = talib.ROC(close, timeperiod=10)
            atr = talib.ATR(high, low, close)
            bb_upper, bb_middle, bb_lower = talib.BBANDS(close)
            obv = talib.OBV(close, volume)
        else:
            # Fallback implementations when TA-Lib is not available
            rsi = pd.Series(close).rolling(14).apply(lambda x: 100 - (100 / (1 + np.mean(x[x > x.mean()]) / np.mean(x[x < x.mean()]) if np.mean(x[x < x.mean()]) != 0 else 1)))
            # Simplified MACD (12-26 EMA difference)
            ema12 = pd.Series(close).ewm(span=12).mean()
            ema26 = pd.Series(close).ewm(span=26).mean()
            macd_val = ema12 - ema26
            macd_signal = macd_val.ewm(span=9).mean()
            macd_hist = macd_val - macd_signal
            macd = macd_val
            macd_signal = macd_signal
            macd_hist = macd_hist
            # Simplified CCI
            typical_price = (high + low + close) / 3
            cci = (typical_price - typical_price.rolling(20).mean()) / (0.015 * typical_price.rolling(20).std())
            roc = pd.Series(close).pct_change(10) * 100
            # Simplified ATR
            tr = pd.Series([max(h - l, abs(h - c_prev), abs(l - c_prev)) for h, l, c, c_prev in 
                           zip(high[1:], low[1:], close[1:], close[:-1])])
            atr = pd.Series([np.nan] + tr.rolling(14).mean().tolist())
            # Simplified Bollinger bands
            bb_middle = pd.Series(close).rolling(20).mean()
            bb_std = pd.Series(close).rolling(20).std()
            bb_upper = bb_middle + (bb_std * 2)
            bb_lower = bb_middle - (bb_std * 2)
            # Simplified OBV
            obv = [0]
            for i in range(1, len(close)):
                if close[i] > close[i-1]:
                    obv.append(obv[-1] + volume[i])
                elif close[i] < close[i-1]:
                    obv.append(obv[-1] - volume[i])
                else:
                    obv.append(obv[-1])
        
        # Volatility Indicators
        volatility = pd.Series(close).rolling(20).std()
        
        # Statistical Indicators
        correlation = pd.Series(close).rolling(10).corr(pd.Series(close).shift(1))
        skewness = pd.Series(close).rolling(20).apply(lambda x: stats.skew(x))
        
        # Volume Indicators
        volume_sma_ratio = volume / pd.Series(volume).rolling(20).mean()
        
        # Price Position Indicators
        price_position = (close - low) / (high - low)  # Stochastic-like
        
        # Advanced features
        returns = pd.Series(close).pct_change()
        hurst_exponent = self._calculate_hurst_exponent(close)
        hurst_exponent = hurst_exponent if hurst_exponent is not None else 0.5
        
        # Extract the last values from the indicators, handling both pandas Series and numpy arrays
        def get_last_valid_value(indicator, default_val, current_price=None):
            if isinstance(indicator, (pd.Series, pd.DataFrame)):
                val = indicator.iloc[-1] if len(indicator) > 0 else np.nan
            else:  # numpy array or similar
                val = indicator[-1] if len(indicator) > 0 else np.nan
            
            if pd.isna(val) or np.isnan(val):
                if current_price is not None and 'close' in str(current_price):
                    # For bollinger bands, use price-based fallback
                    if 'upper' in str(default_val):
                        return current_price * 1.02
                    elif 'middle' in str(default_val):
                        return current_price
                    elif 'lower' in str(default_val):
                        return current_price * 0.98
                return default_val
            return float(val)
        
        return {
            'rsi': get_last_valid_value(rsi, 50),
            'macd': {
                'value': get_last_valid_value(macd, 0),
                'signal': get_last_valid_value(macd_signal, 0),
                'histogram': get_last_valid_value(macd_hist, 0)
            },
            'cci': get_last_valid_value(cci, 0),
            'bollinger_bands': {
                'upper': get_last_valid_value(bb_upper, close[-1] * 1.02, 'upper'),
                'middle': get_last_valid_value(bb_middle, close[-1], 'middle'),
                'lower': get_last_valid_value(bb_lower, close[-1] * 0.98, 'lower')
            },
            'atr': get_last_valid_value(atr, 0),
            'volatility': get_last_valid_value(volatility, 0),
            'correlation': get_last_valid_value(correlation, 0),
            'skewness': get_last_valid_value(skewness, 0),
            'obv': get_last_valid_value(obv, 0),
            'volume_sma_ratio': get_last_valid_value(volume_sma_ratio, 1),
            'price_position': price_position[-1] if not pd.isna(price_position[-1]) else 0.5,
            'roc': get_last_valid_value(roc, 0),
            'hurst_exponent': hurst_exponent,
            'current_price': close[-1],
            'returns': get_last_valid_value(returns, 0)
        }
    
    def _calculate_hurst_exponent(self, prices):
        """
        Calculate Hurst exponent to determine market regime (0.5 = random, <0.5 = mean reverting, >0.5 = trending)
        """
        try:
            n = len(prices)
            if n < 20:
                return None
            
            # Log returns
            log_prices = np.log(prices)
            
            # Different time scales
            scales = np.arange(10, min(50, n//2))
            
            # Calculate rescaled range for each scale
            rs_vals = []
            for scale in scales:
                rs = []
                for start in range(0, n - scale, scale):
                    segment = log_prices[start:start+scale]
                    if len(segment) < 2:
                        continue
                    
                    mean = np.mean(segment)
                    devs = segment - mean
                    cumsum_devs = np.cumsum(devs)
                    r = np.max(cumsum_devs) - np.min(cumsum_devs)
                    s = np.std(segment)
                    
                    if s != 0:
                        rs.append(r / s)
                
                if rs:
                    rs_vals.append(np.mean(rs))
            
            if rs_vals and len(rs_vals) > 1:
                log_rs = np.log(rs_vals)
                log_scales = np.log(scales[:len(rs_vals)])
                
                # Fit line to log(R/S) vs log(n)
                slope, _, _, _, _ = stats.linregress(log_scales, log_rs)
                return slope
            else:
                return 0.5
        except:
            return 0.5
    
    def generate_advanced_signals(self, indicators: dict, asset: str, portfolio_value: float) -> dict:
        """
        Generate multiple sophisticated signals combining technical and ML-based analysis
        """
        signals = {}
        
        # Technical-based signals with adaptive thresholds
        signals['trend_signal'] = self._calculate_trend_signal(indicators)
        signals['mean_reversion_signal'] = self._calculate_mean_reversion_signal(indicators)
        signals['momentum_signal'] = self._calculate_momentum_signal(indicators)
        signals['volatility_signal'] = self._calculate_volatility_signal(indicators)
        
        # Market regime analysis
        regime = self.regime_detector.detect_regime(indicators)
        signals['regime_signal'] = self._adjust_signals_for_regime(signals, regime)
        
        # Risk-adjusted position sizing
        position_size = self.risk_manager.calculate_position_size(
            asset, indicators, portfolio_value, regime
        )
        
        # Calculate combined signal with regime-dependent weights
        if regime == 'trending':
            # In trending markets, favor momentum/trend-following
            combined_signal = (
                0.35 * signals['trend_signal'] + 
                0.25 * signals['momentum_signal'] + 
                0.20 * signals['regime_signal'] +
                0.20 * signals['volatility_signal']
            )
        elif regime == 'volatile':
            # In volatile markets, favor mean reversion with caution
            combined_signal = (
                0.30 * signals['mean_reversion_signal'] + 
                0.25 * signals['volatility_signal'] + 
                0.25 * signals['regime_signal'] +
                0.20 * signals['momentum_signal']
            )
        else:  # ranging/normal
            # Balanced approach
            combined_signal = (
                0.25 * signals['trend_signal'] + 
                0.25 * signals['mean_reversion_signal'] + 
                0.25 * signals['momentum_signal'] + 
                0.25 * signals['volatility_signal']
            )
        
        return {
            'combined_signal': combined_signal,
            'position_size': position_size,
            'regime': regime,
            'individual_signals': signals,
            'confidence': abs(combined_signal)  # Higher absolute value means more confident
        }
    
    def _calculate_trend_signal(self, indicators: dict) -> float:
        """
        Calculate trend-following signal
        """
        rsi = indicators['rsi']
        macd_val = indicators['macd']['value']
        macd_sig = indicators['macd']['signal']
        ema = indicators.get('ema', indicators['current_price'] * 0.99)  # fallback
        sma = indicators.get('sma', indicators['current_price'])  # fallback
        current_price = indicators['current_price']
        
        signal = 0
        if current_price > ema and ema > sma:  # Bullish trend
            signal += 0.5
        elif current_price < ema and ema < sma:  # Bearish trend
            signal -= 0.5
            
        if macd_val > macd_sig:  # MACD bullish
            signal += 0.3
        elif macd_val < macd_sig:  # MACD bearish
            signal -= 0.3
            
        # RSI not too extreme (trend can continue)
        if 30 < rsi < 70:
            signal *= 1.2  # Strengthen if not overbought/oversold
        elif rsi > 70:  # Overbought but trend might continue
            signal *= 0.8
        elif rsi < 30:  # Oversold but trend might continue
            signal *= 0.8
            
        return signal
    
    def _calculate_mean_reversion_signal(self, indicators: dict) -> float:
        """
        Calculate mean reversion signal
        """
        rsi = indicators['rsi']
        bb_upper = indicators['bollinger_bands']['upper']
        bb_lower = indicators['bollinger_bands']['lower']
        current_price = indicators['current_price']
        bb_position = (current_price - bb_lower) / (bb_upper - bb_lower) if (bb_upper - bb_lower) != 0 else 0.5
        
        signal = 0
        if rsi < 30:  # Oversold - buy
            signal += 0.8
        elif rsi < 40:  # Mildly oversold - buy
            signal += 0.5
        elif rsi > 70:  # Overbought - sell
            signal -= 0.8
        elif rsi > 60:  # Mildly overbought - sell
            signal -= 0.5
            
        # Bollinger Bands mean reversion
        if bb_position < 0.2:  # Below lower band - buy
            signal += 0.6
        elif bb_position < 0.3:  # Near lower band - buy
            signal += 0.4
        elif bb_position > 0.8:  # Above upper band - sell
            signal -= 0.6
        elif bb_position > 0.7:  # Near upper band - sell
            signal -= 0.4
            
        return signal
    
    def _calculate_momentum_signal(self, indicators: dict) -> float:
        """
        Calculate momentum signal
        """
        roc = indicators['roc']
        macd_hist = indicators['macd']['histogram']
        cci = indicators.get('cci', 0)  # Commodity Channel Index
        volume_ratio = indicators.get('volume_sma_ratio', 1)
        
        signal = 0
        if roc > 0:  # Positive momentum
            signal += 0.4 * min(roc * 10, 1)  # Cap the effect
        elif roc < 0:  # Negative momentum
            signal -= 0.4 * min(abs(roc) * 10, 1)
            
        if macd_hist > 0:  # Positive momentum from MACD histogram
            signal += 0.3
        elif macd_hist < 0:  # Negative momentum from MACD histogram
            signal -= 0.3
            
        # CCI for momentum
        if cci > 100:  # Above +100 - strong momentum
            signal += 0.3
        elif cci < -100:  # Below -100 - strong negative momentum
            signal -= 0.3
        elif cci > 0:  # Positive momentum
            signal += 0.1
        elif cci < 0:  # Negative momentum
            signal -= 0.1
            
        # Volume confirmation
        if volume_ratio > 1.2:  # Above average volume
            signal *= 1.2
        elif volume_ratio < 0.8:  # Below average volume
            signal *= 0.8
            
        return signal
    
    def _calculate_volatility_signal(self, indicators: dict) -> float:
        """
        Calculate volatility-based signal
        """
        volatility = indicators['volatility']
        atr = indicators['atr']
        hurst = indicators['hurst_exponent']
        skewness = indicators['skewness']
        
        signal = 0
        
        # Hurst exponent for regime detection
        if hurst > 0.6:  # Strong trending
            signal += 0.2
        elif hurst < 0.4:  # Strong mean reversion
            signal -= 0.2
        # For hurst around 0.5, neutral
        
        # Volatility breakout
        if volatility > np.mean(indicators.get('volatility_history', [volatility])) * 1.5:
            # High volatility breakout - potentially more momentum
            signal += 0.1 * (volatility / np.mean(indicators.get('volatility_history', [volatility])))
        
        # Skewness for trend direction
        if skewness > 0.5:  # Positive skew - potential up move
            signal += 0.1
        elif skewness < -0.5:  # Negative skew - potential down move
            signal -= 0.1
            
        return signal
    
    def _adjust_signals_for_regime(self, signals: dict, regime: str) -> float:
        """
        Adjust combined signal based on market regime
        """
        # In trending regimes, favor trend-following
        # In range-bound, favor mean reversion
        # In volatile, be more cautious
        if regime == 'trending':
            trend_weight = 1.2
            mean_rev_weight = 0.8
        elif regime == 'volatile':
            trend_weight = 0.8
            mean_rev_weight = 0.6
        else:  # 'ranging'
            trend_weight = 0.8
            mean_rev_weight = 1.2
        
        # Calculate regime-adjusted signal
        trend_signal = signals['trend_signal'] * trend_weight
        mean_rev_signal = signals['mean_reversion_signal'] * mean_rev_weight
        momentum_signal = signals['momentum_signal'] * 1.0  # Neutral for momentum
        vol_signal = signals['volatility_signal'] * 1.0  # Neutral for volatility
        
        return (trend_signal + mean_rev_signal + momentum_signal + vol_signal) / 4.0


class AdvancedRiskManager:
    """
    Advanced risk management with position sizing based on Kelly Criterion
    """
    
    def __init__(self):
        self.max_position_size = 0.1  # Max 10% per position
        self.max_total_risk = 0.25    # Max 25% total portfolio risk
        self.kelly_fraction = 0.25    # Use 25% of Kelly formula recommendation
    
    def calculate_position_size(self, asset: str, indicators: dict, portfolio_value: float, regime: str) -> float:
        """
        Calculate optimal position size using multiple risk factors
        """
        # Kelly Criterion approximation
        win_rate = self._estimate_win_rate(indicators, regime)
        avg_win = 0.02  # 2% average win
        avg_loss = 0.015  # 1.5% average loss
        
        # Kelly formula: K = (bp - q) / b
        # where b = odds (avg_win / avg_loss), p = win_rate, q = 1 - win_rate
        if avg_loss > 0:
            b = avg_win / avg_loss
            kelly_percentage = (b * win_rate - (1 - win_rate)) / b
            kelly_percentage = max(0, min(self.max_position_size, kelly_percentage))  # Cap between 0 and max
        else:
            kelly_percentage = 0.02  # Default small position if no loss data
        
        # Adjust for market regime
        if regime == 'volatile':
            kelly_percentage *= 0.7  # Reduce position in volatile markets
        elif regime == 'trending':
            kelly_percentage *= 1.2  # Slightly increase in trending markets
        
        # Apply Kelly fraction
        position_size = kelly_percentage * self.kelly_fraction
        position_size = min(self.max_position_size, position_size)  # Cap at max position size
        
        # Calculate dollar amount
        dollar_amount = portfolio_value * position_size
        return min(dollar_amount, portfolio_value * self.max_total_risk)  # Also cap total risk
    
    def _estimate_win_rate(self, indicators: dict, regime: str) -> float:
        """
        Estimate win rate based on indicators and market regime
        """
        rsi = indicators['rsi']
        roc = indicators['roc']
        volatility = indicators['volatility']
        
        base_win_rate = 0.55  # 55% baseline win rate
        
        # Adjust based on RSI (mean reversion)
        if 30 <= rsi <= 70:  # In neutral zone - more random
            base_win_rate -= 0.05
        elif rsi < 30 or rsi > 70:  # At extremes - higher chance of reversion
            base_win_rate += 0.05
            
        # Adjust based on momentum (ROC)
        if abs(roc) > 0.03:  # Strong momentum
            if roc > 0:  # Positive momentum
                base_win_rate += 0.03
            else:  # Negative momentum
                base_win_rate += 0.03
                
        # Adjust for high volatility (reduce win rate)
        if volatility > 0.05:  # High volatility environment
            base_win_rate -= 0.05
            
        # Adjust for regime
        if regime == 'volatile':
            base_win_rate -= 0.05
        elif regime == 'trending':
            base_win_rate += 0.02  # Slightly better in trending markets
            
        return max(0.45, min(0.65, base_win_rate))  # Bound between 45% and 65%


class MarketRegimeDetector:
    """
    Detect market regime (trending, ranging, volatile) for adaptive strategy
    """
    
    def detect_regime(self, indicators: dict) -> str:
        """
        Determine current market regime
        """
        volatility = indicators['volatility']
        atr = indicators['atr']
        hurst = indicators['hurst_exponent']
        rsi_variability = abs(indicators['rsi'] - 50) / 50  # How far from neutral
        
        # Volatility threshold - high volatility (> 5% of price)
        is_high_vol = volatility > 0.05 * indicators['current_price']
        
        # Hurst exponent - determines trendiness (0.5 = random, >0.5 = trendy)
        is_trending = hurst > 0.6
        is_mean_reverting = hurst < 0.4
        
        if is_high_vol:
            return 'volatile'
        elif is_trending:
            return 'trending'
        elif is_mean_reverting:
            return 'ranging'
        else:
            # Look at price action - if ATR is large relative to price, it's trending
            if atr > 0.02 * indicators['current_price']:
                return 'trending'
            else:
                return 'ranging'


def make_advanced_trading_decision(asset: str, price_data: pd.DataFrame, portfolio_value: float) -> dict:
    """
    Main function to make advanced trading decisions
    """
    try:
        # Initialize the algorithm
        algo = AdvancedTradingAlgorithm()
        
        # Calculate advanced indicators from price data
        indicators = algo.calculate_advanced_indicators(price_data)
        
        # Generate advanced signals
        advanced_signals = algo.generate_advanced_signals(indicators, asset, portfolio_value)
        
        # Create decision based on combined signal
        combined_signal = advanced_signals['combined_signal']
        confidence = advanced_signals['confidence']
        regime = advanced_signals['regime']
        
        # Determine decision with confidence-based thresholds
        if combined_signal > 0.3:  # Strong buy signal
            decision = 'BUY'
            strength = 'STRONG'
        elif combined_signal > 0.1:  # Weak buy signal
            decision = 'BUY'
            strength = 'WEAK'
        elif combined_signal < -0.3:  # Strong sell signal
            decision = 'SELL'
            strength = 'STRONG'
        elif combined_signal < -0.1:  # Weak sell signal
            decision = 'SELL'
            strength = 'WEAK'
        else:  # Hold signal
            decision = 'HOLD'
            strength = 'NEUTRAL'
        
        # Add detailed analysis output
        result = {
            'decision': decision,
            'strength': strength,
            'combined_signal': combined_signal,
            'confidence': confidence,
            'regime': regime,
            'position_size': advanced_signals['position_size'],
            'detailed_signals': advanced_signals['individual_signals'],
            'indicators_used': {
                'rsi': indicators['rsi'],
                'macd': indicators['macd']['value'],
                'volatility': indicators['volatility'],
                'hurst_exponent': indicators['hurst_exponent']
            }
        }
        
        return result
    
    except Exception as e:
        print(f"Error in advanced trading decision: {e}")
        # Fallback to simple technical decision
        from agent.decision_maker import quant_based_decision
        # Create a basic indicators dict to pass to fallback
        basic_indicators = {
            'rsi': 50, 'macd': {'value': 0, 'signal': 0, 'histogram': 0},
            'ema': price_data['close'].iloc[-1], 'sma': price_data['close'].iloc[-1],
            'bollinger_bands': {'upper': price_data['close'].iloc[-1]*1.02, 
                               'middle': price_data['close'].iloc[-1], 
                               'lower': price_data['close'].iloc[-1]*0.98},
            'current_price': price_data['close'].iloc[-1]
        }
        simple_decision = quant_based_decision(basic_indicators)
        return {
            'decision': simple_decision,
            'strength': 'FALLBACK',
            'combined_signal': 0,
            'confidence': 0.3,
            'regime': 'unknown',
            'position_size': portfolio_value * 0.01,  # 1% default position
            'detailed_signals': {},
            'indicators_used': basic_indicators
        }