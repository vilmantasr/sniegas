"""12.31: audito pataisos – kadro apsauga, klaidos langas ne kadro viduje, GetWindow ciklo riba, SWP_ASYNCWINDOWPOS."""
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
    def __init__(s): s.n = sn.numatytieji()
    def __getattr__(s, k):
        if k.startswith("__"): raise AttributeError(k)
        m = mock.MagicMock(name=k); object.__setattr__(s, k, m); return m
sn.ZURNALAS.ijungtas = False
a = B(); a.root = mock.MagicMock(); a.baigiama = False
def luzta(): raise RuntimeError("bandymas")
a._kadras = luzta
a.kadras()
tikrinti("kadrui nulūžus – kitas vis tiek suplanuojamas", a.root.after.call_args[0][1] == a.kadras)
a = B(); a.root = mock.MagicMock(); a.baigiama = True; a._kadras = luzta; a.kadras()
tikrinti("baigiant – nebeplanuojama", not a.root.after.called)
a = B(); a.root = mock.MagicMock(); a.klaida_parodyta = False; a.d_klaidos = 0
sn.messagebox = mock.MagicMock()
a.klaida(ValueError("x"))
tikrinti("klaidos langas – ne iškart (after_idle), kadras nelaukia", not sn.messagebox.showerror.called and a.root.after_idle.called)
a.root.after_idle.call_args[0][0]()
tikrinti("…ir parodomas vėliau", sn.messagebox.showerror.called)
# GetWindow ratas: grąžina tą patį langą be galo
a = B(); a.perdangos_hwnd = 1; a.senio_hwnd = set(); a.vx = a.vy = 0; a.vw, a.vh = 100, 100
skaicius = [0]
def gw(h, k): skaicius[0] += 1; return 77
sn.user32 = mock.MagicMock(); sn.user32.GetWindow = gw; sn.user32.IsWindowVisible = lambda h: False
tikrinti("užsisukus GetWindow ratui – ciklas baigiasi (≤ 3000)", a.kas_nors_virs_perdangos() is None and skaicius[0] <= 3001,
         str(skaicius[0]))
src = open(byla, encoding="utf-8").read()
tikrinti("Explorer patarimas keliamas su SWP_ASYNCWINDOWPOS", "SWP_NOACTIVATE | SWP_ASYNCWINDOWPOS)" in src and sn.SWP_ASYNCWINDOWPOS == 0x4000)
print(f"{sum(REZ)}/{len(REZ)}")
