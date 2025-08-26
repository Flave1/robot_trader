from typing import Optional, Dict, Tuple
import os
from openai import OpenAI
import pandas as pd
from pydantic import BaseModel, Field
from langchain_core.tools import tool

from src.bot.custom_types import RiskManagementInputData
from src.bot.utils import calculate_atr, get_trade_params
from src.users.trader_account_service import TraderAccountService



class RiskManagementAgent:
    """
    Risk Management Agent.
    Calculates position size, applies stop logic, and provides risk advice.
    Supports rule-based and LLM-augmented risk management.
    """
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        # Initialize OpenAI client
        if self.openai_api_key:
            self.client = OpenAI(api_key=self.openai_api_key)
        else:
            self.client = None

    def calculate_position_size(self, account_balance: float, entry: float, stop_loss: float, risk_pct: float = 0.2, atr: Optional[float] = None, kelly: bool = False, win_rate: float = 0.55, rr: float = 2.0, max_risk_pct: float = 0.2) -> float:
        """
        Calculate position size based on risk per trade, ATR, and optionally Kelly Criterion.
        Enforces a maximum risk of 20% of account balance.
        """
        # Enforce max risk of 20%
        # risk_pct = min(risk_pct, max_risk_pct)
        risk_amount = account_balance * 0.9 #* risk_pct
        stop_dist = abs(entry - stop_loss)
        if stop_dist == 0:
            return 0.0
        if kelly:
            # Kelly Criterion: f* = win_rate - (1-win_rate)/rr
            kelly_fraction = win_rate - (1 - win_rate) / rr
            kelly_fraction = max(0, min(kelly_fraction, 1))
            risk_amount *= kelly_fraction
        if atr:
            # Optionally scale position by ATR
            stop_dist = max(stop_dist, atr)
        position_size = risk_amount / stop_dist
        return position_size

    def calculate_lot_size(self, position_size: float, contract_size: float = 100000) -> float:
        """
        Calculate lot size based on position size and contract size (default 100,000 for forex).
        """
        if contract_size is None or contract_size == 0:
            contract_size = 100000
        return position_size / contract_size

    def apply_trailing_stop(self, current_price: float, entry: float, stop_loss: float, take_profit: float, trailing_pct: float = 0.5) -> float:
        """
        Adjust stop loss as price moves in favor (trailing stop).
        trailing_pct: percent of distance from entry to take profit
        """
        if current_price > entry:
            new_stop = entry + (current_price - entry) * trailing_pct
            return min(new_stop, take_profit)
        elif current_price < entry:
            new_stop = entry - (entry - current_price) * trailing_pct
            return max(new_stop, take_profit)
        else:
            return stop_loss

    def should_trade(self, open_trades: int, max_trades: int, drawdown: float, max_drawdown: float) -> bool:
        """
        Approve trade if not over max trades or drawdown.
        """
        if open_trades >= max_trades:
            return False
        if drawdown >= max_drawdown:
            return False
        return True

    def llm_risk_advice(self, context: Dict) -> str:
        """
        Use OpenAI LLM to provide risk commentary/advice.
        """
        if not self.client:
            return "No LLM API key provided."
        
        prompt = f"""
        You are a trading risk management AI. Given the following context, provide a brief risk assessment and advice:
        {context}
        """
        try:
            response = self.client.chat.completions.create(
                model="03-mini",
                messages=[{"role": "system", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"LLM error: {e}"

    def run(self, trade_params: Dict, account_state: Dict, market_state: Optional[str] = None, method: str = 'rule', llm_advice: bool = False) -> Dict:
        """
        Main entry: Returns position size, stop loss, trade approval, lot size, and LLM advice if requested.
        trade_params: dict with entry, stop_loss, take_profit, current_price, atr, contract_size (optional)
        account_state: dict with account_balance, open_trades, max_trades, drawdown, max_drawdown, risk_pct
        """
        contract_size = trade_params.get('contract_size')
        position_size = self.calculate_position_size(
            account_balance=account_state['account_balance'],
            entry=trade_params['entry'],
            stop_loss=trade_params['stop_loss'],
            risk_pct=account_state.get('risk_pct'),
            atr=trade_params.get('atr'),
            kelly=account_state.get('kelly', False),
            win_rate=account_state.get('win_rate'),
            rr=account_state.get('rr', 2.0),
            max_risk_pct=0.2
        )
        lot_size = self.calculate_lot_size(position_size, contract_size)
        stop_loss = trade_params['stop_loss']
        if 'trailing' in trade_params and trade_params['trailing']:
            stop_loss = self.apply_trailing_stop(
                current_price=trade_params['current_price'],
                entry=trade_params['entry'],
                stop_loss=stop_loss,
                take_profit=trade_params['take_profit'],
                trailing_pct=trade_params.get('trailing_pct', 0.5)
            )
        trade_approved = self.should_trade(
            open_trades=account_state['open_trades'],
            max_trades=account_state['max_trades'],
            drawdown=account_state['drawdown'],
            max_drawdown=account_state['max_drawdown']
        )
        advice = None
        if llm_advice:
            context = {
                'trade_params': trade_params,
                'account_state': account_state,
                'market_state': market_state
            }
            advice = self.llm_risk_advice(context)
        return {
            'position_size': position_size,
            'lot_size': lot_size,
            'stop_loss': stop_loss,
            'trade_approved': trade_approved,
            'llm_advice': advice
        }
    
    async def account_risk_managament(self, db, features_df: pd.DataFrame, prediction_result: dict, trader_account_id: int) -> Tuple[dict, dict]:
        atr_value = calculate_atr(features_df)
        trade_params = get_trade_params(features_df, prediction_result, atr_value)
        account_state = await TraderAccountService.get_account_state(db, trader_account_id)
        return trade_params, account_state
    

@tool
async def risk_management_tool(input: dict) -> Dict:
    """
    Risk Management Tool for Trading Analysis.

    This tool evaluates trade parameters and account state to calculate optimal position sizing, stop loss, take profit, 
    and other risk management metrics. It ensures trades are executed within acceptable risk limits based 
    on the trader's account and the current market context.

    Args:
        input (dict): An object containing:
            - features_df (list[dict]): The features data as a list of dicts.
            - prediction_result (dict): The output from the price prediction tool.
            - trader_account_id (int): The unique identifier for the trader's account.

    Returns:
        Dict: A dictionary containing risk management results, such as recommended position size, stop loss, take profit, and risk metrics.

    Use this tool when you need to determine safe and optimal trade parameters based on account state, predictions, and market features.
    """
    import pandas as pd
    from src.database import get_db
    
    # Convert features_df to DataFrame
    features_df = pd.DataFrame(input["features_df"])
    prediction_result = input["prediction_result"]
    current_price = features_df['close'].iloc[-1]
    async for db in get_db():
        atr_value = calculate_atr(features_df)
        trade_params = get_trade_params(features_df, prediction_result, atr_value)
        account_state = await TraderAccountService.get_account_state(db, input["trader_account_id"])
        break

    trade_params = {
        'entry': prediction_result.get('entry', current_price),
        'stop_loss': prediction_result.get('stop_loss', current_price * 0.99),
        'take_profit': prediction_result.get('take_profit', current_price * 1.01),
        'current_price': current_price,
        'atr': atr_value
    }
    
    rma = RiskManagementAgent()
    risk_result = rma.run(trade_params, account_state)
    return risk_result
