<img width="962" height="372" alt="explorer_8M7qv8u89v" src="https://github.com/user-attachments/assets/ea3878f2-5177-4645-9edb-dc5538f0e537" />

# Sniegas

Sniegas paverčia Windows darbalaukį žiema: snaigės krenta virš langų, kaupiasi ant jų ir ekrano apačioje.

- Snaigės krenta ir svyruoja. Jas neša vėjas, gūsiai ir sūkuriai.
- Galima įjungti glotnų snaigių judėjimą: kraštai glotnūs, snaigės juda tolygiai, ne taškas po taško (labiau apkrauna kompiuterį).
- Sniegas kaupiasi ekrano apačioje (virš užduočių juostos) ir ant atidarytų langų viršaus.
- Apačioje stovi pixel art eglutės su mirksinčiomis lemputėmis.
- Sniegu rieda bumbuliukai.
- Vaikšto sniego seniai. Juos galima pačiupti pele už šaliko.
- Sniegą stumia buldozeriukai.
- Ekrano šonuose kabo girliandos.
- Pagal laikrodį danguje iššaunami fejerverkai.
- Yra paruošti nustatymų rinkiniai: nuo ramaus snygio iki pūgos.
- Sąsaja lietuvių arba anglų kalba.

<img width="1501" height="944" alt="sniegas1228" src="https://github.com/user-attachments/assets/9f70235b-58eb-447a-90e8-611247c405fd" />

## Reikalavimai

- Windows 10 arba 11.
- Python 3 su tkinter (įprastas diegimas iš [python.org](https://www.python.org/)). Papildomų bibliotekų nereikia.

## Paleidimas

```
py Sniegas.pyw
```

Arba dukart spustelėkite `Sniegas.pyw`. Programos piktograma atsiranda prie laikrodžio. Spustelėjus ją, atidaromi nustatymai.

## Kompiliavimas į .exe

Jei norite, kad programa veiktų be įdiegto Python:

```
py -m pip install pyinstaller
py Sniegas.pyw --ikona
py -m PyInstaller --onefile --noconsole --icon sniegas.ico --name Sniegas Sniegas.pyw
```

Paruoštas `Sniegas.exe` bus aplanke `dist`.

## Nustatymai ir diagnostika

- Nustatymai saugomi šalia programos, faile `sniegas_nustatymai.json`. Jei ten rašyti negalima (pvz., `Program Files`), jie saugomi `%APPDATA%\Sniegas`.
- Nustatymus galima eksportuoti ir importuoti skiltyje „Kita“.
- Diagnostikos žurnalas įjungiamas skiltyje „Diagnostika“ (numatytai jis išjungtas). Žurnalas `sniegas_diagnostika.log` rašomas šalia nustatymų.
- Ten pat – „Našumo testas…“ (~5 min): programa paeiliui įjungia įvairius nustatymus ir matuoja, kiek kiekvienas kainuoja (kadro laikas, procesorius, NVIDIA vaizdo plokštės galia). Rezultatai prirašomi į `sniegas_nasumas.txt` šalia nustatymų, jūsų nustatymai po testo grąžinami.
- Su Python 3.15 ar naujesniu ten pat yra mygtukas „Profilis…“: programa paleidžiama iš naujo su našumo profiliuotuvu, o ją išjungus šalia nustatymų įrašomas `sniegas_profilis.txt` – kurios programos dalys užima daugiausia laiko.

## Autoriai

- Autorius: Vilmantas Ramonas
- Testuotojas: Jonas Ramonas
- Sukurta su Claude (Anthropic) pagalba

## Licencija

[GNU General Public License v3.0](LICENSE) (GPL-3.0). Programą galima laisvai naudoti, keisti ir platinti, bet pakeistos versijos irgi turi būti platinamos su atviru kodu pagal tą pačią licenciją.

---

## English

Sniegas turns the Windows desktop into a winter scene: snowflakes fall over your windows and pile up on top of them and at the bottom of the screen.

- Snowflakes fall and sway, carried by wind, gusts and eddies.
- Optional smooth flake motion: smooth edges and even movement instead of pixel steps (uses more CPU).
- Snow builds up at the bottom of the screen (above the taskbar) and on top of open windows.
- Pixel art Christmas trees with blinking lights stand at the bottom.
- Glass baubles roll through the snow.
- Snowmen walk around; you can grab them by the scarf with the mouse.
- Little bulldozers push the snow.
- Light strings hang along the sides of the screen.
- Fireworks are launched on a schedule.
- Ready-made presets, from gentle snowfall to a blizzard.
- Lithuanian or English interface (switch in the top right corner of the settings window).

### Requirements

- Windows 10 or 11.
- Python 3 with tkinter (the standard installer from [python.org](https://www.python.org/)). No extra packages are needed.

### Running

```
py Sniegas.pyw
```

Or double-click `Sniegas.pyw`. The program icon appears next to the clock; click it to open the settings.

### Building an .exe

To run the program without Python installed:

```
py -m pip install pyinstaller
py Sniegas.pyw --ikona
py -m PyInstaller --onefile --noconsole --icon sniegas.ico --name Sniegas Sniegas.pyw
```

The finished `Sniegas.exe` will be in the `dist` folder.

### Settings and diagnostics

- Settings are saved next to the program in `sniegas_nustatymai.json`. If that folder is not writable (e.g. `Program Files`), they go to `%APPDATA%\Sniegas`.
- Settings can be exported and imported in the “Other” section.
- The diagnostics log is turned on in the “Diagnostics” section (off by default). The log `sniegas_diagnostika.log` is written next to the settings.
- The same section has “Performance test…” (~5 min): the program switches through various settings and measures what each one costs (frame time, CPU, NVIDIA graphics card power). Results are appended to `sniegas_nasumas.txt` next to the settings; your own settings are restored afterwards.
- With Python 3.15 or newer there is also “Profile…”: the program restarts under the performance profiler, and when you exit it writes `sniegas_profilis.txt` next to the settings, showing which parts of the program take the most time.

### Authors

- Author: Vilmantas Ramonas
- Tester: Jonas Ramonas
- Made with the help of Claude (Anthropic)

### License

[GNU General Public License v3.0](LICENSE) (GPL-3.0). You may freely use, modify and distribute the program, but modified versions must also be distributed as open source under the same license.
