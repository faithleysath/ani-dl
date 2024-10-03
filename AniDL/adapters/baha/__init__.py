from AniDL.Models import Season, Episode, VideoMedia, AudioMedia, SubtitleMedia, UrlType, DRMType
from AniDL.Interfaces import BaseAdapterInterface, SeasonNotExistsError
from typing import List, Dict, Any, Optional, Tuple
from httpx import Cookies, Client
from datetime import datetime
import m3u8
import re

headers = {
'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",
'Accept-Encoding': "gzip, deflate",
'sec-ch-ua': "\"Chromium\";v=\"128\", \"Not;A=Brand\";v=\"24\", \"Microsoft Edge\";v=\"128\"",
'dnt': "1",
'sec-ch-ua-mobile': "?0",
'sec-ch-ua-platform': "\"Windows\"",
'sec-fetch-site': "same-origin",
'sec-fetch-mode': "cors",
'sec-fetch-dest': "empty",
'referer': "https://ani.gamer.com.tw/animeVideo.php?sn=18427",
'accept-language': "en-GB,en;q=0.9,en-US;q=0.8,zh-CN;q=0.7,zh;q=0.6",
'priority': "u=1, i",
'Origin': 'https://ani.gamer.com.tw'
}

class BahaAPI:
    season_episode_info = "https://api.gamer.com.tw/anime/v1/video.php?videoSn={sn}"
    master_m3u8 = "https://ani.gamer.com.tw/ajax/m3u8.php?sn={sn}&device={device_id}"

class BahaAdapter(BaseAdapterInterface):
    """巴哈姆特动画疯适配器"""
    class Config:
        adapter_name = "baha"
        base_play_url = ["https://ani.gamer.com.tw/animeRef.php?sn=", "https://ani.gamer.com.tw/animeVideo.php?sn="]
        custom_login = False

    def __init__(self, cookies: Cookies = None):
        self.set_cookies(cookies)
        self.client = Client(headers=headers, cookies=cookies)
        self.device_id = self.client.get('https://ani.gamer.com.tw/ajax/getdeviceid.php').json()['deviceid']

    def set_cookies(self, cookies: Cookies) -> None:
        self.cookies = cookies

    def login(self, username: str, password: str, set_cookies: bool = True) -> Cookies:
        pass

    @property
    def username(self) -> str | None:
        if not self.cookies:
            return None
        response = self.client.get('https://home.gamer.com.tw/profile/index.php', follow_redirects=False)
        # 该请求一定是302重定向，获得重定向地址
        redirect_url = response.headers['Location']
        # 如果登录成功，则定向到https://home.gamer.com.tw/profile/index.php?owner={username}，否则为https://home.gamer.com.tw
        if redirect_url == 'https://home.gamer.com.tw':
            return None
        else:
            username = redirect_url.split('=')[-1]
            return username
        
    @property
    def subscription_due_date(self) -> datetime | None:
        response = self.client.get('https://ani.gamer.com.tw/animePayed.php', follow_redirects=False)
        pattern = re.compile(r"最終服務到期日為 <b>(.+?)</b>")
        result = pattern.search(response.text)
        result = result.group(1) if result else None # 比如2024-10-15 22:51
        return datetime.strptime(result, "%Y-%m-%d %H:%M") if result else None
    
    def parse_playurl(self, playurl: str) -> Tuple[Season, List[Episode]]:
        if playurl.startswith(self.Config.base_play_url[0]):
            # https://ani.gamer.com.tw/animeRef.php?sn=112458
            response = self.client.get(playurl, follow_redirects=False)
            if response.status_code == 301 or response.status_code == 302:
                playurl = response.headers.get('Location')
            else:
                raise SeasonNotExistsError(playurl)
        sn = re.search(r"sn=(\d+)", playurl).group(1)
        url = BahaAPI.season_episode_info.format(sn=sn)
        response = self.client.get(url)
        data = response.json()
        anime = data['data']['anime']
        season_id = anime['animeSn']
        season_title = anime['title']
        season_title = re.sub(r"\[\d+\]", "", season_title).strip() # 对标题要用正则删除[2]这种标记
        season = Season(season_id=season_id, season_title=season_title, namespace=self.Config.adapter_name)
        episodes = []
        raw_episodes = list(anime['episodes'].values())[0]
        for raw_episode in raw_episodes:
            episodes.append(
                Episode(
                    episode_id=raw_episode['videoSn'], 
                    episode_title='', 
                    season_id=season_id, 
                    episode_number=raw_episode['episode'], 
                    namespace=self.Config.adapter_name
                )
            )
        return season, episodes

    def parse_stream(self, episode: Episode) -> Tuple[List[VideoMedia], Optional[List[AudioMedia]], Optional[List[SubtitleMedia]]]:
        """解析剧集流，返回视频、音频、字幕流"""
        url = BahaAPI.master_m3u8.format(sn=episode.episode_id, device_id=self.device_id)
        response = self.client.get(url)
        data = response.json()
        m3u8_url = data['src']
        base_url = m3u8_url.split('playlist_advance.m3u8')[0]
        response = self.client.get(m3u8_url)
        master_m3u8 = response.text
        master_playlist = m3u8.loads(master_m3u8, uri=base_url)
        video_medias = []
        for playlist in master_playlist.playlists:
            video_medias.append(
                VideoMedia(
                    episode_id=episode.episode_id,
                    url=base_url + playlist.uri,
                    url_type=UrlType.HTTPS,
                    headers={'Origin': 'https://ani.gamer.com.tw'},
                    biterate=playlist.stream_info.bandwidth,
                    drm_type=DRMType.HLS,
                    width=playlist.stream_info.resolution[0],
                    height=playlist.stream_info.resolution[1],
                    namespace=self.Config.adapter_name
                )
            )
        return video_medias, None, None