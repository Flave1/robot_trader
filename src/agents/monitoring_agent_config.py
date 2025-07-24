import yaml
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
import os

class OpportunityCriteria(BaseModel):
    min_expected_return_pct: float = 0.2
    min_confidence: float = 0.7
    max_volatility: float = 0.05

class NotificationPreferences(BaseModel):
    email: Optional[str]
    dashboard: bool = True
    sms: bool = False

class MonitoringAgentConfig(BaseModel):
    symbols: List[str]
    trader_account_id: int
    timeframe: str = 'M1'
    confidence_threshold: float = 0.7
    initial_balance: float = 10000.0
    risk_pct: float = 0.01
    max_drawdown: float = 0.2
    max_trades: int = 5
    use_llm: bool = True
    units: Optional[float] = None
    opportunity_criteria: OpportunityCriteria = OpportunityCriteria()
    notification_preferences: NotificationPreferences = NotificationPreferences()


def load_monitoring_agent_config(yaml_path: str = None) -> MonitoringAgentConfig:
    if yaml_path is None:
        yaml_path = os.path.join(os.path.dirname(__file__), '../config/monitoring_agent_config.yaml')
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)
    return MonitoringAgentConfig(**data) 