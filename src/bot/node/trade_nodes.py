from src.bot.custom_types import ActiveTradesInput
from src.bot.tools.common_tools import get_active_trades_tool
from src.bot.tools.trading_tools import (
    list_orders_tool, get_order_tool, cancel_order_tool, replace_order_tool,
    create_order_tool, trade_execution_tool, list_trades_tool, get_trade_tool,
    close_trade_tool, update_trade_orders_tool, get_active_positions_tool
)
from src.bot.utils import extract_nested_fields
from langgraph.types import StreamWriter
from langgraph.prebuilt.tool_node import ToolMessage
from typing import Dict, Any

# ============================================================================
# ORDER MANAGEMENT NODES
# ============================================================================

async def list_orders_node(input: Dict[str, Any], writer: StreamWriter):
    """
    Node for listing orders with filtering options.
    """
    extracted = extract_nested_fields(input, ['trader_account_id', 'state', 'count', 'instrument', 'id'])
    trader_account_id = extracted.get('trader_account_id')
    state = extracted.get('state', 'PENDING')
    count = extracted.get('count', 50)
    instrument = extracted.get('instrument')
    tool_call_id = extracted.get('id')

    if not trader_account_id:
        return {
            "messages": [
                ToolMessage(content=f"Missing required field: trader_account_id={trader_account_id}", tool_call_id=tool_call_id)
            ]
        }

    tool_input = {
        'trader_account_id': trader_account_id,
        'state': state,
        'count': count
    }
    if instrument:
        tool_input['instrument'] = instrument

    result = list_orders_tool(tool_input)
    writer({"feedback_state": [{"feedback": result, "state": f"Listing orders for account {trader_account_id}"}]})

    content = {"type": "json", "orders_result": result}
    return {
        "messages": [ToolMessage(content=content, tool_call_id=tool_call_id)],
        "orders": [result]
    }

async def get_order_node(input: Dict[str, Any], writer: StreamWriter):
    """
    Node for getting specific order details.
    """
    extracted = extract_nested_fields(input, ['trader_account_id', 'order_id', 'id'])
    trader_account_id = extracted.get('trader_account_id')
    order_id = extracted.get('order_id')
    tool_call_id = extracted.get('id')

    if not trader_account_id or not order_id:
        return {
            "messages": [
                ToolMessage(content=f"Missing required fields: trader_account_id={trader_account_id}, order_id={order_id}", tool_call_id=tool_call_id)
            ]
        }

    tool_input = {
        'trader_account_id': trader_account_id,
        'order_id': order_id
    }

    result = get_order_tool(tool_input)
    writer({"feedback_state": [{"feedback": result, "state": f"Getting order {order_id}"}]})

    content = {"type": "json", "order_result": result}
    return {
        "messages": [ToolMessage(content=content, tool_call_id=tool_call_id)],
        "order": [result]
    }

async def cancel_order_node(input: Dict[str, Any], writer: StreamWriter):
    """
    Node for canceling a specific order.
    """
    extracted = extract_nested_fields(input, ['trader_account_id', 'order_id', 'id'])
    trader_account_id = extracted.get('trader_account_id')
    order_id = extracted.get('order_id')
    tool_call_id = extracted.get('id')

    if not trader_account_id or not order_id:
        return {
            "messages": [
                ToolMessage(content=f"Missing required fields: trader_account_id={trader_account_id}, order_id={order_id}", tool_call_id=tool_call_id)
            ]
        }

    tool_input = {
        'trader_account_id': trader_account_id,
        'order_id': order_id
    }

    result = cancel_order_tool(tool_input)
    writer({"feedback_state": [{"feedback": result, "state": f"Canceling order {order_id}"}]})

    content = {"type": "json", "cancel_result": result}
    return {
        "messages": [ToolMessage(content=content, tool_call_id=tool_call_id)],
        "order_cancellation": [result]
    }

async def replace_order_node(input: Dict[str, Any], writer: StreamWriter):
    """
    Node for replacing an existing order.
    """
    extracted = extract_nested_fields(input, ['trader_account_id', 'order_id', 'new_order_data', 'id'])
    trader_account_id = extracted.get('trader_account_id')
    order_id = extracted.get('order_id')
    new_order_data = extracted.get('new_order_data')
    tool_call_id = extracted.get('id')

    if not trader_account_id or not order_id or not new_order_data:
        return {
            "messages": [
                ToolMessage(content=f"Missing required fields: trader_account_id={trader_account_id}, order_id={order_id}, new_order_data={new_order_data}", tool_call_id=tool_call_id)
            ]
        }

    tool_input = {
        'trader_account_id': trader_account_id,
        'order_id': order_id,
        'new_order_data': new_order_data
    }

    result = replace_order_tool(tool_input)
    writer({"feedback_state": [{"feedback": result, "state": f"Replacing order {order_id}"}]})

    content = {"type": "json", "replace_result": result}
    return {
        "messages": [ToolMessage(content=content, tool_call_id=tool_call_id)],
        "order_replacement": [result]
    }

