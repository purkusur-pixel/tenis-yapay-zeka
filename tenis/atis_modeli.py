"""
ATIŞ MODELİ (4 girdi → 4 çıktı) — top atma makinesi için.

Kullanıcının SEÇTİĞİ girdiler (yalnızca bunlar):
    cinsiyet, kategori, vuran konumu (atışın yapıldığı yer), rakip konumu
Makine öğrenmesinin TAHMİN ETTİĞİ çıktılar:
    düşme bölgesi (18 kanonik hücre), spin (3), top yüksekliği (3), kademe (3)

Vuruş stili bilinçli olarak KULLANILMAZ.
Spin, yükseklik ve kademe girdi DEĞİL, çıktıdır: model, verilen duruma göre
profesyonel maçlarda en olası spini / yüksekliği / kademeyi önerir.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from . import ayarlar as A
from . import bolgeler as B
from .ozellikler import OZELLIK_ADLARI, ozellik_satiri

# ── Çıktılar (hedefler) ─────────────────────────────────────────────────────
SPIN_ETIKET = ["Topspin", "Kesik", "Düz"]          # Kesik = Slice + Backspin + underspin
YUKSEKLIK_ETIKET = ["Alçak", "Orta", "Yüksek"]      # veritabanı kodu 1, 2, 3
KADEME_ETIKET = ["Kolay", "Nötr", "Zor"]            # veritabanı kodu 1, 2, 3

HEDEFLER = {
    "bolge": {"ad": "Düşme bölgesi",
              "etiketler": [B.hucre_etiketi(h) for h in B.HEDEF_HUCRELER]},
    "spin": {"ad": "Spin", "etiketler": SPIN_ETIKET},
    "yukseklik": {"ad": "Top yüksekliği", "etiketler": YUKSEKLIK_ETIKET},
    "kademe": {"ad": "Kademe (zorluk)", "etiketler": KADEME_ETIKET},
}


def hedef_vektoru(df: pd.DataFrame, hedef: str) -> np.ndarray:
    """Hedefin tamsayı sınıf kodu; eksik / tanımsız değer → -1."""
    if hedef == "bolge":
        return df.y.to_numpy().astype(int)
    if hedef == "spin":
        s = df.spin_ad.map(A.SPIN_GRUBU).map({e: i for i, e in enumerate(SPIN_ETIKET)})
    else:
        s = pd.to_numeric(df[hedef], errors="coerce") - 1      # 1,2,3 → 0,1,2
        s = s.where(s.isin([0, 1, 2]))
    return s.fillna(-1).to_numpy().astype(int)


# ── Girdiler (özellikler) ───────────────────────────────────────────────────
# Mevcut özellik fonksiyonu yeniden kullanılır; vuruş / spin / el / yükseklik /
# kademe sütunları atılır. Geriye konum + göreli geometri + cinsiyet + kategori kalır.
_ATILAN_ON_EKLER = ("aile_", "el_", "spin_")
GIRDI_ADLARI = [k for k in OZELLIK_ADLARI
                if not k.startswith(_ATILAN_ON_EKLER) and k not in ("yukseklik", "kademe")]


def girdi_satiri(cinsiyet: str, kategori: str, vuran: str, rakip: str | None) -> dict:
    s = ozellik_satiri(cinsiyet, kategori, vuran, rakip)
    return {k: s[k] for k in GIRDI_ADLARI}


def girdi_tablosu(df: pd.DataFrame) -> pd.DataFrame:
    satirlar = []
    for r in df.itertuples(index=False):
        s = ozellik_satiri(r.cinsiyet, r.kategori, r.vurulan_bolge, r.nereden_geldi,
                           vuran_yari=r.vuran_yari)
        satirlar.append({k: s[k] for k in GIRDI_ADLARI})
    return pd.DataFrame(satirlar)[GIRDI_ADLARI].astype(np.float32)


# ── Modeller ────────────────────────────────────────────────────────────────
class Hizala(BaseEstimator, ClassifierMixin):
    """Bir katta bazı sınıflar hiç görülmezse olasılık sütunlarını n_sinif'e hizalar."""

    def __init__(self, model, n_sinif: int):
        self.model = model
        self.n_sinif = n_sinif

    def fit(self, X, y):
        y = np.asarray(y)
        self.gorulen_ = np.unique(y)
        harita = {c: i for i, c in enumerate(self.gorulen_)}
        self.model.fit(X, np.array([harita[v] for v in y]))
        self.classes_ = np.arange(self.n_sinif)
        return self

    def predict_proba(self, X):
        p = self.model.predict_proba(X)
        out = np.zeros((len(X), self.n_sinif))
        out[:, self.gorulen_] = p
        return out


