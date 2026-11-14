"""12.33: sniegas ant lango uždengia lango viršutinę eilutę (1 px rėmelį), paviršius nepakinta."""
import sys, ctypes, importlib.util, importlib.machinery
from unittest import mock
ctypes.windll = mock.MagicMock(); sys.modules["winreg"] = mock.MagicMock(); ctypes.WINFUNCTYPE = ctypes.CFUNCTYPE
byla = sys.argv[1]
spec = importlib.util.spec_from_file_location("sn", byla, loader=importlib.machinery.SourceFileLoader("sn", byla))
sn = importlib.util.module_from_spec(spec); sys.modules["sn"] = sn; spec.loader.exec_module(sn)
REZ = []
def tikrinti(pav, sal, info=""):
    REZ.append(bool(sal)); print(("  OK  " if sal else "  KLAIDA ") + pav + (f"  [{info}]" if info else ""))
class P:
    def __init__(s): s.pol, s.st = [], []
    def poligonas(s, pts, c): s.pol.append(pts)
    def staciakampis(s, *a): s.st.append(a)
    def linija(s, *a): pass
class B(sn.Sniegas):
    def __init__(s): s.k = 1.0; s.statinis = P()
a = B(); S = sn.STULPELIS; t = 500
h = [8.0] * 20
a.piesti_sluoksni(h, 0, 20, 100, t, 1.0, None, apacia=2)
ys = a.statinis.pol[0][1::2]
tikrinti("poligono apačia – t + 2 (GDI neužpildo apatinės briaunos → užpildoma ir eilutė t)", max(ys) == t + 2, max(ys))
tikrinti("paviršius nepakito (t − h)", min(ys) == t - 8, min(ys))
tikrinti("klodai irgi iki t + 2", all(r[3] == t + 2 for r in a.statinis.st if r[1] > t - 8), [r[3] for r in a.statinis.st][:3])
a2 = B(); a2.piesti_sluoksni(h, 0, 20, 100, t, 0.7, None)
tikrinti("ekrano apačios pusnys – kaip buvo (iki pagrindo)", max(a2.statinis.pol[0][1::2]) == t)
print(f"{sum(REZ)}/{len(REZ)}")
print("2. Apvalūs lango kampai (12.35: sniegas ant lanko nesilaiko)")
a3 = B(); L, Rr = 100, 100 + 20 * S + 2
a3.piesti_sluoksni(h, 0, 20, L, t, 1.0, None, apacia=2, kampai=(8, Rr))
pts = list(zip(a3.statinis.pol[0][0::2], a3.statinis.pol[0][1::2]))
tikrinti("kairėje sniegas prasideda ten, kur lankas ≤ 1 px (8 px spinduliu – nuo L + 5)",
         min(x for x, _ in pts) == L + 5, min(x for x, _ in pts))
tikrinti("dešinėje – irgi (iki Rr − 5)", max(x for x, _ in pts) == Rr - 5, max(x for x, _ in pts))
tikrinti("apačia nebeapgaubia kampo (ne žemiau t + 2 + 1)", max(y for _, y in pts) <= t + 3, max(y for _, y in pts))
tikrinti("galas suapvalintas (krašte žemiau nei viduryje)",
         min(y for x, y in pts if x == L + 5) > t - 8 and min(y for x, y in pts) == t - 8)
a4 = B(); a4.piesti_sluoksni(h, 5, 15, L, t, 1.0, None, apacia=2, kampai=(8, Rr))
tikrinti("ne krašte (dalinis perpiešimas viduryje) – apačia tiesi", max(a4.statinis.pol[0][1::2]) == t + 2)
print(f"{sum(REZ)}/{len(REZ)}")
print("3. Prie lango krašto – suapvalintas galas (12.42: ketvirtis apskritimo, spindulys – sniego aukštis)")
hh = [20.0] * 50
sn.nusodinti(hh, 25, 0.1, 20, krastai=True, profilis=[1.0] * 50)
kr, des = hh[:8], hh[::-1][:8]
tikrinti("galas simetriškas", all(abs(a - b) < 1e-9 for a, b in zip(kr, des)), [round(x, 1) for x in kr])
tikrinti("ne smailus ir ne stati siena: krašte 30–50 % aukščio", 0.3 * 20 <= kr[0] <= 0.5 * 20, round(kr[0], 1))
tikrinti("kyla, kol pasiekia sniego aukštį (per ~aukštį px)", all(a < b for a, b in zip(kr, kr[1:6])) and hh[7] == 20.0)
tikrinti("išgaubtas (prieaugis mažėja – apvalus, ne pleištas)",
         all(b - a > c - b for a, b, c in zip(kr, kr[1:], kr[2:6])))
h1 = [5.0] * 30
sn.nusodinti(h1, 15, 0.01, 5, krastai=True, profilis=[1.0] * 30)
tikrinti("plonas sniegas (5 px) – galas trumpas (≤ 2 stulpeliai), ne ilga adata", h1[2] == 5.0 and h1[0] >= 2.5,
         [round(x, 1) for x in h1[:4]])
print(f"{sum(REZ)}/{len(REZ)}")
print("4. Klodai ir šešėlis neišeina už sniego galo prie kampo")
class P2(P):
    def staciakampis(s, x1, y1, x2, y2, c): s.st.append((x1, y1, x2, y2, c))
class B2(sn.Sniegas):
    def __init__(s): s.k = 1.0; s.statinis = P2()
a5 = B2(); hh5 = [min(20.0, (j + 1) * 2.5) for j in range(10)] + [20.0] * 20 + [min(20.0, (j + 1) * 2.5) for j in range(10)][::-1]
L5 = 100; Rr5 = L5 + 40 * S
a5.piesti_sluoksni(hh5, 0, 40, L5, t, 1.0, None, kampai=(8, Rr5))
xs5 = a5.statinis.pol[0][0::2]
tikrinti("visi stačiakampiai – sniego plote", all(min(xs5) <= r[0] and r[2] <= max(xs5) for r in a5.statinis.st),
         [r for r in a5.statinis.st if r[2] > max(xs5)][:2])
print(f"{sum(REZ)}/{len(REZ)}")
print("5. Sniego valytuvo kauburys prie krašto nenukerpamas (12.35)")
n5 = 40; pr5 = [0.5] * n5
h5 = [min(5.0, (min(j, n5 - 1 - j) + 1) * 2.5) for j in range(n5)]  # kraštai – jau pagal nuolydį
for j in range(n5 - 9, n5 - 2):
    h5[j] = 16.0
sust5 = bytearray(n5); sust5[n5 - 12:n5] = b"\x01" * 12
pries5 = sum(h5[n5 - 12:])
sn.nusodinti(h5, n5 - 5, 0.5, 18.0, krastai=True, profilis=pr5, sust=sust5)
tikrinti("kauburys beveik visas liko (≥ 90 %; tik šlaitu nubyrėjo prie krašto)", sum(h5[n5 - 12:]) >= 0.9 * pries5,
         (round(pries5, 1), round(sum(h5[n5 - 12:]), 1)))
h6 = [5.0] * n5
for j in range(n5 - 9, n5 - 2):
    h6[j] = 16.0
sn.nusodinti(h6, n5 - 5, 0.5, 18.0, krastai=True, profilis=pr5)
tikrinti("be žymės – nukerpamas (kaip buvo)", max(h6[n5 - 9:n5 - 2]) <= 9.0 + 1e-9, max(h6[n5 - 9:n5 - 2]))
print(f"{sum(REZ)}/{len(REZ)}")
