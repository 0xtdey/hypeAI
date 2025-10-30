"""
Quantitative Indicator Calculator using Python quant libraries
Provides technical analysis when TAAPI or LLM services fail
"""
import pandas as pd
import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_loader import load_config
from typing import Dict, Any, Optional

# Import optional dependencies with fallbacks
try:
    import pandas_ta as ta
    PANDAS_TA_AVAILABLE = True
except ImportError:
    PANDAS_TA_AVAILABLE = False
    ta = None

try:
    import ta as ta_lib
    TA_LIB_AVAILABLE = True
except ImportError:
    TA_LIB_AVAILABLE = False
    ta_lib = None


class QuantIndicatorCalculator:
    """
    A class to calculate technical indicators using Python quant libraries
    as a fallback when external APIs are unavailable
    """
    
    def __init__(self):
        """Initialize with configuration"""
        self.config = load_config()
    
    def calculate_indicators_from_data(self, price_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate technical indicators from price data DataFrame
        
        Args:
            price_data: DataFrame with columns ['open', 'high', 'low', 'close', 'volume']
            
        Returns:
            Dictionary containing calculated indicators
        """
        # Ensure required columns exist
        required_cols = ['open', 'high', 'low', 'close']
        for col in required_cols:
            if col not in price_data.columns:
                raise ValueError(f"Required column '{col}' not found in price data")
        
        # Make sure data is sorted by time if there's a time column
        if 'timestamp' in price_data.columns:
            price_data = price_data.sort_values('timestamp')
        
        # Use the 'close' prices for calculations
        close_prices = price_data['close'].values
        high_prices = price_data['high'].values
        low_prices = price_data['low'].values
        open_prices = price_data['open'].values
        volume = price_data['volume'].values if 'volume' in price_data.columns else np.ones(len(close_prices))
        
        # Calculate RSI
        rsi = self._calculate_rsi(close_prices)
        
        # Calculate MACD
        macd_data = self._calculate_macd(close_prices)
        
        # Calculate EMA (Exponential Moving Average)
        ema = self._calculate_ema(close_prices)
        
        # Calculate SMA (Simple Moving Average)
        sma = self._calculate_sma(close_prices)
        
        # Calculate Bollinger Bands
        bb_data = self._calculate_bollinger_bands(close_prices)
        
        # Calculate additional indicators for better analysis
        stoch_data = self._calculate_stochastic(high_prices, low_prices, close_prices)
        bb_width = bb_data['upper'] - bb_data['lower']
        bb_position = (close_prices[-1] - bb_data['lower']) / (bb_width) if bb_width != 0 and bb_width is not None else 0.5
        
        return {
            'rsi': rsi,
            'macd': macd_data,
            'ema': ema,
            'sma': sma,
            'bollinger_bands': bb_data,
            'stochastic': stoch_data,
            'bb_width': bb_width,
            'bb_position': bb_position,
            'current_price': float(close_prices[-1]),
            'volume': float(volume[-1]) if len(volume) > 0 else 0.0
        }
    
    def _calculate_rsi(self, prices: np.array, period: int = 14) -> float:
        """
        Calculate Relative Strength Index using pandas-ta
        """
        try:
            # Convert to pandas Series
            series = pd.Series(prices)
            if PANDAS_TA_AVAILABLE:
                rsi = ta.rsi(series, length=period)
                if rsi is not None and len(rsi) > 0:
                    return float(rsi.iloc[-1])
            else:
                print("pandas-ta not available, using manual RSI calculation")
        except:
            pass
        
        # Fallback calculation if pandas-ta fails or is not available
        deltas = np.diff(prices)
        gain = np.where(deltas > 0, deltas, 0)
        loss = np.where(deltas < 0, -deltas, 0)
        
        if len(gain) >= period and len(loss) >= period:
            avg_gain = np.mean(gain[-period:])
            avg_loss = np.mean(loss[-period:])
        else:
            avg_gain = np.mean(gain) if len(gain) > 0 else 0
            avg_loss = np.mean(loss) if len(loss) > 0 else 0.001  # Avoid division by zero
        
        if avg_loss == 0 or avg_loss is None:
            return 100.0
        
        rs = avg_gain / avg_loss if avg_loss != 0 else 0
        rsi = 100 - (100 / (1 + rs)) if (1 + rs) != 0 else 50.0
        return float(rsi)

        # Default fallback
        return 50.0
    
    def _calculate_macd(self, prices: np.array) -> Dict[str, float]:
        """
        Calculate MACD using pandas-ta
        """
        try:
            series = pd.Series(prices)
            if PANDAS_TA_AVAILABLE:
                macd_df = ta.macd(series)
                if macd_df is not None and not macd_df.empty:
                    return {
                        'value': float(macd_df['MACD_12_26_9'].iloc[-1]) if 'MACD_12_26_9' in macd_df.columns else 0.0,
                        'signal': float(macd_df['MACDs_12_26_9'].iloc[-1]) if 'MACDs_12_26_9' in macd_df.columns else 0.0,
                        'histogram': float(macd_df['MACDh_12_26_9'].iloc[-1]) if 'MACDh_12_26_9' in macd_df.columns else 0.0
                    }
            else:
                print("pandas-ta not available, using manual MACD calculation")
        except:
            pass
        
        # Fallback implementation
        exp1 = self._ema(prices, 12)
        exp2 = self._ema(prices, 26)
        macd_line = exp1 - exp2
        signal_line = self._ema(macd_line, 9)
        
        return {
            'value': float(macd_line[-1]),
            'signal': float(signal_line[-1]),
            'histogram': float(macd_line[-1] - signal_line[-1])
        }
    
        # Default fallback
        return {'value': 0.0, 'signal': 0.0, 'histogram': 0.0}
    
    def _calculate_ema(self, prices: np.array, period: int = 20) -> float:
        """
        Calculate Exponential Moving Average
        """
        try:
            series = pd.Series(prices)
            if PANDAS_TA_AVAILABLE:
                ema = ta.ema(series, length=period)
                if ema is not None and len(ema) > 0:
                    return float(ema.iloc[-1])
            else:
                print("pandas-ta not available, using manual EMA calculation")
        except:
            pass
        
        # Fallback implementation
        multiplier = 2 / (period + 1)
        if len(prices) > 0:
            ema = prices[0]
            for price in prices[1:]:
                ema = (price - ema) * multiplier + ema
            return float(ema)
        
        # Default fallback
        return float(np.mean(prices[-period:]) if len(prices) >= period else np.mean(prices) if len(prices) > 0 else 0)
    
    def _calculate_sma(self, prices: np.array, period: int = 20) -> float:
        """
        Calculate Simple Moving Average
        """
        try:
            series = pd.Series(prices)
            if PANDAS_TA_AVAILABLE:
                sma = ta.sma(series, length=period)
                if sma is not None and len(sma) > 0:
                    return float(sma.iloc[-1])
            else:
                print("pandas-ta not available, using manual SMA calculation")
        except:
            pass
        
        # Fallback calculation
        if len(prices) >= period:
            return float(np.mean(prices[-period:]))
        
        # Default fallback
        return float(np.mean(prices) if len(prices) > 0 else 0)
    
    def _calculate_bollinger_bands(self, prices: np.array, period: int = 20, std_dev: int = 2) -> Dict[str, float]:
        """
        Calculate Bollinger Bands
        """
        try:
            series = pd.Series(prices)
            if PANDAS_TA_AVAILABLE:
                bb = ta.bbands(series, length=period, std=std_dev)
                if bb is not None and not bb.empty:
                    return {
                        'upper': float(bb[f'BBU_{period}_{std_dev}.0'].iloc[-1]) if f'BBU_{period}_{std_dev}.0' in bb.columns else float(np.mean(prices) + std_dev * np.std(prices)),
                        'middle': float(bb[f'BBM_{period}_{std_dev}.0'].iloc[-1]) if f'BBM_{period}_{std_dev}.0' in bb.columns else float(np.mean(prices)),
                        'lower': float(bb[f'BBL_{period}_{std_dev}.0'].iloc[-1]) if f'BBL_{period}_{std_dev}.0' in bb.columns else float(np.mean(prices) - std_dev * np.std(prices))
                    }
            else:
                print("pandas-ta not available, using manual Bollinger Bands calculation")
        except:
            pass
        
        # Fallback implementation
        if len(prices) >= period:
            sma = np.mean(prices[-period:])
            std = np.std(prices[-period:])
        else:
            sma = np.mean(prices) if len(prices) > 0 else 0
            std = np.std(prices) if len(prices) > 0 else 0
        
        return {
            'upper': float(sma + std_dev * std),
            'middle': float(sma),
            'lower': float(sma - std_dev * std)
        }
    
        # Default fallback
        mean_price = float(np.mean(prices) if len(prices) > 0 else 0)
        std_price = float(np.std(prices) if len(prices) > 0 else 0)
        return {
            'upper': mean_price + std_dev * std_price,
            'middle': mean_price,
            'lower': mean_price - std_dev * std_price
        }
    
    def _calculate_stochastic(self, high_prices: np.array, low_prices: np.array, close_prices: np.array, k_period: int = 14, d_period: int = 3) -> Dict[str, float]:
        """
        Calculate Stochastic Oscillator
        """
        try:
            if PANDAS_TA_AVAILABLE:
                high_series = pd.Series(high_prices)
                low_series = pd.Series(low_prices)
                close_series = pd.Series(close_prices)
                
                stoch = ta.stoch(high_series, low_series, close_series, k=k_period, d=d_period, smooth_k=1)
                if stoch is not None and not stoch.empty:
                    return {
                        'k': float(stoch[f'STOCHk_{k_period}_{d_period}_1'].iloc[-1]) if f'STOCHk_{k_period}_{d_period}_1' in stoch.columns else 50.0,
                        'd': float(stoch[f'STOCHd_{k_period}_{d_period}_1'].iloc[-1]) if f'STOCHd_{k_period}_{d_period}_1' in stoch.columns else 50.0
                    }
            else:
                print("pandas-ta not available, using manual Stochastic calculation")
        except:
            pass
        
        # Fallback implementation
        if len(low_prices) >= k_period and len(high_prices) >= k_period:
            low_min = np.min(low_prices[-k_period:])
            high_max = np.max(high_prices[-k_period:])
        else:
            low_min = np.min(low_prices) if len(low_prices) > 0 else close_prices[-1] if len(close_prices) > 0 else 1
            high_max = np.max(high_prices) if len(high_prices) > 0 else close_prices[-1] if len(close_prices) > 0 else 1
        
        if high_max - low_min != 0:
            k_val = (close_prices[-1] - low_min) / (high_max - low_min) * 100
            k_val = max(0, min(100, k_val))  # Clamp between 0 and 100
        else:
            k_val = 50.0
        
        # For D, we'd normally calculate a moving average of K, but with only one K value,
        # we'll use the same value or implement a lookback if we have historical data
        d_val = k_val  # Simplified since we only have one K value
        
        return {
            'k': float(k_val),
            'd': float(d_val)
        }
    
        # Default fallback
        return {'k': 50.0, 'd': 50.0}
    
    def _ema(self, prices: np.array, period: int) -> np.array:
        """
        Helper function to calculate EMA
        """
        multiplier = 2 / (period + 1)
        ema_values = np.zeros_like(prices)
        ema_values[0] = prices[0]
        for i in range(1, len(prices)):
            ema_values[i] = (prices[i] - ema_values[i-1]) * multiplier + ema_values[i-1]
        return ema_values


def get_quant_indicators(asset: str, interval: str = '1h', mock_data: bool = True) -> Dict[str, Any]:
    """
    Main function to get quant-based indicators as a fallback
    When mock_data=True, it generates realistic mock data for simulation
    """
    calculator = QuantIndicatorCalculator()
    
    if mock_data:
        # Generate mock price data for the given asset and interval
        # This simulates real market data for demonstration purposes
        periods = 50  # Last 50 periods of data
        
        # Generate realistic price data
        base_price = _get_base_price_for_asset(asset)
        price_changes = np.random.normal(0, 0.02, periods)  # 2% daily volatility
        prices = [base_price]
        
        for change in price_changes[1:]:
            new_price = prices[-1] * (1 + change)
            prices.append(new_price)
        
        # Create DataFrame with mock OHLC data
        df = pd.DataFrame({
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],  # Add some variation for high
            'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],   # Add some variation for low
            'close': prices,
            'volume': np.random.randint(1000, 10000, len(prices))  # Random volume
        })
        
        return calculator.calculate_indicators_from_data(df)
    else:
        # This would be where we fetch real price data from an exchange API
        # For now, we return mock data since we don't have real price data fetching implemented
        return get_quant_indicators(asset, interval, mock_data=True)


def _get_base_price_for_asset(asset: str) -> float:
    """
    Helper function to get a reasonable base price for different assets
    """
    base_prices = {
        'BTC': 60000,
        'ETH': 3000,
        'SOL': 150,
        'XRP': 0.5,
        'ADA': 0.4,
        'DOGE': 0.15,
        'DOT': 7,
        'AVAX': 40,
        'LINK': 15,
        'MATIC': 0.8,
        'SUSHI': 3,
        'UNI': 10,
        'AAVE': 150,
        'SNX': 3.5,
        'CRV': 0.85,
        'FTM': 0.75,
        'NEAR': 6,
        'ATOM': 12,
        'FIL': 6,
        'THETA': 1.8,
        'VET': 0.03,
        'XLM': 0.15,
        'ETC': 25,
        'BSV': 100,
        'BCH': 600,
        'LTC': 90,
        'TRX': 0.15,
        'EOS': 0.75,
        'XTZ': 0.85,
        'MKR': 3000
    }
    
    return base_prices.get(asset.upper(), 100.0)  # Default to $100 if asset not found


if __name__ == "__main__":
    # Example usage and testing
    print("Testing QuantIndicatorCalculator...")
    
    # Test with mock data
    result = get_quant_indicators('BTC')
    print("BTC Indicators:", result)
    
    print("\nTesting with ETH:")
    result = get_quant_indicators('ETH')
    print("ETH Indicators:", result)