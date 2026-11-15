"""12.46: bumbuliuko kilputė, senio mirksėjimas (visose pozose), pakelto senio burna."""
import sys, ctypes, importlib.util, importlib.machinery
from unittest import mock
ctypes.windll = mock.MagicMock(); sys.modules["winreg"] = mock.MagicMock(); ctypes.WINFUNCTYPE = ctypes.CFUNCTYPE
byla = sys.argv[1]
spec = importlib.util.spec_from_file_location("sn", byla, loader=importlib.machinery.SourceFileLoader("sn", byla))
sn = importlib.util.module_from_spec(spec); sys.modules["sn"] = sn; spec.loader.exec_module(sn)
REZ = []
def tikrinti(pav, sal, info=""):
    REZ.append(bool(sal)); print(("  OK  " if sal else "  KLAIDA ") + pav + (f"  [{info}]" if info else ""))
def langeliai(g): return sum(c is not None for e in g for c in e)
# kilputė – visuose sukimosi kadruose, visų dydžių, ir tinklelis vienodo dydžio su mažėjančiais ir tirpimo kadrais
truksta = []
for R in range(3, 17):
    for k in range(sn.BUMBULU_KADRAI):
        su = sn.bumbulo_tinklelis(R, 0, "juosta", k, kilpute=True)
        be = sn.bumbulo_tinklelis(R, 0, "juosta", k, sn.bumbulo_krastine(R))
        if langeliai(su) != langeliai(be) + 1:
            truksta.append((R, k))
tikrinti("kilputė – 1 langelis visuose kadruose (R 3–16)", not truksta, truksta[:5])
R = 6
n = sn.bumbulo_krastine(R)
tikrinti("kadrų tinkleliai vienodo dydžio", {len(sn.bumbulo_tinklelis(R, 0, "juosta", 0, kilpute=True)),
                                             len(sn.bumbulo_tinklelis(2, 0, "juosta", 0, n, True)),
                                             len(sn.tirpimo_tinklelis(R, 0, "juosta", 0)), n} == {n})
tikrinti("nustatymų paveikslėliai – be kilputės (telpa į 32 px)", len(sn.bumbulo_tinklelis(5, 0, "juosta", 0)) * 2 <= 32)
# mirksėjimas – visose pozose ir kryptyse užmerkiamos abi akys (2 langeliai)
blogi = [(p, k, i) for p, k in sn.SENIO_KADRAI for i in (False, True) if len(sn.senio_mirksnio_langeliai(p, k, i)) != 2]
tikrinti("mirksi visose pozose", not blogi, blogi[:5])
s_ = {}
import time
n_mirk = 0
t0 = time.monotonic()
with mock.patch.object(sn.time, "monotonic") as m:
    for i in range(2000):
        m.return_value = t0 + i * 0.01
        n_mirk += sn.senio_mirksi(s_)
tikrinti("sumirksi retai ir trumpai (20 s – 2–5 kartai × ~12 kadrų)", 12 <= n_mirk <= 70, n_mirk)
# pakelto senio burna – ne kontūro eilutėje (matosi)
K = sn.SENIO_SPALVOS["K"]
g = sn.senio_tinklelis("kabo", 0, False)
tikrinti("pakelto senio burna – 2 langeliai", sum(r[11] == K for r in g[20:24]) == 2)
print(f"{sum(REZ)}/{len(REZ)}")
sys.exit(0 if all(REZ) else 1)
