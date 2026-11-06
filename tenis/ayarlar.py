"""
Tüm sabitler tek yerde. Başka hiçbir dosyada "sihirli sayı" olmamalı.
"""
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
VERITABANI = KOK / "veri" / "veritabani2.db"
CIKTI = KOK / "cikti"
MODEL_DOSYASI = CIKTI / "model.joblib"

RASTGELE = 42
N_FOLD = 5                      # GroupKFold (maç bazlı) kat sayısı

# ── Kort ızgarası ────────────────────────────────────────────────────────────
# Her yarı: 8 sütun x 4 satır = 32 bölge (+ 8 koridor bölgesi LT/RT veya LB/RB).
# Satır 0 = file en yakın, satır 3 = dip çizgi arkası.
N_SUTUN = 8
N_SATIR = 4

# Mesafe metriği için yaklaşık ölçüler (GUI çizimiyle uyumlu varsayım):
# 8 sütun tekler genişliğini (8,23 m), 4 satır file→dip mesafesini (11,89 m) kaplar.
SUTUN_METRE = 8.23 / N_SUTUN
SATIR_METRE = 11.89 / N_SATIR

# ── Hedef (tahmin edilen) bölge tanımı ───────────────────────────────────────
# Başarılı atışların %99,8'i satır 0-2 ve sütun 1-6 içine düşüyor → 18 sınıf.
HEDEF_SATIRLAR = (0, 1, 2)
HEDEF_SUTUNLAR = (1, 2, 3, 4, 5, 6)
DERINLIK_ADLARI = {0: "Kısa", 1: "Orta", 2: "Derin"}
# Kaba yön: vuran oyuncunun bakış açısından sol / orta / sağ
YON_GRUBU = {1: "Sol", 2: "Sol", 3: "Orta", 4: "Orta", 5: "Sağ", 6: "Sağ"}

# ── Kategorik değişkenlerin sadeleştirilmesi ────────────────────────────────
# Veritabanında 24 vuruş stili var, bir kısmı aynı şeyin farklı yazımı.
VURUS_AILESI = {
    "Forehand": "Forehand", "Topspin Forehand": "Forehand",
    "Backhand": "Backhand", "Two-Handed Backhand": "Backhand", "Topspin Backhand": "Backhand",
    "Forehand slice": "Slice", "backhand slice": "Slice", "Slice": "Slice",
    "Volley": "Vole", "Forehand volley": "Vole", "Backhand volley": "Vole",
    "Half Volley": "Vole", "Drive Volley": "Vole", "Drop Volley": "Vole",
    "Serve Flat": "Servis", "Serve Slice": "Servis", "Serve Topspin": "Servis",
    "Kick Serve": "Servis",
    "Smash": "Smaç",
    "Drop Shot": "Diğer", "Lob": "Diğer", "Return": "Diğer",
    "Approach Shot": "Diğer", "Passing Shot": "Diğer",
}
VURUS_AILELERI = ["Forehand", "Backhand", "Slice", "Vole", "Servis", "Smaç", "Diğer"]

# Vuruşun hangi el tarafından yapıldığı (kros/paralel yönü için önemli)
VURUS_ELI = {
    "Forehand": "FH", "Topspin Forehand": "FH", "Forehand slice": "FH", "Forehand volley": "FH",
    "Backhand": "BH", "Two-Handed Backhand": "BH", "Topspin Backhand": "BH",
    "backhand slice": "BH", "Backhand volley": "BH",
}
ELLER = ["FH", "BH", "Yok"]

# Spin: Backspin / Slice / underspin aynı fiziksel etki → tek grup
SPIN_GRUBU = {"Topspin": "Topspin", "Slice": "Kesik", "Backspin": "Kesik",
              "underspin": "Kesik", "flat": "Düz"}
SPINLER = ["Topspin", "Kesik", "Düz"]

CINSIYETLER = ["Erkekler", "Kadınlar"]
KATEGORILER = ["Best", "Middle", "Low"]

# ── Modelde KULLANILMAYAN sütunlar ve nedenleri ─────────────────────────────
DISLANAN_SUTUNLAR = {
    "top_hizi": "atış sonrası ölçülür",
    "top_mesafe_metre": "atış sonrası ölçülür",
    "top_ucus_suresi": "atış sonrası ölçülür",
    "frame_farklari": "atış sonrası ölçülür",
    "bulusulan_bolge": "rakibin topa BİR SONRAKİ temas noktası (gelecek bilgisi)",
    "dustugu_bolge": "hedef değişken",
}
