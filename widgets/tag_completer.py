from PySide6.QtCore import Qt, QStringListModel

CUSTOM_ROLE = Qt.ItemDataRole.UserRole + 1
MAX_COMPLETION_ITEMS = 15   # 数量限制


class TagListModel(QStringListModel):
    """支持显示 'tag[翻译]' 的模型，不再重写 match"""
    def __init__(self, tags, translation_callback=None, parent=None):
        super().__init__(tags, parent)
        self.translation_callback = translation_callback
        self._cache = {}

    def clear_cache(self):
        self._cache.clear()

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and self.translation_callback:
            tag = super().data(index, Qt.ItemDataRole.DisplayRole)
            if tag not in self._cache:
                trans = self.translation_callback(tag)
                self._cache[tag] = f"{tag}  [{trans}]" if trans else tag
            return self._cache[tag]
        if role == CUSTOM_ROLE:
            return super().data(index, Qt.ItemDataRole.DisplayRole)   # 纯 tag
        return super().data(index, role)


def create_completer_model(sorted_tags):
    """返回源模型（TagListModel），后面会动态替换"""
    return TagListModel(sorted_tags)