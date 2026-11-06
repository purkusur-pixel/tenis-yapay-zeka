"""
TENİS AKILLI ATIŞ SİSTEMİ — TOP ATMA MAKİNESİ ARAYÜZÜ
=====================================================
Seçilen 4 girdi:   cinsiyet, kategori (Orta / Low), vuran konumu (P), rakip konumu (R)
ML'in önerdiği 4 çıktı: düşme bölgesi, spin, top yüksekliği, kademe

Model EĞİTİLMEZ; 04_atis_modeli_egit.py'nin bir kez ürettiği cikti/onhesap.json okunur.

Kullanım:
    python gui_atis.py                          # fare ile seç
    python gui_atis.py Kadınlar Low 27x 29      # açılışta bu seçimlerle başla
    (açıkken terminale komut yazın — örn.  erkek orta 20x 28  — arayüz aynı seçimi yapar;
     komut listesi için:  yardim)
"""
from __future__ import annotations

import argparse
import queue
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from gui import (CH, CW, PCOL, App as _EskiApp, _BG_CARD, _BG_CARD2, _BG_MAIN, _BG_PANEL,
                 _ACC_GRN, _ACC_YEL, _PAD_B, _PAD_T, _TXT_BLU, _TXT_CYN, _TXT_MUT, _TXT_ORG,
                 _TXT_WHT, _zone_poly, click2zone)
from tenis import onhesap as O

_YESIL = '#44EE88'
_SPIN_RENK = {"Topspin": '#FF8844', "Kesik": '#44AAFF', "Düz": '#DDDDDD'}
_UC_RENK = ['#55CC00', '#FFDD00', '#FF5533']


