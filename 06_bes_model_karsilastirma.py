"""
ADIM 6 — BEŞ MAKİNE ÖĞRENMESİ MODELİNİN KARŞILAŞTIRILMASI (makaledeki tamamlayıcı analiz)

Girdiler:  cinsiyet, maç düzeyi (kategori), vuranın konumu, rakibin konumu
Çıktılar:  düşme bölgesi (18 kanonik hücre), spin (3), top yüksekliği (3), kademe (3)
Modeller:  çok terimli lojistik regresyon, rastgele orman, XGBoost, LightGBM, MLP
Taban:     çoğunluk sınıfı, koşullu frekans tablosu

Üretilenler (cikti/karsilastirma/):
  tablo5_dusme_bolgesi.csv        Makale Tablo 5
  tablo6_spin_yukseklik_kademe.csv  Makale Tablo 6
  tablo7_servis_ralli.csv         Makale Tablo 7 (servis / ralli alt kırılımı)
  cv_<cikti>.csv                  her çıktı için tüm metrikler (95% GA dahil)
  fark_<cikti>.csv                frekans tablosuna göre eşleştirilmiş bootstrap farkları
  wilcoxon_<cikti>.csv            maç bazlı Wilcoxon (log-kaybı ve ilk-1), Holm düzeltmeli
  hiperparametreler.csv, surumler.csv
  sekil4_logkaybi_farki.png       Makale Şekil 4
  sekil5_guvenirlik.png           Makale Şekil 5
  karsilastirma_tablolari.xlsx    yukarıdaki tüm tablolar tek dosyada
  oof_olasiliklar.npz             katlar dışı olasılıklar (önbellek)

Çalıştırma:
  python 06_bes_model_karsilastirma.py              # her şeyi hesaplar (~2-3 dk)
  python 06_bes_model_karsilastirma.py --onbellek   # kayıtlı katlar dışı olasılıkları kullanır
"""
import argparse
import os
import platform
import time
from importlib.metadata import version

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon
from sklearn.model_selection import GroupKFold

from tenis import ayarlar as A
from tenis.atis_modeli import (GIRDI_ADLARI, HEDEFLER, ML_MODELLER, TABAN_MODELLER,
                               girdi_tablosu, hedef_vektoru, model_olustur, ozet_metrik)
from tenis.metrikler import holm, ozet as bolge_ozet
from tenis.veri import hazirla, yukle

ap = argparse.ArgumentParser()
ap.add_argument("--onbellek", action="store_true", help="kayıtlı oof_olasiliklar.npz'yi kullan")
ap.add_argument("--bootstrap", type=int, default=2000)
arg = ap.parse_args()

pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 30)
pd.set_option("display.float_format", lambda v: f"{v:.3f}")

KLASOR = A.CIKTI / "karsilastirma"
KLASOR.mkdir(parents=True, exist_ok=True)
TUM = TABAN_MODELLER + ML_MODELLER
KISA = {"Çoğunluk sınıfı": "Çoğunluk sınıfı", "Frekans tablosu": "Koşullu frekans tablosu",
        "Lojistik regresyon": "Çok terimli lojistik", "Random Forest": "Rastgele orman",
        "XGBoost": "XGBoost", "LightGBM": "LightGBM", "MLP (sinir ağı)": "MLP"}
CIKTI_ADI = {"bolge": "Düşme bölgesi", "spin": "Spin", "yukseklik": "Yükseklik",
             "kademe": "Kademe"}
rng = np.random.default_rng(A.RASTGELE)
t_bas = time.time()

# ── Veri ────────────────────────────────────────────────────────────────────
df, rapor = hazirla(yukle())
X = girdi_tablosu(df)
gruplar = df.mac_id.to_numpy()
servis = (df.vurus_ailesi == "Servis").to_numpy()      # YALNIZCA raporlama için, girdi değil
katlar = list(GroupKFold(n_splits=A.N_FOLD).split(X, groups=gruplar))
Y = {h: hedef_vektoru(df, h) for h in HEDEFLER}
print(f"Atış: {len(df):,} | Maç: {rapor['mac_sayisi']} | Girdi: {len(GIRDI_ADLARI)} özellik "
      f"| Bootstrap: {arg.bootstrap}")

# ── 1) Katlar dışı olasılıklar ──────────────────────────────────────────────
onbellek = KLASOR / "oof_olasiliklar.npz"
P = {}
if arg.onbellek and onbellek.exists():
    z = np.load(onbellek)
    P = {(h, m): z[f"{h}__{i}"] for h in HEDEFLER for i, m in enumerate(TUM)}
    print("Katlar dışı olasılıklar önbellekten yüklendi.")
