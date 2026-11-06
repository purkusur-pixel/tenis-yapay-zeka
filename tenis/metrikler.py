"""
Değerlendirme metrikleri ve istatistiksel testler.
"""
from __future__ import annotations

from itertools import combinations

import numpy as np
import pandas as pd
from scipy.stats import binomtest, wilcoxon

from . import ayarlar as A
from . import bolgeler as B

_H = np.array(B.HEDEF_HUCRELER)                                   # (18, 2)
_KABA = np.array([B.kaba_etiket(tuple(h)) for h in B.HEDEF_HUCRELER])
_KABA_SIN = sorted(set(_KABA))
_KABA_M = np.array([[k == s for k in _KABA] for s in _KABA_SIN], float).T   # (18, 9)
_DER_M = np.array([[h[0] == d for h in B.HEDEF_HUCRELER] for d in A.HEDEF_SATIRLAR], float).T
_YON = [A.YON_GRUBU[h[1]] for h in B.HEDEF_HUCRELER]
_YON_SIN = ["Sol", "Orta", "Sağ"]
_YON_M = np.array([[y == s for y in _YON] for s in _YON_SIN], float).T
# Hücreler arası mesafe matrisi (metre)
_MESAFE = np.array([[B.mesafe_metre(tuple(a), tuple(b)) for b in _H] for a in _H])


def holm(p) -> np.ndarray:
    """Holm–Bonferroni düzeltmesi (çoklu karşılaştırma)."""
    p = np.asarray(p, float)
    m = len(p)
    sira = np.argsort(p)
    duz = np.empty(m)
    enb = 0.0
    for i, j in enumerate(sira):
        enb = max(enb, (m - i) * p[j])
        duz[j] = min(1.0, enb)
    return duz


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    p = k / n
    d = 1 + z * z / n
    m = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return m - h, m + h


def ozet(p: np.ndarray, y: np.ndarray) -> dict:
    """p: (n, 18) olasılık, y: (n,) gerçek hücre indeksi."""
    sira = np.argsort(-p, axis=1)
    tah = sira[:, 0]
    dogru = tah == y
    lo, hi = wilson(int(dogru.sum()), len(y))
    return {
        "Top-1 %": 100 * dogru.mean(),
        "Top-1 GA95": f"{100*lo:.1f}–{100*hi:.1f}",
        "Top-3 %": 100 * (sira[:, :3] == y[:, None]).any(1).mean(),
        "Kaba 9 sınıf %": 100 * ((p @ _KABA_M).argmax(1) == (np.eye(18)[y] @ _KABA_M).argmax(1)).mean(),
        "Derinlik %": 100 * ((p @ _DER_M).argmax(1) == (np.eye(18)[y] @ _DER_M).argmax(1)).mean(),
        "Yön %": 100 * ((p @ _YON_M).argmax(1) == (np.eye(18)[y] @ _YON_M).argmax(1)).mean(),
        "Ort. hata (m)": _MESAFE[tah, y].mean(),
        "Beklenen hata (m)": (p * _MESAFE[:, y].T).sum(1).mean(),
        "Log-loss": -np.mean(np.log(np.clip(p[np.arange(len(y)), y], 1e-12, 1))),
    }


def mcnemar_tablosu(dogrular: dict[str, np.ndarray]) -> pd.DataFrame:
    """Tüm model çiftleri için kesin (binom) McNemar testi + Holm düzeltmesi."""
    satirlar = []
    for a, b in combinations(dogrular, 2):
        x, z = dogrular[a], dogrular[b]
        n01, n10 = int((x & ~z).sum()), int((~x & z).sum())
        p = binomtest(n01, n01 + n10, 0.5).pvalue if n01 + n10 else 1.0
        satirlar.append({"Model A": a, "Model B": b, "A doğru/B yanlış": n01,
                         "A yanlış/B doğru": n10, "p (ham)": p})
    t = pd.DataFrame(satirlar)
    t["p (Holm)"] = holm(t["p (ham)"])
    t["Anlamlı (α=0,05)"] = np.where(t["p (Holm)"] < 0.05, "Evet", "Hayır")
    return t


def mac_bazli_wilcoxon(mac_dogruluk: pd.DataFrame, referans: str) -> pd.DataFrame:
    """Her maçın doğruluğu bir gözlem → n = maç sayısı (5 kattan çok daha güçlü)."""
    satirlar = []
    for m in mac_dogruluk.columns:
        if m == referans:
            continue
        fark = mac_dogruluk[referans] - mac_dogruluk[m]
        p = wilcoxon(mac_dogruluk[referans], mac_dogruluk[m]).pvalue if fark.abs().sum() else 1.0
        satirlar.append({"Karşılaştırma": f"{referans} − {m}",
                         "Ort. fark (puan)": 100 * fark.mean(),
                         "Kazandığı maç": int((fark > 0).sum()), "p (ham)": p})
    t = pd.DataFrame(satirlar)
    t["p (Holm)"] = holm(t["p (ham)"])
    return t
