from AniDL.adapters import Adapter
from httpx import Cookies
import rich

cookies = ''

import json
cookies_json = json.loads(cookies)
cookies = Cookies()
for cookie in cookies_json:
    cookies.set(name=cookie['name'], value=cookie['value'], domain=cookie['domain'])

adapter = Adapter('baha', cookies=cookies)
print(adapter.username)
print(adapter.subscription_due_date)
season, episodes = adapter.parse_playurl('https://ani.gamer.com.tw/animeVideo.php?sn=40122')
rich.print(season)
rich.print(episodes)
episode = episodes[0]
video_medias, audio_medias, subtitle_medias = adapter.parse_stream(episode)
rich.print(video_medias)