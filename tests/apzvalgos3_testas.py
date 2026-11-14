"""12.35 apžvalga: GDI įstatyti objektai, kampų geometrija, dalinis perpiešimas, ekranų kartojimas, bumbuliukų patarimai."""
import sys, ctypes, importlib.util, importlib.machinery
from unittest import mock
ctypes.windll = mock.MagicMock(); sys.modules["winreg"] = mock.MagicMock(); ctypes.WINFUNCTYPE = ctypes.CFUNCTYPE
byla = sys.argv[1]
spec = importlib.util.spec_from_file_location("sn", byla, loader=importlib.machinery.SourceFileLoader("sn", byla))
sn = importlib.util.module_from_spec(spec); sys.modules["sn"] = sn; spec.loader.exec_module(sn)
REZ = []
def tikrinti(pav, sal, info=""):
    REZ.append(bool(sal)); print(("  OK  " if sal else "  KLAIDA ") + pav + (f"  [{info}]" if info else ""))

print("1. GDI: į DC įstatyti teptukai nepamirštami")
gyvi, istatyti, n = set(), set(), [0]
def kurti(*a):
    n[0] += 1; gyvi.add(n[0]); return n[0]
def trinti(h):
    if h in istatyti: return 0
    gyvi.discard(h); return 1
g0 = getattr(sn, "gdi32", None)
sn.gdi32 = mock.MagicMock(); sn.gdi32.CreateSolidBrush.side_effect = kurti; sn.gdi32.CreatePen.side_effect = kurti
sn.gdi32.DeleteObject.side_effect = trinti
g = sn.Priemones()
for kadras in range(300):
    g.apriboti()
    istatyti.clear()
    for j in range(20):
        h = g.teptukas("#%02x%02x%02x" % ((kadras * 20 + j) % 256, kadras % 256, 7))
    istatyti.update((h, g.teptukas("#ffffff")))  # paskutinis kadro teptukas lieka įstatytas į 2 DC
valdomi = set(g.teptukai.values()) | set(g.piestukai.values())
tikrinti("nevaldomų (nutekėjusių) objektų nėra", not (gyvi - valdomi), len(gyvi - valdomi))
tikrinti("gyvų – ne daugiau už ribą + kadrą", len(gyvi) <= sn.PRIEMONIU_RIBA + 22, len(gyvi))
sn.gdi32 = g0 or mock.MagicMock(); sn.user32 = getattr(sn, "user32", None) or mock.MagicMock()
print(f"{sum(REZ)}/{len(REZ)}")

print("2. Trumpas sniegas prie apvalaus kampo")
class P:
    def __init__(s): s.pol, s.st = [], []
    def poligonas(s, pts, c): s.pol.append(pts)
    def staciakampis(s, *a): s.st.append(a)
    def linija(s, *a): pass
class B(sn.Sniegas):
    def __init__(s): s.k = 1.75; s.statinis = P()
S = sn.STULPELIS; t = 500; L = 100
h = [22.0] * 4 + [0.0] * 60  # krūva prie kairio kampo, už jos nuvalyta
Rr = L + len(h) * S
a = B(); a.piesti_sluoksni(h, 0, len(h), L, t, 1.0, None, kampai=(14, Rr))
pts = list(zip(a.statinis.pol[0][0::2], a.statinis.pol[0][1::2])) if a.statinis.pol else []
tikrinti("galas neišlenda už sniego (≤ L + 4·S)", pts and max(x for x, _ in pts) <= L + 4 * S, max(x for x, _ in pts) if pts else None)
ivirsus = [x for x, y in pts if y < t]
tikrinti("poligonas nekerta savęs (apačios taškai – sniego ribose)",
         all(min(ivirsus) <= x <= max(ivirsus) for x, y in pts if y >= t), pts[:3])
h2 = [3.0] * 2 + [0.0] * 60  # sniegas tik ant paties lanko
a2 = B(); a2.piesti_sluoksni(h2, 0, len(h2), L, t, 1.0, None, kampai=(14, L + len(h2) * S))
tikrinti("sniegas tik ant lanko – nepiešiamas", not a2.statinis.pol and not a2.statinis.st, a2.statinis.pol)
h3 = [10.0] * 7
a3 = B(); a3.piesti_sluoksni(h3, 0, 7, L, t, 1.0, None, kampai=(14, L + 7 * S))
xs3 = a3.statinis.pol[0][0::2] if a3.statinis.pol else []
tikrinti("abu galai trumpame lange – x didėja (galai nesusikerta)",
         xs3 and all(xs3[i] <= xs3[i + 1] for i in range(len(xs3) - 1) if a3.statinis.pol[0][2 * i + 1] < t
                     and a3.statinis.pol[0][2 * i + 3] < t), xs3[:12])
print(f"{sum(REZ)}/{len(REZ)}")

print("3. Dalinis perpiešimas, kliudantis apvalų kampą")
class B3(sn.Sniegas):
    def __init__(s):
        s.vw, s.vh = 1920, 1080; s.k = 1.0; s.n = sn.numatytieji();
        s.zemes_ruozai = []; s.egles = []; s.girliandos = []; s.sdc = 1; s.g = mock.MagicMock()
        s.kvietimai = []
    def ribos(s, l, t, r, b): return (l, t, r, b)
    def piesti_sluoksni(s, h, a, b, *args, **kw): s.kvietimai.append((a, b))
    def __getattr__(s, k):
        if k.startswith("__"): raise AttributeError(k)
        m = mock.MagicMock(name=k); object.__setattr__(s, k, m); return m
