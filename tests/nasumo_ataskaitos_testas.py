"""12.33: našumo testo ataskaita – atstatymo stulpeliai ir įverčiai."""
import sys, ctypes, importlib.util, importlib.machinery, time
from unittest import mock
ctypes.windll = mock.MagicMock(); sys.modules["winreg"] = mock.MagicMock(); ctypes.WINFUNCTYPE = ctypes.CFUNCTYPE
byla = sys.argv[1]
spec = importlib.util.spec_from_file_location("sn", byla, loader=importlib.machinery.SourceFileLoader("sn", byla))
sn = importlib.util.module_from_spec(spec); sys.modules["sn"] = sn; spec.loader.exec_module(sn)
REZ = []
def tikrinti(pav, sal, info=""):
    REZ.append(bool(sal)); print(("  OK  " if sal else "  KLAIDA ") + pav + (f"  [{info}]" if info else ""))
class B(sn.Sniegas):
    def __init__(s): pass
    def __getattr__(s, k):
        if k.startswith("__"): raise AttributeError(k)
        m = mock.MagicMock(name=k); object.__setattr__(s, k, m); return m
sn.proceso_busena = lambda: (0, 0, 0, 1.0); sn.ekrano_daznis = lambda: 60
a = B(); a.diag_ekranai = lambda *x: "1920x1200@0,0"; a.testo_etapas = lambda i: None
a.kaina_atstatymo, a.kaina_pilno_atst = 0.006, 1.9
a.testas = {"matas0": (time.perf_counter() - 20, 0.0), "meginiai": [], "rez": [], "pradzia": "x", "gpu": "",
            "etapai": [("Programa paslėpta (bazė)", None, None), ("+ bumbuliukai", {}, None)]}
a.testas["rez"].append({"pav": "Programa paslėpta (bazė)", "ks": None, "darbas": None, "p95": None, "fizika": None,
                        "piesimas": None, "ekranas": None, "cpu": 1, "w": None, "mhz": None})
# 60 kadrų: 40 pilnų, 20 dalinių po 200 stačiakampių
a.testo_matas = [(6.0, 0.8, 4.0, 1.7, 0.1, 1.9, True, 230)] * 40 + [(5.0, 0.8, 3.0, 1.7, 0.1, 1.0, False, 200)] * 20
a.testo_irasyti(1)
r = a.testas["rez"][-1]
tikrinti("pilni % = 67", round(r["pilni"]) == 67, r["pilni"])
tikrinti("stačiakampių (kai ne visas) = 200", r["stac"] == 200)
tekstas = a.nasumo_ataskaita(a.testas)
print(tekstas)
eil = [e for e in tekstas.splitlines() if e.startswith("+ bumbuliukai")]
tikrinti("lentelėje – pilni % ir stač.", eil and " 67 " in eil[0] and " 200 " in eil[0], eil)
tikrinti("įverčių skyrius", "vieno stačiakampio 6.0 µs, viso buferio 1.90 ms" in tekstas)
print(f"{sum(REZ)}/{len(REZ)}")
