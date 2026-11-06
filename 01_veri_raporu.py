"""
ADIM 1 — Veri denetimi. Modelden önce verinin ne söylediğini görmek için.
Çalıştırma:  python 01_veri_raporu.py
"""
import pandas as pd

from tenis import ayarlar as A
from tenis import bolgeler as B
from tenis.veri import hazirla, yukle

pd.set_option("display.width", 160)
A.CIKTI.mkdir(exist_ok=True)

ham = yukle(sadece_basarili=False)
print(f"Toplam kayıt: {len(ham):,}  |  başarılı: {(ham.atis_basarili_mi == 1).sum():,}")

df, rapor = hazirla(yukle())
print("\nTemizleme raporu:", rapor)

print("\nMaç başına atış (değerlendirme birimi = maç):")
print(df.groupby(["mac_id", "cinsiyet", "kategori"]).size().rename("atış").to_string())

print("\nVuruş ailesi dağılımı (24 ham stil → 7 aile):")
print(pd.crosstab(df.vurus_ad, df.vurus_ailesi).loc[lambda t: t.sum(axis=1) > 0].to_string())

print("\nSpin x vuruş ailesi (spin büyük ölçüde vuruştan türetilebiliyor):")
print(pd.crosstab(df.vurus_ailesi, df.spin_ad).to_string())

print("\nKanonik hedef dağılımı (satır=derinlik, sütun=vuranın solundan sağına):")
tab = df.hedef_hucre.value_counts().rename_axis("h").reset_index()
tab["derinlik"] = tab.h.map(lambda h: A.DERINLIK_ADLARI[h[0]])
tab["sutun"] = tab.h.map(lambda h: h[1])
isi = tab.pivot(index="derinlik", columns="sutun", values="count").loc[["Kısa", "Orta", "Derin"]]
print(isi.to_string())
print(f"\nEn sık sınıfın payı (çoğunluk taban çizgisi): %{100*df.y.value_counts(normalize=True).max():.1f}")

print("\nKaba hedef (derinlik x yön) dağılımı:")
print(df.y_kaba.value_counts(normalize=True).mul(100).round(1).to_string())

print("\nModelden dışlanan sütunlar:")
for k, v in A.DISLANAN_SUTUNLAR.items():
    print(f"  {k:<18} → {v}")

isi.to_csv(A.CIKTI / "hedef_isi_haritasi.csv")