else:
    sure = {}
    for h in HEDEFLER:
        k = len(HEDEFLER[h]["etiketler"])
        y = Y[h]
        for m in TUM:
            t0 = time.time()
            Pm = np.full((len(y), k), np.nan)
            for tr, te in katlar:
                tr, te = tr[y[tr] >= 0], te[y[te] >= 0]
                Pm[te] = model_olustur(m, k).fit(X.iloc[tr], y[tr]).predict_proba(X.iloc[te])
            P[(h, m)] = Pm
            sure[(h, m)] = time.time() - t0
            print(f"  {CIKTI_ADI[h]:<14} {m:<20} {sure[(h, m)]:5.1f} sn")
    np.savez_compressed(onbellek, **{f"{h}__{i}": P[(h, m)]
                                     for h in HEDEFLER for i, m in enumerate(TUM)})


# ── Yardımcılar ─────────────────────────────────────────────────────────────
def ece(p, y, n_kutu=10):
    """En olası sınıfın beklenen kalibrasyon hatası (10 eşit genişlikte kutu)."""
    g, t = p.max(1), p.argmax(1) == y
    kutu = np.minimum((g * n_kutu).astype(int), n_kutu - 1)
    return sum((kutu == b).mean() * abs(t[kutu == b].mean() - g[kutu == b].mean())
               for b in range(n_kutu) if (kutu == b).any())


def guvenirlik(p, y, n_kutu=10, en_az=20):
    g, t = p.max(1), p.argmax(1) == y
    kutu = np.minimum((g * n_kutu).astype(int), n_kutu - 1)
    s = [(g[kutu == b].mean(), t[kutu == b].mean(), (kutu == b).sum())
         for b in range(n_kutu) if (kutu == b).sum() >= en_az]
    return np.array(s)


def mac_toplamlari(dizi, mac):
    """Maç başına toplam ve sayım (bootstrap için)."""
    s = pd.DataFrame({"m": mac, "v": dizi}).groupby("m").v.agg(["sum", "count"])
    return s["sum"].to_numpy(), s["count"].to_numpy(), s.index.to_numpy()


macs = np.unique(gruplar)
boot_idx = rng.integers(0, len(macs), size=(arg.bootstrap, len(macs)))


def boot_ga(toplam, sayi):
    est = (toplam[boot_idx].sum(1)) / (sayi[boot_idx].sum(1))
    return np.percentile(est, [2.5, 97.5])


