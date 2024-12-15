"""
数据采集器基类
"""
import asyncio
from abc import ABC, abstractmethod
import json
from typing import Any, Optional
from weakref import proxy
import aiohttp
from aiohttp import ClientResponse, ClientSession, ClientTimeout, WSMsgType
from aiohttp.client_exceptions import ServerDisconnectedError
import traceback
from loguru import logger as log

class AsyncRest(ABC):
    """REST API采集器基类"""
    
    def __init__(
        self,
        host: str,
        session: Optional[ClientSession] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: float = 30,
        proxy=None
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
    
    async def check_rate_limit(self) :
        """
        检查频率限制，返回需要等待的时间（秒）
        
        Returns:
            float: 需要等待的时间，0表示可以立即请求
        """
        return 0
    
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


class AsyncWS(ABC):
    """WebSocket采集器基类"""
    def __init__(self, url: str,proxy=None):
        self.proxy = proxy
        self.url = url
        self._ws = None  # Websocket connection object.
        self.session = None
            
    def init(self, url, connected_callback, process_callback=None, process_binary_callback=None):
        self.url = url
        self.connected_callback = connected_callback
        self.process_binary_callback = process_binary_callback
        self.process_callback = process_callback

    async def conn(self):
        await self._connect()

    async def _connect(self):
        """连接到 WebSocket 服务器"""
        self.session = aiohttp.ClientSession()
        try:
            if self.proxy:
                self._ws = await self.session.ws_connect(self.url, proxy=self.proxy)
            else:
                self._ws = await self.session.ws_connect(self.url)
            log.debug("WebSocket connected successfully")
            
            if hasattr(self, 'connected_callback'):
                await self.connected_callback()
                log.debug("WebSocket connected callback executed")
            
            await self._receive()
        except Exception as e:
            log.error(f"WebSocket connection error: {str(e)}")
            traceback.print_exc()
            await asyncio.sleep(1)  # 添加重连延迟
            await self._check_connection()
        finally:
            if hasattr(self, 'session'):
                await self.session.close()

    async def _receive(self):
        """接收 WebSocket 消息"""
        async for msg in self._ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                if self.process_callback:
                    try:
                        data = json.loads(msg.data)
                    except json.JSONDecodeError:
                        data = msg.data
                    await self.process_callback(data)
            elif msg.type == aiohttp.WSMsgType.BINARY:
                if self.process_binary_callback:
                    await self.process_binary_callback(msg.data)
            elif msg.type == aiohttp.WSMsgType.CLOSED:
                log.warning(f"WebSocket connection closed: {msg}")
                await self._reconnect()
            elif msg.type == aiohttp.WSMsgType.PING:
                log.debug(f"Received PING: {msg.data}")
                await self._ws.pong(msg.data)
            elif msg.type == aiohttp.WSMsgType.ERROR:
                log.error(f"WebSocket error occurred: {msg}")
            else:
                log.warning(f"Unhandled WebSocket message type: {msg}")

    async def _check_connection(self):
        """检查 WebSocket 连接状态，如果断开则重连"""
        if not self._ws:
            log.warning("WebSocket connection not established")
            await asyncio.sleep(1)  # 添加重连延迟
            await self._connect()
            return
            
        if self._ws.closed:
            log.warning("WebSocket connection closed, attempting to reconnect")
            await asyncio.sleep(1)  # 添加重连延迟
            await self._reconnect()

    async def _reconnect(self):
        """重新连接到 WebSocket 服务器"""
        log.info("Reconnecting to WebSocket server")
        if self._ws and not self._ws.closed:
            await self._ws.close()
        await self._connect()

    async def send(self, data):
        """发送数据到 WebSocket 服务器
        
        Args:
            data: 要发送的数据
            
        Raises:
            ConnectionError: WebSocket 未连接时抛出
        """
        if not self._ws or self._ws.closed:
            log.warning("WebSocket not connected, attempting to connect")
            await self._connect()
            
        if self._ws and not self._ws.closed:
            if isinstance(data, (dict, list)):
                await self._ws.send_json(data)
            elif isinstance(data, str):
                await self._ws.send_str(data)
            else:
                await self._ws.send_bytes(data)
        else:
            raise ConnectionError("Failed to establish WebSocket connection")
