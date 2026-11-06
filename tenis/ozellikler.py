"""
Özellik çıkarımı — EĞİTİM ve TAHMİN için TEK fonksiyon.
Eski projede aynı mantık prepare_data, inference_boosting, inference_dl ve GUI'de
ayrı ayrı yazılmıştı; küçük farklar (ör. "NONE" kontrolü) sessiz hatalara yol açıyordu.

Tüm özellikler atış ÖNCESİNDE bilinebilir ve vuranın bakış açısında (kanonik) ifade edilir.
Hiçbir özellik veriden öğrenilmiş istatistik içermez → sızıntı riski yok, ayrı encoder dosyası gerekmez.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from . import ayarlar as A
from . import bolgeler as B
from .veri import vuran_yarisi

BILINMIYOR = -1.0


def _onehot(on_ek: str, deger: str, secenekler: list[str]) -> dict:
    return {f"{on_ek}_{s}": float(deger == s) for s in secenekler}


def ozellik_satiri(cinsiyet, kategori, vurulan, nereden=None, vurus="Forehand",
                   spin="Topspin", kademe=2, yukseklik=2, vuran_yari=None) -> dict:
    vy = vuran_yari or vuran_yarisi(vurulan, nereden) or "X"

    # 1) Vuran oyuncunun konumu
    v = B.kanonik(vurulan, vy)
    v_bilinmiyor = v is None
    v_satir, v_sutun = (BILINMIYOR, BILINMIYOR) if v_bilinmiyor else (float(v[0]), float(v[1]))

    # 2) Rakibin konumu (nereden_geldi: veride rakibin vuruş anındaki bölgesi, hedefle aynı yarıda)
    r = B.kanonik(nereden, vy)
    r_bilinmiyor = r is None or B.yari(nereden) == vy
    r_satir, r_sutun = (BILINMIYOR, BILINMIYOR) if r_bilinmiyor else (float(r[0]), float(r[1]))

    # 3) Göreli geometri (yalnızca iki konum da biliniyorsa)
    if v_bilinmiyor or r_bilinmiyor:
        yan_fark = aci = 0.0
    else:
        yan_fark = r_sutun - v_sutun        # >0: rakip vuranın sağ tarafında
        # vuran → rakip doğrultusunun açısı (dik=0)
        dy = (v_satir + 0.5) * A.SATIR_METRE + (r_satir + 0.5) * A.SATIR_METRE
        aci = math.degrees(math.atan2(yan_fark * A.SUTUN_METRE, dy))

    aile = A.VURUS_AILESI.get(str(vurus), "Diğer")
    el = A.VURUS_ELI.get(str(vurus), "Yok")
    spin_g = A.SPIN_GRUBU.get(str(spin), "Topspin")

    s = {
        "vuran_satir": v_satir, "vuran_sutun": v_sutun, "vuran_disarida": float(v_bilinmiyor),
        "vuran_merkezden": 0.0 if v_bilinmiyor else abs(v_sutun - 3.5),
        "rakip_satir": r_satir, "rakip_sutun": r_sutun, "rakip_bilinmiyor": float(r_bilinmiyor),
        "rakip_merkezden": 0.0 if r_bilinmiyor else abs(r_sutun - 3.5),
        "yan_fark": yan_fark, "aci_derece": aci,
        "yukseklik": float(yukseklik if pd.notna(yukseklik) else 2),
        "kademe": float(kademe if pd.notna(kademe) else 2),
    }
    s.update(_onehot("aile", aile, A.VURUS_AILELERI))
    s.update(_onehot("el", el, A.ELLER))
    s.update(_onehot("spin", spin_g, A.SPINLER))
    s.update(_onehot("cins", cinsiyet, A.CINSIYETLER))
    s.update(_onehot("kat", kategori, A.KATEGORILER))
    return s


def ozellik_tablosu(df: pd.DataFrame) -> pd.DataFrame:
    satirlar = [
        ozellik_satiri(r.cinsiyet, r.kategori, r.vurulan_bolge, r.nereden_geldi,
                       r.vurus_ad, r.spin_ad, r.kademe, r.yukseklik, r.vuran_yari)
        for r in df.itertuples(index=False)
    ]
    return pd.DataFrame(satirlar).astype(np.float32)


OZELLIK_ADLARI = list(ozellik_satiri("Erkekler", "Best", "29x", "27").keys())
