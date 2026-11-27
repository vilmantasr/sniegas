"""Sąveikų bandymai (saveikos_testas.py, nuo 13.04): visa programa su netikru Windows API. Nukritęs senis pašokdina
bumbuliukus; gumulas ant senio galvos (susiūbuoja, „apči“, tik ne tolimesnio lango seniui); pustymas nuo langų
(dulkės – lango gylyje, nusėda ant langų); kylantis srautas gūsio priekyje; sniegas ant eglių prisninga ir nupučiamas.
Paskutinė eilutė – „praėjo/iš viso“."""
from tkinter import messagebox
for nm in ("showinfo", "showerror", "showwarning"): setattr(messagebox, nm, lambda *a_, **k: None)
ZK = []
sn.ZURNALAS.rasyti = lambda t, visada=False: ZK.append(t) if t.startswith("KLAIDA") else None
laikas = [time.perf_counter()]
sn.time.perf_counter = lambda: laikas[0]
a.kadras = lambda: None
a.sargai_visada = True
REZ = []
def tikrinti(pav, sal, info=""):
    REZ.append(bool(sal)); print(("  OK  " if sal else "  KLAIDA ") + pav + (f"  [{info}]" if info else ""), flush=True)
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
def langas(t_):  # lango (st) su viršumi ties t_ (fake API gali paslinkti px)
    return min(a.langai.items(), key=lambda kv: abs(kv[1]["t"] - t_))
def ivykiai(): return dict(a.__dict__.get("d_ivykiai") or {})
vejo_zingsnis = a.vejo_zingsnis
def vejas(v):  # pastovus vėjas (be gūsių); None – vėl įprastas
    if v is None:
        a.vejo_zingsnis = vejo_zingsnis
    else:
        a.vejo_zingsnis = lambda dt: None; a.vejas = float(v)

# 1. Nukritęs senis pašokdina šalia gulintį bumbuliuką
random.seed(1); langai.clear()
nustatyti(bumbulai=True, bumbulu_kiekis=1, bumbulu_dingsta=False); eiti(8)
b = a.bumbulai[0]
v0 = []; _sp = a.smugis_pasokdina
def _sp_w(s__, x_, smugis, Ps):  # smūgio akimirką: bumbuliuko greičio pokytis (jei tuo metu jis ne ore)
    v, ore = b["v"], b["ore"]
    _sp(s__, x_, smugis, Ps)
    if not ore: v0.append(((b["v"] - v) * (1 if b["x"] >= x_ else -1), b["vy"] if b["ore"] else 0.0))  # + – nuo senio
a.smugis_pasokdina = _sp_w
for _k in range(4):  # bumbuliukas kartais pats pašoka – tada bandoma iš naujo
    for _ in range(200):
        if b["busena"] == "rieda" and not b["ore"] and b.get("pav") and b["pav"][0] == "zeme": break
        eiti(0.2)
    s_ = a.seniai[0]
    s_.update(busena="krenta", x=b["x"] + 25, y=b["y"] - 500, vy=600.0, vx=0.0, pav=None, st=None, iskris=None)
    eiti(1.5)
    if v0: break
a.smugis_pasokdina = _sp
tikrinti("smūgis: bumbuliukas pašoko", v0 and v0[0][1] < -50 * a.k, v0)
tikrinti("smūgis: stumtelėtas į šalį nuo senio", v0 and v0[0][0] > 0, v0)

# 2. Gumulas ant galvos: vaikštantis susiūbuoja; „Tik stovi vietoje“ – sniego daugiau, kartais „apči“
random.seed(2); langai.clear()
langai.update({2: [200, 700, 1600, 1100, False], 1: [300, 450, 900, 900, False]})  # žemesnis – virš aukštesnio
nustatyti(senio_stovi=False); eiti(2)
h2, st2 = langas(700); h1, st1 = langas(450)
s_ = a.seniai[0]
def padeti(x_, y_):
    s_.update(busena="krenta", x=x_, y=y_, vy=0.0, vx=0.0, pav=None, st=None, iskris=None); eiti(3)
