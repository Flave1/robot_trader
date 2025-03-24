from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Dict, Union

class MarketType(BaseModel):
    marketType: str = Field(..., description="Crypto-currencies or forex market")

@tool("get-available-currencies", args_schema=MarketType, return_direct=True)
def get_available_currencies(marketType: str) -> Union[Dict, str]:
    """Get all currencies."""
    try:
        currencies = [
            "EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CAD", "USD/CHF", "NZD/USD", "EUR/GBP", "EUR/JPY", "GBP/JPY"
        ]
        
        return {
            "currencyPairs": currencies,
            "rates": 0,
            "marketType": marketType
        }
    except Exception as err:
        # Log and return the error
        print("Error fetching currencies:", err)
        return  "There was an error fetching available currencies."
        