#!/usr/bin/env python3
"""
Test script for Market Watchdog Agent Graph
This script tests the full market watchdog agent workflow using the actual graph.
"""

import asyncio
import json
from src.agents.market_watch_dog_agent import market_watch_dog_agent
from src.bot.custom_types import AppState

async def test_market_watchdog_agent():
    """Test the full market watchdog agent workflow"""
    print("🧪 Testing Market Watchdog Agent Graph")
    print("=" * 50)
    
    # Test 1: Basic market analysis
    print("Test 1: Basic market analysis for EUR_USD")
    try:
        initial_state = AppState(
            messages=[
                {
                    "role": "user",
                    "content": "Analyze the EUR_USD market and provide trading recommendations"
                }
            ],
            symbol="EUR_USD"
        )
        
        # Add required configuration for MemorySaver
        config = {
            "configurable": {
                "thread_id": "test_thread_1",
                "checkpoint_ns": "test_namespace",
                "checkpoint_id": "test_checkpoint_1"
            }
        }
        
        result = await market_watch_dog_agent.ainvoke(initial_state, config=config)
        print("✅ Basic market analysis completed")
        print(f"Messages: {len(result.get('messages', []))}")
        return True
    except Exception as e:
        print(f"❌ Basic market analysis failed: {e}")
        return False

async def test_market_watchdog_with_active_trades():
    """Test the agent with active trades monitoring"""
    print("\nTest 2: Active trades monitoring")
    try:
        initial_state = AppState(
            messages=[
                {
                    "role": "user",
                    "content": "Check my active trades and provide recommendations for account ID 1"
                }
            ],
            symbol="EUR_USD"
        )
        
        config = {
            "configurable": {
                "thread_id": "test_thread_2",
                "checkpoint_ns": "test_namespace",
                "checkpoint_id": "test_checkpoint_2"
            }
        }
        
        result = await market_watch_dog_agent.ainvoke(initial_state, config=config)
        print("✅ Active trades monitoring completed")
        print(f"Messages: {len(result.get('messages', []))}")
        return True
    except Exception as e:
        print(f"❌ Active trades monitoring failed: {e}")
        return False

async def test_market_watchdog_with_specific_analysis():
    """Test the agent with specific market analysis"""
    print("\nTest 3: Specific market analysis")
    try:
        initial_state = AppState(
            messages=[
                {
                    "role": "user",
                    "content": "Analyze GBP_USD market on M5 timeframe and predict price direction"
                }
            ],
            symbol="GBP_USD"
        )
        
        config = {
            "configurable": {
                "thread_id": "test_thread_3",
                "checkpoint_ns": "test_namespace",
                "checkpoint_id": "test_checkpoint_3"
            }
        }
        
        result = await market_watch_dog_agent.ainvoke(initial_state, config=config)
        print("✅ Specific market analysis completed")
        print(f"Messages: {len(result.get('messages', []))}")
        return True
    except Exception as e:
        print(f"❌ Specific market analysis failed: {e}")
        return False

async def test_market_watchdog_with_risk_management():
    """Test the agent with risk management analysis"""
    print("\nTest 4: Risk management analysis")
    try:
        initial_state = AppState(
            messages=[
                {
                    "role": "user",
                    "content": "Analyze USD_JPY market and calculate optimal position size and risk parameters for account ID 1"
                }
            ],
            symbol="USD_JPY"
        )
        
        config = {
            "configurable": {
                "thread_id": "test_thread_4",
                "checkpoint_ns": "test_namespace",
                "checkpoint_id": "test_checkpoint_4"
            }
        }
        
        result = await market_watch_dog_agent.ainvoke(initial_state, config=config)
        print("✅ Risk management analysis completed")
        print(f"Messages: {len(result.get('messages', []))}")
        return True
    except Exception as e:
        print(f"❌ Risk management analysis failed: {e}")
        return False

async def test_market_watchdog_with_comprehensive_analysis():
    """Test the agent with comprehensive market analysis"""
    print("\nTest 5: Comprehensive market analysis")
    try:
        initial_state = AppState(
            messages=[
                {
                    "role": "user",
                    "content": "Provide a comprehensive analysis of EUR_USD including market state, price prediction, risk assessment, and trading recommendations"
                }
            ],
            symbol="EUR_USD"
        )
        
        config = {
            "configurable": {
                "thread_id": "test_thread_5",
                "checkpoint_ns": "test_namespace",
                "checkpoint_id": "test_checkpoint_5"
            }
        }
        
        result = await market_watch_dog_agent.ainvoke(initial_state, config=config)
        print("✅ Comprehensive market analysis completed")
        print(f"Messages: {len(result.get('messages', []))}")
        
        # Print the last AI message to see the analysis
        if result.get('messages'):
            last_message = result['messages'][-1]
            if hasattr(last_message, 'content'):
                print(f"Analysis: {last_message.content[:200]}...")
            elif isinstance(last_message, dict):
                print(f"Analysis: {last_message.get('content', '')[:200]}...")
        
        return True
    except Exception as e:
        print(f"❌ Comprehensive market analysis failed: {e}")
        return False

async def test_market_watchdog_with_memory():
    """Test the agent with memory enabled"""
    print("\nTest 6: Agent with memory")
    try:
        # First conversation
        initial_state = AppState(
            messages=[
                {
                    "role": "user",
                    "content": "Analyze EUR_USD market"
                }
            ],
            symbol="EUR_USD",
            thread_id="test_thread_6"
        )
        
        config1 = {
            "configurable": {
                "thread_id": "test_thread_6",
                "checkpoint_ns": "test_namespace",
                "checkpoint_id": "test_checkpoint_6_1"
            }
        }
        
        result1 = await market_watch_dog_agent.ainvoke(initial_state, config=config1)
        print("✅ First conversation completed")
        
        # Second conversation with memory
        follow_up_state = AppState(
            messages=[
                {
                    "role": "user",
                    "content": "Based on your previous analysis, what should I do next?"
                }
            ],
            symbol="EUR_USD",
            thread_id="test_thread_6"
        )
        
        config2 = {
            "configurable": {
                "thread_id": "test_thread_6",
                "checkpoint_ns": "test_namespace",
                "checkpoint_id": "test_checkpoint_6_2"
            }
        }
        
        result2 = await market_watch_dog_agent.ainvoke(follow_up_state, config=config2)
        print("✅ Second conversation with memory completed")
        print(f"Total messages in conversation: {len(result2.get('messages', []))}")
        
        return True
    except Exception as e:
        print(f"❌ Agent with memory failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🧪 Testing Market Watchdog Agent Graph")
    print("=" * 50)
    
    tests = [
        test_market_watchdog_agent,
        test_market_watchdog_with_active_trades,
        test_market_watchdog_with_specific_analysis,
        test_market_watchdog_with_risk_management,
        test_market_watchdog_with_comprehensive_analysis,
        test_market_watchdog_with_memory
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
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
        print("🎉 All market watchdog agent tests passed!")
        print("The agent is ready for production use.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        print("The agent may need some adjustments before production use.")

if __name__ == "__main__":
    asyncio.run(main()) 