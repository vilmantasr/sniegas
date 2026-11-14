"""Dūmų testas: visa programa su netikru Windows API (visos funkcijos grąžina skaičių), tikras Tk (Xvfb)."""
import types
import sys, ctypes, importlib.util, importlib.machinery, random, time, traceback, os, tempfile
class F:
    def __init__(s, name): s.name = name; s.argtypes = None; s.restype = None; s.kv = 0
    def __call__(s, *a):
        s.kv += 1
        KV[s.name] = KV.get(s.name, 0) + 1
        r = SPEC.get(s.name)
        return r(*a) if callable(r) else ((0 if s.name.startswith('Gdip') else 1) if r is None else r)
class Lib:
    def __init__(s, n): s._n = n; s._f = {}
    def __getattr__(s, k):
        if k.startswith("__"): raise AttributeError(k)
        if k in NERA: raise AttributeError(k)
        f = s._f.get(k)
        if f is None: f = s._f[k] = F(k)
        return f
class W:
    def __init__(s): s._l = {}
    def __getattr__(s, k):
        if k.startswith("__"): raise AttributeError(k)
        return s._l.setdefault(k, Lib(k))
KV = {}; NERA = set()
h = [1000]
GYVI = {}
def nauja(*a): h[0] += 1; return h[0]
def kur(rusis):
    def f(*a):
        h[0] += 1; GYVI[h[0]] = rusis; return h[0]
    return f
def trinti(x):
    return 1 if GYVI.pop(x, None) is not None else 1
BLOGI = {}
def blogas(kas, *a):
    import traceback as tb
    vieta = [f for f in tb.extract_stack() if f.filename.endswith("Sniegas.pyw")][-1]
    BLOGI.setdefault((kas, vieta.lineno), [0, a, vieta.name])[0] += 1
DCB = {}  # dc → (w, h) pasirinkto paveikslėlio
BMP = {}
def ccb(dc, w, h):
    hh = kur("bmp")()
    if not (0 < w <= 32767 and 0 < h <= 32767) or w * h > 150_000_000: blogas("CreateCompatibleBitmap dydis", w, h)
    BMP[hh] = (w, h); return hh
def selobj(dc, o):
    if o in BMP: DCB[dc] = BMP[o]
    return 7
def bitblt(d, x, y, w, h, s_, sx, sy, rop):
    if w <= 0 or h <= 0: blogas("BitBlt tuščias", w, h)
    if s_ in DCB and (sx < 0 or sy < 0 or sx + w > DCB[s_][0] or sy + h > DCB[s_][1]): blogas("BitBlt už šaltinio ribų", x, y, w, h, sx, sy, DCB[s_])
    return 1
def tblt(d, x, y, w, h, s_, sx, sy, sw, sh, c):
    if w <= 0 or h <= 0 or sw <= 0 or sh <= 0: blogas("TransparentBlt tuščias", w, h, sw, sh)
    if s_ in DCB and (sx < 0 or sy < 0 or sx + sw > DCB[s_][0] or sy + sh > DCB[s_][1]): blogas("TransparentBlt už šaltinio ribų", sx, sy, sw, sh, DCB[s_])
    return 1
def fillrect(dc, r, br):
    r = getattr(r, "_obj", r)
    if r.right < r.left or r.bottom < r.top: blogas("FillRect apverstas", r.left, r.top, r.right, r.bottom)
    if max(abs(r.left), abs(r.right), abs(r.top), abs(r.bottom)) > 30000: blogas("FillRect milžiniškas", r.left, r.top, r.right, r.bottom)
    if not br: blogas("FillRect be teptuko")
    return 1
def polygon(dc, arr, n):
    if n < 3: blogas("Polygon < 3 taškų", n)
    if any(abs(v) > 30000 for v in arr[:2 * n]): blogas("Polygon milžiniškas", n)
    return 1
def polyline(dc, arr, n):
    if n < 2: blogas("Polyline < 2 taškų", n)
    return 1
SPEC = {"CreateCompatibleDC": kur("dc"), "CreateCompatibleBitmap": ccb, "BitBlt": bitblt, "TransparentBlt": tblt, "FillRect": fillrect, "Polygon": polygon, "Polyline": polyline, "CreateSolidBrush": kur("tept"), "CreatePen": kur("piest"), "DeleteObject": trinti, "DeleteDC": trinti, "CreateRectRgn": kur("rgn"), "CreateFontW": kur("font"), "DestroyIcon": trinti,
        "GetDC": nauja, "SelectObject": selobj, "GetStockObject": 5, "CreateMutexW": 11, "GetDpiForWindow": 96,
        "GetForegroundWindow": 0, "EnumWindows": 1, "GetAncestor": 0, "GetParent": 0, "IsWindow": 1, "IsIconic": 0, "IsZoomed": 0,
        "DwmGetWindowAttribute": 1, "GetLastError": 0, "RegisterWindowMessageW": 50000, "SetWinEventHook": nauja,
        "CallWindowProcW": 0, "DefWindowProcW": 0, "GetSystemMetrics": 32, "CreateDIBSection": kur("dib"), "timeBeginPeriod": 0,
        "GdiplusStartup": 0, "Shell_NotifyIconW": 1, "CreateIconFromResourceEx": kur("ikona"), "CreateIcon": kur("ikona"),
         "GetCurrentThreadId": 1, "GetCurrentProcessId": 1, "AvSetMmThreadCharacteristicsW": 0}
ctypes.windll = W(); ctypes.WINFUNCTYPE = ctypes.CFUNCTYPE
ctypes.WinDLL = lambda *a, **k: Lib("x")
ctypes.get_last_error = lambda: 0; ctypes.set_last_error = lambda v: None
sys.platform = "win32"; sys.getwindowsversion = lambda: types.SimpleNamespace(build=26100, major=10, minor=0); import types

wr = types.ModuleType("winreg")
class _K:
    def __enter__(s): return s
    def __exit__(s, *a): return False
def _raise(*a, **k): raise FileNotFoundError
for n in ("OpenKey", "QueryValueEx", "CreateKey", "SetValueEx", "DeleteValue", "CloseKey"): setattr(wr, n, _raise)
wr.HKEY_CURRENT_USER = 1; wr.KEY_READ = 1; wr.KEY_SET_VALUE = 2; wr.REG_SZ = 1; wr.KEY_WRITE = 2
sys.modules["winreg"] = wr
byla = sys.argv[1]
tmp = tempfile.mkdtemp()
os.environ["APPDATA"] = tmp; os.environ["LOCALAPPDATA"] = tmp
spec = importlib.util.spec_from_file_location("sn", byla, loader=importlib.machinery.SourceFileLoader("sn", byla))
sn = importlib.util.module_from_spec(spec); sys.modules["sn"] = sn; spec.loader.exec_module(sn)
