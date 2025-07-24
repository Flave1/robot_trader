from fastapi import APIRouter, HTTPException
from src.bot.custom_types import FullPipelineRequest
from src.agents.dap import DataAcquisitionProcessor
from src.agents.laa import FeatureEngineeringAgent
from src.agents.msc import MarketStateClassifier
from src.agents.pp import PricePredictionAgent
from src.agents.rm import RiskManagementAgent
from src.infrastructure.oanda_api.oanda_api_service import OandaApiService
from src.users.trader_account_service import TraderAccountsTradesService
from src.users.models import TraderAccountsTradesCreate
from src.bot.utils import validate_prediction_result
from src.users.trader_account_service import TraderAccountService
from src.core.backtesting import BacktestingEngine, run_quick_backtest, compare_strategies, generate_performance_report
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio
from pydantic import BaseModel

router = APIRouter(tags=["Pipeline"])

# Global backtesting engine instance
backtest_engine = BacktestingEngine()

class BacktestRequest(BaseModel):
    symbol: str
    start_date: str
    end_date: str
    timeframe: str = "M1"
    use_llm: bool = True
    confidence_threshold: float = 0.7
    initial_balance: float = 10000.0

@router.post("/pipeline/full/analysis")
async def pipeline_full_analysis(req: FullPipelineRequest): 
    from src.database import get_db  # Import here to avoid circular import
    try:
        print(f"Starting pipeline for symbol: {req.symbol}, timeframe: {req.timeframe}")
        # 1. Data Acquisition & Preprocessing
        print("Step 1: Data Acquisition")
        async for db in get_db():
            market_df, news_df = await DataAcquisitionProcessor.initialize_dap(db, req)        

            # 2. Feature Engineering
            print("Step 2: Feature Engineering")
            fea = FeatureEngineeringAgent()
            features_df = fea.engineer_features(market_df, news_df, req.timeframe)

            # 3. Market State Classification
            print("Step 3: Market State Classification")
            msc = MarketStateClassifier()
            market_state = await msc.classify_market_state(features_df)

            # 4. Price Prediction / Decision-Making
            print("Step 4: Price Prediction")
            ppa = PricePredictionAgent()
            prediction_result = ppa.run(features_df, market_state, method='llm' if req.use_llm else 'ml')
            # Validate prediction result 
            prediction_result = validate_prediction_result(features_df, prediction_result)

            # 5. Risk Management
            print("Step 5: Risk Management")
            rma = RiskManagementAgent()
            trade_params, _ = await rma.account_risk_managament(db, features_df, prediction_result, req.trader_account_id)
            account_state = await TraderAccountService.get_account_state(db, req.trader_account_id)
            risk_result = rma.run(trade_params, account_state)
            break  # Only need one db session

        print(f"Risk result: {risk_result}")
        units = req.units if req.units is not None else risk_result['position_size']

        # Only return analysis, do not execute trade
        result = _format_pipeline_analysis_result(market_df, features_df, market_state, prediction_result, risk_result)
        # Add confidence threshold to the result
        result['confidence_threshold'] = getattr(req, 'confidence_threshold', 0.7)
        print("Pipeline completed successfully")
        return result
        
    except Exception as e:
        print(f"Pipeline error: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backtest/run")
