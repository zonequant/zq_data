"""
Broker基类实现
提供基础的配置加载和数据获取功能
"""
import os
from re import A
from weakref import proxy
import yaml
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Callable, Dict, Optional
import polars as pl
from ..core.asyncrequest import AsyncRest, AsyncWS


class BaseBroker(ABC):
    """Broker基类"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化Broker
        
        Args:
            config_path: 配置文件路径,如果不提供则使用默认路径
        """
        super().__init__()
        self.config = self._load_config(config_path)
        self.rest_client =AsyncRest(self.config["rest_host"],proxy=self.config["proxy"])
        self.ws_client = AsyncWS(self.config["ws_host"],proxy=self.config["proxy"])
        
    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径,如果不提供则使用默认路径
            
        Returns:
            配置字典
        """
        if not config_path:
            # 使用当前文件名对应的yaml配置
            current_file = os.path.basename(__file__)
            config_name = os.path.splitext(current_file)[0] + '.yaml'
            config_path = os.path.join(os.path.dirname(__file__), config_name)
            
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
            
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    


    
    async def get_kline(self, symbol: str, freq: str,
                       start_time: datetime, end_time: datetime) -> pl.DataFrame:
        """
        获取K线数据
        
        Args:
            symbol: 交易对
            freq: K线周期
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            K线数据DataFrame
        """
        
        # 子类实现具体的数据获取逻辑
        raise NotImplementedError
        
    async def get_tick(self, symbol: str,
                      start_time: datetime, end_time: datetime) -> pl.DataFrame:
        """
        获取Tick数据
        
        Args:
            symbol: 交易对
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            Tick数据DataFrame
        """
        # 子类实现具体的数据获取逻辑
        raise NotImplementedError
        
    async def subscribe_tick(self, symbol: str, callback: Callable):
        """
        订阅Tick数据
        
        Args:
            symbol: 交易对
            callback: 数据回调函数
        """
        # 子类实现具体的订阅逻辑
        raise NotImplementedError
