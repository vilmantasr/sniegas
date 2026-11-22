"""13.04: sąveikų testas (dumu/saveikos.py) – visa programa su netikru Windows API ir tikru Tk (Xvfb). Nukritęs senis
pašokdina bumbuliukus, gumulas ant senio galvos, pustymas nuo langų, kylantis srautas gūsio priekyje, sniegas ant
eglių."""
import os, subprocess, sys
cia = os.path.dirname(os.path.abspath(__file__))
env = dict(os.environ, SCENARIJUS=os.path.join(cia, "dumu", "saveikos.py"), FH="280")
r = subprocess.run([sys.executable, "-u", os.path.join(cia, "dumu", "paleisti.py"), sys.argv[1]], capture_output=True,
                   text=True, timeout=290, env=env)
print(r.stdout[-6000:])
if r.returncode:
    print(r.stderr[-3000:])
    print("0/1")
