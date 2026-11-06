import os
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# Output directory
docs_img = Path(__file__).resolve().parent / "docs" / "images"
docs_img.mkdir(parents=True, exist_ok=True)

# Colors
C_BG = "#0D1826"
C_COURT_TOP = "#1665A0"
C_COURT_BOT = "#125488"
C_ALLEY = "#1E6E38"
C_SVC = "#1B72B8"
C_LINE = "#FFFFFF"
C_NET = "#E0E0E0"
C_TEXT_LIGHT = "#EAF2F8"
C_TEXT_DIM = "#8AAEC4"
C_ACCENT_YELLOW = "#FFD700"
C_ACCENT_CYAN = "#00E5FF"
C_ACCENT_ORANGE = "#FF9100"
C_ACCENT_RED = "#FF3D00"
C_ACCENT_GREEN = "#00E676"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "figure.facecolor": C_BG,
    "axes.facecolor": C_BG,
    "savefig.facecolor": C_BG,
    "savefig.edgecolor": C_BG,
})

# ==============================================================================
# 1. SAHA IZGARA SEMASI (Court Grid Diagram: 32 Zones Top + 32 Zones Bottom + Alleys)
# ==============================================================================
def draw_court_grid():
    fig, ax = plt.subplots(figsize=(12, 14), dpi=300)
    ax.set_xlim(-1.5, 9.5)
    ax.set_ylim(-1, 9)
    ax.set_aspect("equal")
    ax.axis("off")

    # Titles
    ax.text(4.0, 8.6, "TENİS KORTU IZGARA VE BÖLGE ŞEMASI", ha="center", va="center",
            fontsize=18, fontweight="bold", color=C_TEXT_LIGHT)
    ax.text(4.0, 8.25, "Tennis Court Grid & Zone Coordinate Architecture (32 + 32 Zones)",
            ha="center", va="center", fontsize=11, color=C_TEXT_DIM)

    # Court background polygons
    # Top Half (Opponent, 1-32)
    top_court = patches.Rectangle((0, 4), 8, 4, facecolor=C_COURT_TOP, edgecolor=C_LINE, linewidth=2.5)
    ax.add_patch(top_court)
    # Bottom Half (Striker, 1x-32x)
    bot_court = patches.Rectangle((0, 0), 8, 4, facecolor=C_COURT_BOT, edgecolor=C_LINE, linewidth=2.5)
    ax.add_patch(bot_court)

    # Doubles Alleys
    # Left Top Alley
    ax.add_patch(patches.Rectangle((-0.8, 4), 0.8, 4, facecolor=C_ALLEY, edgecolor=C_LINE, linewidth=1.5))
    # Right Top Alley
    ax.add_patch(patches.Rectangle((8, 4), 0.8, 4, facecolor=C_ALLEY, edgecolor=C_LINE, linewidth=1.5))
    # Left Bottom Alley
    ax.add_patch(patches.Rectangle((-0.8, 0), 0.8, 4, facecolor=C_ALLEY, edgecolor=C_LINE, linewidth=1.5))
    # Right Bottom Alley
    ax.add_patch(patches.Rectangle((8, 0), 0.8, 4, facecolor=C_ALLEY, edgecolor=C_LINE, linewidth=1.5))

    # Grid Lines inside Singles Court
    for c in range(1, 8):
        ax.plot([c, c], [0, 8], color=C_LINE, linestyle="--", linewidth=0.8, alpha=0.6)

    # Rows (from net to baselines)
    # Net is at y = 4
    # Rows Top: y = 5 (Row 0: Kısa), y = 6 (Row 1: Orta), y = 7 (Row 2: Derin), y = 8 (Baseline)
    for r in range(1, 4):
        ax.plot([0, 8], [4 + r, 4 + r], color=C_LINE, linestyle="--", linewidth=0.8, alpha=0.6)
        ax.plot([0, 8], [4 - r, 4 - r], color=C_LINE, linestyle="--", linewidth=0.8, alpha=0.6)
        # Alley horizontal splits
        ax.plot([-0.8, 0], [4 + r, 4 + r], color=C_LINE, linestyle=":", linewidth=0.7, alpha=0.5)
        ax.plot([8, 8.8], [4 + r, 4 + r], color=C_LINE, linestyle=":", linewidth=0.7, alpha=0.5)
        ax.plot([-0.8, 0], [4 - r, 4 - r], color=C_LINE, linestyle=":", linewidth=0.7, alpha=0.5)
        ax.plot([8, 8.8], [4 - r, 4 - r], color=C_LINE, linestyle=":", linewidth=0.7, alpha=0.5)

    # Service Line highlight (Row 2 boundary from net, y=6 and y=2 in standard approx, but in grid: y=5, y=3)
    ax.plot([0, 8], [6, 6], color=C_LINE, linestyle="-", linewidth=2.0)
    ax.plot([0, 8], [2, 2], color=C_LINE, linestyle="-", linewidth=2.0)
    # Center service line
    ax.plot([4, 4], [2, 6], color=C_LINE, linestyle="-", linewidth=2.0)

    # Net (Ağ)
    ax.plot([-1.1, 9.1], [4, 4], color=C_NET, linewidth=5.0, solid_capstyle="round")
    ax.plot([-1.1, 9.1], [3.97, 3.97], color="#333333", linewidth=1.5)
    ax.text(-1.3, 4.0, "AĞ / NET", ha="right", va="center", fontsize=10, fontweight="bold", color=C_NET)

    # Label Top Zones (1 to 32)
    # Note in tenis_atis_sistemi:
    # col = (n-1)%8, row = (n-1)//8
    # y = 4 + row + 0.5 (row 0 is closest to net)
    for n in range(1, 33):
        col = (n - 1) % 8
        row = (n - 1) // 8
        cx = col + 0.5
        cy = 4 + row + 0.5
        ax.text(cx, cy, str(n), ha="center", va="center", fontsize=11, fontweight="bold", color="#B8E2FF")

    # Label Bottom Zones (1x to 32x)
    # row 0 is closest to net: y = 4 - row - 0.5
    for n in range(1, 33):
        col = (n - 1) % 8
        row = (n - 1) // 8
        cx = col + 0.5
        cy = 4 - (row + 0.5)
        ax.text(cx, cy, f"{n}x", ha="center", va="center", fontsize=11, fontweight="bold", color=C_ACCENT_YELLOW)

    # Label Alley Zones
    for i in range(1, 5):
        # Top: LT1..4, RT1..4
        # LT4 is closest to net, LT1 is farthest (satir A.N_SATIR - k)
        y_top = 4 + (4 - i) + 0.5
        ax.text(-0.4, y_top, f"LT{i}", ha="center", va="center", fontsize=8, color="#A5D6A7")
        ax.text(8.4, y_top, f"RT{i}", ha="center", va="center", fontsize=8, color="#A5D6A7")
        # Bottom: LB1..4, RB1..4
        # LB1 is closest to net: row k - 1
        y_bot = 4 - (i - 1) - 0.5
        ax.text(-0.4, y_bot, f"LB{i}", ha="center", va="center", fontsize=8, color="#A5D6A7")
        ax.text(8.4, y_bot, f"RB{i}", ha="center", va="center", fontsize=8, color="#A5D6A7")

    # Side indicators & depth indicators
    depths = [("Satır 0: Kısa (Short)", 0.5), ("Satır 1: Orta (Medium)", 1.5),
              ("Satır 2: Derin (Deep)", 2.5), ("Satır 3: Dip Çizgi (Baseline)", 3.5)]

    for d_text, dy in depths:
        # Top side
        ax.text(9.2, 4 + dy, d_text, ha="left", va="center", fontsize=8, color=C_TEXT_DIM)
        # Bottom side
        ax.text(9.2, 4 - dy, d_text, ha="left", va="center", fontsize=8, color=C_TEXT_DIM)

    # Header labels for opponent and striker halves
    ax.text(4.0, 8.0, "▲ RAKİP SAHASI / OPPONENT HALF (Bölgeler 1 – 32) ▲",
            ha="center", va="bottom", fontsize=12, fontweight="bold", color="#7ABADC")
    ax.text(4.0, -0.05, "▼ VURAN SAHASI / STRIKER HALF (Bölgeler 1x – 32x) ▼",
            ha="center", va="top", fontsize=12, fontweight="bold", color="#FFE080")

    # Outer court dimensions notes
    ax.text(4.0, -0.6, "Izgara: 8 Sütun (Tekler Genişliği: 8.23 m) × 4 Satır (Yarı Kort Derinliği: 11.89 m)\n"
                       "Koridorlar: LT/RT (Üst) ve LB/RB (Alt) Çiftler Koridoru (Doubles Alleys)",
            ha="center", va="center", fontsize=9, color=C_TEXT_DIM)

    plt.tight_layout()
    fig.savefig(docs_img / "saha_bolgeleri_grid.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("[OK] saha_bolgeleri_grid.png olusturuldu.")

# ==============================================================================
# 2. KANONİK DÖNÜŞÜM VE 18 HEDEF HÜCRE ŞEMASI (Canonical Transformation)
# ==============================================================================
def draw_canonical_transform():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 9), dpi=300)
    for ax in (ax1, ax2):
        ax.set_aspect("equal")
        ax.axis("off")

    # Title
    fig.suptitle("KANONİK DÖNÜŞÜM & HEDEF ALAN MİMARİSİ\nCanonical Transformation: 51 Chaotic Classes → 18 Clean Tactical Cells",
                 fontsize=16, fontweight="bold", color=C_TEXT_LIGHT, y=0.98)

    # AX1: Traditional 51-class chaos
    ax1.set_xlim(-1, 9)
    ax1.set_ylim(-1, 9)
    ax1.text(4.0, 8.5, "Klasik Yaklaşım (51 Sınıf)\nTarget Spans Entire Court & Corridors",
             ha="center", va="center", fontsize=12, fontweight="bold", color="#FF7043")

    # Full court background
    ax1.add_patch(patches.Rectangle((0, 0), 8, 8, facecolor="#14283D", edgecolor="#FF5722", linewidth=2))
    ax1.add_patch(patches.Rectangle((-0.8, 0), 0.8, 8, facecolor="#1E3A2F", edgecolor="#FF5722", linewidth=1))
    ax1.add_patch(patches.Rectangle((8, 0), 0.8, 8, facecolor="#1E3A2F", edgecolor="#FF5722", linewidth=1))
    ax1.plot([-1, 9], [4, 4], color=C_NET, linewidth=3)

    # Scatter of chaotic target distributions across both sides
    np.random.seed(42)
    x_chaos = np.random.uniform(0.2, 7.8, 120)
    y_chaos = np.random.uniform(0.2, 7.8, 120)
    ax1.scatter(x_chaos, y_chaos, color="#FF8A65", alpha=0.6, s=30)
    ax1.text(4.0, 2.0, "Top hangi yarıya gidecek?\n(Model boş yere yarı öğrenmeye çalışır)\nModel wastes capacity guessing half",
             ha="center", va="center", fontsize=10, color="#FFCCBC",
             bbox=dict(boxstyle="round,pad=0.5", facecolor="#3E2723", edgecolor="#FF7043", alpha=0.9))
    ax1.text(4.0, -0.6, "• 51 ayrık sınıf (çoğu 1-3 örnekli gürültü)\n• Simetri yok, veri ikiye bölünür\n• Top-1 doğruluk tavanı çok düşük kalır",
             ha="center", va="center", fontsize=9, color=C_TEXT_DIM)

    # AX2: Canonical 18-cell + 9-coarse class mapping
    ax2.set_xlim(-1, 9)
    ax2.set_ylim(-1, 9)
    ax2.text(4.0, 8.5, "Kanonik Dönüşümlü Sistem (18 Hücre & 9 Kaba Bölge)\nStriker-Centric Invariance: 99.8% Density in 18 Cells",
             ha="center", va="center", fontsize=12, fontweight="bold", color=C_ACCENT_GREEN)

    # Canonical half: 3 target rows x 6 columns (Columns 1 to 6)
    ax2.add_patch(patches.Rectangle((0, 0), 8, 4, facecolor="#0B1A28", edgecolor="#37474F", linewidth=1.5, linestyle="--"))
    ax2.text(4.0, 2.0, "Vuran Oyuncu (Her Zaman Alt Yarıda Görünür)\nStriker Always Oriented at Bottom (X)",
             ha="center", va="center", fontsize=10, color=C_ACCENT_YELLOW)

    # Net
    ax2.plot([-0.5, 8.5], [4, 4], color=C_NET, linewidth=4)
    ax2.text(-0.7, 4.0, "AĞ", ha="right", va="center", fontsize=10, fontweight="bold", color=C_NET)

    # Target Half (Opposite Side)
    # The 18 canonical cells are Rows 0, 1, 2 and Columns 1, 2, 3, 4, 5, 6
    # In y: y = 4 + row (row 0: 4-5, row 1: 5-6, row 2: 6-7)
    # 9 coarse regions colors:
    # Sol (cols 1, 2), Orta (cols 3, 4), Sag (cols 5, 6)
    coarse_colors = {
        ("Kısa", "Sol"): "#1565C0", ("Kısa", "Orta"): "#0D47A1", ("Kısa", "Sağ"): "#1976D2",
        ("Orta", "Sol"): "#00838F", ("Orta", "Orta"): "#006064", ("Orta", "Sağ"): "#0097A7",
        ("Derin", "Sol"): "#2E7D32", ("Derin", "Orta"): "#1B5E20", ("Derin", "Sağ"): "#388E3C",
    }

    row_names = ["Kısa (Short)", "Orta (Medium)", "Derin (Deep)"]
    dir_names = ["Sol (Left)", "Orta (Center)", "Sağ (Right)"]

    for r_idx in range(3):
        for c_idx in range(1, 7):
            d_idx = (c_idx - 1) // 2  # 0: Sol, 1: Orta, 2: Sag
            c_name = coarse_colors[(["Kısa", "Orta", "Derin"][r_idx], ["Sol", "Orta", "Sağ"][d_idx])]
            rect = patches.Rectangle((c_idx, 4 + r_idx), 1, 1, facecolor=c_name, edgecolor=C_LINE, linewidth=1.5)
            ax2.add_patch(rect)
            # Label
            ax2.text(c_idx + 0.5, 4 + r_idx + 0.5, f"R{r_idx}-C{c_idx}", ha="center", va="center",
                     fontsize=9, fontweight="bold", color="#FFFFFF")

    # Coarse Region Grouping brackets / annotations
    ax2.text(2.0, 7.3, "SOL (Left)\nSütun 1–2", ha="center", va="center", fontsize=9, fontweight="bold", color=C_ACCENT_CYAN)
    ax2.text(4.0, 7.3, "ORTA (Center)\nSütun 3–4", ha="center", va="center", fontsize=9, fontweight="bold", color=C_ACCENT_CYAN)
    ax2.text(6.0, 7.3, "SAĞ (Right)\nSütun 5–6", ha="center", va="center", fontsize=9, fontweight="bold", color=C_ACCENT_CYAN)

    for r_idx, r_name in enumerate(row_names):
        ax2.text(7.3, 4 + r_idx + 0.5, r_name, ha="left", va="center", fontsize=9, fontweight="bold", color=C_ACCENT_GREEN)

    ax2.text(4.0, -0.6, "• 18 Kanonik Hücre: Vuruşların %99.8'i bu alana düşer\n• 9 Kaba Hedef (3 Derinlik × 3 Yön): Antrenörler için taktik özet\n• Üst yarıdan vuranlar 180° döndürülür → Çift yönlü veri verimi",
             ha="center", va="center", fontsize=9, color=C_TEXT_DIM)

    plt.tight_layout()
    fig.savefig(docs_img / "kanonik_donusum_semasi.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("[OK] kanonik_donusum_semasi.png olusturuldu.")
    return
# ==============================================================================
# 3. AKILLI TOP ATMA MAKİNESİ MİMARİSİ (4 Inputs -> 5 Models -> 4 Outputs)
# ==============================================================================
def draw_architecture():
    fig, ax = plt.subplots(figsize=(15, 8.5), dpi=300)
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 9)
    ax.axis("off")

    # Header
    ax.text(7.5, 8.5, "AKILLI ATIŞ SİSTEMİ MİMARİSİ (TOP ATMA MAKİNESİ)",
            ha="center", va="center", fontsize=18, fontweight="bold", color=C_TEXT_LIGHT)
    ax.text(7.5, 8.1, "4 Input Parameters  →  5 Ensembled ML Models  →  4 Tactical Recommendations",
            ha="center", va="center", fontsize=11, color=C_TEXT_DIM)

    # Box styling helper
    def draw_card(x, y, w, h, bg, border, title, items, title_col="#FFFFFF"):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2",
                                      facecolor=bg, edgecolor=border, linewidth=2)
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h - 0.4, title, ha="center", va="center",
                fontsize=11, fontweight="bold", color=title_col)
        ax.plot([x + 0.2, x + w - 0.2], [y + h - 0.75, y + h - 0.75], color=border, linewidth=1)
        for idx, item in enumerate(items):
            ax.text(x + 0.3, y + h - 1.15 - (idx * 0.45), f"• {item}", ha="left", va="center",
                    fontsize=9.5, color=C_TEXT_LIGHT)

    # 1. Inputs (Left)
    inputs = [
        "Cinsiyet: Erkekler / Kadınlar",
        "Kategori: Orta (Middle) / Düşük (Low)",
        "Vuran Konumu (P): 1x–32x / Dışarı",
        "Rakip Konumu (R): 1–32 / Dışarı",
        "─── Vuruş Stili Gerekmez ───"
    ]
    draw_card(0.5, 1.8, 3.8, 5.4, "#0D2538", C_ACCENT_CYAN, "GİRDİLER (INPUTS)", inputs, C_ACCENT_CYAN)

    # 2. Precomputation Engine & Feature Engine (Middle Left)
    engine_items = [
        "15 Kanonik Geometrik Özellik",
        "Yan Fark & Doğrultu Açısı",
        "Merkezden Sapma Mesafeleri",
        "4,356 Senaryo Önceden Hesaplanır",
        "cikti/onhesap.json (2.7 MB)",
        "Gömülü Sistem / CPU Uyumlu"
    ]
    draw_card(4.7, 1.8, 3.2, 5.4, "#132D42", "#80D8FF", "ÖN HESAP & ÖZNİTELİK", engine_items, "#80D8FF")

    # 3. Models (Middle Right)
    models = [
        "XGBoost (Düşme Bölgesi & Kademe En İyisi)",
        "LightGBM (Spin & Yükseklik En İyisi)",
        "Random Forest (300 Ağaç)",
        "MLP (128x64 Çok Katmanlı Algılayıcı)",
        "Çok Terimli Lojistik Regresyon",
        "Taban Çizgisi: Koşullu Frekans Tablosu"
    ]
    draw_card(8.3, 1.8, 3.4, 5.4, "#1A233A", C_ACCENT_YELLOW, "5 MAKİNE ÖĞRENMESİ", models, C_ACCENT_YELLOW)

    # 4. Outputs (Right)
    outputs = [
        "Düşme Bölgesi: 18 Hücre (Top-1: %19.6)",
        "Spin Türü: Topspin / Kesik / Düz (%87.9)",
        "Top Yüksekliği: Alçak / Orta / Yüksek (%76.7)",
        "Kademe / Zorluk: Kolay / Nötr / Zor (%91.3)",
        "Kaba Hedef (9 Sınıf): %32.8",
        "Ortalama Mesafe Sapması: ~2.24 metre"
    ]
    draw_card(12.1, 1.8, 2.7, 5.4, "#0E3320", C_ACCENT_GREEN, "ÇIKTILAR (OUTPUTS)", outputs, C_ACCENT_GREEN)

    # Connecting arrows
    arrow_props = dict(arrowstyle="-|>", color="#90CAF9", linewidth=2.5, mutation_scale=18)
    ax.annotate("", xy=(4.7, 4.5), xytext=(4.3, 4.5), arrowprops=arrow_props)
    ax.annotate("", xy=(8.3, 4.5), xytext=(7.9, 4.5), arrowprops=arrow_props)
    ax.annotate("", xy=(12.1, 4.5), xytext=(11.7, 4.5), arrowprops=arrow_props)

    # Bottom footer stats banner
    banner = patches.FancyBboxPatch((0.5, 0.5), 14.3, 0.9, boxstyle="round,pad=0.15",
                                    facecolor="#102030", edgecolor="#29B6F6", linewidth=1.5)
    ax.add_patch(banner)
    ax.text(7.5, 0.95, "Akademik Doğrulama: 19 Maç, 11,724 Atış, Maç Bazlı 5-Kat GroupKFold CV, 2,000 Bootstrap 95% GA, Wilcoxon & Holm Testleri",
            ha="center", va="center", fontsize=9.5, fontweight="bold", color=C_TEXT_LIGHT)

    plt.tight_layout()
    fig.savefig(docs_img / "atis_modeli_mimarisi.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("[OK] atis_modeli_mimarisi.png olusturuldu.")

# ==============================================================================
# 4. SAHA ÜZERİNDE ÖRNEK ATIŞ SENARYOSU (Sample Shot Tactical Trajectory Diagram)
# ==============================================================================
def draw_sample_shot():
    fig, ax = plt.subplots(figsize=(10, 13), dpi=300)
    ax.set_xlim(-1, 9)
    ax.set_ylim(-0.8, 8.8)
    ax.set_aspect("equal")
    ax.axis("off")

    # Titles
    ax.text(4.0, 8.5, "ÖRNEK ATIŞ TAHMİNİ SENARYOSU", ha="center", va="center",
            fontsize=17, fontweight="bold", color=C_TEXT_LIGHT)
    ax.text(4.0, 8.15, "Örnek Senaryo: Kadınlar · Low · Vuran: 27x · Rakip: 29",
            ha="center", va="center", fontsize=11, color=C_TEXT_DIM)

    # Court background
    ax.add_patch(patches.Rectangle((0, 4), 8, 4, facecolor="#144C78", edgecolor=C_LINE, linewidth=2))
    ax.add_patch(patches.Rectangle((0, 0), 8, 4, facecolor="#0F3D60", edgecolor=C_LINE, linewidth=2))
    # Alleys
    ax.add_patch(patches.Rectangle((-0.8, 0), 0.8, 8, facecolor="#165B32", edgecolor=C_LINE, linewidth=1.5))
    ax.add_patch(patches.Rectangle((8, 0), 0.8, 8, facecolor="#165B32", edgecolor=C_LINE, linewidth=1.5))

    # Grid
    for c in range(1, 8):
        ax.plot([c, c], [0, 8], color=C_LINE, linestyle="--", linewidth=0.6, alpha=0.5)
    for r in range(1, 4):
        ax.plot([0, 8], [4 + r, 4 + r], color=C_LINE, linestyle="--", linewidth=0.6, alpha=0.5)
        ax.plot([0, 8], [4 - r, 4 - r], color=C_LINE, linestyle="--", linewidth=0.6, alpha=0.5)

    # Net
    ax.plot([-1, 9], [4, 4], color=C_NET, linewidth=4.5)
    ax.text(-1.1, 4.0, "AĞ", ha="right", va="center", fontsize=9, fontweight="bold", color=C_NET)

    # Vuran P: 27x -> (n=27, col=(27-1)%8 = 2, row=(27-1)//8 = 3 (dip cizgi)).
    # cx = 2.5, cy = 4 - 3.5 = 0.5
    px, py = 2.5, 0.5
    # Rakip R: 29 -> (n=29, col=(29-1)%8 = 4, row=(29-1)//8 = 3).
    # cx = 4.5, cy = 4 + 3.5 = 7.5
    rx, ry = 4.5, 7.5

    # Top-5 Predicted Landing Zones (Sample real model predictions for Kadınlar Low 27x 29)
    # Zone 29 (row 3, col 4: cy=7.5, cx=4.5), Zone 28 (row 3, col 3: cy=7.5, cx=3.5),
    # Zone 21 (row 2, col 4: cy=6.5, cx=4.5), Zone 20 (row 2, col 3: cy=6.5, cx=3.5),
    # Zone 13 (row 1, col 4: cy=5.5, cx=4.5)
    preds = [
        {"zone": "28", "cx": 3.5, "cy": 7.5, "prob": 26.4, "col": "#FF1744", "rank": "1. Tercih"},
        {"zone": "27", "cx": 2.5, "cy": 7.5, "prob": 18.2, "col": "#FF9100", "rank": "2. Tercih"},
        {"zone": "20", "cx": 3.5, "cy": 6.5, "prob": 14.7, "col": "#FFEA00", "rank": "3. Tercih"},
        {"zone": "29", "cx": 4.5, "cy": 7.5, "prob": 11.5, "col": "#76FF03", "rank": "4. Tercih"},
        {"zone": "21", "cx": 4.5, "cy": 6.5, "prob": 8.3, "col": "#00E5FF", "rank": "5. Tercih"}
    ]

    # Draw Predictions landing heat rectangles and trajectories
    for p in reversed(preds):
        # Target cell rectangle highlight
        rect = patches.Rectangle((p["cx"] - 0.5, p["cy"] - 0.5), 1, 1,
                                 facecolor=p["col"], alpha=0.45, edgecolor=p["col"], linewidth=2.5)
        ax.add_patch(rect)
        # Shot path arc
        ax.annotate("", xy=(p["cx"], p["cy"]), xytext=(px, py),
                    arrowprops=dict(arrowstyle="->", color=p["col"], linewidth=2.2,
                                    linestyle="--", connectionstyle="arc3,rad=-0.12"))
        # Text in cell
        ax.text(p["cx"], p["cy"] + 0.15, f"Bölge {p['zone']}", ha="center", va="center",
                fontsize=9.5, fontweight="bold", color="#FFFFFF")
        ax.text(p["cx"], p["cy"] - 0.2, f"%{p['prob']:.1f}", ha="center", va="center",
                fontsize=9, fontweight="bold", color="#FFFFFF")

    # Striker Marker P
    ax.plot(px, py, "o", markersize=26, color="#00E5FF", markeredgecolor="#FFFFFF", markeredgewidth=3)
    ax.text(px, py, "P", ha="center", va="center", fontsize=12, fontweight="bold", color="#001830")
    ax.text(px, py - 0.5, "Vuran (P): 27x", ha="center", va="top", fontsize=10, fontweight="bold", color="#00E5FF")

    # Opponent Marker R
    ax.plot(rx, ry, "o", markersize=26, color="#FF9100", markeredgecolor="#FFFFFF", markeredgewidth=3)
    ax.text(rx, ry, "R", ha="center", va="center", fontsize=12, fontweight="bold", color="#001830")
    ax.text(rx, ry + 0.5, "Rakip (R): 29", ha="center", va="bottom", fontsize=10, fontweight="bold", color="#FF9100")

    # Tactical output card at bottom
    info_card = patches.FancyBboxPatch((-0.8, -0.65), 9.6, 0.75, boxstyle="round,pad=0.15",
                                       facecolor="#0B1A28", edgecolor=C_ACCENT_GREEN, linewidth=1.5)
    ax.add_patch(info_card)
    ax.text(4.0, -0.28, "🤖 YZ Önerileri: Düşme Bölgesi: Bölge 28 (%26.4)  |  Spin: Kesik (Slice)  |  Yükseklik: Alçak  |  Kademe: Zor",
            ha="center", va="center", fontsize=9.5, fontweight="bold", color=C_ACCENT_GREEN)

    plt.tight_layout()
    fig.savefig(docs_img / "saha_ornek_tahmin.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("[OK] saha_ornek_tahmin.png olusturuldu.")

if __name__ == "__main__":
    draw_court_grid()
    draw_canonical_transform()
    draw_architecture()
    draw_sample_shot()
