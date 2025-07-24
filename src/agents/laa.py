import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator
from ta.volatility import BollingerBands
from textblob import TextBlob
from langchain_core.tools import tool

from src.bot.custom_types import FeatureEngineerData


class FeatureEngineeringAgent:
    """
    Learning and Adaptation Agent (LAA):
    Converts raw market/news data into model-ready features for trading AI.
    """
    def __init__(self):
        pass

    def _get_timeframe_multiplier(self, timeframe: str) -> int:
        """Get multiplier for adjusting window sizes based on timeframe"""
        timeframe_map = {
            'M1': 1,
            'M5': 5,
            'M15': 15,
            'M30': 30,
            'H1': 60,
            'H4': 240,
            'D': 1440
        }
        return timeframe_map.get(timeframe, 1)

    def ensure_1d_series(self, series: pd.Series) -> pd.Series:
        """Ensure the input is a 1-dimensional pandas Series."""
        if isinstance(series, pd.DataFrame):
            if series.shape[1] == 1:
                return series.iloc[:, 0]
            else:
                raise ValueError(f"Data must be 1-dimensional, got shape {series.shape} instead")
        return series

    def add_technical_indicators(self, df: pd.DataFrame, timeframe: str = 'M1') -> pd.DataFrame:
        multiplier = self._get_timeframe_multiplier(timeframe)
        
        # Adjust window sizes based on timeframe
        rsi_window = max(14, int(14 * multiplier / 60))  # Scale RSI window
        ema_short = max(20, int(20 * multiplier / 60))   # Scale EMA windows
        ema_long = max(50, int(50 * multiplier / 60))
        bb_window = max(20, int(20 * multiplier / 60))   # Scale Bollinger Bands window
        
        close_1d = self.ensure_1d_series(df['close'])
        df['rsi'] = RSIIndicator(close=close_1d, window=rsi_window).rsi()
        macd = MACD(close=close_1d)
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['macd_diff'] = macd.macd_diff()
        df['ema_20'] = EMAIndicator(close=close_1d, window=ema_short).ema_indicator()
        df['ema_50'] = EMAIndicator(close=close_1d, window=ema_long).ema_indicator()
        bb = BollingerBands(close=close_1d, window=bb_window, window_dev=2)
        df['bb_high'] = bb.bollinger_hband()
        df['bb_low'] = bb.bollinger_lband()
        df['bb_width'] = df['bb_high'] - df['bb_low']
        return df

    def add_price_action_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        df['doji'] = np.abs(df['open'] - df['close']) < (df['high'] - df['low']) * 0.1
        df['bullish_engulfing'] = (df['close'] > df['open']) & (df['close'].shift(1) < df['open'].shift(1)) & (df['close'] > df['open'].shift(1)) & (df['open'] < df['close'].shift(1))
        df['bearish_engulfing'] = (df['close'] < df['open']) & (df['close'].shift(1) > df['open'].shift(1)) & (df['open'] > df['close'].shift(1)) & (df['close'] < df['open'].shift(1))
        df['double_top'] = (df['high'] > df['high'].shift(1)) & (df['high'] > df['high'].shift(-1)) & (df['high'].shift(1) > df['high'].shift(2))
        df['double_bottom'] = (df['low'] < df['low'].shift(1)) & (df['low'] < df['low'].shift(-1)) & (df['low'].shift(1) < df['low'].shift(2))
        return df

    def add_volatility_volume_features(self, df: pd.DataFrame, timeframe: str = 'M1') -> pd.DataFrame:
        multiplier = self._get_timeframe_multiplier(timeframe)
        vol_window = max(20, int(20 * multiplier / 60))  # Scale volatility window
        
        df['volatility_20'] = df['close'].rolling(window=vol_window).std()
        vol_mean = df['volume'].rolling(window=vol_window).mean()
        vol_std = df['volume'].rolling(window=vol_window).std()
        df['volume_spike'] = df['volume'] > (vol_mean + 2 * vol_std)
        return df

    def add_sentiment_score(self, news_df: pd.DataFrame) -> float:
        if 'title' not in news_df:
            return 0.0
        sentiments = [TextBlob(str(title)).sentiment.polarity for title in news_df['title']]
        return np.mean(sentiments) if sentiments else 0.0

    def add_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df['time'] = pd.to_datetime(df['time'])
        df['hour'] = df['time'].dt.hour
        df['day_of_week'] = df['time'].dt.dayofweek
        def session(hour):
            if 0 <= hour < 7:
                return 'Asia'
            elif 7 <= hour < 15:
                return 'London'
            else:
                return 'NY'
        df['session'] = df['hour'].apply(session)
        return df

    def engineer_features(self, market_df: pd.DataFrame, news_df: pd.DataFrame, timeframe: str = 'M1') -> pd.DataFrame:
        df = market_df.copy()
        df = self.add_technical_indicators(df, timeframe)
        df = self.add_price_action_patterns(df)
        df = self.add_volatility_volume_features(df, timeframe)
        df = self.add_time_features(df)
        sentiment = self.add_sentiment_score(news_df)
        df['sentiment_score'] = sentiment

        print(f"Features data shape: {df.shape}")
        return df
    
@tool
def engineer_features_tool(input: dict) -> list[dict]:
    """
    Feature Engineering Tool for Trading Analysis.

    This tool processes raw market and news data to generate engineered features that are useful for downstream analysis, 
    machine learning models, or trading decision-making. It combines and transforms the input data to extract meaningful 
    signals and indicators.

    Args:
        input (dict): An object containing:
            - market_df (list[dict]): The preprocessed market data.
            - news_df (list[dict]): The preprocessed news data.
            - timeframe (str): The timeframe for which features should be engineered.

    Returns:
        list[dict]: A list of dicts containing the engineered features for the specified symbol and timeframe.

    Use this tool when you need to transform raw market and news data into a set of features for further analysis or model input.
    """
    import pandas as pd
    market_df = pd.DataFrame(input["market_df"])
    news_df = pd.DataFrame(input["news_df"])
    fea = FeatureEngineeringAgent()
    features_df = fea.engineer_features(market_df, news_df, input["timeframe"])
    return features_df.to_dict(orient="records")
