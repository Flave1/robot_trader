from langchain_core.tools import tool

from bot.tools.account_nodes import AccountValidation, account_validation_node


@tool("brokerage_validation_tool", args_schema=AccountValidation, return_direct=True)
def brokerage_validation_tool(arg: AccountValidation):
    """
    Validates a brokerage account by checking the provided login credentials 
    and broker name. If any credential is missing, request the user to provide login_id, 
    password, and broker_name.
    
    Returns validation status.
    """
    return account_validation_node(arg)