def gumulas(t_):
    Po = a.senio_Ps(s_)
    galva = s_["y"] - sn.senio_aukstis_langeliais(a.senio_puosmena(s_), False) * Po
    d = {"x": s_["x"] + 1, "y": galva - 40, "vx": 0.0, "vy": 60.0, "gyv": 5.0, "kiekis": 2.0, "sena": None, "dyd": 3,
         "l": True, "is_lango": t_}
    a.valyt_daleles.append(d); return d
padeti(1200.0, 600.0)
tikrinti("gumulas: senis ant žemesnio lango", s_["pav"] == ("langas", h2) and s_["busena"] in sn.SENIO_ANT_PAVIRSIAUS,
         (s_["pav"], s_["busena"]))
s_["x_buvo"] = s_["x"]
d = gumulas(st1["t"]); bus = []
eiti(1, lambda i: bus.append(s_["busena"]))
tikrinti("gumulas: vaikštantis susiūbavo", "nukrenta" in bus, bus[:8])
tikrinti("gumulas: dingo (sutyžo ant galvos)", all(x is not d for x in a.valyt_daleles))
# senis ant aukštesnio (tolimesnio) lango: arčiau krentantis gumulas pro jį praskrenda
padeti(600.0, 300.0)
tikrinti("gumulas: senis ant aukštesnio lango", s_["pav"] == ("langas", h1), s_["pav"])
pr = ivykiai().get("seniai: gumulas ant galvos", 0)
gumulas(st2["t"]); bus = []; eiti(1.5, lambda i: bus.append(s_["busena"]))
tikrinti("gumulas: arčiau esantis (žemesnio lango) – nepataiko", ivykiai().get("seniai: gumulas ant galvos", 0) == pr
         and "nukrenta" not in bus, bus[:6])
# „Tik stovi vietoje“: nesusiūbuoja, sniego ant galvos daugiau; su tikimybe 1 – „apči“
nustatyti(senio_stovi=True, sniegas_ant_senio=True); eiti(1); padeti(1200.0, 600.0)
sn.SENIO_GUMULO_APCI = (0.0, 0.0); s_["sniegas"] = 0.3
gumulas(st1["t"]); bus = []; eiti(1, lambda i: bus.append(s_["busena"]))
tikrinti("gumulas: stovintis nesusiūbuoja, sniego daugiau", "nukrenta" not in bus and s_.get("sniegas", 0) > 0.45,
         (bus[::6], round(s_.get("sniegas", 0), 2)))
sn.SENIO_GUMULO_APCI = (1.0, 0.0); eiti(sn.SENIO_GUMULO_PERTRAUKA)
gumulas(st1["t"]); bus = []; eiti(2, lambda i: bus.append(s_["busena"]))
tikrinti("gumulas: stovintis – „apči“", "ciaudi" in bus, bus[::6])
# to paties lango gumulas (valytuvas išpylė šalia) – ne „nukrito nuo aukštesnio lango“: nepataiko
eiti(sn.SENIO_GUMULO_PERTRAUKA); pr = ivykiai().get("seniai: gumulas ant galvos", 0)
gumulas(st2["t"]); eiti(1.5)
tikrinti("gumulas: to paties lango – nepataiko", ivykiai().get("seniai: gumulas ant galvos", 0) == pr)
# keli gumulai iš eilės – ne dažniau kaip kas SENIO_GUMULO_PERTRAUKA s
gumulas(st1["t"]); eiti(0.5); gumulas(st1["t"]); eiti(1.5)
tikrinti("gumulas: du iš eilės – pataiko tik pirmas", ivykiai().get("seniai: gumulas ant galvos", 0) == pr + 1,
         ivykiai().get("seniai: gumulas ant galvos", 0) - pr)
