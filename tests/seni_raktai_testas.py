"""12.32: sena nustatymų byla su „ekskavatoriai“ raktais – reikšmės perkeliamos į „valytuvai“."""
import sys, ctypes, importlib.util, importlib.machinery, json, tempfile, pathlib
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
sn.messagebox = mock.MagicMock()
with tempfile.TemporaryDirectory() as d:
    p = pathlib.Path(d) / "s.json"
    p.write_text(json.dumps({"ekskavatoriai": False, "ekskavatoriu_kiekis": 5, "ekskavatoriu_dydis": 150}), encoding="utf-8")
    n = B().ikelti_nustatymus(importuojama=str(p))
    tikrinti("seni raktai perkelti", (n["valytuvai"], n["valytuvu_kiekis"], n["valytuvu_dydis"]) == (False, 5, 150),
             (n["valytuvai"], n["valytuvu_kiekis"], n["valytuvu_dydis"]))
    tikrinti("senų raktų nebelieka", not any(k.startswith("ekskav") for k in n))
    p.write_text(json.dumps({"ekskavatoriu_kiekis": 5, "valytuvu_kiekis": 2}), encoding="utf-8")
    n = B().ikelti_nustatymus(importuojama=str(p))
    tikrinti("jei yra ir naujas – naudojamas naujas", n["valytuvu_kiekis"] == 2)
tikrinti("numatytuosiuose ir paruoštukuose – tik nauji raktai",
         not any("ekskav" in k for k in sn.NUMATYTI) and not any("ekskav" in k for _, p_ , *_ in sn.PARUOSTUKAI
                                                                 for k in (p_ if isinstance(p_, dict) else {})))
print(f"{sum(REZ)}/{len(REZ)}")
