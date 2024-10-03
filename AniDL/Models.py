from typing import Dict, Tuple, Any, List, Type, Optional
from pydantic import BaseModel, Field
from copy import deepcopy
from enum import Enum
import weakref

class IndexModelError(Exception):
    """基础异常类，用于索引模型相关的错误"""
    def __init__(self, message: str):
        super().__init__(message)

class MissingFieldError(IndexModelError):
    """当缺少索引字段时引发的异常"""
    def __init__(self, field_name: str):
        message = f"索引字段 '{field_name}' 不存在。"
        super().__init__(message)

class DuplicateFieldError(IndexModelError):
    """当索引字段重复时引发的异常"""
    def __init__(self, field_name: str):
        message = f"索引字段 '{field_name}' 已存在。"
        super().__init__(message)

class InstanceAlreadyExistsError(IndexModelError):
    """当实例已经存在时引发的异常"""
    def __init__(self, key_values: Tuple[Any, ...], namespace: str):
        message = f"索引值 '{key_values}' 已存在于命名空间 '{namespace}' 中！"
        super().__init__(message)

class NoIndexFieldsError(IndexModelError):
    """当未找到索引字段时引发的异常"""
    def __init__(self, class_name: str):
        message = f"{class_name} 类必须用 @index_field 装饰器标记索引字段！"
        super().__init__(message)

class InstanceNotFoundError(IndexModelError):
    """当实例未找到时引发的异常"""
    def __init__(self, keys: Tuple[Any, ...], namespace: str):
        message = f"索引 {keys} 不存在于命名空间 '{namespace}' 中！"
        super().__init__(message)

class InstanceGarbageCollectedError(IndexModelError):
    """当实例已被垃圾回收时引发的异常"""
    def __init__(self, keys: Tuple[Any, ...]):
        message = f'索引 {keys} 的实例已被垃圾回收！'
        super().__init__(message)

class EmptyFieldNamesError(IndexModelError):
    """当索引字段名称为空时引发的异常"""
    def __init__(self):
        message = "索引字段名称不能为空。"
        super().__init__(message)

class FieldNameTypeError(IndexModelError):
    """当索引字段名称不是字符串时引发的异常"""
    def __init__(self, field_name: Any):
        message = f"索引字段名称 '{field_name}' 必须是字符串。"
        super().__init__(message)

class EmptyKeysError(IndexModelError):
    """当索引字段为空时引发的异常"""
    def __init__(self):
        message = "索引字段不能为空！"
        super().__init__(message)

class KeysMismatchError(IndexModelError):
    """当索引字段数量不匹配时引发的异常"""
    def __init__(self, expected: int, provided: int):
        message = f"索引字段数量不匹配！预期: {expected}，提供: {provided}。"
        super().__init__(message)


def index_field(*field_names):
    """装饰器，用于标记索引字段"""
    if not field_names:
        raise EmptyFieldNamesError()
    for field_name in field_names:
        if not isinstance(field_name, str):
            raise FieldNameTypeError(field_name)
    
    def decorator(cls: Type[IndexBaseModel]):
        # 给cls添加一个新的Config类
        if not hasattr(cls.Config, 'index_fields'):
            setattr(cls, 'Config', type('Config', (), {'instances': {}, 'index_fields': []}))
        # 检查字段是否在模型中
        for field_name in field_names:
            if field_name not in cls.__fields__:
                raise MissingFieldError(field_name)
        for field_name in field_names:
            if field_name in cls.Config.index_fields:
                raise DuplicateFieldError(field_name)
            cls.Config.index_fields = deepcopy(cls.Config.index_fields)
            cls.Config.index_fields.append(field_name)
        return cls
    return decorator

