"""
数据采集器基类
"""
from abc import ABC, abstractmethod
from typing import Callable, Optional
from datetime import datetime

import polars as pl


class BaseCollector(ABC):
    """数据采集器基类"""
    
    @abstractmethod
    async def get_kline(self, symbol: str, freq: str, 
                       start_time: datetime, end_time: datetime) -> pl.DataFrame:
        """获取K线数据"""
        pass
    
    @abstractmethod
    async def get_tick(self, symbol: str, 
                      start_time: datetime, end_time: datetime) -> pl.DataFrame:
        """获取Tick数据"""
        pass
    
    @abstractmethod
    async def subscribe_tick(self, symbol: str, callback: Callable):
        """订阅Tick数据"""
        pass
    
    @abstractmethod
    async def subscribe_kline(self, symbol: str, freq: str, callback: Callable):
        """订阅K线数据"""
        pass
