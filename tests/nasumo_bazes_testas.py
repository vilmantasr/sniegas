"""12.35: bazė matuojama ir pabaigoje; galios palyginimas – su mažesniąja."""
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
    def __init__(s): pass
    def __getattr__(s, k):
        if k.startswith("__"): raise AttributeError(k)
        m = mock.MagicMock(name=k); object.__setattr__(s, k, m); return m
sn.ekrano_daznis = lambda: 120
a = B(); a.diag_ekranai = lambda *x: "2560x1440@0,0"
et = a.nasumo_etapai()
tikrinti("paskutinis etapas – vėl paslėpta programa", et[-1][1] is None and et[0][1] is None, et[-1][0])
def r(pav, w, d=3.0, paslepta=False):
    return {"pav": pav, "paslepta": paslepta, "ks": 60.0, "darbas": None if paslepta else d, "p95": 4.0, "fizika": 0.4,
            "piesimas": 2.0, "ekranas": 0.5, "statinis": 0.1, "atstatymas": 0.6, "pilni": 0.0, "stac": 200, "cpu": 20,
            "w": w, "mhz": 400, "kaina_st": 3.1, "kaina_pil": 0.7, "stac_visi": 200}
rez = [r("Programa paslėpta (bazė)", 10.5, paslepta=True), r("Jūsų nustatymai", 8.2), r("Tik sniegas, 60 kadr./s", 11.8),
       r("Tik sniegas, 30 kadr./s", 8.4), r("Programa paslėpta (bazė, pabaigoje)", 7.6, paslepta=True)]
t = a.nasumo_ataskaita({"rez": rez, "pradzia": "x", "gpu": "RTX"})
print(t)
tikrinti("palyginime paslėptas etapas neminimas", "pabaigoje)" not in t.split("Kaina, palyginti")[1].split("Atkūrimo sprendimo")[0])
# 12.42: W palyginimų nebėra (vaizdo plokštės dažnis šokinėja – skirtumai klaidino), lieka tik pastaba
kaina = t.split("Kaina, palyginti")[1].split("Atkūrimo sprendimo")[0]
tikrinti("kainos palyginime W nėra", " W" not in kaina.replace("GPU W", ""))
tikrinti("pastaba apie GPU W parodyta", "tik informacijai" in kaina)
tikrinti("įverčiuose paslėptų etapų nėra", "pabaigoje)" not in t.split("Atkūrimo sprendimo")[1])
print(f"{sum(REZ)}/{len(REZ)}")
