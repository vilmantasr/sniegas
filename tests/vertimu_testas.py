"""12.37: kiekvienas sąsajos tekstas turi angliškąjį vertimą, ir nėra nenaudojamų vertimų (kad .po byla atitiktų kodą)."""
import sys, ast
byla = sys.argv[1]
src = open(byla, encoding="utf-8").read()
t = ast.parse(src)
REZ = []
def tikrinti(pav, sal, info=""):
    REZ.append(bool(sal)); print(("  OK  " if sal else "  KLAIDA ") + pav + (f"  [{info}]" if info else ""))
en_n = [n for n in t.body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "EN"][0]
EN = {k.value for k in en_n.value.args[0].keys}
naudojami = set()
for n in ast.walk(t):  # T("...")
    if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "T" and n.args and isinstance(n.args[0], ast.Constant):
        naudojami.add(n.args[0].value)
for n in t.body:  # APRASAI ir tekstų rinkiniai, verčiami per T(kintamasis)
    if isinstance(n, ast.Assign):
        vardas = ast.unparse(n.targets[0])
        if vardas == "APRASAI" or vardas.endswith(("_TEKSTAI", "_PAVADINIMAI")) or vardas in ("PARUOSTUKAI", "PARUOSTUKU_PLYTOS"):
            v = n.value.args[0] if isinstance(n.value, ast.Call) and n.value.args else n.value
            if vardas == "APRASAI":
                elementai = v.values
            elif vardas == "PARUOSTUKAI":
                elementai = [e.elts[0] for e in v.elts]
            elif vardas == "PARUOSTUKU_PLYTOS":
                elementai = [e.elts[1] for e in v.elts]
            else:
                elementai = [v]
            for e in elementai:
                for c in ast.walk(e):
                    if isinstance(c, ast.Constant) and isinstance(c.value, str):
                        naudojami.add(c.value)
truksta = sorted(s for s in naudojami if s not in EN and any(ch.isalpha() for ch in s))
tikrinti("visi sąsajos tekstai turi EN vertimą", not truksta, truksta[:5])
kitur = set()
for n in ast.walk(t):
    if isinstance(n, ast.Constant) and isinstance(n.value, str) and not (en_n.lineno <= n.lineno <= en_n.end_lineno):
        kitur.add(n.value)
nenaudojami = sorted(k for k in EN if k not in kitur)
tikrinti("nėra nenaudojamų vertimų", not nenaudojami, nenaudojami[:5])
print(f"{sum(REZ)}/{len(REZ)}")
