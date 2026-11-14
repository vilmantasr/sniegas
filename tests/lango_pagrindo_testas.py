"""12.33: lango pagrindas – po rėmeliu (150 % – 2 eilutės); lango identitetas nepasikeičia kiekvieną skaitymą."""
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
        s.n = sn.numatytieji(); s.k = 1.5; s.vx = s.vy = 0; s.vw, s.vh = 1920, 1200; s.langai = {}
        s.nesvarios_sritys = []; s.monitoriai = [((0, 0, 1920, 1200), (0, 0, 1920, 1128))]
    def __getattr__(s, k):
        if k.startswith("__"): raise AttributeError(k)
        m = mock.MagicMock(name=k); object.__setattr__(s, k, m); return m
sn.user32 = mock.MagicMock(); sn.user32.GetDpiForWindow.return_value = 144
sn.lango_kampo_spindulys = lambda h: 12
a = B(); a.ant_ekrano = lambda x, y: True; a.nubyrinti = mock.MagicMock(); a.tikrinti_pilna_ekrana = lambda: None
def skaityti():
    a.langu_sarasas = []
    sn.user32.EnumWindows.side_effect = lambda cb, lp: a.langu_sarasas.append((7, (229, 175, 1920, 1128), False))
    a.perskaityti_langus()
skaityti(); st = a.langai[7]
tikrinti("150 %: pagrindas – 2 eilutės žemiau lango viršaus", st["t"] == 177 and st["B"] == 2, (st["t"], st["B"]))
tikrinti("kampo spindulys 12", st["R"] == 12)
tikrinti("sritis apima rėmelį ir kampą", st["sritis"][3] >= 177 + 12 and st["sritis"][1] < 175)
skaityti()
tikrinti("tas pats langas – neperkuriamas (nenubyra kiekvieną kartą)", a.langai[7] is st and not a.nubyrinti.called)
seg = a.langu_segmentai[0]
tikrinti("snaigės leidžiasi ant pagrindo (po rėmeliu)", seg[0] == 177)
print(f"{sum(REZ)}/{len(REZ)}")