class AtisApp:
    # Saha çizimi ve ttk stili eski arayüzden AYNEN kullanılır (kod tekrarı yok).
    _draw_court = _EskiApp._draw_court
    _setup_ttk = _EskiApp._setup_ttk

    def __init__(self, root: tk.Tk, tablo: O.OnHesap):
        self.root, self.tablo = root, tablo
        self.vuran = self.rakip = None
        self.son_sonuc = None
        self._toplu = False

        root.title("🎾  Tenis Akıllı Atış Sistemi — Top Atma Makinesi")
        root.configure(bg=_BG_MAIN)
        root.resizable(False, False)
        self._setup_ttk()
        self._sol_panel()
        self._kort()
        self._sag_panel()
        self._draw_court()
        self._guncelle()

    # ═════════════════════════════════════════════════════════════════════
    #  ARAYÜZ
    # ═════════════════════════════════════════════════════════════════════
    def _baslik(self, p, t, fg=_TXT_BLU):
        tk.Label(p, text=t, font=('Helvetica', 9, 'bold'), bg=_BG_PANEL, fg=fg
                 ).pack(anchor=tk.W, padx=10, pady=(8, 2))

    def _ayrac(self, p):
        tk.Frame(p, bg='#1E3040', height=1).pack(fill=tk.X, padx=6, pady=6)

    def _radyo(self, p, var, secenekler):
        f = tk.Frame(p, bg=_BG_PANEL)
        f.pack(fill=tk.X, padx=10)
        for deger, yazi in secenekler:
            tk.Radiobutton(f, text=yazi, variable=var, value=deger, bg=_BG_PANEL, fg=_TXT_WHT,
                           selectcolor=_BG_CARD, activebackground=_BG_PANEL,
                           font=('Helvetica', 10)).pack(side=tk.LEFT, padx=4)

    def _sol_panel(self):
        lp = tk.Frame(self.root, bg=_BG_PANEL, width=250)
        lp.pack(side=tk.LEFT, fill=tk.Y, padx=(8, 0), pady=8)
        lp.pack_propagate(False)

        tk.Label(lp, text="🎾  Akıllı Atış Sistemi", font=('Helvetica', 13, 'bold'),
                 bg=_BG_PANEL, fg=_ACC_GRN).pack(pady=(12, 0))
        tk.Label(lp, text="4 girdi seç  →  ML 4 çıktı önerir", font=('Helvetica', 8),
                 bg=_BG_PANEL, fg=_TXT_MUT).pack()
        self._ayrac(lp)

        self._baslik(lp, "🧠  Model")
        self.v_model = tk.StringVar(value=O.OTOMATIK)
        ttk.Combobox(lp, textvariable=self.v_model, state='readonly', width=27,
                     values=[O.OTOMATIK] + self.tablo.modeller).pack(padx=10)

        self._baslik(lp, "⚥  Cinsiyet")
        self.v_cin = tk.StringVar(value=O.CINSIYETLER[0])
        self._radyo(lp, self.v_cin, [(c, c) for c in O.CINSIYETLER])

        self._baslik(lp, "🏆  Kategori")
        self.v_kat = tk.StringVar(value=O.KATEGORILER[0])
        self._radyo(lp, self.v_kat, [(k, O.KATEGORI_GORUNEN[k]) for k in O.KATEGORILER])
        self._ayrac(lp)

        self._baslik(lp, "📍  Konumlar")
        kf = tk.Frame(lp, bg=_BG_CARD)
        kf.pack(fill=tk.X, padx=8, pady=2)
        for i, (yazi, renk) in enumerate([("Vuran  P:", _TXT_CYN), ("Rakip  R:", _TXT_ORG)]):
            tk.Label(kf, text=yazi, bg=_BG_CARD, fg=renk, font=('Helvetica', 9), width=9,
                     anchor=tk.W).grid(row=i, column=0, padx=8, pady=4, sticky=tk.W)
        self.lbl_p = tk.Label(kf, text="—", font=('Courier', 12, 'bold'), bg='#001A33',
                              fg='#44CCFF', width=9, relief=tk.GROOVE, bd=1)
        self.lbl_p.grid(row=0, column=1, pady=4)
        self.lbl_r = tk.Label(kf, text="—", font=('Courier', 12, 'bold'), bg='#1A0E00',
                              fg='#FFBB55', width=9, relief=tk.GROOVE, bd=1)
        self.lbl_r.grid(row=1, column=1, pady=4)

        bf = tk.Frame(lp, bg=_BG_PANEL)
        bf.pack(fill=tk.X, padx=8, pady=(4, 0))
        for yazi, komut in [("P kort dışı", lambda: self.uygula({"vuran": O.DISARI})),
                            ("R kort dışı", lambda: self.uygula({"rakip": O.DISARI}))]:
            tk.Button(bf, text=yazi, font=('Helvetica', 8), bg=_BG_CARD2, fg='#88BBDD',
                      activebackground='#223355', relief=tk.FLAT, cursor='hand2',
                      command=komut).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(lp, text="🗑  TEMİZLE", font=('Helvetica', 9), bg='#2A0A00', fg='#FFAAAA',
                  activebackground='#400A00', relief=tk.FLAT, cursor='hand2', pady=5,
                  command=self.temizle).pack(fill=tk.X, padx=10, pady=(6, 0))
        self._ayrac(lp)

        self.lbl_adim = tk.Label(lp, text="", wraplength=228, justify=tk.LEFT,
                                 font=('Helvetica', 9, 'bold'), bg=_BG_PANEL, fg=_ACC_YEL)
        self.lbl_adim.pack(padx=10, anchor=tk.W)
        tk.Label(lp, text="Fare: ALT yarıya tıkla → vuran (P)\n"
                          "         ÜST yarıya tıkla → rakip (R)\n"
                          "Kortun altına / üstüne tıkla → kort dışı\n\n"
                          "Konsol: terminale komut yaz, örn.\n"
                          "   kadin low 27x 29\n"
                          "   rakip=31   model=mlp   yardim",
                 justify=tk.LEFT, font=('Helvetica', 8), bg=_BG_PANEL, fg=_TXT_MUT
                 ).pack(padx=10, pady=(10, 0), anchor=tk.W)

        for v in (self.v_model, self.v_cin, self.v_kat):
            v.trace_add('write', lambda *_: None if self._toplu else self._guncelle(kaynak="fare"))

    def _kort(self):
        f = tk.Frame(self.root, bg=_BG_MAIN)
        f.pack(side=tk.LEFT, padx=6, pady=8)
        tk.Label(f, text="Rakip sahası (1–32)  ▲   |   ▼  Vuran sahası (1x–32x)",
                 font=('Helvetica', 9, 'bold'), bg=_BG_MAIN, fg=_TXT_BLU).pack(pady=(0, 3))
        self.cv = tk.Canvas(f, width=CW, height=CH, bg='#0A1E30', highlightthickness=2,
                            highlightbackground='#2A6AAA', cursor='hand2')
        self.cv.pack()
        self.cv.bind('<Button-1>', self._tikla)
        self.lbl_ipucu = tk.Label(f, text="", font=('Helvetica', 9, 'italic'), bg=_BG_MAIN,
                                  fg='#7A90A0')
        self.lbl_ipucu.pack()

    def _sag_panel(self):
        rp = tk.Frame(self.root, bg=_BG_PANEL, width=300)
        rp.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8), pady=8)
        rp.pack_propagate(False)

        tk.Label(rp, text="🎯  Önerilen Atış", font=('Helvetica', 12, 'bold'), bg=_BG_PANEL,
                 fg=_YESIL).pack(pady=(12, 4))
        kart = tk.Frame(rp, bg=_BG_CARD, bd=1, relief=tk.GROOVE)
        kart.pack(fill=tk.X, padx=10)
        self.lbl_oneri_bolge = tk.Label(kart, text="—", font=('Courier', 22, 'bold'),
                                        bg=_BG_CARD, fg=PCOL[0])
        self.lbl_oneri_bolge.pack(pady=(6, 0))
        self.lbl_oneri_alt = tk.Label(kart, text="", font=('Helvetica', 10, 'bold'),
                                      bg=_BG_CARD, fg=_TXT_WHT, justify=tk.CENTER)
        self.lbl_oneri_alt.pack(pady=(0, 8))

        self._baslik(rp, "📋  Düşme bölgesi — ilk 5", fg='#AAAAFF')
        self.f_bolge = tk.Frame(rp, bg=_BG_PANEL)
        self.f_bolge.pack(fill=tk.X, padx=8)
        self.f_dag = {}
        for h, baslik in [("spin", "🔄  Spin"), ("yukseklik", "↕  Top yüksekliği"),
                          ("kademe", "📊  Kademe (zorluk)")]:
            self._baslik(rp, baslik, fg='#AAAAFF')
            self.f_dag[h] = tk.Frame(rp, bg=_BG_PANEL)
            self.f_dag[h].pack(fill=tk.X, padx=8)
        self.lbl_model = tk.Label(rp, text="", font=('Helvetica', 8), bg=_BG_PANEL, fg='#6A8090',
                                  justify=tk.LEFT, wraplength=280)
        self.lbl_model.pack(padx=10, pady=(10, 4), anchor=tk.W)

    # ═════════════════════════════════════════════════════════════════════
    #  SEÇİM
    # ═════════════════════════════════════════════════════════════════════
    def secim(self) -> dict:
        return {"cinsiyet": self.v_cin.get(), "kategori": self.v_kat.get(),
                "vuran": self.vuran, "rakip": self.rakip, "model": self.v_model.get()}

    def uygula(self, degisim: dict, kaynak: str = "fare"):
        """Fare ve konsol AYNI yoldan geçer → arayüzde aynı seçim oluşur."""
        self._toplu = True
        try:
            if "cinsiyet" in degisim: self.v_cin.set(degisim["cinsiyet"])
            if "kategori" in degisim: self.v_kat.set(degisim["kategori"])
            if "model" in degisim: self.v_model.set(degisim["model"])
            if "vuran" in degisim: self.vuran = degisim["vuran"]
            if "rakip" in degisim: self.rakip = degisim["rakip"]
        finally:
            self._toplu = False
        return self._guncelle(kaynak)

    def temizle(self, kaynak: str = "fare"):
        self.vuran = self.rakip = None
        self._guncelle(kaynak)

    def _tikla(self, e):
        # Kortun altı / üstü → kort dışı (click2zone bu noktaları en yakın bölgeye yuvarlar)
        if e.y > CH - _PAD_B:
            self.uygula({"vuran": O.DISARI})
            return
        if e.y < _PAD_T:
            self.uygula({"rakip": O.DISARI})
            return
        z = click2zone(e.x, e.y)
        if z is None:
            return
        if z[:2] in ("LT", "RT", "LB", "RB"):
            self.lbl_ipucu.config(text=f"{z}: koridor bölgeleri veride yok — iç bölge seçin",
                                  fg=_TXT_ORG)
            return
        self.uygula({"vuran": z} if z.upper().endswith("X") else {"rakip": z})

    # ═════════════════════════════════════════════════════════════════════
    #  TAHMİN + ÇİZİM
    # ═════════════════════════════════════════════════════════════════════
    def _guncelle(self, kaynak: str = "fare"):
        s = self.secim()
        self.lbl_p.config(text=s["vuran"] or "—")
        self.lbl_r.config(text=s["rakip"] or "—")
        self.cv.delete("overlay")
        if s["vuran"] is None or s["rakip"] is None:
            eksik = "vuran (P) konumunu — ALT yarı" if s["vuran"] is None else \
                    "rakip (R) konumunu — ÜST yarı"
            self.lbl_adim.config(text=f"📍 Şimdi {eksik} seçin", fg=_ACC_YEL)
            self.lbl_ipucu.config(text="", fg='#7A90A0')
            self._ciz_konumlar()
            self._sonuclari_temizle()
            self.son_sonuc = None
            return None
        sonuc = self.tablo.sorgula(s["cinsiyet"], s["kategori"], s["vuran"], s["rakip"], s["model"])
        self.son_sonuc = sonuc
        self.lbl_adim.config(text="✅ Öneri hazır — istediğin girdiyi değiştir", fg=_YESIL)
        self.lbl_ipucu.config(text=f"Kaynak: {kaynak}", fg='#7A90A0')
        self._ciz_tahmin(sonuc["bolge"]["liste"][:5])
        self._sonuclari_yaz(sonuc)
        if kaynak == "fare" and KONSOL_ACIK:
            print("\n[fare] " + O.metin_ozeti(s, sonuc).replace("\n", "\n       "))
            print("komut> ", end="", flush=True)
        return sonuc

    @staticmethod
    def _merkez(z, rol):
        if z == O.DISARI:
            return (CW / 2, CH - 14) if rol == "vuran" else (CW / 2, 14)
        pts = _zone_poly(z)
        return (sum(p[0] for p in pts) / 4, sum(p[1] for p in pts) / 4)

    def _isaret(self, z, rol):
        if z is None:
            return
        dolgu, cerceve, harf = (('#1166DD', '#44AAFF', 'P') if rol == "vuran"
                                else ('#CC7700', '#FFAA33', 'R'))
        if z != O.DISARI:
            pts = _zone_poly(z)
            self.cv.create_polygon([v for p in pts for v in p], outline=cerceve, fill='#002255',
                                   width=3, stipple='gray50', tags="overlay")
        x, y = self._merkez(z, rol)
        self.cv.create_oval(x - 12, y - 12, x + 12, y + 12, fill=dolgu, outline='white',
                            width=3, tags="overlay")
        self.cv.create_text(x, y, text=harf, fill='white', font=('Helvetica', 10, 'bold'),
                            tags="overlay")

    def _ciz_konumlar(self):
        self._isaret(self.vuran, "vuran")
        self._isaret(self.rakip, "rakip")

    def _ciz_tahmin(self, ilk5):
        self._ciz_konumlar()
        px, py = self._merkez(self.vuran, "vuran")
        for i in reversed(range(len(ilk5))):          # en olası en üstte kalsın
            o, renk = ilk5[i], PCOL[i]
            pts = _zone_poly(o["bolge"])
            flat = [v for p in pts for v in p]
            tx, ty = sum(p[0] for p in pts) / 4, sum(p[1] for p in pts) / 4
            self.cv.create_polygon(flat, fill=renk, outline='', stipple='gray50', tags="overlay")
            self.cv.create_polygon(flat, fill='', outline=renk, width=4 if i == 0 else 2,
                                   tags="overlay")
            self.cv.create_line(px, py, tx, ty, fill=renk, width=4 if i == 0 else 2,
                                arrow=tk.LAST, arrowshape=(16, 20, 7) if i == 0 else (10, 13, 5),
                                dash=() if i == 0 else (8, 4), tags="overlay")
            self.cv.create_rectangle(tx - 31, ty - 14, tx + 31, ty + 14, fill='#0D1520',
                                     outline=renk, width=2, tags="overlay")
            self.cv.create_text(tx, ty - 6, text=f"#{i+1}  {o['bolge']}", fill=renk,
                                font=('Helvetica', 9, 'bold'), tags="overlay")
            self.cv.create_text(tx, ty + 7, text=f"%{100*o['olasilik']:.1f}", fill='white',
                                font=('Helvetica', 9, 'bold'), tags="overlay")
        self._isaret(self.vuran, "vuran")
        self._isaret(self.rakip, "rakip")

    def _cubuk(self, ebeveyn, sol, yazi, oran, renk, sol_genislik=7, olcek=1.0):
        fr = tk.Frame(ebeveyn, bg='#0D1520')
        fr.pack(fill=tk.X, pady=1)
        tk.Label(fr, text=sol, font=('Helvetica', 9, 'bold'), bg=renk if sol.startswith('#')
                 else '#0D1520', fg='#000000' if sol.startswith('#') else renk,
                 width=3 if sol.startswith('#') else sol_genislik, anchor=tk.W
                 ).pack(side=tk.LEFT, padx=(0, 4))
        if yazi:
            tk.Label(fr, text=yazi, font=('Courier', 10, 'bold'), bg='#0D1520', fg=renk,
                     width=9, anchor=tk.W).pack(side=tk.LEFT)
        c = tk.Canvas(fr, width=110, height=14, bg='#0D1520', highlightthickness=0)
        c.create_rectangle(0, 2, max(2, int(110 * oran / olcek)), 12, fill=renk, outline='')
        c.pack(side=tk.LEFT, padx=2)
        tk.Label(fr, text=f"%{100*oran:.1f}", font=('Helvetica', 9, 'bold'), bg='#0D1520',
                 fg='white', width=6).pack(side=tk.LEFT)

    def _sonuclari_temizle(self):
        for f in [self.f_bolge, *self.f_dag.values()]:
            for w in f.winfo_children():
                w.destroy()
        self.lbl_oneri_bolge.config(text="—")
        self.lbl_oneri_alt.config(text="Vuran ve rakip konumunu seçin")
        self.lbl_model.config(text="")

    def _sonuclari_yaz(self, sonuc):
        self._sonuclari_temizle()
        b = sonuc["bolge"]["liste"]
        ilk = {h: sonuc[h]["liste"][0] for h in ("spin", "yukseklik", "kademe")}
        self.lbl_oneri_bolge.config(text=b[0]["bolge"])
        self.lbl_oneri_alt.config(text=(
            f"{b[0]['etiket']}  (%{100*b[0]['olasilik']:.1f})\n"
            f"{ilk['spin']['etiket']}  •  {ilk['yukseklik']['etiket']} yükseklik  •  "
            f"{ilk['kademe']['etiket']}"))
        for i, o in enumerate(b[:5]):
            # çubuklar en olası bölgeye göre ölçeklenir (yüzdeler gerçek değer)
            self._cubuk(self.f_bolge, f"#{i+1}", o["bolge"], o["olasilik"], PCOL[i],
                        olcek=b[0]["olasilik"])
        for h, f in self.f_dag.items():
            for j, o in enumerate(sonuc[h]["liste"]):
                renk = _SPIN_RENK.get(o["etiket"]) if h == "spin" else _UC_RENK[min(j, 2)]
                self._cubuk(f, o["etiket"], "", o["olasilik"], renk)
        satir = []
        for h, ad in [("bolge", "Bölge"), ("spin", "Spin"), ("yukseklik", "Yükseklik"),
                      ("kademe", "Kademe")]:
            m = sonuc[h]["model"]
            t1 = self.tablo.cv[h][m]["Top-1 %"]
            satir.append(f"{ad}: {m}  (CV doğruluk %{t1:.1f})")
        self.lbl_model.config(text="Kullanılan modeller (maç bazlı CV):\n" + "\n".join(satir))


