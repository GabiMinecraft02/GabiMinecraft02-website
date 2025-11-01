@echo off
title Lancement du site Flask - GabiMinecraft02
echo ===========================================
echo   🚀 Lancement du site Flask localement
echo ===========================================

:: Aller dans le dossier du projet
cd /d "C:\Users\gabri\Desktop\projets\GabiMinecraft02 website"

:: Active l'environnement virtuel si présent
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate
)

:: Lancer Flask
python app.py

:: Si Flask plante, garder la fenêtre ouverte
if %errorlevel% neq 0 (
    echo ⚠️ Le serveur Flask s'est arrêté avec une erreur.
)

pause
