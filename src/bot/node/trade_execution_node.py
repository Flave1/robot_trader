from src.bot.tools.trade_execution_tool import trade_execution_tool
from langgraph.types import StreamWriter

async def trade_execution_node(input: dict, writer: StreamWriter):
    # Extract required fields
    params = {
        'trader_account_id': input.get('trader_account_id'),
        'symbol': input.get('symbol'),
        'units': input.get('units'),
        'entry': input.get('entry'),
        'stop_loss': input.get('stop_loss'),
        'take_profit': input.get('take_profit'),
        'action': input.get('action', 'buy')
    }
    result = trade_execution_tool(params)
    writer({"feedback_state": [{"feedback": result, "state": f"Trade execution for {params['symbol']}"}]})
    return {"messages": [result], "trade_execution": [result]} 