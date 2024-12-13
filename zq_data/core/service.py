"""
数据服务
"""
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Optional, Union

import polars as pl

from zq_data.core.collector import BaseCollector
from zq_data.core.storage import Storage


class ZQData:
    """数据服务"""
    
    def __init__(self, data_dir: Union[str, Path], config_path: Optional[str] = None):
        self.storage = Storage(data_dir)
        self.collectors: Dict[str, BaseCollector] = {}
        
    def register_collector(self, name: str, collector: BaseCollector):
        """注册数据采集器"""
        self.collectors[name] = collector
        
    async def get_kline(self, symbol: str, freq: str, 
                       start_time: datetime, end_time: datetime,
                       collector: Optional[str] = None) -> pl.DataFrame:
        """获取K线数据"""
        if collector and collector in self.collectors:
            return await self.collectors[collector].get_kline(
                symbol, freq, start_time, end_time
            )
        return pl.DataFrame()
    
    async def get_tick(self, symbol: str, 
                      start_time: datetime, end_time: datetime,
                      collector: Optional[str] = None) -> pl.DataFrame:
        """获取Tick数据"""
        if collector and collector in self.collectors:
            return await self.collectors[collector].get_tick(
                symbol, start_time, end_time
            )
        return pl.DataFrame()
    
    async def subscribe_tick(self, symbol: str, callback: Callable,
                           collector: Optional[str] = None):
        """订阅Tick数据"""
        if collector and collector in self.collectors:
            await self.collectors[collector].subscribe_tick(symbol, callback)
            
    async def subscribe_kline(self, symbol: str, freq: str, callback: Callable,
                            collector: Optional[str] = None):
        """订阅K线数据"""
        if collector and collector in self.collectors:
            await self.collectors[collector].subscribe_kline(symbol, freq, callback)
