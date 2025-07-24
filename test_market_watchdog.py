#!/usr/bin/env python3
"""
Test script for Market Watchdog Agent tools
This script tests all the tools used in the market watchdog agent to ensure they work properly.
"""

import asyncio
import pandas as pd
from src.agents.dap import data_acquisition_tool
from src.agents.laa import engineer_features_tool
from src.agents.msc import classify_market_state_tool
from src.agents.pp import price_prediction_tool
from src.agents.rm import risk_management_tool
from src.bot.tools.common_tools import get_active_trades_tool
from src.bot.custom_types import (
    AnalysisInputModel,
    FeatureEngineerData,
    MarketStateClassifierInput,
    PricePredictionInputData,
    RiskManagementInputData,
    ActiveTradesInput
)

def test_data_acquisition_tool():
    """Test the data acquisition tool"""
    print("Testing data_acquisition_tool...")
    try:
        input_data = {
            "input": {
                "symbol": "EUR_USD",
                "timeframe": "M1",
                "tool_call_id": "test_123"
            }
        }
        market_data, news_data = data_acquisition_tool(input_data)
        print(f"✅ Data acquisition successful - Market data: {len(market_data)} records, News: {len(news_data)} items")
        return True
    except Exception as e:
        print(f"❌ Data acquisition failed: {e}")
        return False

def test_engineer_features_tool():
    """Test the feature engineering tool"""
    print("Testing engineer_features_tool...")
    try:
        # Create sample market data
        market_data = [
            {
                'time': '2024-01-01 10:00:00',
                'open': 1.1000,
                'high': 1.1010,
                'low': 1.0990,
                'close': 1.1005,
                'volume': 1000
            },
            {
                'time': '2024-01-01 10:01:00',
                'open': 1.1005,
                'high': 1.1020,
                'low': 1.1000,
                'close': 1.1015,
                'volume': 1200
            }
        ]
        
        news_data = [
            {'title': 'EUR strengthens against USD', 'content': 'Positive news for EUR'},
            {'title': 'ECB announces new policy', 'content': 'Market reacts to ECB decision'}
        ]
        
        input_data = {
            "input": {
                "market_df": market_data,
                "news_df": news_data,
                "timeframe": "M1"
            }
        }
        
        features = engineer_features_tool(input_data)
        print(f"✅ Feature engineering successful - Features: {len(features)} records")
        return True
    except Exception as e:
        print(f"❌ Feature engineering failed: {e}")
        return False

def test_classify_market_state_tool():
    """Test the market state classification tool"""
    print("Testing classify_market_state_tool...")
    try:
        # Create sample features data
        features_data = [
            {
                'time': '2024-01-01 10:00:00',
                'open': 1.1000,
                'high': 1.1010,
                'low': 1.0990,
                'close': 1.1005,
                'volume': 1000,
                'rsi': 55.0,
                'macd': 0.001,
                'macd_signal': 0.0005,
                'ema_20': 1.1002,
                'ema_50': 1.0998
            },
            {
                'time': '2024-01-01 10:01:00',
                'open': 1.1005,
                'high': 1.1020,
                'low': 1.1000,
                'close': 1.1015,
                'volume': 1200,
                'rsi': 58.0,
                'macd': 0.002,
                'macd_signal': 0.001,
                'ema_20': 1.1008,
                'ema_50': 1.1000
            }
        ]
        
        input_data = {
            "input": {
                "features_df": features_data
            }
        }
        market_state = classify_market_state_tool(input_data)
        print(f"✅ Market state classification successful - State: {market_state}")
        return True
    except Exception as e:
        print(f"❌ Market state classification failed: {e}")
        return False

def test_price_prediction_tool():
    """Test the price prediction tool"""
    print("Testing price_prediction_tool...")
    try:
        # Create sample features data
        features_data = [
            {
                'time': '2024-01-01 10:00:00',
                'open': 1.1000,
                'high': 1.1010,
                'low': 1.0990,
                'close': 1.1005,
                'volume': 1000,
                'rsi': 55.0,
                'macd': 0.001,
                'macd_signal': 0.0005,
                'ema_20': 1.1002,
                'ema_50': 1.0998
            },
            {
                'time': '2024-01-01 10:01:00',
                'open': 1.1005,
                'high': 1.1020,
                'low': 1.1000,
                'close': 1.1015,
                'volume': 1200,
                'rsi': 58.0,
                'macd': 0.002,
                'macd_signal': 0.001,
                'ema_20': 1.1008,
                'ema_50': 1.1000
            }
        ]
        
        input_data = {
            "input": {
                "features_df": features_data,
                "market_state": "Trending Up"
            }
        }
        
        prediction = price_prediction_tool(input_data)
        print(f"✅ Price prediction successful - Prediction: {prediction.get('action', 'Unknown')}")
        return True
    except Exception as e:
        print(f"❌ Price prediction failed: {e}")
        return False

def test_risk_management_tool():
    """Test the risk management tool"""
    print("Testing risk_management_tool...")
    try:
        # Create sample features data
        features_data = [
            {
                'time': '2024-01-01 10:00:00',
                'open': 1.1000,
                'high': 1.1010,
                'low': 1.0990,
                'close': 1.1005,
                'volume': 1000
            },
            {
                'time': '2024-01-01 10:01:00',
                'open': 1.1005,
                'high': 1.1020,
                'low': 1.1000,
                'close': 1.1015,
                'volume': 1200
            }
        ]
        
        prediction_result = {
            'prediction': 'up',
            'confidence': 0.75,
            'action': 'Buy',
            'entry': 1.1015,
            'stop_loss': 1.1000,
            'take_profit': 1.1030,
            'strategy': 'Long breakout'
        }
        
        input_data = {
            "input": {
                "features_df": features_data,
                "prediction_result": prediction_result,
                "account_id": 1
            }
        }
        
        risk_result = risk_management_tool(input_data)
        print(f"✅ Risk management successful - Position size: {risk_result.get('position_size', 'Unknown')}")
        return True
    except Exception as e:
        print(f"❌ Risk management failed: {e}")
        return False

def test_get_active_trades_tool():
    """Test the get active trades tool"""
    print("Testing get_active_trades_tool...")
    try:
        input_data = {
            "account_id": 1
        }
        
        active_trades = get_active_trades_tool(input_data)
        print(f"✅ Get active trades successful - Trades: {len(active_trades) if isinstance(active_trades, list) else 'Error'}")
        return True
    except Exception as e:
        print(f"❌ Get active trades failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Market Watchdog Agent Tools")
    print("=" * 50)
    
    tests = [
        test_data_acquisition_tool,
        test_engineer_features_tool,
        test_classify_market_state_tool,
        test_price_prediction_tool,
        test_risk_management_tool,
        test_get_active_trades_tool
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
        print()
    
    # Summary
    print("=" * 50)
    print("📊 Test Results Summary:")
    passed = sum(results)
    total = len(results)
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 All tools are working properly!")
    else:
        print("⚠️  Some tools need attention. Check the errors above.")

if __name__ == "__main__":
    main() 