# ── 2) Metrikler, güven aralıkları, testler ────────────────────────────────
cv, farklar, wil_tab, en_iyi, mac_ll_tum, mac_t1_tum = {}, {}, {}, {}, {}, {}
for h in HEDEFLER:
    gec = Y[h] >= 0
    y, mac = Y[h][gec], gruplar[gec]
    satirlar, ll_mac, t1_mac = {}, {}, {}
    for m in TUM:
        p = P[(h, m)][gec]
        ll = -np.log(np.clip(p[np.arange(len(y)), y], 1e-12, 1))
        dogru = (p.argmax(1) == y).astype(float)
        met = ozet_metrik(p, y)
        met["ECE"] = ece(p, y)
        if h == "bolge":
            bo = bolge_ozet(p, y)
            met.update({k: bo[k] for k in ("Kaba 9 sınıf %", "Derinlik %", "Yön %", "Ort. hata (m)")})
        ts, ns, _ = mac_toplamlari(ll, mac)
        lo, hi = boot_ga(ts, ns)
        met["Log-loss GA alt"], met["Log-loss GA üst"] = lo, hi
        ds, _, _ = mac_toplamlari(dogru, mac)
        lo, hi = boot_ga(ds, ns)
        met["Top-1 GA alt"], met["Top-1 GA üst"] = 100 * lo, 100 * hi
        satirlar[m] = met
        ll_mac[m] = ts / ns
        t1_mac[m] = ds / ns
        mac_ll_tum[(h, m)], mac_t1_tum[(h, m)] = (ts, ns), (ds, ns)
    tablo = pd.DataFrame(satirlar).T
    cv[h] = tablo
    en_iyi[h] = min(ML_MODELLER, key=lambda m: tablo.loc[m, "Log-loss"])

    # Frekans tablosuna göre eşleştirilmiş bootstrap farkları (negatif = daha iyi)
    ref_t, ref_n = mac_ll_tum[(h, "Frekans tablosu")]
    fs = []
    for m in ML_MODELLER:
        t, n = mac_ll_tum[(h, m)]
        fark = (t[boot_idx].sum(1) - ref_t[boot_idx].sum(1)) / n[boot_idx].sum(1)
        fs.append({"Model": m, "Log-loss farkı": (t.sum() - ref_t.sum()) / n.sum(),
                   "GA alt": np.percentile(fark, 2.5), "GA üst": np.percentile(fark, 97.5)})
    farklar[h] = pd.DataFrame(fs)

    # Maç bazlı Wilcoxon: en iyi model vs diğerleri, log-kaybı ve ilk-1, Holm
    ref = en_iyi[h]
    w = []
    for m in TUM:
        if m == ref:
            continue
        d_ll = ll_mac[m] - ll_mac[ref]                  # >0: en iyi model daha iyi
        d_t1 = t1_mac[ref] - t1_mac[m]                  # >0: en iyi model daha iyi
        w.append({"Karşılaştırma": f"{ref} vs {m}",
                  "Log-loss farkı (ort.)": d_ll.mean(), "LL: daha iyi maç": int((d_ll > 0).sum()),
                  "LL p (ham)": wilcoxon(ll_mac[ref], ll_mac[m]).pvalue if np.abs(d_ll).sum() else 1.0,
                  "İlk-1 farkı (puan)": 100 * d_t1.mean(), "İlk-1: daha iyi maç": int((d_t1 > 0).sum()),
                  "İlk-1 p (ham)": wilcoxon(t1_mac[ref], t1_mac[m]).pvalue if np.abs(d_t1).sum() else 1.0})
    w = pd.DataFrame(w)
    w["LL p (Holm)"] = holm(w["LL p (ham)"])
    w["İlk-1 p (Holm)"] = holm(w["İlk-1 p (ham)"])
    wil_tab[h] = w

    print(f"\n=== {CIKTI_ADI[h].upper()} — en iyi (log-kaybı): {ref} ===")
    sutun = ["Top-1 %", "Top-3 %", "Log-loss", "Log-loss GA alt", "Log-loss GA üst", "Brier", "ECE",
             "Dengeli doğruluk %"]
    print(tablo[[c for c in sutun if c in tablo]].to_string())
    print(farklar[h].to_string(index=False))
    print(w.to_string(index=False))
    tablo.to_csv(KLASOR / f"cv_{h}.csv")
    farklar[h].to_csv(KLASOR / f"fark_{h}.csv", index=False)
    w.to_csv(KLASOR / f"wilcoxon_{h}.csv", index=False)


# ── 3) Makale tabloları ─────────────────────────────────────────────────────
def ll_ga(t, m):
    r = t.loc[m]
    return f"{r['Log-loss']:.3f} ({r['Log-loss GA alt']:.3f}–{r['Log-loss GA üst']:.3f})"


b = cv["bolge"]
tablo5 = pd.DataFrame([{
    "Model": KISA[m], "Log-kaybı (95% GA)": ll_ga(b, m), "Brier": f"{b.loc[m, 'Brier']:.3f}",
    "ECE": f"{b.loc[m, 'ECE']:.3f}", "İlk-1": f"{b.loc[m, 'Top-1 %']:.1f}%",
    "İlk-3": f"{b.loc[m, 'Top-3 %']:.1f}%", "Kaba (9 sınıf)": f"{b.loc[m, 'Kaba 9 sınıf %']:.1f}%",
    "Ort. hata (m)": f"{b.loc[m, 'Ort. hata (m)']:.2f}"} for m in TUM])

tablo6 = []
for h in ("spin", "yukseklik", "kademe"):
    t = cv[h]
    for m in TUM:
        tablo6.append({"Çıktı": CIKTI_ADI[h], "Model": KISA[m], "Log-kaybı (95% GA)": ll_ga(t, m),
                       "Brier": f"{t.loc[m, 'Brier']:.3f}", "ECE": f"{t.loc[m, 'ECE']:.3f}",
                       "İlk-1": f"{t.loc[m, 'Top-1 %']:.1f}%",
                       "Dengeli doğruluk": f"{t.loc[m, 'Dengeli doğruluk %']:.1f}%"})
tablo6 = pd.DataFrame(tablo6)