async def create_order_node(input: Dict[str, Any], writer: StreamWriter):
    """
    Node for creating new orders (market, limit, or stop).
    """
    extracted = extract_nested_fields(input, [
        'trader_account_id', 'symbol', 'units', 'order_type', 'price', 
        'take_profit', 'stop_loss', 'id'
    ])
    trader_account_id = extracted.get('trader_account_id')
    symbol = extracted.get('symbol')
    units = extracted.get('units')
    order_type = extracted.get('order_type', 'MARKET')
    price = extracted.get('price')
    take_profit = extracted.get('take_profit')
    stop_loss = extracted.get('stop_loss')
    tool_call_id = extracted.get('id')

    if not trader_account_id or not symbol or units is None:
        return {
            "messages": [
                ToolMessage(content=f"Missing required fields: trader_account_id={trader_account_id}, symbol={symbol}, units={units}", tool_call_id=tool_call_id)
            ]
        }

    tool_input = {
        'trader_account_id': trader_account_id,
        'symbol': symbol,
        'units': units,
        'order_type': order_type
    }
    
    if price is not None:
        tool_input['price'] = price
    if take_profit is not None:
        tool_input['take_profit'] = take_profit
    if stop_loss is not None:
        tool_input['stop_loss'] = stop_loss

    result = create_order_tool(tool_input)
    writer({"feedback_state": [{"feedback": result, "state": f"Creating {order_type} order for {symbol}"}]})

    content = {"type": "json", "order_creation_result": result}
    return {
        "messages": [ToolMessage(content=content, tool_call_id=tool_call_id)],
        "order_creation": [result]
    }

async def trade_execution_node(input: Dict[str, Any], writer: StreamWriter):
    """
    Node for executing market trades (legacy compatibility).
    """
    extracted = extract_nested_fields(input, [
        'trader_account_id', 'symbol', 'units', 'take_profit', 'stop_loss', 'id'
    ])
    trader_account_id = extracted.get('trader_account_id')
    symbol = extracted.get('symbol')
    units = extracted.get('units')
    take_profit = extracted.get('take_profit')
    stop_loss = extracted.get('stop_loss')
    tool_call_id = extracted.get('id')

    if not trader_account_id or not symbol or units is None:
        return {
            "messages": [
                ToolMessage(content=f"Missing required fields: trader_account_id={trader_account_id}, symbol={symbol}, units={units}", tool_call_id=tool_call_id)
            ]
        }

    tool_input = {
        'trader_account_id': trader_account_id,
        'symbol': symbol,
        'units': units
    }
    
    if take_profit is not None:
        tool_input['take_profit'] = take_profit
    if stop_loss is not None:
        tool_input['stop_loss'] = stop_loss

    result = trade_execution_tool(tool_input)
    writer({"feedback_state": [{"feedback": result, "state": f"Executing market trade for {symbol}"}]})

    content = {"type": "json", "trade_execution_result": result}
    return {
        "messages": [ToolMessage(content=content, tool_call_id=tool_call_id)],
        "trade_execution": [result]
    }

# ============================================================================
# POSITION/TRADE MANAGEMENT NODES
# ============================================================================

async def list_trades_node(input: Dict[str, Any], writer: StreamWriter):
    """
    Node for listing trades with filtering options.
    """
    extracted = extract_nested_fields(input, ['trader_account_id', 'state', 'count', 'instrument', 'id'])
    trader_account_id = extracted.get('trader_account_id')
    state = extracted.get('state', 'OPEN')
    count = extracted.get('count', 50)
    instrument = extracted.get('instrument')
    tool_call_id = extracted.get('id')

    if not trader_account_id:
        return {
            "messages": [
                ToolMessage(content=f"Missing required field: trader_account_id={trader_account_id}", tool_call_id=tool_call_id)
            ]
        }

    tool_input = {
        'trader_account_id': trader_account_id,
        'state': state,
        'count': count
    }
    if instrument:
        tool_input['instrument'] = instrument

    result = list_trades_tool(tool_input)
    writer({"feedback_state": [{"feedback": result, "state": f"Listing trades for account {trader_account_id}"}]})

    content = {"type": "json", "trades_result": result}
    return {
        "messages": [ToolMessage(content=content, tool_call_id=tool_call_id)],
        "trades": [result]
    }

