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

tikrinti("programos klaidų nebuvo", not ZK and not KLAIDOS, (ZK + KLAIDOS)[:1])
print(f"{sum(REZ)}/{len(REZ)}")
