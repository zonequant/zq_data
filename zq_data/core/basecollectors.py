"""
数据采集器基类
"""
import asyncio
from abc import ABC, abstractmethod
import json
from typing import Any, Optional
import aiohttp
from aiohttp import ClientResponse, ClientSession, ClientTimeout, WSMsgType
from aiohttp.client_exceptions import ServerDisconnectedError
import traceback
from loguru import logger as log

class BaseRestCollector(ABC):
    """REST API采集器基类"""
    
    def __init__(
        self,
        session: Optional[ClientSession] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: float = 30
    ):
        """
        初始化REST采集器
        
        Args:
            session: aiohttp会话，如果不提供则创建新的
            max_retries: 最大重试次数
            retry_delay: 重试基础延迟时间(秒)
            timeout: 请求超时时间(秒)
        """
        self.session = session or ClientSession(
            timeout=ClientTimeout(total=timeout)
        )
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    @abstractmethod
    async def check_rate_limit(self) -> float:
        """
        检查频率限制，返回需要等待的时间（秒）
        
        Returns:
            float: 需要等待的时间，0表示可以立即请求
        """
        pass
    
    async def _retry_request(
        self,
        method: str,
        url: str,
        retry_count: int = 0,
        **kwargs
    ) -> ClientResponse:
        """
        带重试的请求
        
        Args:
            method: 请求方法
            url: 请求URL
            retry_count: 当前重试次数
            **kwargs: 请求参数
            
        Returns:
            响应对象
            
        Raises:
            aiohttp.ClientError: 重试次数用完后仍然失败
        """
        try:
            # 检查频率限制
            wait_time = await self.check_rate_limit()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            
            # 发送请求
            response = await self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
            
        except aiohttp.ClientError as e:
            # 如果还有重试次数
            if retry_count < self.max_retries:
                # 计算延迟时间：基础延迟 * (2^重试次数)
                delay = self.retry_delay * (2 ** retry_count)
                await asyncio.sleep(delay)
                
                # 递归重试
                return await self._retry_request(
                    method,
                    url,
                    retry_count + 1,
                    **kwargs
                )
            raise e
    
    async def get(self, url: str, **kwargs) -> Any:
        """
        发送GET请求并解析JSON响应
        
        Args:
            url: 请求URL
            **kwargs: 请求参数
        
        Returns:
            解析后的JSON数据
        """
        async with await self._retry_request("GET", url, **kwargs) as response:
            return await response.json()
    
    async def post(self, url: str, **kwargs) -> Any:
        """
        发送POST请求并解析JSON响应
        Args:
            url: 请求URL
            **kwargs: 请求参数
        
        Returns:
            解析后的JSON数据
        """
        async with await self._retry_request("POST", url, **kwargs) as response:
            return await response.json()
    
    async def close(self):
        """关闭会话"""
        if self.session and not self.session.closed:
            await self.session.close()


class BaseWSCollector(ABC):
    """WebSocket采集器基类"""
    
    def __init__(self, url: str,proxy=None):
        self.proxy = proxy
        self.url = url
        self._ws = None  # Websocket connection object.
            
    def init(self, url, connected_callback, process_callback=None, process_binary_callback=None):
        self.url = url
        self.connected_callback = connected_callback
        self.process_binary_callback = process_binary_callback
        self.process_callback = process_callback

    async def conn(self):
        await self._connect()

    async def _connect(self):
        session = aiohttp.ClientSession()
        try:
            if self.proxy:
                self._ws = await session.ws_connect(self.url, proxy=self.proxy)
            else:
                self._ws = await session.ws_connect(self.url)
                log.debug("ws connected")
            await self.connected_callback()
            log.debug("ws connected callback")
            await self._receive()
            await self.on_disconnected()
        except Exception:
            print("ws error")
            traceback.print_exc()
            await self._check_connection()

    @property
    def ws(self):
        return self._ws

    async def on_disconnected(self):
        log.info("connected closed.")
        await self._check_connection()

    async def _reconnect(self):
        """Re-connect to Websocket server."""
        log.warning("reconnecting to Websocket server right now!")
        await self._connect()

    async def _receive(self):
        """Receive stream message from Websocket connection."""
        async for msg in self.ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                if self.process_callback:
                    try:
                        data = json.loads(msg.data)
                    except:
                        data = msg.data
                    await self.process_callback(data)
            elif msg.type == aiohttp.WSMsgType.BINARY:
                if self.process_binary_callback:
                    await self.process_binary_callback(msg.data)
            elif msg.type == aiohttp.WSMsgType.CLOSED:
                log.warning("receive event CLOSED:", msg, caller=self)
                await self._reconnect()
            elif msg.type == aiohttp.WSMsgType.PING:
                print(f"ping:{msg.data}")
                await self._ws.send(WSMsgType.PONG)
            elif msg.type == aiohttp.WSMsgType.ERROR:
                log.error("receive event ERROR:", msg, caller=self)
            else:
                log.warning("unhandled msg:", msg, caller=self)

    async def _check_connection(self):
        """Check Websocket connection, if connection closed, re-connect immediately."""
        if not self._ws:
            log.warning("Websocket connection not connected yet!")
            return
        if self._ws.closed:
            await self._reconnect()

    async def send(self, data):
        try:
            if not self.ws:
                log.warning("Websocket connection not connected yet!")
                return False
            if isinstance(data, dict):
                await self.ws.send_json(data)
            elif isinstance(data, str):
                await self.ws.send_str(data)
            else:
                return False
            return True
        except :
            log.error("ws send error")
            await self._check_connection()
