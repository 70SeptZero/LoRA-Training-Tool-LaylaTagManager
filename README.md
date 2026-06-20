<div align="center">

__简体中文__ | [English](./README/README_EN.md) 

</div>

# LaylaTagManager

一个给自己写的 LoRA 训练标签管理器。

压缩包只有 29MB（7z），解压完 65MB，自带 Python 环境，不用折腾，打开就能用。

## 一点背景
起因是在用BooruDatasetTagManager的时候，感觉图片单独一个页面不太方便，于是就自己（ds）写了个把图片界面给集成到主界面的效果（顺手给其他功能也简化了一下）  

然后把danbooru.csv和e621.csv和翻译给整合成了一个tags.csv，里面有21万条tag数据，差不多够用了  

其实这个软件就是我让ds给我写来自己用的，因为我想要一个看图功能也集成进去的TagManager，所以只有中文。折腾了半天改bug优化性能，目前感觉挺好用的。

## 这玩意儿能干啥

训练集里一堆图片和 txt，改Tag改到眼花。这个工具把图片直接放Tag旁边，边看边改，省事不少。

- 左边看图，中间改当前图片的Tag，右边批量操作。
- Tag自动补全，还带中文翻译。
- 针对这个翻译功能，添加了自定义翻译的设计，双击翻译文字自己改，以后都按你改的来。
- 批量给所有图片加标签、删标签、替换标签、查找含某标签的图，点几下就行。
- 编辑完保存后txt就会更新，放弃保存就完全保持原样。


## 界面

![主界面](https://github.com/70SeptZero/LoRA-Training-Tool-LaylaTagManager/blob/master/README/img/1.png)

三栏布局，宽度随便拖。

## 使用方法

1. 左上角文件 -> 打开文件夹，选图片所在的文件夹（不搜子文件夹）。
2. 左边选择图片，中间展示这张图片的Tag。
3. 双击Tag进行编辑，也可以使用上下键选择标签，选中后按Enter编辑，左右键调顺序。
4. 中间上方工具栏包括：添加Tag(Ctrl+E)、删除Tag(Delete)、撤销(Ctrl+Z)、搜索(Ctrl+F)
5. 右边批量改整个数据集：给所有图片添加Tag、删除Tag、替换Tag、查询包含Tag的图片
6. Ctrl+S 保存。

![使用演示](https://github.com/70SeptZero/LoRA-Training-Tool-LaylaTagManager/blob/master/README/gif/2.gif)


## 主要功能

### 自动补全和翻译

打字自动提示标签,上下选择后按Enter键。数据用的是 [a1111-sd-webui-tagcomplete](https://github.com/DominikDoom/a1111-sd-webui-tagcomplete) 的，把danbooru.csv和e621.csv给合并了，还合并了一部分翻译进去

### 自定义翻译与标签

感觉翻译不行或者缺少翻译就双击直接改。改完以后这个标签都会显示你改的翻译，自动补全时这个Tag也会排在前面。你只需要编辑过翻译，就会把这个tag标记成自定义tag了。  

![自定义翻译](https://github.com/70SeptZero/LoRA-Training-Tool-LaylaTagManager/blob/master/README/gif/3.gif)

### 左边：图片和文件列表

上边大图，下边缩略图列表，中间分割条可以拉，拉到底只留大图，拉到顶部就只留列表。
![使用演示](https://github.com/70SeptZero/LoRA-Training-Tool-LaylaTagManager/blob/master/README/gif/1.gif)

### 中间：当前图片的标签

- 双击标签编辑，或者选中后按Enter
- Ctrl+E 添加，Delete 删除，Ctrl+Z 撤销，Ctrl+F 搜索
- 上下键选标签，__左右键__ 调整当前标签的位置
- 直接按字母键可以跳转该首字母的Tag

![编辑标签](https://github.com/70SeptZero/LoRA-Training-Tool-LaylaTagManager/blob/master/README/img/3.png)

### 右边：批量操作

- **给所有图片加标签**：可以加到开头、结尾或指定位置（填数字，1 就是第一个，超过tag数了就放最后）
- **删掉某标签**：整个文件夹统一去掉选中的这个标签
- **替换标签**：把选中的标签全改成另一个
- **查标签**：只看包含选中标签的图片，点旁边的“退出查询”恢复显示所有图片

### 设置
设置可以修改：字号、顶部工具栏显示方式、快捷键  

![设置](https://github.com/70SeptZero/LoRA-Training-Tool-LaylaTagManager/blob/master/README/img/2.png)

## 运行方法

### 下载直接用（推荐）

去 [Releases](https://github.com/70SeptZero/LoRA-Training-Tool-LaylaTagManager/releases/tag/v1.0.0) 下压缩包，解压，双击 `LaylaTagManager.exe`。

不用装 Python，不用配环境。压缩包 29MB（7z）或 35MB（zip），解压后 65MB。

Tags是标签文件，自定义标签放在`custom_tags.csv`中的

`config.json`是你的一些配置文件，比如界面布局等

### 从源码运行
代码环境采用了uv环境，所有源码都在LaylaTagManager文件夹下，运行 `main.py` 文件即可

使用了：pyside6-essentials和pillow

已经写在`pyproject.toml`中了

最后，请确保您已经安装了 __uv__ 环境
```bash
git clone https://github.com/70SeptZero/LoRA-Training-Tool-LaylaTagManager.git
uv sync
uv run python LaylaTagManager/main.py
```
# 感谢
[BooruDatasetTagManager](https://github.com/starik222/BooruDatasetTagManager) 提供了最初的想法和布局

[a1111-sd-webui-tagcomplete](https://github.com/DominikDoom/a1111-sd-webui-tagcomplete) 的标签数据

# 其他
只有中文界面，虽然也没几个字。

仓库里是源码，打包好的 exe 在 Releases。

有问题或者建议去 [Issues](https://github.com/70SeptZero/LoRA-Training-Tool-LaylaTagManager/issues) 提。

如果觉得好用，点个 Star 让我知道，谢啦。