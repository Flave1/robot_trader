from metaapi_cloud_sdk import MetaApi
from ...domain.interfaces.trading_service import TradingService
from ...domain.entities.trade import Trade
import os
import logging

logging.basicConfig(
    filename='app_logs.log',       # Your log file
    level=logging.INFO,         # Log level
    format='%(asctime)s [%(levelname)s] %(message)s'
)
class MetaApiService(TradingService):
    def __init__(self):
        self.token = os.getenv('TOKEN', 'eyJhbGciOiJSUzUxMiIsInR5cCI6IskpXVCJ9.eyJfaWQiOiJlYmExMGY2NmRkODI0Y2Y0MGViMzEwYTBiMmZmOGEyZiIsImFjY2Vzc1J1bGVzIjpbeyJpZCI6InRyYWRpbmctYWNjb3VudC1tYW5hZ2VtZW50LWFwaSIsIm1ldGhvZHMiOlsidHJhZGluZy1hY2NvdW50LW1hbmFnZW1lbnQtYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiLCJ3cml0ZXIiXSwicmVzb3VyY2VzIjpbIio6JFVTRVJfSUQkOioiXX0seyJpZCI6Im1ldGFhcGktcmVzdC1hcGkiLCJtZXRob2RzIjpbIm1ldGFhcGktYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiLCJ3cml0ZXIiXSwicmVzb3VyY2VzIjpbIio6JFVTRVJfSUQkOioiXX0seyJpZCI6Im1ldGFhcGktcnBjLWFwaSIsIm1ldGhvZHMiOlsibWV0YWFwaS1hcGk6d3M6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiLCJ3cml0ZXIiXSwicmVzb3VyY2VzIjpbIio6JFVTRVJfSUQkOioiXX0seyJpZCI6Im1ldGFhcGktcmVhbC10aW1lLXN0cmVhbWluZy1hcGkiLCJtZXRob2RzIjpbIm1ldGFhcGktYXBpOndzOnB1YmxpYzoqOioiXSwicm9sZXMiOlsicmVhZGVyIiwid3JpdGVyIl0sInJlc291cmNlcyI6WyIqOiRVU0VSX0lEJDoqIl19LHsiaWQiOiJtZXRhc3RhdHMtYXBpIiwibWV0aG9kcyI6WyJtZXRhc3RhdHMtYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiLCJ3cml0ZXIiXSwicmVzb3VyY2VzIjpbIio6JFVTRVJfSUQkOioiXX0seyJpZCI6InJpc2stbWFuYWdlbWVudC1hcGkiLCJtZXRob2RzIjpbInJpc2stbWFuYWdlbWVudC1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciIsIndyaXRlciJdLCJyZXNvdXJjZXMiOlsiKjokVVNFUl9JRCQ6KiJdfSx7ImlkIjoiY29weWZhY3RvcnktYXBpIiwibWV0aG9kcyI6WyJjb3B5ZmFjdG9yeS1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciIsIndyaXRlciJdLCJyZXNvdXJjZXMiOlsiKjokVVNFUl9JRCQ6KiJdfSx7ImlkIjoibXQtbWFuYWdlci1hcGkiLCJtZXRob2RzIjpbIm10LW1hbmFnZXItYXBpOnJlc3Q6ZGVhbGluZzoqOioiLCJtdC1tYW5hZ2VyLWFwaTpyZXN0OnB1YmxpYzoqOioiXSwicm9sZXMiOlsicmVhZGVyIiwid3JpdGVyIl0sInJlc291cmNlcyI6WyIqOiRVU0VSX0lEJDoqIl19LHsiaWQiOiJiaWxsaW5nLWFwaSIsIm1ldGhvZHMiOlsiYmlsbGluZy1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciJdLCJyZXNvdXJjZXMiOlsiKjokVVNFUl9JRCQ6KiJdfV0sImlnbm9yZVJhdGVMaW1pdHMiOmZhbHNlLCJ0b2tlbklkIjoiMjAyMTAyMTMiLCJpbXBlcnNvbmF0ZWQiOmZhbHNlLCJyZWFsVXNlcklkIjoiZWJhMTBmNjZkZDgyNGNmNDBlYjMxMGEwYjJmZjhhMmYiLCJpYXQiOjE3NDM4NTA2MDAsImV4cCI6MTc1MTYyNjYwMH0.YjrnJOBxTmTK5Of0gJM5GhF8IAnrjvuBDHVHSaslcFd7h5D267Ac8GvRfppLhQTF5uDiRM5g_7m0GCGSKKnASkm3KLaXJj87pG-J-gZ6LGL5XOdOIotvh5jSMUPJalQZWQKsjsdlP6wKTncN5BBr3FvV4D5jNsAbS2vSoMjGrBCpvvXYCTaxucFgb2Ze5UWKxzzPjnurz6hzaEFOHDl9DsaTqW7_-4pXS93kXZETisLKGpgmNYOC7X4x5imcV2SZS_nnGM-dPHb7xK66ugkNtvLTwlDG4aaXnB02PU--Esk7irFU7xSdP44tdRfYvWsXFaTZnJc5MHpl3flfWm1xKIVWFkCRbSVMOHdOLbCiYXNJ4DA93EDdMQjRQAVBGfL3VaaoMO7yOGJkRV0esnacOUHCL43XK-KgP-sfs-5AOqcHpDLCj8NClWC6r_z_U08euOnIDNLg1zRyUYPbalOk2CKkIkv0hxzUFgCqEjcC3Lb8ubePfWgbff0denhKn5tI10FhZWXyJ6yUePhEsCGSahAJuA5-IBnQ2Lcbr_Jj8vZfCW-whgpykNqwqwUL4L_cJtGSbk9G_KA0oQ2Jm1_CzfNog-dSjHhp7Xo61nVpvH0d16TwPGgJ3l8CtUWS4V0nQmmDdvHEvQaQ_6jOer_KL9uU04bgZI0H4MU2Tyn-DdU')
        self.login = os.getenv('LOGIN', '208584876')
        self.password = os.getenv('PASSWORD', '85236580@Ex')
        self.server_name = os.getenv('SERVER', 'Exness-MT5Trial9')
        self.api = MetaApi(self.token)
        self.connection = None
        self.account = None

    async def initialize(self):
        logging.info("trying to initialize")
        try:
            accounts = await self.api.metatrader_account_api.get_accounts_with_infinite_scroll_pagination()
            self.account = next((item for item in accounts if item.login == self.login and item.type.startswith('cloud')), None)
           
            if not self.account:
                self.account = await self.api.metatrader_account_api.create_account({
                    'name': 'flavedemo',
                    'reliability': "regular",
                    'type': 'cloud-g1',
                    'login': self.login,
                    'password': self.password,
                    'server': self.server_name,
                    'platform': 'mt5',
                    'application': 'MetaApi',
                    'magic': 1000,
                })

            await self.account.deploy()
            await self.account.wait_connected()
            
            self.connection = self.account.get_rpc_connection()
            await self.connection.connect()
            await self.connection.wait_synchronized()

        except Exception as e:
            logging.error(f"Failed to initialize MetaAPI:", e)
            raise ValueError(e)

    async def execute_trade(self, trade: Trade):
        try:
            if trade.type == "ORDER_TYPE_BUY":
                result = await self.connection.create_limit_buy_order(
                    trade.symbol,
                    trade.volume,
                    trade.open_price,
                    trade.stop_loss,
                    trade.take_profit,
                    {
                        'comment': trade.comment,
                        'clientId': trade.client_id,
                        'expiration': {
                            'type': 'ORDER_TIME_SPECIFIED',
                            'time': trade.expiration
                        } if trade.expiration else None
                    }
                )
                return result
        except Exception as e:
            logging.error(f"Failed to execute trade: {str(e)}")
            raise Exception(f"Failed to execute trade: {str(e)}")

    async def get_market_data(self, symbol: str):
        try:
            logging.info(f"Symbol pass: {symbol}")
            return await self.connection.get_symbol_price(symbol)
        except Exception as e:
            logging.error("Failed to get market data: {str(e)}")
            raise Exception(f"Failed to get market data: {str(e)}")

    async def get_positions(self):
        try:
            return await self.connection.get_positions()
        except Exception as e:
            logging.error(f"Failed to get positions: {str(e)}")
            raise Exception(f"Failed to get positions: {str(e)}")

    async def monitor_position(self, position_id: str):
        try:
            return await self.connection.get_position(position_id)
        except Exception as e:
            logging.error(f"Failed to monitor position: {str(e)}")
            raise Exception(f"Failed to monitor position: {str(e)}")