tablo7 = []
for h in HEDEFLER:
    gec = Y[h] >= 0
    for etiket, maske in (("Servis", servis), ("Ralli", ~servis)):
        mm = gec & maske
        for m in ("Frekans tablosu", en_iyi[h]):
            p = P[(h, m)][mm]
            y = Y[h][mm]
            tablo7.append({"Çıktı": CIKTI_ADI[h], "Alt küme": etiket, "n": int(mm.sum()),
                           "Model": KISA[m], "İlk-1": f"{100*(p.argmax(1) == y).mean():.1f}%",
                           "Log-kaybı": f"{-np.mean(np.log(np.clip(p[np.arange(len(y)), y], 1e-12, 1))):.3f}"})
tablo7 = pd.DataFrame(tablo7)

ozet = pd.DataFrame([{
    "Çıktı": CIKTI_ADI[h], "En iyi model": KISA[en_iyi[h]],
    "Çoğunluk ilk-1": f"{cv[h].loc['Çoğunluk sınıfı', 'Top-1 %']:.1f}%",
    "Frekans ilk-1": f"{cv[h].loc['Frekans tablosu', 'Top-1 %']:.1f}%",
    "En iyi ilk-1": f"{cv[h].loc[en_iyi[h], 'Top-1 %']:.1f}%",
    "Frekans log-kaybı": f"{cv[h].loc['Frekans tablosu', 'Log-loss']:.3f}",
    "En iyi log-kaybı": f"{cv[h].loc[en_iyi[h], 'Log-loss']:.3f}",
    "Fark (95% GA)": "{:.3f} ({:.3f} ile {:.3f})".format(
        *farklar[h].set_index("Model").loc[en_iyi[h], ["Log-loss farkı", "GA alt", "GA üst"]]),
    "Wilcoxon p (Holm), frekansa göre": f"{wil_tab[h].set_index('Karşılaştırma').loc[f'{en_iyi[h]} vs Frekans tablosu', 'LL p (Holm)']:.3f}",
} for h in HEDEFLER])

hiper = pd.DataFrame([
    ("Koşullu frekans tablosu", "P(çıktı | vuran hücresi, rakip hücresi); az veride P(çıktı | vuran hücresi) ve marjinal dağılıma doğru düzleştirme, sözde sayım α = 5"),
    ("Çok terimli lojistik", "Standartlaştırma + L2 düzenlileştirme, C = 0.5, en fazla 3,000 iterasyon (lbfgs)"),
    ("Rastgele orman", "300 ağaç, yaprakta en az 10 vuruş, max_features = √p, tohum 42"),
    ("XGBoost", "300 ağaç, öğrenme oranı 0.05, en fazla derinlik 4, subsample 0.8, colsample_bytree 0.8, min_child_weight 5, L2 (λ) 1.0, hist"),
    ("LightGBM", "300 ağaç, öğrenme oranı 0.03, 15 yaprak, yaprakta en az 20 vuruş, subsample 0.8, colsample_bytree 0.8, L2 (λ) 1.0"),
    ("MLP", "Standartlaştırma + 128 ve 64 nöronlu iki gizli katman, ReLU, Adam (öğrenme oranı 0.001), α = 0.001, erken durdurma (15% doğrulama, 15 iterasyon sabır), en fazla 400 iterasyon"),
], columns=["Model", "Hiperparametreler (önceden sabit, katmanlarda ayarlanmadı)"])

surum = pd.DataFrame([("Python", platform.python_version()), ("İşletim sistemi", platform.platform()),
                      ("CPU çekirdeği", str(os.cpu_count()))] +
                     [(p, version(p)) for p in ("numpy", "pandas", "scipy", "scikit-learn", "xgboost",
                                                "lightgbm", "matplotlib")],
                     columns=["Bileşen", "Sürüm"])

for ad, t in (("tablo5_dusme_bolgesi", tablo5), ("tablo6_spin_yukseklik_kademe", tablo6),
              ("tablo7_servis_ralli", tablo7), ("ozet", ozet), ("hiperparametreler", hiper),
              ("surumler", surum)):
    t.to_csv(KLASOR / f"{ad}.csv", index=False)
print("\n=== TABLO 5 — DÜŞME BÖLGESİ ===\n" + tablo5.to_string(index=False))
print("\n=== TABLO 6 — SPİN, YÜKSEKLİK, KADEME ===\n" + tablo6.to_string(index=False))
print("\n=== TABLO 7 — SERVİS / RALLİ ===\n" + tablo7.to_string(index=False))
print("\n=== ÖZET ===\n" + ozet.to_string(index=False))
print("\n" + surum.to_string(index=False))

