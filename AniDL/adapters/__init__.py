from AniDL.adapters.baha import BahaAdapter
from AniDL.Models import Season, Episode, VideoMedia, AudioMedia, SubtitleMedia
from typing import List, Dict, Any, Optional, Tuple
from AniDL.Interfaces import BaseAdapterInterface
from datetime import datetime
from httpx import Cookies

# 定义未找到适配器异常
class AdapterNotFound(Exception):
    def __init__(self, adapter_name: str):
        self.adapter_name = adapter_name
        self.message = f"Adapter {adapter_name} not found"
        super().__init__(self.message)

class Adapter(BaseAdapterInterface):
    """通用适配器，自动匹配对应的适配器"""
    AdapterList = [BahaAdapter]

    def get_adapter(self, adapter_name: str) -> BaseAdapterInterface:
        for adapter in self.AdapterList:
            if adapter.Config.adapter_name == adapter_name:
                return adapter
        raise AdapterNotFound(adapter_name)
            
    def choose_adapter(self, url: str) -> BaseAdapterInterface:
        for adapter in self.AdapterList:
            for base_url in adapter.Config.base_play_url:
                if base_url in url:
                    return adapter
        raise AdapterNotFound("Unknown")

    def __init__(self, feature: str, cookies: Cookies = None):
        # 判断feature是否为url
        if feature.startswith("http"):
            adapter = self.choose_adapter(feature)
        else:
            adapter = self.get_adapter(feature)
        self.adapter = adapter(cookies)
    
    def set_cookies(self, cookies: Cookies) -> None:
        self.adapter.set_cookies(cookies)

    async def login(self, username: str, password: str, set_cookies: bool = True) -> Cookies:
        return await self.adapter.login(username, password, set_cookies)
    
    async def username(self) -> str | None:
        return await self.adapter.username()
    
    async def subscription_due_date(self) -> datetime | None:
        return await self.adapter.subscription_due_date()
    
    async def parse_playurl(self, playurl: str) -> Tuple[Season, List[Episode]]:
        return await self.adapter.parse_playurl(playurl)
    
    async def parse_stream(self, episode: Episode) -> Tuple[List[VideoMedia], Optional[List[AudioMedia]], Optional[List[SubtitleMedia]]]:
        return await self.adapter.parse_stream(episode)