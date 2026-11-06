"""
Önceden hesaplanmış tahmin tablosu (cikti/onhesap.json) + komut çözücü.

Modeller 04_atis_modeli_egit.py ile BİR KEZ eğitilir; tüm girdi kombinasyonlarının
(cinsiyet x kategori x vuran x rakip) sonuçları bu dosyaya yazılır. Arayüz ve
konsol yalnızca bu tabloyu okur → anında yanıt, scikit-learn / XGBoost gerekmez.

Bu dosya yalnızca Python standart kütüphanesini kullanır.
"""
from __future__ import annotations

import json
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
ONHESAP_DOSYASI = KOK / "cikti" / "onhesap.json"

OTOMATIK = "Otomatik (en iyi)"
DISARI = "OUTSIDE"
VURAN_SECENEKLERI = [f"{n}x" for n in range(1, 33)] + [DISARI]   # alt yarı
RAKIP_SECENEKLERI = [str(n) for n in range(1, 33)] + [DISARI]    # üst yarı
CINSIYETLER = ["Erkekler", "Kadınlar"]
KATEGORILER = ["Middle", "Low"]
KATEGORI_GORUNEN = {"Middle": "Orta", "Low": "Low"}


def anahtar(cinsiyet, kategori, vuran, rakip) -> str:
    return f"{cinsiyet}|{kategori}|{vuran}|{rakip}"


class OnHesap:
    def __init__(self, yol: Path = ONHESAP_DOSYASI):
        if not Path(yol).exists():
            raise FileNotFoundError(
                f"{yol} bulunamadı. Önce bir kez şunu çalıştırın:  python 04_atis_modeli_egit.py")
        with open(yol, encoding="utf-8") as f:
            d = json.load(f)
        self.meta = d["meta"]
        self.hedefler = d["hedefler"]          # {hedef: {"ad", "etiketler"}}
        self.modeller = d["modeller"]          # 5 ML modeli
        self.en_iyi = d["en_iyi"]              # {hedef: model adı}
        self.cv = d["cv"]                      # {hedef: {model: {metrik: değer}}}
        self.bolge_adlari = d["bolge_adlari"]  # 18 hücre → üst yarı bölge adı
        self._indeks = {k: i for i, k in enumerate(d["kombinasyonlar"])}
        self._olc = d["olcek"]
        self._p = d["olasiliklar"]             # {model: {hedef: [[int, ...], ...]}}

    def model_adi(self, hedef: str, model: str = OTOMATIK) -> str:
        return self.en_iyi[hedef] if model in (None, "", OTOMATIK) else model

    def sorgula(self, cinsiyet, kategori, vuran, rakip, model: str = OTOMATIK) -> dict:
        """Her çıktı için olasılığa göre sıralı liste döner:
        {hedef: {"model": ad, "liste": [{"etiket", "olasilik", ("bolge")}, ...]}}"""
        i = self._indeks.get(anahtar(cinsiyet, kategori, vuran, rakip))
        if i is None:
            raise KeyError(f"Bu kombinasyon tabloda yok: {cinsiyet}, {kategori}, {vuran}, {rakip}")
        sonuc = {}
        for h, bilgi in self.hedefler.items():
            m = self.model_adi(h, model)
            p = [v / self._olc for v in self._p[m][h][i]]
            liste = []
            for j in sorted(range(len(p)), key=lambda j: -p[j]):
                ogeler = {"etiket": bilgi["etiketler"][j], "olasilik": p[j]}
                if h == "bolge":
                    ogeler["bolge"] = self.bolge_adlari[j]
                liste.append(ogeler)
            sonuc[h] = {"model": m, "liste": liste}
        return sonuc


