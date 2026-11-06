"""
TENİS AKILLI ATIŞ SİSTEMİ — GUI
================================
Saha çizimi ve etkileşim eski GUI'den aynen korunmuştur; yalnızca MODEL KATMANI
değiştirilmiştir. Artık tek bir model dosyası (cikti/model.joblib) ve tek bir
tahmin sınıfı (tenis.tahmin.TenisTahminci) kullanılır.

Önce:   python 02_egit_degerlendir.py      (modeli üretir)
Sonra:  python gui.py
"""

import tkinter as tk
from tkinter import ttk, messagebox
import math
from pathlib import Path

from tenis import ayarlar as A

# ═══════════════════════════════════════════════════════════════════════════════
#  SAHA GEOMETRİSİ  — v6'dan birebir kopyalandı
# ═══════════════════════════════════════════════════════════════════════════════
CW, CH = 640, 700
S = 0.056

_PAD_L = 38;  _PAD_R = 38;  _PAD_T = 30;  _PAD_B = 28

_UL = (_PAD_L + 52,   _PAD_T)
_UR = (CW - _PAD_R - 52, _PAD_T)
_AL = (_PAD_L,          CH - _PAD_B)
_AR = (CW - _PAD_R,     CH - _PAD_B)
_NL = (_PAD_L + 26,    (_PAD_T + CH - _PAD_B) // 2)
_NR = (CW - _PAD_R - 26, (_PAD_T + CH - _PAD_B) // 2)

def _lerp(a, b, t):
    return (a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t)

def _quad_pt(nx, ny):
    if ny <= 0.5:
        t=ny/0.5;  left=_lerp(_UL,_NL,t);  right=_lerp(_UR,_NR,t)
    else:
        t=(ny-0.5)/0.5; left=_lerp(_NL,_AL,t); right=_lerp(_NR,_AR,t)
    return (left[0]+(right[0]-left[0])*nx, left[1]+(right[1]-left[1])*nx)

def _zbounds_norm(z):
    z=str(z).strip().upper()
    if z in ('OUTSIDE','OUT',''): return None
    K={
        'LT1':(0,0.000,S,0.125),'LT2':(0,0.125,S,0.250),
        'LT3':(0,0.250,S,0.375),'LT4':(0,0.375,S,0.500),
        'RT1':(1-S,0.000,1,0.125),'RT2':(1-S,0.125,1,0.250),
        'RT3':(1-S,0.250,1,0.375),'RT4':(1-S,0.375,1,0.500),
        'LB1':(0,0.500,S,0.625),'LB2':(0,0.625,S,0.750),
        'LB3':(0,0.750,S,0.875),'LB4':(0,0.875,S,1.000),
        'RB1':(1-S,0.500,1,0.625),'RB2':(1-S,0.625,1,0.750),
        'RB3':(1-S,0.750,1,0.875),'RB4':(1-S,0.875,1,1.000),
    }
    if z in K: return K[z]
    ix=z.endswith('X')
    try: n=int(z.replace('X',''))
    except: return None
    if not 1<=n<=32: return None
    col,row=(n-1)%8,(n-1)//8
    gw=(1-2*S)/8; x1=S+col*gw
    y1=(0.5+row*0.125) if ix else (0.5-(row+1)*0.125)
    return (x1,y1,x1+gw,y1+0.125)

def _zone_poly(z):
    b=_zbounds_norm(z)
    if b is None: return None
    x1,y1,x2,y2=b
    return [_quad_pt(x1,y1),_quad_pt(x2,y1),_quad_pt(x2,y2),_quad_pt(x1,y2)]

def zcenter(z):
    b=_zbounds_norm(z)
    return ((b[0]+b[2])/2,(b[1]+b[3])/2) if b else (0.5,0.5)

def click2zone(px, py):
    def _row(ny):
        if ny<=0.5:
            t=ny/0.5; lx=_UL[0]*(1-t)+_NL[0]*t; rx=_UR[0]*(1-t)+_NR[0]*t
            ly=_UL[1]*(1-t)+_NL[1]*t
        else:
            t=(ny-0.5)/0.5; lx=_NL[0]*(1-t)+_AL[0]*t; rx=_NR[0]*(1-t)+_AR[0]*t
            ly=_NL[1]*(1-t)+_AL[1]*t
        return lx,rx,ly
    lo,hi=0.0,1.0
    for _ in range(20):
        mid=(lo+hi)/2; _,_,ly=_row(mid)
        if ly<py: lo=mid
        else: hi=mid
    ny=(lo+hi)/2; lx,rx,_=_row(ny)
    if rx==lx: return None
    nx=(px-lx)/(rx-lx)
    if not (0<=nx<=1 and 0<=ny<=1): return None
    if nx<S or nx>1-S:
        side='L' if nx<S else 'R'; half='T' if ny<0.5 else 'B'
        return f"{side}{half}{min(3,int((ny%0.5)/0.125))+1}"
    gw=(1-2*S)/8; col=max(0,min(7,int((nx-S)/gw)))
    if ny>=0.5:
        row=max(0,min(3,int((ny-0.5)/0.125))); return f"{row*8+col+1}x"
    row=max(0,min(3,int((0.5-ny)/0.125))); return str(row*8+col+1)

def isx(z): return str(z).strip().upper().endswith('X')

# ═══════════════════════════════════════════════════════════════════════════════
#  RENK PALETİ  — Australian Open hardcourt
#  Görsel referans: mavi iç alan, yeşil koridor, beyaz çizgiler
# ═══════════════════════════════════════════════════════════════════════════════
# Saha
_BLUE_TOP    = '#1368B0'   # rakip taraf mavi (hardcourt)
_BLUE_BOT    = '#1060A0'   # oyuncu taraf mavi (hafif koyu)
_GREEN_ALLEY = '#276B2A'   # doubles koridoru yeşili
_BLUE_SVC    = '#1872C0'   # servis kutusu (hafif açık mavi)
_BG_OUTER    = '#0A2030'   # saha dışı zemin

# Paneller
_BG_MAIN  = '#0D1520'   # ana arka plan
_BG_PANEL = '#111C2A'   # sol panel
_BG_CARD  = '#162030'   # kart/form elemanları
_BG_CARD2 = '#1A2840'   # kart2

# Yazı
_TXT_WHT  = '#E8F0F8'
_TXT_BLU  = '#7ABADC'
_TXT_GRN  = '#5CDD88'
_TXT_ORG  = '#FFAA44'
_TXT_MUT  = '#4A6070'
_TXT_CYN  = '#44CCFF'

# Aksanlar
_ACC_GRN  = '#00BB66'
_ACC_BLU  = '#2288DD'
_ACC_ORG  = '#FF7722'
_ACC_YEL  = '#FFCC00'

# Tahmin renkleri  (kırmızı → sarı → yeşil ısı haritası)
PCOL = ['#FF2200','#FF8800','#FFDD00','#55CC00','#1199FF']

def _zone_fill(z):
    z=str(z).upper()
    if z[:2] in ('LT','RT'): return _GREEN_ALLEY
    if z[:2] in ('LB','RB'): return _GREEN_ALLEY
    return _BLUE_BOT if z.endswith('X') else _BLUE_TOP


# ═══════════════════════════════════════════════════════════════════════════════
#  MODEL KATMANI  — tek kaynak: tenis/tahmin.py
# ═══════════════════════════════════════════════════════════════════════════════
class DemoPredictor:
    """Model dosyası yoksa arayüzü denemek için sahte tahmin üretir."""
    def predict(self, cinsiyet, kategori, vurulan, nereden=None, **kw):
        import hashlib, random
        seed = int(hashlib.md5(f"{vurulan}{nereden}".encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)
        pool = [str(i) for i in range(1, 33)] if isx(vurulan) else [f"{i}x" for i in range(1, 33)]
        zones = rng.sample(pool, 5)
        probs = sorted([rng.uniform(0.05, 0.40) for _ in zones], reverse=True)
        s = sum(probs)
        return [{'zone': z, 'prob': p / s} for z, p in zip(zones, probs)]


def load_best_predictor():
    if A.MODEL_DOSYASI.exists():
        try:
            from tenis.tahmin import TenisTahminci
            p = TenisTahminci()
            t1 = p.cv_ozet.get("Top-1 %")
            ek = f" (maç bazlı CV Top-1 %{t1:.1f})" if t1 else ""
            return p, f"{p.model_adi}{ek}"
        except Exception as e:
            print(f"[Model] yüklenemedi: {e}")
    return DemoPredictor(), 'Demo Modu'



# ═══════════════════════════════════════════════════════════════════════════════
#  ANA UYGULAMA
# ═══════════════════════════════════════════════════════════════════════════════
class App:
    def __init__(self, root):
        self.root=root
        self.p_zone=None
        self.r_zone=None

        root.title("🎾  Tenis Akıllı Atış Tahmini")
        root.configure(bg=_BG_MAIN)
        root.resizable(False,False)

        # Model yükle
        self.pred,self.model_name=load_best_predictor()

        self._setup_ttk()
        self._build_ui()
        self._draw_court()
        self._refresh_step()

    # ── TTK stil ──────────────────────────────────────────────────────────────
    def _setup_ttk(self):
        s=ttk.Style()
        s.theme_use('clam')
        s.configure('TCombobox',
            fieldbackground=_BG_CARD2,background=_BG_CARD2,
            foreground=_TXT_WHT,selectbackground=_BG_CARD,
            selectforeground=_TXT_WHT,bordercolor='#2A4060',
            arrowcolor=_TXT_CYN,font=('Helvetica',9))
        s.map('TCombobox',fieldbackground=[('readonly',_BG_CARD2)])

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        root=self.root

        # ── SOL PANEL ─────────────────────────────────────────────────────────
        lp=tk.Frame(root,bg=_BG_PANEL,width=238)
        lp.pack(side=tk.LEFT,fill=tk.Y,padx=(8,0),pady=8)
        lp.pack_propagate(False)

        # Başlık
        tk.Label(lp,text="🎾  Akıllı Atış Tahmini",
                 font=('Helvetica',12,'bold'),bg=_BG_PANEL,fg=_ACC_GRN).pack(pady=(10,0))
        tk.Label(lp,text="Taktik Analiz  —  Rakip Konum Dahil",
                 font=('Helvetica',7),bg=_BG_PANEL,fg=_TXT_MUT).pack(pady=(0,4))

        # Model etiketi
        _mcols={'Demo Modu':_TXT_ORG}
        mdl_col=_mcols.get(self.model_name,
                           '#55FFAA' if self.model_name.startswith('DL:') else _TXT_BLU)
        tk.Label(lp,text=f"▸ {self.model_name}",
                 font=('Helvetica',8),bg=_BG_PANEL,fg=mdl_col).pack()

        def sep(): tk.Frame(lp,bg='#1E3040',height=1).pack(fill=tk.X,padx=6,pady=5)
        def lbl(t,fg=_TXT_BLU):
            tk.Label(lp,text=t,font=('Helvetica',8,'bold'),bg=_BG_PANEL,fg=fg
                     ).pack(anchor=tk.W,padx=10,pady=(6,1))

        sep()

        # ── SPORCU / CİNSİYET / KATEGORİ ─────────────────────────────────────
        is_v6=False
        is_boost=True   # cinsiyet/kategori seçimi her modelde gösterilir

        if is_v6:
            lbl("👤  Sporcu")
            self.v_sp=tk.StringVar(value=self.pred.sporcular[0])
            ttk.Combobox(lp,textvariable=self.v_sp,values=self.pred.sporcular,
                         width=26,state='readonly').pack(padx=10)
            self.v_cin=None; self.v_kat=None
        elif is_boost:
            lbl("⚥  Cinsiyet")
            self.v_cin=tk.StringVar(value='Erkekler')
            cf=tk.Frame(lp,bg=_BG_PANEL); cf.pack(fill=tk.X,padx=10)
            for v in ['Erkekler','Kadınlar']:
                tk.Radiobutton(cf,text=v,variable=self.v_cin,value=v,
                    bg=_BG_PANEL,fg=_TXT_WHT,selectcolor=_BG_CARD,
                    activebackground=_BG_PANEL,font=('Helvetica',9)
                    ).pack(side=tk.LEFT,padx=4)
            lbl("🏆  Kategori")
            self.v_kat=tk.StringVar(value='Best')
            kf=tk.Frame(lp,bg=_BG_PANEL); kf.pack(fill=tk.X,padx=10)
            for v in ['Best','Middle','Low']:
                tk.Radiobutton(kf,text=v,variable=self.v_kat,value=v,
                    bg=_BG_PANEL,fg=_TXT_WHT,selectcolor=_BG_CARD,
                    activebackground=_BG_PANEL,font=('Helvetica',9)
                    ).pack(side=tk.LEFT,padx=4)
            self.v_sp=None
        else:
            # Demo
            lbl("👤  Sporcu")
            self.v_sp=tk.StringVar(value=self.pred.sporcular[0])
            ttk.Combobox(lp,textvariable=self.v_sp,values=self.pred.sporcular,
                         width=26,state='readonly').pack(padx=10)
            self.v_cin=None; self.v_kat=None

        sep()

        # ── VURUŞ STİLİ ───────────────────────────────────────────────────────
        lbl("🎾  Vuruş Stili")
        self.v_vs=tk.StringVar(value='Forehand')
        ttk.Combobox(lp,textvariable=self.v_vs,width=26,state='readonly',
                     values=['Forehand','Backhand','Serve Flat','backhand slice',
                             'Forehand slice','Forehand volley','Backhand volley',
                             'Smash','Kick Serve','Drop Shot','Lob','Return']
                     ).pack(padx=10)

        # ── SPİN ──────────────────────────────────────────────────────────────
        lbl("🔄  Spin")
        self.v_spin=tk.StringVar(value='Topspin')
        ttk.Combobox(lp,textvariable=self.v_spin,width=26,state='readonly',
                     values=['Topspin','Slice','flat','Backspin','Bilinmiyor']
                     ).pack(padx=10)

        sep()

        # ── KADEME ────────────────────────────────────────────────────────────
        lbl("📊  Kademe (Zorluk)")
        kf2=tk.Frame(lp,bg=_BG_PANEL); kf2.pack(fill=tk.X,padx=10)
        self.v_kad=tk.IntVar(value=2)
        for v,t in [(1,'Kolay'),(2,'Nötr'),(3,'Zor')]:
            tk.Radiobutton(kf2,text=t,variable=self.v_kad,value=v,
                bg=_BG_PANEL,fg=_TXT_WHT,selectcolor=_BG_CARD,
                activebackground=_BG_PANEL,font=('Helvetica',8)
                ).pack(side=tk.LEFT,padx=2)

        # ── YÜKSEKLİK ─────────────────────────────────────────────────────────
        lbl("↕  Top Yüksekliği")
        yf2=tk.Frame(lp,bg=_BG_PANEL); yf2.pack(fill=tk.X,padx=10)
        self.v_yuk=tk.IntVar(value=2)
        for v,t in [(1,'Alt'),(2,'Orta'),(3,'Yüksek')]:
            tk.Radiobutton(yf2,text=t,variable=self.v_yuk,value=v,
                bg=_BG_PANEL,fg=_TXT_WHT,selectcolor=_BG_CARD,
                activebackground=_BG_PANEL,font=('Helvetica',8)
                ).pack(side=tk.LEFT,padx=2)

        sep()

        # ── ADIM GÖSTERGESİ ───────────────────────────────────────────────────
        self.lbl_step=tk.Label(lp,text="",wraplength=214,justify=tk.LEFT,
                                font=('Helvetica',8,'bold'),bg=_BG_PANEL,fg=_ACC_YEL)
        self.lbl_step.pack(padx=10,pady=(2,4),anchor=tk.W)

        # ── SEÇİM KUTULARI ────────────────────────────────────────────────────
        sf=tk.Frame(lp,bg=_BG_CARD); sf.pack(fill=tk.X,padx=8,pady=4)
        sf.columnconfigure(1,weight=1)

        # Başlık satırı
        tk.Label(sf,text="SEÇİLİ BÖLGE",bg=_BG_CARD,fg=_TXT_MUT,
                 font=('Helvetica',7,'bold')).grid(row=0,column=0,columnspan=3,
                 sticky=tk.W,padx=8,pady=(6,2))

        # Oyuncu satırı
        tk.Label(sf,text="Oyuncu P:",bg=_BG_CARD,fg=_TXT_CYN,
                 font=('Helvetica',8),width=10,anchor=tk.W
                 ).grid(row=1,column=0,sticky=tk.W,padx=8,pady=3)
        self.lbl_pz=tk.Label(sf,text="—",font=('Courier',11,'bold'),
                              bg='#001A33',fg='#44CCFF',width=7,relief=tk.GROOVE,bd=1)
        self.lbl_pz.grid(row=1,column=1,sticky=tk.W,pady=3)
        self.lbl_bas=tk.Label(sf,text="",font=('Helvetica',7),bg=_BG_CARD,fg='#66AA66',width=5)
        self.lbl_bas.grid(row=1,column=2,padx=(4,8))

        # Rakip satırı
        tk.Label(sf,text="Rakip  R:",bg=_BG_CARD,fg=_TXT_ORG,
                 font=('Helvetica',8),width=10,anchor=tk.W
                 ).grid(row=2,column=0,sticky=tk.W,padx=8,pady=3)
        self.lbl_rz=tk.Label(sf,text="— seçilmedi",font=('Courier',9),
                              bg='#1A0E00',fg='#FFBB55',width=14,relief=tk.GROOVE,bd=1)
        self.lbl_rz.grid(row=2,column=1,columnspan=2,sticky=tk.W,pady=(3,6))

        sep()

        # ── BUTONLAR ──────────────────────────────────────────────────────────
        bf=tk.Frame(lp,bg=_BG_PANEL); bf.pack(fill=tk.X,padx=10,pady=4)

        self.btn_pred=tk.Button(bf,text="🎯  TAHMİN ET",
            font=('Helvetica',11,'bold'),
            bg='#003D1A',fg='#AAFFCC',activebackground='#005525',
            command=self._predict,pady=9,relief=tk.FLAT,cursor='hand2',
            state=tk.DISABLED)
        self.btn_pred.pack(fill=tk.X,pady=(0,3))

        tk.Button(bf,text="⚡  Rakipsiz Tahmin",
            font=('Helvetica',9),bg=_BG_CARD2,fg='#88BBDD',
            activebackground='#223355',
            command=self._predict_no_rakip,pady=5,relief=tk.FLAT,cursor='hand2'
            ).pack(fill=tk.X,pady=(0,3))

        tk.Button(bf,text="🗑  TEMİZLE",
            font=('Helvetica',9),bg='#2A0A00',fg='#FFAAAA',
            activebackground='#400A00',
            command=self._clear,pady=5,relief=tk.FLAT,cursor='hand2'
            ).pack(fill=tk.X)

        sep()

        # ── SONUÇLAR ──────────────────────────────────────────────────────────
        tk.Label(lp,text="📋  Top-5 Tahmin",font=('Helvetica',8,'bold'),
                 bg=_BG_PANEL,fg='#AAAAFF').pack(anchor=tk.W,padx=10,pady=(2,2))

        self.res_f=tk.Frame(lp,bg=_BG_PANEL)
        self.res_f.pack(fill=tk.X,padx=8)

        self.lbl_src=tk.Label(lp,text="",font=('Helvetica',7),
                               bg=_BG_PANEL,fg='#445566',wraplength=220)
        self.lbl_src.pack(padx=10,pady=(3,6),anchor=tk.W)

        # ── ORTA + SAĞ: KORT ──────────────────────────────────────────────────
        rp=tk.Frame(root,bg=_BG_MAIN)
        rp.pack(side=tk.LEFT,padx=(6,8),pady=8)

        tk.Label(rp,text="🎾  Tenis Akıllı Atış Tahmini  —  Perspektif Görünüm",
                 font=('Helvetica',9,'bold'),bg=_BG_MAIN,fg=_TXT_BLU).pack(pady=(0,3))

        self.cv=tk.Canvas(rp,width=CW,height=CH,
                          bg='#0A1E30',highlightthickness=2,
                          highlightbackground='#2A6AAA',cursor='crosshair')
        self.cv.pack()
        self.cv.bind('<Button-1>',self._click)
        self.cv.bind('<Motion>',  self._hover)

        self.lbl_hint=tk.Label(rp,text="",font=('Helvetica',8,'italic'),
                                bg=_BG_MAIN,fg='#4A6070')
        self.lbl_hint.pack()

    # ── YARDIMCI ──────────────────────────────────────────────────────────────
    def _get_sporcu(self):
        if self.v_sp: return self.v_sp.get()
        return ''

    def _get_cinsiyet(self):
        if self.v_cin: return self.v_cin.get()
        return 'Erkekler'

    def _get_kategori(self):
        if self.v_kat: return self.v_kat.get()
        return 'Best'

    # ── ADIM GÜNCELLEMESİ ────────────────────────────────────────────────────
    def _refresh_step(self):
        if self.p_zone is None:
            self.lbl_step.config(
                text="📍 ADIM 1 — Oyuncu konumunu seçin\n"
                     "ALT sahadan (1x–32x) kendi bölgenizi tıklayın",
                fg=_ACC_YEL)
            self.lbl_hint.config(text="▼ Alt yarıdan kendi konumunuzu tıklayın")
            self.cv.config(highlightbackground='#1A7744')
            self.btn_pred.config(state=tk.DISABLED,bg='#1A3322',fg='#559977')
        elif self.r_zone is None:
            self.lbl_step.config(
                text="📍 ADIM 2 — Rakip konumunu seçin  (opsiyonel)\n"
                     "ÜST sahadan (1–32) rakibin bölgesini tıklayın\n"
                     "ya da  ⚡ Rakipsiz Tahmin",
                fg=_TXT_ORG)
            self.lbl_hint.config(text="▲ Üst yarıdan rakip konumunu tıklayın")
            self.cv.config(highlightbackground='#BB7700')
            self.btn_pred.config(state=tk.DISABLED,bg='#1A3322',fg='#559977')
        else:
            self.lbl_step.config(text="✅ Hazır — TAHMİN ET butonuna basın",fg='#44EE88')
            self.lbl_hint.config(text="Tahmin için butona basın ya da farklı rakip/oyuncu seçin")
            self.cv.config(highlightbackground='#22AA55')
            self.btn_pred.config(state=tk.NORMAL,bg='#004D22',fg='#AAFFCC')

    # ── TIKLAMA ───────────────────────────────────────────────────────────────
    def _click(self,event):
        z=click2zone(event.x,event.y)
        if not z: return
        if self.p_zone is None:
            self.p_zone=z
            self.lbl_pz.config(text=f"  {z}  ")
            if hasattr(self.pred,'basari_orani'):
                sporcu=self._get_sporcu() or 'Demo'
                br=self.pred.basari_orani(sporcu,z)
                if br is not None:
                    c='#FF5555' if br<0.5 else ('#FFAA44' if br<0.75 else '#55EE55')
                    self.lbl_bas.config(text=f"%{br*100:.0f}",fg=c)
        elif self.r_zone is None:
            self.r_zone=z
            self.lbl_rz.config(text=f"  {z}  ")
        self._redraw()
        self._refresh_step()

    def _hover(self,event):
        self.cv.config(cursor='hand2' if click2zone(event.x,event.y) else 'crosshair')

    # ── TEMİZLE ───────────────────────────────────────────────────────────────
    def _clear(self):
        self.p_zone=self.r_zone=None
        self.lbl_pz.config(text="—"); self.lbl_rz.config(text="— seçilmedi")
        self.lbl_bas.config(text=""); self.lbl_src.config(text="")
        for w in self.res_f.winfo_children(): w.destroy()
        self._draw_court(); self._refresh_step()

    # ── TAHMİN ────────────────────────────────────────────────────────────────
    def _predict(self): self._run(True)

    def _predict_no_rakip(self):
        if not self.p_zone:
            messagebox.showwarning("Eksik","Önce oyuncu konumunu seçin.")
            return
        self._run(False)

    def _run(self,use_rakip):
        nereden=self.r_zone if use_rakip else None
        try:
            results=self.pred.predict(
                self._get_cinsiyet(),self._get_kategori(),
                self.p_zone,nereden=nereden,
                vurus=self.v_vs.get(),spin=self.v_spin.get(),
                kademe=self.v_kad.get(),yukseklik=self.v_yuk.get())[:5]
            src=self.model_name
        except Exception as e:
            messagebox.showerror("Tahmin Hatası",str(e))
            return
        self._draw_predictions(results)
        self._update_list(results,src)

    # ═══════════════════════════════════════════════════════════════════════════
    #  KORT ÇİZİMİ  — v6 orijinali + AO renk paleti
    # ═══════════════════════════════════════════════════════════════════════════
    def _draw_court(self):
        c=self.cv; c.delete("all")

        # Dış zemin
        c.create_rectangle(0,0,CW,CH,fill=_BG_OUTER,outline='')

        def poly(pts,fill,outline='',width=1):
            flat=[v for p in pts for v in p]
            c.create_polygon(flat,fill=fill,outline=outline,width=width)

        def line(p1,p2,**kw):
            c.create_line(p1[0],p1[1],p2[0],p2[1],**kw)

        # ── 1) ZONE ZEMİNLERİ ────────────────────────────────────────────────
        all_z=([str(n) for n in range(1,33)]+[f"{n}x" for n in range(1,33)]+
               [f"LT{i}" for i in range(1,5)]+[f"RT{i}" for i in range(1,5)]+
               [f"LB{i}" for i in range(1,5)]+[f"RB{i}" for i in range(1,5)])
        for z in all_z:
            pts=_zone_poly(z)
            if pts:
                poly(pts,_zone_fill(z),outline='#4A90C8',width=1)

        # ── 2) DIŞ ÇERÇEVE ───────────────────────────────────────────────────
        outer=[_quad_pt(0,0),_quad_pt(1,0),_quad_pt(1,1),_quad_pt(0,1)]
        c.create_polygon([v for p in outer for v in p],fill='',outline='#FFFFFF',width=3)

        # Kenar şerit (singles sınırı)
        for nx in [S,1-S]:
            line(_quad_pt(nx,0),_quad_pt(nx,1),fill='#FFFFFF',width=2)

        # ── 3) DİKEY IZGARA ──────────────────────────────────────────────────
        gw=(1-2*S)/8
        for col in range(1,8):
            nx=S+col*gw
            line(_quad_pt(nx,0),_quad_pt(nx,1),fill='#FFFFFF',width=1,dash=(4,4))

        # ── 4) YATAY IZGARA ──────────────────────────────────────────────────
        for row in range(1,4):
            for ny in [0.5-row*0.125,0.5+row*0.125]:
                if row==1:   lw,dk=2,()
                elif row==2: lw,dk=1,(5,5)
                else:        lw,dk=1,(3,5)
                kw=dict(fill='#FFFFFF',width=lw)
                if dk: kw['dash']=dk
                line(_quad_pt(S,ny),_quad_pt(1-S,ny),**kw)
        for row in range(1,4):
            for nxs,nxe in [(0,S),(1-S,1)]:
                for ny in [row*0.125,0.5+row*0.125]:
                    line(_quad_pt(nxs,ny),_quad_pt(nxe,ny),
                         fill='#88CC88',width=1,dash=(2,3))

        # ── 5) AĞ (FILE) ─────────────────────────────────────────────────────
        nl=_quad_pt(0,0.5); nr=_quad_pt(1,0.5)
        c.create_line(nl[0]+1,nl[1]+2,nr[0]+1,nr[1]+2,fill='#000000',width=5)
        c.create_line(nl[0],nl[1],nr[0],nr[1],fill='#FFFFFF',width=4)
        nm=_quad_pt(0.5,0.5); nm_top=(nm[0],nm[1]-8)
        c.create_line(nm[0],nm[1],nm_top[0],nm_top[1],fill='#CCCCCC',width=2)
        for t in [0.25,0.5,0.75]:
            lpt=(nl[0]*(1-t)+nr[0]*t,nl[1]*(1-t)+nr[1]*t)
            c.create_line(lpt[0],lpt[1]-1,lpt[0],lpt[1]+3,fill='#AAAAAA',width=1)
        c.create_line(nl[0],nl[1]+1,nr[0],nr[1]+1,fill='#555555',width=2)

        # ── 6) SERVİS MERKEZ ─────────────────────────────────────────────────
        line(_quad_pt(0.5,0.25),_quad_pt(0.5,0.5),fill='#FFFFFF',width=2)
        line(_quad_pt(0.5,0.5), _quad_pt(0.5,0.75),fill='#FFFFFF',width=2)

        # ── 7) ZONE ETİKETLERİ ───────────────────────────────────────────────
        gw2=(1-2*S)/8
        for n in range(1,33):
            col,row=(n-1)%8,(n-1)//8
            cx,cy=_quad_pt(S+(col+0.5)*gw2,0.5-(row+0.5)*0.125)
            fsz=max(5,8-row)
            c.create_text(cx,cy,text=str(n),fill='#DDEEFF',font=('Helvetica',fsz,'bold'))
            cx2,cy2=_quad_pt(S+(col+0.5)*gw2,0.5+(row+0.5)*0.125)
            fsz2=min(9,6+row)
            c.create_text(cx2,cy2,text=f"{n}x",fill='#FFE080',font=('Helvetica',fsz2,'bold'))
        for sd,nxc in [('L',S/2),('R',1-S/2)]:
            for r in range(1,5):
                for half,nyc in [('T',0.5-(r-0.5)*0.125),('B',0.5+(r-0.5)*0.125)]:
                    cx,cy=_quad_pt(nxc,nyc)
                    c.create_text(cx,cy,text=f"{sd}{half}{r}",fill='#CCCCCC',font=('Helvetica',6))

        # ── 8) ETIKET BANTLARI ────────────────────────────────────────────────
        tx,ty=_quad_pt(0.5,0.04)
        c.create_text(tx,ty-12,text="◀  RAKİP SAHASI  (1–32)  ▶",
                      fill='#C090F0',font=('Helvetica',8,'bold'))
        tx2,ty2=_quad_pt(0.5,0.97)
        c.create_text(tx2,ty2+10,text="◀  OYUNCU SAHASI  (1x–32x)  ▶",
                      fill='#66DD66',font=('Helvetica',8,'bold'))

    # ── SEÇİM İŞARETLERİ ─────────────────────────────────────────────────────
    def _redraw(self):
        self.cv.delete("overlay")
        if self.p_zone:
            pts=_zone_poly(self.p_zone)
            if pts:
                flat=[v for p in pts for v in p]
                self.cv.create_polygon(flat,outline='#44AAFF',fill='#002255',
                    width=3,stipple='gray50',tags="overlay")
                cx=sum(p[0] for p in pts)/4; cy=sum(p[1] for p in pts)/4
                self.cv.create_oval(cx-10,cy-10,cx+10,cy+10,
                    fill='#1166DD',outline='white',width=2,tags="overlay")
                self.cv.create_text(cx,cy,text="P",
                    fill='white',font=('Helvetica',9,'bold'),tags="overlay")
        if self.r_zone:
            pts=_zone_poly(self.r_zone)
            if pts:
                flat=[v for p in pts for v in p]
                self.cv.create_polygon(flat,outline='#FFAA33',fill='#331100',
                    width=3,stipple='gray50',tags="overlay")
                cx=sum(p[0] for p in pts)/4; cy=sum(p[1] for p in pts)/4
                self.cv.create_oval(cx-10,cy-10,cx+10,cy+10,
                    fill='#CC7700',outline='white',width=2,tags="overlay")
                self.cv.create_text(cx,cy,text="R",
                    fill='white',font=('Helvetica',9,'bold'),tags="overlay")

    # ── TAHMİN GÖRSEL ─────────────────────────────────────────────────────────
    def _draw_predictions(self,results):
        self.cv.delete("overlay")
        self._redraw()
        if not self.p_zone: return
        p_pts=_zone_poly(self.p_zone)
        if not p_pts: return
        scx=sum(pt[0] for pt in p_pts)/4
        scy=sum(pt[1] for pt in p_pts)/4

        # ── Gölgeli arka plan bantları (köşe etiket kartları için)
        top5 = results[:5]

        for i,res in enumerate(top5):
            z,prob,col = res['zone'], res['prob'], PCOL[i]
            pts = _zone_poly(z)
            if not pts: continue
            flat = [v for pt in pts for v in pt]
            tcx = sum(pt[0] for pt in pts)/4
            tcy = sum(pt[1] for pt in pts)/4

            # Bölge dolgusu — alfa simülasyonu için stipple ile katman
            self.cv.create_polygon(flat, fill=col, outline='', stipple='gray75', tags="overlay")
            # Bölge çerçevesi
            lw = 4 if i==0 else (3 if i<3 else 2)
            self.cv.create_polygon(flat, fill='', outline=col, width=lw, tags="overlay")

            # Ok çizgisi (ok ucu sadece en iyi tahmin için)
            aw = 4 if i==0 else (3 if i<3 else 2)
            if i==0:
                self.cv.create_line(scx,scy,tcx,tcy,fill=col,width=aw,
                    arrow=tk.LAST,arrowshape=(18,22,8),tags="overlay",dash=())
            else:
                self.cv.create_line(scx,scy,tcx,tcy,fill=col,width=aw,
                    arrow=tk.LAST,arrowshape=(12,15,5),tags="overlay",
                    dash=(8,4) if i<3 else (4,6))

            # Etiket kartı — arka plan + yazı
            rank_lbl = f"#{i+1}"
            pct_lbl  = f"{prob*100:.1f}%"
            zone_lbl = z

            # Kart boyutları
            cw2, ch2 = 32, 28
            # Kartı bölge merkezinde, ortalanmış çiz
            x0,y0 = tcx-cw2, tcy-ch2//2
            x1,y1 = tcx+cw2, tcy+ch2//2
            # Kart gölgesi
            self.cv.create_rectangle(x0+2,y0+2,x1+2,y1+2,
                fill='#000000',outline='',tags="overlay")
            # Kart arka planı
            self.cv.create_rectangle(x0,y0,x1,y1,
                fill='#0D1520',outline=col,width=2,tags="overlay")
            # Rank + zone tek satır
            self.cv.create_text(tcx, tcy-7,
                text=f"{rank_lbl}  {zone_lbl}",
                fill=col, font=('Helvetica', 9 if i==0 else 8, 'bold'),
                anchor='center', tags="overlay")
            # Olasılık
            self.cv.create_text(tcx, tcy+8,
                text=pct_lbl,
                fill='white', font=('Helvetica', 9 if i==0 else 8, 'bold'),
                anchor='center', tags="overlay")

        # P noktası öne (büyütülmüş)
        self.cv.create_oval(scx-13,scy-13,scx+13,scy+13,
            fill='#0D2244',outline='white',width=3,tags="overlay")
        self.cv.create_oval(scx-11,scy-11,scx+11,scy+11,
            fill='#1166DD',outline='',tags="overlay")
        self.cv.create_text(scx,scy,text="P",
            fill='white',font=('Helvetica',10,'bold'),tags="overlay")

        # R noktası öne
        if self.r_zone:
            r_pts=_zone_poly(self.r_zone)
            if r_pts:
                rcx=sum(pt[0] for pt in r_pts)/4
                rcy=sum(pt[1] for pt in r_pts)/4
                self.cv.create_oval(rcx-13,rcy-13,rcx+13,rcy+13,
                    fill='#2A1500',outline='white',width=3,tags="overlay")
                self.cv.create_oval(rcx-11,rcy-11,rcx+11,rcy+11,
                    fill='#CC7700',outline='',tags="overlay")
                self.cv.create_text(rcx,rcy,text="R",
                    fill='white',font=('Helvetica',10,'bold'),tags="overlay")

    # ── SONUÇ LİSTESİ ─────────────────────────────────────────────────────────
    def _update_list(self,results,src):
        for w in self.res_f.winfo_children(): w.destroy()
        for i,res in enumerate(results):
            col=PCOL[i]
            fr=tk.Frame(self.res_f,bg='#0D1520',bd=1,relief=tk.GROOVE)
            fr.pack(fill=tk.X,pady=2,padx=2)
            # Rank badge
            tk.Label(fr,text=f"#{i+1}",font=('Helvetica',10,'bold'),
                     bg=col,fg='#000000' if i>2 else '#FFFFFF',
                     width=3,padx=2).pack(side=tk.LEFT)
            # Zone name
            tk.Label(fr,text=res['zone'],font=('Courier',11,'bold'),
                     bg='#0D1520',fg=col,width=6).pack(side=tk.LEFT,padx=(4,0))
            # Bar
            bw=max(3,int(res['prob']*100))
            bar=tk.Canvas(fr,width=80,height=16,bg='#0D1520',highlightthickness=0)
            bar.create_rectangle(0,3,bw,13,fill=col,outline='')
            bar.pack(side=tk.LEFT,padx=(2,2))
            # Probability
            tk.Label(fr,text=f"{res['prob']*100:.1f}%",
                     font=('Helvetica',9,'bold'),bg='#0D1520',fg='white',width=5
                     ).pack(side=tk.LEFT,padx=(0,4))
        rstr=f"Rakip: {self.r_zone}" if self.r_zone else "Rakip: —"
        self.lbl_src.config(text=f"📊 {src}   |   {rstr}")


# ─── MAIN ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root=tk.Tk()
    app=App(root)
    root.mainloop()
