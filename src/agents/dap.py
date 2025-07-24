import pandas as pd
import requests
from typing import List, Dict, Any, Optional, Tuple
from typing import Optional
import os
from langchain_core.tools import tool
from src.users.trader_account_service import TraderAccountService
from src.bot.custom_types import AnalysisInputModel, FullPipelineRequest
try:
    import yfinance as yf
except ImportError:
    yf = None
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


# Optional: import broker/news APIs as needed
# import MetaTrader5 as mt5
# import ccxt
# import yfinance as yf
# from bs4 import BeautifulSoup

class DataAcquisitionProcessor:
    """
    Handles data acquisition and preprocessing for forex trading AI.
    Responsibilities:
      - Ingest live forex market data (candlesticks, tick data, spreads, volumes)
      - Fetch news headlines, economic calendar, macro events
      - Pull historical data for backtesting/model training
    """

    def __init__(self, broker_config: Optional[Dict[str, Any]] = None, news_api_keys: Optional[Dict[str, str]] = None):
        self.broker_config = broker_config or {}
        self.news_api_keys = news_api_keys or {}
        self.oanda_token = self.broker_config.get('OANDA_API_TOKEN')
        self.oanda_account_id = self.broker_config.get('OANDA_ACCOUNT_ID')
        self.oanda_url = self.broker_config.get('OANDA_API_URL')
        self.newsapi_key = 'c01c92ea923842ab9761527f6e05fac0' ##self.news_api_keys.get('NEWS_API_KEY') or self.news_api_keys.get('newsapi')
        # Initialize broker/news API clients here as needed

    # --- Broker Data ---
    def get_live_candlesticks(self, symbol: str, timeframe: str = 'M1', count: int = 100) -> pd.DataFrame:
        """Fetch live candlestick (OHLCV) data from OANDA. Fallback to yfinance if needed."""
        if not self.oanda_url or not self.oanda_token:
            df = self.use_yf_data(symbol)
        headers = {'Authorization': f'Bearer {self.oanda_token}'}
        params = {
            'granularity': timeframe,
            'count': count
        }
        url = f"{self.oanda_url}/instruments/{symbol}/candles"
        try:
            r = requests.get(url, headers=headers, params=params)
            r.raise_for_status()
            candles = r.json()['candles']
            data = [{
                'time': c['time'],
                'open': float(c['mid']['o']),
                'high': float(c['mid']['h']),
                'low': float(c['mid']['l']),
                'close': float(c['mid']['c']),
                'volume': c['volume']
            } for c in candles if c['complete']]
            df = pd.DataFrame(data)
            # Ensure no NaN values
            df = df.dropna()
            if df.empty:
                raise ValueError("No valid candlestick data received")
            return df
        except Exception as e:
            print(f"OANDA candlestick fetch failed: {e}, falling back to yfinance.")
            if yf is None:
                raise ValueError("yfinance not available")
            # ... fallback code unchanged ...

    def get_live_tick_data(self, symbol: str, count: int = 100) -> pd.DataFrame:
        """Fetch live tick data from OANDA (last N price points)."""
        headers = {'Authorization': f'Bearer {self.oanda_token}'}
        params = {'count': count}
        url = f"{self.oanda_url}/instruments/{symbol}/candles"
        try:
            r = requests.get(url, headers=headers, params=params)
            r.raise_for_status()
            candles = r.json()['candles']
            data = [{
                'time': c['time'],
                'price': float(c['mid']['c'])
            } for c in candles if c['complete']]
            return pd.DataFrame(data)
        except Exception as e:
            print(f"OANDA tick fetch failed: {e}")
            return pd.DataFrame([])

    def get_spreads_and_volumes(self, symbol: str) -> Dict[str, Any]:
        """Fetch current spread and volume data for a symbol from OANDA."""
        headers = {'Authorization': f'Bearer {self.oanda_token}'}
        url = f"{self.oanda_url}/accounts/{self.oanda_account_id}/instruments/{symbol}/positionBook"
        try:
            r = requests.get(url, headers=headers)
            r.raise_for_status()
            data = r.json()
            # OANDA does not provide direct spread, so this is a placeholder
            spread = None
            volume = data.get('totalLongPositionUnits', 0) + data.get('totalShortPositionUnits', 0)
            return {'spread': spread, 'volume': volume}
        except Exception as e:
            print(f"OANDA spread/volume fetch failed: {e}")
            return {'spread': None, 'volume': None}

    def get_historical_data(self, symbol: str, timeframe: str = '1h', start: Optional[str] = None, end: Optional[str] = None) -> pd.DataFrame:
        """Fetch historical OHLCV data for backtesting/model training using yfinance."""
        if yf is None:
            print("yfinance not available for historical data")
            return pd.DataFrame()
        
        # Map internal timeframes to yfinance intervals
        tf_map = {
            'M1': '1m',
            'M5': '5m',
            'M15': '15m',
            'H1': '1h',
            'H4': '4h',
            'D1': '1d'
        }
        yf_timeframe = tf_map.get(timeframe, timeframe)  # fallback to original if not mapped

        # Convert symbol format for yfinance
        if symbol == 'BTC_USD':
            yf_symbol = 'BTC-USD'
        elif symbol.endswith('=X'):
            yf_symbol = symbol
        else:
            # Convert forex pairs like EUR_USD to EURUSD=X
            yf_symbol = symbol.replace('_', '') + '=X'
        
        df = yf.download(yf_symbol, start=start, end=end, interval=yf_timeframe)
        if df.empty:
            print(f"No data returned for {yf_symbol} with interval {yf_timeframe}")
            return pd.DataFrame()
        df = df.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'})
        df = df.reset_index().rename(columns={'Datetime': 'time', 'Date': 'time'})
        if 'time' not in df.columns:
            print("No 'time' column in downloaded data")
            return pd.DataFrame()
        return df[['time', 'open', 'high', 'low', 'close', 'volume']]

    # --- News & Events ---
    def fetch_news_headlines(self, query: str = 'forex', limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch latest news headlines using NewsAPI."""
        if not self.newsapi_key:
            print("NewsAPI key not provided, skipping news fetch")
            return []
        
        url = f'https://newsapi.org/v2/everything'
        params = {
            'q': query,
            'apiKey': self.newsapi_key,
            'pageSize': limit,
            'sortBy': 'publishedAt',
            'language': 'en'
        }
        try:
            r = requests.get(url, params=params)
            r.raise_for_status()
            articles = r.json().get('articles', [])
            return articles
        except Exception as e:
            print(f"NewsAPI fetch failed: {e}")
            return []

    def fetch_economic_calendar(self, source: str = 'forexfactory') -> List[Dict[str, Any]]:
        """Fetch upcoming economic events from ForexFactory (scraping)."""
        if source == 'forexfactory':
            if BeautifulSoup is None:
                print("BeautifulSoup not available, skipping economic calendar")
                return []
            
            url = 'https://www.forexfactory.com/calendar.php'
            try:
                r = requests.get(url)
                soup = BeautifulSoup(r.text, 'html.parser')
                events = []
                for row in soup.select('tr.calendar__row'):
                    event = {
                        'time': row.select_one('.calendar__time').text.strip() if row.select_one('.calendar__time') else '',
                        'currency': row.select_one('.calendar__currency').text.strip() if row.select_one('.calendar__currency') else '',
                        'impact': row.select_one('.impact').get('title', '') if row.select_one('.impact') else '',
                        'event': row.select_one('.calendar__event').text.strip() if row.select_one('.calendar__event') else '',
                        'actual': row.select_one('.calendar__actual').text.strip() if row.select_one('.calendar__actual') else '',
                        'forecast': row.select_one('.calendar__forecast').text.strip() if row.select_one('.calendar__forecast') else '',
                        'previous': row.select_one('.calendar__previous').text.strip() if row.select_one('.calendar__previous') else '',
                    }
                    events.append(event)
                return events
            except Exception as e:
                print(f"ForexFactory scraping failed: {e}")
                return []
        else:
            print(f"Economic calendar source '{source}' not supported.")
            return []

    def fetch_macro_events(self) -> List[Dict[str, Any]]:
        """Fetch macroeconomic events from supported APIs (placeholder)."""
        # You can implement this with a real macro data API
        return []

    # --- Preprocessing ---
    def preprocess_market_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and preprocess market data (handle missing values)."""
        df = df.dropna()
        # Remove normalization as it causes issues with technical indicators
        # Keep original price values for proper analysis
        return df

    def preprocess_news_data(self, news: List[Dict[str, Any]]) -> pd.DataFrame:
        """Preprocess news headlines for NLP/model input (convert to DataFrame)."""
        return pd.DataFrame(news)
    
    def use_yf_data(self, symbol: str) -> pd.DataFrame:
        print("OANDA URL or token not provided, falling back to yfinance")
        # Skip OANDA and go directly to yfinance
        if yf is None:
            raise ValueError("yfinance not available") 
            
        # Convert symbol format for yfinance
        if symbol == 'BTC_USD':
            yf_symbol = 'BTC-USD'
        elif symbol.endswith('=X'):
                yf_symbol = symbol
        else:
                # Convert forex pairs like EUR_USD to EURUSD=X
                yf_symbol = symbol.replace('_', '') + '=X'
            
        try:
            df = yf.download(yf_symbol, period='7d', interval='1m')
            if df.empty:
                raise ValueError("No data available from yfinance")
            df = df.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'})
            df = df.reset_index().rename(columns={'Datetime': 'time'})
            df = df[['time', 'open', 'high', 'low', 'close', 'volume']]
            # Ensure no NaN values
            df = df.dropna()
            if df.empty:
                raise ValueError("No valid data after cleaning")
            return df
        except Exception as yf_error:
            raise ValueError("YFinance Data download error")

    async def initialize_dap(db, req: FullPipelineRequest):       
        api_token, oanda_account_id, oanda_api_url, account_type = await TraderAccountService.get_oanda_credentials_by_account_id(db, req.trader_account_id)
        if api_token is  None or oanda_account_id is None:
            raise ValueError("Oanda credentials not provided")
        
        dap = DataAcquisitionProcessor(
            broker_config={
                'OANDA_API_TOKEN': api_token,
                'OANDA_ACCOUNT_ID': oanda_account_id,
                'OANDA_API_URL': oanda_api_url,
                'ACCOUNT_TYPE': account_type
            },
            news_api_keys={'newsapi': os.getenv('NEWSAPI_KEY')}
        )
        market_df = dap.get_live_candlesticks(req.symbol, timeframe=req.timeframe)
        if market_df is None:
              raise ValueError("No Market data available")
        print(f"Market data shape: {market_df.shape}")
        market_df = dap.preprocess_market_data(market_df)
        print(f"Preprocessed market data shape: {market_df.shape}")
        
        news = dap.fetch_news_headlines()
        news_df = dap.preprocess_news_data(news)
        print(f"News data shape: {news_df.shape}")
        return market_df, news_df
    

@tool
def data_acquisition_tool(input: dict) -> Tuple[list[dict], list[dict]]:
    """
    Data Acquisition and Preprocessing Tool for Trading Analysis.
    
    This tool retrieves the latest market data (such as price, volume, and technical indicators) 
    and relevant news for a specified trading symbol and timeframe, then preprocesses this data 
    to prepare it for further analysis, feature engineering, or trading decision-making.
    
    Args:
        input (dict): An object containing the following fields:
            - symbol (str): The trading symbol (e.g., 'EUR_USD').
            - timeframe (str): The timeframe for the data (e.g., 'M1', 'H1').
            - account_id (int): The account ID for the trader.
    
    Returns:
        Tuple[list[dict], list[dict]]:
            - The first list contains the preprocessed market data for the requested symbol and timeframe.
            - The second list contains preprocessed relevant news data.
    
    Use this tool when you need up-to-date, preprocessed market and news data to inform trading strategies or analysis steps.
    """
    # Provide default for account_balance if missing
    req = FullPipelineRequest(
        symbol=input["symbol"],
        timeframe=input["timeframe"],
        trader_account_id=1,
        account_balance=0,
        risk_pct=0,
        units=0,
        sl=0,
        tp=0,
        price=0,
        retries=3,
        use_llm=True
    )
    dap = DataAcquisitionProcessor()
    market_df = dap.get_live_candlesticks(req.symbol, req.timeframe)
    news_data = dap.fetch_news_headlines()

    print("market_df:news_data", market_df, news_data)
    return market_df, news_data
        
# Example usage (to be removed in production):
# dap = DataAcquisitionProcessor()
# df = dap.get_live_candlesticks('EURUSD')
