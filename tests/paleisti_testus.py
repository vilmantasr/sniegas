"""Visi Sniego testai: python tests/paleisti_testus.py [kelias/iki/Sniegas.pyw] [--dumai]

Kiekvienas *_testas.py paleidžiamas atskiru procesu su programos byla (numatytai – ../Sniegas.pyw) ir parašo,
kiek patikrinimų praėjo. Windows API pakeičiamas netikru (unittest.mock), todėl testai veikia ir ne Windows.
ivedimo_testas.py reikia tikro tkinter lango (Linux – Xvfb, pvz. DISPLAY=:99).
--dumai – dar 3 dūmų bandymai (dumu/paleisti.py): visa programa su netikru Windows API, atsitiktiniai veiksmai."""
import os, subprocess, sys, glob

cia = os.path.dirname(os.path.abspath(__file__))
argai = [a for a in sys.argv[1:] if not a.startswith("--")]
byla = os.path.abspath(argai[0] if argai else os.path.join(cia, "..", "Sniegas.pyw"))
blogi = 0
for t in sorted(glob.glob(os.path.join(cia, "*_testas.py"))):
    r = subprocess.run([sys.executable, t, byla], capture_output=True, text=True, timeout=300)
    paskutine = (r.stdout.strip().splitlines() or ["(nieko)"])[-1]
    gerai = r.returncode == 0 and "/" in paskutine and paskutine.split("/")[0] == paskutine.split("/")[1]
    blogi += not gerai
    print(f"{'OK    ' if gerai else 'KLAIDA'} {os.path.basename(t):32} {paskutine}")
    if not gerai:
        print((r.stdout + r.stderr)[-2000:])
if "--dumai" in sys.argv:
    for sekla in (1, 2, 3):
        env = dict(os.environ, SEKLA=str(sekla), KADRU="6000", DAZNIS="0.2", FH="170")
        r = subprocess.run([sys.executable, "-u", os.path.join(cia, "dumu", "paleisti.py"), byla], capture_output=True,
                           text=True, timeout=400, env=env)
        eil = [e for e in r.stdout.splitlines() if e.startswith(("BAIGTA", "---"))]
        gerai = r.returncode == 0 and any(e.startswith("BAIGTA") and "klaidų=0" in e for e in eil)
        blogi += not gerai
        print(f"{'OK    ' if gerai else 'KLAIDA'} dūmų bandymas, sėkla {sekla}: {eil[-1] if eil else r.stderr[-500:]}")
print("Viskas gerai." if not blogi else f"Nepavyko: {blogi}.")
sys.exit(1 if blogi else 0)