sn.SENIO_GUMULO_APCI = (0.4, 20.0)

# 3. Pustymas nuo langų: stiprus vėjas, dulkės – lango gylyje, nusėda ant langų
random.seed(3); langai.clear()
langai.update({2: [300, 800, 1700, 1100, False], 1: [200, 500, 1000, 1000, False]})
nustatyti(senio_kiekis=0, sniego_senis=False, kaupimo_greitis=800); eiti(20)
st1 = langas(500)[1]
pries = sum(st1["h"]); vejas(8.0)
dalys = []; ant_lango_piesta = []
f0 = a.piesti_pustomas
def pp(i_langa, visas, lange=None, gylis=None):
    pries = {id(p): p.get("sena") for p in a.pustomos}
    r = f0(i_langa, visas, lange, gylis)
    if lange is False:  # ekrano apačios praėjimas: kurios nupieštos (pasikeitė „sena“)
        ant_lango_piesta.extend(p for p in a.pustomos if p.get("is_lango") is not None and p.get("sena") is not None
                                and p.get("sena") is not pries.get(id(p)))
    return r
a.piesti_pustomas = pp
eiti(6, lambda i: dalys.append(sum(1 for p in a.pustomos if p.get("is_lango") is not None)))
a.piesti_pustomas = f0
tikrinti("pustymas: nuo lango keliamos dulkės", max(dalys) > 5 and ivykiai().get("langai: pustoma nuo lango", 0) > 5, max(dalys))
tikrinti("pustymas: lango dulkės nepiešiamos ekrano apačios gylyje", not ant_lango_piesta, len(ant_lango_piesta))
vejas(0.0); eiti(8)
tikrinti("pustymas: nurimus dulkių nelieka", not [p for p in a.pustomos if p.get("is_lango") is not None],
         len(a.pustomos))
vejas(None)

# 4. Gūsio priekyje oras kyla: dalis snaigių trumpam juda aukštyn
random.seed(4); langai.clear()
nustatyti(senio_kiekis=0, sniego_senis=False, vejas_ijungtas=True, gusiai=0); eiti(5)
vejas(0.0); eiti(3)
def kyla():
    y0 = [f[sn.SY] for f in a.snaiges]; eiti(1 / 30)
    return sum(1 for f, y in zip(a.snaiges, y0) if f[sn.SY] < y - 0.2) / max(1, len(y0))
ramu = max(kyla() for _ in range(30))
for v in range(1, 9):  # vėjas sustiprėja per ~1 s
    a.vejas = float(v); eiti(4 / 30)
gusis = max(kyla() for _ in range(60))
tikrinti("gūsis: kylantis srautas atsiranda", a.__dict__.get("_kilimas") is not None, None)
tikrinti("gūsis: aukštyn juda daugiau snaigių nei ramiu oru", gusis > ramu + 0.05, (round(ramu, 2), round(gusis, 2)))
eiti(6)
tikrinti("gūsis: vėjui nusistovėjus srautas nuslopsta", a.__dict__.get("_kilimas") is None, None)
# vėjas pereina per 0 (krypties pasikeitimas) – vejo_juostos „apsiverčia“, bet tai ne gūsis
a.vejas = 0.4; eiti(4); a.vejas = -0.4; eiti(1 / 30)
_k = a.__dict__.get("_kilimas")
tikrinti("gūsis: vėjui perėjus per 0 – kylančio srauto nėra", not _k or max(_k) < 2 * a.k, _k and round(max(_k), 1))
vejas(None)