async def get_trade_node(input: Dict[str, Any], writer: StreamWriter):
    """
    Node for getting specific trade details.
    """
    extracted = extract_nested_fields(input, ['trader_account_id', 'trade_id', 'id'])
    trader_account_id = extracted.get('trader_account_id')
    trade_id = extracted.get('trade_id')
    tool_call_id = extracted.get('id')

    if not trader_account_id or not trade_id:
        return {
            "messages": [
                ToolMessage(content=f"Missing required fields: trader_account_id={trader_account_id}, trade_id={trade_id}", tool_call_id=tool_call_id)
            ]
        }

    tool_input = {
        'trader_account_id': trader_account_id,
        'trade_id': trade_id
    }

    result = get_trade_tool(tool_input)
    writer({"feedback_state": [{"feedback": result, "state": f"Getting trade {trade_id}"}]})

    content = {"type": "json", "trade_result": result}
    return {
        "messages": [ToolMessage(content=content, tool_call_id=tool_call_id)],
        "trade": [result]
    }

async def close_trade_node(input: Dict[str, Any], writer: StreamWriter):
    """
    Node for closing trades (partial or full).
    """
    extracted = extract_nested_fields(input, ['trader_account_id', 'trade_id', 'units', 'id'])
    trader_account_id = extracted.get('trader_account_id')
    trade_id = extracted.get('trade_id')
    units = extracted.get('units', 'ALL')
    tool_call_id = extracted.get('id')

    if not trader_account_id or not trade_id:
        return {
            "messages": [
                ToolMessage(content=f"Missing required fields: trader_account_id={trader_account_id}, trade_id={trade_id}", tool_call_id=tool_call_id)
            ]
        }

    tool_input = {
        'trader_account_id': trader_account_id,
        'trade_id': trade_id,
        'units': units
    }

    result = close_trade_tool(tool_input)
    writer({"feedback_state": [{"feedback": result, "state": f"Closing trade {trade_id}"}]})

    content = {"type": "json", "close_result": result}
    return {
        "messages": [ToolMessage(content=content, tool_call_id=tool_call_id)],
        "trade_closure": [result]
    }

async def update_trade_orders_node(input: Dict[str, Any], writer: StreamWriter):
    """
    Node for setting or updating stop loss and take profit for trades.
    """
    extracted = extract_nested_fields(input, ['trader_account_id', 'trade_id', 'stop_loss', 'take_profit', 'id'])
    trader_account_id = extracted.get('trader_account_id')
    trade_id = extracted.get('trade_id')
    stop_loss = extracted.get('stop_loss')
    take_profit = extracted.get('take_profit')
    tool_call_id = extracted.get('id')

    if not trader_account_id or not trade_id:
        return {
            "messages": [
                ToolMessage(content=f"Missing required fields: trader_account_id={trader_account_id}, trade_id={trade_id}", tool_call_id=tool_call_id)
            ]
        }

    tool_input = {
        'trader_account_id': trader_account_id,
        'trade_id': trade_id
    }
    
    if stop_loss is not None:
        tool_input['stop_loss'] = stop_loss
    if take_profit is not None:
        tool_input['take_profit'] = take_profit

    result = update_trade_orders_tool(tool_input)
    writer({"feedback_state": [{"feedback": result, "state": f"Updating trade orders for {trade_id}"}]})

    content = {"type": "json", "update_result": result}
    return {
        "messages": [ToolMessage(content=content, tool_call_id=tool_call_id)],
        "trade_orders_update": [result]
    }

# async def get_active_positions_node(input: Dict[str, Any], writer: StreamWriter):
#     """
#     Node for getting all active positions for a trader account.
#     """
#     extracted = extract_nested_fields(input, ['trader_account_id', 'id'])
#     trader_account_id = extracted.get('trader_account_id')
#     tool_call_id = extracted.get('id')

#     if not trader_account_id:
#         return {
#             "messages": [
#                 ToolMessage(content=f"Missing required field: trader_account_id={trader_account_id}", tool_call_id=tool_call_id)
#             ]
#         }

#     tool_input = {
#         'trader_account_id': trader_account_id
#     }

#     result = get_active_positions_tool(tool_input)
#     writer({"feedback_state": [{"feedback": result, "state": f"Getting active positions for account {trader_account_id}"}]})

#     content = {"type": "json", "positions_result": result}
#     return {
    #     "messages": [ToolMessage(content=content, tool_call_id=tool_call_id)],
    #     "active_positions": [result]
    # }

async def get_active_positions_node(input: ActiveTradesInput, writer: StreamWriter):
    extracted = extract_nested_fields(input, ['trader_account_id', 'id'])
    trader_account_id = extracted.get('trader_account_id')
    tool_call_id = extracted.get('id')

    if not trader_account_id:
        return {
            "messages": [ToolMessage(content="trader_account_id required", tool_call_id=tool_call_id)]
        }
    active_trades = get_active_trades_tool({'trader_account_id': trader_account_id})
    writer({"feedback_state": [
        {"feedback": f"Retrieved {len(active_trades) if isinstance(active_trades, list) else 0} active trades", "state": f"Fetching active trades for account {trader_account_id}"}
    ]})
    return {"messages": [ToolMessage(content={"type": "json", "data": active_trades}, tool_call_id=tool_call_id)], 
            "feedback_state": [{"feedback": "Fetched Active trades", "search_status": "", "result": active_trades}]}
