"""
币安 REST API 采集器
"""
from datetime import datetime

import polars as pl

from zq_data.core.collectors import BaseRestCollector


class BinanceRestCollector(BaseRestCollector):
    """币安 REST API 采集器"""
    
    BASE_URL = "https://api.binance.com"
    
    async def get_kline(self, symbol: str, freq: str, 
                       start_time: datetime, end_time: datetime) -> pl.DataFrame:
        """获取K线数据"""
        url = f"{self.BASE_URL}/api/v3/klines"
        params = {
            "symbol": symbol,
            "interval": freq,
            "startTime": int(start_time.timestamp() * 1000),
            "endTime": int(end_time.timestamp() * 1000),
            "limit": 1000
        }
        
        async with self.session.get(url, params=params) as resp:
            data = await resp.json()
            
        # 转换为DataFrame
        df = pl.DataFrame(
            data,
            schema={
                "timestamp": pl.Int64,
                "open": pl.Float64,
                "high": pl.Float64,
                "low": pl.Float64,
                "close": pl.Float64,
                "volume": pl.Float64,
                "close_time": pl.Int64,
                "quote_volume": pl.Float64,
                "trades": pl.Int64,
                "taker_buy_base": pl.Float64,
                "taker_buy_quote": pl.Float64,
                "ignore": pl.Float64
            }
        )
        return df
    
    async def get_tick(self, symbol: str, 
                      start_time: datetime, end_time: datetime) -> pl.DataFrame:
        """获取Tick数据"""
        url = f"{self.BASE_URL}/api/v3/trades"
        params = {
            "symbol": symbol,
            "limit": 1000
        }
        
        async with self.session.get(url, params=params) as resp:
            data = await resp.json()
            
        # 转换为DataFrame
        df = pl.DataFrame(
            data,
            schema={
                "id": pl.Int64,
                "price": pl.Float64,
                "qty": pl.Float64,
                "quoteQty": pl.Float64,
                "time": pl.Int64,
                "isBuyerMaker": pl.Boolean,
                "isBestMatch": pl.Boolean
            }
        )
        return df
