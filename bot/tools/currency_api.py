import datetime
from typing import TypedDict
import requests
from pydantic.v1 import Field
from langchain_core.messages import ToolMessage

from bot.custom_types import CurrencyPair


def search_currency_price_node(input: CurrencyPair):

    """
    Fetches the latest exchange rate for a given currency pair using ExchangeRate-API.

    :param base_currency: The base currency (e.g., "USD").
    :param target_currency: The target currency (e.g., "EUR").
    :return: JSON response with exchange rate data.
    """
    current_date = datetime.datetime.today().strftime('%Y-%m-%d')
    api_key="cur_live_tJzey70L4c4V47hkangBCpKsGpW07Gm5ko65qm3W"
    tool_call_id = input["id"]
    base_currency = input["args"]["base_currency"]
    target_currency = input["args"]["target_currency"]
    target_currencies = [target_currency]
    try:
        url = 'https://api.currencyapi.com/v3/historical'
        headers = {
            'apikey': api_key
        }
        params = {
            'date': current_date,
            'base_currency': base_currency,
            'currencies': ','.join(target_currencies) if target_currencies else None
        }
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            result = response.json()
            return {
                "messages": [
                                ToolMessage(
                                    content=str(response.json()),
                                    tool_call_id=tool_call_id
                            )
                        ]
            }
        else:

            print("Error occurred!", response.text)
            return {
            "messages": [
                ToolMessage(
                    content=f"{response.status_code}, {response.text}",
                    tool_call_id=tool_call_id
                )
            ]
        }
    except Exception as ex:
        print("Error occurred!", ex)
        return {
            "messages": [
                ToolMessage(
                    content=f"An error occurred: {ex}",
                    tool_call_id=tool_call_id
                )
            ]
        }

