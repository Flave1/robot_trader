from src.bot.tools.alerting_tool import alerting_tool
from langgraph.types import StreamWriter

async def alerting_node(input: dict, writer: StreamWriter):
    event = {
        'type': input.get('event_type', 'info'),
        'message': input.get('message', ''),
        'details': input.get('details', {}),
        'notification_preferences': input.get('notification_preferences', {})
    }
    result = alerting_tool(event)
    writer({"feedback_state": [{"feedback": result, "state": f"Alerting: {event['type']}"}]})
    return {"messages": [result], "alerting": [result]} 