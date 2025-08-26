from typing import Dict, Any
from src.bot.custom_types import FullPipelineRequest
from src.agents.dap import DataAcquisitionProcessor
from src.agents.laa import FeatureEngineeringAgent
from src.agents.msc import MarketStateClassifier
from src.agents.pp import PricePredictionAgent
from src.agents.rm import RiskManagementAgent
from src.bot.utils import validate_prediction_result
from langchain_core.tools import tool

@tool
async def full_pipeline_tool(input: dict) -> Dict[str, Any]:
    """
    Full Pipeline Tool for ARBIX Monitoring Agent.
    Runs the complete analysis and trade decision pipeline for a single symbol and trader account.

    Args:
        input (dict): An object containing the following fields:
            - symbol (str): The trading symbol (e.g., 'EUR_USD').
            - timeframe (str): The timeframe for the data (e.g., 'M1', 'H1').
            - trader_account_id (int): The account ID for the trader.

    Returns:
        dict: Pipeline result including market data, features, market state, prediction, risk, and units.
    """
    from src.database import get_db
    # Extract and validate parameters
    symbol = input['symbol']
    timeframe = input['timeframe']
    trader_account_id = input['trader_account_id']
    if not symbol or not timeframe or trader_account_id is None:
        return {'error': 'Missing required fields: symbol, timeframe, and trader_account_id are required.'}
    # Set all other parameters to sensible defaults

    print("inputed_data", input)
    account_balance = 10000.0
    risk_pct = 0.01
    units = None
    use_llm = True
    sl = 0
    tp = 0
    price = 0
    retries = 3
    try:
        async for db in get_db():
            # Data Acquisition
            market_df, news_df = await DataAcquisitionProcessor.initialize_dap(db, FullPipelineRequest(
                symbol=symbol,
                timeframe=timeframe,
                trader_account_id=trader_account_id,
                account_balance=account_balance,
                risk_pct=risk_pct,
                units=units or 0,
                sl=sl, tp=tp, price=price, retries=retries, use_llm=use_llm
            ))
            # Feature Engineering
            fea = FeatureEngineeringAgent()
            features_df = fea.engineer_features(market_df, news_df, timeframe)
            # Market State Classification
            msc = MarketStateClassifier()
            market_state = await msc.classify_market_state(features_df)
            # Price Prediction
            ppa = PricePredictionAgent()
            prediction_result = ppa.run(features_df, market_state, method='llm' if use_llm else 'ml')
            prediction_result = validate_prediction_result(features_df, prediction_result)
            # Risk Management
            rma = RiskManagementAgent()
            trade_params, account_state = await rma.account_risk_managament(db, features_df, prediction_result, trader_account_id)
            risk_result = rma.run(trade_params, account_state)
            break
        units_final = units if units is not None else risk_result['position_size']
        return {
            'symbol': symbol,
            'market_data': market_df.tail(5).to_dict(),
            'features': features_df.tail(5).to_dict(),
            'market_state': market_state,
            'prediction': prediction_result,
            'risk': risk_result,
            'units': units_final,
            'confidence_threshold': 0.7  # default, can be parameterized
        }
    except Exception as e:
        return {'symbol': symbol, 'error': str(e)} 