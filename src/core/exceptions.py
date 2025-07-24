class ArbiXException(Exception):
    """Base exception for ArbiX application"""
    pass

class TradingException(ArbiXException):
    """Base exception for trading-related errors"""
    pass

class APIException(TradingException):
    """Exception for API-related errors"""
    pass

class ConfigurationException(ArbiXException):
    """Exception for configuration-related errors"""
    pass

class ValidationException(ArbiXException):
    """Exception for validation-related errors"""
    pass

class DatabaseException(ArbiXException):
    """Exception for database-related errors"""
    pass

class RiskManagementException(TradingException):
    """Exception for risk management-related errors"""
    pass

class InsufficientFundsException(TradingException):
    """Exception for insufficient funds errors"""
    pass

class InvalidOrderException(TradingException):
    """Exception for invalid order errors"""
    pass

class MarketDataException(TradingException):
    """Exception for market data-related errors"""
    pass 