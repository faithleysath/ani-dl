from baha import BahaAdapter
from Models import Season, Episode, VideoMedia, AudioMedia, SubtitleMedia
from typing import List, Dict, Any, Optional, Tuple
from Interfaces import BaseAdapterInterface
from datetime import datetime
from httpx import Cookies

class Adapter(BaseAdapterInterface):
    """通用适配器，自动匹配对应的适配器"""
    AdapterList = [BahaAdapter]

    def get_adapter(self, adapter_name: str) -> BaseAdapterInterface:
        for adapter in self.AdapterList:
            if adapter.Config.adapter_name == adapter_name:
                return adapter
            
    def choose_adapter(self, url: str) -> BaseAdapterInterface:
        for adapter in self.AdapterList:
            for base_url in adapter.Config.base_play_url:
                if base_url in url:
                    return adapter

    def __init__(self, feature: str, cookies: Cookies = None):
        # 判断feature是否为url
        if feature.startswith("http"):
            adapter = self.choose_adapter(feature)
        else:
            adapter = self.get_adapter(feature)
        self.adapter = adapter(cookies)
    
    def set_cookies(self, cookies: Cookies) -> None:
        self.adapter.set_cookies(cookies)

    def login(self, username: str, password: str, set_cookies: bool = True) -> Cookies:
        return self.adapter.login(username, password, set_cookies)
    
    @property
    def username(self) -> str | None:
        return self.adapter.username
    
    @property
    def subscription_due_date(self) -> datetime | None:
        return self.adapter.subscription_due_date
    
    def parse_playurl(self, playurl: str) -> Tuple[Season, List[Episode]]:
        return self.adapter.parse_playurl(playurl)
    
    def parse_stream(self, episode: Episode) -> Tuple[List[VideoMedia], Optional[List[AudioMedia]], Optional[List[SubtitleMedia]]]:
        return self.adapter.parse_stream(episode)