async def run_backtest(request: BacktestRequest):
    """
    Run a comprehensive backtest on historical data.
    """
    try:
        # Create new backtesting engine instance
        engine = BacktestingEngine(initial_balance=request.initial_balance)
        
        # Run backtest
        result = engine.run_backtest(
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            timeframe=request.timeframe,
            use_llm=request.use_llm,
            confidence_threshold=request.confidence_threshold
        )
        
        # Generate performance report
        report = generate_performance_report(result)
        
        return {
            "status": "success",
            "backtest_result": {
                "total_trades": result.total_trades,
                "winning_trades": result.winning_trades,
                "losing_trades": result.losing_trades,
                "win_rate": result.win_rate,
                "total_pnl": result.total_pnl,
                "total_pnl_pct": result.total_pnl_pct,
                "profit_factor": result.profit_factor,
                "sharpe_ratio": result.sharpe_ratio,
                "max_drawdown": result.max_drawdown,
                "calmar_ratio": result.calmar_ratio,
                "avg_trade_duration": result.avg_trade_duration,
                "best_trade": result.best_trade,
                "worst_trade": result.worst_trade,
                "avg_win": result.avg_win,
                "avg_loss": result.avg_loss
            },
            "performance_report": report,
            "equity_curve": result.equity_curve.to_dict('records') if not result.equity_curve.empty else [],
            "trades_summary": [
                {
                    "id": trade.id,
                    "symbol": trade.symbol,
                    "entry_time": trade.entry_time.isoformat() if trade.entry_time else None,
                    "exit_time": trade.exit_time.isoformat() if trade.exit_time else None,
                    "entry_price": trade.entry_price,
                    "exit_price": trade.exit_price,
                    "units": trade.units,
                    "direction": trade.direction,
                    "pnl": trade.pnl,
                    "pnl_pct": trade.pnl_pct,
                    "confidence": trade.confidence,
                    "market_regime": trade.market_regime,
                    "strategy": trade.strategy,
                    "status": trade.status.value
                }
                for trade in result.trades
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")


@router.post("/backtest/quick")
async def quick_backtest(
    symbol: str,
    days: int = 30,
    timeframe: str = "M1",
    confidence_threshold: float = 0.7
):
    """
    Run a quick backtest for the last N days.
    """
    try:
        result = run_quick_backtest(symbol, days, timeframe)
        
        return {
            "status": "success",
            "symbol": symbol,
            "days": days,
            "timeframe": timeframe,
            "backtest_result": {
                "total_trades": result.total_trades,
                "win_rate": result.win_rate,
                "total_pnl": result.total_pnl,
                "total_pnl_pct": result.total_pnl_pct,
                "profit_factor": result.profit_factor,
                "sharpe_ratio": result.sharpe_ratio,
                "max_drawdown": result.max_drawdown
            },
            "performance_report": generate_performance_report(result)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quick backtest failed: {str(e)}")


@router.post("/backtest/compare")
async def compare_backtest_strategies(
    symbol: str,
    start_date: str,
    end_date: str,
    strategies: List[Dict]
):
    """
    Compare multiple trading strategies.
    
    Args:
        symbol: Trading symbol
        start_date: Start date
        end_date: End date
        strategies: List of strategy configurations
    """
    try:
        results = compare_strategies(symbol, start_date, end_date, strategies)
        
        comparison = {}
        for strategy_name, result in results.items():
            comparison[strategy_name] = {
                "total_trades": result.total_trades,
                "win_rate": result.win_rate,
                "total_pnl": result.total_pnl,
                "total_pnl_pct": result.total_pnl_pct,
                "profit_factor": result.profit_factor,
                "sharpe_ratio": result.sharpe_ratio,
                "max_drawdown": result.max_drawdown,
                "calmar_ratio": result.calmar_ratio
            }
        
        return {
            "status": "success",
            "symbol": symbol,
            "period": f"{start_date} to {end_date}",
            "strategies_comparison": comparison
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Strategy comparison failed: {str(e)}")


@router.get("/backtest/performance")
async def get_performance_summary():
    """
    Get a summary of all backtest runs.
    """
    try:
        summary = backtest_engine.get_performance_summary()
        return {
            "status": "success",
            "performance_summary": summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance summary: {str(e)}")


@router.post("/monitoring/start")
async def start_live_monitoring(
    symbol: str,
    timeframe: str = "M1",
    confidence_threshold: float = 0.7
):
    """
    Start live monitoring of the trading pipeline.
    """
    try:
        backtest_engine.start_live_monitoring(symbol, timeframe, confidence_threshold)
        return {
            "status": "success",
            "message": f"Live monitoring started for {symbol}",
            "symbol": symbol,
            "timeframe": timeframe,
            "confidence_threshold": confidence_threshold
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start monitoring: {str(e)}")


@router.post("/monitoring/stop")
async def stop_live_monitoring():
    """
    Stop live monitoring.
    """
    try:
        backtest_engine.stop_live_monitoring()
        return {
            "status": "success",
            "message": "Live monitoring stopped"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop monitoring: {str(e)}")


@router.get("/monitoring/status")
async def get_monitoring_status():
    """
    Get current monitoring status.
    """
    return {
        "status": "success",
        "monitoring_active": backtest_engine.live_monitoring,
        "current_balance": backtest_engine.current_balance,
        "open_trades": len([t for t in backtest_engine.trades if t.status.value == "open"])
    }


@router.post("/pipeline/execute-trade")
async def pipeline_execute_trade(req: FullPipelineRequest):
    """Executes a trade with parameters sent from the frontend only."""
    from src.database import get_db
    from sqlalchemy.ext.asyncio import AsyncSession
    from src.users.trader_account_service import TraderAccountService

    try:
        # Fetch Oanda credentials for the trader account
        async for db in get_db():
            api_token, oanda_account_id, oanda_api_url, account_type = await TraderAccountService.get_oanda_credentials_by_account_id(db, req.trader_account_id)
            break
        if not api_token or not oanda_account_id:
            raise HTTPException(status_code=400, detail="Oanda credentials not found for this account.")
        oanda_service = OandaApiService(api_token=api_token, account_id=oanda_account_id, oanda_api_url=oanda_api_url, account_type=account_type)

        trade_result = oanda_service.place_trade(
            symbol=req.symbol,
            units=req.units,
            take_profit=req.tp,
            stop_loss=req.sl
        )
        
        # Analyze Oanda response for execution status
        status = "unknown"
        message = ""
        oanda_order_id = None
        oanda_position_id = None
        
        if "orderFillTransaction" in trade_result:
            status = "success"
            message = "Trade executed successfully."
            # Extract order and position IDs from successful trade
            order_fill = trade_result["orderFillTransaction"]
            oanda_order_id = order_fill.get("id")
            oanda_position_id = order_fill.get("positionID")
            
            # Log the trade to our database
            try:
                async for db in get_db():
                    trade_data = TraderAccountsTradesCreate(
                        trader_account_id=req.trader_account_id,
                        symbol=req.symbol,
                        trade_type="buy" if req.units > 0 else "sell",
                        units=abs(req.units),
                        entry_price=req.price or 0,
                        stop_loss=req.sl,
                        take_profit=req.tp,
                        oanda_order_id=str(oanda_order_id) if oanda_order_id else None,
                        oanda_position_id=str(oanda_position_id) if oanda_position_id else None
                    )
                    
                    logged_trade = await TraderAccountsTradesService.create_trade(db, trade_data)
                    print(f"Trade logged successfully with ID: {logged_trade.id}")
                    break
            except Exception as db_error:
                print(f"Failed to log trade to database: {db_error}")
                # Don't fail the trade execution if logging fails
                
        elif "orderCancelTransaction" in trade_result:
            status = "cancelled"
            reason = trade_result["orderCancelTransaction"].get("reason", "Order was cancelled.")
            message = f"Trade was cancelled: {reason}"
        elif "orderRejectTransaction" in trade_result:
            status = "rejected"
            reason = trade_result["orderRejectTransaction"].get("rejectReason", "Order was rejected.")
            message = f"Trade was rejected: {reason}"
        else:
            message = "Unknown trade response."
            
        return {
            'status': status,
            'message': message,
            'trade_execution': trade_result,
            'logged_trade_id': logged_trade.id if status == "success" and 'logged_trade' in locals() else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 


def _format_pipeline_analysis_result(market_df, features_df, market_state, prediction_result, risk_result):
    import numpy as np
    import pandas as pd
    # Format the data for frontend display
    market_data_for_frontend = market_df.tail(5).copy()
    features_data_for_frontend = features_df.tail(5).copy()
    
    # Convert time to readable format
    if 'time' in market_data_for_frontend.columns:
        market_data_for_frontend['time'] = pd.to_datetime(market_data_for_frontend['time']).dt.strftime('%H:%M:%S')
    if 'time' in features_data_for_frontend.columns:
        features_data_for_frontend['time'] = pd.to_datetime(features_data_for_frontend['time']).dt.strftime('%H:%M:%S')
    
    # Replace NaN values with 0 for JSON serialization
    market_data_for_frontend = market_data_for_frontend.replace([np.inf, -np.inf], np.nan).fillna(0)
    features_data_for_frontend = features_data_for_frontend.replace([np.inf, -np.inf], np.nan).fillna(0)
    
    # Convert numpy types to Python types for JSON serialization 
    def convert_numpy_types(obj):
        if isinstance(obj, dict):
            return {k: convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy_types(v) for v in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj
    
    result = {
        'data_acquisition': convert_numpy_types(market_data_for_frontend.to_dict()),
        'feature_engineering': convert_numpy_types(features_data_for_frontend.to_dict()),
        'market_state': market_state,
        'prediction': convert_numpy_types(prediction_result),
        'risk_management': convert_numpy_types(risk_result),
        'decision_reason': prediction_result.get('reason', None)
    }
    return result 