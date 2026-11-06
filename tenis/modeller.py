"""
Model kayıt defteri. Her model aynı arayüzü sunar: fit(X, y) ve predict_proba(X) → (n, 18).
Yeni bir model (ör. PyTorch MLP) eklemek için buraya bir giriş eklemek yeterlidir.
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

N_SINIF = len(B.HEDEF_HUCRELER)


class FrekansTablosu(BaseEstimator, ClassifierMixin):
    """Koşullu frekans taban çizgisi (hiyerarşik geri çekilmeli / backoff).
    P(hedef | vuran hücre, rakip hücre, vuruş ailesi)  →  bulunamazsa
    P(hedef | vuran hücre, vuruş ailesi) → P(hedef | vuruş ailesi) → P(hedef).
    Makine öğrenmesi modellerinin geçmesi gereken GERÇEK taban çizgisi budur;
    rastgele tahmin (%1,96) yanıltıcı derecede düşüktür."""

    def __init__(self, alfa: float = 5.0):
        self.alfa = alfa

    @staticmethod
    def _anahtarlar(X: pd.DataFrame):
        aile = X[[c for c in X.columns if c.startswith("aile_")]].to_numpy().argmax(1)
        v = list(zip(X.vuran_satir, X.vuran_sutun))
        r = list(zip(X.rakip_satir, X.rakip_sutun))
        return [[(a,), (a, vv), (a, vv, rr)] for a, vv, rr in zip(aile, v, r)]

    def fit(self, X, y):
        y = np.asarray(y)
        self.classes_ = np.arange(N_SINIF)
        self.genel_ = np.bincount(y, minlength=N_SINIF) + 1.0
        self.genel_ /= self.genel_.sum()
        self.sayim_ = {}
        for anahtarlar, yi in zip(self._anahtarlar(X), y):
            for k in anahtarlar:
                self.sayim_.setdefault(k, np.zeros(N_SINIF))[yi] += 1
        return self

    def predict_proba(self, X):
        cikti = np.zeros((len(X), N_SINIF))
        for i, anahtarlar in enumerate(self._anahtarlar(X)):
            p = self.genel_
            for k in anahtarlar:                  # genelden özele doğru düzelt
                s = self.sayim_.get(k)
                if s is not None:
                    p = (s + self.alfa * p) / (s.sum() + self.alfa)
            cikti[i] = p
        return cikti


class Hizala(BaseEstimator, ClassifierMixin):
    """Bir katta bazı sınıflar eğitimde hiç görülmezse olasılık sütunlarını 18'e hizalar."""

    def __init__(self, model):
        self.model = model

    def fit(self, X, y):
        y = np.asarray(y)
        self.gorulen_ = np.unique(y)
        harita = {c: i for i, c in enumerate(self.gorulen_)}
        self.model.fit(X, np.array([harita[v] for v in y]))
        self.classes_ = np.arange(N_SINIF)
        return self

    def predict_proba(self, X):
        p = self.model.predict_proba(X)
        out = np.zeros((len(X), N_SINIF))
        out[:, self.gorulen_] = p
        return out


def model_olustur(ad: str):
    R = A.RASTGELE
    if ad == "Çoğunluk sınıfı":
        return Hizala(DummyClassifier(strategy="prior"))
    if ad == "Frekans tablosu":
        return FrekansTablosu(alfa=5.0)
    if ad == "Lojistik regresyon":
        return Hizala(make_pipeline(StandardScaler(), LogisticRegression(C=0.5, max_iter=3000)))
    if ad == "Random Forest":
        return Hizala(RandomForestClassifier(n_estimators=500, min_samples_leaf=5,
                                             max_features="sqrt", n_jobs=-1, random_state=R))
    if ad == "XGBoost":
        import xgboost as xgb
        return Hizala(xgb.XGBClassifier(n_estimators=400, learning_rate=0.05, max_depth=5,
                                        subsample=0.8, colsample_bytree=0.8, min_child_weight=5,
                                        reg_lambda=1.0, tree_method="hist", n_jobs=-1,
                                        random_state=R, verbosity=0))
    if ad == "LightGBM":
        import lightgbm as lgb
        return Hizala(lgb.LGBMClassifier(n_estimators=400, learning_rate=0.03, num_leaves=15,
                                         min_child_samples=20, subsample=0.8, subsample_freq=1,
                                         colsample_bytree=0.8, reg_lambda=1.0, n_jobs=-1,
                                         random_state=R, verbose=-1))
    if ad == "MLP (sinir ağı)":
        return Hizala(make_pipeline(StandardScaler(), MLPClassifier(
            hidden_layer_sizes=(128, 64), alpha=1e-3, learning_rate_init=1e-3,
            early_stopping=True, validation_fraction=0.15, n_iter_no_change=15,
            max_iter=400, random_state=R)))
    raise ValueError(f"Bilinmeyen model: {ad}")


MODELLER = ["Çoğunluk sınıfı", "Frekans tablosu", "Lojistik regresyon",
            "Random Forest", "XGBoost", "LightGBM", "MLP (sinir ağı)"]
