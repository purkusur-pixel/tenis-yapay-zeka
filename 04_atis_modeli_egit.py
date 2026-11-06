"""
ADIM 4 — ATIŞ MODELİ: 4 girdi → 4 çıktı, 5 makine öğrenmesi modeli.  (BİR KEZ çalıştırılır)

Girdiler (arayüzde seçilen):  cinsiyet, kategori, vuran konumu, rakip konumu
Çıktılar (ML'in tahmin ettiği): düşme bölgesi, spin, top yüksekliği, kademe
Modeller: Lojistik regresyon, Random Forest, XGBoost, LightGBM, MLP
          (+ karşılaştırma için 2 taban çizgisi: çoğunluk sınıfı, frekans tablosu)

Yapılanlar:
  1) Maç bazlı 5-kat çapraz doğrulama (GroupKFold) → her çıktı için model karşılaştırması
  2) Maç bazlı Wilcoxon testi (en iyi model vs diğerleri, log-loss üzerinden, Holm düzeltmeli)
  3) 5 modeli tüm veriyle eğitip kaydetme      → cikti/atis_modelleri.joblib
  4) TÜM girdi kombinasyonlarını önceden hesaplama → cikti/onhesap.json
     (arayüz ve konsol yalnızca bu dosyayı okur; tekrar eğitim gerekmez)

Çalıştırma:  python 04_atis_modeli_egit.py
"""
import json
import os
import time
from datetime import datetime
from itertools import product

import joblib
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon
from sklearn.model_selection import GroupKFold

from tenis import ayarlar as A
from tenis import bolgeler as B
from tenis import onhesap as O
from tenis.atis_modeli import (GIRDI_ADLARI, HEDEFLER, ML_MODELLER, TABAN_MODELLER,
                               girdi_satiri, girdi_tablosu, hedef_vektoru, model_olustur,
                               ozet_metrik)
from tenis.metrikler import holm, ozet as bolge_ozet
from tenis.veri import hazirla, yukle

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)
pd.set_option("display.float_format", lambda v: f"{v:.3f}")

KLASOR = A.CIKTI / "atis_modeli"
KLASOR.mkdir(parents=True, exist_ok=True)
OLCEK = 10000                      # olasılıklar JSON'da tamsayı (onbinde) saklanır

t_bas = time.time()
print(f"İşlemci çekirdeği: {os.cpu_count()}  (tüm modeller CPU'da çalışır)")

# ── Veri ────────────────────────────────────────────────────────────────────
df, rapor = hazirla(yukle())
X = girdi_tablosu(df)
gruplar = df.mac_id.to_numpy()
katlar = list(GroupKFold(n_splits=A.N_FOLD).split(X, groups=gruplar))
print(f"Atış: {len(df):,}  |  Maç: {rapor['mac_sayisi']}  |  Girdi özelliği: {len(GIRDI_ADLARI)}")
print("Girdi özellikleri:", ", ".join(GIRDI_ADLARI))

Y = {h: hedef_vektoru(df, h) for h in HEDEFLER}
for h, y in Y.items():
    gecerli = y >= 0
    dag = np.bincount(y[gecerli], minlength=len(HEDEFLER[h]["etiketler"])) / gecerli.sum()
    if h != "bolge":
        print(f"  {HEDEFLER[h]['ad']:<16} n={gecerli.sum():,}  dağılım: " +
              ", ".join(f"{e} %{100*d:.1f}" for e, d in zip(HEDEFLER[h]["etiketler"], dag)))


def oof(model_adi: str, h: str) -> tuple[np.ndarray, np.ndarray]:
    """Katlar dışı olasılıklar (her atış, maçı eğitimde YOKKEN tahmin edilir)."""
    y = Y[h]
    k = len(HEDEFLER[h]["etiketler"])
    P = np.full((len(y), k), np.nan)
    for tr, te in katlar:
        tr = tr[y[tr] >= 0]
        te = te[y[te] >= 0]
        m = model_olustur(model_adi, k).fit(X.iloc[tr], y[tr])
        P[te] = m.predict_proba(X.iloc[te])
    gecerli = y >= 0
    return P[gecerli], gecerli


