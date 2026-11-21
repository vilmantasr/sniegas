"""Elgsenos bandymai (elgsenos_testas.py): visa programa su netikru Windows API, konkrečios situacijos – siaura lango
vieta, per aukštai pakeltas langas, langas prie ekrano viršaus, daug objektų, „Išdėlioti iš naujo“. Kiekvienoje
tikrinama ir elgsenos sargais (Sniegas.sargu_zingsnis): nė vienas neturi suveikti. Pabaigoje – sargų savitikra
(dirbtinai sukeltos klaidos turi būti pagautos). Paskutinė eilutė – „praėjo/iš viso“."""
import collections
from tkinter import messagebox
for nm in ("showinfo", "showerror", "showwarning"): setattr(messagebox, nm, lambda *a_, **k: None)
messagebox.askyesno = messagebox.askokcancel = lambda *a_, **k: True
ZK = []
def rasyti(tekstas, visada=False):
    if tekstas.startswith("KLAIDA") or "Traceback" in tekstas: ZK.append(tekstas)
sn.ZURNALAS.rasyti = rasyti
laikas = [time.perf_counter()]
REZ = []
def tikrinti(pav, sal, info=""):
    REZ.append(bool(sal)); print(("  OK  " if sal else "  KLAIDA ") + pav + (f"  [{info}]" if info else ""), flush=True)
a.kadras = lambda: None
a.sargai_visada = True
sn.time.perf_counter = lambda: laikas[0]
langai = {}
def enum(cb, lp):
    for h_, v in list(langai.items()):
        a.langu_sarasas.append((h_, tuple(v[:4]), v[4]))
    return 1
SPEC["EnumWindows"] = enum
def nustatyti(**kw):
    nn = dict(sn.numatytieji()); nn.update(sniego_senis=True, senio_kiekis=1, senio_dydziai=False, senio_stovi=False,
                                           valytuvai=False, bumbulai=False, egles=False, girliandos=False, fejerverkai=False)
    nn.update(kw); a.taikyti_nustatymus(nn); a.langai_judejo = True
def eiti(sek, f=None):
    for i in range(int(sek * 30)):
        laikas[0] += 1 / 30; a._kadras()
        if i % 10 == 0: root.update()
        if f: f(i)
def sargai(rusys=None):
    return [e for r_, _, e in a.__dict__.get("sargu_pranesimai", ()) if rusys is None or r_ in rusys]
def isvalyti(): a.__dict__["sargu_pranesimai"] = []
def klaidos(): return list(ZK) + list(KLAIDOS)

# 1. Siaura matoma lango dalis (150 px, senis ~78 px): stovi, nevaikšto pirmyn atgal
random.seed(3); isvalyti()
langai.clear(); langai.update({3: [100, 300, 300, 1050, False], 2: [450, 300, 1900, 1050, False], 1: [300, 600, 1300, 1000, False]})
nustatyti(senio_dydis=100); eiti(1)
s_ = a.seniai[0]; s_.update(busena="krenta", x=375.0, y=400.0, vy=0.0, vx=0.0, pav=None, st=None)
xs = []; eiti(20, lambda i: xs.append(s_["x"]) if i > 60 else None)
tikrinti("siaura vieta: senis stovi (nevaikšto pirmyn atgal)", max(xs) - min(xs) < 2, (round(min(xs)), round(max(xs))))
tikrinti("siaura vieta: sargai tylūs", not sargai(), sargai()[:2])

# 2. Vidutinė (250 px ≈ 3 pločiai): vaikšto, bet nesiblaško
isvalyti(); langai[2][0] = 550; a.langai_judejo = True
s_.update(busena="krenta", x=425.0, y=400.0, vy=0.0, vx=0.0, pav=None, st=None)
kr = []; eiti(40, lambda i: kr.append(s_["kryptis"]) if s_["busena"] == "eina" else None)
apsis = sum(1 for p_, q in zip(kr, kr[1:]) if p_ != q)
tikrinti("vidutinė vieta: vaikšto", len(kr) > 300, len(kr))
tikrinti("vidutinė vieta: per 40 s apsisuka ne daugiau 12 kartų", apsis <= 12, apsis)
tikrinti("vidutinė vieta: sargai tylūs", not sargai(), sargai()[:2])

