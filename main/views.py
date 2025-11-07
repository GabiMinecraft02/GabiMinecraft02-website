from django.shortcuts import render
from django.conf import settings
from django.views.generic import TemplateView
from pathlib import Path

# ---------------------------
# 🌍 Pages publiques
# ---------------------------

def index(request):
    buttons = {
        "Website": {"Minecraft Modding Website": "..."},
        "Servers": {...},
        "YT & TikTok": {...},
        "Backups": {
            "WantersV1": "/advancements/WantersV1",
            "BakaV1": "/advancements/BakaV1",
            "BakaV2": "/advancements/BakaV2",
            "LasV1": "/advancements/LasV1",
        },
    }
    return render(request, 'main/index.html', {"buttons": buttons})


def advancements(request, folder):
    folder_path = Path(settings.TOOLS_DIR) / folder
    images, texts = [], []

    if folder_path.exists():
        for f in folder_path.iterdir():
            if f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif']:
                images.append(f.name)
            elif f.suffix.lower() in ['.txt', '.md']:
                texts.append(f.read_text(encoding='utf-8'))

    return render(request, 'main/advancements.html', {
        "folder": folder,
        "images": images,
        "texts": texts,
    })