# 5. Sniegas ant eglių: prisninga pakopomis, stipriu vėju nupučiamas (dulkės nuo šakų)
random.seed(5); langai.clear()
nustatyti(senio_kiekis=0, sniego_senis=False, egles=True, sniegas_ant_egliu=True, kaupimo_greitis=800); vejas(0.0)
a.egliu_sniegas = 0.0; eiti(1)
pak0 = {e.get("sniego_pakopa") for e in a.egles}
eiti(35)
pak1 = {e.get("sniego_pakopa") for e in a.egles}
a.egliu_sniegas = 0.99; eiti(3)
pak3 = {e.get("sniego_pakopa") for e in a.egles}
tikrinti("eglės: sniegas prisninga pakopomis (iki visų)", pak0 == {0} and min(pak1) >= 2 and pak3 == {sn.EGLIU_SNIEGO_PAKOPOS},
         (pak0, pak1, pak3))
tikrinti("eglės: matomų juostelių daugėja", all(len(sn.egles_sniegas(dict(e, sniego_pakopa=2))) < len(sn.egles_sniegas(e))
                                                for e in a.egles if e.get("snieg")))
# perdėliojus eglės lieka tiek pat apsnigtos (ne visos iš karto, ne plikos)
a.perdelioti_egles(); eiti(0.5)
tikrinti("eglės: perdėliotos – tiek pat apsnigtos", {e.get("sniego_pakopa") for e in a.egles} == {sn.EGLIU_SNIEGO_PAKOPOS},
         {e.get("sniego_pakopa") for e in a.egles})
vejas(8.0); dulk = []
eiti(20, lambda i: dulk.append(sum(1 for p in a.pustomos if p.get("egle"))))
pak2 = {e.get("sniego_pakopa") for e in a.egles}
tikrinti("eglės: stiprus vėjas nupučia (ne iki galo)", pak2 and max(pak2) < sn.EGLIU_SNIEGO_PAKOPOS and min(pak2) >= 2, pak2)
tikrinti("eglės: nuo šakų pakyla dulkės", max(dulk) > 0, max(dulk))
a.nuvalyti(); eiti(0.2)
tikrinti("eglės: nuvalius sniegą – ir nuo šakų", {e.get("sniego_pakopa") for e in a.egles} == {0}, {e.get("sniego_pakopa") for e in a.egles})
vejas(None)

# 6. Spalvoti blizgesiai: šalia šviečiančios eglės lemputės – jos spalvos, toli – įprasti
random.seed(6); langai.clear()
nustatyti(senio_kiekis=0, sniego_senis=False, egles=True, egliu_lemputes=True, egliu_mirksi=False); vejas(0.0); eiti(1)
e = a.egles[0]; r_, c_, sp_, _ = e["lemp"][0]
lx, ly = e["x0"] + (c_ + 0.5) * e["s"], e["y0"] + (r_ + 0.5) * e["s"]
arti = [a.blizgesio_spalva(lx + 3, ly + 3) for _ in range(200)]
toli = [a.blizgesio_spalva(lx, ly - 2000) for _ in range(50)]
tikrinti("blizgesiai: prie lemputės – jos spalvos", sum(1 for x in arti if x == sn._maisyti(sp_, "#ffffff", 0.25)) > 150,
         sum(1 for x in arti if x))
tikrinti("blizgesiai: toli nuo lempučių – įprasti", not any(toli))
eiti(10); spalv = [b_.get("spalva") for b_ in a.blizgesiai]
tikrinti("blizgesiai: piešiami be klaidų (su spalvomis)", not ZK and not KLAIDOS)
vejas(None)

# 8. Glotnios snaigės: tolimos pusiau permatomos (lentelė), artimos – ne
z_ = sn.TIPU_GYLIS
tol = min(range(len(sn.TIPAI)), key=lambda t: z_[t]); art = max(range(len(sn.TIPAI)), key=lambda t: z_[t])
lt = sn.alfa_toli_lentele(tol)
tikrinti("glotnios: toliausia – ~45 % dengimo, artimiausia – nepermatoma", lt is not None and abs(lt[255] - 115) <= 2
         and sn.alfa_toli_lentele(art) is None, (lt and lt[255]))