# 3. Langas tarp mažo ir didelio senio aukščio: niekas nekrenta vis į tą pačią vietą ir nekrenta be galo
isvalyti(); langai.clear(); langai[1] = [300, 500, 1600, 900, False]
nustatyti(senio_kiekis=5, senio_dydziai=True, senio_dydis=150); eiti(1)
auk = [sn.senio_aukstis_langeliais(a.senio_puosmena(o), False) * a.senio_Ps(o) for o in a.seniai]
t = int((min(auk) + max(auk)) / 2) + 2; langai[1] = [300, t, 1600, t + 500, False]; a.langai_judejo = True
eiti(90)
ant = [o for o in a.seniai if o.get("pav") and o["pav"][0] == "langas"]
tikrinti("aukštas langas: ant lango tik telpantys", all(sn.senio_aukstis_langeliais(a.senio_puosmena(o), False) * a.senio_Ps(o) <= t for o in ant),
         [round(sn.senio_aukstis_langeliais(a.senio_puosmena(o), False) * a.senio_Ps(o)) for o in ant])
tikrinti("aukštas langas: sargai tylūs", not sargai(), sargai()[:2])

# 4. Langas pakeliamas iki ekrano viršaus: viskas nukrenta, niekas neužstringa už ekrano
isvalyti(); langai.clear(); langai[1] = [300, 500, 1600, 900, False]
nustatyti(senio_kiekis=3, valytuvai=True, valytuvu_kiekis=2, bumbulai=True, bumbulu_kiekis=6); eiti(30)
langai[1] = [300, 10, 1600, 410, False]; a.langai_judejo = True; eiti(15)
lange = [o for o in a.seniai + a.valytuvai if o.get("pav") and o["pav"][0] == "langas"]
tikrinti("langas prie viršaus: ant jo nelieka senių ir valytuvų", not lange, len(lange))
tikrinti("langas prie viršaus: sargai tylūs", not sargai(), sargai()[:2])

# 5. Daug visko, langai kartais pajuda, du kartus „Išdėlioti iš naujo“: sargai tylūs, juostos pernaudojamos
isvalyti(); langai.clear()
langai.update({1: [100, 600, 1300, 1000, False], 2: [450, 300, 1900, 900, False], 3: [200, 800, 1700, 1050, False]})
nustatyti(senio_kiekis=5, senio_dydziai=True, valytuvai=True, valytuvu_kiekis=3, bumbulai=True, bumbulu_kiekis=8, egles=True,
          ledas_languose=True)
def judinti(i):
    if i % 300 == 150:
        v = langai[random.choice(list(langai))]; dx = random.randint(-60, 60); v[0] += dx; v[2] += dx; a.langai_judejo = True
eiti(40, judinti)
juostos = {id(v) for v in a.senio_juostos.values()}; a.perdelioti_senius(); eiti(10, judinti)
po = {id(v) for v in a.senio_juostos.values()}
tikrinti("„Išdėlioti iš naujo“: to paties dydžio juostos nepiešiamos iš naujo", juostos & po, (len(juostos), len(po & juostos)))
a.perdelioti_senius(); eiti(50, judinti)
tikrinti("daug visko: sargai tylūs", not sargai(), sargai()[:3])
busenos = collections.Counter(o["busena"] for o in a.seniai)
tikrinti("daug visko: seniai vaikšto (ne visi stovi)", busenos.get("eina", 0) >= 1, dict(busenos))

