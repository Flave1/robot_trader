import json
from langgraph.types import StateSnapshot
import pandas as pd


def checkpoint_event(value):
    """Create a checkpoint event for the client."""

    def format_values(values: dict):
        formatted_values = values.copy()
        if "messages" in formatted_values:
            formatted_values["messages"] = [
                {
                    "type": msg.get("type") if isinstance(msg, dict) else msg.type,
                    "content": msg.get("content") if isinstance(msg, dict) else msg.content,
                    "id": msg.get("id") if isinstance(msg, dict) else msg.id,
                    "tool_calls": msg.get("tool_calls") if isinstance(msg, dict) else (msg.tool_calls if hasattr(msg, 'tool_calls') else None)
                }
                for msg in formatted_values["messages"]
            ]
        return formatted_values

    def format_writes(writes: dict):
        if writes is None:
            return None
        formatted_writes = {}
        for key, value in writes.items():
            if isinstance(value, dict):
                formatted_writes[key] = format_values(value)
            elif isinstance(value, list):
                formatted_writes[key] = [format_values(item) if isinstance(
                    item, dict) else item for item in value]
            else:
                formatted_writes[key] = value
        return formatted_writes

    configurable = value["payload"]["config"]["configurable"]
    data = {
        "next": value["payload"]["next"],
        "values": format_values(value["payload"]["values"]),
        "config": {
            "configurable": {
                "checkpoint_id": configurable["checkpoint_id"],
                "checkpoint_ns": configurable["checkpoint_ns"],
                "thread_id": configurable["thread_id"]
            }
        },
        "metadata": {
            "source": value["payload"]["metadata"]["source"],
            "step": value["payload"]["metadata"]["step"],
            "writes": format_writes(value["payload"]["metadata"]["writes"]),
            "parents": value["payload"]["metadata"]["parents"]
        }
    }
    return {
        "event": "checkpoint",
        "data": json.dumps(data)
    }


def message_chunk_event(node_name, message_chunk):
    """Create a message chunk event for the client."""

    def format_messages(value):
        """Format message chunk into a serializable dictionary. 
        This is needed because the message class is not serializable.
        """
        return {
            "content": value.content,
            "id": value.id,
            "tool_calls": value.tool_calls if hasattr(value, 'tool_calls') else None,
            "tool_call_chunks": value.tool_call_chunks if hasattr(value, 'tool_call_chunks') else None
        }

    return {
        "event": "message_chunk",
        "data": json.dumps({
            "node_name": node_name,
            "message_chunk": format_messages(message_chunk)
        })
    }


def interrupt_event(interrupts):
    """Create an interrupt event for the client."""
    formatted_interrupts = [{"value": interrupt["value"]}
                            for interrupt in interrupts]
    return {
        "event": "interrupt",
        "data": json.dumps(formatted_interrupts)
    }


def custom_event(value):
    """Create a custom event for the client."""
    return {
        "event": "custom",
        "data": json.dumps(value)
    }


def format_state_snapshot(snapshot: StateSnapshot):
    interrupts = []
    for task in snapshot.tasks:
        for interrupt in task.interrupts:
            interrupts.append({"value": interrupt.value})
    return {
        "values": snapshot.values,
        "next": snapshot.next,
        "config": snapshot.config,
        "interrupts": interrupts,
        "parent_config": snapshot.parent_config,
        "metadata": snapshot.metadata
    }

def calculate_atr(df: pd.DataFrame) -> float:
    try:
        atr_value = df['close'].rolling(window=14).std().iloc[-1]
        if pd.isna(atr_value) or atr_value == 0:
            atr_value = df['close'].iloc[-1] * 0.01  # 1% of current price as fallback
            return atr_value
    except Exception as e:
        print(f"ATR calculation failed: {e}, using fallback")
        atr_value = df['close'].iloc[-1] * 0.01
        return atr_value


def get_trade_params(features_df: pd.DataFrame, prediction_result: dict, atr_value: float) -> dict:
    trade_params = {
            'entry': prediction_result['entry'],
            'stop_loss': prediction_result['stop_loss'],
            'take_profit': prediction_result['take_profit'],
            'current_price': features_df['close'].iloc[-1],
            'atr': atr_value,
            'trailing': False
        }
    return trade_params

def validate_prediction_result(features_df: pd.DataFrame, prediction_result: pd.DataFrame):
        current_price = features_df['close'].iloc[-1]
        if pd.isna(prediction_result['entry']) or prediction_result['entry'] <= 0:
            prediction_result['entry'] = current_price
        if pd.isna(prediction_result['stop_loss']) or prediction_result['stop_loss'] <= 0:
            prediction_result['stop_loss'] = current_price * 0.99  # 1% below current price
        if pd.isna(prediction_result['take_profit']) or prediction_result['take_profit'] <= 0:
            prediction_result['take_profit'] = current_price * 1.01  # 1% above current price

        return prediction_result


def extract_nested_fields(input_obj, field_names):
    found = {}
    if isinstance(input_obj, dict):
        for field in field_names:
            if field in input_obj:
                found[field] = input_obj[field]
        if len(found) == len(field_names):
            return found
        for key in ['input', 'args']:
            if key in input_obj and isinstance(input_obj[key], dict):
                nested_found = extract_nested_fields(input_obj[key], field_names)
                found.update(nested_found)
                if len(found) == len(field_names):
                    return found
    return found