"""WebSocket 连接管理器，支持频道广播和个人消息。"""

import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """管理 WebSocket 连接，支持按频道分组和定向推送。"""

    def __init__(self) -> None:
        # 频道 -> {websocket_id: WebSocket}
        self._channels: dict[str, dict[int, WebSocket]] = {}
        # websocket_id -> 频道集合（用于断连时快速清理）
        self._client_channels: dict[int, set[str]] = {}

    async def connect(self, websocket: WebSocket, channel: str) -> None:
        """接受 WebSocket 连接并加入指定频道。"""
        await websocket.accept()
        ws_id = id(websocket)
        self._channels.setdefault(channel, {})[ws_id] = websocket
        self._client_channels.setdefault(ws_id, set()).add(channel)
        logger.info("WebSocket connected: id=%d, channel=%s", ws_id, channel)

    def disconnect(self, websocket: WebSocket) -> None:
        """断开 WebSocket 连接，从所有频道移除。"""
        ws_id = id(websocket)
        channels = self._client_channels.pop(ws_id, set())
        for channel in channels:
            channel_clients = self._channels.get(channel)
            if channel_clients:
                channel_clients.pop(ws_id, None)
                if not channel_clients:
                    del self._channels[channel]
        logger.info("WebSocket disconnected: id=%d, channels=%s", ws_id, channels)

    async def broadcast(self, channel: str, data: Any) -> None:
        """向指定频道所有连接广播消息。"""
        channel_clients = self._channels.get(channel, {})
        message = json.dumps(data, ensure_ascii=False) if not isinstance(data, str) else data
        disconnected: list[int] = []
        for ws_id, ws in channel_clients.items():
            try:
                await ws.send_text(message)
            except Exception:
                logger.warning("Failed to send to ws_id=%d, marking disconnected", ws_id)
                disconnected.append(ws_id)
        # 清理断开的连接
        for ws_id in disconnected:
            channel_clients.pop(ws_id, None)

    async def send_personal(self, websocket: WebSocket, data: Any) -> None:
        """向特定连接发送消息。"""
        message = json.dumps(data, ensure_ascii=False) if not isinstance(data, str) else data
        try:
            await websocket.send_text(message)
        except Exception:
            logger.warning("Failed to send personal message to ws_id=%d", id(websocket))
            self.disconnect(websocket)

    def get_channel_clients(self, channel: str) -> int:
        """获取指定频道的连接数。"""
        return len(self._channels.get(channel, {}))


# 全局 WebSocket 管理器实例
ws_manager = ConnectionManager()
