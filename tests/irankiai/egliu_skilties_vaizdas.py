"""Eglučių skiltis atskirai (Xvfb): kurti_egliu_skilti ant tikro Tk, likusi programa – mock."""
import sys, ctypes, importlib.util, importlib.machinery, subprocess, time
from unittest import mock
ctypes.windll = mock.MagicMock(); sys.modules["winreg"] = mock.MagicMock(); ctypes.WINFUNCTYPE = ctypes.CFUNCTYPE
byla = sys.argv[1]
spec = importlib.util.spec_from_file_location("sn", byla, loader=importlib.machinery.SourceFileLoader("sn", byla))
sn = importlib.util.module_from_spec(spec); sys.modules["sn"] = sn; spec.loader.exec_module(sn)
import tkinter as tk
from tkinter import ttk
REZ = []
def tikrinti(pav, sal, info=""):
    REZ.append(bool(sal)); print(("  OK  " if sal else "  KLAIDA ") + pav + (f"  [{info}]" if info else ""))
class B(sn.Sniegas):
    def __init__(s, root):
        s.root = root; s.n = sn.numatytieji(); s.k = 1.0; s.P = 2
        s.kint, s.valdikliai, s.etiketes, s.skiltys = {}, {}, {}, {}
        s.uzvesta = set(); s.sasajos_karta = 0; s.slinkties_stilius_sukurtas = False
    def __getattr__(s, k):
        if k.startswith("__"): raise AttributeError(k)
        m = mock.MagicMock(name=k); object.__setattr__(s, k, m); return m
root = tk.Tk(); root.geometry("+0+0")
a = B(root)
for vardas in ("piesti_egliu_perziura", "animuoti_uzvedus", "skilties_ikona", "atnaujinti_paruostukus", "atideti",
               "perdelioti_egles", "atnaujinti_skiltis", "atnaujinti_ispejimus"):
    setattr(a, vardas, lambda *x, **k: None)
tevas = ttk.Frame(root, padding=6); tevas.pack()
a.kurti_egliu_skilti(tevas)
a.atnaujinti_egliu_valdiklius()
def nuotrauka(kelias):
    for _ in range(20): root.update(); time.sleep(0.02)
    subprocess.run(["import", "-window", "root", "-crop", f"{tevas.winfo_reqwidth()}x{tevas.winfo_reqheight()}+0+0", kelias])
    return tevas.winfo_reqheight()
h1 = nuotrauka(sys.argv[2] + "_atsitiktinis.png")
tikrinti("atsitiktinis: matosi „nuo–iki“, nesimato vienodo aukščio", a.etiketes["egliu_min"].winfo_ismapped()
         and not a.etiketes["egliu_aukstis"].winfo_ismapped())
a.kint["egliu_atsitiktinis"].set(False); a.pakeista("egliu_atsitiktinis")
h2 = nuotrauka(sys.argv[2] + "_vienodas.png"); w_v = tevas.winfo_reqwidth()
tikrinti("vienodas: matosi aukštis su juosta, nesimato „nuo–iki“", a.etiketes["egliu_aukstis"].winfo_ismapped()
         and not a.etiketes["egliu_min"].winfo_ismapped())
tikrinti("abiem atvejais tas pats aukštis (eilutė ta pati)", h1 == h2, f"{h1} / {h2}")
x_v = a.valdikliai["egliu_kiekis"].master.winfo_x()
a.kint["egliu_atsitiktinis"].set(True); a.pakeista("egliu_atsitiktinis")
for _ in range(10): root.update()
x_a = a.valdikliai["egliu_kiekis"].master.winfo_x()
tikrinti("perjungiant – antras stulpelis nepasislenka", x_v == x_a, f"{x_v} / {x_a}")
tikrinti("ir skilties plotis tas pats", tevas.winfo_reqwidth() == w_v, f"{w_v} / {tevas.winfo_reqwidth()}")
a.kint["egliu_atsitiktinis"].set(True); a.pakeista("egliu_atsitiktinis")
sb = a.valdikliai["egliu_min"]
tikrinti("mažiausio rodyklės – iki 119", str(sb.cget("to")) in ("119", "119.0"), sb.cget("to"))
sbx = a.valdikliai["egliu_max"]
tikrinti("didžiausio rodyklės – nuo mažiausio + 1 (61)", str(sbx.cget("from")) in ("61", "61.0"), sbx.cget("from"))
a.kint["egliu_min"].set("30"); a.kint["egliu_max"].set("40")
for r in ("egliu_max", "egliu_min", "egliu_max"): a.kint[r].set(str(sn.NUMATYTI[r]))
tikrinti("numatytosios grąžinamos ir iš siauros poros (30–40 → 60–120)", (a.n["egliu_min"], a.n["egliu_max"]) == (60, 120),
         f'{a.n["egliu_min"]}–{a.n["egliu_max"]}')
print(f"{sum(REZ)}/{len(REZ)}")
