# <center>Note: The interface is currently Chinese-only.</center>
<div align="center">

[简体中文](https://github.com/70SeptZero/LoRA-Training-Tool-LaylaTagManager) | __English__
</div>

# LaylaTagManager

A LoRA training tag manager I wrote for myself.

The archive is only 29MB (7z), 65MB after extraction, comes with a built-in Python environment, no setup needed, just open and use.

## A Bit of Background
It started when I was using BooruDatasetTagManager and felt that having the image on a separate page was a bit inconvenient, so I (DeepSeek) wrote a tool that integrates the image viewer into the main interface (and simplified some other features as well).  
Then I merged danbooru.csv, e621.csv, and translations into a single tags.csv with around 210,000 tag entries, which is pretty much enough.  
Actually, I had DeepSeek write this software for my own use, so it's only in Chinese. After a lot of bug fixing and performance tweaking, it now feels pretty good to use.

## What It Can Do
With a training set full of images and txt files, editing tags can be exhausting. This tool puts the image right next to the tags, so you can view and edit at the same time, saving a lot of effort.

- View images on the left, edit the current image's tags in the middle, batch operations on the right.
- Tag autocomplete with Chinese translation.
- For the translation feature, I added custom translation support: double-click a translation to edit it, and from then on your version will be used.
- The top toolbar in the middle includes: Add Tag (Ctrl+E), Delete Tag (Delete), Undo (Ctrl+Z), Search (Ctrl+F).
- Batch add, delete, replace tags, or find images containing a certain tag — just a few clicks.
- After editing and saving, the txt file is updated; discard changes and it stays exactly as before.

## Interface

![Main interface](https://github.com/70SeptZero/LoRA-Training-Tool-LaylaTagManager/blob/master/README/img/1.png)

Three-column layout, drag to adjust widths freely.

## How to Use

1. Top-left File -> Open Folder, select the folder containing images (subfolders are not searched).
2. Select an image on the left; its tags appear in the middle.
3. Double-click a tag to edit, or use Up/Down arrow keys to select a tag, press Enter to edit, Left/Right arrows to reorder.
4. The top toolbar lets you add, delete, undo, and search tags.
5. The right panel is for batch editing the entire dataset.
6. Ctrl+S to save.

![Demo](https://github.com/70SeptZero/LoRA-Training-Tool-LaylaTagManager/blob/master/README/gif/2.png)

## Main Features

### Autocomplete and Translation
Type to autocomplete tags, use Up/Down to select and Enter to confirm. The data comes from [a1111-sd-webui-tagcomplete](https://github.com/DominikDoom/a1111-sd-webui-tagcomplete), with danbooru.csv and e621.csv merged, along with some translations.

### Custom Translations and Tags
If a translation is inaccurate or missing, just double-click to edit it. After editing, that tag will show your custom translation and appear higher in autocomplete results. Once you've edited a translation, the tag is marked as a custom tag.
![Custom Tags](https://github.com/70SeptZero/LoRA-Training-Tool-LaylaTagManager/blob/master/README/gif/3.png)

### Left: Image and File List
Large image on top, thumbnail list at the bottom, with a draggable divider in between: pull it all the way down to show only the large image, or all the way up to show only the list.
![Demo](https://github.com/70SeptZero/LoRA-Training-Tool-LaylaTagManager/blob/master/README/gif/1.png)

### Middle: Current Image Tags
- Double-click a tag to edit, or select and press Enter
- Ctrl+E to add, Delete to remove, Ctrl+Z to undo, Ctrl+F to search
- Up/Down to select tags, __Left/Right__ to adjust tag position
- Press a letter key to jump to tags starting with that letter

![Edit Tags](https://github.com/70SeptZero/LoRA-Training-Tool-LaylaTagManager/blob/master/README/img/3.png)

### Right: Batch Operations
- **Add tags to all images**: add to the beginning, the end, or a specific position (enter a number: 1 means first, too large a number puts it at the end)
- **Delete a tag**: remove the selected tag from the entire folder
- **Replace a tag**: replace the selected tag with another one entirely
- **Search by tag**: filter to show only images containing the selected tag, click "Exit Search" to restore all images

### Settings
Settings allow you to modify: font size, top toolbar display mode, and keyboard shortcuts.
![setting](https://github.com/70SeptZero/LoRA-Training-Tool-LaylaTagManager/blob/master/README/img/2.png)

## How to Run

### Download and Run Directly (Recommended)
Download the archive from [Releases](https://github.com/70SeptZero/LoRA-Training-Tool-LaylaTagManager/releases/tag/v1.0.0), extract it, and double-click `LaylaTagManager.exe`.

No need to install Python or configure environments. The archive is 29MB (7z) or 35MB (zip), 65MB after extraction.

Files in Tags are data of tags. Your custom tags are saved in `custom_tags.csv`
Your configuration including layout is saved in `config.json`

### Run from Source
The code uses the uv environment, all source code is in the LaylaTagManager folder, just run `main.py`.
Dependencies: pyside6-essentials and pillow, already listed in `pyproject.toml`.
Make sure you have __uv__ installed first.
```bash
git clone https://github.com/70SeptZero/LoRA-Training-Tool-LaylaTagManager.git
uv sync
uv run python LaylaTagManager/main.py
```

# Acknowledgements
[BooruDatasetTagManager](https://github.com/starik222/BooruDatasetTagManager) for the initial idea and layout

[a1111-sd-webui-tagcomplete](https://github.com/DominikDoom/a1111-sd-webui-tagcomplete)for the tag data

# Other
The interface is Chinese-only, though there aren't many words.

The repository contains source code; the packaged exe is in Releases.

For questions or suggestions, go to [Issues](https://github.com/70SeptZero/LoRA-Training-Tool-LaylaTagManager/issues).

If you find it useful, a Star would let me know — thanks!