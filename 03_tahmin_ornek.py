"""
ADIM 3 — Kaydedilmiş modelle örnek tahmin.
Çalıştırma:  python 03_tahmin_ornek.py
"""
from tenis.tahmin import TenisTahminci

t = TenisTahminci()
print(f"Model: {t.model_adi}  |  CV Top-1: %{t.cv_ozet.get('Top-1 %', float('nan')):.1f}\n")

ornekler = [
    dict(cinsiyet="Erkekler", kategori="Best", vurulan="29x", nereden="27", vurus="Forehand"),
    dict(cinsiyet="Erkekler", kategori="Best", vurulan="29", nereden="27x", vurus="Forehand"),
    dict(cinsiyet="Kadınlar", kategori="Middle", vurulan="31x", nereden="26", vurus="Backhand"),
    dict(cinsiyet="Erkekler", kategori="Best", vurulan="OUTSIDE", nereden="28", vurus="Serve Flat",
         spin="Slice", kademe=3, yukseklik=1),
]
for o in ornekler:
    print(o)
    for i, r in enumerate(t.predict(**o), 1):
        print(f"   {i}. {r['zone']:>4}  ({r['hucre']:<8}) %{100*r['prob']:5.1f}")
    kaba = list(t.kaba_tahmin(**o).items())[:3]
    print("   Kaba:", ", ".join(f"{k} %{100*v:.0f}" for k, v in kaba), "\n")
