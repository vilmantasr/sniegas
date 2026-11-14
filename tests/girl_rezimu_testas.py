"""12.31: girliandų režimai „lieja“ (Slo-glo) ir „persilieja“ (Slow fade)."""
import sys, ctypes, importlib.util, importlib.machinery, random
from unittest import mock
ctypes.windll = mock.MagicMock(); sys.modules["winreg"] = mock.MagicMock(); ctypes.WINFUNCTYPE = ctypes.CFUNCTYPE
byla = sys.argv[1]
spec = importlib.util.spec_from_file_location("sn", byla, loader=importlib.machinery.SourceFileLoader("sn", byla))
sn = importlib.util.module_from_spec(spec); sys.modules["sn"] = sn; spec.loader.exec_module(sn)
REZ = []
def tikrinti(pav, sal, info=""):
    REZ.append(bool(sal)); print(("  OK  " if sal else "  KLAIDA ") + pav + (f"  [{info}]" if info else ""))
tikrinti("nauji režimai sąraše, „ramus“ – paskutinis", {"lieja", "persilieja"} <= set(sn.GIRL_REZIMAI) and sn.GIRL_REZIMAI[-1] == "ramus")
def eiga(rezimas, sek=10.0, dt=1 / 60):
    g = {"mirk": sn.girliandos_valdiklis(random.Random(1), 12), "vietos": [None] * 12}
    g["mirk"].update(rezimas=rezimas, liko=999.0, t=0.0)
    lyg = []
    for _ in range(int(sek / dt)):
        sn.girliandu_zingsnis([g], dt, 1.0, atspindziai=False)
        lyg.append(g["mirk"]["lygiai"])
    return lyg
L = eiga("lieja")
tikrinti("lieja: visos lemputės visada vienodos", all(len(set(x)) == 1 for x in L))
v = [x[0] for x in L]
tikrinti("lieja: pereina visas pakopas (beveik užgęsta ir pilnai šviečia)", min(v) <= 1 and max(v) == sn.GIRL_LYGIAI - 1, f"{min(v)}–{max(v)}")
pokyciai = sum(1 for a, b in zip(v, v[1:]) if a != b)
tikrinti("lieja: smulkūs žingsniai – per 10 s bent 60 pakopos pokyčių (ne laiptai)", pokyciai >= 60, str(pokyciai))
P = eiga("persilieja")
nuokr = max(abs(x[0] + x[1] - (sn.GIRL_LYGIAI - 1)) for x in P[60:])
tikrinti("persilieja: lyginės ir nelyginės – priešingos (suma beveik pastovi; siūlelis vėsta lėčiau nei įkaista)",
         nuokr <= 2, f"didžiausias nuokrypis {nuokr} iš {sn.GIRL_LYGIAI - 1}")
tikrinti("persilieja: abi grupės pereina nuo tamsios iki šviesios",
         min(x[0] for x in P) == 0 and max(x[0] for x in P) == sn.GIRL_LYGIAI - 1)
print("Lempučių atlasas (16 pakopų)")
from unittest import mock as _m
class B(sn.Sniegas):
    def __init__(s): s.n = sn.numatytieji()
    def __getattr__(s, k):
        if k.startswith("__"): raise AttributeError(k)
        m = _m.MagicMock(name=k); object.__setattr__(s, k, m); return m
sn.user32 = _m.MagicMock(); sn.GdiPiesejas = _m.MagicMock()
dydziai = []
a = B(); a.naujas_dc = lambda w, h: dydziai.append((w, h)) or {"dc": 1, "bmp": 1}
Pg = 11.2  # 4K ekranas, 200 %
atl = a.girl_lempuciu_atlasas("desinen", Pg)
tikrinti("atlasas – ne platesnis nei 32 767 px net 4K ir 200 %", dydziai and dydziai[0][0] <= 32767 and dydziai[0][1] <= 32767,
         str(dydziai))
v = {a.girl_lemputes_vieta(atl, sp, lyg, "desinen", f) for sp in range(len(sn.GIRL_SPALVOS))
     for lyg in range(sn.GIRL_LYGIAI) for f in range(3)}
w, h = dydziai[0]
tikrinti("kiekviena lemputė – sava vieta atlase ir telpa jame",
         len(v) == len(sn.GIRL_SPALVOS) * sn.GIRL_LYGIAI * 3 and all(x + atl["lw"] <= w and y + atl["lh"] <= h for x, y in v))
print(f"{sum(REZ)}/{len(REZ)}")