with pd.ExcelWriter(KLASOR / "karsilastirma_tablolari.xlsx") as xw:
    ozet.to_excel(xw, sheet_name="Özet", index=False)
    tablo5.to_excel(xw, sheet_name="Tablo 5", index=False)
    tablo6.to_excel(xw, sheet_name="Tablo 6", index=False)
    tablo7.to_excel(xw, sheet_name="Tablo 7 servis-ralli", index=False)
    for h in HEDEFLER:
        cv[h].to_excel(xw, sheet_name=f"CV {CIKTI_ADI[h]}")
        wil_tab[h].to_excel(xw, sheet_name=f"Wilcoxon {CIKTI_ADI[h]}", index=False)
    hiper.to_excel(xw, sheet_name="Hiperparametreler", index=False)
    surum.to_excel(xw, sheet_name="Sürümler", index=False)

# ── 4) Şekiller ─────────────────────────────────────────────────────────────
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, StrMethodFormatter

MAVI, GRI, METIN, IKINCIL = "#2a78d6", "#8a8984", "#0b0b0b", "#52514e"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": "#c9c8c3",
                     "axes.labelcolor": IKINCIL, "xtick.color": IKINCIL, "ytick.color": IKINCIL,
                     "axes.spines.top": False, "axes.spines.right": False})

# Şekil 4 — frekans tablosuna göre log-kaybı farkı (95% GA)
fig, eks = plt.subplots(2, 2, figsize=(8, 5.6), sharey=True)
eks = eks.ravel()
for ax, h in zip(eks, HEDEFLER):
    f = farklar[h].set_index("Model").loc[ML_MODELLER]
    yk = np.arange(len(ML_MODELLER))[::-1]
    ax.axvline(0, color=GRI, lw=1, ls="--", zorder=1)
    for yi, m in zip(yk, ML_MODELLER):
        r = f.loc[m]
        en = m == en_iyi[h]
        ax.plot([r["GA alt"], r["GA üst"]], [yi, yi], color=MAVI, lw=2, solid_capstyle="round",
                zorder=2)
        ax.plot(r["Log-loss farkı"], yi, "o", ms=8 if en else 6, color=MAVI if en else "white",
                mec=MAVI, mew=2, zorder=3)
    ax.set_yticks(yk, [KISA[m] for m in ML_MODELLER])
    ax.xaxis.set_major_locator(MaxNLocator(4))
    ax.xaxis.set_major_formatter(StrMethodFormatter("{x:.2f}"))
    ax.set_title(CIKTI_ADI[h], color=METIN, fontsize=11, loc="left")
    ax.grid(axis="x", color="#e6e5e0", lw=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
for ax in eks[2:]:
    ax.set_xlabel("Log-kaybı farkı (model − frekans tablosu)")
fig.text(0.99, 0.01, "Sol (negatif) = frekans tablosundan daha iyi · dolu nokta = en iyi model",
         ha="right", va="bottom", color=IKINCIL, fontsize=8)
fig.tight_layout(rect=(0, 0.04, 1, 1))
fig.savefig(KLASOR / "sekil4_logkaybi_farki.png", dpi=300)
plt.close(fig)

# Şekil 5 — güvenirlik: en iyi model ve frekans tablosu
fig, eks = plt.subplots(2, 2, figsize=(8, 6.4))
eks = eks.ravel()
for ax, h in zip(eks, HEDEFLER):
    gec = Y[h] >= 0
    ax.plot([0, 1], [0, 1], color=GRI, lw=1, ls="--")
    for m, renk, cizgi in (("Frekans tablosu", GRI, "-"), (en_iyi[h], MAVI, "-")):
        r = guvenirlik(P[(h, m)][gec], Y[h][gec])
        ax.plot(r[:, 0], r[:, 1], cizgi, color=renk, lw=2, marker="o", ms=5,
                label=KISA[m], mec="white", mew=1)
    lo = 0 if h == "bolge" else 0.3
    ax.set_xlim(lo, 1); ax.set_ylim(lo, 1)
    ax.set_title(CIKTI_ADI[h], color=METIN, fontsize=11, loc="left")
    if h in ("yukseklik", "kademe"):
        ax.set_xlabel("Tahmin edilen olasılık")
    if h in ("bolge", "yukseklik"):
        ax.set_ylabel("Gözlenen doğru oranı")
    ax.grid(color="#e6e5e0", lw=0.8); ax.set_axisbelow(True); ax.tick_params(length=0)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
fig.tight_layout()
fig.savefig(KLASOR / "sekil5_guvenirlik.png", dpi=300)
plt.close(fig)

print(f"\nTablolar ve şekiller → {KLASOR}")
print(f"Toplam süre: {time.time() - t_bas:.0f} sn")
