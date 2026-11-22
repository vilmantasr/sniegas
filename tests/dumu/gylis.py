"""Gylio testas (gylio_testas.py): atsitiktinės scenos su keliais langais vienas virš kito, seniais, valytuvais,
bumbuliukais ir jų dalelėmis (konfeti, gabalai, gniūžtės, purslai, gumulai, šukės). Kiekviename kadre užfiksuojama,
kas kokia tvarka nupiešta, ir tikrinama viena taisyklė: kas toliau (aukštesnio lango gylyje), negali būti nupiešta
ant to, kas arčiau (žemesnio lango ar ekrano apačios), jei jų stačiakampiai persidengia (daiktas–daiktas ir
daiktas–dalelė; dalelė–dalelė netikrinama).

„Tiesa“ apie gylį nustatoma nepriklausomai nuo programos žymų: daikto – pagal jo paviršių (langas – jo viršus,
ekrano apačia ir oras – arčiausiai); dalelės – pagal daiktą, prie kurio ji atsirado (kadro pradžioje ar pabaigoje
jo stačiakampis apima dalelės vietą), ties kurio lango viršumi atsirado, nuo kurios dalelės atskilo, o gulinčios –
pagal tai, ant ko guli. Kai kilmė dviprasmiška, naudojama programos žyma (tikrinama bent piešimo tvarka). Paskutinė eilutė – „praėjo/iš viso“."""
import collections
from tkinter import messagebox
for nm in ("showinfo", "showerror", "showwarning"): setattr(messagebox, nm, lambda *a_, **k: None)
ZK = []
sn.ZURNALAS.rasyti = lambda t, visada=False: ZK.append(t) if t.startswith("KLAIDA") else None
laikas = [time.perf_counter()]
sn.time.perf_counter = lambda: laikas[0]
a.kadras = lambda: None
REZ = []
def tikrinti(pav, sal, info=""):
    REZ.append(bool(sal)); print(("  OK  " if sal else "  KLAIDA ") + pav + (f"  [{info}]" if info else ""), flush=True)

ARTI = 1e9  # ekrano apačia ir oras – arčiausiai
PUST = set()  # šio kadro pustomų dalelių id
langai = {}
def enum(cb, lp):
    for h_, v in list(langai.items()):
        a.langu_sarasas.append((h_, tuple(v[:4]), v[4]))
    return 1
SPEC["EnumWindows"] = enum

def daikto_gylis(o):
    pav, st = o.get("pav"), o.get("st")
    return st["t"] if pav and pav[0] == "langas" and st is not None else ARTI

def daikto_deze(o, rusis):
    x, y = o.get("x"), o.get("y")
    if x is None or y is None or o.get("busena") == "nera":
        return None
    if rusis == "senis":
        Ps = a.senio_Ps(o); W, H = sn.SENIO_W * Ps, sn.SENIO_H * Ps
        return (x - W / 2 - 6, y - H - 6, x + W / 2 + 6, y + 6)
    if rusis == "valytuvas":
        Pe = a.valyt_Pe; W, H = sn.VALYT_PLOTIS * Pe, sn.VALYT_AUKSTIS * Pe
        return (x - W / 2 - 6, y - H - 6, x + W / 2 + 6, y + 6)
    r = o.get("r", 10)
    return (x - 2 * r, y - 3 * r, x + 2 * r, y + r)

def daiktai():
    return [("senis", o) for o in a.seniai] + [("valytuvas", o) for o in a.valytuvai] + [("bumbulas", o) for o in a.bumbulai]

def dalelės():
    return list(a.senio_daleles) + list(a.valyt_daleles) + list(a.skeveldros) + list(a.pustomos)

def ore(o):
    return o.get("busena") == "krenta" or bool(o.get("ore"))

def dezes_dabar():
    """Daiktų stačiakampiai ir gylis; ore esančio (krenta, pašokęs) – None: iš kur jo dalelės, nežinoma (nuo lango
    ką tik nukritęs valytuvas ar bumbuliukas dar beria to lango sniegą)."""
    return {id(o): (d, None if ore(o) else daikto_gylis(o)) for rusis, o in daiktai() if (d := daikto_deze(o, rusis))}

def ties_lango(x, y, kitaip):
    """Taškas ties vieno lango viršumi (pvz. valytuvo stumiamas ar per kraštą nustumtas gumulas) – to lango gylis."""
    ties = {st["t"] for st in a.langai.values() if st["l"] - 30 <= x <= st["r"] + 30 and -4 <= st["t"] - y <= 16}
    return ties.pop() if len(ties) == 1 else kitaip