# 9. Išeinantis pro ekrano kraštą senis, įjungus „Tik stovi vietoje“, grįžta į ekraną (nenukrenta už jo)
random.seed(9); langai.clear()
nustatyti(senio_kiekis=1, senio_stovi=False, egles=False); eiti(3)
s_ = a.seniai[0]
for _ in range(100):
    if s_.get("pav") and s_["pav"][0] == "zeme" and s_["busena"] in sn.SENIO_ANT_PAVIRSIAUS: break
    eiti(0.2)
r1 = a.zemes_ruozai[s_["pav"][1]][0] * sn.STULPELIS
s_.update(busena="eina", x=r1 - 15.0, kryptis=-1, iseina=True, tikslas_x=None)
pr = ivykiai().get("seniai: nukrito nuo žemės", 0)
a.n["senio_stovi"] = True; eiti(4)
tikrinti("išeinantis + „Tik stovi vietoje“: grįžta, nenukrenta", ivykiai().get("seniai: nukrito nuo žemės", 0) == pr
         and s_["x"] >= r1, (round(s_["x"]), r1, s_["busena"]))
a.n["senio_stovi"] = False

# 10. Eglių įvairovė (13.05): vos vos skirtingos spalvos, dalis – ilgesniu kamienu; šakos tokio pat dydžio
random.seed(10); langai.clear()
nustatyti(senio_kiekis=0, sniego_senis=False, egles=True, egliu_kiekis=40); eiti(1)  # 40 – kad ilgų tikrai būtų
sp = {e["spalvos"][0] for e in a.egles}
ilgi = [e for e in a.egles if e.get("eil")]
tikrinti("eglės: spalvos skiriasi", len(sp) >= 0.8 * len(a.egles), (len(sp), len(a.egles)))
tikrinti("eglės: dalis – ilgesniu kamienu (3 langeliai)", 0 < len(ilgi) < len(a.egles) and
         all(len(e["eil"]) == len(sn.EGLIU_SABLONAI[e["sab"]]) + 1 and e["eil"][-1].strip(".") == "n" for e in ilgi),
         (len(ilgi), len(a.egles)))
