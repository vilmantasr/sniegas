from tkinter import messagebox, filedialog
import types as _t
SEKLA = int(os.environ.get("SEKLA", "1")); KADRU = int(os.environ.get("KADRU", "3000"))
rnd = random.Random(SEKLA)
for nm in ("askyesno", "askokcancel"): setattr(messagebox, nm, lambda *a, **k: rnd.random() < 0.7)
for nm in ("showinfo", "showerror", "showwarning"): setattr(messagebox, nm, lambda *a, **k: None)
filedialog.asksaveasfilename = lambda *a, **k: os.path.join(_d, "eksp.json")
filedialog.askopenfilename = lambda *a, **k: os.path.join(_d, "eksp.json") if os.path.exists(os.path.join(_d, "eksp.json")) else ""
ZK = []
_r = sn.ZURNALAS.rasyti
def rasyti(tekstas, visada=False):
    if (tekstas.startswith("KLAIDA") or "Traceback" in tekstas or "NEPAGAUTA" in tekstas) and "GLOTNUS JUD" not in tekstas: ZK.append(tekstas)
    return None
sn.ZURNALAS.rasyti = rasyti
# netikras laikrodis: kiekvienas kadras – 1/30 s
laikas = [time.perf_counter()]
_pc = time.perf_counter
time.perf_counter = lambda: laikas[0]
# netikri langai
langai = {}
def nauji_langai():
    for h in list(langai):
        if rnd.random() < 0.1: del langai[h]
    while len(langai) < rnd.randint(0, 5):
        l = rnd.randint(-200, 1700); t = rnd.randint(-50, 1000); w = rnd.randint(60, 900)
        langai[rnd.randint(100, 10 ** 9)] = [l, t, l + w, t + rnd.randint(50, 600), rnd.random() < 0.1]
    for v in langai.values():
        if rnd.random() < 0.3:
            dx, dy = rnd.randint(-40, 40), rnd.randint(-40, 40); v[0] += dx; v[2] += dx; v[1] += dy; v[3] += dy
        if rnd.random() < 0.1: v[2] = v[0] + rnd.randint(60, 900)
def enum(cb, lp):
    for h, v in list(langai.items()):
        a.langu_sarasas.append((h, (v[0], v[1], v[2], v[3]), v[4]))
    return 1
SPEC["EnumWindows"] = enum
RAKTAI = [k for k in sn.NUMATYTI if k not in ("kalba", "diagnostika", "tipai", "bumbulu_rastai", "bumbulu_spalvos", "bumbulu_dingimai", "kryzelis")]
def keisti():
    k = rnd.choice(RAKTAI); v0 = sn.NUMATYTI[k]
    if k not in a.kint: return
    if isinstance(v0, bool): nv = rnd.random() < 0.5
    elif isinstance(v0, int):
        if k in sn.RIBOS:
            nuo, iki = a.leistinos(k); nv = rnd.choice((nuo, iki, rnd.randint(nuo, iki), rnd.randint(nuo, iki), nuo - 1, iki + 5))
        elif k == "fps": nv = rnd.choice((30, 60, 120))
        elif k == "egliu_plotis_min": nv = rnd.choice(sn.EGLIU_PLOCIAI)
        else: return
    elif isinstance(v0, str):
        nv = rnd.choice(sn.TEKSTINES_REIKSMES[k]) if k in sn.TEKSTINES_REIKSMES else None
        if nv is None: return
        if k in ("vejo_kryptis", "senio_lempuciu_animacija"):  # per combobox – tiesiogiai
            a.n[k] = nv; return
    else: return
    try: a.kint[k].set(nv if isinstance(v0, bool) else str(nv) if k in sn.RIBOS else nv)
    except Exception: return
    a.pakeista(k); ZURN.append((k, nv))
ZURN = []
class Ev:
    def __init__(s, x, y): s.x = s.x_root = x; s.y = s.y_root = y