def priskirti_tiesa(dezes_pries, tevai=()):
    PUST.clear(); PUST.update(id(p) for p in a.pustomos)
    """Naujoms dalelėms – gylis daikto, prie kurio jos atsirado (kadro pradžioje ar pabaigoje); gulinčioms – ant ko guli."""
    dezes_po = dezes_dabar()
    for d in dalelės():
        if d.get("guli"):
            an = d.get("ant")
            d["_tiesa"] = an[1]["t"] if an is not None else ties_lango(d["x"], d["y"], ARTI)
            continue
        if "_tiesa" in d:
            continue
        x, y = d.get("x", 0), d.get("y", 0)
        d["_tiesa"] = None  # nežinoma / dviprasmiška – netikrinama
        # tiesa priskiriama tik tada, kai ji vienareikšmė; kitaip (None) tvarka tikrinama pagal programos žymą
        # (daleles_t) – tada tikrinamas bent piešimo tvarkos mechanizmas
        # nuo kitos dalelės atskilęs trupinys (byra) – jos gylyje, jei visos šalia esančios to paties gylio
        if any(abs(hx - x) <= 30 and abs(hy - y) <= 30 for hx, hy in GALVOS):
            continue  # gumulas sutyžo ant senio galvos – purslai senio gylyje (kilmė dviprasmiška – programos žyma)
        tev = {g for tx, ty, g, i_ in tevai if abs(tx - x) <= 12 and abs(ty - y) <= 12} if "kiekis" in d and id(d) not in PUST \
            else set()  # trupiniai – tik sniego gumulų (valyt_daleles), ne pustomas sniegas
        if tev:
            if len(tev) == 1:
                d["_tiesa"] = tev.pop()
            continue
        # daiktai, kurių stačiakampis kadro pradžioje ar pabaigoje apima dalelės vietą; daiktas, kurio gylis per kadrą
        # pasikeitė (ką tik nusileido ar nuo lango nuslydo), – dviprasmiškas
        rado = set(); dvipr = False
        for i_, (bx, g) in list(dezes_po.items()) + list(dezes_pries.items()):
            l, t, r, b = bx
            if l <= x <= r and t <= y <= b:
                g0 = dezes_pries.get(i_, (None, g))[1]; g1 = dezes_po.get(i_, (None, g))[1]
                if g0 != g1:
                    dvipr = True
                else:
                    rado.add(g)
        if dvipr or len(rado) > 1 or None in rado:
            continue
        # ore esančio daikto dalelė, atsiradusi ties lango viršumi (pvz. valytuvo per kraštą nustumtas gumulas, kai
        # valytuvas jau krenta), – dviprasmiška
        if rado:
            g = rado.pop()
            d["_tiesa"] = None if g == ARTI and ties_lango(x, y, None) is not None else g

# Kiekvienas piešimo kvietimas: kurie daiktai ir dalelės jame nupiešti (jų „sena“ – naujas stačiakampis)
PIESIMAS = []
def apgaubti(vardas):
    f = getattr(a, vardas)
    def w(*ar, **kw):
        visi = [o for _, o in daiktai()] + dalelės()
        pries = {id(o): o.get("sena") for o in visi}
        rez = f(*ar, **kw)
        kv = len(PIESIMAS)
        for o in visi:
            sena = o.get("sena")
            if sena is not None and sena is not pries.get(id(o)):
                PIESIMAS.append((kv, sena, o))
        return rez
    setattr(a, vardas, w)
for v in ("piesti_senius", "piesti_gumulus", "piesti_bumbulus_kadre", "piesti_valytuvus", "piesti_pustomas"):
    apgaubti(v)

def tiesa(o):
    if "_tiesa" in o:
        if o["_tiesa"] is None:  # nežinoma – programos žyma (pustomos – tik „is_lango“, kitaip ekrano apačios)
            t = o.get("is_lango") if id(o) in PUST else a.daleles_t(o)
            return ARTI if t is None else t
        return o["_tiesa"]
    return daikto_gylis(o)

def persidengia(p, q):
    return p[0] < q[2] and q[0] < p[2] and p[1] < q[3] and q[1] < p[3]

