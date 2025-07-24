from langchain_openai import ChatOpenAI
import pandas as pd
import numpy as np
from pydantic import BaseModel, Field
from ta.trend import ADXIndicator
from ta.momentum import RSIIndicator
from sklearn.cluster import KMeans
from langchain_core.tools import tool

from src.bot.custom_types import MarketStateClassifierInput




class MarketStateClassifier:
    """
    Market State Classification Agent.
    Classifies the current market as Trending (up/down), Range-bound, Volatile, or Low Liquidity.
    Supports both rule-based and ML-based (KMeans) classification.
    """
    def __init__(self):
        pass

    def rule_based_classification(self, features_df: pd.DataFrame) -> str:
        """
        Classify market state using technical indicators (RSI, ADX, volume).
        Returns one of: 'Trending Up', 'Trending Down', 'Range-bound', 'Volatile', 'Low Liquidity'
        """
        # Defensive: ensure all columns are Series, not DataFrames
        def ensure_1d(col):
            if isinstance(col, pd.DataFrame):
                if col.shape[1] == 1:
                    return col.iloc[:, 0]
                else:
                    raise ValueError(f"Column is not 1-dimensional: shape {col.shape}")
            return col
        close = ensure_1d(features_df['close'])
        high = ensure_1d(features_df['high'])
        low = ensure_1d(features_df['low'])
        volume = ensure_1d(features_df['volume'])
        # Calculate indicators if not present
        if 'rsi' not in features_df:
            features_df['rsi'] = RSIIndicator(close=close, window=14).rsi()
        if 'adx' not in features_df:
            features_df['adx'] = ADXIndicator(high=high, low=low, close=close, window=14).adx()
        # Use last N rows for state
        recent = features_df.tail(20)
        mean_rsi = recent['rsi'].mean()
        mean_adx = recent['adx'].mean()
        mean_vol = recent['volume'].mean()
        std_close = recent['close'].std()
        # Rule-based logic
        if mean_adx > 25:
            if mean_rsi > 60:
                return 'Trending Up'
            elif mean_rsi < 40:
                return 'Trending Down'
            else:
                return 'Trending'
        elif std_close > 0.01 * recent['close'].mean():
            return 'Volatile'
        elif mean_vol < 0.5 * features_df['volume'].mean():
            return 'Low Liquidity'
        else:
            return 'Range-bound'

    def ml_based_classification(self, df: pd.DataFrame, n_clusters: int = 3) -> str:
        """
        Classify market state using KMeans clustering on volatility and returns.
        Returns cluster label as string.
        """
        # Feature engineering for clustering
        df = df.copy()
        df['returns'] = df['close'].pct_change().fillna(0)
        df['volatility'] = df['close'].rolling(window=20).std().fillna(0)
        X = df[['returns', 'volatility']].tail(100).values
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X)
        # Use the label of the most recent point
        label = labels[-1]
        # Map cluster to state (simple mapping: highest mean return = uptrend, lowest = downtrend, middle = range/volatile)
        cluster_means = [X[labels == i][:,0].mean() for i in range(n_clusters)]
        sorted_idx = np.argsort(cluster_means)
        mapping = {sorted_idx[0]: 'Trending Down', sorted_idx[1]: 'Range-bound', sorted_idx[2]: 'Trending Up'}
        return mapping.get(label, f'Cluster {label}')
    
    async def llm_based_classification(self, df: pd.DataFrame) -> str:
        prompt = """
        You are a professional financial market analyst. Based on the provided market data — 
        specifically volatility and returns — classify the current market condition 
        into one of the following categories:

        - Trending Up
        - Trending Down
        - Range-bound
        - Volatile
        - Low Liquidity

        Use only the given data to inform your classification. Be concise and return only the classification label without any explanation.
        """

        messages = [{"role": "system", "content": prompt},
                    {"role": "user", "content": df.to_string()}]
        llm = ChatOpenAI(model="gpt-4o-mini")
        response = await llm.ainvoke(messages)
        return response.content.strip()


    async def classify_market_state(self, df: pd.DataFrame, method: str = 'llm') -> str:
        """
        Classify market state using the specified method ('rule' or 'ml').
        """
        if method == 'ml':
            return self.ml_based_classification(df)
        elif method == 'llm':
            return await self.llm_based_classification(df)
        else:
            return self.rule_based_classification(df) 
        
@tool
def classify_market_state_tool(input: dict) -> str:
    """
    Market State Classification Tool for Trading Analysis.

    This tool analyzes engineered features from market and news data to classify the current state of the market 
    (e.g., trending, ranging, volatile, etc.). The classification can be used to inform trading strategies, 
    risk management, or further analysis.

    Args:
        input (dict): An object containing:
            - features_df (list[dict]): The features data as a list of dicts for the relevant symbol and timeframe.

    Returns:
        str: A string label representing the classified market state (e.g., 'trending', 'ranging', 'volatile').

    Use this tool when you need to determine the current market regime or context based on processed feature data.
    """
    import pandas as pd
    features_df = pd.DataFrame(input["features_df"])
    msc = MarketStateClassifier()
    market_state = msc.rule_based_classification(features_df)  # Use rule-based for sync
    return market_state
        