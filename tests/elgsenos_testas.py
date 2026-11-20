"""13.02: elgsenos bandymai (dumu/elgsena.py) – visa programa su netikru Windows API ir tikru Tk (Xvfb). Tikrina tai,
ko kiti testai nemato: senis siauroje vietoje nedreba, per aukštas langas, langas prie ekrano viršaus, daug objektų,
„Išdėlioti iš naujo“; elgsenos sargai neturi suveikti, o dirbtinai sukeltas klaidas – pagauti."""
import os, subprocess, sys
cia = os.path.dirname(os.path.abspath(__file__))
env = dict(os.environ, SCENARIJUS=os.path.join(cia, "dumu", "elgsena.py"), FH="280")
r = subprocess.run([sys.executable, "-u", os.path.join(cia, "dumu", "paleisti.py"), sys.argv[1]], capture_output=True,
                   text=True, timeout=290, env=env)
print(r.stdout[-6000:])
if r.returncode:
    print(r.stderr[-3000:])
    print("0/1")
