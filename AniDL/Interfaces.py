from .Models import Season, Episode, Media, VideoMedia, AudioMedia, SubtitleMedia
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
from datetime import datetime
from httpx import Cookies

class BaseAdapterInterface(ABC):
    """基础适配器接口"""
    # 定义一些常量
    class Config:
        """配置类"""
        adapter_name: str
        base_play_url: List[str]
        custom_login: bool = False # 是否需要自定义登录

    @abstractmethod
    def __init__(self, cookies: Optional[Cookies] = None):
        """初始化适配器"""
        pass

    @abstractmethod
    def set_cookies(self, cookies: Cookies) -> None:
        """设置 cookies"""
        pass

    @abstractmethod
    def login(self, username: str, password: str, set_cookies: Optional[bool] = True) -> Cookies:
        """登录返回 cookies"""
        pass

    @property
    @abstractmethod
    def username(self) -> str | None:
        """返回用户名，也可以用来检查是否登录"""
        pass

    @property
    @abstractmethod
    def subscription_due_date(self) -> datetime | None:
        """返回订阅到期时间，也可以用来检查是否订阅"""
        pass

    @abstractmethod
    def parse_playurl(self, playurl: str) -> Tuple[Season, List[Episode]]:
        """解析播放链接，返回剧集信息"""
        pass

    @abstractmethod
    def parse_stream(self, episode: Episode) -> Tuple[List[VideoMedia], Optional[List[AudioMedia]], Optional[List[SubtitleMedia]]]:
        """解析剧集流，返回视频、音频、字幕流"""
        pass