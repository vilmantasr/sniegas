import faulthandler; faulthandler.dump_traceback_later(int(__import__("os").environ.get("FH","40")), exit=True)
import shutil, sys, tempfile, os
_d = tempfile.mkdtemp(); _b = os.path.join(_d, "Sniegas.pyw"); shutil.copy(sys.argv[1], _b); sys.argv[1] = _b
_cia = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(_cia, "dumas.py"), encoding="utf-8").read())
import tkinter as tk
_wa = tk.Wm.wm_attributes
def wa(self, *a, **k):
    if a and a[0] in ("-transparentcolor", "-toolwindow", "-disabled"): return ""
    return _wa(self, *a, **k)
tk.Wm.wm_attributes = wa; tk.Wm.attributes = wa
_ib = tk.Wm.wm_iconbitmap
tk.Wm.wm_iconbitmap = tk.Wm.iconbitmap = lambda self, *a, **k: None
sn.gauti_monitorius = lambda: [((0, 0, 1920, 1080), (0, 0, 1920, 1040))]
root = tk.Tk(); root.withdraw()
KLAIDOS = []
root.report_callback_exception = lambda *e: KLAIDOS.append("".join(traceback.format_exception(*e)))
try:
    a = sn.Sniegas(root, False)
    print("SUKURTA")
except Exception:
    traceback.print_exc(); sys.exit(1)
exec(open(os.path.join(_cia, "scenarijus.py"), encoding="utf-8").read())
