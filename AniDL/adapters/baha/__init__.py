from AniDL.Interfaces import BaseAdapterInterface

class BahaAdapter(BaseAdapterInterface):
    """巴哈姆特动画疯适配器"""
    class Config:
        adapter_name = "baha"
        base_play_url = ["https://ani.gamer.com.tw/animeRef.php?sn=", "https://ani.gamer.com.tw/animeVideo.php?sn="]
        custom_login = False

    