"""
币安 WebSocket 采集器
"""
import json
from datetime import datetime
from typing import Callable

import polars as pl

from zq_data.core.collectors import BaseWSCollector


class BinanceWSCollector(BaseWSCollector):
    """币安 WebSocket 采集器"""
    
    def __init__(self):
        super().__init__("wss://stream.binance.com:9443/ws")
        
    async def subscribe_tick(self, symbol: str, callback: Callable):
        """订阅Tick数据"""
        await self.connect()
        
        # 订阅消息
        subscribe_msg = {
            "method": "SUBSCRIBE",
            "params": [f"{symbol.lower()}@trade"],
            "id": 1
        }
        await self.ws.send(json.dumps(subscribe_msg))
        
        # 注册回调
        if symbol not in self.callbacks:
            self.callbacks[symbol] = set()
        self.callbacks[symbol].add(callback)
        
        # 启动消息处理
        while True:
            try:
                msg = await self.ws.recv()
                data = json.loads(msg)
                
                # 转换为DataFrame
                df = pl.DataFrame(
                    [data],
                    schema={
                        "e": pl.Utf8,  # 事件类型
                        "E": pl.Int64,  # 事件时间
                        "s": pl.Utf8,  # 交易对
                        "t": pl.Int64,  # 成交ID
                        "p": pl.Float64,  # 成交价格
                        "q": pl.Float64,  # 成交数量
                        "b": pl.Int64,  # 买方订单ID
                        "a": pl.Int64,  # 卖方订单ID
                        "T": pl.Int64,  # 成交时间
                        "m": pl.Boolean,  # 是否是买方主动成交
                        "M": pl.Boolean   # 是否是最优匹配
                    }
                )
                
                # 调用回调函数
                for cb in self.callbacks[symbol]:
                    await cb(df)
                    
            except Exception as e:
                print(f"Error processing message: {e}")
                await self.disconnect()
                break
    
    async def subscribe_kline(self, symbol: str, freq: str, callback: Callable):
        """订阅K线数据"""
        await self.connect()
        
        # 订阅消息
        subscribe_msg = {
            "method": "SUBSCRIBE",
            "params": [f"{symbol.lower()}@kline_{freq}"],
            "id": 1
        }
        await self.ws.send(json.dumps(subscribe_msg))
        
        # 注册回调
        key = f"{symbol}_{freq}"
        if key not in self.callbacks:
            self.callbacks[key] = set()
        self.callbacks[key].add(callback)
        
        # 启动消息处理
        while True:
            try:
                msg = await self.ws.recv()
                data = json.loads(msg)
                
                # 转换为DataFrame
                df = pl.DataFrame(
                    [data],
                    schema={
                        "e": pl.Utf8,  # 事件类型
                        "E": pl.Int64,  # 事件时间
                        "s": pl.Utf8,  # 交易对
                        "k": pl.Struct({
                            "t": pl.Int64,    # K线开始时间
                            "T": pl.Int64,    # K线结束时间
                            "s": pl.Utf8,     # 交易对
                            "i": pl.Utf8,     # K线间隔
                            "f": pl.Int64,    # 首笔成交ID
                            "L": pl.Int64,    # 末笔成交ID
                            "o": pl.Float64,  # 开盘价
                            "c": pl.Float64,  # 收盘价
                            "h": pl.Float64,  # 最高价
                            "l": pl.Float64,  # 最低价
                            "v": pl.Float64,  # 成交量
                            "n": pl.Int64,    # 成交笔数
                            "x": pl.Boolean,  # 是否完结
                            "q": pl.Float64,  # 成交额
                            "V": pl.Float64,  # 主动买入成交量
                            "Q": pl.Float64   # 主动买入成交额
                        })
                    }
                )
                
                # 调用回调函数
                for cb in self.callbacks[key]:
                    await cb(df)
                    
            except Exception as e:
                print(f"Error processing message: {e}")
                await self.disconnect()
                break
