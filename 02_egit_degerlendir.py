"""
ADIM 2 — Maç bazlı çapraz doğrulama, karşılaştırma, istatistiksel testler ve son model.

Değerlendirme birimi MAÇTIR: test katındaki maçların hiçbir atışı eğitimde görülmez
(GroupKFold). Rastgele atış bölmesinde aynı maçın/rallinin atışları iki tarafa da
düşer ve sonuçlar iyimser çıkar.

Çalıştırma:
    python 02_egit_degerlendir.py                 # tüm modeller
    python 02_egit_degerlendir.py --hizli         # MLP/RF olmadan
    python 02_egit_degerlendir.py --ablasyon      # özellik grubu ablasyonu da yap
"""
import argparse
import json
import time

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.model_selection import GroupKFold

from tenis import ayarlar as A
from tenis.metrikler import mac_bazli_wilcoxon, mcnemar_tablosu, ozet
from tenis.modeller import MODELLER, model_olustur
from tenis.ozellikler import OZELLIK_ADLARI, ozellik_tablosu
from tenis.veri import hazirla, yukle

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)
pd.set_option("display.float_format", lambda v: f"{v:.3f}")

ap = argparse.ArgumentParser()
ap.add_argument("--hizli", action="store_true")
ap.add_argument("--ablasyon", action="store_true")
arg = ap.parse_args()
A.CIKTI.mkdir(exist_ok=True)

# ── Veri ─────────────────────────────────────────────────────────────────────
df, rapor = hazirla(yukle())
X = ozellik_tablosu(df)[OZELLIK_ADLARI]
y = df.y.to_numpy()
gruplar = df.mac_id.to_numpy()
print(f"Atış: {len(df):,}  |  Maç: {rapor['mac_sayisi']}  |  Özellik: {X.shape[1]}  |  Sınıf: 18")

katlar = list(GroupKFold(n_splits=A.N_FOLD).split(X, y, gruplar))
modeller = [m for m in MODELLER if not (arg.hizli and m in ("MLP (sinir ağı)", "Random Forest"))]


def oof_tahmin(model_adi, X_):
    """Katlar dışı (out-of-fold) olasılıklar: her atış, maçı eğitimde yokken tahmin edilir."""
    P = np.zeros((len(X_), 18))
    for tr, te in katlar:
        m = model_olustur(model_adi)
        m.fit(X_.iloc[tr], y[tr])
        P[te] = m.predict_proba(X_.iloc[te])
    return P


# ── 1) Model karşılaştırması ────────────────────────────────────────────────
P, sureler = {}, {}
for ad in modeller:
    t0 = time.time()
    P[ad] = oof_tahmin(ad, X)
    sureler[ad] = time.time() - t0
    print(f"  {ad:<20} {sureler[ad]:6.1f} sn   Top-1 %{100*(P[ad].argmax(1) == y).mean():.2f}")

tablo = pd.DataFrame({ad: ozet(P[ad], y) for ad in modeller}).T
tablo["Süre (sn)"] = pd.Series(sureler)
print("\n=== MAÇ BAZLI 5-KAT ÇAPRAZ DOĞRULAMA (tüm atışlar, katlar dışı) ===")
print(tablo.to_string())

# ── 2) Alt kırılımlar: servis vs ralli, grup ────────────────────────────────
ml_modeller = [m for m in modeller if m not in ("Çoğunluk sınıfı", "Frekans tablosu")]
en_iyi = max(ml_modeller, key=lambda m: tablo.loc[m, "Top-1 %"])
print(f"\nEn iyi ML modeli (Top-1): {en_iyi}")

servis = (df.vurus_ailesi == "Servis").to_numpy()
kirilim = []
for ad in ["Frekans tablosu", en_iyi]:
    for etiket, maske in [("Servis", servis), ("Ralli (servis hariç)", ~servis)]:
        kirilim.append({"Model": ad, "Alt küme": etiket, "n": int(maske.sum()),
                        **{k: v for k, v in ozet(P[ad][maske], y[maske]).items()
                           if k in ("Top-1 %", "Top-3 %", "Kaba 9 sınıf %", "Ort. hata (m)")}})
