"""
Bölge (zone) geometrisi — projede TEK kaynak.
Eski projede zone_to_norm() dört ayrı dosyaya kopyalanmıştı; artık hepsi burayı kullanır.

Bölge adları:
    "1".."32"   → üst yarı (N),  "1x".."32x" → alt yarı (X)
    numara n:  sütun = (n-1) % 8 (görüntüde soldan sağa), satır = (n-1) // 8 (fileden uzaklık)
    LT1-4 / RT1-4 → üst yarı sol/sağ koridor,  LB1-4 / RB1-4 → alt yarı sol/sağ koridor
    OUTSIDE      → kort dışı (konumu bilinmiyor)

KANONİK ÇERÇEVE:
    Her atış, VURAN OYUNCUNUN ARKASINDAN bakılıyormuş gibi ifade edilir:
      - vuran oyuncu her zaman "alt" yarıda,
      - sütun 0 = vuranın solu, sütun 7 = vuranın sağı,
      - satır 0 = file dibi, satır 3 = dip çizgi.
    Üst yarıdan vuran oyuncu için görüntü 180° döndürülür (sütun → 7 - sütun).
    Böylece "hangi yarıdan vurdu" bilgisi hedefi ikiye bölmez; 51 sınıf yerine 18 sınıf kalır.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from . import ayarlar as A

_BOS = {"", "NAN", "NONE", "OUTSIDE", "OUT"}


@dataclass(frozen=True)
class Bolge:
    yari: str     # "N" (üst) veya "X" (alt)
    satir: int    # 0..3, fileden uzaklık
    sutun: int    # -1 (sol koridor), 0..7, 8 (sağ koridor) — GÖRÜNTÜ çerçevesinde


def coz(ad) -> Optional[Bolge]:
    """Bölge adını çözer. Bilinmiyor / OUTSIDE ise None döner."""
    if ad is None:
        return None
    z = str(ad).strip().upper()
    if z in _BOS:
        return None
    if len(z) == 3 and z[:2] in ("LT", "RT", "LB", "RB") and z[2].isdigit():
        k = int(z[2])
        sutun = -1 if z[0] == "L" else A.N_SUTUN
        if z[1] == "T":                    # üst yarı: LT1 en derin, LT4 fileye en yakın
            return Bolge("N", A.N_SATIR - k, sutun)
        return Bolge("X", k - 1, sutun)    # alt yarı: LB1 fileye en yakın
    alt = z.endswith("X")
    try:
        n = int(z.rstrip("X"))
    except ValueError:
        return None
    if not 1 <= n <= A.N_SUTUN * A.N_SATIR:
        return None
    return Bolge("X" if alt else "N", (n - 1) // A.N_SUTUN, (n - 1) % A.N_SUTUN)


def yari(ad) -> Optional[str]:
    b = coz(ad)
    return b.yari if b else None


def kanonik_sutun(sutun: int, vuran_yari: str) -> int:
    """Görüntü sütununu vuranın bakış açısına çevirir (alt yarıdan vuran için değişmez)."""
    return sutun if vuran_yari == "X" else (A.N_SUTUN - 1) - sutun


def kanonik(ad, vuran_yari: str) -> Optional[tuple[int, int]]:
    """Bir bölgeyi (satır, kanonik_sütun) olarak döndürür."""
    b = coz(ad)
    if b is None:
        return None
    return b.satir, kanonik_sutun(b.sutun, vuran_yari)


def kanonikten_ada(satir: int, k_sutun: int, vuran_yari: str) -> str:
    """Kanonik hedef hücresini, vuranın yarısına göre gerçek bölge adına çevirir."""
    sutun = kanonik_sutun(k_sutun, vuran_yari)       # dönüşüm kendi tersidir
    n = satir * A.N_SUTUN + sutun + 1
    return str(n) if vuran_yari == "X" else f"{n}x"  # hedef karşı yarıda


def merkez_norm(ad) -> tuple[float, float]:
    """GUI ile uyumlu normalize (x, y) merkez koordinatı. Ağ y=0,5'te."""
    S = 0.056
    b = coz(ad)
    if b is None:
        return (0.5, 0.5)
    if b.sutun < 0:
        nx = S / 2
    elif b.sutun >= A.N_SUTUN:
        nx = 1 - S / 2
    else:
        nx = S + (b.sutun + 0.5) * (1 - 2 * S) / A.N_SUTUN
    d = (b.satir + 0.5) * (0.5 / A.N_SATIR)
    ny = 0.5 + d if b.yari == "X" else 0.5 - d
    return (round(nx, 4), round(ny, 4))


def mesafe_metre(a: tuple[int, int], b: tuple[int, int]) -> float:
    """İki kanonik hücre merkezi arasındaki yaklaşık mesafe (metre)."""
    return math.hypot((a[0] - b[0]) * A.SATIR_METRE, (a[1] - b[1]) * A.SUTUN_METRE)


# ── Hedef sınıflar ───────────────────────────────────────────────────────────
HEDEF_HUCRELER = [(r, c) for r in A.HEDEF_SATIRLAR for c in A.HEDEF_SUTUNLAR]
HUCRE_ID = {h: i for i, h in enumerate(HEDEF_HUCRELER)}


def hucre_etiketi(h: tuple[int, int]) -> str:
    return f"{A.DERINLIK_ADLARI[h[0]]}-{h[1]}"


def kaba_etiket(h: tuple[int, int]) -> str:
    """9 sınıflı kaba hedef: derinlik x yön (ör. 'Derin-Sol')."""
    return f"{A.DERINLIK_ADLARI[h[0]]}-{A.YON_GRUBU[h[1]]}"