PAZEIDIMAI = collections.Counter(); PAVYZDZIAI = []
def tikrinti_kadra():
    PUST.clear(); PUST.update(id(p) for p in a.pustomos)
    el = [(kv, r, o, tiesa(o)) for kv, r, o in PIESIMAS]
    for i, (kv1, r1, o1, g1) in enumerate(el):
        for kv2, r2, o2, g2 in el[i + 1:]:
            # o2 nupieštas vėliau (ar tame pačiame kvietime): jis neturi būti toliau nei o1, jei persidengia
            # dalelė ant dalelės netikrinama: taškelis ant taškelio gylio klaidos neparodo, o jų kilmės gylis dažnai
            # dviprasmiškas (keli šaltiniai vienoje vietoje)
            if "_tiesa" in o1 and "_tiesa" in o2:
                continue
            if g2 < g1 - 0.5 and persidengia(r1, r2):
                k_ = ("dalelė" if "_tiesa" in o2 else "daiktas") + " toliau – ant " + ("dalelės" if "_tiesa" in o1 else "daikto")
                PAZEIDIMAI[k_] += 1
                if len(PAZEIDIMAI) and len(PAVYZDZIAI) < 6:
                    def apr(o):
                        return {k: o.get(k) for k in ("tipas", "busena", "l", "is_lango", "guli", "d", "dyd") if o.get(k) is not None}
                    PAVYZDZIAI.append((k_, round(g2), round(g1), apr(o2), apr(o1), kv1, kv2))

GALVOS = []  # šio kadro gumulų ant senių galvų vietos
_sgg = a.senis_gavo_gumula
def _sgg_w(o, d):
    GALVOS.append((d["x"], d["y"])); return _sgg(o, d)
a.senis_gavo_gumula = _sgg_w
def scena(sekla, sek=50):
    random.seed(sekla)
    langai.clear()
    # 3–4 langai pakopomis (aukštesnis – žemiau z tvarkoje, kad visų viršūs matytųsi), persidengiantys
    n = random.randint(3, 4)
    for j in range(n):
        l = random.randint(100, 700) + j * 120; t = 250 + j * random.randint(45, 90)
        langai[100 + j] = [l, t, l + random.randint(700, 1100), t + 500, False]
    # z tvarka: pirmas – viršutinis; žemesnis langas (didesnis t) – virš aukštesnio, kad abiejų viršūs matytųsi
    langai_z = dict(sorted(langai.items(), key=lambda kv: -kv[1][1])); langai.clear(); langai.update(langai_z)
    nn = dict(sn.numatytieji()); nn.update(sniego_senis=True, senio_kiekis=6, senio_dydziai=True, senio_stovi=False,
                                           valytuvai=True, valytuvu_kiekis=4, bumbulai=True, bumbulu_kiekis=10,
                                           egles=False, girliandos=False, fejerverkai=False, kaupimo_greitis=300,
                                           vejas_ijungtas=True, vejas=6 if sekla % 2 else 3, gusio_stiprumas=8 if sekla % 2 else 2)
    a.taikyti_nustatymus(nn); a.langai_judejo = True
    for i in range(int(sek * 30)):
        dezes = dezes_dabar()
        tevai = [(d["x"], d["y"], d.get("_tiesa"), id(d)) for d in a.valyt_daleles]
        # retkarčiais: senis ant lango subyra, bumbuliukas ant lango sudūžta (kad būtų gabalų, šukių, purslų)
        if i % 90 == 45:
            ant = [o for o in a.seniai if o.get("pav") and o["pav"][0] == "langas" and o["busena"] == "eina"]
            if ant: a.senio_subyreti(random.choice(ant), a.senio_Ps(ant[0]))
        if i % 120 == 60:
            ant = [b for b in a.bumbulai if b.get("pav") and b["pav"][0] == "langas" and b["busena"] == "rieda" and not b["ore"]]
            if ant: a.pradeti_dingima(random.choice(ant))
        PIESIMAS.clear(); GALVOS.clear()
        laikas[0] += 1 / 30; a._kadras()
        priskirti_tiesa(dezes, tevai)
        tikrinti_kadra()
        if i % 10 == 0: root.update()

for sekla in (1, 2, 3, 4):
    pries = sum(PAZEIDIMAI.values())
    scena(sekla)
    print(f"   scena {sekla}: pažeidimų {sum(PAZEIDIMAI.values()) - pries}", flush=True)
tikrinti("gylis: niekas tolimesnis nenupieštas ant artimesnio (persidengiant)", not PAZEIDIMAI,
         (dict(PAZEIDIMAI), PAVYZDZIAI[:4]))
tikrinti("programos klaidų nebuvo", not ZK and not KLAIDOS, (ZK + KLAIDOS)[:1])
print(f"{sum(REZ)}/{len(REZ)}")
