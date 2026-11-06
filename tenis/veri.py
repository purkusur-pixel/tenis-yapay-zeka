"""
Veritabanını okur, temizler ve modele hazır "ham ama tutarlı" bir tablo üretir.
Burada HİÇBİR istatistik (ortalama, sayım, ölçekleme) hesaplanmaz — bunlar
veri sızıntısı yaratmamak için yalnızca eğitim katı içinde yapılmalıdır.
"""
from __future__ import annotations

import sqlite3

import pandas as pd

from . import ayarlar as A
from . import bolgeler as B


def yukle(yol=A.VERITABANI, sadece_basarili: bool = True) -> pd.DataFrame:
    sorgu = """
        SELECT k.*, v.ad AS vurus_ad, s.ad AS spin_ad,
               k.mac_bilgisi || ' | ' || k.turnuva || ' ' || k.yil AS mac_id
        FROM kayitlar k
        LEFT JOIN vurus_stilleri v ON v.id = k.vurus_id
        LEFT JOIN spinler s        ON s.id = k.spin_id
    """
    with sqlite3.connect(yol) as c:
        df = pd.read_sql_query(sorgu, c)
    if sadece_basarili:
        df = df[df["atis_basarili_mi"] == 1]
    return df.sort_values(["mac_id", "frame_baslangic"]).reset_index(drop=True)


def vuran_yarisi(vurulan, nereden) -> str | None:
    """Vuranın hangi yarıda olduğunu yalnızca ATIŞ ÖNCESİ bilgiden bulur.
    1) vurulan bölge biliniyorsa oradan,
    2) değilse (OUTSIDE) rakip karşı yarıdadır → nereden_geldi'nin tersi."""
    y = B.yari(vurulan)
    if y:
        return y
    r = B.yari(nereden)
    if r:
        return "X" if r == "N" else "N"
    return None


def hazirla(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Kanonik hedefi ekler, tanımsız/geçersiz hedefleri çıkarır. (tablo, rapor) döner."""
    rapor = {"baslangic": len(df)}
    df = df.copy()
    df["vuran_yari"] = [vuran_yarisi(v, n) for v, n in zip(df.vurulan_bolge, df.nereden_geldi)]
    rapor["yari_belirsiz"] = int(df.vuran_yari.isna().sum())

    hedef = []
    for d, vy in zip(df.dustugu_bolge, df.vuran_yari):
        b = B.coz(d)
        if b is None or vy is None or b.yari == vy:      # bilinmiyor / kendi yarısına düşmüş
            hedef.append(None)
            continue
        h = (b.satir, B.kanonik_sutun(b.sutun, vy))
        hedef.append(h if h in B.HUCRE_ID else None)
    df["hedef_hucre"] = hedef
    rapor["hedef_tanimsiz_nadir_veya_yari_belirsiz"] = int(df.hedef_hucre.isna().sum())
    df = df[df.hedef_hucre.notna()].reset_index(drop=True)
    df["y"] = df.hedef_hucre.map(B.HUCRE_ID).astype(int)
    df["y_kaba"] = df.hedef_hucre.map(B.kaba_etiket)
    df["vurus_ailesi"] = df.vurus_ad.map(A.VURUS_AILESI).fillna("Diğer")
    df["grup"] = df.cinsiyet + "_" + df.kategori
    rapor["son"] = len(df)
    rapor["mac_sayisi"] = int(df.mac_id.nunique())
    return df, rapor
