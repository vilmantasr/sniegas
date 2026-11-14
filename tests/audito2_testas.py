"""12.32 auditas: valytuvų spraitas eilutėmis; laikina ekranų klaida be klaidos lango."""
import sys, ctypes, importlib.util, importlib.machinery
from unittest import mock
ctypes.windll = mock.MagicMock(); sys.modules["winreg"] = mock.MagicMock(); ctypes.WINFUNCTYPE = ctypes.CFUNCTYPE
byla = sys.argv[1]
spec = importlib.util.spec_from_file_location("sn", byla, loader=importlib.machinery.SourceFileLoader("sn", byla))
sn = importlib.util.module_from_spec(spec); sys.modules["sn"] = sn; spec.loader.exec_module(sn)
REZ = []
def tikrinti(pav, sal, info=""):
    REZ.append(bool(sal)); print(("  OK  " if sal else "  KLAIDA ") + pav + (f"  [{info}]" if info else ""))
class B(sn.Sniegas):
    def __init__(s):
        s.n = sn.numatytieji(); s.k = 2.0; s.P = 5; s.baigiama = False
    def __getattr__(s, k):
        if k.startswith("__"): raise AttributeError(k)
        m = mock.MagicMock(name=k); object.__setattr__(s, k, m); return m
sn.piks_piesti = lambda *a, **k: None; sn.GdiPiesejas = mock.MagicMock()
print("1. Valytuvų spraitas (4K, išplėstos ribos, 600 %, 6 spalvos)")
a = B(); a.n.update(valytuvai=True, valytuvu_dydis=600, valytuvu_kiekis=6)
dydziai = []
a.naujas_dc = lambda w, h: dydziai.append((w, h)) or {"dc": 1, "bmp": 1}
a.valytuvai = []; a.valyt_sprite = None
a.kurti_valytuvus()
w, h = dydziai[-1]
tikrinti("plotis ≤ 32 767 px", w <= 32767, f"{w}×{h}")
tikrinti("6 eilutės (po vieną spalvai)", h == 6 * round(sn.VALYT_AUKSTIS * a.valyt_Pe))
a2 = B(); a2.n.update(valytuvai=True, valytuvu_dydis=600, valytuvu_kiekis=6)
a2.naujas_dc = lambda w, h: {"dc": 1, "bmp": 0}; a2.naikinti_dc = mock.MagicMock(); a2.valytuvai = []; a2.valyt_sprite = None
a2.kurti_valytuvus()
tikrinti("nepavykus sukurti – valytuvų nėra (ne švyturėliai be korpuso)", not a2.valytuvai and a2.valyt_sprite is None)
print("2. Ekranų pasikeitimas, kai buferių sukurti nepavyksta")
a = B(); a.taikyti_stilius = mock.MagicMock(); a.naikinti_kadro_buferius = mock.MagicMock(); a.nustatyti_ekranus = mock.MagicMock()
a.ekranu_klaidos = 0; a.ekranu_klaida = False
a.monitoriai = [((0, 0, 1920, 1080), (0, 0, 1920, 1040))]
sn.gauti_monitorius = lambda: [((0, 0, 3840, 2160), (0, 0, 3840, 2120))]
a.kurti_kadro_buferius = mock.MagicMock(side_effect=RuntimeError("DWM"))
a.aukstis = []
klaidos = 0
for i in range(5):
    try:
        a.tikrinti_ekranus()
    except RuntimeError:
        klaidos += 1
tikrinti("pirmi 4 kartai – be klaidos (tik žurnale), 5-as – klaida", klaidos == 1 and a.ekranu_klaidos == 5, klaidos)
a.kurti_kadro_buferius = mock.MagicMock()
for m in ("kurti_zeme", "kurti_egles", "kurti_girliandas", "kurti_bumbulus", "kurti_valytuvus", "kurti_senius",
          "kurti_snaigiu_atlasa"):
    setattr(a, m, mock.MagicMock())
a.tikrinti_ekranus()
tikrinti("pavykus – skaitiklis nunulinamas", a.ekranu_klaidos == 0 and not a.ekranu_klaida)
print(f"{sum(REZ)}/{len(REZ)}")