# ═══════════════════════════════════════════════════════════════════════════
#  KOMUT ÇÖZÜCÜ — konsoldan yazılan satırı seçimlere çevirir
# ═══════════════════════════════════════════════════════════════════════════
YARDIM = """\
Komut örnekleri (büyük/küçük harf ve Türkçe karakter fark etmez):
  Kadınlar Low 27x 29               → hepsini birden seç (sıra serbest)
  erkek orta 20x 28                 → aynı şekilde
  vuran=27x rakip=29                → anahtar=değer biçimi
  cinsiyet=kadin kategori=low       → yalnızca bazılarını değiştir
  vuran=disari   /  rakip=disari    → kort dışı / rakip konumu bilinmiyor
  model=mlp  (lr, rf, xgb, lgbm, mlp, oto)
  temizle     → seçimleri sıfırla
  durum       → mevcut seçimleri göster
  yardim      → bu metin
  cikis       → kapat
Bölge kuralı: vuran ALT yarıdadır (1x–32x), rakip ÜST yarıdadır (1–32)."""

_TR = str.maketrans("ıİşŞçÇğĞöÖüÜ", "iissccggoouu")


def _sade(s: str) -> str:
    return s.strip().translate(_TR).lower()


_CINSIYET = {"erkek": "Erkekler", "erkekler": "Erkekler", "e": "Erkekler", "men": "Erkekler",
             "male": "Erkekler", "kadin": "Kadınlar", "kadinlar": "Kadınlar", "bayan": "Kadınlar",
             "women": "Kadınlar", "female": "Kadınlar", "kiz": "Kadınlar"}
_KATEGORI = {"orta": "Middle", "middle": "Middle", "mid": "Middle",
             "low": "Low", "dusuk": "Low", "alt": "Low"}
_KATEGORI_YASAK = {"best", "zor", "en iyi", "eniyi", "ust"}
_DISARI = {"disari", "outside", "out", "kortdisi", "dis", "yok", "bilinmiyor", "-"}
_MODEL = {"lr": "Lojistik regresyon", "lojistik": "Lojistik regresyon",
          "rf": "Random Forest", "random": "Random Forest", "orman": "Random Forest",
          "xgb": "XGBoost", "xgboost": "XGBoost",
          "lgbm": "LightGBM", "lightgbm": "LightGBM", "lgb": "LightGBM",
          "mlp": "MLP (sinir ağı)", "sinir": "MLP (sinir ağı)", "nn": "MLP (sinir ağı)",
          "oto": OTOMATIK, "otomatik": OTOMATIK, "auto": OTOMATIK, "eniyi": OTOMATIK}
_ANAHTAR = {"cinsiyet": "cinsiyet", "c": "cinsiyet", "cins": "cinsiyet",
            "kategori": "kategori", "kat": "kategori", "k": "kategori",
            "vuran": "vuran", "v": "vuran", "p": "vuran", "oyuncu": "vuran", "atis": "vuran",
            "rakip": "rakip", "r": "rakip",
            "model": "model", "m": "model"}
KOMUTLAR = {"temizle": "temizle", "sifirla": "temizle", "clear": "temizle",
            "durum": "durum", "liste": "durum", "status": "durum",
            "yardim": "yardim", "help": "yardim", "?": "yardim", "h": "yardim",
            "cikis": "cikis", "q": "cikis", "quit": "cikis", "exit": "cikis"}


def _bolge(deger: str, rol: str | None) -> tuple[str, str]:
    """Bölge metnini çözer → (rol, bölge adı). rol None ise yarıdan bulunur."""
    d = _sade(deger)
    if d in _DISARI:
        if rol is None:
            raise ValueError("'disari' için kimin dışarıda olduğunu yazın: vuran=disari veya rakip=disari")
        return rol, DISARI
    z = d.upper().replace("X", "x")
    if z.upper()[:2] in ("LT", "RT", "LB", "RB"):
        raise ValueError(f"{deger}: koridor bölgeleri veride hiç yok, seçilemez.")
    alt = z.endswith("x")
    try:
        n = int(z.rstrip("x"))
    except ValueError:
        raise ValueError(f"'{deger}' tanınmadı (yardım için: yardim)") from None
    if not 1 <= n <= 32:
        raise ValueError(f"{deger}: bölge numarası 1–32 arasında olmalı.")
    bulunan = "vuran" if alt else "rakip"
    if rol and rol != bulunan:
        if rol == "vuran":
            raise ValueError(f"{deger}: vuran ALT yarıda olmalı (1x–32x).")
        raise ValueError(f"{deger}: rakip ÜST yarıda olmalı (1–32).")
    return bulunan, f"{n}x" if alt else str(n)