b3 = B3()
st = {"l": 300, "t": 400, "r": 300 + 100 * S, "h": [10.0] * 100, "matomi": [(0, 100)], "R": 8,
      "sritis": (298, 300, 302 + 100 * S, 410)}
b3.langai = {1: st}
b3.perpiesti_statini((300 + 2 * S, 380, 300 + 30 * S, 420))
tikrinti("kairys kampas – piešiamas nuo 0 stulpelio", b3.kvietimai and b3.kvietimai[0][0] == 0, b3.kvietimai)
b3.kvietimai.clear()
b3.perpiesti_statini((300 + 95 * S, 380, 300 + 98 * S, 420))
tikrinti("dešinys – iki galo ir su visu kampu", b3.kvietimai and b3.kvietimai[0][1] == 100
         and b3.kvietimai[0][0] <= 100 - (2 * 8 // S + 4), b3.kvietimai)
b3.kvietimai.clear()
b3.perpiesti_statini((300 + 40 * S, 380, 300 + 50 * S, 420))
tikrinti("viduryje – kaip buvo", b3.kvietimai and b3.kvietimai[0][0] > 30 and b3.kvietimai[0][1] < 60, b3.kvietimai)
print(f"{sum(REZ)}/{len(REZ)}")

print("4. Ekranų perkūrimo kartojimas išlaiko „tik darbo sritis“")
class B4(sn.Sniegas):
    def __init__(s):
        s.n = sn.numatytieji(); s.k = 1.0; s.P = 2; s.baigiama = False
        for m in ("taikyti_stilius", "naikinti_kadro_buferius", "kurti_zeme", "kurti_egles", "kurti_girliandas",
                  "kurti_bumbulus", "kurti_valytuvus", "kurti_senius", "kurti_snaigiu_atlasa", "pritaikyti_kieki",
                  "diag_ekranai", "fejerverku_P"):
            setattr(s, m, mock.MagicMock(return_value=""))
    def __getattr__(s, k):
        if k.startswith("__"): raise AttributeError(k)
        m = mock.MagicMock(name=k); object.__setattr__(s, k, m); return m
a4 = B4(); a4.ekranu_klaidos = 0; a4.ekranu_klaida = False
a4.monitoriai = [((0, 0, 1920, 1080), (0, 0, 1920, 1040))]
nauji = [((0, 0, 1920, 1080), (0, 0, 1920, 1000))]
sn.gauti_monitorius = lambda: nauji
def nustatyti(m): a4.monitoriai = m
a4.nustatyti_ekranus = nustatyti
a4.kurti_kadro_buferius = mock.MagicMock(side_effect=RuntimeError("DWM"))
irasai = []
sn.ZURNALAS = mock.MagicMock(); sn.ZURNALAS.rasyti.side_effect = lambda t, **k: irasai.append(t)
a4.aukstis = [5.0] * 10
a4.tikrinti_ekranus()
a4.kurti_kadro_buferius = mock.MagicMock()
a4.tikrinti_ekranus()
tikrinti("antras bandymas – vis dar „tik darbo sritis“", sum("tik darbo sritis" in t for t in irasai) == 2, [t[:60] for t in irasai if "ĮVYKIS" in t])
a5 = B4(); a5.ekranu_klaidos = 0; a5.ekranu_klaida = False
a5.monitoriai = [((0, 0, 1920, 1080), (0, 0, 1920, 1040))]
nauji = [((0, 0, 3840, 2160), (0, 0, 3840, 2120))]
a5.nustatyti_ekranus = lambda m: setattr(a5, "monitoriai", m)
a5.kurti_kadro_buferius = mock.MagicMock(side_effect=RuntimeError("DWM")); a5.aukstis = []
irasai.clear(); a5.tikrinti_ekranus(); a5.kurti_kadro_buferius = mock.MagicMock(); a5.tikrinti_ekranus()
tikrinti("pasikeitus ekranui – ir kartojant „perkuriama viskas“",
         sum("perkuriama viskas" in t for t in irasai) == 2, [t[:60] for t in irasai if "ĮVYKIS" in t])
print(f"{sum(REZ)}/{len(REZ)}")

print("5. Bumbuliukų vieta: vertimas ir patarimai")
tikrinti("naujasis aprašas išverstas", sn.APRASAI["bumbulai_languose"] in sn.EN)
tikrinti("senojo aprašo vertimo nebėra", "Bumbuliukai rieda ir ant langų viršaus, nuo krašto nurieda ir nukrenta." not in sn.EN)
a6 = B4(); a6.ispejimas = lambda r: None
a6.papildomi_aprasai = {"bumbulai_languose": lambda: "⚠ Reikia įjungti „Kaupti ant langų viršaus“."}
tikrinti("numatytoji – „Ir ant langų“", "Ir ant langų" in a6.numatytoji_tekstu("bumbulai_languose"),
         a6.numatytoji_tekstu("bumbulai_languose"))
tikrinti("„Ir ant langų“ – su įspėjimu", "⚠" in a6.slankiklio_patarimas("bumbulai_languose"))
tikrinti("„Tik ekrano apačioje“ – be įspėjimo", "⚠" not in a6.slankiklio_patarimas("bumbulai_languose", be_ispejimo=True))
print(f"{sum(REZ)}/{len(REZ)}")