_e = ilgi[0] if ilgi else a.egles[0]
_kx = _e["x0"] + (len(sn.egles_sablonas(_e)[0]) // 2 + 0.5) * _e["s"]; _ky = _e["ribos"][3] - 2
tikrinti("eglės: ilgesnis kamienas – eglės dalis (dengia)", sn.egle_dengia(_e, _kx, _ky), (_kx, _ky))
tikrinti("eglės: skirtumas mažas (žalia lieka žalia)", all(abs(int(e["spalvos"][0][3:5], 16) - 0xa0) < 0x20 for e in a.egles))

# 11. Pastabų pataisymai (13.05)
class _Iv:  # pelės įvykis
    def __init__(self, x, y): self.x_root, self.y_root = x + a.vx, y + a.vy
random.seed(11); langai.clear()
nustatyti(senio_kiekis=1); eiti(1)
s_ = a.seniai[0]
s_.update(busena="krenta", x=600.0, y=100.0, vy=0.0, vx=0.0, pav=None, st=None, iskris="zeme", iskris_xy=(600.0, 900.0),
          apsisukti=True, jega="silpnai", pasemta=True)
a.senis_paimtas(s_, _Iv(600, 80)); a.senis_tempiamas(s_, _Iv(640, 80))
tikrinti("pačiuptas iškrintantis senis – be iškritimo ir pusiau atliktų veiksmų žymių",
         s_["busena"] == "kabo" and not s_.get("iskris") and not s_.get("iskris_xy") and not s_.get("apsisukti")
         and not s_.get("jega") and not s_.get("pasemta"), {k: s_.get(k) for k in ("busena", "iskris", "apsisukti", "jega")})
a.senis_paleistas(s_, _Iv(640, 80)); eiti(1)
_pn = sn.paruostuko_nustatymai(dict(sn.PARUOSTUKAI[0][1]))
tikrinti("paruoštukai atstato „Kaupti ekrano apačioje“", _pn.get("kaupti_apacioje") is True, _pn.get("kaupti_apacioje"))
_mon = a.monitoriai[0][0]
tikrinti("pusiau už ekrano nustumtas langas – vis dar ekrane", a.ant_ekrano_atkarpos(_mon[2] - 400, _mon[2] + 600, 500)
         and not a.ant_ekrano_atkarpos(_mon[2] - 40, _mon[2] + 600, 500))
tikrinti("uždaryto lango dalelė – pirmo ne aukštesnio lango grupėje", a.daleles_grupe({"is_lango": 333}, [251, 401, 601]) == 401)

# 12. Antros pastabų dalies pataisymai (13.05)
random.seed(12)
_ats = 0
for _ in range(600):
    _s = {"busena": "konfeti", "t": 0.0, "kryptis": 1, "x": 500.0}
    sn.senio_veiksmo_eiga(_s, lambda l: (500.0, 500.0), 1.0, (0, 1920), (0, 1080), [])
    _ats += _s["kryptis"] == -1
tikrinti("konfeti: maždaug trečdalį kartų senis atsisuka", 0.25 < _ats / 600 < 0.42, _ats / 600)
# vienas virš kito esantys monitoriai: viršutinio ekrano langas – daiktai ant jo telpa
_mon0, _vy0 = a.__dict__.get("monitoriai"), a.vy
a.monitoriai, a.vy = [((0, -1080, 1920, 0), (0, -1080, 1920, -40)), ((0, 0, 1920, 1080), (0, 0, 1920, 1040))], -1080
_st = {"l": 300, "r": 900, "t": 500, "B": 0}  # ekrano y = 500 - 1080 → viršutiniame monitoriuje
tikrinti("vertikalūs monitoriai: ant viršutinio ekrano lango daiktai telpa", a.lange_telpa(_st, 100))
_st = {"l": 300, "r": 900, "t": 1130, "B": 0}  # apatinio monitoriaus pačiame viršuje – netelpa
tikrinti("vertikalūs monitoriai: apatinio ekrano viršuje – netelpa", not a.lange_telpa(_st, 100))
a.monitoriai, a.vy = _mon0, _vy0
# eglių skilties ↺: 20–40 → 60–120 (mažesnė riba neapribojama senąja didesne), net kai fokusas laukelyje
nustatyti(egles=True, egliu_min=20, egliu_max=40); eiti(0.5)
_ask = messagebox.askyesno; messagebox.askyesno = lambda *a_, **k: True
try:
    a.valdikliai["egliu_min"].focus_force(); root.update()
    a.atkurti_skilti("egles", "Eglutės"); root.update()
finally:
    messagebox.askyesno = _ask
tikrinti("eglių ↺: abi ribos – numatytosios", (a.n["egliu_min"], a.n["egliu_max"]) == (sn.NUMATYTI["egliu_min"],
         sn.NUMATYTI["egliu_max"]) and a.kint["egliu_min"].get() == str(sn.NUMATYTI["egliu_min"]),
         (a.n["egliu_min"], a.n["egliu_max"], a.kint["egliu_min"].get()))
# bylos su visais nuliais (bumbuliukų raštai, spalvos, dingimai) – numatytosios
import json as _js, tempfile as _tf
_b = sn.Path(_tf.mkdtemp()) / "n.json"
_b.write_text(_js.dumps({"bumbulu_rastai": [0] * 4, "bumbulu_spalvos": [0] * 14, "bumbulu_dingimai": [0] * 4}), encoding="utf-8")
_n = a.ikelti_nustatymus(_b)
tikrinti("nustatymai: visi nuliai bumbuliukų sąrašuose – numatytieji", all(_n[k] == sn.NUMATYTI[k] for k in
         ("bumbulu_rastai", "bumbulu_spalvos", "bumbulu_dingimai")))
# našumo testo metu dėklas: nustatymai neatsidaro, paruoštukai nepritaikomi; „Išjungti“ – lieka
_rod, _par, _bai = a.rodyti_nustatymus, a.pritaikyti_paruostuka, a.baigti
_kv = []
a.rodyti_nustatymus = lambda: _kv.append("rodyti"); a.pritaikyti_paruostuka = lambda *x, **k: _kv.append("paruostukas")
a.baigti = lambda: _kv.append("baigti")
a.testas = {"dummy": True}
try:
    a.deklo_ivykiai[:] = [sn.WM_LBUTTONUP, sn.WM_MBUTTONUP]
    a.meniu_komandos[:] = [1, 2, sn.MENIU_PARUOSTUKAI + 1, 3]
    _vp, _si = a.vartotojas_paslepe, a.sniegas_isjungtas
    a.tikrinti_deklo_ivykius()
    tikrinti("našumo testo metu dėklas: tik „Išjungti“", _kv == ["baigti"] and a.vartotojas_paslepe == _vp
             and a.sniegas_isjungtas == _si, _kv)
finally:
    a.__dict__.pop("testas", None)
    a.rodyti_nustatymus, a.pritaikyti_paruostuka, a.baigti = _rod, _par, _bai
# tempiamas tuščias langas: nesvarių sričių nebeprideda, kopų forma ta pati
random.seed(13); langai.clear()
nustatyti(senio_kiekis=0, sniego_senis=False); langai[0x77] = [400, 400, 1000, 800, False]; eiti(0.5)
_st0 = a.langai[0x77]
_pr = _st0["profilis"]
_st0["h"][:] = [0.0] * len(_st0["h"]); _st0.pop("ledas", None)  # tuščias (sniegas nubyrėjo pirmu tempimo žingsniu)
a.nesvarios_sritys = []
langai[0x77] = [420, 400, 1020, 800, False]; a.langai_judejo = True
a.perskaityti_langus()
tikrinti("tuščias langas pajudėjo: perpiešimo nereikia, kopų forma ta pati",
         not a.nesvarios_sritys and a.langai[0x77]["profilis"] is _pr, a.nesvarios_sritys)
langai.clear(); a.perskaityti_langus()

# 13. Paskutinio audito pataisymai (13.06)
random.seed(14)
_ats = 0
for _ in range(300):
    _s = {"busena": "konfeti", "t": 0.0, "kryptis": 1, "x": 5.0, "iseina": True}
    sn.senio_veiksmo_eiga(_s, lambda l: (5.0, 500.0), 1.0, (0, 1920), (0, 1080), [])
    _ats += _s["kryptis"] == -1
tikrinti("konfeti: išeinantis pro kraštą neatsisuka", _ats == 0, _ats)
# laukelyje paliktas nepritaikytas (per mažas) skaičius neperrašo paruoštuko / ↺ reikšmės, išėjus iš laukelio
nustatyti(egles=True); eiti(0.3)
a.valdikliai["egliu_min"].focus_force(); root.update()
a.kint["egliu_min"].set("1"); root.update()
_buvo = a.n["egliu_min"]
a.nustatyti_laukelius({"egliu_min": sn.NUMATYTI["egliu_min"]}); root.update(); root.update()
tikrinti("laukelyje nebaigtas rinkti tekstas paruoštuko neperrašo", _buvo == sn.NUMATYTI["egliu_min"]
         and a.n["egliu_min"] == sn.NUMATYTI["egliu_min"] and a.kint["egliu_min"].get() == str(sn.NUMATYTI["egliu_min"]),
         (_buvo, a.n["egliu_min"], a.kint["egliu_min"].get()))
# testo metu meniu gija prideda „Išjungti“ tuo metu, kai tvarkomi kiti įvykiai – nedingsta
class _Saras(list):
    def pop(self, *x):
        v = super().pop(*x)
        if v == sn.WM_LBUTTONUP: a.meniu_komandos.append(3)
        return v
_bai, _kv = a.baigti, []
a.baigti = lambda: _kv.append("baigti"); a.testas = {"dummy": True}
_iv0 = a.deklo_ivykiai
try:
    a.deklo_ivykiai = _Saras([sn.WM_LBUTTONUP]); a.meniu_komandos[:] = [1]
    a.tikrinti_deklo_ivykius()
    tikrinti("testo metu „Išjungti“, pridėtas tvarkant kitus įvykius, nedingsta", _kv == ["baigti"], _kv)
finally:
    a.__dict__.pop("testas", None); a.baigti = _bai; a.deklo_ivykiai = _iv0

# 14. Dar vieno audito pataisymai (13.06)
import threading as _th
# klaida našumo testo etape – testas nutraukiamas, viskas grąžinama
nustatyti(senio_kiekis=0, sniego_senis=False); eiti(0.2)
_pr = dict(a.n); _ev = _th.Event(); _ts, _kl = a.testo_sniegas, a.klaida_parodyta
a.testo_sniegas = lambda: 1 / 0
a.testas = {"pradiniai": _pr, "etapai": [("x", {"kiekis": 5}, None)], "rez": [], "stabdyti": _ev, "gpu": {"pav": ""},
            "meginiai": [], "pradzia": "x", "paslepe": False}
try:
    a.testo_etapas(0); root.update()
finally:
    a.testo_sniegas = _ts
tikrinti("klaida testo etape: testas nutrauktas, nustatymai grąžinti", "testas" not in a.__dict__ and _ev.is_set()
         and a.n.get("kiekis") == _pr.get("kiekis") and not a.vartotojas_paslepe)
KLAIDOS[:] = [k_ for k_ in KLAIDOS if "ZeroDivision" not in str(k_)]; ZK[:] = [k_ for k_ in ZK if "ZeroDivision" not in k_]
a.klaida_parodyta = _kl
# žurnalo pervadinimas nepavyko (byla užrakinta) – rašoma toliau
_d = sn.Path(_tf.mkdtemp()); _z = sn.Zurnalas(_d / "z.log"); _z.MAKS = 10
(_d / "z.log").write_text("x" * 50, encoding="utf-8")
_rp = sn.Path.replace
def _blogas(self, *x): raise PermissionError("užrakinta")
sn.Path.replace = _blogas
try:
    _z.rasyti("BANDYMAS")
finally:
    sn.Path.replace = _rp
tikrinti("žurnalas: nepavykus pervadinti – rašoma toliau", "BANDYMAS" in (_d / "z.log").read_text(encoding="utf-8"))
# valytuvas nenusileidžia ant lango, siauresnio nei 3 tarpai (iš ten kitą kadrą išvyktų ir vėl kristų)
random.seed(15); langai.clear()
nustatyti(senio_kiekis=0, sniego_senis=False, valytuvai=True); eiti(0.5)
_tp = a.valyt_tarpas(); _w = int(2.5 * _tp)
langai[0x88] = [800, 500, 800 + _w, 700, False]; a.langai_judejo = True; eiti(0.3)
_st = a.langai.get(0x88)
_e = a.valytuvai[0]
_e.update(busena="krenta", x=800 + _w / 2 - a.vx, y=_st["t"] - 50 if _st else 400.0, vy=0.0, pav=None, st=None)
for _ in range(30):
    a.valyt_kristi(_e, 1 / 30)
    if _e["busena"] != "krenta": break
tikrinti("valytuvas: ant per siauro lango nenusileidžia", _st is not None and not (_e.get("pav") or ("",))[0] == "langas",
         (_e["busena"], _e.get("pav"), _w))
langai.clear(); a.perskaityti_langus()

tikrinti("programos klaidų nebuvo", not ZK and not KLAIDOS, (ZK + KLAIDOS)[:1])
print(f"{sum(REZ)}/{len(REZ)}")
