"""Visas nustatymų langas (Xvfb): kurti_sasaja ant tikro Tk, likusi programa – mock. argv: byla, png."""
import sys, ctypes, importlib.util, importlib.machinery, subprocess, time, os
from unittest import mock
ctypes.windll = mock.MagicMock(); sys.modules["winreg"] = mock.MagicMock(); ctypes.WINFUNCTYPE = ctypes.CFUNCTYPE
byla = sys.argv[1]
spec = importlib.util.spec_from_file_location("sn", byla, loader=importlib.machinery.SourceFileLoader("sn", byla))
sn = importlib.util.module_from_spec(spec); sys.modules["sn"] = sn; spec.loader.exec_module(sn)
import tkinter as tk
from tkinter import ttk
class B(sn.Sniegas):
    def __init__(s, root):
        s.root = root; s.n = sn.numatytieji(); s.n["kalba"] = os.environ.get("KALBA", s.n["kalba"]); s.k = 1.0; s.P = 2
        s.uzvesta = set(); s.sasajos_karta = 0; s.sasaja = None; s.plociu_praejimas = True
        s.perziuru_plociai = {}; s.vartotojas_paslepe = False; s.paskutine_klaida = None; s.windows_trynimai = 0
        s.baigiama = False
    def __getattr__(s, k):
        if k.startswith("__"): raise AttributeError(k)
        m = mock.MagicMock(name=k); object.__setattr__(s, k, m); return m
if os.environ.get("KALBA"): sn.nustatyti_kalba(os.environ["KALBA"])
root = tk.Tk(); root.geometry("+0+0")
a = B(root)
for vardas in ("animuoti_uzvedus", "atideti", "pritaikyti_perziuru_plocius"):
    setattr(a, vardas, lambda *x, **k: None)
sn.autostartas_ijungtas = lambda: None
try:
    a.kurti_sasaja()
except Exception:
    import traceback; traceback.print_exc()
for _ in range(30): root.update(); time.sleep(0.02)
w, h = root.winfo_reqwidth(), root.winfo_reqheight()
subprocess.run(["import", "-window", "root", "-crop", f"{w}x{h}+0+0", sys.argv[2]])
print("dydis", w, h)