# 5a. Didelis senis (200 %) nušoka nuo lango krašto – nusileidžia už lango, o ne atgal ant jo (kitaip šoktų vėl ir vėl)
isvalyti(); langai.clear(); langai[1] = [300, 500, 1600, 900, False]
nustatyti(senio_dydis=200); eiti(1)
s_ = a.seniai[0]; _tik = sn.SENIO_SUOLIO_TIKIMYBE; sn.SENIO_SUOLIO_TIKIMYBE = 1.0
grizo = suoliai = 0
for _ in range(6):
    s_.update(busena="krenta", x=1450.0, y=300.0, vy=0.0, vx=0.0, pav=None, st=None, kryptis=1); skrenda = False
    for _i in range(30 * 12):
        laikas[0] += 1 / 30; a._kadras()
        if s_["busena"] == "eina" and s_.get("pav") and s_["pav"][0] == "langas": s_["kryptis"] = 1
        if s_["busena"] == "krenta" and s_.get("vy", 0) < 0 and not skrenda: skrenda = True; suoliai += 1
        if skrenda and s_["busena"] in ("nukrenta", "eina") and s_.get("pav"):
            grizo += s_["pav"][0] == "langas"; break
sn.SENIO_SUOLIO_TIKIMYBE = _tik
tikrinti("didelis senis nušoka už lango (ne atgal ant jo)", suoliai >= 5 and not grizo, (suoliai, grizo))

# 5b. „Išdėlioti iš naujo“ 10 kartų iš eilės: iškrintantys seniai nenukrenta vienas ant kito (nesubyra)
isvalyti(); langai.clear(); langai[1] = [300, 600, 1300, 1000, False]
nustatyti(senio_kiekis=6, senio_dydziai=True); eiti(5)
_sub = a.senio_subyreti; subyrejo = []
# tik nusileidžiant (krenta / nukrenta) – eidami susidūrę seniai subyra tyčia
a.senio_subyreti = lambda o, *x_, **k_: (subyrejo.append(o["busena"]) if o["busena"] in ("krenta", "nukrenta") else None,
                                         _sub(o, *x_, **k_))
for _ in range(10):
    a.perdelioti_senius(); eiti(2)  # kaip naudotojas – kas 2 s
eiti(3)
a.senio_subyreti = _sub
tikrinti("„Išdėlioti iš naujo“ ×10: iškrintantys nenukrenta vienas ant kito", not subyrejo, subyrejo[:6])
tikrinti("„Išdėlioti iš naujo“ ×10: sargai tylūs (iškritimai – ne klaida)", not sargai(), sargai()[:2])

# 5c. Išjungus sniego kaupimąsi seniai ir valytuvai nuo langų nenukrenta; sniegas nuo langų nubyra
isvalyti(); langai.clear(); langai[1] = [300, 600, 1700, 1000, False]
nustatyti(senio_kiekis=4, valytuvai=True, valytuvu_kiekis=2, kaupimo_greitis=300); eiti(40)
for _o, _x in zip(a.seniai[:2], (700.0, 1300.0)):  # bent du tikrai ant lango (kitaip kartais nebūdavo nė vieno)
    _o.update(busena="krenta", x=_x, y=450.0, vy=0.0, vx=0.0, pav=None, st=None, iskris=None)
eiti(4)
pries = sum(1 for o in a.seniai + a.valytuvai if o.get("pav") and o["pav"][0] == "langas")
nukrito = []; _iv = a.ivykis
a.ivykis = lambda kas: (nukrito.append(kas) if kas == "seniai: nukrito nuo lango" else None, _iv(kas))
valyt_krito = []
def stebeti(i):
    valyt_krito.extend(e for e in a.valytuvai if e["busena"] == "krenta" and e.get("pav") is None and e.get("vy", 0) >= 0
                       and e.get("_buvo_lange"))
    for e in a.valytuvai: e["_buvo_lange"] = bool(e.get("pav") and e["pav"][0] == "langas")
nn_ = dict(a.n); nn_["kaupimasis"] = False; a.taikyti_nustatymus(nn_); a.langai_judejo = True; eiti(10, stebeti)
a.ivykis = _iv
tikrinti("be kaupimosi: langai sekami, niekas nuo jų nenukrito (nušokti gali)", a.langai and pries and not nukrito and not valyt_krito,
         (pries, nukrito, len(valyt_krito)))
tikrinti("be kaupimosi: sniego ant langų nėra", all(max(st["h"]) < 0.01 for st in a.langai.values()))
tikrinti("be kaupimosi: sargai tylūs", not sargai(), sargai()[:2])

