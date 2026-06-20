import csv
import os
import sys

from PIL import Image
from PySide6.QtGui import QPixmap

from models import ImageData


def get_base_path():
    """获取可写文件（config.json, tags/）存放的目录（exe所在目录）"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def get_resource_path(relative_path):
    """获取只读资源（如 icons）的路径，兼容开发与打包"""
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)


def scan_folder(folder_path):
    """扫描文件夹，返回 {文件名: ImageData}"""
    images = {}
    if not os.path.isdir(folder_path):
        return images
    img_exts = ('.jpg', '.jpeg', '.png', '.webp', '.bmp')
    for fname in os.listdir(folder_path):
        if fname.lower().endswith(img_exts):
            full_path = os.path.join(folder_path, fname)
            txt_name = os.path.splitext(fname)[0] + '.txt'
            txt_path = os.path.join(folder_path, txt_name)
            tags = []
            if os.path.isfile(txt_path):
                with open(txt_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        tags = [t.strip() for t in content.split(',') if t.strip()]
            img_data = ImageData(
                path=full_path,
                txt_path=txt_path,
                original_tags=list(tags),
                tags=list(tags),
            )
            try:
                with Image.open(full_path) as img:
                    img_data.width, img_data.height = img.size
            except Exception:
                img_data.width, img_data.height = 0, 0
            images[fname] = img_data
    return images

def generate_thumbnail(path, size=(100, 100)):
    """生成缩略图"""
    try:
        with Image.open(path) as img:
            img.thumbnail(size)
            from PIL.ImageQt import ImageQt
            qim = ImageQt(img)
            return QPixmap.fromImage(qim)
    except Exception:
        return QPixmap(size)

def load_tag_metadata(csv_path):
    """读取标准标签"""
    metadata = {}
    if not os.path.isfile(csv_path):
        return metadata

    # 尝试 utf-8-sig，失败则 gb18030
    content = None
    for encoding in ['utf-8-sig', 'gb18030']:
        try:
            with open(csv_path, 'r', encoding=encoding) as f:
                content = f.read()
            break
        except UnicodeDecodeError:
            continue
    if content is None:
        return metadata

    from io import StringIO
    reader = csv.reader(StringIO(content))
    for row in reader:
        if len(row) >= 1:
            tag = row[0].strip().replace('_', ' ')
            if not tag:
                continue
            # B列(索引1) 作为翻译
            translation = row[1].strip() if len(row) > 1 else ''
            category = ''
            metadata[tag] = {
                'category': category,
                'frequency': 0,          # 频率由程序统计
                'translation': translation
            }
    return metadata

def load_custom_tags(csv_path):
    """读取自定义标签"""
    custom = {}
    if not os.path.isfile(csv_path):
        return custom
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        # 无表头，直接读
        for row in reader:
            if len(row) >= 2:
                tag = row[0].strip().replace('_', ' ')
                trans = row[1].strip()
                if tag:
                    custom[tag] = trans
    return custom

def save_custom_tags(csv_path, custom_dict):
    """保存自定义标签CSV"""
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        # 不写表头，直接写数据行
        for tag, trans in sorted(custom_dict.items()):
            writer.writerow([tag, trans])

def compute_tag_frequencies(images):
    """统计所有图片中各标签出现次数"""
    freq = {}
    for img in images.values():
        for tag in img.tags:
            freq[tag] = freq.get(tag, 0) + 1
    return freq

def update_metadata_frequencies(metadata, freq):
    """将统计频率写入metadata"""
    for tag, count in freq.items():
        if tag in metadata:
            metadata[tag]['frequency'] = count
        else:
            metadata[tag] = {'category': '', 'frequency': count, 'translation': ''}
    for tag in metadata:
        if tag not in freq:
            metadata[tag]['frequency'] = 0