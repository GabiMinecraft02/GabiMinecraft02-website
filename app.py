from flask import Flask, render_template, request, redirect, url_for
import os

app = Flask(__name__)

# Dossier des fichiers uploadés
UPLOAD_FOLDER = os.path.join("static", "uploads")
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Page d'accueil (redirige vers /advancements)
@app.route("/")
def home():
    return redirect(url_for("advancements"))

# Route pour afficher les publications
@app.route("/advancements")
def advancements():
    images = []
    texts = []
    if os.path.exists(UPLOAD_FOLDER):
        # Récupère toutes les images
        images = [f for f in os.listdir(UPLOAD_FOLDER) if f.lower().endswith((".jpg", ".jpeg", ".png", ".gif"))]
        # Récupère les textes
        text_file = os.path.join(UPLOAD_FOLDER, "text.txt")
        if os.path.exists(text_file):
            with open(text_file, "r", encoding="utf-8") as f:
                texts = [line.strip() for line in f.readlines()]
    return render_template("advancements.html", images=images, texts=texts)

# Route pour uploader une image
@app.route("/upload_image", methods=["POST"])
def upload_image():
    if "image" not in request.files or request.files["image"].filename == "":
        return redirect(url_for("advancements"))
    file = request.files["image"]
    filename = file.filename
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    return redirect(url_for("advancements"))

# Route pour uploader du texte
@app.route("/upload_text", methods=["POST"])
def upload_text():
    text_content = request.form.get("text_content", "").strip()
    if text_content:
        text_file = os.path.join(UPLOAD_FOLDER, "text.txt")
        with open(text_file, "a", encoding="utf-8") as f:
            f.write(text_content + "\n")
    return redirect(url_for("advancements"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render fournit le port
    app.run(host="0.0.0.0", port=port)
