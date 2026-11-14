# Sniego testai

Testai tikrina programos logiką be Windows: Windows API pakeičiamas netikru (`unittest.mock`), todėl jie veikia ir Linux.

```
python tests/paleisti_testus.py            # visi *_testas.py su ../Sniegas.pyw
python tests/paleisti_testus.py --dumai    # + 3 dūmų bandymai (visa programa, atsitiktiniai veiksmai)
python tests/vertimu_testas.py Sniegas.pyw # vienas testas
```

Reikia Python 3.12 ar naujesnio su tkinter. `ivedimo_testas.py` ir dūmų bandymams reikia tikro lango (Linux – Xvfb, pvz. `Xvfb :99 &` ir `DISPLAY=:99`).

## Aplankai

- `*_testas.py` – testai. Kiekvienas gauna programos bylą kaip pirmą argumentą ir pabaigoje parašo `praėjo/iš viso`.
- `dumu/` – dūmų bandymas: `paleisti.py Sniegas.pyw` paleidžia visą programą su netikru Windows API (`dumas.py` dar tikrina GDI objektų nutekėjimą ir kopijavimą už paveikslėlio ribų), `scenarijus.py` – atsitiktiniai veiksmai. Aplinkos kintamieji: `SEKLA`, `KADRU`, `DAZNIS`, `GYVAS=1` (daug senių, valytuvų, bumbuliukų, langų).
- `irankiai/` – vertimų .po bylos (`po_eksportas.py`, `po_en.py`, `po_pritaikymas.py`) ir nustatymų lango nuotrauka (`visas_langas.py`).