class FrekansTablosu(BaseEstimator, ClassifierMixin):
    """Taban çizgisi: P(çıktı | vuran hücre, rakip hücre), az veri varsa
    P(çıktı | vuran hücre) → P(çıktı) yönünde düzleştirilir."""

    def __init__(self, n_sinif: int, alfa: float = 5.0):
        self.n_sinif = n_sinif
        self.alfa = alfa

    @staticmethod
    def _anahtarlar(X):
        v = list(zip(X.vuran_satir, X.vuran_sutun))
        r = list(zip(X.rakip_satir, X.rakip_sutun))
        return [[(vv,), (vv, rr)] for vv, rr in zip(v, r)]

    def fit(self, X, y):
        y = np.asarray(y)
        self.classes_ = np.arange(self.n_sinif)
        self.genel_ = np.bincount(y, minlength=self.n_sinif) + 1.0
        self.genel_ /= self.genel_.sum()
        self.sayim_ = {}
        for anahtarlar, yi in zip(self._anahtarlar(X), y):
            for k in anahtarlar:
                self.sayim_.setdefault(k, np.zeros(self.n_sinif))[yi] += 1
        return self

    def predict_proba(self, X):
        out = np.zeros((len(X), self.n_sinif))
        for i, anahtarlar in enumerate(self._anahtarlar(X)):
            p = self.genel_
            for k in anahtarlar:
                s = self.sayim_.get(k)
                if s is not None:
                    p = (s + self.alfa * p) / (s.sum() + self.alfa)
            out[i] = p
        return out


ML_MODELLER = ["Lojistik regresyon", "Random Forest", "XGBoost", "LightGBM", "MLP (sinir ağı)"]
TABAN_MODELLER = ["Çoğunluk sınıfı", "Frekans tablosu"]


def model_olustur(ad: str, n_sinif: int):
    R = A.RASTGELE
    if ad == "Çoğunluk sınıfı":
        return Hizala(DummyClassifier(strategy="prior"), n_sinif)
    if ad == "Frekans tablosu":
        return FrekansTablosu(n_sinif, alfa=5.0)
    if ad == "Lojistik regresyon":
        return Hizala(make_pipeline(StandardScaler(), LogisticRegression(C=0.5, max_iter=3000)),
                      n_sinif)
    if ad == "Random Forest":
        return Hizala(RandomForestClassifier(n_estimators=300, min_samples_leaf=10,
                                             max_features="sqrt", n_jobs=-1, random_state=R),
                      n_sinif)
    if ad == "XGBoost":
        import xgboost as xgb
        return Hizala(xgb.XGBClassifier(n_estimators=300, learning_rate=0.05, max_depth=4,
                                        subsample=0.8, colsample_bytree=0.8, min_child_weight=5,
                                        reg_lambda=1.0, tree_method="hist", n_jobs=-1,
                                        random_state=R, verbosity=0), n_sinif)
    if ad == "LightGBM":
        import lightgbm as lgb
        return Hizala(lgb.LGBMClassifier(n_estimators=300, learning_rate=0.03, num_leaves=15,
                                         min_child_samples=20, subsample=0.8, subsample_freq=1,
                                         colsample_bytree=0.8, reg_lambda=1.0, n_jobs=-1,
                                         random_state=R, verbose=-1), n_sinif)
    if ad == "MLP (sinir ağı)":
        return Hizala(make_pipeline(StandardScaler(), MLPClassifier(
            hidden_layer_sizes=(128, 64), alpha=1e-3, learning_rate_init=1e-3,
            early_stopping=True, validation_fraction=0.15, n_iter_no_change=15,
            max_iter=400, random_state=R)), n_sinif)
    raise ValueError(f"Bilinmeyen model: {ad}")


# ── Metrikler ───────────────────────────────────────────────────────────────
def ozet_metrik(p: np.ndarray, y: np.ndarray) -> dict:
    """Her çıktı için ortak metrikler. p: (n, k) olasılık, y: (n,) sınıf."""
    k = p.shape[1]
    tah = p.argmax(1)
    dogru = tah == y
    sinif_dog = [dogru[y == c].mean() for c in range(k) if (y == c).any()]
    out = {
        "Top-1 %": 100 * dogru.mean(),
        "Dengeli doğruluk %": 100 * float(np.mean(sinif_dog)),
        "Log-loss": float(-np.mean(np.log(np.clip(p[np.arange(len(y)), y], 1e-12, 1)))),
        "Brier": float(np.mean(np.sum((p - np.eye(k)[y]) ** 2, axis=1))),
    }
    if k > 3:
        out["Top-3 %"] = 100 * (np.argsort(-p, 1)[:, :3] == y[:, None]).any(1).mean()
    return out