# 5d. Žemiau stovintis senis piešiamas priekyje (ne „palenda“ po aukščiau stovinčiu, net jei sąraše pirmas)
isvalyti(); langai.clear(); langai.update({2: [900, 600, 1500, 1050, False], 1: [300, 400, 1700, 1000, False]})
nustatyti(senio_kiekis=2, senio_stovi=True); eiti(1)
s0, s1 = a.seniai
s0.update(busena="krenta", x=1100.0, y=500.0, vy=0.0, vx=0.0, pav=None, st=None)
s1.update(busena="krenta", x=1120.0, y=300.0, vy=0.0, vx=0.0, pav=None, st=None)
eiti(3)
eil = []; _pk = a.permatomas_kopijavimas
a.permatomas_kopijavimas = lambda dydis, x0, y0, *r_, **k_: (eil.append(y0), _pk(dydis, x0, y0, *r_, **k_))[1]
a.piesti_senius([], True, lange=True); a.permatomas_kopijavimas = _pk
tikrinti("žemiau stovintis senis piešiamas priekyje", len(eil) == 2 and eil == sorted(eil), (eil, s0["pav"], s1["pav"]))

# 5e. Valytuvas ant aukštesnio lango nepiešiamas ant žemiau esančio lango senio (piešiama pagal langus)
isvalyti(); langai.clear(); langai.update({2: [900, 450, 1500, 1050, False], 1: [300, 400, 1700, 1000, False]})
nustatyti(senio_kiekis=1, senio_stovi=True, valytuvai=True, valytuvu_kiekis=1); eiti(1)
s0, e0 = a.seniai[0], a.valytuvai[0]
s0.update(busena="krenta", x=1100.0, y=430.0, vy=0.0, vx=0.0, pav=None, st=None)
e0.update(busena="krenta", x=1150.0, y=300.0, vy=0.0, pav=None, st=None)
eiti(2)
eil = []; _pk = a.permatomas_kopijavimas
_vdc = a.valyt_sprite["dc"]; _Ps = a.senio_Ps(s0); _sw = (round(sn.SENIO_W * _Ps), round(sn.SENIO_H * _Ps))
a.permatomas_kopijavimas = lambda dydis, x0, y0, *r_, **k_: (eil.append(("valytuvas" if r_ and r_[0] == _vdc else "senis"
                                                                          if tuple(dydis) == _sw else "kita", y0)),
                                                             _pk(dydis, x0, y0, *r_, **k_))[1]
a.piesti(); a.permatomas_kopijavimas = _pk
eil = [k_ for k_, _ in eil if k_ in ("senis", "valytuvas")]
_t1, _t2 = a.langai[1]["t"], a.langai[2]["t"]
_virsai = sorted((_t1, _t2))
tikrinti("purslas ir konfeti ant aukštesnio lango – to lango gylyje (už žemiau stovinčio senio)",
         a.daleles_grupe({"x": 1150.0, "y": _t1 - 20.0, "l": True}, _virsai) == _t1
         and a.daleles_grupe({"x": 1150.0, "y": _t1, "ant": (1, a.langai[1])}, _virsai) == _t1
         and a.daleles_grupe({"x": 1150.0, "y": _t2 - 3.0, "l": True}, _virsai) == _t2, (_t1, _t2))
# senis ant aukštesnio lango paleidžia konfeti – skrisdama ji to lango gylyje (ne priešais žemiau stovintį senį)
_s_up = {"pav": ("langas", 1), "st": a.langai[1]}
_n0 = len(a.senio_daleles); a.senio_daleles.append({"x": 1150.0, "y": _t1 - 60.0, "tipas": "konfeti", "sena": None})
a.zymeti_senio_daleles(_s_up, _n0); _kf = a.senio_daleles.pop()
tikrinti("senio ant lango paleista konfeti – to lango gylyje", sn.ant_lango(_kf) and a.daleles_grupe(_kf, _virsai) == _t1,
         _kf.get("is_lango"))
