"""Sniego lietuviškų tekstų .po byla: python po_eksportas.py Sniegas.pyw išvestis.po
msgid = dabartinis tekstas (pagal jį randama vieta kode), msgstr = tas pats (taisoma ji), #. EN: – angliškas vertimas."""
import ast, re, sys
byla, isvestis = sys.argv[1], sys.argv[2]
src = open(byla, encoding="utf-8").read(); t = ast.parse(src)
versija = re.search(r'^VERSIJA = "([^"]+)"', src, re.M).group(1); data = re.search(r'^DATA = "([^"]+)"', src, re.M).group(1)
en_n = [n for n in t.body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "EN"][0]
EN = [(k.value, v.value) for k, v in zip(en_n.value.args[0].keys, en_n.value.args[0].values)]
vietos = {}
for n in ast.walk(t):
    if isinstance(n, ast.Constant) and isinstance(n.value, str) and not (en_n.lineno <= n.lineno <= en_n.end_lineno):
        vietos.setdefault(n.value, []).append(n.lineno)
def esc(s): return s.replace("\\", "\\\\").replace('"', '\\"').replace("\t", "\\t")
def po(s):
    if "\n" not in s:
        return '"' + esc(s) + '"'
    d = s.split("\n")
    return "\n".join(['""'] + ['"' + esc(p) + ("\\n" if i < len(d) - 1 else "") + '"' for i, p in enumerate(d) if p or i < len(d) - 1])
L = [f"# Sniego programos lietuviški tekstai ({versija}, {data}).",
     "# Taisykite TIK msgstr eilutes (msgid – dabartinis tekstas, pagal jį randama vieta kode).",
     "# Palikite nepakeistus {vardus} riestiniuose skliaustuose ir \\n (eilutės lūžius).",
     "# „#. EN:“ – dabartinis angliškas vertimas (jei keičiasi prasmė – pataisysiu ir jį).",
     'msgid ""', 'msgstr ""', f'"Project-Id-Version: Sniegas {versija}\\n"', '"Language: lt\\n"',
     '"MIME-Version: 1.0\\n"', '"Content-Type: text/plain; charset=UTF-8\\n"', '"Content-Transfer-Encoding: 8bit\\n"', ""]
for k, v in sorted(EN, key=lambda kv: (min(vietos.get(kv[0], [10 ** 9])), kv[0])):
    L.append("#. EN: " + v.replace("\n", " ⏎ "))
    if k in vietos:
        L.append("#: " + " ".join(f"Sniegas.pyw:{x}" for x in sorted(set(vietos[k]))[:4]))
    if re.search(r"\{[a-z_0-9]*\}", k):
        L.append("#, python-brace-format")
    L += ["msgid " + po(k), "msgstr " + po(k), ""]
open(isvestis, "w", encoding="utf-8").write("\n".join(L))
print(len(EN), "tekstų →", isvestis)
