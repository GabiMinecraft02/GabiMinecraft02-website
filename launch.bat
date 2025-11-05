@echo off
title Lancement du site GabiMinecraft02
echo ==========================================
echo      🚀 Lancement du serveur Django
echo ==========================================
echo.

REM Aller dans le dossier du projet
cd /d "%~dp0"

REM Activer l'environnement virtuel
call venv\Scripts\activate.bat

REM Lancer le serveur Django
python manage.py runserver 5000

REM Garder la fenêtre ouverte
pause