def veiksmas():
    r = rnd.random()
    if r < 0.45: keisti()
    elif r < 0.52: a.pritaikyti_paruostuka(rnd.randrange(len(sn.PARUOSTUKAI))); ZURN.append("paruoštukas")
    elif r < 0.54: a.atkurti_numatytuosius(); ZURN.append("numatytieji")
    elif r < 0.60: nauji_langai(); a.langai_judejo = True; ZURN.append("langai")
    elif r < 0.63: a.fejerverkai_dabar(); ZURN.append("fj")
    elif r < 0.64: a.didysis_sou(); ZURN.append("didysis")
    elif r < 0.66: a.fejerverku_mygtukas(); ZURN.append("fj mygt")
    elif r < 0.68: a.nuvalyti(); ZURN.append("nuvalyti")
    elif r < 0.70: a.perjungti_rodyma(); ZURN.append("rodymas")
    elif r < 0.72: a.perjungti_sniega(); ZURN.append("sniegas")
    elif r < 0.74:
        i = rnd.randrange(len(a.n["tipai"])); a.tipu_kint[i].set(str(rnd.choice((0, 1, 50, 300)))) if hasattr(a, "tipu_kint") else None; ZURN.append("tipai")
    elif r < 0.76:
        for raktas in ("bumbulu_rastai", "bumbulu_spalvos"):
            vs = a.tipu_varneles[raktas]; rnd.choice(vs).set(rnd.random() < 0.5); a.pakeisti_tipus(raktas)
        ZURN.append("bumb tipai")
    elif r < 0.78:
        vs = a.tipu_varneles["bumbulu_dingimai"]; rnd.choice(vs).set(rnd.random() < 0.5); a.pakeisti_dingimus(); ZURN.append("dingimai")
    elif r < 0.80: a.perdelioti_egles(nauja_sekla=True); ZURN.append("eglės")
    elif r < 0.82: a.kurti_bumbulus(); ZURN.append("bumbulai")
    elif r < 0.84:
        m = rnd.choice(([((0, 0, 1920, 1080), (0, 0, 1920, 1040))], [((0, 0, 1920, 1080), (0, 0, 1920, 1000))],
                        [((0, 0, 2560, 1440), (0, 0, 2560, 1400)), ((2560, 200, 4480, 1280), (2560, 200, 4480, 1240))],
                        [((0, 0, 1280, 720), (0, 40, 1280, 720))]))
        sn.gauti_monitorius = lambda m=m: m; a.tikrinti_ekranus(); ZURN.append(("ekranai", len(m)))
    elif r < 0.86 and getattr(a, "seniai", None):
        s_ = rnd.choice(a.seniai)
        if s_.get("y") is not None and s_.get("busena") != "nera" and s_.get("rodomas"):
            x, y = int(s_["x"]), int(s_["y"] or 500)
            a.senis_paimtas(s_, Ev(x, y))
            for i in range(rnd.randint(0, 6)): a.senis_tempiamas(s_, Ev(x + rnd.randint(-300, 300), y + rnd.randint(-300, 100)))
            a.senis_paleistas(s_, Ev(x + rnd.randint(-300, 300), y - rnd.randint(0, 300))); ZURN.append("senis")
    elif r < 0.88: a.kalbos_kint.set(rnd.choice(("lt", "en"))); a.pakeista_kalba(); ZURN.append("kalba")
    elif r < 0.90:
        for nm in ("egles", "senis", "bumbulai", "valytuvai", "girliandos", "fejerverkai", "vejas"):
            (a.uzvesta.add if rnd.random() < 0.5 else a.uzvesta.discard)(nm)
        ZURN.append("užvesta")
    elif r < 0.92: a.eksportuoti_nustatymus(); ZURN.append("eksp")
    elif r < 0.94: a.importuoti_nustatymus(); ZURN.append("imp")
    elif r < 0.95: a.be_apribojimu_kint.set(rnd.random() < 0.5); a.perjungti_apribojimus(); ZURN.append("ribos")
    elif r < 0.97:
        k = rnd.choice(list(sn.SKILCIU_NUSTATYMAI)); a.atkurti_skilti(k, k); ZURN.append("atk skiltį")
    else:
        a.vejas = rnd.uniform(-12, 12) if hasattr(a, "vejas") else 0; ZURN.append("vėjas")
a.kadras = lambda: None
AFT = collections.Counter() if 'collections' in dir() else None
import collections as _c
AFT = _c.Counter(); _ra = root.after
def _after(ms, func=None, *args):
    if func is not None:
        nm = getattr(func, "__qualname__", None) or getattr(getattr(func, "func", None), "__qualname__", repr(func))
        code = getattr(func, "__code__", None)
        AFT[(nm, code.co_firstlineno if code else 0, ms if ms in (0, 1) else ">1")] += 1
    return _ra(ms, func, *args)
root.after = _after
if os.environ.get('GYVAS'):
    nn = dict(a.n); nn.update(be_apribojimu=True, sniego_senis=True, senio_kiekis=12, senio_stovi=False, valytuvai=True, valytuvu_kiekis=8,
              bumbulai=True, bumbulu_kiekis=12, egles=True, girliandos=True, vejas=8, gusio_stiprumas=9, gusiai=6, kaupimo_greitis=500,
              fejerverkai=False, sniegas_ant_senio=True, senio_lemputes=True)
    nn["tipai"] = [60] * len(nn["tipai"])
    a.taikyti_nustatymus(nn); nauji_langai(); nauji_langai(); a.langai_judejo = True
    RAKTAI[:] = ["senio_stovi", "vejas", "gusio_stiprumas", "senio_dydis", "valytuvu_dydis", "bumbulu_juda", "bumbulai_languose", "kaupimo_greitis", "max_aukstis", "max_aukstis_languose", "senio_lempuciu_animacija"]
if os.environ.get('DIAG'):
    sn.ZURNALAS.ijungtas = True; a.n['diagnostika'] = True
    try: a.ijungta_diagnostika()
    except Exception: traceback.print_exc()