# ── 1) Çapraz doğrulama ─────────────────────────────────────────────────────
TUM = TABAN_MODELLER + ML_MODELLER
cv_tablolar, en_iyi, wilcox = {}, {}, {}
for h in HEDEFLER:
    print(f"\n=== {HEDEFLER[h]['ad'].replace('i', 'İ').upper()} — maç bazlı 5-kat CV ===")
    satir, mac_ll = {}, {}
    for ad in TUM:
        t0 = time.time()
        P, gecerli = oof(ad, h)
        y = Y[h][gecerli]
        m = ozet_metrik(P, y)
        if h == "bolge":
            bo = bolge_ozet(P, y)
            m.update({k: bo[k] for k in ("Kaba 9 sınıf %", "Derinlik %", "Yön %", "Ort. hata (m)")})
        m["Süre (sn)"] = time.time() - t0
        satir[ad] = m
        ll = -np.log(np.clip(P[np.arange(len(y)), y], 1e-12, 1))
        mac_ll[ad] = pd.Series(ll).groupby(gruplar[gecerli]).mean()
        print(f"  {ad:<20} Top-1 %{m['Top-1 %']:5.1f}   log-loss {m['Log-loss']:.3f}   "
              f"({m['Süre (sn)']:.1f} sn)")
    tablo = pd.DataFrame(satir).T
    cv_tablolar[h] = tablo
    en_iyi[h] = min(ML_MODELLER, key=lambda a: tablo.loc[a, "Log-loss"])

    # Maç bazlı Wilcoxon: en iyi model vs diğerleri (log-loss; pozitif fark = en iyi daha iyi)
    ref = en_iyi[h]
    w = []
    for ad in TUM:
        if ad == ref:
            continue
        fark = mac_ll[ad] - mac_ll[ref]
        p = wilcoxon(mac_ll[ref], mac_ll[ad]).pvalue if fark.abs().sum() else 1.0
        w.append({"Karşılaştırma": f"{ref} vs {ad}", "Ort. log-loss farkı": fark.mean(),
                  "Daha iyi olduğu maç": int((fark > 0).sum()), "p (ham)": p})
    w = pd.DataFrame(w)
    w["p (Holm)"] = holm(w["p (ham)"])
    w["Anlamlı (α=0,05)"] = np.where(w["p (Holm)"] < 0.05, "Evet", "Hayır")
    wilcox[h] = w

    print(tablo.to_string())
    print(f"→ En iyi (en düşük log-loss): {ref}")
    print(w.to_string(index=False))
    tablo.to_csv(KLASOR / f"cv_{h}.csv")
    w.to_csv(KLASOR / f"wilcoxon_{h}.csv", index=False)

# ── 2) Son modeller: tüm veriyle eğit ───────────────────────────────────────
print("\nSon modeller tüm veriyle eğitiliyor...")
son = {}
for ad in ML_MODELLER:
    son[ad] = {}
    for h in HEDEFLER:
        y = Y[h]
        g = y >= 0
        son[ad][h] = model_olustur(ad, len(HEDEFLER[h]["etiketler"])).fit(X[g], y[g])
    print(f"  {ad} ✓")
joblib.dump({"modeller": son, "girdi_adlari": GIRDI_ADLARI, "hedefler": HEDEFLER,
             "en_iyi": en_iyi}, A.CIKTI / "atis_modelleri.joblib", compress=3)

# ── 3) Tüm kombinasyonları önceden hesapla ─────────────────────────────────
komb = list(product(O.CINSIYETLER, O.KATEGORILER, O.VURAN_SECENEKLERI, O.RAKIP_SECENEKLERI))
Xk = pd.DataFrame([girdi_satiri(*k) for k in komb])[GIRDI_ADLARI].astype(np.float32)
print(f"\n{len(komb):,} kombinasyon x {len(ML_MODELLER)} model x {len(HEDEFLER)} çıktı hesaplanıyor...")
olas = {ad: {h: np.rint(son[ad][h].predict_proba(Xk) * OLCEK).astype(int).tolist()
             for h in HEDEFLER} for ad in ML_MODELLER}

cv_json = {h: {ad: {k: round(float(v), 4) for k, v in cv_tablolar[h].loc[ad].items()}
               for ad in TUM} for h in HEDEFLER}
paket = {
    "meta": {"olusturma": datetime.now().isoformat(timespec="seconds"),
             "atis_sayisi": int(len(df)), "mac_sayisi": int(rapor["mac_sayisi"]),
             "girdiler": ["cinsiyet", "kategori", "vuran", "rakip"],
             "not": "Kategori Best eğitimde kullanıldı; tabloda yalnızca Middle ve Low var."},
    "hedefler": HEDEFLER,
    "modeller": ML_MODELLER,
    "en_iyi": en_iyi,
    "cv": cv_json,
    "bolge_adlari": [B.kanonikten_ada(r, c, "X") for r, c in B.HEDEF_HUCRELER],
    "kombinasyonlar": [O.anahtar(*k) for k in komb],
    "olcek": OLCEK,
    "olasiliklar": olas,
}
with open(O.ONHESAP_DOSYASI, "w", encoding="utf-8") as f:
    json.dump(paket, f, ensure_ascii=False, separators=(",", ":"))

ozet = pd.DataFrame({HEDEFLER[h]["ad"]: {
    "En iyi model": en_iyi[h],
    "Top-1 %": cv_tablolar[h].loc[en_iyi[h], "Top-1 %"],
    "Frekans tablosu Top-1 %": cv_tablolar[h].loc["Frekans tablosu", "Top-1 %"],
    "Log-loss": cv_tablolar[h].loc[en_iyi[h], "Log-loss"],
    "Frekans tablosu log-loss": cv_tablolar[h].loc["Frekans tablosu", "Log-loss"]}
    for h in HEDEFLER}).T
ozet.to_csv(KLASOR / "ozet.csv")
print("\n=== ÖZET ===")
print(ozet.to_string())
boyut = O.ONHESAP_DOSYASI.stat().st_size / 1e6
print(f"\nKaydedildi → {O.ONHESAP_DOSYASI}  ({boyut:.1f} MB)")
print(f"Kaydedildi → {A.CIKTI / 'atis_modelleri.joblib'}")
print(f"Tablolar   → {KLASOR}")
print(f"Toplam süre: {time.time() - t_bas:.0f} sn.  Şimdi:  python gui_atis.py")
