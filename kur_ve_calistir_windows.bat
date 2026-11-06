@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === Tenis Akilli Atis Sistemi - Kurulum ===
if not exist venv (
    echo Sanal ortam olusturuluyor...
    py -m venv venv || python -m venv venv
)
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if not exist cikti\onhesap.json (
    echo.
    echo === Modeller egitiliyor ^(bir kez, 2-3 dakika^) ===
    python 04_atis_modeli_egit.py
)
echo.
echo === Arayuz aciliyor - bu pencereye komut yazabilirsiniz (yardim) ===
python gui_atis.py
pause
