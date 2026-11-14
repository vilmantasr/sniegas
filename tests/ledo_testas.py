"""12.43: ledas sniego valytuvų nuvalytose lango vietose – susidarymas, slidumas, užsnigimas, tirpimas, piešimas."""
import sys, ctypes, random, importlib.util, importlib.machinery
from unittest import mock
ctypes.windll = mock.MagicMock(); sys.modules["winreg"] = mock.MagicMock(); ctypes.WINFUNCTYPE = ctypes.CFUNCTYPE
byla = sys.argv[1]
spec = importlib.util.spec_from_file_location("sn", byla, loader=importlib.machinery.SourceFileLoader("sn", byla))
sn = importlib.util.module_from_spec(spec); sys.modules["sn"] = sn; spec.loader.exec_module(sn)
REZ = []
def tikrinti(pav, sal, info=""):
    REZ.append(bool(sal)); print(("  OK  " if sal else "  KLAIDA ") + pav + (f"  [{info}]" if info else ""))
class P:
    def __init__(s): s.st = []
    def poligonas(s, *a): pass
    def staciakampis(s, *a): s.st.append(a)
    def linija(s, *a): pass
class B(sn.Sniegas):
    def __init__(s):
        s.k = 1.0; s.statinis = P(); s.nesvarus_langai = []
        s.n = dict(sn.NUMATYTI, ledas_languose=True, valytuvai=True, kaupti_languose=True)
random.seed(1)
S = sn.STULPELIS
a = B(); n = 300  # 900 px langas
st = {"l": 100, "t": 400, "r": 100 + n * S, "h": [12.0] * n, "matomi": [(0, n)], "nesvarus": False}
a.langai = {1: st}
# valytuvas nuvalė 100–220 stulpelius (360 px), kitur sniegas lieka
for c in range(100, 220):
    st["h"][c] = 0.0
a.ledo_zymeti(st, 100 + 100 * S, 100 + 220 * S - 1)
for _ in range(20):
    a.ledo_zingsnis(1.0)
tikrinti("per 20 s ledo dar nėra", not st.get("ledas"))
for _ in range(60):
    a.ledo_zingsnis(1.0)
led = st.get("ledas") or []
ledo = [c for c, v in enumerate(led) if v > 0]
tikrinti("po ~30 s susidarė ledas", ledo, len(ledo))
if ledo:
    ilgis = (ledo[-1] - ledo[0] + 1) * S
    tikrinti("ledo ruoželis – vientisas", len(ledo) == ledo[-1] - ledo[0] + 1)
    tikrinti("ilgis 50–100 px", 50 - S <= ilgis <= 100 + S, ilgis)
    tikrinti("tik nuvalytoje vietoje ir ne per visą ją", 100 < ledo[0] and ledo[-1] < 219, (ledo[0], ledo[-1]))
    x = st["l"] + (ledo[0] + 2) * S
    tikrinti("ant ledo slidu", a.ant_ledo(st, x))
    tikrinti("šalia ledo neslidu", not a.ant_ledo(st, st["l"] + 50 * S))
    a.statinis = P(); a.piesti_leda(st, 0, n)
    tikrinti("ledas nupieštas (juostelė lango viršuje)", a.statinis.st and a.statinis.st[0][3] == st["t"]
             and a.statinis.st[0][0] == st["l"] + ledo[0] * S, a.statinis.st[:1])
    for c in ledo:
        st["h"][c] = 5.0
    tikrinti("užsnigtas ledas neslidus", not a.ant_ledo(st, x))
    a.statinis = P(); a.piesti_leda(st, 0, n)
    tikrinti("užsnigtas ledas nepiešiamas", not a.statinis.st)
    for c in ledo:
        st["h"][c] = 0.0  # valytuvas vėl nuvalė
    tikrinti("nuvalytas – vėl slidus", a.ant_ledo(st, x))
    for _ in range(400):
        a.ledo_zingsnis(1.0)
    tikrinti("po kelių minučių ištirpo", not a.ant_ledo(st, x))
# prisnigus nuvalytai vietai – ledas nesusidaro
b = B(); st2 = {"l": 0, "t": 400, "r": n * S, "h": [0.0] * n, "matomi": [(0, n)], "nesvarus": False}
b.langai = {1: st2}; b.ledo_zymeti(st2, 0, n * S)
for _ in range(10):
    b.ledo_zingsnis(1.0)
for c in range(n):
    st2["h"][c] = 6.0
for _ in range(60):
    b.ledo_zingsnis(1.0)
tikrinti("prisnigusioje vietoje ledas nesusidaro", not st2.get("ledas"))
# išjungus – ledas dingsta
if ledo:
    a.ledo_zymeti(st, 100 + 100 * S, 100 + 220 * S - 1)
    for c in range(100, 220):
        st["h"][c] = 0.0
    for _ in range(80):
        a.ledo_zingsnis(1.0)
    a.n["ledas_languose"] = False
    a.ledo_zingsnis(1.0)
    tikrinti("išjungus nustatymą ledas dingsta", not st.get("ledas") and "valyta" not in st)
c = B(); c.n["ledas_languose"] = False; st3 = {"l": 0, "t": 400, "r": n * S, "h": [0.0] * n, "matomi": [(0, n)], "nesvarus": False}
c.langai = {1: st3}
for _ in range(80):
    c.ledo_zingsnis(1.0)
tikrinti("išjungtas – ledo nėra", not st3.get("ledas"))
print(f"{sum(REZ)}/{len(REZ)}")
sys.exit(0 if all(REZ) else 1)
