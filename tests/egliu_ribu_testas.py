"""12.31: eglių aukščio ribos – mažiausias visada mažesnis už didžiausią; siluetai – dvi retos šviesios eilės; priekinės eglutės nekeičiamos."""
import sys, ctypes, importlib.util, importlib.machinery, json, tempfile, pathlib
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
        s.n = sn.numatytieji(); s.k = 1.0; s.P = 2; s.vw, s.vh = 1600, 900; s.vx = s.vy = 0
    def __getattr__(s, k):
        if k.startswith("__"): raise AttributeError(k)
        m = mock.MagicMock(name=k); object.__setattr__(s, k, m); return m
class Kint:
    def __init__(s, v): s.v = str(v)
    def get(s): return s.v
    def set(s, v): s.v = str(v)
sn.user32 = mock.MagicMock(); sn.gdi32 = mock.MagicMock(); sn.msimg32 = mock.MagicMock()
print("1. Ribos")
a = B(); a.n.update(egliu_min=45, egliu_max=120)
tikrinti("mažiausias – iki didžiausio − 1", a.leistinos_dabar("egliu_min") == (16, 119))
tikrinti("didžiausias – nuo mažiausio + 1", a.leistinos_dabar("egliu_max") == (46, 250))
tikrinti("pavadinimuose: mažiausias 16–249, didžiausias 17–250", a.leistinos("egliu_min") == (16, 249) and a.leistinos("egliu_max") == (17, 250))
print("2. Keitimas")
a.kint = {"egliu_min": Kint(45), "egliu_max": Kint(120)}
a.valdikliai = {"egliu_min": mock.MagicMock(), "egliu_max": mock.MagicMock()}
veliau = []
a.root = mock.MagicMock(); a.root.after_idle = lambda f: veliau.append(f)
a.root.focus_get = lambda: None  # juosta (ne laukelis)
a.atideti = lambda *x: None; a.atnaujinti_egliu_valdiklius = lambda: None; a.piesti_egliu_perziura = lambda: None
a.kint["egliu_min"].set(130); a.pakeista("egliu_min")
for f in veliau: f()
tikrinti("juosta už didžiausio – mažiausias 119, parodoma 119", a.n["egliu_min"] == 119 and a.kint["egliu_min"].get() == "119",
         f'{a.n["egliu_min"]} / {a.kint["egliu_min"].get()}')
veliau.clear(); a.root.focus_get = lambda: a.valdikliai["egliu_max"]  # renkama laukelyje
a.kint["egliu_max"].set(1); a.pakeista("egliu_max")
for f in veliau: f()
tikrinti("renkant didžiausią „1“ – apribojama iki 120, bet laukelio tekstas nekeičiamas (galima rinkti toliau)",
         a.n["egliu_max"] == 120 and a.kint["egliu_max"].get() == "1", f'{a.n["egliu_max"]} / {a.kint["egliu_max"].get()}')
a.kint["egliu_max"].set(150); a.pakeista("egliu_max")
tikrinti("surinkus „150“ – 150", a.n["egliu_max"] == 150)
a.kint["egliu_max"].set(119); a.pakeista("egliu_max")
tikrinti("renkant „119“ (= mažiausias) – dar netaikoma (12.32)", a.n["egliu_max"] == 150)
a.root.focus_get = lambda: None; a.baigti_ivedima("egliu_max"); a.pakeista("egliu_max")  # mock kint – be trace
tikrinti("išėjus: didžiausias negali būti lygus mažiausiam (119 → 120)", a.n["egliu_max"] == 120 and a.n["egliu_min"] == 119)
print("3. Laukelių rodyklės")
sbs = {k: mock.MagicMock() for k in ("egliu_min", "egliu_max")}
a.valdikliai = sbs; a.ribu_tikrinimas = lambda iki: ("tikr", iki)
a.n.update(egliu_min=45, egliu_max=120); a.egliu_ribu_laukeliai()
km = sbs["egliu_min"].configure.call_args.kwargs; kx = sbs["egliu_max"].configure.call_args.kwargs
tikrinti("rodyklės: mažiausias 16–119, didžiausias 46–250", (km["from_"], km["to"], kx["from_"], kx["to"]) == (16, 119, 46, 250)
         and km["validatecommand"] == ("tikr", 249) and kx["validatecommand"] == ("tikr", 250))  # rinkti – iki absoliučios (12.32)
print("4. Bylos įkėlimas")
for mn, mx, laukta in ((120, 120, (120, 121)), (150, 100, (100, 150)), (250, 250, (249, 250)), (45, 120, (45, 120))):
    with tempfile.TemporaryDirectory() as d:
        bp = pathlib.Path(d) / "n.json"; bp.write_text(json.dumps({"egliu_min": mn, "egliu_max": mx}), encoding="utf-8")
        b = B(); sn.messagebox = mock.MagicMock()
        n = b.ikelti_nustatymus(importuojama=bp)
        tikrinti(f"byloje {mn}/{mx} → {laukta[0]}/{laukta[1]}", (n["egliu_min"], n["egliu_max"]) == laukta,
                 f'{n["egliu_min"]}/{n["egliu_max"]}')
src = open(byla, encoding="utf-8").read()
tikrinti("priekinės eglutės – be rūko (kaip 12.30)", "egliu_rukas" not in src and "RUKO_SPALVA" not in src and "def ruke(" not in src)
print(f"{sum(REZ)}/{len(REZ)}")
