import asyncio
from typing import List, Dict, Any, Optional
from .monitoring_agent_config import load_monitoring_agent_config, MonitoringAgentConfig
from src.bot.custom_types import FullPipelineRequest
from src.agents.dap import DataAcquisitionProcessor
from src.agents.laa import FeatureEngineeringAgent
from src.agents.msc import MarketStateClassifier
from src.agents.pp import PricePredictionAgent
from src.agents.rm import RiskManagementAgent
from src.users.trader_account_service import TraderAccountService
from src.bot.utils import validate_prediction_result
import os

class MonitoringAgentOrchestrator:
    def __init__(self, config: Optional[MonitoringAgentConfig] = None, config_path: Optional[str] = None):
        """
        Orchestrator for the ARBIX Monitoring Agent.
        Loads configuration from YAML by default. To customize, edit backend/config/monitoring_agent_config.yaml.
        """
        if config is None:
            config = load_monitoring_agent_config(config_path)
        self.config = config
        self.symbols = config.symbols
        self.trader_account_id = config.trader_account_id
        self.timeframe = config.timeframe
        self.confidence_threshold = config.confidence_threshold
        self.initial_balance = config.initial_balance
        self.risk_pct = config.risk_pct
        self.use_llm = config.use_llm
        self.units = config.units
        self.max_drawdown = config.max_drawdown
        self.max_trades = config.max_trades
        self.opportunity_criteria = config.opportunity_criteria
        self.notification_preferences = config.notification_preferences

    async def run_pipeline_for_symbol(self, symbol: str) -> Dict[str, Any]:
        from src.database import get_db
        try:
            async for db in get_db():
                # Data Acquisition
                market_df, news_df = await DataAcquisitionProcessor.initialize_dap(db, FullPipelineRequest(
                    symbol=symbol,
                    timeframe=self.timeframe,
                    trader_account_id=self.trader_account_id,
                    account_balance=self.initial_balance,
                    risk_pct=self.risk_pct,
                    units=self.units or 0,
                    sl=0, tp=0, price=0, retries=3, use_llm=self.use_llm
                ))
                # Feature Engineering
                fea = FeatureEngineeringAgent()
                features_df = fea.engineer_features(market_df, news_df, self.timeframe)
                # Market State Classification
                msc = MarketStateClassifier()
                market_state = await msc.classify_market_state(features_df)
                # Price Prediction
                ppa = PricePredictionAgent()
                prediction_result = ppa.run(features_df, market_state, method='llm' if self.use_llm else 'ml')
                prediction_result = validate_prediction_result(features_df, prediction_result)
                # Risk Management
                rma = RiskManagementAgent()
                trade_params, account_state = await rma.account_risk_managament(db, features_df, prediction_result, self.trader_account_id)
                risk_result = rma.run(trade_params, account_state)
                break
            units = self.units if self.units is not None else risk_result['position_size']
            return {
                'symbol': symbol,
                'market_data': market_df.tail(5).to_dict(),
                'features': features_df.tail(5).to_dict(),
                'market_state': market_state,
                'prediction': prediction_result,
                'risk': risk_result,
                'units': units,
                'confidence_threshold': self.confidence_threshold,
                'opportunity_criteria': self.opportunity_criteria.dict(),
                'notification_preferences': self.notification_preferences.dict()
            }
        except Exception as e:
            return {'symbol': symbol, 'error': str(e)}

    async def run(self) -> List[Dict[str, Any]]:
        tasks = [self.run_pipeline_for_symbol(symbol) for symbol in self.symbols]
        results = await asyncio.gather(*tasks)
        return results

# Usage:
# 1. Edit backend/config/monitoring_agent_config.yaml to customize currencies, risk, and preferences.
# 2. Run the orchestrator:
#    from backend.src.agents.monitoring_agent_orchestrator import MonitoringAgentOrchestrator
#    orchestrator = MonitoringAgentOrchestrator()
#    results = asyncio.run(orchestrator.run())
#    print(results) 