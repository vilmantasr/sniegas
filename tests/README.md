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
- `dumu/` – dūmų bandymas: `paleisti.py Sniegas.pyw` paleidžia visą programą su netikru Windows API (`dumas.py` dar tikrina GDI objektų nutekėjimą ir kopijavimą už paveikslėlio ribų), `scenarijus.py` – atsitiktiniai veiksmai. Aplinkos kintamieji: `SEKLA`, `KADRU`, `DAZNIS`, `GYVAS=1` (daug senių, valytuvų, bumbuliukų, langų; įjungtas ledas, jis susidaro po `LEDO_LAIKAS` s – numatyta 2), `KAUP` (sniego kaupimosi greitis).
- `elgsenos_testas.py` + `dumu/elgsena.py` – elgsenos bandymai su visa programa (reikia Xvfb): siaura lango vieta, per aukštai pakeltas langas, langas prie ekrano viršaus, daug objektų, „Išdėlioti iš naujo“, didelio senio šuolis nuo lango. Tikrinama ir **elgsenos sargais** (`Sniegas.sargu_zingsnis`: blaškosi, krenta vis į tą pačią vietą, krenta be galo, už ekrano, užstrigo, bumbuliukas be vietos) – nė vienas neturi suveikti; sargų savitikra dirbtinai sukelia kiekvieną klaidą. Kitas scenarijus dūmų bandymui – aplinkos kintamasis `SCENARIJUS`.
- `gylio_testas.py` + `dumu/gylis.py` – **gylio** bandymas (reikia Xvfb): atsitiktinės scenos su 3–4 langais vienas virš kito, seniais, valytuvais, bumbuliukais, konfeti, gabalais, purslais, gumulais ir šukėmis. Kiekviename kadre užfiksuojama piešimo tvarka ir tikrinama viena taisyklė: kas toliau (aukštesnio lango gylyje), nenupieštas ant to, kas arčiau, jei persidengia. Gylio „tiesa“ nustatoma nepriklausomai nuo programos žymų (pagal paviršių ir dalelės kilmę); dviprasmiškais atvejais – pagal programos žymą.
- `saveikos_testas.py` + `dumu/saveikos.py` – sąveikų bandymai (reikia Xvfb, nuo 13.04): nukritęs senis pašokdina šalia gulintį bumbuliuką; gumulas ant senio galvos (vaikštantis susiūbuoja, „Tik stovi vietoje“ – daugiau sniego ir „apči“, to paties ar tolimesnio lango gumulas nepataiko); pustymas nuo langų (dulkės – lango gylyje); kylantis srautas gūsio priekyje (ir jo nėra, kai vėjas pereina per 0); sniegas ant eglių prisninga pakopomis, nupučiamas, perdėliojus išlieka, nuvalius – nuvalomas; spalvoti blizgesiai prie lempučių; tolimų glotnių snaigių permatomumas; išeinantis senis, įjungus „Tik stovi vietoje“, grįžta į ekraną.
- `irankiai/` – vertimų .po bylos (`po_eksportas.py`, `po_en.py`, `po_pritaikymas.py`) ir nustatymų lango nuotrauka (`visas_langas.py`).
