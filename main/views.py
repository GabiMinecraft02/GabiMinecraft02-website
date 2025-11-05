from django.shortcuts import render
from django.conf import settings
from pathlib import Path

def index(request):
    # Catégories et boutons
    buttons = {
        "Website": {"Minecraft Modding Website": "https://minecraft-ps3-moding-website.onrender.com/"},
        "Servers": {
            "PS3 Backup Discord": "https://discord.gg/ex8Jgrm255",
            "YouTube Server": "https://discord.gg/dZUEhNZWWD",
            "Snapchat Chat": "https://snapchat.com/t/NuFx4joB",
        },
        "YT & TikTok": {
            "YouTube": "https://www.youtube.com/@GabiMinecraft02ps3",
            "TikTok": "https://www.tiktok.com/@gabiminecraft028",
        },
        "Backups": ["WantersV1", "BakaV1", "BakaV2", "LasV1"],
    }
    return render(request, 'main/index.html', {"buttons": buttons})

def advancements(request, folder):
    folder_path = Path(settings.TOOLS_DIR) / folder
    images = []
    texts = []
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
