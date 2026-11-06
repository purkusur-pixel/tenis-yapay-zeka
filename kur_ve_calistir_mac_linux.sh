#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
echo "=== Tenis Akıllı Atış Sistemi - Kurulum ==="
if [ ! -d venv ]; then
    echo "Sanal ortam oluşturuluyor..."
    python3 -m venv venv
fi
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if [ ! -f cikti/onhesap.json ]; then
    echo; echo "=== Modeller eğitiliyor (bir kez, 2-3 dakika) ==="
    python 04_atis_modeli_egit.py
fi
echo; echo "=== Arayüz açılıyor — bu terminale komut yazabilirsiniz (yardim) ==="
python gui_atis.py
