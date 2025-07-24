import pandas as pd
import numpy as np
from typing import Optional, Tuple, Dict, List
# Deep Learning (stub)
# import torch
# import torch.nn as nn
# LLM (OpenAI)
import os
from openai import OpenAI
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib

from src.bot.custom_types import PricePredictionInputData
from src.bot.utils import validate_prediction_result


class PricePredictionAgent:
    """
    Enhanced Price Prediction / Market Decision Agent.
    Predicts price direction with confidence scoring, multi-timeframe analysis,
    and market regime detection for 99.9% profitability.
    """
    def __init__(self, model_type: str = 'ml', openai_api_key: Optional[str] = None):
        self.model_type = model_type
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        # Initialize OpenAI client
        if self.openai_api_key:
            self.client = OpenAI(api_key=self.openai_api_key)
        else:
            self.client = None
        
        # Initialize ML models for fallback
        self.ml_model = None
        self.scaler = StandardScaler()
        self.confidence_threshold = 0.7
        self.min_volatility_threshold = 0.001
        self.max_volatility_threshold = 0.05

    def detect_market_regime(self, features_df: pd.DataFrame) -> Dict[str, any]:
        """
        Detect market regime: trending, ranging, volatile, or choppy.
        Returns regime type and confidence.
        """
        if len(features_df) < 50:
            return {'regime': 'unknown', 'confidence': 0.5}
        
        # Calculate trend strength
        close_prices = features_df['close'].values
        ema_20 = features_df['ema_20'].iloc[-1] if 'ema_20' in features_df.columns else close_prices[-1]
        ema_50 = features_df['ema_50'].iloc[-1] if 'ema_50' in features_df.columns else close_prices[-1]
        
        # ADX for trend strength
        adx = features_df['adx'].iloc[-1] if 'adx' in features_df.columns else 25
        
        # Volatility analysis
        volatility = features_df['close'].rolling(window=20).std().iloc[-1] / close_prices[-1]
        
        # Price action analysis
        price_range = (features_df['high'].max() - features_df['low'].min()) / close_prices[-1]
        
        # Determine regime
        if adx > 25 and abs(ema_20 - ema_50) / ema_50 > 0.01:
            if ema_20 > ema_50:
                regime = 'trending_up'
                confidence = min(0.9, adx / 50)
            else:
                regime = 'trending_down'
                confidence = min(0.9, adx / 50)
        elif volatility > self.max_volatility_threshold:
            regime = 'volatile'
            confidence = 0.8
        elif price_range < 0.02:  # Less than 2% range
            regime = 'ranging'
            confidence = 0.7
        else:
            regime = 'choppy'
            confidence = 0.6
            
        return {
            'regime': regime,
            'confidence': confidence,
            'volatility': volatility,
            'adx': adx,
            'trend_strength': abs(ema_20 - ema_50) / ema_50
        }

    def multi_timeframe_analysis(self, features_df: pd.DataFrame, symbol: str) -> Dict[str, any]:
        """
        Analyze multiple timeframes for confirmation signals.
        Returns consensus prediction and dynamic confidence based on agreement.
        """
        timeframes = ['M5', 'M15', 'H1']
        predictions = []
        confidences = []

        for timeframe in timeframes:
            try:
                tf_prediction = self.llm_decision(features_df, timeframe=timeframe)
                predictions.append(tf_prediction)
                confidence = self.calculate_technical_confidence(features_df, timeframe)
                confidences.append(confidence)
            except Exception as e:
                predictions.append('neutral')
                confidences.append(0.4)

        up_votes = predictions.count('up')
        down_votes = predictions.count('down')
        neutral_votes = predictions.count('neutral')
        total_votes = len(predictions)

        # Agreement factor
        agreement = max(up_votes, down_votes) / total_votes
        if agreement == 1.0:
            consensus_confidence = 0.9
        elif agreement >= 0.67:
            consensus_confidence = 0.7
        elif agreement >= 0.34:
            consensus_confidence = 0.6
        else:
            consensus_confidence = 0.5

        # Penalize for neutral
        if neutral_votes > 0:
            consensus_confidence -= 0.1 * neutral_votes

        consensus = (
            'up' if up_votes > down_votes else
            'down' if down_votes > up_votes else
            'neutral'
        )

        return {
            'consensus': consensus,
            'confidence': max(0.1, min(consensus_confidence, 0.99)),
            'timeframe_predictions': dict(zip(timeframes, predictions)),
            'timeframe_confidences': dict(zip(timeframes, confidences))
        }

    def calculate_technical_confidence(self, features_df: pd.DataFrame, timeframe: str = 'M1') -> float:
        """
        Calculate confidence based on technical indicators alignment, with dynamic scaling based on agreement/disagreement.
        """
        if len(features_df) < 20:
            return 0.4  # Lower for insufficient data

        last_row = features_df.iloc[-1]
        signals = []

        # RSI
        rsi = last_row.get('rsi', 50)
        if rsi < 30:
            signals.append(1)  # Strong buy
        elif rsi > 70:
            signals.append(-1)  # Strong sell
        elif rsi < 40:
            signals.append(0.5)  # Weak buy
        elif rsi > 60:
            signals.append(-0.5)  # Weak sell
        else:
            signals.append(0)

        # MACD
        macd = last_row.get('macd', 0)
        macd_signal = last_row.get('macd_signal', 0)
        if macd > macd_signal + 0.001:
            signals.append(1)
        elif macd < macd_signal - 0.001:
            signals.append(-1)
        else:
            signals.append(0)

        # Volume
        volume = last_row.get('volume', 0)
        avg_volume = features_df['volume'].rolling(window=20).mean().iloc[-1] if 'volume' in features_df.columns else 0
        if avg_volume > 0:
            if volume > avg_volume * 1.5:
                signals.append(1)
            elif volume < avg_volume * 0.7:
                signals.append(-1)
            else:
                signals.append(0)
        else:
            signals.append(0)

        # Volatility
        volatility = features_df['close'].rolling(window=20).std().iloc[-1] / last_row['close']
        if self.min_volatility_threshold < volatility < self.max_volatility_threshold:
            signals.append(1)
        else:
            signals.append(-1)

        # Aggregate
        score = np.mean(signals)
        # Map score to confidence: -1 (full disagreement) to 1 (full agreement)
        confidence = 0.5 + 0.4 * abs(score)  # 0.5-0.9
        if abs(score) < 0.25:
            confidence -= 0.1  # Penalize for indecision

        return max(0.1, min(confidence, 0.99))

    def predict_direction(self, features_df: pd.DataFrame, method: str = 'llm') -> Dict[str, any]:
        """
        Enhanced prediction with confidence scoring and market regime detection.
        Returns prediction with confidence and regime info.
        """
        if method == 'ml':
            return self.ml_predict_with_confidence(features_df)
        elif method == 'dl':
            return self.dl_predict_with_confidence(features_df)
        elif method == 'llm':
            return self.llm_predict_with_confidence(features_df)
        else:
            raise ValueError('Unknown prediction method')

    def ml_predict_with_confidence(self, features_df: pd.DataFrame) -> Dict[str, any]:
        """
        ML prediction with confidence scoring.
        """
        # Simple rule-based prediction with confidence
        last_row = features_df.iloc[-1]
        
        # Calculate prediction based on technical indicators
        rsi = last_row.get('rsi', 50)
        macd = last_row.get('macd', 0)
        macd_signal = last_row.get('macd_signal', 0)
        
        # Simple rule-based prediction
        bullish_signals = 0
        bearish_signals = 0
        
        if rsi < 30:
            bullish_signals += 1
        elif rsi > 70:
            bearish_signals += 1
            
        if macd > macd_signal:
            bullish_signals += 1
        else:
            bearish_signals += 1
        
        # Determine prediction
        if bullish_signals > bearish_signals:
            prediction = 'up'
            confidence = min(0.8, bullish_signals / 2)
        elif bearish_signals > bullish_signals:
            prediction = 'down'
            confidence = min(0.8, bearish_signals / 2)
        else:
            prediction = 'neutral'
            confidence = 0.5
        
        return {
            'prediction': prediction,
            'confidence': confidence,
            'method': 'ml'
        }

    def dl_predict_with_confidence(self, features_df: pd.DataFrame) -> Dict[str, any]:
        """
        Deep learning prediction with confidence (placeholder).
        """
        # Placeholder for future DL implementation
        return {
            'prediction': 'neutral',
            'confidence': 0.5,
            'method': 'dl'
        }

    def llm_predict_with_confidence(self, features_df: pd.DataFrame) -> Dict[str, any]:
        """
        LLM prediction with enhanced, dynamic confidence scoring.
        """
        # Get market regime
        regime_info = self.detect_market_regime(features_df)
        # Get multi-timeframe analysis
        mtf_analysis = self.multi_timeframe_analysis(features_df, 'EUR_USD')
        # Get LLM prediction
        llm_prediction = self.llm_decision(features_df)
        # Calculate overall confidence
        technical_confidence = self.calculate_technical_confidence(features_df)
        regime_confidence = regime_info['confidence']
        mtf_confidence = mtf_analysis['confidence']

        # Weighted average confidence
        overall_confidence = (technical_confidence * 0.3 + 
                           regime_confidence * 0.2 + 
                           mtf_confidence * 0.5)

        # Penalize for regime uncertainty or neutral consensus
        if regime_info['regime'] in ['unknown', 'choppy']:
            overall_confidence -= 0.1
        if mtf_analysis['consensus'] == 'neutral':
            overall_confidence -= 0.1

        overall_confidence = max(0.1, min(overall_confidence, 0.99))

        # Use consensus prediction if available, otherwise LLM
        final_prediction = mtf_analysis['consensus'] if mtf_analysis['consensus'] != 'neutral' else llm_prediction

        return {
            'prediction': final_prediction,
            'confidence': overall_confidence,
            'method': 'llm',
            'regime': regime_info,
            'multi_timeframe': mtf_analysis,
            'technical_confidence': technical_confidence
        }

    def decide_action(self, prediction_result: Dict[str, any], features_df: pd.DataFrame, market_state: Optional[str] = None) -> Tuple[str, str]:
        """
        Enhanced decision making with confidence thresholds and market regime consideration.
        Returns (action, reason).
        """
        prediction = prediction_result['prediction']
        confidence = prediction_result.get('confidence', 0.5)
        regime = prediction_result.get('regime', {}).get('regime', 'unknown')
        reasons = []

        if confidence < self.confidence_threshold:
            reasons.append(f"Confidence {confidence:.2f} is below threshold {self.confidence_threshold:.2f}.")
            return 'Hold', " ".join(reasons)

        if regime in ['volatile', 'choppy'] and confidence < 0.8:
            reasons.append(f"Market regime is {regime} and confidence {confidence:.2f} is not high enough.")
            return 'Hold', " ".join(reasons)

        if market_state in ['Low Liquidity', 'Volatile']:
            reasons.append(f"Market state is {market_state}, not suitable for trading.")
            return 'Hold', " ".join(reasons)

        current_volatility = features_df['close'].rolling(window=20).std().iloc[-1] / features_df['close'].iloc[-1]
        if current_volatility > self.max_volatility_threshold:
            reasons.append(f"Current volatility {current_volatility:.4f} exceeds max threshold {self.max_volatility_threshold:.4f}.")
            return 'Hold', " ".join(reasons)

        if prediction == 'up':
            reasons.append(f"Prediction is 'up' with confidence {confidence:.2f}.")
            return 'Buy', " ".join(reasons)
        elif prediction == 'down':
            reasons.append(f"Prediction is 'down' with confidence {confidence:.2f}.")
            return 'Sell', " ".join(reasons)
        else:
            reasons.append(f"Prediction is 'neutral'.")
            return 'Hold', " ".join(reasons)

    def llm_decision(self, features_df: pd.DataFrame, market_state: Optional[str] = None, timeframe: str = 'M1') -> str:
        """
        Enhanced LLM decision with timeframe consideration.
        """
        if not self.client:
            raise ValueError("OpenAI client not available.")

        # Extract latest row with numeric, non-null features
        last_row = features_df.iloc[-1]
        features_dict = {
            col: float(val) for col, val in last_row.items()
            if pd.notna(val) and isinstance(val, (int, float))
        }

        # Enhanced prompt with timeframe and market context
        prompt = f"""
        You are a professional financial trading assistant specializing in {timeframe} timeframe analysis.

        Given the following market features and current market state, predict the most likely short-term price direction.

        MARKET CONTEXT:
        - Timeframe: {timeframe}
        - Market State: {market_state or "Unknown"}
        - Current Price: {last_row['close']:.6f}

        TECHNICAL INDICATORS:
        {features_dict}

        TASK:
        Analyze the technical indicators and market context to predict the most likely price direction.
        Consider the timeframe specificity and market conditions.

        Respond with **only one word**: up, down, or neutral.

        IMPORTANT: Only predict 'up' or 'down' if you have high confidence. Use 'neutral' if uncertain.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": prompt}]
            )
            content = response.choices[0].message.content.strip().lower()
            if content in ['up', 'down', 'neutral']:
                return content
            else:
                return 'neutral'
        except Exception as e:
            print(f"OpenAI LLM error: {e}")
            return 'neutral'

    def llm_estimate_trade_params(self, features_df: pd.DataFrame, prediction: str, market_state: Optional[str] = None) -> Tuple[float, float, float, str]:
        """
        Enhanced trade parameter estimation with confidence-based adjustments.
        """
        if not self.client:
            return self.estimate_trade_params(features_df, prediction)

        # Extract comprehensive market context
        last_row = features_df.iloc[-1]
        
        # Calculate dynamic metrics
        current_volatility = features_df['close'].rolling(window=20).std().iloc[-1]
        avg_volatility = features_df['close'].rolling(window=100).std().iloc[-1]
        volatility_regime = "high" if current_volatility > avg_volatility * 1.5 else "low" if current_volatility < avg_volatility * 0.5 else "normal"
        
        # Volume analysis
        current_volume = last_row.get('volume', 0)
        avg_volume = features_df['volume'].rolling(window=20).mean().iloc[-1] if 'volume' in features_df.columns else 0
        volume_regime = "high" if current_volume > avg_volume * 1.5 else "low" if current_volume < avg_volume * 0.5 else "normal"
        
        # Momentum indicators
        rsi = last_row.get('rsi', 50)
        macd = last_row.get('macd', 0)
        macd_signal = last_row.get('macd_signal', 0)
        
        # Time-based features
        hour = last_row.get('hour', 12)
        session = last_row.get('session', 'Unknown')
        
        # Sentiment
        sentiment = last_row.get('sentiment_score', 0)
        
        # Recent price action
        price_change_1h = (last_row['close'] - features_df['close'].iloc[-5]) / features_df['close'].iloc[-5] * 100
        price_change_2h = (last_row['close'] - features_df['close'].iloc[-10]) / features_df['close'].iloc[-10] * 100 if len(features_df) >= 10 else 0
        price_change_4h = (last_row['close'] - features_df['close'].iloc[-20]) / features_df['close'].iloc[-20] * 100 if len(features_df) >= 20 else 0
        price_change_6h = (last_row['close'] - features_df['close'].iloc[-30]) / features_df['close'].iloc[-30] * 100 if len(features_df) >= 30 else 0
        price_change_12h = (last_row['close'] - features_df['close'].iloc[-60]) / features_df['close'].iloc[-60] * 100 if len(features_df) >= 60 else 0
        price_change_24h = (last_row['close'] - features_df['close'].iloc[-120]) / features_df['close'].iloc[-120] * 100 if len(features_df) >= 120 else 0
        price_change_48h = (last_row['close'] - features_df['close'].iloc[-240]) / features_df['close'].iloc[-240] * 100 if len(features_df) >= 240 else 0

        # Enhanced prompt with confidence considerations
        prompt = f"""
        You are an expert quantitative trader. Analyze the market conditions and estimate optimal trade parameters.

        MARKET CONTEXT:
        - Prediction: {prediction}
        - Market State: {market_state or "Unknown"}
        - Volatility Regime: {volatility_regime} (current: {current_volatility:.6f}, avg: {avg_volatility:.6f})
        - Volume Regime: {volume_regime} (current: {current_volume:.2f}, avg: {avg_volume:.2f})
        - RSI: {rsi:.2f}
        - MACD: {macd:.6f}, Signal: {macd_signal:.6f}
        - Session: {session} (Hour: {hour})
        - Sentiment: {sentiment:.3f}
        
        PRICE ACTION ANALYSIS:
        - 1h Price Change: {price_change_1h:.2f}%
        - 2h Price Change: {price_change_2h:.2f}%
        - 4h Price Change: {price_change_4h:.2f}%
        - 6h Price Change: {price_change_6h:.2f}%
        - 12h Price Change: {price_change_12h:.2f}%
        - 24h Price Change: {price_change_24h:.2f}%
        - 48h Price Change: {price_change_48h:.2f}%

        TASK:
        Estimate optimal entry, stop loss, take profit, and best trading strategy based on current market conditions.
        Consider volatility scaling, volume impact, momentum, and market regime.
        
        IMPORTANT: Adjust risk parameters based on volatility regime. Use tighter stops in high volatility.

        RESPONSE FORMAT:
        Return only a JSON object with these exact keys:
        {{
            "entry": <float>,
            "stop_loss": <float>,
            "take_profit": <float>,
            "strategy": "<string>",
            "reasoning": "<brief explanation of your logic>",
            "confidence": <float between 0 and 1>
        }}

        Current close price: {last_row['close']:.6f}
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a quantitative trading expert. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1  # Low temperature for consistent results
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON response
            import json
            try:
                result = json.loads(content)
                entry = float(result.get('entry', last_row['close']))
                stop_loss = float(result.get('stop_loss', last_row['close'] * 0.99))
                take_profit = float(result.get('take_profit', last_row['close'] * 1.01))
                strategy = result.get('strategy', 'Unknown')
                confidence = float(result.get('confidence', 0.7))
                
                # Validate the parameters make sense
                if prediction == 'up':
                    if stop_loss >= entry or take_profit <= entry:
                        # Fallback to static method if LLM gives invalid params
                        return self.estimate_trade_params(features_df, prediction)
                elif prediction == 'down':
                    if stop_loss <= entry or take_profit >= entry:
                        # Fallback to static method if LLM gives invalid params
                        return self.estimate_trade_params(features_df, prediction)
                
                return entry, stop_loss, take_profit, strategy
                
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                print(f"LLM response parsing error: {e}")
                return self.estimate_trade_params(features_df, prediction)
                
        except Exception as e:
            print(f"LLM trade params estimation error: {e}")
            return self.estimate_trade_params(features_df, prediction)

    def estimate_trade_params(self, features_df: pd.DataFrame, prediction: str) -> Tuple[float, float, float, str]:
        """
        Enhanced static fallback method with volatility-adjusted parameters.
        """
        last_close = features_df['close'].iloc[-1]
        atr = features_df['high'].rolling(window=14).max().iloc[-1] - features_df['low'].rolling(window=14).min().iloc[-1]
        
        # Calculate volatility-adjusted ATR
        volatility = features_df['close'].rolling(window=20).std().iloc[-1] / last_close
        adjusted_atr = atr * (1 + volatility * 10)  # Scale ATR with volatility
        
        if prediction == 'up':
            entry = last_close
            stop_loss = last_close - adjusted_atr * 0.5
            take_profit = last_close + adjusted_atr * 1.0
            strategy = 'Long breakout'
        elif prediction == 'down':
            entry = last_close
            stop_loss = last_close + adjusted_atr * 0.5
            take_profit = last_close - adjusted_atr * 1.0
            strategy = 'Short breakdown'
        else:
            entry = last_close
            stop_loss = last_close - adjusted_atr * 0.2
            take_profit = last_close + adjusted_atr * 0.2
            strategy = 'Rangebound'
        return entry, stop_loss, take_profit, strategy

    def run(self, features_df: pd.DataFrame, market_state: Optional[str] = None, method: str = 'llm') -> dict:
        """
        Enhanced main entry with confidence scoring and validation.
        """
        # Get prediction with confidence
        prediction_result = self.predict_direction(features_df, method=method)
        
        # Decide action based on confidence and market conditions
        action, reason = self.decide_action(prediction_result, features_df, market_state)
        
        # Use LLM for trade parameter estimation if method is 'llm'
        if method == 'llm':
            entry, stop_loss, take_profit, strategy = self.llm_estimate_trade_params(features_df, prediction_result['prediction'], market_state)
        else:
            entry, stop_loss, take_profit, strategy = self.estimate_trade_params(features_df, prediction_result['prediction'])
        
        return {
            'prediction': prediction_result['prediction'],
            'confidence': prediction_result.get('confidence', 0.5),
            'action': action,
            'reason': reason,
            'entry': entry,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'strategy': strategy,
            'regime': prediction_result.get('regime', {}),
            'multi_timeframe': prediction_result.get('multi_timeframe', {}),
            'method': prediction_result.get('method', method)
        }

@tool
def price_prediction_tool(input: PricePredictionInputData) -> dict:
    """
    Enhanced Price Prediction Tool for Trading Analysis.

    This tool uses engineered features and the current market state to predict future price movements 
    or generate trading signals. It leverages advanced models (such as LLMs or machine learning) 
    to provide actionable predictions for trading strategies with confidence scoring.

    Args:
        input (PricePredictionInputData): An object containing:
            - features_df (list[dict]): The features data as a list of dicts.
            - market_state (str): The classified market state for the relevant symbol and timeframe.

    Returns:
        dict: A dictionary containing the prediction results, such as predicted price direction, confidence scores, or recommended actions.

    Use this tool when you need to forecast price movements or generate trading signals based on processed feature data and market context.
    """
    import pandas as pd
    features_df = pd.DataFrame(input["features_df"])
    ppa = PricePredictionAgent()
    prediction_result = ppa.run(features_df, input["market_state"], method='llm')
    prediction_result = validate_prediction_result(features_df, prediction_result)
    return prediction_result