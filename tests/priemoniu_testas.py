"""12.34: GDI teptukų podėlis ribojamas (kadro pradžioje)."""
import sys, ctypes, importlib.util, importlib.machinery
from unittest import mock
ctypes.windll = mock.MagicMock(); sys.modules["winreg"] = mock.MagicMock(); ctypes.WINFUNCTYPE = ctypes.CFUNCTYPE
byla = sys.argv[1]
spec = importlib.util.spec_from_file_location("sn", byla, loader=importlib.machinery.SourceFileLoader("sn", byla))
sn = importlib.util.module_from_spec(spec); sys.modules["sn"] = sn; spec.loader.exec_module(sn)
REZ = []
def tikrinti(pav, sal, info=""):
    REZ.append(bool(sal)); print(("  OK  " if sal else "  KLAIDA ") + pav + (f"  [{info}]" if info else ""))
gyvi = set(); n = [0]
def kurti(*a):
    n[0] += 1; gyvi.add(n[0]); return n[0]
sn.gdi32 = mock.MagicMock(); sn.gdi32.CreateSolidBrush.side_effect = kurti; sn.gdi32.CreatePen.side_effect = kurti
sn.gdi32.DeleteObject.side_effect = lambda h: gyvi.discard(h)
g = sn.Priemones()
for kadras in range(100):  # senio lemputė: kas kadrą kitas atspalvis
    g.apriboti()
    for j in range(20):
        g.teptukas("#%02x%02x%02x" % ((kadras * 20 + j) % 256, kadras % 256, 7))
tikrinti("gyvų GDI objektų ne daugiau už ribą + 1 kadrą", len(gyvi) <= sn.PRIEMONIU_RIBA + 20, len(gyvi))
a = g.teptukas("#ffffff"); b = g.teptukas("#ffffff")
tikrinti("ta pati spalva – tas pats teptukas (podėlis veikia)", a == b)
g2 = sn.Priemones(); [g2.teptukas(f"#0000{i:02x}") for i in range(50)]; g2.apriboti()
tikrinti("iki ribos – nieko neišmeta", len(g2.teptukai) == 50)
print(f"{sum(REZ)}/{len(REZ)}")