def _deger(alan: str, deger: str):
    d = _sade(deger)
    if alan == "cinsiyet":
        if d in _CINSIYET:
            return _CINSIYET[d]
        raise ValueError(f"Cinsiyet '{deger}' tanınmadı (erkek / kadin).")
    if alan == "kategori":
        if d in _KATEGORI:
            return _KATEGORI[d]
        if d in _KATEGORI_YASAK:
            raise ValueError("Arayüzde yalnızca Orta ve Low kategorileri var.")
        raise ValueError(f"Kategori '{deger}' tanınmadı (orta / low).")
    if alan == "model":
        if d in _MODEL:
            return _MODEL[d]
        raise ValueError(f"Model '{deger}' tanınmadı (lr, rf, xgb, lgbm, mlp, oto).")
    return _bolge(deger, alan)[1]


def komut_coz(satir: str) -> tuple[str | None, dict]:
    """Bir konsol satırını çözer.
    Döner: (komut, değişiklikler)  — komut: temizle/durum/yardim/cikis veya None;
    değişiklikler: {"cinsiyet"?, "kategori"?, "vuran"?, "rakip"?, "model"?}.
    Hatalı girdide ValueError (açıklamalı) fırlatır."""
    satir = satir.strip()
    if not satir:
        return None, {}
    if _sade(satir) in KOMUTLAR:
        return KOMUTLAR[_sade(satir)], {}
    degisim: dict = {}
    for parca in satir.replace(",", " ").replace(";", " ").split():
        if "=" in parca or ":" in parca:
            a, _, v = parca.replace(":", "=").partition("=")
            alan = _ANAHTAR.get(_sade(a))
            if alan is None:
                raise ValueError(f"'{a}' anahtarı tanınmadı (cinsiyet, kategori, vuran, rakip, model).")
            degisim[alan] = _deger(alan, v)
            continue
        p = _sade(parca)
        if p in _CINSIYET:
            degisim["cinsiyet"] = _CINSIYET[p]
        elif p in _KATEGORI:
            degisim["kategori"] = _KATEGORI[p]
        elif p in _KATEGORI_YASAK:
            raise ValueError("Arayüzde yalnızca Orta ve Low kategorileri var.")
        elif p in _MODEL and not p.isdigit():
            degisim["model"] = _MODEL[p]
        else:
            rol, z = _bolge(parca, None)
            degisim[rol] = z
    return None, degisim


def metin_ozeti(secim: dict, sonuc: dict) -> str:
    """Konsola yazdırılacak okunur özet."""
    b = sonuc["bolge"]["liste"]
    sat = [f"Seçim: {secim['cinsiyet']} | {KATEGORI_GORUNEN.get(secim['kategori'], secim['kategori'])}"
           f" | vuran {secim['vuran']} | rakip {secim['rakip']}",
           f"ÖNERİLEN ATIŞ → bölge {b[0]['bolge']} ({b[0]['etiket']}), "
           f"{sonuc['spin']['liste'][0]['etiket']}, "
           f"{sonuc['yukseklik']['liste'][0]['etiket']} yükseklik, "
           f"kademe {sonuc['kademe']['liste'][0]['etiket']}"]
    sat.append(f"  Düşme bölgesi [{sonuc['bolge']['model']}]: " +
               ", ".join(f"{o['bolge']} %{100*o['olasilik']:.1f}" for o in b[:5]))
    for h, ad in (("spin", "Spin"), ("yukseklik", "Yükseklik"), ("kademe", "Kademe")):
        sat.append(f"  {ad:<9} [{sonuc[h]['model']}]: " +
                   ", ".join(f"{o['etiket']} %{100*o['olasilik']:.0f}" for o in sonuc[h]["liste"]))
    return "\n".join(sat)
