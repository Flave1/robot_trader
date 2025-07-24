import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import asyncio
import json
import os
from dataclasses import dataclass
from enum import Enum
import logging
from concurrent.futures import ThreadPoolExecutor
import sqlite3
import threading

from src.agents.dap import DataAcquisitionProcessor
from src.agents.laa import FeatureEngineeringAgent
from src.agents.msc import MarketStateClassifier
from src.agents.pp import PricePredictionAgent
from src.agents.rm import RiskManagementAgent
from src.bot.utils import validate_prediction_result

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TradeStatus(Enum):
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class PerformanceMetric(Enum):
    WIN_RATE = "win_rate"
    PROFIT_FACTOR = "profit_factor"
    SHARPE_RATIO = "sharpe_ratio"
    MAX_DRAWDOWN = "max_drawdown"
    TOTAL_RETURN = "total_return"
    CALMAR_RATIO = "calmar_ratio"


@dataclass
class Trade:
    """Represents a single trade with all relevant information."""
    id: str
    symbol: str
    entry_time: datetime
    entry_price: float
    units: float
    direction: str  # 'buy' or 'sell'
    stop_loss: float
    take_profit: float
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    status: TradeStatus = TradeStatus.OPEN
    pnl: float = 0.0
    pnl_pct: float = 0.0
    confidence: float = 0.0
    market_regime: str = ""
    strategy: str = ""
    timeframe: str = ""
    prediction_method: str = ""


@dataclass
class BacktestResult:
    """Results from a backtest run."""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    total_pnl_pct: float
    profit_factor: float
    sharpe_ratio: float
    max_drawdown: float
    calmar_ratio: float
    avg_trade_duration: float
    best_trade: float
    worst_trade: float
    avg_win: float
    avg_loss: float
    trades: List[Trade]
    equity_curve: pd.DataFrame
    performance_metrics: Dict[str, float]


