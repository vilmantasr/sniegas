"""13.03: gylio testas (dumu/gylis.py) – visa programa su netikru Windows API ir tikru Tk (Xvfb). Atsitiktinės scenos su
keliais langais vienas virš kito, seniais, valytuvais, bumbuliukais ir jų dalelėmis; kiekviename kadre tikrinama, kad
tai, kas toliau (aukštesnio lango gylyje), nebūtų nupiešta ant to, kas arčiau."""
import os, subprocess, sys
cia = os.path.dirname(os.path.abspath(__file__))
env = dict(os.environ, SCENARIJUS=os.path.join(cia, "dumu", "gylis.py"), FH="280")
r = subprocess.run([sys.executable, "-u", os.path.join(cia, "dumu", "paleisti.py"), sys.argv[1]], capture_output=True,
                   text=True, timeout=290, env=env)
print(r.stdout[-6000:])
if r.returncode:
    print(r.stderr[-3000:])
    print("0/1")
