"""Pataisytos .po bylos tekstai – į kodą: python po_pritaikymas.py Sniegas.pyw pataisos.po
Kiekvienas tekstas, kurio msgstr skiriasi nuo msgid, pakeičiamas visose kodo vietose (ir EN rakte). {vardai} turi likti."""
import ast, re, sys, polib
byla, po_byla = sys.argv[1], sys.argv[2]
src = open(byla, encoding="utf-8").read()
pakeitimai = {e.msgid: e.msgstr for e in polib.pofile(po_byla) if e.msgstr and e.msgstr != e.msgid}
for a, b in pakeitimai.items():
    va, vb = sorted(re.findall(r"\{[a-z_0-9]*\}", a)), sorted(re.findall(r"\{[a-z_0-9]*\}", b))
    if va != vb:
        sys.exit(f"KLAIDA: pakeisti {{vardai}}: {a!r} → {b!r}")
t = ast.parse(src)
eil = src.splitlines(keepends=True)
poslinkiai = [0]
for e in eil:
    poslinkiai.append(poslinkiai[-1] + len(e.encode("utf-8")))
b_src = src.encode("utf-8")
def pozicija(l, c):  # ast col_offset – baitais
    return poslinkiai[l - 1] + c
def literalas(tekstas, stulp, kelios):
    """Python eilutės literalas; ilgas – keliomis dalimis (kaip buvo), sulygiuotomis po pirmąja."""
    def r(x):
        return '"' + x.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'
    if not kelios or len(tekstas) < 90:
        return r(tekstas)
    dalys, d = [], ""
    for zodis in re.split(r"(?<= )", tekstas):
        if len(d) + len(zodis) > 100 and d:
            dalys.append(d); d = ""
        d += zodis
    dalys.append(d)
    return ("\n" + " " * stulp).join(r(x) for x in dalys)
vietos = []
for n in ast.walk(t):
    if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value in pakeitimai:
        a, b = pozicija(n.lineno, n.col_offset), pozicija(n.end_lineno, n.end_col_offset)
        stulp = len(b_src[poslinkiai[n.lineno - 1]:a].decode("utf-8"))
        vietos.append((a, b, literalas(pakeitimai[n.value], stulp, n.end_lineno > n.lineno)))
for a, b, naujas in sorted(vietos, reverse=True):
    b_src = b_src[:a] + naujas.encode("utf-8") + b_src[b:]
naujas_src = b_src.decode("utf-8")
ast.parse(naujas_src)
rasta = {n.value for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Constant) and n.value in pakeitimai}
open(byla, "w", encoding="utf-8").write(naujas_src)
print(f"pakeista tekstų: {len(rasta)} iš {len(pakeitimai)}, vietų kode: {len(vietos)}")
for x in pakeitimai:
    if x not in rasta:
        print("  NERASTA:", x[:80])
