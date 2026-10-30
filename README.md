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

<img width="1494" height="1024" alt="Sniegas_v12 14_yxIcpEUTJy" src="https://github.com/user-attachments/assets/e6d6dd99-c45d-4676-b8f8-7811780f1710" />

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
- Diagnostikos žurnalas įjungiamas skiltyje „Kita“ (numatytai jis išjungtas). Žurnalas `sniegas_diagnostika.log` rašomas šalia nustatymų.

## Autoriai

- Autorius: Vilmantas Ramonas
- Testuotojas: Jonas Ramonas
- Sukurta su Claude (Anthropic) pagalba

## Licencija

[GNU General Public License v3.0](LICENSE) (GPL-3.0). Programą galima laisvai naudoti, keisti ir platinti, bet pakeistos versijos irgi turi būti platinamos su atviru kodu pagal tą pačią licenciją.

---

## English

Sniegas turns the Windows desktop into a winter scene: snow falls over windows and piles up on them and at the bottom of the screen.

Also:

- optional smooth flake motion (smooth edges, even movement; uses more CPU);
- pixel art trees, rolling baubles, snowmen you can grab by the scarf, little bulldozers, light strings and scheduled fireworks;
- English interface available.

Requirements: Windows 10/11 and Python 3 with tkinter, with no extra packages. To run it: `py Sniegas.pyw`. License: GPL-3.0.
