from flask import Flask, render_template
import os

app = Flask(__name__)

# 📁 Dossier des publications
UPLOAD_FOLDER = os.path.join("static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -----------------------------
# ROUTE MENU PRINCIPAL
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")  # menu principal

# -----------------------------
# ROUTE BACKUP
# -----------------------------
@app.route("/backup")
def backup():
    return render_template("backup.html")  # créer ce template ou remplacer par un message

# -----------------------------
# ROUTE ADVANCEMENTS
# -----------------------------
@app.route("/advancements")
def advancements():
    # Liste des images
    images = [f for f in os.listdir(UPLOAD_FOLDER) if f.lower().endswith((".jpg", ".png", ".jpeg", ".gif"))]
    
    # Texte
    text_file = os.path.join(UPLOAD_FOLDER, "text.txt")
    texts = []
    if os.path.exists(text_file):
        with open(text_file, "r", encoding="utf-8") as f:
            texts = f.readlines()
    
    return render_template("advancements.html", images=images, texts=texts)

# -----------------------------
# LANCEMENT DE L'APPLICATION
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)