t0 = _pc(); klaidu = 0
import collections, math
def dydziai():
    d = {}
    for k, v in a.__dict__.items():
        if isinstance(v, (list, dict, set, bytearray)): d[k] = len(v)
    d["GDI"] = len(GYVI)
    for rusis, n_ in collections.Counter(GYVI.values()).items(): d["GDI:" + rusis] = n_
    try: d["tk_after"] = len(root.tk.call("after", "info"))
    except Exception: pass
    for nm in ("egliu_drobe", "senio_drobe", "girl_drobe", "bumbulu_drobe", "valyt_drobe", "fj_drobe", "vejo_drobe"):
        try: d["drobė:" + nm] = len(getattr(a, nm).find_all())
        except Exception: pass
    d["tk_valdikliu"] = sum(1 for _ in root.tk.call("winfo", "children", ".")) 
    return d
ISTORIJA = []
def tikrinti_busena(kadras):
    for vardas in ("aukstis", "kelias"):
        v = getattr(a, vardas, None)
        if v and any((x != x) or x in (float("inf"), float("-inf")) or x < -0.01 for x in v):
            print(f"--- BLOGA REIKŠMĖ {vardas} kadre {kadras}: {ZURN[-6:]}"); return
    for st in a.langai.values():
        if any((x != x) or x < -0.01 or x > 5000 for x in st["h"]):
            print(f"--- BLOGA lango h kadre {kadras}: {ZURN[-6:]}"); return
    for f in a.snaiges:
        if f[sn.SX] != f[sn.SX] or f[sn.SY] != f[sn.SY]:
            print(f"--- NaN snaigė kadre {kadras}: {ZURN[-6:]}"); return
for kadras in range(KADRU):
    laikas[0] += 1 / 30 + rnd.random() * 0.002
    if rnd.random() < 0.02: laikas[0] += rnd.uniform(0.1, 3.0)  # stabtelėjimas
    try:
        if rnd.random() < float(os.environ.get("DAZNIS", "0.08")): veiksmas()
        a._kadras()
        if kadras % 10 == 0: root.update()
    except Exception:
        klaidu += 1
        print(f"--- IŠIMTIS kadre {kadras}, paskutiniai veiksmai: {ZURN[-6:]}"); traceback.print_exc()
        if klaidu > 8: break
    if kadras % 500 == 499: ISTORIJA.append(dydziai()); tikrinti_busena(kadras)
    if ZK:
        print(f"--- ŽURNALO KLAIDA kadre {kadras}, veiksmai: {ZURN[-6:]}"); print("\n".join(z[:3000] for z in ZK)); ZK.clear(); klaidu += 1
        if klaidu > 8: break
    if KLAIDOS:
        print(f"--- TK KLAIDA kadre {kadras}: {ZURN[-6:]}"); print("\n".join(KLAIDOS)); KLAIDOS.clear(); klaidu += 1
print(f"BAIGTA sėkla={SEKLA} kadrų={kadras + 1} klaidų={klaidu} veiksmų={len(ZURN)} trukmė={_pc() - t0:.0f}s GDI kvietimų={sum(KV.values())}")

if len(ISTORIJA) >= 6:
    pr, pb = ISTORIJA[len(ISTORIJA) // 3], ISTORIJA[-1]
    for k in sorted(pb):
        eil = [h_.get(k, 0) for h_ in ISTORIJA]
        if pb.get(k, 0) > 2 * max(50, pr.get(k, 0)) or (k.startswith(("GDI", "tk_")) and pb[k] > 1.5 * pr.get(k, 0) + 30):
            print("AUGA?", k, eil[::max(1, len(eil) // 10)])
    print("GDI pabaigoje:", dict(collections.Counter(GYVI.values())), "tk_after:", pb.get("tk_after"))
if os.environ.get("TESTAS"):
    messagebox.askokcancel = lambda *a_, **k: True; sn.shutil.which = lambda *a_, **k: None
    sn.NASUMO_ISIBEGEJIMAS, sn.NASUMO_MATAVIMAS = 0.02, 0.06
    ZK.clear(); KLAIDOS.clear()
    try:
        a.nasumo_testas()
        for i in range(4000):
            laikas[0] += 1 / 30
            a._kadras()
            if i % 3 == 0: root.update()
            if not a.__dict__.get("testas"): break
            time.sleep(0.002)
        print("našumo testas baigtas po", i, "kadrų; byla yra:", sn.NASUMO_BYLA.exists())
        if sn.NASUMO_BYLA.exists(): print(sn.NASUMO_BYLA.read_text(encoding="utf-8")[:2500])
    except Exception: traceback.print_exc()
    print("ZK:", ZK[:3], "TK:", KLAIDOS[:3])
if os.environ.get("BAIGTI"):
    try: a.baigti(); print("baigti() OK; GDI liko:", dict(collections.Counter(GYVI.values())))
    except Exception: traceback.print_exc()

for (kas, eil_), (kiek, arg, fn) in sorted(BLOGI.items(), key=lambda x: -x[1][0])[:25]:
    print(f"BLOGAS GDI: {kas} ×{kiek} eil. {eil_} ({fn}) pvz. {arg}")

print("after tvarkaraštis (dažniausi):", AFT.most_common(12))