# ═════════════════════════════════════════════════════════════════════════
#  KONSOL — terminale yazılan komutlar arayüzde aynı seçimi yapar
# ═════════════════════════════════════════════════════════════════════════
KONSOL_ACIK = False


def konsol_baglat(root: tk.Tk, app: AtisApp):
    global KONSOL_ACIK
    if sys.stdin is None or not sys.stdin.isatty():
        return
    KONSOL_ACIK = True
    kuyruk: queue.Queue = queue.Queue()
    islendi = threading.Event()

    def oku():
        print("\nKonsol hazır — komut yazın (yardım için: yardim)")
        while True:
            try:
                satir = input("komut> ")
            except (EOFError, KeyboardInterrupt, OSError, RuntimeError):
                kuyruk.put("cikis")
                return
            islendi.clear()
            kuyruk.put(satir)
            islendi.wait()

    def isle():
        try:
            while True:
                satir = kuyruk.get_nowait()
                try:
                    komut_isle(app, satir, root)
                finally:
                    islendi.set()
        except queue.Empty:
            pass
        root.after(100, isle)

    threading.Thread(target=oku, daemon=True).start()
    root.after(100, isle)


def komut_isle(app: AtisApp, satir: str, root: tk.Tk | None = None):
    try:
        komut, degisim = O.komut_coz(satir)
    except ValueError as e:
        print(f"  ⚠ {e}")
        return
    if komut == "yardim":
        print(O.YARDIM)
    elif komut == "cikis":
        if root is not None:
            root.after(0, root.destroy)
    elif komut == "temizle":
        app.temizle(kaynak="konsol")
        print("  Seçimler temizlendi.")
    elif komut == "durum":
        print("  " + ", ".join(f"{k}={v}" for k, v in app.secim().items()))
    elif degisim:
        sonuc = app.uygula(degisim, kaynak="konsol")
        if sonuc:
            print(O.metin_ozeti(app.secim(), sonuc))
        else:
            s = app.secim()
            print(f"  Seçildi: {', '.join(f'{k}={v}' for k, v in degisim.items())}  "
                  f"→ eksik: {'vuran' if s['vuran'] is None else 'rakip'}")


def main():
    ap = argparse.ArgumentParser(description="Tenis akıllı atış arayüzü")
    ap.add_argument("komut", nargs="*", help="Açılış seçimi, örn.: Kadınlar Low 27x 29")
    ap.add_argument("--konsolsuz", action="store_true", help="Terminalden komut okuma")
    a = ap.parse_args()
    try:
        tablo = O.OnHesap()
    except FileNotFoundError as e:
        print(e)
        r = tk.Tk(); r.withdraw()
        messagebox.showerror("Önhesap tablosu yok", str(e))
        return
    root = tk.Tk()
    app = AtisApp(root, tablo)
    if a.komut:
        komut_isle(app, " ".join(a.komut), root)
    if not a.konsolsuz:
        konsol_baglat(root, app)
    root.mainloop()


if __name__ == "__main__":
    main()