class IndexBaseModel(BaseModel):
    """带索引功能的基础模型"""

    namespace: str = Field(default="global")

    class Config:
        instances: Dict[str, Dict[Tuple[Any, ...], weakref.ref]]
        index_fields: List[str]

    def __init__(self, **data: Any):
        super().__init__(**data)
        # 检查Config类中是否存在index_fields属性
        if not hasattr(self.__class__.Config, 'index_fields'):
            raise NoIndexFieldsError(self.__class__.__name__)
        # 自动存储实例到类变量
        key_values = self._get_index_values()
        namespace_instances = self.__class__.Config.instances.setdefault(self.namespace, {})
        if key_values in namespace_instances and namespace_instances[key_values]() is not None:
            raise InstanceAlreadyExistsError(key_values, self.namespace)
        # 使用弱引用保存实例
        namespace_instances[key_values] = weakref.ref(self)
    
    def _get_index_values(self) -> Tuple[Any, ...]:
        """获取索引字段的值"""
        index_keys = self.__class__.Config.index_fields
        if not index_keys:
            raise NoIndexFieldsError(self.__class__.__name__)
        return tuple(getattr(self, key) for key in index_keys)
    
    @classmethod
    def get_instances(cls, namespace: str = "global") -> Dict[Tuple[Any, ...], weakref.ref]:
        """获取命名空间中的实例字典"""
        return cls.Config.instances.get(namespace, {})
    
    @classmethod
    def clear_instances(cls, namespace: str = "global"):
        """清空命名空间中的所有实例"""
        cls.Config.instances[namespace].clear()

    @classmethod
    def clear_all_instances(cls):
        """清空所有命名空间中的实例"""
        cls.Config.instances.clear()
    
    @classmethod
    def get(cls: Type['IndexBaseModel'], *keys, namespace: str = "global") -> 'IndexBaseModel':
        """通过索引字段获取实例"""
        if not keys:
            raise EmptyKeysError()
        if len(keys) != len(cls.Config.index_fields):
            raise KeysMismatchError(len(cls.Config.index_fields), len(keys))
        namespace_instances = cls.get_instances(namespace)
        try:
            instance_ref = namespace_instances[keys]
            instance_ref = instance_ref()
            if instance_ref is None:
                raise InstanceGarbageCollectedError(keys)
            return instance_ref
        except KeyError:
            raise InstanceNotFoundError(keys, namespace)

@index_field('season_id')
class Season(IndexBaseModel):
    """描述剧集的季信息"""
    season_id: int
    season_title: str

@index_field('episode_id')
class Episode(IndexBaseModel):
    """描述剧集的集信息"""
    episode_id: int
    episode_title: str
    season_id: int
    episode_number: int # 集数

class UrlType(str, Enum):
    """描述媒体资源的类型"""
    HTTP = "http"
    HTTPS = "https"
    FTP = "ftp"
    LOCAL = "local"
    SMB = "smb"

class DRMType(str, Enum):
    """描述数字版权管理类型"""
    FAIRPLAY = "fairplay"
    WIDEVINE = "widevine"
    PLAYREADY = "playready"
    # 普通的加密方式
    AES = "aes"
    DES = "des"
    RSA = "rsa"
    chaCha20 = "chacha20"

@index_field('episode_id')
class Media(IndexBaseModel):
    """描述媒体资源信息"""
    episode_id: int
    url: str
    url_type: UrlType
    headers: Optional[Dict[str, str]] = None # 自定义请求头
    size: Optional[int] = None # 文件大小，单位：字节
    length: Optional[int] = None # 媒体时长，单位：毫秒
    drm_type: Optional[DRMType] = None
    drm_info: Optional[dict] = None # 可能的值：key, iv, license_url, license_headers, cene

resolution_to_quality = {
    (3840, 2160): "4K",
    (1920, 1080): "1080P",
    (1280, 720): "720P",
    (854, 480): "480P",
    (640, 360): "360P",
    (426, 240): "240P",
}

@index_field('quality', 'codec')
class VideoMedia(Media):
    """描述视频媒体资源信息"""
    width: int
    height: int
    codec: Optional[str] = None
    quality: Optional[str] = None
    def __init__(self, **data):
        super().__init__(**data)
        if not self.quality:
            self.quality = resolution_to_quality.get((self.width, self.height), "未知")

@index_field('language', 'codec')
class AudioMedia(Media):
    """描述音频媒体资源信息"""
    codec: Optional[str] = None
    language: Optional[str] = None

class SubtitleType(str, Enum):
    """描述字幕类型"""
    SRT = "srt"
    ASS = "ass"

@index_field('language', 'subtitle_type')
class SubtitleMedia(Media):
    """描述字幕媒体资源信息"""
    subtitle_type: SubtitleType
    language: str