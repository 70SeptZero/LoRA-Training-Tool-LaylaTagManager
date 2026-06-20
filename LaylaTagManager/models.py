from dataclasses import dataclass, field
from PySide6.QtGui import QPixmap

@dataclass
class ImageData:
    path: str                   # 图片文件绝对路径
    txt_path: str               # 对应标签txt路径
    original_tags: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    thumbnail: QPixmap = None   # 缩略图
    width: int = 0
    height: int = 0

    def is_modified(self) -> bool:
        return self.tags != self.original_tags