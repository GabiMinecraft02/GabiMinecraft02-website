from django.shortcuts import render
from pathlib import Path
from django.conf import settings

# ---------------------------
# 🌍 Pages publiques
# ---------------------------

def index(request):
    buttons = {
        "Website": {"Minecraft Modding Website": "https://minecraft-ps3-moding-website.onrender.com/"},
        "Servers": {
            "PS3 Backup Discord": "https://discord.gg/ex8Jgrm255",
            "YouTube Server": "https://discord.gg/dZUEhNZWWD",
            "Snapchat Chat": "https://snapchat.com/t/NuFx4joB",
        },
        "YT & TikTok": {
            "YouTube": "https://www.youtube.com/@GabiMinecraft02ps3",
            "TikTok": "https://www.tiktok.com/@gabiminecraft028?is_from_webapp=1&sender_device=pc",
        },
        "Backups": {
            "WantersV1": "/advancements/WantersV1",
            "BakaV1": "/advancements/BakaV1",
            "BakaV2": "/advancements/BakaV2",
            "LasV1": "/advancements/LasV1",
        },
    }
def index(request):
    return render(request, 'main/index.html')


def advancements(request, folder):
    # Chemin sur le disque vers static/advancements/<folder>
    folder_path = Path(settings.STATICFILES_DIRS[0]) / "advancements" / folder
    static_rel_path = f"advancements/{folder}/"

    images, texts = [], []

    if folder_path.exists():
        for f in sorted(folder_path.iterdir()):
            if f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
                images.append(static_rel_path + f.name)
            elif f.suffix.lower() in ['.txt', '.md']:
                texts.append(f.read_text(encoding='utf-8'))

    return render(request, 'main/advancements.html', {
        "folder": folder,
        "backup_title": folder,
        "images": images,
        "texts": texts,
    })