for g in sorted(df.grup.unique()):
    m = (df.grup == g).to_numpy()
    kirilim.append({"Model": en_iyi, "Alt küme": g, "n": int(m.sum()),
                    **{k: v for k, v in ozet(P[en_iyi][m], y[m]).items()
                       if k in ("Top-1 %", "Top-3 %", "Kaba 9 sınıf %", "Ort. hata (m)")}})
kirilim = pd.DataFrame(kirilim)
print("\n=== ALT KIRILIMLAR ===")
print(kirilim.to_string(index=False))

# ── 3) İstatistiksel testler ────────────────────────────────────────────────
dogrular = {ad: P[ad].argmax(1) == y for ad in modeller if ad != "Çoğunluk sınıfı"}
mcn = mcnemar_tablosu(dogrular)
print("\n=== McNEMAR (kesin binom) + HOLM DÜZELTMESİ — n =", len(y), "===")
print(mcn.to_string(index=False))

mac_dog = pd.DataFrame({ad: pd.Series(d).groupby(gruplar).mean() for ad, d in dogrular.items()})
wil = mac_bazli_wilcoxon(mac_dog, en_iyi)
print(f"\n=== MAÇ BAZLI WILCOXON (n = {len(mac_dog)} maç) — referans: {en_iyi} ===")
print(wil.to_string(index=False))

# ── 4) Ablasyon (isteğe bağlı) ──────────────────────────────────────────────
abl = None
if arg.ablasyon:
    gruplar_ozellik = {
        "Rakip konumu": [c for c in X.columns if c.startswith("rakip_")] + ["yan_fark", "aci_derece"],
        "Vuran konumu": [c for c in X.columns if c.startswith("vuran_")] + ["yan_fark", "aci_derece"],
        "Vuruş/spin/el": [c for c in X.columns if c.startswith(("aile_", "el_", "spin_"))],
        "Yükseklik+kademe": ["yukseklik", "kademe"],
        "Cinsiyet+kategori": [c for c in X.columns if c.startswith(("cins_", "kat_"))],
    }
    satir = [{"Çıkarılan grup": "— (tam model)", **ozet(P[en_iyi], y)}]
    for g, cols in gruplar_ozellik.items():
        Xa = X.drop(columns=sorted(set(cols)))
        satir.append({"Çıkarılan grup": g, **ozet(oof_tahmin(en_iyi, Xa), y)})
        print(f"  ablasyon: {g} bitti")
    abl = pd.DataFrame(satir)[["Çıkarılan grup", "Top-1 %", "Top-3 %", "Kaba 9 sınıf %",
                               "Ort. hata (m)", "Log-loss"]]
    print(f"\n=== ABLASYON ({en_iyi}) ===")
    print(abl.to_string(index=False))

# ── 5) Son model: tüm veriyle eğit ve kaydet ────────────────────────────────
son = model_olustur(en_iyi).fit(X, y)
joblib.dump({"model": son, "model_adi": en_iyi, "ozellik_adlari": OZELLIK_ADLARI,
             "cv_ozet": tablo.loc[en_iyi].to_dict()}, A.MODEL_DOSYASI)
print(f"\nKaydedildi → {A.MODEL_DOSYASI}")

tablo.to_csv(A.CIKTI / "model_karsilastirma.csv")
kirilim.to_csv(A.CIKTI / "alt_kirilimlar.csv", index=False)
mcn.to_csv(A.CIKTI / "mcnemar.csv", index=False)
wil.to_csv(A.CIKTI / "wilcoxon_mac_bazli.csv", index=False)
mac_dog.to_csv(A.CIKTI / "mac_bazli_dogruluk.csv")
if abl is not None:
    abl.to_csv(A.CIKTI / "ablasyon.csv", index=False)
with open(A.CIKTI / "veri_raporu.json", "w", encoding="utf-8") as f:
    json.dump(rapor, f, ensure_ascii=False, indent=2)
