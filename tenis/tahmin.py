"""
Eğitilmiş modeli yükleyip tek atış için tahmin üretir.
GUI'nin beklediği arayüzle uyumludur: predict(...) → [{"zone", "prob", "x", "y", ...}, ...]
"""
from __future__ import annotations

import joblib
import numpy as np
import pandas as pd

from . import ayarlar as A
from . import bolgeler as B
from .ozellikler import ozellik_satiri
from .veri import vuran_yarisi


class TenisTahminci:
    def __init__(self, yol=A.MODEL_DOSYASI):
        paket = joblib.load(yol)
        self.model = paket["model"]
        self.model_adi = paket["model_adi"]
        self.ozellik_adlari = paket["ozellik_adlari"]
        self.cv_ozet = paket.get("cv_ozet", {})

    def olasiliklar(self, cinsiyet, kategori, vurulan, nereden=None, vurus="Forehand",
                    spin="Topspin", kademe=2, yukseklik=2) -> np.ndarray:
        s = ozellik_satiri(cinsiyet, kategori, vurulan, nereden, vurus, spin, kademe, yukseklik)
        X = pd.DataFrame([s])[self.ozellik_adlari].astype(np.float32)
        return self.model.predict_proba(X)[0]

    def predict(self, cinsiyet, kategori, vurulan, nereden=None, vurus="Forehand",
                spin="Topspin", kademe=2, yukseklik=2, top_n=5):
        p = self.olasiliklar(cinsiyet, kategori, vurulan, nereden, vurus, spin, kademe, yukseklik)
        vy = vuran_yarisi(vurulan, nereden) or "X"
        sonuc = []
        for i in np.argsort(-p)[:top_n]:
            h = B.HEDEF_HUCRELER[i]
            zone = B.kanonikten_ada(h[0], h[1], vy)
            x, y = B.merkez_norm(zone)
            sonuc.append({"zone": zone, "prob": round(float(p[i]), 4), "x": x, "y": y,
                          "hucre": B.hucre_etiketi(h), "kaba": B.kaba_etiket(h)})
        return sonuc

    def kaba_tahmin(self, *args, **kw) -> dict:
        """9 sınıflı (derinlik x yön) olasılıklar — antrenör için daha okunabilir çıktı."""
        p = self.olasiliklar(*args, **kw)
        out: dict[str, float] = {}
        for pi, h in zip(p, B.HEDEF_HUCRELER):
            k = B.kaba_etiket(h)
            out[k] = out.get(k, 0.0) + float(pi)
        return dict(sorted(out.items(), key=lambda kv: -kv[1]))
