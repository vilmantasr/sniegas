"""Angliškų vertimų .po: python po_en.py eksportuoti Sniegas.pyw išvestis.po
                        python po_en.py pritaikyti Sniegas.pyw pataisos.po
msgid – lietuviškas originalas (nekeičiamas), msgstr – angliškas vertimas (taisomas)."""
import ast, re, sys
veiksmas, byla, po_byla = sys.argv[1:4]
src = open(byla, encoding="utf-8").read(); t = ast.parse(src)
en_n = [n for n in t.body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "EN"][0]
poros = list(zip(en_n.value.args[0].keys, en_n.value.args[0].values))
if veiksmas == "eksportuoti":
    versija = re.search(r'^VERSIJA = "([^"]+)"', src, re.M).group(1)
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
    L = [f"# Sniegas {versija} – English UI translation. Source (msgid) is Lithuanian; edit msgstr only.",
         "# Sniego programos angliški tekstai: msgid – lietuviškas originalas (nekeisti), taisoma tik msgstr.",
         "# Keep {placeholders} and \\n unchanged. Context: Windows desktop snow overlay with settings window.",
         'msgid ""', 'msgstr ""', f'"Project-Id-Version: Sniegas {versija}\\n"', '"Language: en\\n"',
         '"MIME-Version: 1.0\\n"', '"Content-Type: text/plain; charset=UTF-8\\n"', '"Content-Transfer-Encoding: 8bit\\n"', ""]
    for k, v in sorted(poros, key=lambda kv: (min(vietos.get(kv[0].value, [10 ** 9])), kv[0].value)):
        k, v = k.value, v.value
        if k in vietos:
            L.append("#: " + " ".join(f"Sniegas.pyw:{x}" for x in sorted(set(vietos[k]))[:4]))
        if re.search(r"\{[a-z_0-9]*\}", k):
            L.append("#, python-brace-format")
        L += ["msgid " + po(k), "msgstr " + po(v), ""]
    open(po_byla, "w", encoding="utf-8").write("\n".join(L))
    print(len(poros), "vertimų →", po_byla)
else:
    import polib
    nauji = {e.msgid: e.msgstr for e in polib.pofile(po_byla) if e.msgstr}
    b_src = src.encode("utf-8")
    eil = src.splitlines(keepends=True); pos = [0]
    for e in eil:
        pos.append(pos[-1] + len(e.encode("utf-8")))
    vietos, keista = [], 0
    for k, v in poros:
        if k.value in nauji and nauji[k.value] != v.value:
            if sorted(re.findall(r"\{[a-z_0-9]*\}", k.value)) != sorted(re.findall(r"\{[a-z_0-9]*\}", nauji[k.value])):
                sys.exit(f"KLAIDA: {{vardai}} nesutampa: {k.value!r} → {nauji[k.value]!r}")
            a, b = pos[v.lineno - 1] + v.col_offset, pos[v.end_lineno - 1] + v.end_col_offset
            r = '"' + nauji[k.value].replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'
            vietos.append((a, b, r)); keista += 1
    for a, b, r in sorted(vietos, reverse=True):
        b_src = b_src[:a] + r.encode("utf-8") + b_src[b:]
    ast.parse(b_src.decode("utf-8"))
    open(byla, "w", encoding="utf-8").write(b_src.decode("utf-8"))
    print("pakeista vertimų:", keista)
