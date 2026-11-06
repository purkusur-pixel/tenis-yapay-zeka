"""
ADIM 5 — Arayüz olmadan, yalnızca konsoldan tahmin.  (cikti/onhesap.json'u okur)

    python 05_konsol_tahmin.py Kadınlar Low 27x 29     # tek seferlik
    python 05_konsol_tahmin.py                         # etkileşimli (yardim, cikis)
"""
import sys

from tenis import onhesap as O

tablo = O.OnHesap()
secim = {"cinsiyet": "Erkekler", "kategori": "Middle", "vuran": None, "rakip": None,
         "model": O.OTOMATIK}


def isle(satir: str) -> bool:
    try:
        komut, degisim = O.komut_coz(satir)
    except ValueError as e:
        print(f"  ⚠ {e}")
        return True
    if komut == "cikis":
        return False
    if komut == "yardim":
        print(O.YARDIM)
    elif komut == "temizle":
        secim.update(vuran=None, rakip=None)
    elif komut == "durum":
        print("  " + ", ".join(f"{k}={v}" for k, v in secim.items()))
    secim.update(degisim)
    if degisim:
        if secim["vuran"] and secim["rakip"]:
            print(O.metin_ozeti(secim, tablo.sorgula(**secim)))
        else:
            print(f"  Eksik: {'vuran' if not secim['vuran'] else 'rakip'}")
    return True


if len(sys.argv) > 1:
    isle(" ".join(sys.argv[1:]))
else:
    print("Tenis atış önerisi — konsol modu (yardım: yardim, çıkış: cikis)")
    while True:
        try:
            if not isle(input("komut> ")):
                break
        except (EOFError, KeyboardInterrupt):
            break