class BacktestingEngine:
    """
    Comprehensive backtesting engine for the trading pipeline.
    Supports historical testing and live monitoring.
    """
    
    def __init__(self, initial_balance: float = 10000.0, commission: float = 0.0001):
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.commission = commission
        self.trades: List[Trade] = []
        self.equity_curve = []
        self.max_drawdown = 0.0
        self.peak_balance = initial_balance
        
        # Performance tracking
        self.daily_returns = []
        self.monthly_returns = []
        
        # Live monitoring
        self.live_monitoring = False
        self.monitoring_thread = None
        self.stop_monitoring = False
        
        # Database for storing results
        self.db_path = "backtest_results.db"
        self.init_database()

    def init_database(self):
        """Initialize SQLite database for storing backtest results."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backtest_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_date TEXT,
                end_date TEXT,
                symbol TEXT,
                timeframe TEXT,
                initial_balance REAL,
                final_balance REAL,
                total_trades INTEGER,
                win_rate REAL,
                profit_factor REAL,
                sharpe_ratio REAL,
                max_drawdown REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id TEXT PRIMARY KEY,
                backtest_run_id INTEGER,
                symbol TEXT,
                entry_time TEXT,
                exit_time TEXT,
                entry_price REAL,
                exit_price REAL,
                units REAL,
                direction TEXT,
                pnl REAL,
                pnl_pct REAL,
                confidence REAL,
                market_regime TEXT,
                strategy TEXT,
                FOREIGN KEY (backtest_run_id) REFERENCES backtest_runs (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS live_monitoring (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                symbol TEXT,
                current_price REAL,
                prediction TEXT,
                confidence REAL,
                action TEXT,
                market_regime TEXT,
                balance REAL,
                open_trades INTEGER,
                daily_pnl REAL
            )
        ''')
        
        conn.commit()
        conn.close()

    def run_backtest(self, 
                    symbol: str, 
                    start_date: str, 
                    end_date: str, 
                    timeframe: str = 'M1',
                    use_llm: bool = True,
                    confidence_threshold: float = 0.7) -> BacktestResult:
        """
        Run a comprehensive backtest on historical data.
        
        Args:
            symbol: Trading symbol (e.g., 'EUR_USD')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            timeframe: Timeframe for analysis
            use_llm: Whether to use LLM for predictions
            confidence_threshold: Minimum confidence to take a trade
            
        Returns:
            BacktestResult with comprehensive performance metrics
        """
        logger.info(f"Starting backtest for {symbol} from {start_date} to {end_date}")
        
        # Reset state
        self.current_balance = self.initial_balance
        self.trades = []
        self.equity_curve = []
        self.max_drawdown = 0.0
        self.peak_balance = self.initial_balance
        
        # Initialize agents
        dap = DataAcquisitionProcessor()
        fea = FeatureEngineeringAgent()
        msc = MarketStateClassifier()
        ppa = PricePredictionAgent()
        rma = RiskManagementAgent()
        
        # Get historical data
        try:
            historical_data = dap.get_historical_data(symbol, timeframe, start_date, end_date)
            if historical_data.empty:
                raise ValueError(f"No historical data available for {symbol}")
        except Exception as e:
            logger.error(f"Failed to get historical data: {e}")
            return self._create_empty_result()
        
        # Process data in chunks to simulate real-time trading
        chunk_size = 100  # Process 100 candles at a time
        total_chunks = len(historical_data) // chunk_size
        
        for chunk_idx in range(total_chunks):
            start_idx = chunk_idx * chunk_size
            end_idx = start_idx + chunk_size
            chunk_data = historical_data.iloc[start_idx:end_idx]
            
            # Process each candle in the chunk
            for idx in range(len(chunk_data)):
                current_data = chunk_data.iloc[:idx+1]
                if len(current_data) < 50:  # Need minimum data for analysis
                    continue
                
                # Simulate real-time pipeline
                try:
                    # 1. Feature Engineering
                    features_df = fea.engineer_features(current_data, pd.DataFrame(), timeframe)
                    
                    # 2. Market State Classification
                    market_state = msc.rule_based_classification(features_df)
                    
                    # 3. Price Prediction
                    prediction_result = ppa.run(features_df, market_state, method='llm' if use_llm else 'ml')
                    prediction_result = validate_prediction_result(features_df, prediction_result)
                    
                    # 4. Risk Management
                    account_state = {
                        'account_balance': self.current_balance,
                        'open_trades': len([t for t in self.trades if t.status == TradeStatus.OPEN]),
                        'max_trades': 5,
                        'drawdown': self._calculate_drawdown(),
                        'max_drawdown': 0.2,
                        'risk_pct': 0.02
                    }
                    
                    # Check if we should take a trade
                    if self._should_take_trade(prediction_result, confidence_threshold):
                        trade = self._execute_trade(
                            symbol, current_data.iloc[-1], prediction_result, 
                            account_state, rma, market_state
                        )
                        if trade:
                            self.trades.append(trade)
                    
                    # Check for trade exits
                    self._check_trade_exits(current_data.iloc[-1])
                    
                    # Update equity curve
                    self._update_equity_curve(current_data.iloc[-1]['time'])
                    
                except Exception as e:
                    logger.error(f"Error processing candle {idx}: {e}")
                    continue
        
        # Close any remaining open trades
        self._close_all_trades(historical_data.iloc[-1])
        
        # Calculate final results
        result = self._calculate_performance_metrics()
        
        # Save results to database
        self._save_backtest_results(symbol, start_date, end_date, timeframe, result)
        
        logger.info(f"Backtest completed. Win rate: {result.win_rate:.2%}, Total PnL: ${result.total_pnl:.2f}")
        return result

    def _should_take_trade(self, prediction_result: Dict, confidence_threshold: float) -> bool:
        """Determine if we should take a trade based on prediction and confidence."""
        confidence = prediction_result.get('confidence', 0.0)
        action = prediction_result.get('action', 'Hold')
        
        # Only trade if confidence is above threshold and action is not Hold
        if confidence < confidence_threshold:
            return False
        
        if action == 'Hold':
            return False
        
        # Check if we have too many open trades
        open_trades = len([t for t in self.trades if t.status == TradeStatus.OPEN])
        if open_trades >= 5:  # Max 5 concurrent trades
            return False
        
        return True

    def _execute_trade(self, symbol: str, current_candle: pd.Series, 
                      prediction_result: Dict, account_state: Dict, 
                      rma: RiskManagementAgent, market_state: str) -> Optional[Trade]:
        """Execute a trade based on prediction results."""
        try:
            # Calculate position size using risk management
            atr_value = current_candle['close'] * 0.01  # Simplified ATR
            trade_params = {
                'entry': prediction_result['entry'],
                'stop_loss': prediction_result['stop_loss'],
                'take_profit': prediction_result['take_profit'],
                'current_price': current_candle['close'],
                'atr': atr_value
            }
            
            risk_result = rma.run(trade_params, account_state)
            
            if not risk_result['trade_approved']:
                return None
            
            # Create trade
            trade = Trade(
                id=f"trade_{len(self.trades)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                symbol=symbol,
                entry_time=pd.to_datetime(current_candle['time']),
                entry_price=current_candle['close'],
                units=risk_result['position_size'],
                direction='buy' if prediction_result['action'] == 'Buy' else 'sell',
                stop_loss=prediction_result['stop_loss'],
                take_profit=prediction_result['take_profit'],
                confidence=prediction_result.get('confidence', 0.0),
                market_regime=prediction_result.get('regime', {}).get('regime', ''),
                strategy=prediction_result.get('strategy', ''),
                prediction_method=prediction_result.get('method', '')
            )
            
            # Deduct commission
            commission_cost = abs(trade.units) * current_candle['close'] * self.commission
            self.current_balance -= commission_cost
            
            logger.info(f"Executed trade: {trade.direction} {trade.units} {symbol} at {trade.entry_price}")
            return trade
            
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return None

    def _check_trade_exits(self, current_candle: pd.Series):
        """Check if any open trades should be closed."""
        current_price = current_candle['close']
        current_time = pd.to_datetime(current_candle['time'])
        
        for trade in self.trades:
            if trade.status != TradeStatus.OPEN:
                continue
            
            # Check stop loss
            if trade.direction == 'buy':
                if current_price <= trade.stop_loss:
                    self._close_trade(trade, current_price, current_time, 'stop_loss')
                elif current_price >= trade.take_profit:
                    self._close_trade(trade, current_price, current_time, 'take_profit')
            else:  # sell
                if current_price >= trade.stop_loss:
                    self._close_trade(trade, current_price, current_time, 'stop_loss')
                elif current_price <= trade.take_profit:
                    self._close_trade(trade, current_price, current_time, 'take_profit')

    def _close_trade(self, trade: Trade, exit_price: float, exit_time: datetime, reason: str):
        """Close a trade and calculate PnL."""
        trade.exit_price = exit_price
        trade.exit_time = exit_time
        trade.status = TradeStatus.CLOSED
        
        # Calculate PnL
        if trade.direction == 'buy':
            trade.pnl = (exit_price - trade.entry_price) * trade.units
        else:
            trade.pnl = (trade.entry_price - exit_price) * trade.units
        
        # Deduct commission
        commission_cost = abs(trade.units) * exit_price * self.commission
        trade.pnl -= commission_cost
        
        # Update balance
        self.current_balance += trade.pnl
        
        # Calculate percentage PnL
        trade.pnl_pct = (trade.pnl / (trade.entry_price * trade.units)) * 100
        
        logger.info(f"Closed trade: {trade.direction} {trade.units} {trade.symbol} at {exit_price}, PnL: ${trade.pnl:.2f} ({trade.pnl_pct:.2f}%)")

    def _close_all_trades(self, final_candle: pd.Series):
        """Close all remaining open trades at the final price."""
        for trade in self.trades:
            if trade.status == TradeStatus.OPEN:
                self._close_trade(trade, final_candle['close'], pd.to_datetime(final_candle['time']), 'end_of_backtest')

    def _update_equity_curve(self, timestamp: str):
        """Update equity curve with current balance."""
        self.equity_curve.append({
            'timestamp': timestamp,
            'balance': self.current_balance,
            'drawdown': self._calculate_drawdown()
        })
        
        # Update peak balance and max drawdown
        if self.current_balance > self.peak_balance:
            self.peak_balance = self.current_balance
        
        current_drawdown = self._calculate_drawdown()
        if current_drawdown > self.max_drawdown:
            self.max_drawdown = current_drawdown

    def _calculate_drawdown(self) -> float:
        """Calculate current drawdown percentage."""
        if self.peak_balance == 0:
            return 0.0
        return (self.peak_balance - self.current_balance) / self.peak_balance

    def _calculate_performance_metrics(self) -> BacktestResult:
        """Calculate comprehensive performance metrics."""
        if not self.trades:
            return self._create_empty_result()
        
        # Basic metrics
        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if t.pnl > 0])
        losing_trades = len([t for t in self.trades if t.pnl < 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # PnL metrics
        total_pnl = sum(t.pnl for t in self.trades)
        total_pnl_pct = ((self.current_balance - self.initial_balance) / self.initial_balance) * 100
        
        # Profit factor
        gross_profit = sum(t.pnl for t in self.trades if t.pnl > 0)
        gross_loss = abs(sum(t.pnl for t in self.trades if t.pnl < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Sharpe ratio (simplified)
        returns = [t.pnl_pct for t in self.trades]
        sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
        
        # Calmar ratio
        calmar_ratio = total_pnl_pct / self.max_drawdown if self.max_drawdown > 0 else 0
        
        # Trade statistics
        avg_trade_duration = np.mean([
            (t.exit_time - t.entry_time).total_seconds() / 3600 
            for t in self.trades if t.exit_time
        ]) if any(t.exit_time for t in self.trades) else 0
        
        best_trade = max([t.pnl for t in self.trades]) if self.trades else 0
        worst_trade = min([t.pnl for t in self.trades]) if self.trades else 0
        
        avg_win = np.mean([t.pnl for t in self.trades if t.pnl > 0]) if winning_trades > 0 else 0
        avg_loss = np.mean([t.pnl for t in self.trades if t.pnl < 0]) if losing_trades > 0 else 0
        
        # Create equity curve DataFrame
        equity_df = pd.DataFrame(self.equity_curve)
        
        # Performance metrics dictionary
        performance_metrics = {
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': self.max_drawdown,
            'total_return': total_pnl_pct,
            'calmar_ratio': calmar_ratio,
            'avg_trade_duration': avg_trade_duration,
            'best_trade': best_trade,
            'worst_trade': worst_trade,
            'avg_win': avg_win,
            'avg_loss': avg_loss
        }
        
        return BacktestResult(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_pnl=total_pnl,
            total_pnl_pct=total_pnl_pct,
            profit_factor=profit_factor,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=self.max_drawdown,
            calmar_ratio=calmar_ratio,
            avg_trade_duration=avg_trade_duration,
            best_trade=best_trade,
            worst_trade=worst_trade,
            avg_win=avg_win,
            avg_loss=avg_loss,
            trades=self.trades,
            equity_curve=equity_df,
            performance_metrics=performance_metrics
        )

    def _create_empty_result(self) -> BacktestResult:
        """Create empty result when no trades are executed."""
        return BacktestResult(
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0.0,
            total_pnl=0.0,
            total_pnl_pct=0.0,
            profit_factor=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            calmar_ratio=0.0,
            avg_trade_duration=0.0,
            best_trade=0.0,
            worst_trade=0.0,
            avg_win=0.0,
            avg_loss=0.0,
            trades=[],
            equity_curve=pd.DataFrame(),
            performance_metrics={}
        )

    def _save_backtest_results(self, symbol: str, start_date: str, end_date: str, 
                             timeframe: str, result: BacktestResult):
        """Save backtest results to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Insert backtest run
        cursor.execute('''
            INSERT INTO backtest_runs 
            (start_date, end_date, symbol, timeframe, initial_balance, final_balance,
             total_trades, win_rate, profit_factor, sharpe_ratio, max_drawdown)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (start_date, end_date, symbol, timeframe, self.initial_balance, 
              self.current_balance, result.total_trades, result.win_rate, 
              result.profit_factor, result.sharpe_ratio, result.max_drawdown))
        
        run_id = cursor.lastrowid
        
        # Insert trades
        for trade in result.trades:
            cursor.execute('''
                INSERT INTO trades 
                (id, backtest_run_id, symbol, entry_time, exit_time, entry_price, 
                 exit_price, units, direction, pnl, pnl_pct, confidence, 
                 market_regime, strategy)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (trade.id, run_id, trade.symbol, trade.entry_time.isoformat(),
                  trade.exit_time.isoformat() if trade.exit_time else None,
                  trade.entry_price, trade.exit_price, trade.units, trade.direction,
                  trade.pnl, trade.pnl_pct, trade.confidence, trade.market_regime,
                  trade.strategy))
        
        conn.commit()
        conn.close()

    def start_live_monitoring(self, symbol: str, timeframe: str = 'M1', 
                             confidence_threshold: float = 0.7):
        """Start live monitoring of the trading pipeline."""
        self.live_monitoring = True
        self.stop_monitoring = False
        
        async def monitoring_loop():
            logger.info(f"Starting live monitoring for {symbol}")
            
            # Initialize agents
            dap = DataAcquisitionProcessor()
            fea = FeatureEngineeringAgent()
            msc = MarketStateClassifier()
            ppa = PricePredictionAgent()
            rma = RiskManagementAgent()
            
            while not self.stop_monitoring:
                try:
                    # Get current market data
                    market_df = dap.get_live_candlesticks(symbol, timeframe)
                    if market_df.empty:
                        continue
                    
                    # Run pipeline
                    features_df = fea.engineer_features(market_df, pd.DataFrame(), timeframe)
                    market_state = msc.rule_based_classification(features_df)
                    prediction_result = ppa.run(features_df, market_state, method='llm')
                    prediction_result = validate_prediction_result(features_df, prediction_result)
                    
                    # Save monitoring data
                    self._save_monitoring_data(symbol, market_df.iloc[-1], prediction_result)
                    
                    # Log important events
                    if prediction_result.get('confidence', 0) > confidence_threshold:
                        logger.info(f"High confidence signal: {prediction_result['action']} "
                                  f"with {prediction_result.get('confidence', 0):.2f} confidence")
                    
                    # Wait before next iteration
                    await asyncio.sleep(60)  # Check every minute
                    
                except Exception as e:
                    logger.error(f"Error in live monitoring: {e}")
                    await asyncio.sleep(60)
        
        # Start monitoring in a separate thread using asyncio
        def run_async_loop():
            asyncio.run(monitoring_loop())
        
        self.monitoring_thread = threading.Thread(target=run_async_loop)
        self.monitoring_thread.start()

    def stop_live_monitoring(self):
        """Stop live monitoring."""
        self.stop_monitoring = True
        if self.monitoring_thread:
            self.monitoring_thread.join()
        self.live_monitoring = False
        logger.info("Live monitoring stopped")

    def _save_monitoring_data(self, symbol: str, current_candle: pd.Series, 
                            prediction_result: Dict):
        """Save live monitoring data to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO live_monitoring 
            (timestamp, symbol, current_price, prediction, confidence, action, 
             market_regime, balance, open_trades, daily_pnl)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            current_candle['time'],
            symbol,
            current_candle['close'],
            prediction_result.get('prediction', ''),
            prediction_result.get('confidence', 0.0),
            prediction_result.get('action', ''),
            prediction_result.get('regime', {}).get('regime', ''),
            self.current_balance,
            len([t for t in self.trades if t.status == TradeStatus.OPEN]),
            0.0  # Daily PnL calculation would be added here
        ))
        
        conn.commit()
        conn.close()

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of all backtest runs."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT symbol, timeframe, total_trades, win_rate, profit_factor, 
                   sharpe_ratio, max_drawdown, final_balance, created_at
            FROM backtest_runs
            ORDER BY created_at DESC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        summary = {
            'total_runs': len(results),
            'runs': []
        }
        
        for row in results:
            summary['runs'].append({
                'symbol': row[0],
                'timeframe': row[1],
                'total_trades': row[2],
                'win_rate': row[3],
                'profit_factor': row[4],
                'sharpe_ratio': row[5],
                'max_drawdown': row[6],
                'final_balance': row[7],
                'created_at': row[8]
            })
        
        return summary

    def export_results(self, run_id: int, format: str = 'json') -> str:
        """Export backtest results to file."""
        conn = sqlite3.connect(self.db_path)
        
        # Get backtest run
        run_df = pd.read_sql_query(
            'SELECT * FROM backtest_runs WHERE id = ?', conn, params=[run_id]
        )
        
        # Get trades
        trades_df = pd.read_sql_query(
            'SELECT * FROM trades WHERE backtest_run_id = ?', conn, params=[run_id]
        )
        
        conn.close()
        
        if format == 'json':
            result = {
                'backtest_run': run_df.to_dict('records')[0] if not run_df.empty else {},
                'trades': trades_df.to_dict('records')
            }
            return json.dumps(result, indent=2)
        elif format == 'csv':
            # Save to CSV files
            run_df.to_csv(f'backtest_run_{run_id}.csv', index=False)
            trades_df.to_csv(f'trades_run_{run_id}.csv', index=False)
            return f"Results exported to backtest_run_{run_id}.csv and trades_run_{run_id}.csv"
        else:
            raise ValueError("Unsupported format. Use 'json' or 'csv'")


# Utility functions for easy backtesting
def run_quick_backtest(symbol: str, days: int = 30, timeframe: str = 'M1') -> BacktestResult:
    """Run a quick backtest for the last N days."""
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    engine = BacktestingEngine()
    return engine.run_backtest(symbol, start_date, end_date, timeframe)


def compare_strategies(symbol: str, start_date: str, end_date: str, 
                      strategies: List[Dict]) -> Dict[str, BacktestResult]:
    """Compare multiple trading strategies."""
    results = {}
    
    for strategy in strategies:
        engine = BacktestingEngine()
        result = engine.run_backtest(
            symbol, start_date, end_date,
            timeframe=strategy.get('timeframe', 'M1'),
            use_llm=strategy.get('use_llm', True),
            confidence_threshold=strategy.get('confidence_threshold', 0.7)
        )
        results[strategy.get('name', f'strategy_{len(results)}')] = result
    
    return results


def generate_performance_report(result: BacktestResult) -> str:
    """Generate a comprehensive performance report."""
    report = f"""
    ===== BACKTEST PERFORMANCE REPORT =====
    
    Overall Performance:
    - Total Trades: {result.total_trades}
    - Win Rate: {result.win_rate:.2%}
    - Total PnL: ${result.total_pnl:.2f} ({result.total_pnl_pct:.2f}%)
    - Profit Factor: {result.profit_factor:.2f}
    - Sharpe Ratio: {result.sharpe_ratio:.2f}
    - Max Drawdown: {result.max_drawdown:.2%}
    - Calmar Ratio: {result.calmar_ratio:.2f}
    
    Trade Statistics:
    - Winning Trades: {result.winning_trades}
    - Losing Trades: {result.losing_trades}
    - Average Win: ${result.avg_win:.2f}
    - Average Loss: ${result.avg_loss:.2f}
    - Best Trade: ${result.best_trade:.2f}
    - Worst Trade: ${result.worst_trade:.2f}
    - Average Trade Duration: {result.avg_trade_duration:.1f} hours
    
    Risk Assessment:
    - Risk/Reward Ratio: {abs(result.avg_win / result.avg_loss):.2f} (if avg_loss != 0)
    - Expected Value per Trade: ${(result.avg_win * result.win_rate + result.avg_loss * (1 - result.win_rate)):.2f}
    
    ======================================
    """
    return report 