"""12.32: rinkimas skaičių laukeliuose (Xvfb) – tarpinės reikšmės netaikomos, ribos – išėjus / Enter."""
import sys, ctypes, importlib.util, importlib.machinery, time
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
        s.uzvesta = set(); s.sasajos_karta = 0
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
def atn():
    for _ in range(5): root.update(); time.sleep(0.01)
FOK = [None]
root.focus_get = lambda: FOK[0]  # Xvfb be langų tvarkyklės fokuso neperduoda – imituojama
def fokusas(r):
    FOK[0] = a.valdikliai[r]; atn()
def tikrinimas(r):
    kom, _ = a.valdikliai[r].cget("validatecommand").split()[:2] if isinstance(a.valdikliai[r].cget("validatecommand"), str) else a.valdikliai[r].cget("validatecommand")[:2]
    return lambda t: root.tk.call(str(kom), t) in (1, "1", True)
print("1. Vienas laukelis (eglių aukštis 16–250)")
a.n["egliu_atsitiktinis"] = False
fokusas("egliu_aukstis"); v = a.kint["egliu_aukstis"]; buvo = a.n["egliu_aukstis"]
v.set("1"); atn(); tikrinti("„1“ (< 16) – dar netaikoma", a.n["egliu_aukstis"] == buvo, a.n["egliu_aukstis"])
v.set("15"); atn(); tikrinti("„15“ – dar netaikoma", a.n["egliu_aukstis"] == buvo)
v.set("150"); atn(); tikrinti("„150“ – pritaikoma iš karto", a.n["egliu_aukstis"] == 150)
v.set("5"); atn(); tikrinti("„5“ – netaikoma, rodoma kaip surinkta", a.n["egliu_aukstis"] == 150 and v.get() == "5")
a.baigti_ivedima("egliu_aukstis"); atn()
tikrinti("Enter / išėjus – apribojama iki 16 ir parodoma", a.n["egliu_aukstis"] == 16 and v.get() == "16", v.get())
v.set(""); a.baigti_ivedima("egliu_aukstis"); atn()
tikrinti("tuščias – grąžinama galiojanti", v.get() == "16")
print("2. Eglių ribos 60–70 → norima 80–120, pradedant nuo mažiausio")
a.kint["egliu_max"].set("70"); a.kint["egliu_min"].set("60"); atn()
tikrinti("ribos 60–70", (a.n["egliu_min"], a.n["egliu_max"]) == (60, 70))
tk_ = tikrinimas("egliu_min")
tikrinti("mažiausiajame galima surinkti „80“ (anksčiau – atmetama)", tk_("8") and tk_("80"))
tikrinti("bet ne daugiau už absoliučią ribą (249)", not tk_("250"))
fokusas("egliu_min"); a.kint["egliu_min"].set("80"); atn()
tikrinti("renkant „80“ – dar netaikoma", a.n["egliu_min"] == 60)
fokusas("egliu_max"); a.baigti_ivedima("egliu_min"); atn()
tikrinti("išėjus – mažiausias apribotas iki 69", a.n["egliu_min"] == 69 and a.kint["egliu_min"].get() == "69")
a.kint["egliu_max"].set("120"); a.kint["egliu_min"].set("80"); atn()
tikrinti("tada 80–120 nustatoma", (a.n["egliu_min"], a.n["egliu_max"]) == (80, 120))
print("3. Ne renkant (juosta / rodyklės) – taikoma ir apribojama iš karto")
fokusas("egliu_kiekis"); a.kint["egliu_aukstis"].set("999"); atn()
tikrinti("fokusas kitur: 999 → 250 ir parodoma", a.n["egliu_aukstis"] == 250 and a.kint["egliu_aukstis"].get() == "250")
print(f"{sum(REZ)}/{len(REZ)}")
