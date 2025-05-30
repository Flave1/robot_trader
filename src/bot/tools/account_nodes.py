import asyncio
from langgraph.types import StreamWriter
from langchain_core.messages import ToolMessage
from pydantic import Field
from src.bot.custom_types import CommonUpdateType


class AccountValidation(CommonUpdateType):
    login_id: str = Field(..., description="The unique identifier assigned to the trading account by the broker.")
    password: str = Field(..., description="The password used to authenticate and access the trading account.")
    broker_name: str = Field(..., description="The name of the broker associated with the trading account.")


async def account_validation_node(input: AccountValidation, writer: StreamWriter):

    print("input", input['args'])
    account_login = input['args']["login_id"]
    account_password = input['args']["password"]
    account_name = input['args']["broker_name"]
    tool_call_id = input["id"]

    writer({"trade_update": [
           {"label": "validation", "status": f"Give me a moment, I am trying to validate your account with your broker"}]})

    await asyncio.sleep(10)
    result = "You are account is not validated"
    return {
            "messages": [
                ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call_id
                )
            ]
        }