# ant aukštesnio lango – tik dalelės (subyrėjusio senio gabalai), daiktai – tik ant žemesnio: dalelės vis tiek savo gylyje
_ev = dict(e0); e0.update(busena="nera", pav=None, st=None)
_gab = {"x": 1150.0, "y": float(_t1), "tipas": "gabalas", "sena": None, "guli": True, "ant": (1, a.langai[1])}
a.senio_daleles.append(_gab)
_gr = a.langu_grupes()
tikrinti("langas tik su dalelėmis – sava grupė (dalelės ne priekyje žemesnio lango senio)",
         _gr is not None and [t for t, _ in _gr] == _virsai and a.daleles_grupe(_gab, [t for t, _ in _gr]) == _t1,
         _gr and [t for t, _ in _gr])
a.senio_daleles.remove(_gab); e0.update(_ev); a.__dict__.pop("_daleliu_t", None)
tikrinti("valytuvas ant aukštesnio lango – už žemiau stovinčio senio", s0.get("pav") and e0.get("pav") and s0["pav"] != e0["pav"]
         and eil.index("valytuvas") < eil.index("senis"), (eil, s0.get("pav"), e0.get("pav")))

# 6. Įvykių suvestinė žurnale: dažni įvykiai – viena eilutė „ĮVYKIAI“
eil = []; _rz = sn.ZURNALAS.rasyti
sn.ZURNALAS.rasyti = lambda tekstas, visada=False: (eil.append(tekstas), rasyti(tekstas, visada))
a.ivykis("bandymas: įvykis"); a.ivykis("bandymas: įvykis")
try:
    a.diag_laikas = laikas[0] - 60; a.diag_proc = None
    a.diagnostikos_suvestine(paskutine=True)
except Exception as e_:
    eil.append(repr(e_))
sn.ZURNALAS.rasyti = _rz
tikrinti("žurnalas: dažni įvykiai suskaičiuoti vienoje eilutėje", any(e.startswith("ĮVYKIAI:") and "bandymas: įvykis 2" in e for e in eil),
         [e[:80] for e in eil if "ĮVYKIAI" in e or "KLAIDA" in e])

# 7. Sargų savitikra: dirbtinai sukeltos klaidos (netikri objektai, tik sargai) turi būti pagautos
isvalyti(); _sen = (a.seniai, a.valytuvai, a.bumbulai)
s_ = {"busena": "eina", "x": 800.0, "y": 1000.0, "kryptis": 1, "pav": ("zeme", 0), "st": None, "ps_priedas": 0}
b_ = {"busena": "rieda", "x": 500.0, "y": None, "ore": False, "W": 30, "pav": None}
a.seniai, a.valytuvai, a.bumbulai = [s_], [], [b_]
for i in range(30 * 6):  # blaškosi: apsisuka kas 0,5 s toje pačioje vietoje
    if i % 15 == 0: s_["kryptis"] = -s_["kryptis"]
    s_["x"] += s_["kryptis"] * 0.8; a.sargu_zingsnis(1 / 30)
tikrinti("savitikra: blaškymasis pagautas", sargai({"blaskosi"}), sargai())
tikrinti("savitikra: bumbuliukas be vietos pagautas", sargai({"be_vietos"}), sargai())
for i in range(30 * 5):  # vis krenta toje pačioje vietoje
    s_["busena"] = "krenta" if i % 45 < 20 else "eina"; a.sargu_zingsnis(1 / 30)
tikrinti("savitikra: kritimas į tą pačią vietą pagautas", sargai({"kritimai"}), sargai())
s_.update(busena="eina", x=-300.0)
for i in range(30 * 22): a.sargu_zingsnis(1 / 30)
tikrinti("savitikra: už ekrano pagautas", sargai({"uz_ekrano"}), sargai())
tikrinti("savitikra: užstrigęs (eina, bet nepajuda) pagautas", sargai({"uzstrigo"}), sargai())
a.seniai, a.valytuvai, a.bumbulai = _sen

tikrinti("programos klaidų nebuvo", not klaidos(), klaidos()[:1])
print(f"{sum(REZ)}/{len(REZ)}")
