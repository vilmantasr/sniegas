"""12.31: nustatymų logika – ribos, numatytosios, paruoštukai, vertimai; fejerverkų įspėjimas; kontūro priklausomybė."""
import sys, ctypes, importlib.util, importlib.machinery, re
from unittest import mock
ctypes.windll = mock.MagicMock(); sys.modules["winreg"] = mock.MagicMock(); ctypes.WINFUNCTYPE = ctypes.CFUNCTYPE
byla = sys.argv[1]
spec = importlib.util.spec_from_file_location("sn", byla, loader=importlib.machinery.SourceFileLoader("sn", byla))
sn = importlib.util.module_from_spec(spec); sys.modules["sn"] = sn; spec.loader.exec_module(sn)
REZ = []
def tikrinti(pav, sal, info=""):
    REZ.append(bool(sal)); print(("  OK  " if sal else "  KLAIDA ") + pav + (f"  [{info}]" if info else ""))
N, R, RL = sn.NUMATYTI, sn.RIBOS, sn.RIBOS_LAISVOS
src = open(byla, encoding="utf-8").read()
blogos = [k for k, (a, b) in R.items() if not all(a <= x <= b for x in (N[k] if isinstance(N[k], list) else [N[k]]))]
tikrinti("numatytosios – ribose", not blogos, str(blogos))
tikrinti("išplėstos ribos ne siauresnės", all(RL[k][0] <= a and RL[k][1] >= b for k, (a, b) in R.items()))
blogi = [(p, k) for p, d in sn.PARUOSTUKAI for k, v in d.items() if k != "kiekis" and (k not in N or (k in R and not R[k][0] <= v <= R[k][1]))]
tikrinti("paruoštukų reikšmės – žinomos ir ribose", not blogi, str(blogi))
tikrinti("tekstinės numatytosios – galimos", all(N[k] in g for k, g in sn.TEKSTINES_REIKSMES.items()))
trukst = [t for t in set(re.findall(r'\bT\("((?:[^"\\]|\\.)*)"\)', src)) if t not in sn.EN]
tikrinti("visi T(\"…\") išversti", not trukst, str(trukst[:3]))
class B(sn.Sniegas):
    def __init__(s): s.n = sn.numatytieji()
    def __getattr__(s, k):
        if k.startswith("__"): raise AttributeError(k)
        m = mock.MagicMock(name=k); object.__setattr__(s, k, m); return m
a = B(); a.n.update(fejerverkai=True, fejerverku_intervalas=2, fejerverku_trukme=120)
tikrinti("fejerverkai: šou 120 s, tarpas 2 min – įspėjimas", a.ispejimas("fejerverku_trukme") and a.ispejimas("fejerverku_intervalas"))
a.n.update(fejerverku_trukme=90)
tikrinti("šou 90 s, tarpas 2 min – be įspėjimo", a.ispejimas("fejerverku_trukme") is None)
a.n.update(fejerverkai=False, fejerverku_trukme=180)
tikrinti("išjungtiems fejerverkams – be įspėjimo", a.ispejimas("fejerverku_trukme") is None)
busenos = {}
a = B(); a.valdikliai = {"sniego_konturas": "kont"}; a.valdikliu_grupes = {}
a.valdiklio_busena = lambda w, ij: busenos.__setitem__(w, ij)
a.n.update(kaupimasis=True, kaupti_apacioje=False); a.atnaujinti_bumbulu_valdiklius()
tikrinti("nesikaupiant apačioje – „Sniego kontūras“ papilkėja", busenos["kont"] is False)
a.n.update(kaupti_apacioje=True); a.atnaujinti_bumbulu_valdiklius()
tikrinti("kaupiantis – aktyvus", busenos["kont"] is True)
tikrinti("girliandų mirksėjimo pavadinimas be dvigubų skliaustų", '"Mirksėjimas, %", 4)' in src)
print(f"{sum(REZ)}/{len(REZ)}")
