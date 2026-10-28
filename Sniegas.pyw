#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sniegas – sninga ant Windows darbalaukio. Sąsaja lietuvių arba anglų kalba.
Autorius: Vilmantas Ramonas. Licencija: GNU General Public License v3.0 (GPL-3.0, žr. LICENSE).

Permatomas, pro jį spaudžiamas sluoksnis virš visų langų. Sniegas krenta, jį neša vėjas ir sūkuriai, jis kaupiasi
ekrano apačioje (virš užduočių juostos) ir ant atidarytų langų viršaus. Apačioje stovi pixel art eglutės su
mirksinčiomis lemputėmis; gali riedėti bumbuliukai, vaikščioti sniego seniai (pele pačiumpami už šaliko), važinėti
sniegą stumiantys buldozeriukai, ekrano šonuose kabėti girliandos, o pagal laikrodį danguje iššaunami fejerverkai.
Reikia tik Python 3 su tkinter (Windows 10/11), be papildomų bibliotekų. Piešiama tiesiogiai per Windows GDI su
dviem atminties buferiais, perpiešiant tik pasikeitusius stačiakampius.

Kompiliavimas į .exe (Windows, kad veiktų be įdiegto Python):
    py -m pip install pyinstaller
    py Sniegas.pyw --ikona          (šalia programos sukuria sniegas.ico)
    py -m PyInstaller --onefile --noconsole --icon sniegas.ico --name Sniegas Sniegas.pyw
Paruoštas Sniegas.exe – aplanke dist. Nustatymai saugomi šalia programos (jei ten rašyti negalima –
%APPDATA%\\Sniegas).

Diagnostika (įjungiama skiltyje „Kita“, numatytai išjungta): šalia nustatymų rašomas sniegas_diagnostika.log –
kas minutę viena suvestinės eilutė (kadrai, darbo laikas, procesorius, atmintis, GDI objektai, ką teko
perpiešti) ir visi įvykiai bei klaidos. Programos lūžiai užrašomi visada.
"""

import base64
import bisect
import ctypes
import functools
import gc
import itertools
import json
import math
import os
import platform
import random
import re
import struct
import sys
import tempfile
import threading
import time
import traceback
import webbrowser
import zlib
from ctypes import wintypes
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

VERSIJA = "12.16"
DATA = "2026-10-28"
PAVADINIMAS = f"Sniegas {VERSIJA} ({DATA})"

AUTORIUS = "Vilmantas Ramonas"
LICENCIJOS_NUORODA = "https://www.gnu.org/licenses/gpl-3.0.html"
TESTUOTOJAS = "Jonas Ramonas"
KALBOS = ("lt", "en")


KALBA = "lt"  # numatytoji kalba – visada lietuvių (anglų – pasirinkus EN)


def nustatyti_kalba(kalba):
    global KALBA
    KALBA = kalba if kalba in KALBOS else "lt"


def T(tekstas):
    """Sąsajos tekstas pasirinkta kalba. Raktas – lietuviškas tekstas, todėl lietuviškai kodas skaitomas kaip anksčiau."""
    return EN.get(tekstas, tekstas) if KALBA == "en" else tekstas


EN = {
    "Ramus vakaras": "Calm evening",
    "Pūga": "Blizzard",
    "Šventė": "Celebration",
    "Darbui": "For work",
    "Pritaikyti paruoštuką „{p}“?": "Apply the “{p}” preset?",
    "Keičiami tik šio paruoštuko nustatymai, kiti lieka tokie, kokie yra.": "Only this preset's settings change; the rest stay as they are.",
    "Paruošti nustatymų rinkiniai. Keičia tik savo nustatymus – kiti lieka tavo.": "Ready-made setting sets. Each changes only its own settings – the rest stay yours.",
    "Paruoštukai": "Presets",
    "Per fejerverkus bumbuliukai slepiasi – pasirodys po šou": "Baubles hide during the fireworks – back after the show",
    "Numatytieji nustatymai": "Default settings",
    "Retos snaigės": "Sparse snowflakes",
    "Sninga lėtai, eglutės, sniego senis": "Slow snowfall, trees, a snowman",
    "Eglutės, girliandos, fejerverkai": "Trees, light strings, fireworks",
    "Daug sniego, vėjas, buldozeriukai": "Heavy snow, wind, bulldozers",
    "Pažymėtas ✓ – šiuo metu galiojantis; pakeitus jo nustatymą, žymė dingsta.": "Marked ✓ – currently in effect; change any of its settings and the mark disappears.",
    "Apie…": "About…",
    "versija {v} ({d})": "version {v} ({d})",
    "Apie": "About",
    "Uždaryti": "Close",
    "Autorius": "Author",
    "Testuotojas": "Tester",
    "Laisva programa – GNU GPL 3.0 licencija": "Free software – GNU GPL 3.0 license",
    "Galima laisvai naudoti, keisti ir platinti; pakeistos versijos – irgi su atviru kodu pagal tą pačią licenciją. "
    "Spustelėkite – licencijos tekstas.":
        "You may use, change and share it freely; changed versions must also be open source under the same license. "
        "Click to open the license text.",
    "Sukurta su Claude (Anthropic) pagalba": "Made with the help of Claude (Anthropic)",
    "Numatytasis": "Default",
    "Grąžina visus nustatymus į numatytuosius (kalba lieka).": "Resets all settings to defaults (language stays).",
    "Nėra nė vieno rašto ar spalvos – bumbuliukų nebus": "No pattern or color selected – no baubles",
    "Vidurinis pelės mygtukas – paslėpti / rodyti": "Middle mouse button – hide / show",
    # antraštė, mygtukai
    "Kalba": "Language",
    "Išjungti sniegą": "Snow off",
    "Įjungti sniegą": "Snow on",
    "Paslėpti viską": "Hide all",
    "Rodyti viską": "Show all",
    "Į sistemos dėklą": "To system tray",
    "Išjungti": "Exit",
    "Atkurti numatytuosius": "Restore defaults",
    "Nustatymai…": "Settings…",
    # snaigės
    "Snaigės": "Snowflakes",
    "Rūšis": "Type",
    "Kiek (0–{m})": "Count (0–{m})",
    "Taškelis": "Speck",
    "Mažas rutuliukas": "Small pellet",
    "Rutuliukas": "Pellet",
    "Žvaigždutė": "Star",
    "Kryžiukas": "Cross",
    "Šakotoji": "Branched",
    "Puošnioji": "Ornate",
    "Plunksninė": "Feathery",
    "Šešiakampė plokštelė": "Hexagonal plate",
    "Sektorinė plokštelė": "Sectored plate",
    "Žvaigždinė plokštelė": "Stellar plate",
    "Dvylikašakė": "Twelve-branched",
    "Stulpelis su kepurėlėmis": "Capped column",
    "Iš viso snaigių": "Total flakes",
    "Dukart spustelėkite pavadinimą – numatytieji ({v}, įprastas rūšių mišinys)":
        "Double-click the label for the defaults ({v}, the usual mix of kinds)",
    "Lemputės ant šluotos": "Lights on the broom",
    "Mirksi": "Blinking",
    "Lėtai įsižiebia ir užgęsta": "Slowly fade in and out",
    "Bėga iš apačios į viršų": "Running upwards",
    "Šviečia nemirksėdamos": "Steady",
    "iš {m}": "of {m}",
    "Bendras snaigių kiekis. Pakeitus jį čia, kiekis atsitiktinai paskirstomas po rūšis (kiek kurios – matosi "
    "rūšių eilutėse aukščiau). Vėl pakeitus po pertraukos – parenkamas naujas atsitiktinis rūšių mišinys.":
        "Total number of flakes. When changed here, it is split randomly among the kinds (each kind's count is "
        "shown in its row above). Changing it again after a pause picks a new random mix.",
    "Dydis, %": "Size, %",
    "Kritimo greitis, %": "Fall speed, %",
    "Stilius": "Style",
    "Pixel art": "Pixel art",
    "Įprastos": "Classic",
    "Snaigės sukasi": "Flakes rotate",
    "Sniego kontūras ekrano apačioje": "Snow outline at the bottom of the screen",
    "Plona melsva linija sukaupto sniego viršuje. Ant langų ji būna visada – be jos sniegas ant baltų langų nesimatytų.":
        "A thin bluish line on top of the piled snow. On windows it is always there – without it snow on white "
        "windows would be invisible.",
    "Sniegas kartais sužiba": "Snow sparkles now and then",
    # vėjas, kaupimasis, kita
    "Vėjas": "Wind",
    "Įprastas vėjas": "Normal wind",
    "Gūsio stiprumas": "Gust strength",
    "Kryptis": "Direction",
    "Kintanti": "Changing",
    "Į dešinę": "To the right",
    "Į kairę": "To the left",
    "Sūkuriai": "Swirls",
    "Gūsis dabar": "Gust now",
    "Užveskite pelę ant nustatymo": "Hover over a setting",
    "vėjas {r} {v}": "wind {r} {v}",
    "ramu": "calm", "gūsis": "gust", "rimsta": "easing",
    "Vėjo skaičiai – sąlyginiai vienetai, ne m/s. 1 – artimos snaigės nunešamos į šoną apie 12 taškų per sekundę "
    "(1920×1080 ekrane; didesniame – proporcingai), 3 – apie 36 ir t. t.; tolimos – lėčiau.":
        "Wind numbers are relative units, not m/s. 1 – near flakes drift sideways about 12 pixels per second "
        "(on a 1920×1080 screen; proportionally more on larger ones), 3 – about 36 and so on; distant ones – slower.",
    "Ramiu metu vėjas kas 5–12 s pasirenkamas iš naujo: nuo 0 iki 0,7 šios reikšmės (kintančios krypties – kartais "
    "trumpam ir atgal). Gūsio metu – tiek, kiek „Gūsio stiprumas“.":
        "In calm periods the wind is re-chosen every 5–12 s: from 0 to 0.7 of this value (with changing direction – "
        "sometimes briefly backwards). During a gust – as much as “Gust strength”.",
    "Peržiūroje – dabartinis vėjas: kryptis, stiprumas ir ar dabar ramu, gūsis, ar jis rimsta.":
        "The preview shows the current wind: direction, strength and whether it is calm, gusting or easing.",
    "Sniego kaupimasis": "Snow accumulation",
    "Kaupti ekrano apačioje": "Pile up at the bottom of the screen",
    "Didžiausias aukštis, px": "Maximum height, px",
    "Kaupti ant langų viršaus": "Pile up on top of windows",
    "Kaupimosi greitis, %": "Accumulation speed, %",
    "Nuvalyti sniegą": "Clear snow",
    "Didžiausias aukštis apačioje, px": "Max height at the bottom, px",
    "Visi šios skilties nustatymai – numatytieji.": "All settings in this section are at their defaults.",
    "Spustelėkite (arba Tarpas), kad pakeistumėte. Dešiniuoju – tik šis / vėl visi.":
        "Click (or Space) to toggle. Right-click – only this one / all again.",
    "Sustabdyti": "Stop",
    "Dukart spustelėkite – išvalyti klaidą ir skaitiklius.": "Double-click to clear the error and counters.",
    "Didžiausias aukštis languose, px": "Max height on windows, px",
    "Grąžinti šios skilties nustatymus į numatytuosius (įjungimo varnelė nekeičiama).":
        "Reset this section's settings to defaults (the on/off checkbox is not changed).",
    "Grąžinti skilties „{s}“ nustatymus į numatytuosius?": "Reset the “{s}” section's settings to defaults?",
    "Nustatymai": "Settings",
    "Eksportuoti…": "Export…",
    "Importuoti…": "Import…",
    "Išsaugoti visus nustatymus į bylą (pvz., perkelti į kitą kompiuterį).":
        "Save all settings to a file (e.g. to move them to another computer).",
    "Įkelti nustatymus iš bylos. Kalba lieka dabartinė; byloje nesantys nustatymai – numatytieji.":
        "Load settings from a file. The language stays as it is; settings missing from the file get defaults.",
    "Nustatymų byla": "Settings file",
    "Nustatymai išsaugoti:": "Settings saved:",
    "Nepavyko išsaugoti:": "Could not save:",
    "Nepavyko perskaityti nustatymų bylos:": "Could not read the settings file:",
    "Įkelti nustatymus iš šios bylos? Dabartiniai nustatymai bus pakeisti.":
        "Load settings from this file? The current settings will be replaced.",
    "Byloje įjungtos išplėstos ribos – jos leidžia daug didesnius kiekius ir dydžius, kompiuteris gali strigti."
    "\n\nĮjungti? (Ne – reikšmės bus apribotos įprastomis ribomis.)":
        "The file has extended limits turned on – they allow much larger amounts and sizes, the computer may lag."
        "\n\nTurn them on? (No – values will be clamped to the normal limits.)",
    "Kita": "Other",
    "Kadrų per sekundę": "Frames per second",
    "Slėpti sniegą, kai kita programa per visą ekraną": "Hide snow when another app is full screen",
    "Paleisti kartu su Windows": "Start with Windows",
    "Išjungimo mygtukas": "Close button",
    "Klausti": "Ask",
    "Išjungti programą": "Exit program",
    # fejerverkai
    "Fejerverkai": "Fireworks",
    "Kas kiek minučių": "Every N minutes",
    "Trukmė, s": "Duration, s",
    "Paleisti dabar": "Launch now",
    "Didysis šou! Liko {m}:{s}": "Grand show! {m}:{s} left",
    "Kitas šou: {kada} (po {min} min)": "Next show: {kada} (in {min} min)",
    "Išjungta": "Off",
    "Fejerverkai rodomi tik tada, kai sniegas matomas.": "Fireworks are shown only while the snow is visible.",
    "Bijūnas": "Peony", "Chrizantema": "Chrysanthemum", "Gluosnis": "Willow", "Palmė": "Palm", "Žiedas": "Ring",
    "Dvigubas žiedas": "Double ring", "Širdelė": "Heart", "Žvaigždė": "Star", "Kryžminė": "Crossette",
    "Spragsiukai": "Crackle", "Mirksintis": "Strobe", "Įvairiaspalvis": "Multicolor",
    "Spalvą keičiantis": "Color-changing", "Šypsenėlė": "Smiley", "Snaigė": "Snowflake",
    "Eglutė": "Christmas tree", "Spiralė": "Spiral", "Saturnas": "Saturn", "Krioklys": "Waterfall",
    "Žuvytės": "Fish", "Jurginas": "Dahlia", "Su šerdimi": "With pistil", "Kamuras": "Kamuro",
    "Signalinė raketa": "Signal flare", "Romėniška žvakė": "Roman candle", "Fontanas": "Fountain",
    # bumbuliukai
    "Bumbuliukai": "Baubles",
    "Rieda ir pašokinėja (išjungus – tiesiog stovi)": "Roll and bounce (off – they just stand)",
    "Kartais pradingsta ir atsiranda kitur": "Sometimes vanish and reappear elsewhere",
    "Rieda ir ant langų (nuo jų nurieda ir nukrenta)": "Also roll on windows (and fall off them)",
    "Susitraukia": "Shrink", "Sudūžta": "Shatter", "Ištirpsta": "Melt", "Įsmenga į sniegą": "Sink into snow",
    "Kiek bumbuliukų": "Number of baubles",
    "Judrumas, %": "Liveliness, %",
    "Kaip stipriai bumbuliukai retkarčiais pastumiami, kai beveik sustoja. Mažai – dažniau guli vietoje, "
    "daug – nuolat rieda. Nuokalnėmis ir pučiant vėjui jie rieda vienodai.":
        "How hard the baubles get a nudge when they almost stop. Low – they mostly lie still, high – they keep "
        "rolling. Slopes and wind move them the same either way.",
    "0 – visai nepastumiami (rieda tik nuokalnėmis ir pučiant vėjui).": "0 – never nudged (they roll only on slopes and in wind).",
    "Įprastas vėjas pučia iki maždaug 0,7 savo reikšmės (dabar – iki {v}); gūsis – maždaug tiek, kiek nustatyta čia.":
        "Normal wind blows up to about 0.7 of its value (now up to {v}); a gust is about as strong as set here.",
    "Šiame ekrane su dabartiniu dydžiu telpa iki {n} lempučių – daugiau nebus.":
        "On this screen, at the current size, up to {n} bulbs fit – no more will be shown.",
    "⚠ Gūsis ({g}) silpnesnis už įprastą vėją, kuris pučia iki {v}: gūsiai beveik nesijaus, o stipriai pučiant "
    "gūsis vėją net susilpnina. Padidinkite „Gūsio stiprumą“ bent iki {n} arba sumažinkite „Įprastą vėją“.":
        "⚠ The gust ({g}) is weaker than the normal wind, which blows up to {v}: gusts will hardly be felt, and in "
        "strong wind a gust even weakens it. Raise “Gust strength” to at least {n} or lower “Normal wind”.",
    "⚠ Nustatyta {k} lempučių, bet šiame ekrane su dydžiu {d} % telpa tik {n} – daugiau nerodoma. "
    "Sumažinkite dydį arba lempučių kiekį.":
        "⚠ {k} bulbs are set, but at size {d} % only {n} fit on this screen – the rest are not shown. "
        "Reduce the size or the number of bulbs.",
    "⚠ Mažiausias aukštis ({a}) didesnis už didžiausią ({b}) – kitas pakoreguojamas po akimirkos.":
        "⚠ The minimum height ({a}) is above the maximum ({b}) – the other one is adjusted in a moment.",
    "Tai vienintelis pasirinktas – bent vienas turi likti.": "This is the only one selected – at least one must stay.",
    "Lygus": "Plain", "Juosta": "Stripe", "Dvi juostos": "Two stripes", "Taškai": "Dots",
    "Zigzagas": "Zigzag", "Langeliai": "Checks",
    "Saulutė": "Sun", "Aušrinė": "Morning star", "Žiedelis": "Flower", "Rombai": "Rhombs",
    "Raštai ir spalvos": "Patterns and colors",
    "Raštas": "Pattern", "Spalva": "Color",
    "Raudona": "Red", "Žalia": "Green", "Auksinė": "Gold", "Mėlyna": "Blue", "Violetinė": "Purple",
    "Sidabrinė": "Silver", "Rožinė": "Pink", "Turkio": "Teal",
    "naudojamas": "used", "nenaudojamas": "not used", "naudojama": "used", "nenaudojama": "not used",
    "Bumbuliukai išjungti – įjunkite skilties antraštėje.": "Baubles are off – turn them on in the section header.",
    "Išbarstyti iš naujo": "Scatter again",
    # eglutės
    "Eglutės": "Trees",
    "Kiek eglučių": "Number of trees",
    "Vienodo aukščio": "Same height",
    "   Aukštis, px": "   Height, px",
    "Atsitiktinio aukščio": "Random height",
    "   Mažiausias, px": "   Minimum, px",
    "   Didžiausias, px": "   Maximum, px",
    "Papuošimai": "Decorations",
    "Lemputės": "Lights",
    "Lemputės mirksi": "Lights blink",
    "Burbuliukai": "Ornaments",
    "Sniegas ant šakų": "Snow on branches",
    "Eglių plotis": "Tree width",
    "Taškais 1920×1080 ekrane; didesniame – proporcingai daugiau (šiame ekrane ×{k}, t. y. iki {px} px).":
        "In pixels on a 1920×1080 screen; proportionally more on larger ones (×{k} on this screen, i.e. up to {px} px).",
    "Įvairus": "Mixed",
    "Be siaurų": "No narrow",
    "Vienodas": "Uniform",
    "Siauros, vidutinės ir plačios eglės (siauriausios – {p} % įprasto pločio).":
        "Narrow, medium and wide trees (the narrowest are {p} % of the normal width).",
    "Vidutinės ir plačios eglės (siauriausios – {p} % įprasto pločio).":
        "Medium and wide trees (the narrowest are {p} % of the normal width).",
    "Visos eglės – įprasto pločio.": "All trees have the normal width.",
    "Išdėlioti iš naujo": "Rearrange",
    "mastelis {p}": "scale {p}",
    # išjungimo klausimas, dėklas
    "Ką daryti paspaudus išjungimo mygtuką?": "What should the close button do?",
    "Sistemos dėkle sniegas veikia toliau – nustatymus atversite\nspustelėję piktogramą prie laikrodžio.":
        "In the system tray the snow keeps falling – open the settings\nby clicking the icon next to the clock.",
    "Atšaukti": "Cancel",
    "Daugiau neklausti (pakeisti galima skiltyje „Kita“)": "Don't ask again (can be changed under “Other”)",
    "Sniegas veikia toliau. Nustatymai ir išjungimas – per piktogramą prie laikrodžio.":
        "Sniegas keeps running. Settings and exit – via the icon next to the clock.",
    # būsena
    "Viskas paslėpta.": "Everything hidden.",
    "Pristabdyta – programa per visą ekraną.": "Paused – an app is full screen.",
    "Snaigių: {a}   Kadrų per sek.: {b}   Kadrui: {c} ms   Langų su sniegu: {d}":
        "Flakes: {a}   FPS: {b}   Per frame: {c} ms   Windows with snow: {d}",
    "   Fizika / atstatymas / piešimas / ekranas: {a} / {r} / {b} / {c} ms ({n} kop.)":
        "   Physics / restore / draw / screen: {a} / {r} / {b} / {c} ms ({n} blits)",
    "   Windows trynė vaizdą: {n} k.": "   Windows erased the image: {n}×",
    "   Ekranai keitėsi: {n} k.": "   Display changes: {n}×",
    "   Klaida: {e}": "   Error: {e}",
    # pranešimai
    "Nepavyko perskaityti nustatymų bylos – naudojami numatytieji.": "Could not read the settings file – using defaults.",
    "Kai kurie nustatymai byloje netinkami – jiems naudojamos numatytosios reikšmės:":
        "Some settings in the file are invalid – defaults are used for them:",
    "Nepavyko išsaugoti nustatymų. Gal programos aplankas tik skaitymui?":
        "Could not save the settings. Is the program folder read-only?",
    "Įvyko klaida, bet programa bando dirbti toliau. Jei sniegas elgiasi keistai – paleiskite programą iš naujo.":
        "An error occurred, but the program keeps running. If the snow behaves strangely, restart the program.",
    "Grąžinti visus nustatymus į numatytuosius?": "Restore all settings to defaults?",
    "Nepavyko pakeisti automatinio paleidimo nustatymo.": "Could not change the startup setting.",
    "„Sniegas“ jau veikia – jo piktogramą rasite prie laikrodžio.":
        "“Sniegas” is already running – its icon is next to the clock.",
    "Nepavyko paleisti programos.": "Could not start the program.",
    "Diagnostikos žurnalas": "Diagnostic log",
    "Išplėstos ribos": "Extended limits",
    "Leidžia nustatyti daug didesnius kiekius ir dydžius. Kompiuteris gali pradėti strigti.":
        "Allows much larger amounts and sizes. The computer may start to lag.",
    "Kaip stipriai pučia vėjo gūsis. Gūsiai būna vidutiniškai kas 30 s ir trunka apie 4 s. 0 – gūsių nėra.":
        "How strong a wind gust is. Gusts come about every 30 s on average and last about 4 s. 0 – no gusts.",
    "Krentančios snaigės. Žemiau – kiek ir kokių rūšių, kaip krenta ir atrodo.":
        "Falling snowflakes. Below – how many and which kinds, how they fall and look.",
    "Vėjas, gūsiai ir sūkuriai. Išjungus – oras ramus: snaigės krenta, tik svyruoja.":
        "Wind, gusts and swirls. When off – calm air: flakes fall and only sway.",
    "Sniegas kaupiasi ekrano apačioje ir (ar) ant langų. Išjungus – sukauptas sniegas dingsta ir nebesikaupia.":
        "Snow piles up at the bottom of the screen and/or on windows. When off – the piled snow disappears and no more piles up.",
    "Pixel art eglutės ekranų apačioje – su lemputėmis ir papuošimais.":
        "Pixel art trees along the bottom of the screens – with lights and ornaments.",
    "Retro lempučių girliandos ekrano kairėje ir dešinėje – nuo viršaus iki užduočių juostos.":
        "Retro bulb strings on the left and right of the screen – from the top down to the taskbar.",
    "Fejerverkų šou pagal laikrodį: kas kiek minučių ir kiek trunka – žemiau. „Paleisti dabar“ veikia ir išjungus.":
        "Firework shows by the clock: how often and how long – below. “Launch now” works even when off.",
    "Kalėdiniai bumbuliukai, riedantys sniegu ekrano apačioje (ir ant langų).":
        "Christmas baubles rolling over the snow at the bottom of the screen (and on windows).",
    "Sniego senis ekrano apačioje. Pele jį galima pačiupti už šaliko ir nunešti.":
        "A snowman at the bottom of the screen. You can grab him by the scarf with the mouse and carry him.",
    "Buldozeriukai, kurie važinėja ir stumia sniegą – ekrano apačioje ir ant langų.":
        "Little bulldozers that drive around and push snow – at the bottom of the screen and on windows.",
    "Sniegas kaupiasi ekrano apačioje pusnimis. Išjungus – apačioje sukauptas sniegas dingsta.":
        "Snow piles up in drifts at the bottom of the screen. When off – the snow piled there disappears.",
    "Sniegas kaupiasi ant atidarytų langų viršutinio krašto.":
        "Snow piles up on the top edge of open windows.",
    "Kai aktyvi programa užima visą ekraną (žaidimas, filmas, pristatymas), sniegas paslepiamas. Išdidinti įprasti langai – ne.":
        "When the active program fills the whole screen (a game, a film, a presentation), the snow is hidden. Ordinary maximized windows – not.",
    "Rašo techninį žurnalą sniegas_diagnostika.log (kadrų trukmės, klaidos) – kai reikia ieškoti problemos. „Atverti“ – parodo žurnalą.":
        "Writes a technical log sniegas_diagnostika.log (frame times, errors) – for tracking down problems. “Open” – shows the log.",
    "Snaigės krisdamos sukasi. Išjungus – nesisuka, tik svyruodamos lengvai pasvyra į šoną.":
        "Flakes spin as they fall. When off – they do not spin, only tilt slightly as they sway.",
    "Ant sukaupto sniego ir krentančių snaigių kartais sužiba kibirkštėlė.":
        "Now and then a sparkle glints on the piled snow and on falling flakes.",
    "Įprastos – glotnios snaigės; Pixel art – stambiais taškais, kaip senuose žaidimuose.":
        "Classic – smooth flakes; Pixel art – chunky pixels, like in old games.",
    "Kintanti – vėjas kartais pasikeičia ir trumpam papučia atgal; „Į dešinę“ ir „Į kairę“ – visada ta kryptimi.":
        "Changing – the wind sometimes turns and briefly blows back; “To the right” and “To the left” – always that way.",
    "Šviečiančių lempučių stikle kartais blyksteli atspindys.":
        "A reflection now and then flashes in the glass of lit bulbs.",
    "Bumbuliukai rieda nuokalnėmis, juos stumia vėjas, kartais pašoka. Išjungus – stovi vietoje.":
        "Baubles roll down slopes, the wind pushes them, sometimes they hop. When off – they stand still.",
    "Bumbuliukai rieda ir ant langų viršaus, nuo krašto nurieda ir nukrenta.":
        "Baubles also roll on top of windows, roll off the edge and fall.",
    "Bumbuliukai kartais pradingsta ir atsiranda kitur. Kaip pradingsta – pažymėkite žemiau (kiekvieną kartą parenkamas vienas iš pažymėtų).":
        "Baubles now and then vanish and reappear elsewhere. How they vanish – tick below (one of the ticked ways is picked each time).",
    "Vienodo aukščio – visos eglutės vienodos; atsitiktinio – aukščiai tarp mažiausio ir didžiausio.":
        "Same height – all trees alike; random – heights between the minimum and the maximum.",
    "Spalvotos lemputės ant eglučių.":
        "Colored lights on the trees.",
    "Lemputės mirksi – kiekviena eglutė savo ritmu.":
        "The lights blink – each tree at its own rhythm.",
    "Žaisliukai ant eglučių šakų.":
        "Ornaments on the branches.",
    "Ant dalies šakų viršaus – sniego juostelės.":
        "Strips of snow on top of some branches.",
    "Senis stovi vietoje (kartais pajudina rankas, pasuka galvą). Išjungus – vaikšto. Pačiupti pele galima visada.":
        "The snowman stands in place (now and then moves his arms, turns his head). When off – he walks. You can always grab him.",
    "Stovinčiam seniui pamažu prisninga ant galvos, šakelių galvoje, rankų ir šluotos. Pajudėjus (pačiupus pele, numetus) sniegas nubyra.":
        "Snow slowly settles on a standing snowman’s head, the twigs on it, arms and broom. When he moves (grabbed with the mouse, dropped) the snow falls off.",
    "Girliandos lemputės ant šluotos; kaip šviečia – pasirinkite šalia.":
        "String-light bulbs on the broom; how they shine – choose next to it.",
    "Kaip šviečia lemputės ant šluotos.":
        "How the bulbs on the broom shine.",
    "Ką daro nustatymų lango X: kaskart paklausia, sumažina į sistemos dėklą (sniegas lieka) arba išjungia programą.":
        "What the settings window X does: asks each time, minimizes to the tray (snow stays) or exits the program.",
    "Numatytoji reikšmė – įjungta.": "Default value – on.",
    "Numatytoji reikšmė – išjungta.": "Default value – off.",
    "Numatytoji reikšmė – „{t}“.": "Default value – “{t}”.",
    "Programa pasileidžia automatiškai prisijungus prie Windows.": "The program starts automatically when you sign in to Windows.",
    "Vienas iš būdų, kaip bumbuliukas pradingsta (ir atitinkamai atsiranda). Parenkamas atsitiktinai iš pažymėtų.":
        "One of the ways a bauble vanishes (and reappears accordingly). Picked at random from the ticked ones.",
    "⚠ Bent vienas pradingimo būdas turi likti (norint, kad nepradingtų – nuimkite varnelę viršuje).":
        "⚠ At least one way must stay ticked (to stop them vanishing – untick the box above).",
    "⚠ Reikia įjungti „Kaupti ant langų viršaus“ (skiltyje „Sniego kaupimasis“).":
        "⚠ Turn on “Pile up on top of windows” (in “Snow accumulation”) first.",
    "⚠ Veikia tik kai įjungta „Tik stovi vietoje“.": "⚠ Only works when “Just stands still” is on.",
    "Nepavyko perrašyti piktogramos – greičiausiai ją laiko atidariusi kita programa (dažniausiai Failų "
    "naršyklės langas su šiuo aplanku rodo jos paveikslėlį). Uždarykite to aplanko langą arba ištrinkite "
    "sniegas.ico ir paleiskite dar kartą.":
        "Could not overwrite the icon – most likely another program has it open (usually a File Explorer window "
        "showing this folder displays its picture). Close that folder window or delete sniegas.ico and run again.",
    "Numatytoji reikšmė – {v}. Dukart spustelėkite pavadinimą, kad ją grąžintumėte.":
        "Default value – {v}. Double-click the name to restore it.",
    "Snaigių dydis, % įprasto.":
        "Snowflake size, % of normal.",
    "Kaip greitai snaigės krenta: 100 – įprastai, 200 – dvigubai greičiau.":
        "How fast the flakes fall: 100 – normal, 200 – twice as fast.",
    "Kiek daugiausia sniego susikaupia ekrano apačioje (pusnys – atskiri kalneliai, ne lygus sluoksnis).":
        "The most snow that piles up at the bottom of the screen (drifts are separate mounds, not a flat layer).",
    "Kiek daugiausia sniego susikaupia ant langų viršaus.":
        "The most snow that piles up on top of windows.",
    "Kaip greitai sniegas kaupiasi: 100 – įprastai, 200 – dvigubai greičiau, 50 – perpus lėčiau.":
        "How fast snow piles up: 100 – normal, 200 – twice as fast, 50 – half as fast.",
    "Kaip stipriai oro sūkuriai suka snaiges – kaimyninės juda kartu, pučiant stipriau – ir sūkuriai stipresni. 0 – sūkurių nėra.":
        "How strongly air swirls turn the flakes – neighbours move together; stronger wind – stronger swirls. 0 – no swirls.",
    "Šou paleidžiamas kas tiek minučių, skaičiuojant nuo vidurnakčio (60 – kiekvienos valandos pradžioje, 30 – kas pusvalandį).":
        "A show starts every N minutes, counted from midnight (60 – at the start of every hour, 30 – every half hour).",
    "Šou trukmė sekundėmis.":
        "Show duration in seconds.",
    "Kiek lempučių kabo vienoje ekrano pusėje (kairėje ir dešinėje – po tiek).":
        "How many bulbs hang on one side of the screen (this many on the left and on the right).",
    "Lempučių dydis, % įprasto. Kuo didesnės, tuo mažiau jų telpa.":
        "Bulb size, % of normal. The bigger they are, the fewer fit.",
    "Kaip greitai lemputės mirksi: 100 – įprastai, 200 – dvigubai greičiau, 0 – šviečia nemirksėdamos.":
        "How fast the bulbs blink: 100 – normal, 200 – twice as fast, 0 – steady light.",
    "Kiek bumbuliukų rieda ekrane.":
        "How many baubles roll on the screen.",
    "Bumbuliukų dydis, % įprasto.":
        "Bauble size, % of normal.",
    "Kiek eglučių išdėliojama ekranų apačioje.":
        "How many trees are placed along the bottom of the screens.",
    "Visų eglučių aukštis – tikrais ekrano taškais (didesniame ekrane eglutės santykinai mažesnės).":
        "Height of all trees – in real screen pixels (on a larger screen trees are relatively smaller).",
    "Žemiausių eglučių aukštis. Keičiant keičiasi tik žemiausios – vidutinės ir aukščiausios lieka.":
        "Height of the lowest trees. Changing it changes only the lowest – medium and tallest stay.",
    "Aukščiausių eglučių aukštis. Keičiant keičiasi tik aukščiausios – vidutinės ir žemiausios lieka.":
        "Height of the tallest trees. Changing it changes only the tallest – medium and lowest stay.",
    "Kiek sniego senių.":
        "How many snowmen.",
    "Sniego senių dydis, % įprasto.":
        "Snowman size, % of normal.",
    "Kiek buldozeriukų valo sniegą.":
        "How many little bulldozers clear the snow.",
    "Buldozeriukų dydis, % įprasto.":
        "Bulldozer size, % of normal.",
    "60 – sklandžiau, bet procesorius dirba maždaug dvigubai daugiau.": "60 is smoother, but uses about twice the CPU.",
    "30 – mažiausia apkrova.": "30 uses the least CPU.",
    "Svyravimas į šonus, %": "Side-to-side sway, %",
    "Plasnojimas, %": "Flutter, %",
    "Kaip toli snaigės krisdamos siūbuoja į šonus – kristalai labiausiai (kaip lapelis), smulkūs taškeliai – mažiau. "
    "0 – krenta tiesiai.": "How far snowflakes sway sideways as they fall – crystals the most (like a leaf), small "
                           "dots less. 0 – they fall straight down.",
    "Kaip stipriai kristalai krisdami tai sulėtėja, tai pagreitėja. 0 – krenta tolygiai.":
        "How much crystals alternately slow down and speed up as they fall. 0 – they fall steadily.",
    "120 – tik 120 Hz ar greitesniam ekranui (60 Hz ekrane veiks kaip 60). Procesorius dirba maždaug 4 kartus daugiau nei su 30.":
        "120 is only for 120 Hz or faster displays (on a 60 Hz display it works like 60). Uses about 4 times the CPU of 30.",
    "Išplėstos ribos leidžia nustatyti daug didesnius kiekius ir dydžius (ribos vis tiek lieka – kad programa "
    "neužstrigtų visai). Kompiuteris gali pradėti stipriai strigti, o nustatymų langas – lėtai reaguoti."
    "\n\nĮjungti?":
        "Extended limits allow much larger amounts and sizes (some limits remain so the program does not freeze "
        "completely). The computer may start lagging heavily and the settings window may respond slowly."
        "\n\nTurn on?",
    "Buldozeriukai": "Bulldozers",
    "Sniego senis": "Snowman",
    "Kiek sniego senių": "Number of snowmen",
    "Tik stovi vietoje (pajudina rankas, pasuka galvą)": "Just stands still (moves arms, turns head)",
    "Stovinčiam prisninga ant galvos ir šluotos": "Snow settles on the head and broom while standing",
    "Pačiupk už šaliko!": "Grab the scarf!",
    "Kiek buldozeriukų": "Number of bulldozers",
    "Girliandos": "Light strings",
    "Mirksėjimas, % (0 – nemirksi)": "Blinking, % (0 – steady)",
    "Lempučių vienoje pusėje": "Bulbs on each side",
    "Atspindžiai stikle (kartais blyksteli)": "Glints on the glass (now and then)",
    "Atverti": "Open",
    "Žurnalo dar nėra.": "There is no log yet.",
    "Nepavyko atverti žurnalo.": "Could not open the log.",
}

# Sukompiliuotos (PyInstaller) programos __file__ rodo į laikiną išpakavimo aplanką – nustatymai ten pradingtų.
SUKOMPILIUOTA = getattr(sys, "frozen", False)
PROGRAMOS_APLANKAS = Path(sys.executable).parent if SUKOMPILIUOTA else Path(__file__).parent


VIETINE_BYLA = PROGRAMOS_APLANKAS / "sniegas_nustatymai.json"


def aplankas_rasomas(aplankas):
    bandymas = aplankas / ".sniegas_rasymo_bandymas"
    try:
        bandymas.write_text("", encoding="utf-8")
        return True
    except OSError:
        return False
    finally:
        try:
            bandymas.unlink(missing_ok=True)
        except OSError:
            pass


# Programos vardas sistemoje: %APPDATA% aplankas, automatinio paleidimo įrašas, „jau veikia“ žymė, užduočių juostos
# grupė.
PROGRAMOS_ID = "Sniegas"


def rasti_nustatymu_byla():
    """Šalia programos (nešiojamas režimas), jei ten galima rašyti; kitaip (pvz., Program Files arba byla
    tik skaitymui) – %APPDATA%\\Sniegas. Anksčiau jau esanti byla šalia programos būdavo pasirenkama
    net tada, kai į ją įrašyti negalima – tada keisti nustatymai neišsisaugodavo."""
    if aplankas_rasomas(PROGRAMOS_APLANKAS) and (not VIETINE_BYLA.exists() or os.access(VIETINE_BYLA, os.W_OK)):
        return VIETINE_BYLA
    appdata = Path(os.environ.get("APPDATA") or Path.home())
    aplankas = appdata / PROGRAMOS_ID
    try:
        aplankas.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    return aplankas / "sniegas_nustatymai.json"


NUSTATYMU_BYLA = rasti_nustatymu_byla()
DIAGNOSTIKOS_BYLA = NUSTATYMU_BYLA.with_name("sniegas_diagnostika.log")


class Zurnalas:
    """Diagnostikos žurnalas: kas minutę suvestinė, įvykiai ir klaidos su visa eiga. Byla ribojama iki ~2 MB
    (senesnė dalis – .old.log). Rašymo klaida niekada nesugriauna programos – diagnostika tiesiog praleidžiama."""
    MAKS = 2_000_000

    def __init__(self, kelias):
        self.kelias = kelias
        self.ijungtas = True

    def rasyti(self, tekstas, visada=False):
        if not (self.ijungtas or visada):
            return
        try:
            if self.kelias.exists() and self.kelias.stat().st_size > self.MAKS:
                self.kelias.replace(self.kelias.with_suffix(".old.log"))
            with open(self.kelias, "a", encoding="utf-8") as f:
                f.write(time.strftime("%Y-%m-%d %H:%M:%S  ") + str(tekstas).rstrip().replace("\n", "\n    ") + "\n")
        except Exception:
            pass


ZURNALAS = Zurnalas(DIAGNOSTIKOS_BYLA)
AUTOSTARTO_RAKTAS = r"Software\Microsoft\Windows\CurrentVersion\Run"
AUTOSTARTO_VARDAS = PROGRAMOS_ID

# Ši spalva perdangos lange tampa visiškai permatoma – jokia piešiama spalva su ja nesutampa.
PERMATOMA = "#010203"
SPRAITO_FONAS = "#ff00ff"  # bumbuliukų paveikslėlių fonas, kurio TransparentBlt nekopijuoja
SNIEGAS = "#ffffff"
SNIEGO_KONTURAS = "#9ab0c9"  # sukaupto sniego kontūras – kad matytųsi ir ant baltų langų
SNIEGO_SESELIS = "#c9d7ea"   # šlaitas nuo šviesos (šviesa iš viršaus kairės)
SNIEGO_SLUOKSNIAI = ("#edf2f9", "#e1e9f4")  # gilesni sniego klodai – kuo giliau, tuo melsvesni
# Pusnys ekrano apačioje (už eglių) – šiek tiek melsvesnės: toliau, todėl priešais esantis kelio sniegas (jį valo
# buldozeriukai) ir jų krūvos atsiskiria. Kelias piešiamas ištisai (visuose stulpeliuose), todėl siūlių nėra.
# šviesios ir tik kiek melsvos: tamsesni tonai ("#e4ebf6", "#c6d2e6" ir pan.) atrodė nenatūraliai
PUSNU_SPALVOS = ("#eef2f8", ("#e6ebf3", "#dee5ef"), "#d4dde9")
# Kelio sniegas (priekyje) – klodai beveik balti: įprasti SNIEGO_SLUOKSNIAI apačioje sutapdavo su pusnimis.
KELIO_SPALVOS = (SNIEGAS, ("#f7f9fd", "#f0f4fa"), SNIEGO_SESELIS)
DANGUS = "#1d3557"  # peržiūrų fonas nustatymų lange
SLINKTIES_ILGIS = 64  # nustatymų slinkties juostų ilgis, px
SLINKTIES_STILIUS = "Maza.Horizontal.TScale"  # plona, plokščia juosta – vienoda visose Windows versijose
IKONA = 30  # snaigių rūšių paveikslėlių dydis nustatymuose, px

# Skilčių įjungimo varnelės (skilties pavadinime)
SKILCIU_RAKTAI = ("snaiges", "vejas_ijungtas", "kaupimasis", "fejerverkai", "egles", "girliandos", "ekskavatoriai",
                  "bumbulai", "sniego_senis")

# Skilčių spalvos: skiltis → (fonas, antraštės spalva). Dvi grupės: dangus (sniegas, vėjas,
# fejerverkai) – žydra, puošmenos (eglutės, sniego senis ir kt.) – žalsva, „Kita“ – neutrali pilka.
# Raktas – lietuviškas skilties pavadinimas.
_DANGUS_SK = ("Snaigės", "Vėjas", "Sniego kaupimasis")  # sniegas ir oras – kairėje, melsvai
_PUOSMENOS_SK = ("Eglutės", "Girliandos", "Fejerverkai", "Buldozeriukai", "Bumbuliukai", "Sniego senis")  # dešinėje
SKILCIU_SPALVOS = dict({k: ("#eaf2fb", "#1d4f91") for k in _DANGUS_SK},
                       **{k: ("#acc0af", "#243508") for k in _PUOSMENOS_SK}, Kita=("#f1f1f1", "#444444"))
SKILTIES_TAMSI_TEKSTAS, SKILTIES_TAMSI_PILKA = "#eef3e4", "#8d9a78"  # tekstas tamsiame skilties fone
# Sniego blizgesys: šviesi šerdis ir žydri spinduliai – grynai baltas ant balto sniego nesimatytų.
BLIZG_SERDIS, BLIZG_SPINDULIAI = "#fffbe6", "#9fd6ff"
BLIZG_DAZNIS_PAVIRSIUS = 1.2  # kibirkštėlių per sekundę 1000 px ekrano pločio (kai visur sniegas)
BLIZG_DAZNIS_SNAIGES = 0.006  # kibirkštėlių per sekundę vienai krentančiai snaigei
BLIZG_MAKS = 40
TRAUKA = 900  # laisvojo kritimo pagreitis, px/s² (dauginama iš k); buldozeriukų sniego gumulams – 700 (lengvesni)
MAKS_SENIO_DALELIU, MAKS_EKSKAV_DALELIU = 600, 400  # dalelių riba – kad daug senių / buldozerių nestabdytų kadrų
# Nustatymų peržiūros – dviejų dydžių: didelės (vėjas, fejerverkai – dangus) ir mažos (eglutės, girliandos,
# buldozeriukai, bumbuliukai). Mažose žemė (sniegas) visur tokio pat storio ir tame pačiame aukštyje.
PERZ_DIDELE_MIN = (262, 100)  # mažiausi dydžiai; plotis padidinamas iki skilties pločio (nustatyti_perziuru_plocius)
PERZ_MAZA_MIN = (300, 76)
PERZ_DIDELE = PERZ_DIDELE_MIN
PERZ_MAZA = PERZ_MAZA_MIN
PERZ_ZEME = PERZ_MAZA[1] - 6  # sniego paviršius mažose peržiūrose, px
VEJO_PERZ_W, VEJO_PERZ_H = PERZ_DIDELE  # vėjo peržiūra: krentančios snaigės ir dabartinis vėjas kampe


PERZ_PLOCIAI = {}  # peržiūros vardas → plotis (kiekviena – per visą savo skilties plotį)


def pp(vardas):
    """Peržiūros plotis, px. Aukščiai nekinta (mažos – PERZ_MAZA[1], vėjo ir fejerverkų – PERZ_DIDELE[1])."""
    maz = PERZ_DIDELE_MIN[0] if vardas in ("vejas", "fejerverkai") else PERZ_MAZA_MIN[0]
    return max(maz, int(PERZ_PLOCIAI.get(vardas, 0)))


def nustatyti_perziuru_plocius(plociai):
    """Peržiūrų plotis – visas skilties plotis (skiltys platesnės dėl slinkties juostų). Skiltys
    skirtinguose stulpeliuose skirtingo pločio, todėl kiekviena peržiūra – savo pločio."""
    global VEJO_PERZ_W, VEJO_PERZ_H
    PERZ_PLOCIAI.update(plociai)
    VEJO_PERZ_W, VEJO_PERZ_H = pp("vejas"), PERZ_DIDELE[1]


VEJO_SCENA = (0, 100)  # snaigių juostos viršus ir apačia, px (visa peržiūra)
VEJO_CIKLAS_S = 7.0  # per kiek sekundžių peržiūroje praeina visas vėjo ciklas
STULPELIS = 3  # sniego sluoksnio stulpelio plotis, px

# Snaigių rūšys: pavadinimas, („taskas“, spindulys), („kristalas“, (spindulys, spindulių sk., šakos)) arba
# („kontura“, (spindulys, simetrija, formos funkcija SNAIGIU_FORMOS)). Šaka – (vieta ant spindulio 0–1, ilgis).
# Paskutinės penkios – pagal tikrų snaigių nuotraukas (K. Libbrecht klasifikacija): plokštelės krinta esant
# −1…−3 °C ir −10…−22 °C, dvylikašakės – kai dvi žvaigždutės suauga pasuktos 30°, stulpeliai su kepurėlėmis –
# kai kristalas, užaugęs kaip stulpelis, pakliūna į kitą temperatūrą ir galuose išauga plokštelės.
TIPAI = [
    ("Taškelis", "taskas", 0.9),
    ("Mažas rutuliukas", "taskas", 1.5),
    ("Rutuliukas", "taskas", 2.3),
    ("Žvaigždutė", "kristalas", (4.0, 6, ())),
    ("Kryžiukas", "kristalas", (3.5, 8, ())),
    ("Šakotoji", "kristalas", (6.0, 6, ((0.55, 0.38),))),
    ("Puošnioji", "kristalas", (8.0, 6, ((0.4, 0.34), (0.72, 0.26)))),
    ("Plunksninė", "kristalas", (9.5, 6, ((0.3, 0.3), (0.52, 0.3), (0.74, 0.22)))),
    ("Šešiakampė plokštelė", "kontura", (4.5, 6, "plokstele")),
    ("Sektorinė plokštelė", "kontura", (5.0, 6, "sektorine")),
    ("Žvaigždinė plokštelė", "kontura", (7.5, 6, "zvaigzdine_plokstele")),
    ("Dvylikašakė", "kontura", (8.5, 12, "dvylikasake")),
    ("Stulpelis su kepurėlėmis", "kontura", (4.0, 2, "stulpelis")),
]

# vieno simetrijos periodo dydis laipsniais (6 spinduliai – 60°): po tiek laipsnių snaigė atrodo taip pat
TIPU_PERIODAI = [360 / forma[1] if rusis in ("kristalas", "kontura") else 360 for _, rusis, forma in TIPAI]
# Kai „Snaigės sukasi“ išjungta, kristalas vis tiek nebūna sustingęs lipdukas: svyruodamas į šoną jis
# pasvyra į judėjimo pusę (kaip krentanti plokštelė), ±SUPIMOSI_KAMPAS laipsnių, kai svyravimas numatytasis.
SUPIMOSI_KAMPAS, SUPIMOSI_MAX = 15.0, 30.0

# Tikroviškumui svarbiausia – gylis. Smulkios snaigės yra toli: krenta lėčiau, vėjas jas ekrane neša lėčiau,
# jos blankesnės (oras tarp mūsų ir jų). Stambios – arti: greitesnės, ryškios, labiau svyruoja.
# Kruopos („Rutuliukas“) tikrovėje krenta greičiausiai (1–2 m/s), žvaigždiniai kristalai – lėčiausiai (0,3–0,6 m/s).
TIPU_GYLIS = [0.35, 0.5, 0.7, 0.6, 0.6, 0.8, 0.9, 1.0, 0.7, 0.75, 0.85, 0.95, 0.55]  # 0 – toli, 1 – arti
# plokštelės krinta lėčiau už kruopas, bet greičiau už šakotas žvaigždes; stulpeliai – sunkesni, krinta greičiau
TIPU_GREITIS = [(16, 24), (22, 30), (38, 50), (24, 32), (24, 32), (32, 42), (36, 46), (40, 52),
                (30, 38), (30, 40), (34, 44), (38, 48), (32, 42)]  # px/s, kai mastelis 1

# Tikroviškas oras: sintetinė turbulencija – kelių atsitiktinių krypčių plokščiųjų bangų suma (Kraichnan,
# „kinematinė simuliacija“). Kiekviena banga be „šaltinių“ (div = 0), todėl snaigės nesusispiečia į kruvas.
# Tyrimai (Nemes ir kt. 2017) rodo, kad snaigės orą seka beveik idealiai – jų šoninis blaškymasis yra oro
# judėjimas, todėl kaimynės juda kartu. Įvairaus dydžio sūkuriai (Kolmogorovo spektras: greitis ∝ dydis^⅓),
# pailgi gulsčiai (kaip prie žemės), juos neša vėjas (Tayloro „užšalusi“ turbulencija), tolimų – ekrane mažesni.
ORO_BANGU_ILGIAI = (900, 620, 430, 300, 205, 140)  # px, kai mastelis 1


def oro_modos(ilgis=1.0, greitis=1.0, seed=11):
    """Turbulencijos bangos: (kx, ky, ux, uy, ω, fazė, gylio fazė). Greičių vidutinė kvadratinė vertė – 1."""
    rnd = random.Random(seed)
    modos = []
    for lam in ORO_BANGU_ILGIAI:
        kk = 2 * math.pi / (lam * ilgis)
        th = math.pi / 2 + rnd.uniform(-0.9, 0.9)  # bangos vektorius beveik statmenas – sūkuriai gulsti, pailgi
        kx, ky = kk * math.cos(th), kk * math.sin(th) * rnd.choice((-1, 1))
        a = (lam / 600) ** (1 / 3)
        modos.append([kx, ky, a * ky / kk, -a * kx / kk, rnd.choice((-1, 1)) * 4 * greitis * kk,
                      rnd.uniform(0, 2 * math.pi), rnd.uniform(-5, 5)])
    s = math.sqrt(sum((m[2] ** 2 + m[3] ** 2) / 2 for m in modos))
    for m in modos:
        m[2] /= s
        m[3] /= s
    return tuple(tuple(m) for m in modos)


def _snaiges_tonas(gylis):
    """Tolimos snaigės kiek pilkšvai melsvos (oro perspektyva) – ir ant balto lango jos šiek tiek matosi."""
    t = (1 - gylis) * 0.55
    return "#%02x%02x%02x" % tuple(round(255 + (c - 255) * t) for c in (170, 188, 212))


TIPU_SPALVOS = [_snaiges_tonas(z) for z in TIPU_GYLIS]
# Įprastų snaigių šešėlis: tas pats piešinys 1 tašku žemyn-dešinėn, melsvas (kaip pixel art šešėlinė spalva).
# Be jo ploni balti brūkšniai ant šviesaus lango beveik nematomi; ant tamsaus fono suteikia apimties.
SNAIGES_SESELIS = "#a9c8ea"
# Tolimesnės už šią ribą snaigės krenta UŽ eglučių, sniego pusnių, girliandų, bumbuliukų ir buldozeriukų.
GILUMO_RIBA = 0.58

# „SNIEGAS“ pixel art raidėmis (lango „Apie“ pavadinimas): 7 eilučių raidės, „#“ – taškas
PIKS_RAIDES = {
    "S": (".###.", "#...#", "#....", ".###.", "....#", "#...#", ".###."),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "I": ("###", ".#.", ".#.", ".#.", ".#.", ".#.", "###"),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "G": (".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."),
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
}

# Paruoštukai: pritaikius keičiami tik čia išvardyti nustatymai, kiti (spalvos, dydžiai…) lieka
# naudotojo. Bet visi 6 ekrano objektai (eglės, girliandos, seniai, buldozeriukai, bumbuliukai, fejerverkai) nustatomi kiekviename – kitaip rezultatas
# priklausytų nuo to, kas pritaikyta prieš tai (po „Pūgos“ „Darbui“ likdavo buldozeriukai ir seniai).
# „kiekis“ – snaigių iš viso (rūšių proporcijos lieka). Jei paruoštukas keičia snaiges, vėją ar kaupimąsi,
# atitinkama skiltis įjungiama (kitaip, pvz., „Pūga“ esant išjungtam vėjui būtų be vėjo).
# Paruoštukų plytelės – nuo ramiausio iki aktyviausio: (indeksas PARUOSTUKAI arba NUMATYTIEJI,
# aprašymas, fonas, tekstas). Spalvos – nuo blyškiai pilkos iki sodriai mėlynos (pūga).
PARUOSTUKU_PLYTOS = (  # „Numatytasis“ – viršuje, toliau nuo ramiausio iki aktyviausio
    (-2, "Numatytieji nustatymai", "#dcefd8", "#24401f"),
    (3, "Retos snaigės", "#eceff3", "#2d3a46"),
    (0, "Sninga lėtai, eglutės, sniego senis", "#d7e6f6", "#1f3b5c"),
    (2, "Eglutės, girliandos, fejerverkai", "#ffe0a6", "#5a3a00"),
    (1, "Daug sniego, vėjas, buldozeriukai", "#3f62a0", "#ffffff"),
)
PARUOSTUKO_REMAS = "#1b1b1b"  # galiojančio paruoštuko plytelės rėmelis
PARUOSTUKO_FOKUSAS = "#1d6fd6"  # plytelė su klaviatūros fokusu
NUMATYTUJU_PAV, NUMATYTIEJI = "Numatytasis", -2  # „paruoštukas“, grąžinantis VISUS nustatymus
PARUOSTUKAI = (
    ("Ramus vakaras", {"kiekis": 120, "greitis": 60, "dydis": 70, "vejas": 1, "gusiai": 0, "gusio_stiprumas": 0,
                       "kaupimo_greitis": 70, "egles": True, "egliu_mirksi": True, "girliandos": False,
                       "sniego_senis": True, "senio_kiekis": 1, "senio_stovi": True, "ekskavatoriai": False,
                       "bumbulai": False, "fejerverkai": False}),
    ("Pūga", {"kiekis": 450, "greitis": 130, "dydis": 70, "vejas": 7, "gusiai": 5, "gusio_stiprumas": 7, "kaupimo_greitis": 200,
              "egles": True, "girliandos": False, "sniego_senis": True, "ekskavatoriai": True,
              "ekskavatoriu_kiekis": 3, "bumbulai": False, "fejerverkai": False}),
    ("Šventė", {"kiekis": 200, "dydis": 70, "egles": True, "egliu_kiekis": 12, "egliu_lemputes": True, "egliu_mirksi": True,
                "egliu_burbuliukai": True, "girliandos": True, "bumbulai": True, "bumbulu_kiekis": 8,
                "fejerverkai": True, "sniego_senis": True, "senio_kiekis": 3, "senio_stovi": False,
                "ekskavatoriai": False}),
    # „Darbui“ – tik sniegas: viskas, kas juda, mirksi ar blaško, išjungiama
    ("Darbui", {"kiekis": 80, "dydis": 55, "greitis": 70, "vejas": 1, "gusiai": 0, "gusio_stiprumas": 0,
                "kaupti_languose": False, "max_aukstis": 15, "egles": False, "girliandos": False,
                "sniego_senis": False, "ekskavatoriai": False, "bumbulai": False, "fejerverkai": False}),
)


# Objekto nustatymai – paruoštukas juos nustato tik tada, kai tą objektą įjungia (išjungto nekeičia)
PARUOSTUKU_OBJEKTU_NUSTATYMAI = {"egles": ("egliu_kiekis", "egliu_lemputes", "egliu_mirksi", "egliu_burbuliukai"),
                                  "sniego_senis": ("senio_kiekis", "senio_stovi"),
                                  "ekskavatoriai": ("ekskavatoriu_kiekis",), "bumbulai": ("bumbulu_kiekis",)}


def paruostuko_nustatymai(nust):
    """Visi paruoštuko keičiami nustatymai (be „kiekis“) – su skiltimis, kurias reikia įjungti. Ko paruoštukas
    nenurodo, bet nurodo kiti (pvz., „Darbui“ – kaupti ant langų: ne), imama numatytoji reikšmė: kitaip po
    „Darbui“ ir kiti paruoštukai palikdavo sniegą nesikaupiantį ant langų – rezultatas priklausė nuo to, kas
    pritaikyta prieš tai. Išjungiamo objekto nustatymai (kiekis ir pan.) nekeičiami."""
    visi = {k for _, n_ in PARUOSTUKAI for k in n_} - {"kiekis"}
    objektu = {k: o for o, ks in PARUOSTUKU_OBJEKTU_NUSTATYMAI.items() for k in ks}
    papildomi = {k: NUMATYTI[k] for k in visi if k not in nust and (k not in objektu or nust.get(objektu[k]))}
    nust = {**papildomi, **{k: v for k, v in nust.items() if k != "kiekis"}}
    nust = {"snaiges": True, **nust}  # visi paruoštukai nustato snaigių kiekį – snaigės turi būti įjungtos
    if any(nust.get(k, 0) for k in ("vejas", "gusiai", "gusio_stiprumas")):
        nust = {"vejas_ijungtas": True, **nust}
    if any(k in nust for k in ("kaupimo_greitis", "max_aukstis", "kaupti_languose", "kaupti_apacioje")):
        nust = {"kaupimasis": True, **nust}
    return nust


NUMATYTI = {
    # Kiekviena skiltis įjungiama / išjungiama varnele savo pavadinime: snaiges, vejas_ijungtas,
    # kaupimasis, fejerverkai, egles, girliandos, ekskavatoriai, bumbulai, sniego_senis.
    "snaiges": True,
    "tipai": [25, 20, 8, 20, 5, 25, 25, 25, 10, 10, 10, 10, 7],  # iš viso 200; daugiau stambių – tikroviškiausia
    "greitis": 90,
    "svyravimas": 35,  # %, svyravimas į šonus (netolygus – ne švytuoklė)
    "plasnojimas": 10,  # %, kristalų lėtėjimas / greitėjimas krentant (stiprus atrodo kaip snaigė ant siūlo)
    "snaigiu_stilius": "iprastos",  # „pikseliai“ arba „iprastos“
    "snaiges_sukasi": True,
    "sniego_konturas": True,  # sukaupto sniego kontūras apačioje – matosi ant baltų langų
    "sniegas_blizga": True,  # ant sukaupto sniego ir krentančių snaigių kartais sužiba kibirkštėlė
    "dydis": 70,
    "vejas_ijungtas": True,  # išjungus – jokio vėjo, gūsių ir sūkurių (oras ramus)
    "vejas": 3,  # įprastas (ramaus meto) vėjas
    "gusiai": 2,  # „Sūkuriai“ (raktas „gusiai“ – istorinis, paliktas dėl nustatymų bylų suderinamumo)
    "gusio_stiprumas": 2,  # 0 – gūsių nėra
    "vejo_kryptis": "kintanti",  # „kintanti“, „desine“ arba „kaire“
    "kaupimasis": True,  # išjungus sniegas niekur nesikaupia (žemiau – kur kaupti, kai įjungta)
    "kaupti_apacioje": True,
    "max_aukstis": 40,  # pusnys – atskiri kalneliai, vidutiniškai žemesnės
    "kaupti_languose": True,
    "max_aukstis_languose": 18,
    "kaupimo_greitis": 100,
    "bumbulai": False,
    "bumbulu_juda": True,
    "bumbulu_kiekis": 5,
    "bumbulu_dydis": 70,
    "bumbulu_greitis": 20,
    "bumbulu_dingsta": True,
    "bumbulai_languose": True,  # rieda ir ant langų viršaus, nuo jų nurieda ir nukrenta
    "bumbulu_rastai": [1] * 12,
    "bumbulu_spalvos": [1] * 8,
    "bumbulu_dingimai": [1] * 4,
    "egles": True,
    "egliu_kiekis": 9,
    "egliu_atsitiktinis": True,
    "egliu_aukstis": 45,
    "egliu_min": 25,
    "egliu_max": 120,
    "egliu_plotis_min": 69,  # siauriausių eglučių plotis, % įprastos: 69, 85 arba 100 (EGLIU_PLOCIAI)
    "egliu_lemputes": True,
    "egliu_mirksi": True,
    "egliu_burbuliukai": True,
    "sniegas_ant_egliu": True,  # numatytai įjungta
    "girliandos": False,  # retro lempučių girliandos ekrano kairėje ir dešinėje
    "girliandu_dydis": 60,  # %, dydis keičiasi tolygiai
    "girliandu_kiekis": 18,  # lempučių vienoje ekrano pusėje
    "girliandu_atspindziai": True,  # šviečiančių lempučių stikle kartais blyksteli atspindys
    "girliandu_mirksejimas": 100,  # mirksėjimo greitis, %; 0 – šviečia nemirksėdamos
    "fps": 60,  # sklandžiau: lėta snaigė juda po ~0,5 taško per kadrą, o ne netolygiais 0–2 taškų šuoliukais
    "fejerverkai": False,
    "fejerverku_intervalas": 60,  # min; paleidžiama kas tiek minučių nuo vidurnakčio (60 – pilnomis valandomis)
    "fejerverku_trukme": 30,  # s
    "slepti_pilname_ekrane": True,
    "kryzelis": "klausti",  # ką daro išjungimo mygtukas (X): „klausti“, „deklas“ arba „baigti“
    "kalba": "lt",  # „lt“ arba „en“; numatytoji – lietuvių
    "diagnostika": False,  # rašyti sniegas_diagnostika.log
    "ekskavatoriai": False,
    "sniego_senis": True,  # vaikštantis sniego senis, pačiumpamas pele už šaliko
    "senio_kiekis": 1,
    "senio_dydis": 100,
    "senio_stovi": True,  # senis tik stovi vietoje (kartais pajudina rankas); nunešti vis tiek galima
    "sniegas_ant_senio": True,  # stovinčiam seniui ant galvos (ir šakelių), rankų ir šluotos pamažu prisninga
    "senio_lemputes": False,  # girliandos lemputės ant šluotos (numatytai išjungtos)
    "senio_lempuciu_animacija": "mirksi",  # SENIO_LEMPUCIU_ANIMACIJOS
    "ekskavatoriu_kiekis": 2,
    "ekskavatoriu_dydis": 100,
    "be_apribojimu": False,  # išplėstos ribos (RIBOS_LAISVOS) – savo rizika
}

# Skaitinių nustatymų ribos – bendros nustatymų langui ir bylos skaitymui (ranka pataisyta byla nesugadins programos)
RIBOS = {
    "greitis": (20, 300), "dydis": (50, 250), "vejas": (0, 10), "gusiai": (0, 10),
    "svyravimas": (0, 200), "plasnojimas": (0, 200),
    "gusio_stiprumas": (0, 10),
    "max_aukstis": (5, 200), "max_aukstis_languose": (2, 40), "kaupimo_greitis": (10, 500),
    "bumbulu_kiekis": (1, 12), "bumbulu_dydis": (40, 100), "bumbulu_greitis": (0, 300),
    "egliu_kiekis": (1, 40), "egliu_aukstis": (16, 250), "egliu_min": (16, 250), "egliu_max": (16, 250),
    "egliu_plotis_min": (69, 100),
    "fps": (30, 120), "fejerverku_intervalas": (1, 1440), "fejerverku_trukme": (10, 180),
    "senio_kiekis": (1, 5), "senio_dydis": (50, 200),
    "ekskavatoriu_kiekis": (1, 6), "ekskavatoriu_dydis": (50, 200), "girliandu_dydis": (50, 200), "girliandu_kiekis": (4, 40),
    "girliandu_mirksejimas": (0, 300),
}
# „Išplėstos ribos“: ribos išplečiamos, bet ne iki begalybės – kitaip vienas per didelis skaičius užšaldytų programą
# (pvz. 100 000 snaigių – ~3 s vienam kadrui) ar suėstų gigabaitus atminties (bumbuliukų piešinių juostos).
RIBOS_LAISVOS = {
    "greitis": (5, 1000), "dydis": (10, 1000), "vejas": (0, 50), "gusiai": (0, 10),
    "svyravimas": (0, 400), "plasnojimas": (0, 400),
    "gusio_stiprumas": (0, 50),
    "max_aukstis": (1, 1000), "max_aukstis_languose": (1, 300), "kaupimo_greitis": (1, 5000),
    "bumbulu_kiekis": (1, 40), "bumbulu_dydis": (10, 300), "bumbulu_greitis": (0, 1000),
    "egliu_kiekis": (1, 200), "egliu_aukstis": (16, 1000), "egliu_min": (16, 1000), "egliu_max": (16, 1000),
    "egliu_plotis_min": (69, 100),
    "fps": (30, 120), "fejerverku_intervalas": (1, 1440), "fejerverku_trukme": (5, 3600),
    "senio_kiekis": (1, 20), "senio_dydis": (20, 400),
    "ekskavatoriu_kiekis": (1, 30), "ekskavatoriu_dydis": (20, 600), "girliandu_dydis": (20, 600), "girliandu_kiekis": (2, 150),
    "girliandu_mirksejimas": (0, 1000),
}
# Eglės žemesnės nei 16 px nebūna (šablonas – 16 langelių, langelis ≥ 1 px), plotis – tik EGLIU_PLOCIAI (69–100):
# todėl ir ribos tokios.
ISPEJIMO_SPALVA = "#b35c00"  # nustatymo pavadinimas – šia spalva, kai jo reikšmė (dalinai) neveikia; kodėl – patarime
# Nustatymų aprašai – patarime ant pavadinimo, laukelio ir juostos. Tekstas arba keli tekstai (kiekvienas verčiamas
# atskirai).
APRASAI = {
    "dydis": "Snaigių dydis, % įprasto.",
    "greitis": "Kaip greitai snaigės krenta: 100 – įprastai, 200 – dvigubai greičiau.",
    "max_aukstis": "Kiek daugiausia sniego susikaupia ekrano apačioje (pusnys – atskiri kalneliai, ne lygus sluoksnis).",
    "max_aukstis_languose": "Kiek daugiausia sniego susikaupia ant langų viršaus.",
    "kaupimo_greitis": "Kaip greitai sniegas kaupiasi: 100 – įprastai, 200 – dvigubai greičiau, 50 – perpus lėčiau.",
    "gusiai": "Kaip stipriai oro sūkuriai suka snaiges – kaimyninės juda kartu, pučiant stipriau – ir sūkuriai stipresni. 0 – sūkurių nėra.",
    "fejerverku_intervalas": "Šou paleidžiamas kas tiek minučių, skaičiuojant nuo vidurnakčio (60 – kiekvienos valandos pradžioje, 30 – kas pusvalandį).",
    "fejerverku_trukme": "Šou trukmė sekundėmis.",
    "girliandu_kiekis": "Kiek lempučių kabo vienoje ekrano pusėje (kairėje ir dešinėje – po tiek).",
    "girliandu_dydis": "Lempučių dydis, % įprasto. Kuo didesnės, tuo mažiau jų telpa.",
    "girliandu_mirksejimas": "Kaip greitai lemputės mirksi: 100 – įprastai, 200 – dvigubai greičiau, 0 – šviečia nemirksėdamos.",
    "bumbulu_kiekis": "Kiek bumbuliukų rieda ekrane.",
    "bumbulu_dydis": "Bumbuliukų dydis, % įprasto.",
    "egliu_kiekis": "Kiek eglučių išdėliojama ekranų apačioje.",
    "egliu_aukstis": "Visų eglučių aukštis – tikrais ekrano taškais (didesniame ekrane eglutės santykinai mažesnės).",
    "egliu_min": "Žemiausių eglučių aukštis. Keičiant keičiasi tik žemiausios – vidutinės ir aukščiausios lieka.",
    "egliu_max": "Aukščiausių eglučių aukštis. Keičiant keičiasi tik aukščiausios – vidutinės ir žemiausios lieka.",
    "senio_kiekis": "Kiek sniego senių.",
    "senio_dydis": "Sniego senių dydis, % įprasto.",
    "ekskavatoriu_kiekis": "Kiek buldozeriukų valo sniegą.",
    "ekskavatoriu_dydis": "Buldozeriukų dydis, % įprasto.",
    "gusio_stiprumas": "Kaip stipriai pučia vėjo gūsis. Gūsiai būna vidutiniškai kas 30 s ir trunka apie 4 s. 0 – gūsių nėra.",
    "snaiges": "Krentančios snaigės. Žemiau – kiek ir kokių rūšių, kaip krenta ir atrodo.",
    "vejas_ijungtas": "Vėjas, gūsiai ir sūkuriai. Išjungus – oras ramus: snaigės krenta, tik svyruoja.",
    "kaupimasis": "Sniegas kaupiasi ekrano apačioje ir (ar) ant langų. Išjungus – sukauptas sniegas dingsta ir nebesikaupia.",
    "egles": "Pixel art eglutės ekranų apačioje – su lemputėmis ir papuošimais.",
    "girliandos": "Retro lempučių girliandos ekrano kairėje ir dešinėje – nuo viršaus iki užduočių juostos.",
    "fejerverkai": "Fejerverkų šou pagal laikrodį: kas kiek minučių ir kiek trunka – žemiau. „Paleisti dabar“ veikia ir išjungus.",
    "bumbulai": "Kalėdiniai bumbuliukai, riedantys sniegu ekrano apačioje (ir ant langų).",
    "sniego_senis": "Sniego senis ekrano apačioje. Pele jį galima pačiupti už šaliko ir nunešti.",
    "ekskavatoriai": "Buldozeriukai, kurie važinėja ir stumia sniegą – ekrano apačioje ir ant langų.",
    "kaupti_apacioje": "Sniegas kaupiasi ekrano apačioje pusnimis. Išjungus – apačioje sukauptas sniegas dingsta.",
    "kaupti_languose": "Sniegas kaupiasi ant atidarytų langų viršutinio krašto.",
    "slepti_pilname_ekrane": "Kai aktyvi programa užima visą ekraną (žaidimas, filmas, pristatymas), sniegas paslepiamas. Išdidinti įprasti langai – ne.",
    "diagnostika": "Rašo techninį žurnalą sniegas_diagnostika.log (kadrų trukmės, klaidos) – kai reikia ieškoti problemos. „Atverti“ – parodo žurnalą.",
    "snaiges_sukasi": "Snaigės krisdamos sukasi. Išjungus – nesisuka, tik svyruodamos lengvai pasvyra į šoną.",
    "sniego_konturas": "Plona melsva linija sukaupto sniego viršuje. Ant langų ji būna visada – be jos sniegas ant baltų langų nesimatytų.",
    "sniegas_blizga": "Ant sukaupto sniego ir krentančių snaigių kartais sužiba kibirkštėlė.",
    "snaigiu_stilius": "Įprastos – glotnios snaigės; Pixel art – stambiais taškais, kaip senuose žaidimuose.",
    "vejo_kryptis": "Kintanti – vėjas kartais pasikeičia ir trumpam papučia atgal; „Į dešinę“ ir „Į kairę“ – visada ta kryptimi.",
    "girliandu_atspindziai": "Šviečiančių lempučių stikle kartais blyksteli atspindys.",
    "bumbulu_juda": "Bumbuliukai rieda nuokalnėmis, juos stumia vėjas, kartais pašoka. Išjungus – stovi vietoje.",
    "bumbulai_languose": "Bumbuliukai rieda ir ant langų viršaus, nuo krašto nurieda ir nukrenta.",
    "bumbulu_dingsta": "Bumbuliukai kartais pradingsta ir atsiranda kitur. Kaip pradingsta – pažymėkite žemiau (kiekvieną kartą parenkamas vienas iš pažymėtų).",
    "egliu_atsitiktinis": "Vienodo aukščio – visos eglutės vienodos; atsitiktinio – aukščiai tarp mažiausio ir didžiausio.",
    "egliu_lemputes": "Spalvotos lemputės ant eglučių.",
    "egliu_mirksi": "Lemputės mirksi – kiekviena eglutė savo ritmu.",
    "egliu_burbuliukai": "Žaisliukai ant eglučių šakų.",
    "sniegas_ant_egliu": "Ant dalies šakų viršaus – sniego juostelės.",
    "senio_stovi": "Senis stovi vietoje (kartais pajudina rankas, pasuka galvą). Išjungus – vaikšto. Pačiupti pele galima visada.",
    "sniegas_ant_senio": "Stovinčiam seniui pamažu prisninga ant galvos, šakelių galvoje, rankų ir šluotos. Pajudėjus (pačiupus pele, numetus) sniegas nubyra.",
    "senio_lemputes": "Girliandos lemputės ant šluotos; kaip šviečia – pasirinkite šalia.",
    "senio_lempuciu_animacija": "Kaip šviečia lemputės ant šluotos.",
    "kryzelis": "Ką daro nustatymų lango X: kaskart paklausia, sumažina į sistemos dėklą (sniegas lieka) arba išjungia programą.",
    "svyravimas": "Kaip toli snaigės krisdamos siūbuoja į šonus – kristalai labiausiai (kaip lapelis), smulkūs taškeliai – mažiau. 0 – krenta tiesiai.",
    "plasnojimas": "Kaip stipriai kristalai krisdami tai sulėtėja, tai pagreitėja. 0 – krenta tolygiai.",
    "vejas": "Ramiu metu vėjas kas 5–12 s pasirenkamas iš naujo: nuo 0 iki 0,7 šios reikšmės (kintančios krypties – kartais trumpam ir atgal). Gūsio metu – tiek, kiek „Gūsio stiprumas“.",
    "bumbulu_greitis": ("Kaip stipriai bumbuliukai retkarčiais pastumiami, kai beveik sustoja. Mažai – dažniau guli vietoje, daug – nuolat rieda. Nuokalnėmis ir pučiant vėjui jie rieda vienodai.",
                        "0 – visai nepastumiami (rieda tik nuokalnėmis ir pučiant vėjui)."),
}

MAKS_SNAIGIU_LAISVAI = 5000  # ir vienos rūšies, ir iš viso – virš to kadrai jau labai lėti
SNAIGIU_STILIAI = ("pikseliai", "iprastos")
KRYZELIO_VEIKSMAI = ("klausti", "deklas", "baigti")
KRYZELIO_TEKSTAI = ("Klausti", "Į sistemos dėklą", "Išjungti programą")
VEJO_KRYPTYS = ("kintanti", "desine", "kaire")
VEJO_RAKTAI = ("vejas_ijungtas", "vejas", "gusio_stiprumas", "vejo_kryptis", "gusiai")
# Tikroviški sūkuriai (įvairaus dydžio, nešami vėjo) – visada; senų bylų raktas „tikroviskas_oras“ praleidžiamas
# (senose bylose jis tiesiog praleidžiamas)
VEJO_KRYPCIU_TEKSTAI = ("Kintanti", "Į dešinę", "Į kairę")
# Gūsių laikai – pastovūs (senose nustatymų bylose esantys gusiu_pauze, gusio_trukme, gusio_kilimas, gusio_rimimas
# tiesiog praleidžiami)
GUSIU_PAUZE = 30  # s, vidutiniškai (±50 %)
GUSIO_TRUKME = 4  # s, kartu su įsibėgėjimu (±30 %)
GUSIO_KILIMAS = 100  # %, kaip greitai vėjas stiprėja
GUSIO_RIMIMAS = 100  # %, kaip greitai silpsta
# Kurie nustatymai priklauso kuriai skilčiai (raktas – skilties įjungimo varnelė, ji pati nekeičiama): mygtukas ↺
# skilties pavadinime grąžina tik juos į numatytuosius.
SKILCIU_NUSTATYMAI = {
    "snaiges": ("tipai", "greitis", "svyravimas", "plasnojimas", "snaigiu_stilius", "snaiges_sukasi", "sniego_konturas",
                "sniegas_blizga", "dydis"),
    "vejas_ijungtas": ("vejas", "gusiai", "gusio_stiprumas", "vejo_kryptis"),
    "kaupimasis": ("kaupti_apacioje", "max_aukstis", "kaupti_languose", "max_aukstis_languose", "kaupimo_greitis"),
    "egles": ("egliu_kiekis", "egliu_atsitiktinis", "egliu_aukstis", "egliu_min", "egliu_max", "egliu_plotis_min",
              "egliu_lemputes", "egliu_mirksi", "egliu_burbuliukai", "sniegas_ant_egliu"),
    "girliandos": ("girliandu_dydis", "girliandu_kiekis", "girliandu_atspindziai", "girliandu_mirksejimas"),
    "fejerverkai": ("fejerverku_intervalas", "fejerverku_trukme"),
    "bumbulai": ("bumbulu_juda", "bumbulu_kiekis", "bumbulu_dydis", "bumbulu_greitis", "bumbulu_dingsta",
                 "bumbulai_languose", "bumbulu_rastai", "bumbulu_spalvos", "bumbulu_dingimai"),
    "sniego_senis": ("senio_kiekis", "senio_dydis", "senio_stovi", "sniegas_ant_senio", "senio_lemputes",
                     "senio_lempuciu_animacija"),
    "ekskavatoriai": ("ekskavatoriu_kiekis", "ekskavatoriu_dydis"),
}
# Lemputės ant senio šluotos: kaip šviečia
SENIO_LEMPUCIU_ANIMACIJOS = ("mirksi", "lieja", "bega", "sviecia")
SENIO_LEMPUCIU_TEKSTAI = ("Mirksi", "Lėtai įsižiebia ir užgęsta", "Bėga iš apačios į viršų", "Šviečia nemirksėdamos")
TEKSTINES_REIKSMES = {"snaigiu_stilius": SNAIGIU_STILIAI, "kryzelis": KRYZELIO_VEIKSMAI, "kalba": KALBOS,
                      "vejo_kryptis": VEJO_KRYPTYS, "senio_lempuciu_animacija": SENIO_LEMPUCIU_ANIMACIJOS}
MAKS_SNAIGIU_TIPO = 1000
# Iš viso snaigių – daugiau procesorius nebespėja: ~20–30 µs vienai snaigei per kadrą, 30 kadrų/s → ~1000
MAKS_SNAIGIU_IS_VISO = 1000
SNAIGIU_IBEGIMAS = 8.0  # s – per tiek daugiausia pasirodo padidinus kiekį pridėtos snaigės (ne visos iš karto)


def apriboti_iprastai(n):
    """Nustatymai (vietoje) – į įprastas ribas (RIBOS): išjungus išplėstas ribas ar importuojant be jų."""
    for raktas, (nuo, iki) in RIBOS.items():
        n[raktas] = max(nuo, min(iki, n[raktas]))
    tipai = [min(MAKS_SNAIGIU_TIPO, x) for x in n["tipai"]]
    if sum(tipai) > MAKS_SNAIGIU_IS_VISO:
        tipai = [x * MAKS_SNAIGIU_IS_VISO // sum(tipai) for x in tipai]
    n["tipai"] = tipai


def gusis_silpnas(n):
    """Gūsis silpnesnis už pusę „Įprasto vėjo“: įprastas vėjas pučia iki 0,7 × savo reikšmės, todėl toks gūsis beveik
    nesijaučia, o prie stipraus vėjo net jį susilpnina (apie tai įspėjama, elgsena nekeičiama)."""
    return bool(n["vejas_ijungtas"]) and 0 < n["gusio_stiprumas"] < 0.5 * n["vejas"]


def skaicius_tekstu(x):
    """1 skaitmuo po kablelio, be nereikalingo nulio; lietuviškai – kablelis."""
    t = f"{x:.1f}".rstrip("0").rstrip(".")
    return t.replace(".", ",") if KALBA == "lt" else t


def girl_telpa(virsus, apacia, Pg):
    """Kiek girliandos lempučių telpa tarp darbo srities viršaus ir apačios (kad nesiliestų; pirma ir paskutinė –
    visos, su mažu tarpu nuo krašto). Ta pati formulė ekrane ir patarime."""
    pus = GIRL_STORIS * Pg / 2
    y0, y1 = virsus + pus + 2 * Pg, apacia - pus - 3 * Pg
    return max(0, int((y1 - y0) // (GIRL_STORIS * Pg + Pg)) + 1)


def numatytieji():
    return {k: (list(v) if isinstance(v, list) else v) for k, v in NUMATYTI.items()}

ISIMTOS_KLASES = {
    "Progman", "WorkerW", "Shell_TrayWnd", "Shell_SecondaryTrayWnd",
    "Windows.UI.Core.CoreWindow", "XamlExplorerHostIslandWindow",
    "TopLevelWindowForOverflowXamlIsland",
}
# Sistemos iškylantys langai (paslėptų piktogramų sąrašas, kontekstiniai meniu, „Start“, miniatiūros, patarimai):
# kol kuris nors jų atidarytas virš perdangos, perdanga nekeliama – kitaip po ≤2 s ji juos uždengdavo.
ISKYLANTYS_LANGAI = {
    "TopLevelWindowForOverflowXamlIsland", "NotifyIconOverflowWindow", "Xaml_WindowedPopupClass",
    "Windows.UI.Core.CoreWindow", "XamlExplorerHostIslandWindow", "#32768", "TaskListThumbnailWnd",
    "tooltips_class32",
}
# Kiti tokie langai atpažįstami pagal procesą (užduočių juosta, „Start“, paieška…): mažas iškylantis langas be
# antraštės. Pati užduočių juosta, darbalaukis ir failų naršyklės langai – ne iškylantys.
SISTEMOS_PROCESAI = {"explorer.exe", "shellhost.exe", "shellexperiencehost.exe", "startmenuexperiencehost.exe",
                     "searchhost.exe", "searchapp.exe", "searchui.exe"}
NE_ISKYLANTYS = {"Shell_TrayWnd", "Shell_SecondaryTrayWnd", "Progman", "WorkerW", "CabinetWClass", "ExploreWClass",
                 "EdgeUiInputTopWndClass", "EdgeUiInputWndClass"}  # Edge UI – nematomi ekrano kraštų gestų langai

# snaigės laukai
SX, SY, SVY, SR, SFAZE, SAMP, SDAZN, STASKAI, SDYDIS, SSENA, STIPAS, SSUK_FAZE, SSUKIMAS, SVX, SREAKCIJA, \
    SPLASNOJIMAS, SSKERSMUO, SGYLIS = range(18)
VSYNC_FAZE = 0.002     # kadras pradedamas tiek s po ekrano atnaujinimo (vblank)
SUKIMO_KADRAI = 20      # įprastos snaigės: iš anksto apskaičiuoti posūkiai per vieną simetrijos periodą
                        # (20 – ne 10: daugiau pradinių padėčių ir tolygesnis sukimasis; atlasas ~2,6 MB)


# ---------------------------------------------------------------- Windows API

GWL_EXSTYLE = -20
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_LAYERED = 0x00080000
WS_EX_NOACTIVATE = 0x08000000
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010
SWP_FRAMECHANGED = 0x0020
SWP_SHOWWINDOW = 0x0040
DWMWA_EXTENDED_FRAME_BOUNDS = 9
DWMWA_CLOAKED = 14
MONITOR_DEFAULTTONEAREST = 2
ERROR_ALREADY_EXISTS = 183
SRCCOPY = 0x00CC0020
PATCOPY = 0x00F00021
GWLP_WNDPROC = -4
EVENT_SYSTEM_FOREGROUND = 0x0003
EVENT_SYSTEM_MINIMIZEEND = 0x0017
EVENT_OBJECT_DESTROY = 0x8001
EVENT_OBJECT_SHOW = 0x8002
EVENT_OBJECT_HIDE = 0x8003
EVENT_SYSTEM_MENUPOPUPSTART = 0x0006
EVENT_OBJECT_CLOAKED, EVENT_OBJECT_UNCLOAKED = 0x8017, 0x8018
GWL_STYLE = -16
WS_CAPTION = 0x00C00000
EVENT_OBJECT_LOCATIONCHANGE = 0x800B
WINEVENT_OUTOFCONTEXT = 0x0000
GA_ROOT = 2
GW_HWNDPREV = 3
WM_PAINT = 0x000F
WM_SYSCOMMAND = 0x0112
SC_MINIMIZE = 0xF020
SW_HIDE = 0
WM_ERASEBKGND = 0x0014
WM_APP = 0x8000
WM_DEKLAS = WM_APP + 1
WM_TASKBARCREATED = 0  # Windows – registruojama žemiau (RegisterWindowMessageW)
WM_LBUTTONUP = 0x0202
WM_MBUTTONUP = 0x0208
WM_RBUTTONUP = 0x0205
NIM_ADD, NIM_MODIFY, NIM_DELETE = 0, 1, 2
NIF_MESSAGE, NIF_ICON, NIF_TIP, NIF_INFO = 0x01, 0x02, 0x04, 0x10
IMAGE_ICON = 1
LR_LOADFROMFILE = 0x10
SM_CXSMICON, SM_CYSMICON = 49, 50
SM_CXICON = 11
WM_SETICON, ICON_SMALL, ICON_BIG = 0x0080, 0, 1
GCLP_HICON, GCLP_HICONSM = -14, -34
MF_STRING, MF_SEPARATOR = 0x0000, 0x0800
TPM_RIGHTBUTTON, TPM_NONOTIFY, TPM_RETURNCMD = 0x0002, 0x0080, 0x0100
WS_POPUP = 0x80000000
NULL_PEN = 8


class GUID(ctypes.Structure):
    _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD), ("Data3", wintypes.WORD),
                ("Data4", ctypes.c_ubyte * 8)]


class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("hWnd", wintypes.HWND), ("uID", wintypes.UINT),
                ("uFlags", wintypes.UINT), ("uCallbackMessage", wintypes.UINT), ("hIcon", wintypes.HANDLE),
                ("szTip", ctypes.c_wchar * 128), ("dwState", wintypes.DWORD), ("dwStateMask", wintypes.DWORD),
                ("szInfo", ctypes.c_wchar * 256), ("uVersion", wintypes.UINT), ("szInfoTitle", ctypes.c_wchar * 64),
                ("dwInfoFlags", wintypes.DWORD), ("guidItem", GUID), ("hBalloonIcon", wintypes.HANDLE)]


class MONITORINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT),
                ("rcWork", wintypes.RECT), ("dwFlags", wintypes.DWORD)]


if sys.platform == "win32":
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    dwmapi = ctypes.WinDLL("dwmapi")
    gdi32 = ctypes.WinDLL("gdi32")
    winmm = ctypes.WinDLL("winmm")
    msimg32 = ctypes.WinDLL("msimg32")

    _H = wintypes.HANDLE
    _HDC = wintypes.HDC
    _I = ctypes.c_int

    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    MONITORENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HANDLE, wintypes.HDC,
                                         ctypes.POINTER(wintypes.RECT), wintypes.LPARAM)

    GetWindowLong = getattr(user32, "GetWindowLongPtrW", None) or user32.GetWindowLongW
    SetWindowLong = getattr(user32, "SetWindowLongPtrW", None) or user32.SetWindowLongW
    GetWindowLong.restype = ctypes.c_ssize_t
    GetWindowLong.argtypes = [wintypes.HWND, _I]
    SetWindowLong.restype = ctypes.c_ssize_t
    SetWindowLong.argtypes = [wintypes.HWND, _I, ctypes.c_ssize_t]

    user32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
    user32.EnumDisplayMonitors.argtypes = [_HDC, ctypes.POINTER(wintypes.RECT), MONITORENUMPROC, wintypes.LPARAM]
    user32.GetMonitorInfoW.argtypes = [_H, ctypes.POINTER(MONITORINFO)]
    user32.MonitorFromWindow.restype = _H
    user32.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetParent.restype = wintypes.HWND
    user32.GetParent.argtypes = [wintypes.HWND]
    for _f in ("IsWindow", "IsWindowVisible", "IsIconic", "IsZoomed", "GetWindowTextLengthW"):
        getattr(user32, _f).argtypes = [wintypes.HWND]
    user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, _I]
    user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, _I, _I, _I, _I, wintypes.UINT]
    user32.GetDC.restype = _HDC
    user32.GetDC.argtypes = [wintypes.HWND]
    user32.ReleaseDC.argtypes = [wintypes.HWND, _HDC]
    user32.FillRect.argtypes = [_HDC, ctypes.POINTER(wintypes.RECT), _H]
    dwmapi.DwmGetWindowAttribute.argtypes = [wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
    user32.ShowWindow.argtypes = [wintypes.HWND, _I]
    dwmapi.DwmGetWindowAttribute.restype = ctypes.c_long
    kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
    kernel32.CreateMutexW.restype = _H

    gdi32.CreateCompatibleDC.restype = _HDC
    gdi32.CreateCompatibleDC.argtypes = [_HDC]
    gdi32.CreateCompatibleBitmap.restype = _H
    gdi32.CreateCompatibleBitmap.argtypes = [_HDC, _I, _I]
    gdi32.SelectObject.restype = _H
    gdi32.SelectObject.argtypes = [_HDC, _H]
    gdi32.DeleteObject.argtypes = [_H]
    gdi32.DeleteDC.argtypes = [_HDC]
    gdi32.BitBlt.argtypes = [_HDC, _I, _I, _I, _I, _HDC, _I, _I, wintypes.DWORD]
    gdi32.PatBlt.argtypes = [_HDC, _I, _I, _I, _I, wintypes.DWORD]
    gdi32.CreateSolidBrush.restype = _H
    gdi32.CreateSolidBrush.argtypes = [wintypes.DWORD]
    gdi32.CreatePen.restype = _H
    gdi32.CreatePen.argtypes = [_I, _I, wintypes.DWORD]
    gdi32.GetStockObject.restype = _H
    gdi32.GetStockObject.argtypes = [_I]
    gdi32.Ellipse.argtypes = [_HDC, _I, _I, _I, _I]
    gdi32.Polygon.argtypes = [_HDC, ctypes.c_void_p, _I]
    gdi32.Polyline.argtypes = [_HDC, ctypes.c_void_p, _I]
    gdi32.SetViewportOrgEx.argtypes = [_HDC, _I, _I, ctypes.c_void_p]
    gdi32.SaveDC.argtypes = [_HDC]
    gdi32.RestoreDC.argtypes = [_HDC, _I]
    gdi32.IntersectClipRect.argtypes = [_HDC, _I, _I, _I, _I]
    gdi32.ExcludeClipRect.argtypes = [_HDC, _I, _I, _I, _I]
    winmm.timeBeginPeriod.argtypes = [wintypes.UINT]
    msimg32.TransparentBlt.argtypes = [_HDC, _I, _I, _I, _I, _HDC, _I, _I, _I, _I, wintypes.UINT]
    winmm.timeEndPeriod.argtypes = [wintypes.UINT]
    HWND_TOPMOST = wintypes.HWND(-1)
    WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
    WINEVENTPROC = ctypes.WINFUNCTYPE(None, wintypes.HANDLE, wintypes.DWORD, wintypes.HWND, wintypes.LONG,
                                      wintypes.LONG, wintypes.DWORD, wintypes.DWORD)
    user32.SetWinEventHook.restype = wintypes.HANDLE
    user32.SetWinEventHook.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE, WINEVENTPROC,
                                       wintypes.DWORD, wintypes.DWORD, wintypes.DWORD]
    user32.UnhookWinEvent.argtypes = [wintypes.HANDLE]
    user32.GetAncestor.restype = wintypes.HWND
    user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
    user32.GetWindow.restype = wintypes.HWND
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.RegisterWindowMessageW.argtypes = [wintypes.LPCWSTR]
    user32.RegisterWindowMessageW.restype = wintypes.UINT
    # Persikrovęs explorer.exe (užduočių juosta) šią žinutę išsiunčia visiems viršutiniams langams – tada
    # piktograma prie laikrodžio sukuriama iš naujo iškart, o ne per periodinį tikrinimą
    WM_TASKBARCREATED = user32.RegisterWindowMessageW("TaskbarCreated")
    user32.GetWindow.argtypes = [wintypes.HWND, wintypes.UINT]
    user32.CallWindowProcW.argtypes = [ctypes.c_void_p, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.CallWindowProcW.restype = ctypes.c_ssize_t
    user32.ValidateRect.argtypes = [wintypes.HWND, ctypes.c_void_p]
    shell32 = ctypes.WinDLL("shell32")
    shell32.Shell_NotifyIconW.argtypes = [wintypes.DWORD, ctypes.POINTER(NOTIFYICONDATAW)]
    user32.LoadImageW.restype = wintypes.HANDLE
    user32.LoadImageW.argtypes = [wintypes.HANDLE, wintypes.LPCWSTR, wintypes.UINT, _I, _I, wintypes.UINT]
    user32.DestroyIcon.argtypes = [wintypes.HANDLE]
    user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.SendMessageW.restype = ctypes.c_ssize_t
    # 32 bitų Python'e (x86) SetClassLongPtrW nėra – tik SetClassLongW (kaip ir GetWindowLong)
    SetClassLong = getattr(user32, "SetClassLongPtrW", None) or user32.SetClassLongW
    SetClassLong.argtypes = [wintypes.HWND, _I, ctypes.c_ssize_t]
    SetClassLong.restype = ctypes.c_size_t
    user32.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
    user32.GetSystemMetrics.argtypes = [_I]
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                                                    ctypes.POINTER(wintypes.DWORD)]
    user32.CreatePopupMenu.restype = wintypes.HANDLE
    user32.AppendMenuW.argtypes = [wintypes.HANDLE, wintypes.UINT, ctypes.c_size_t, wintypes.LPCWSTR]
    user32.TrackPopupMenu.argtypes = [wintypes.HANDLE, wintypes.UINT, _I, _I, _I, wintypes.HWND, ctypes.c_void_p]
    user32.TrackPopupMenu.restype = _I
    user32.DestroyMenu.argtypes = [wintypes.HANDLE]
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.CreateWindowExW.restype = wintypes.HWND
    user32.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
                                       _I, _I, _I, _I, wintypes.HWND, wintypes.HANDLE, wintypes.HANDLE,
                                       ctypes.c_void_p]
    user32.DestroyWindow.argtypes = [wintypes.HWND]


def rgb(spalva):
    return int(spalva[1:3], 16) | int(spalva[3:5], 16) << 8 | int(spalva[5:7], 16) << 16


SPRAITO_FONAS_RGB = rgb(SPRAITO_FONAS)
PERMATOMA_RGB = rgb(PERMATOMA)


def nustatyti_dpi():
    # Be to Windows su 125–150 % masteliu „meluoja“ apie koordinates ir sniegas guli ne ten.
    # Pirma – Per-Monitor v2 (Windows 10 1703+): koordinatės tokios pat kaip v1, bet Windows pats
    # tinkamai išdidina dėklo meniu, pranešimų langus ir nustatymų lango antraštę kitame ekrane.
    # -4 = DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2; tai rodyklė (HANDLE), ne int – kitaip 64 bitų
    # Python gali perduoti neteisingą reikšmę. Kviečiama prieš sukuriant bet kurį langą.
    try:
        f = ctypes.windll.user32.SetProcessDpiAwarenessContext
        f.argtypes = [ctypes.c_void_p]
        f.restype = wintypes.BOOL
        if f(ctypes.c_void_p(-4)):
            return
    except Exception:
        pass
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def lango_klase(hwnd):
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buf, 256)
    return buf.value


def lango_staciakampis(hwnd):
    # DWM ribos – be nematomų Windows 10/11 rėmelių šešėliui, t. y. tikrasis lango viršus.
    r = wintypes.RECT()
    if dwmapi.DwmGetWindowAttribute(hwnd, DWMWA_EXTENDED_FRAME_BOUNDS,
                                    ctypes.byref(r), ctypes.sizeof(r)) != 0:
        if not user32.GetWindowRect(hwnd, ctypes.byref(r)):
            return None
    return (r.left, r.top, r.right, r.bottom)


_PROCESU_VARDAI = {}


def proceso_vardas(pid):
    """Proceso vykdomosios bylos vardas mažosiomis raidėmis (pvz., „explorer.exe“) arba ''. Podėlyje."""
    v = _PROCESU_VARDAI.get(pid)
    if v is None:
        v = ""
        try:
            h = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
            if h:
                try:
                    buf = ctypes.create_unicode_buffer(520)
                    n = wintypes.DWORD(520)
                    if kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n)):
                        v = os.path.basename(buf.value).lower()
                finally:
                    kernel32.CloseHandle(h)
        except Exception:
            pass
        if len(_PROCESU_VARDAI) > 500:
            _PROCESU_VARDAI.clear()
        _PROCESU_VARDAI[pid] = v
    return v


def paslepta_dwm(hwnd):
    # „Cloaked“ langai (kitų virtualių darbalaukių, paslėptos UWP programos) yra „matomi“, bet jų nesimato.
    v = ctypes.c_int(0)
    if dwmapi.DwmGetWindowAttribute(hwnd, DWMWA_CLOAKED, ctypes.byref(v), ctypes.sizeof(v)) == 0:
        return v.value != 0
    return False


def gauti_monitorius():
    rez = []

    def cb(hmon, hdc, lprc, lp):
        mi = MONITORINFO()
        mi.cbSize = ctypes.sizeof(MONITORINFO)
        if user32.GetMonitorInfoW(hmon, ctypes.byref(mi)):
            m, w = mi.rcMonitor, mi.rcWork
            rez.append(((m.left, m.top, m.right, m.bottom), (w.left, w.top, w.right, w.bottom)))
        return True

    user32.EnumDisplayMonitors(None, None, MONITORENUMPROC(cb), 0)
    return rez


# ---------------------------------------------------------------- piešimas: GDI ir tkinter drobė
# Eglės piešiamos ta pačia funkcija ir ekrane (GDI), ir nustatymų peržiūroje (tkinter drobė).

class Priemones:
    """GDI pieštukai ir teptukai – sukuriami vieną kartą ir naudojami pakartotinai."""

    def __init__(self):
        self.piestukai = {}
        self.teptukai = {}
        self.be_piestuko = gdi32.GetStockObject(NULL_PEN)

    def piestukas(self, spalva):
        p = self.piestukai.get(spalva)
        if p is None:
            p = self.piestukai[spalva] = gdi32.CreatePen(0, 1, rgb(spalva))
        return p

    def teptukas(self, spalva):
        t = self.teptukai.get(spalva)
        if t is None:
            t = self.teptukai[spalva] = gdi32.CreateSolidBrush(rgb(spalva))
        return t

    def naikinti(self):
        for h in list(self.piestukai.values()) + list(self.teptukai.values()):
            gdi32.DeleteObject(h)
        self.piestukai.clear()
        self.teptukai.clear()


class GdiPiesejas:
    def __init__(self, g, dc):
        self.g = g
        self.dc = dc

    @staticmethod
    def _int(pts):
        return [int(round(v)) for v in pts]

    def poligonas(self, pts, uzpildas):
        g, dc = self.g, self.dc
        gdi32.SelectObject(dc, g.teptukas(uzpildas))
        gdi32.SelectObject(dc, g.be_piestuko)
        pts = self._int(pts)
        gdi32.Polygon(dc, (ctypes.c_long * len(pts))(*pts), len(pts) // 2)

    def staciakampis(self, x1, y1, x2, y2, spalva):
        user32.FillRect(self.dc, ctypes.byref(wintypes.RECT(int(x1), int(y1), int(x2), int(y2))),
                        self.g.teptukas(spalva))

    def linija(self, pts, spalva):
        gdi32.SelectObject(self.dc, self.g.piestukas(spalva))
        pts = self._int(pts)
        gdi32.Polyline(self.dc, (ctypes.c_long * len(pts))(*pts), len(pts) // 2)


# ---------------------------------------------------------------- pixel art buldozeriukai (sniego valytuvai)
# Nustatymų raktai likę „ekskavatoriai…“ – kad neprapultų jau išsaugoti nustatymai.
EKSKAV_SPALVOS = {"D": "#3b3b3b", "d": "#808080", "B": "#9fd3ff", "R": "#ff6a00"}  # korpusas (Y, y) – žemiau
# Korpuso spalvos (šviesi, tamsi) – kiekvienas buldozeriukas savos: pirmas geltonas, kiti – kaip tikros technikos
# spalvos (raudona, žalia, oranžinė, mėlyna). Švyturėlis visiems tas pats.
EKSKAV_KORPUSAI = (("#f4b400", "#b07800"), ("#d8392b", "#8c1f15"), ("#3f9e4d", "#236330"),
                   ("#ff8a1c", "#b35300"), ("#3a7bd5", "#22508f"), ("#e0c200", "#8f7a00"))
EKSKAV_RASTAS = [  # žiūri į dešinę; priekyje – verstuvas, matomas iš šono (išlenktas, viršus ir ašmenys – į priekį)
    "..R...........",  # 5 ratukai
    ".yyyyy........",
    ".yBBBy........",
    ".yBBBy......yY",
    "YYYYYYYYYY.yY.",
    "YYYYYYYYYYyyY.",
    "yyyyyyyyyyyyY.",
    ".DDDDDDDD..yY.",
    None,  # ratukai – du kadrai, kad vikšrai „suktųsi“
    ".DDDDDDDD...DD",
]
EKSKAV_RATAI = ("DdDdDdDdDd.yY.", "dDdDdDdDdD.yY.")
EKSKAV_VERSTUVO_AUKSTIS = 7  # langeliais – kauburys prieš verstuvą ne aukštesnis
# Ekrano apačioje – du sniego sluoksniai: pusnys už eglių (self.aukstis – snaigės, kopos, seniai) ir
# žemas „kelias“ priešais egles (self.kelias), kurį valo buldozeriukai. Ekranas plokščias: jei buldozeriukas (jis –
# priešais egles) valytų už eglių esantį sniegą, kruva vis tiek lįstų už eglės arba ją perkirstų.
KELIO_TIRPIMAS = 0.8  # px/s (× mastelis) – tiek per sekundę patirpsta kelyje paliktos krūvos (iki kelio ribos)
KELIO_NUOLYDIS = 1.2  # kelio sniegas (palikti kauburiai) nuslenka iki tokio šlaito (px aukščio / px pločio)
# kelio sniego riba, px (× mastelis) – ~verstuvo aukštis (buvo 8: kelias susiliedavo su pusnimis ir buldozeriukų darbo
# nesimatė); prie eglių kamienų – duobutės (kelio_ribos)
KELIO_AUKSTIS = 16
EKSKAV_PURSLO_KIEKIS = 12.0  # tiek pertekliaus (stulpelio px) – vienas purslas
GRIUVIMO_NUOLYDIS = 1.0  # giliame sniege prieš verstuvą sniegas nugriūva tokiu šlaitu (px aukščio / px pločio)
EKSKAV_PLOTIS, EKSKAV_AUKSTIS = 14, 10
EKSKAV_VERSTUVAS = (10, 14)  # verstuvo stulpeliai (žiūrint į dešinę)
# Švyturėlis (EKSKAV_RASTAS „R“ – vienas langelis virš kabinos, 2 stulpelis) mirksi kaip įspėjamasis signalas:
# kas EKSKAV_SVYT_PERIODAS s trumpam įsižiebia, kitu metu – tamsus. Tik tas vienas langelis.
EKSKAV_SVYT_STULPELIS = 2
EKSKAV_SVYT_PERIODAS = 1.0
EKSKAV_SVYT_SVIECIA = 0.4  # periodo dalis, kai šviečia
EKSKAV_SVYT_SPALVOS = ("#ff8a1a", "#5c2a0c")  # šviečia, užgesęs
EKSKAV_PAKELIMAS = 3  # kiek langelių verstuvas pakeliamas pravažiuojant pro sniego senį
EKSKAV_VERSTUVO_LAIKAS = 0.3  # s – per tiek verstuvas sklandžiai pakeliamas / nuleidžiamas (po langelį)
# Kabinos stiklas: EKSKAV_RASTAS „B“ langeliai (2–4 stulpelis, 2–3 eilutė) perpiešiami taškų tikslumu –
# viršuje šviesesnis (atsispindi dangus), apačioje tamsesnis; retkarčiais trumpai blyksteli (visas pašviesėja).
EKSKAV_LANGAS = (2, 2, 3, 2)  # stulpelis, eilutė, plotis, aukštis (langeliais, žiūrint į dešinę)
EKSKAV_STIKLAS = ("#d6eeff", "#a6d6ff", "#7cbcec")  # viršus, vidurys, apačia
EKSKAV_BLYKSNIS = ("#ffffff", "#e8f5ff", "#c6e5ff")  # blykstelėjus
EKSKAV_BLYKSNIO_PERIODAS = 5.0  # s – kas tiek (± atsitiktinai kiekvienam) stiklas trumpai blyksteli
EKSKAV_KADRAI = [(ratai, kaire, pakeltas) for ratai in (0, 1) for kaire in (False, True)
                 for pakeltas in range(EKSKAV_PAKELIMAS + 1)]
EKSKAV_KADRO_NR = {k: i for i, k in enumerate(EKSKAV_KADRAI)}


def kauburio_talpa(H_maks, S):
    """Kiek sniego telpa prieš verstuvą. Tikras valytuvas perteklių nustumia į šonus – čia jis nubyra purslais."""
    return 2 * H_maks * H_maks / S


def kauburio_profilis(V, H_maks, S):
    """Sniegas prieš verstuvą – apvalus kauburys: aukščiausias prie verstuvo (ne aukščiau jo), į priekį
    nusileidžia suapvalintu šlaitu, ilgis ne daugiau kaip ~3 aukščiai. Grąžina stulpelių aukščius, suma = V."""
    H = min(H_maks, math.sqrt(V * S))
    if H <= 0:
        return []
    L = 1.5 * V * S / H  # parabolinio kauburio plotas – 2/3 · aukštis · ilgis
    n = max(1, int(math.ceil(L / S)))
    a = [max(0.0, H * (1 - ((i + 0.5) * S / L) ** 2)) for i in range(n)]
    suma = sum(a)
    return [v * V / suma for v in a] if suma > 0 else [V]  # labai mažas kiekis – vienas stulpelis


# Prie paviršiaus (lango, ekrano) krašto kauburys nuožulnus: stulpelis e stulpelių nuo krašto – ne aukščiau
# (e + 0,5)·S·KRASTO_NUOLYDIS virš esamo sniego (~50°, kaip byrančio sniego šlaitas); kas netelpa, nubyra per kraštą.
# Be to kauburio aukščiausia dalis prie krašto likdavo stačiu stulpu.
KRASTO_NUOLYDIS = 1.2


def nuslinkti(h, a, b, riba, remia):
    """Viena slinkimo perėja stulpeliams a…b-1 (lyginant su kairiuoju kaimynu): kur gretimų stulpelių skirtumas
    didesnis už ribą, sniegas pusiau perpilamas į žemesnį – stati siena per keliolika kadrų virsta šlaitu. remia –
    stulpeliai, į kuriuos remiasi verstuvas (ten nepilama). Grąžina pakitusių stulpelių (nuo, iki) arba None."""
    pa = pb = None
    for c in range(max(1, a), b):
        d = h[c] - h[c - 1]
        if d > riba:
            if c in remia:
                continue
            m = (d - riba) / 2
            h[c] -= m
            h[c - 1] += m
        elif d < -riba:
            if c - 1 in remia:
                continue
            m = (-d - riba) / 2
            h[c - 1] -= m
            h[c] += m
        else:
            continue
        if pa is None:
            pa = c - 1
        pb = c
    return None if pa is None else (pa, pb)


def stumti_kauburi(h, d, c_galas, c_priekis, c_lo, c_hi, ilgis, H_maks, S, krastas=False, atmintis=None, griuti_iki=0.0):
    """Verstuvas nugramdo sniegą po savimi ir stumia jį priešais save kauburiu (h keičiamas vietoje).
    d – kryptis (±1), c_galas / c_priekis – verstuvo galinis ir priekinis stulpeliai, [c_lo, c_hi) – paviršius,
    ilgis – ankstesnio kauburio ilgis, krastas – verstuvas pasiekė paviršiaus kraštą. Grąžina None (nėra ko
    stumti) arba (naujas kauburio ilgis, kiek nustumti per kraštą, perteklius purslams, paliesti stulpeliai nuo, iki).

    Kauburys guli ANT priekyje esančio sniego: stumiama tik tai, kas virš jo lygio (pagrindo), o pagrindas lieka
    vietoje, kol jį pasiekia pats verstuvas. (Jei kauburį kiekviename kadre surinktų iki žemės ir
    padėtų iš naujo, jo smailėjantis galas nusileistų iki žemės ir prieš nepaliestą sniegą liktų plyšys.)
    griuti_iki – didžiausias galimas sniego aukštis: giliame sniege (giliau nei verstuvas) prieš verstuvą nelieka
    aukštesnės už jį sienos – kas virš jo, nugriūva šlaitu (GRIUVIMO_NUOLYDIS) ir išbyra purslais."""
    vieta = (c_hi - 1 - c_priekis) if d > 0 else (c_priekis - c_lo)  # stulpelių iki krašto
    ga, gb = (c_galas, c_priekis + 1) if d > 0 else (c_priekis, c_galas + 1)
    ga, gb = max(ga, c_lo), min(gb, c_hi)
    senas = [c for c in (c_priekis + d * (i + 1) for i in range(ilgis)) if c_lo <= c < c_hi]
    c_ref = c_priekis + d * (ilgis + 1)  # pirmas nepaliestas stulpelis priekyje
    if c_lo <= c_ref < c_hi:
        pagrindas = h[c_ref]
    else:
        # Kauburys pasiekė kraštą – nepaliesto sniego priekyje nebėra. Imamas įsimintas pagrindas (atmintis –
        # buldozeriuko žodynas): kitaip pagrindu tapdavo pats kauburys ir jo siena prie krašto nebejudėdavo.
        pagrindas = min((h[c] for c in senas), default=0.0)
        if atmintis is not None and ilgis > 0 and atmintis.get("kruvos_pagrindas") is not None:
            pagrindas = min(pagrindas, atmintis["kruvos_pagrindas"])
    if atmintis is not None:
        atmintis["kruvos_pagrindas"] = pagrindas
    V = (sum(h[ga:gb]) if gb > ga else 0.0) + sum(max(0.0, h[c] - pagrindas) for c in senas)
    if V < 0.05:  # stumti nėra ko, bet prieš verstuvą gali stūksoti siena (pvz. ką tik nusileidus į gilų sniegą)
        griuvo, iki = griuti_pries_verstuva(h, d, c_priekis, c_lo, c_hi, H_maks, S, griuti_iki)
        return (0, 0.0, griuvo, *sorted((c_priekis, iki))) if griuvo > 0 else None
    for c in range(ga, gb):
        h[c] = 0.0
    for c in senas:
        h[c] = min(h[c], pagrindas)
    H_virs = max(2.0, H_maks - pagrindas)  # kauburio viršūnė – ne aukščiau verstuvo
    talpa = kauburio_talpa(H_virs, S)
    perteklius = max(0.0, V - talpa)  # netelpa prieš verstuvą – nubyra per kraštus į šonus
    V -= perteklius
    profilis = kauburio_profilis(V, H_virs, S)
    n = len(profilis)
    n_telpa = min(n, max(0, vieta))
    liko = V
    nukirpta = False
    for i in range(n_telpa):
        c = c_priekis + d * (i + 1)
        dalis = profilis[i]
        riba = (vieta - 1 - i + 0.5) * S * KRASTO_NUOLYDIS  # prie krašto – nuožulniai
        if dalis > riba:
            dalis, nukirpta = max(0.0, riba), True
        h[c] += dalis
        liko -= dalis
    galai = [ga, gb, c_priekis + d * (n_telpa + 1)] + senas
    griuvo, iki = griuti_pries_verstuva(h, d, c_priekis, c_lo, c_hi, H_maks, S, griuti_iki)
    if griuvo > 0:
        perteklius += griuvo
        galai.append(iki)
        if atmintis is not None and c_lo <= c_ref < c_hi:
            atmintis["kruvos_pagrindas"] = min(atmintis["kruvos_pagrindas"], h[c_ref])
    pilti = 0.0
    if liko > 0.05 and (krastas or n_telpa < n or nukirpta):  # netelpa iki krašto – nustumiama žemyn
        pilti = liko
    elif liko > 0.05:  # apvalinimo likutis – už kauburio
        c = c_priekis + d * (n_telpa + 1)
        if c_lo <= c < c_hi:
            h[c] += liko
    return n_telpa, pilti, perteklius, max(c_lo, min(galai)), min(c_hi, max(galai) + 1)


def griuti_pries_verstuva(h, d, c_priekis, c_lo, c_hi, H_maks, S, griuti_iki):
    """Giliame sniege prieš verstuvą sniegas nugriūva šlaitu: j-asis stulpelis priekyje – ne aukščiau
    H_maks + j·S·GRIUVIMO_NUOLYDIS. Grąžina (kiek nugriuvo, paskutinis paliestas stulpelis)."""
    griuvo, iki, j = 0.0, c_priekis, 1
    while griuti_iki > H_maks:
        riba = H_maks + (j - 0.5) * S * GRIUVIMO_NUOLYDIS
        c = c_priekis + d * j
        if riba >= griuti_iki or not c_lo <= c < c_hi:
            break
        if h[c] > riba:
            griuvo += h[c] - riba
            h[c] = riba
            iki = c
        j += 1
    return griuvo, iki


def kalnelio_profilis(V, H_maks, S, pusplotis):
    """Du valytuvai susitiko – sniegas sustumiamas į kalnelį (abu šlaitai apvalūs). Grąžina (aukščiai nuo kairės,
    kiek netilpo). pusplotis – kiek stulpelių į kiekvieną pusę nuo vidurio leidžiama."""
    H = min(H_maks, math.sqrt(V * S / 2))
    if H <= 0:
        return [], V
    L = min(0.75 * V * S / H, max(1, pusplotis) * S)  # pusė kalnelio pločio
    n = max(1, int(math.ceil(L / S)))
    a = [max(0.0, H * (1 - ((abs(i) + 0.5) * S / L) ** 2)) for i in range(-n, n)]
    suma = sum(a)
    if suma <= 0:
        return [], V
    telpa = min(V, suma)  # aukščiai ribojami H, todėl perteklius – purslai
    return a, max(0.0, V - telpa)


@functools.lru_cache(maxsize=None)
def ekskav_stiklo_juostos(w, h, blyksi=False):
    """Kabinos stiklas w×h taškų: [(x1, x2, y, spalva)] – po vieną atkarpą eilutei: viršuje šviesesnis (atsispindi
    dangus), apačioje tamsesnis; blyksi – trumpam visas pašviesėja (EKSKAV_BLYKSNIS)."""
    if w <= 0 or h <= 0:
        return []
    virsus, vidurys, apacia = EKSKAV_BLYKSNIS if blyksi else EKSKAV_STIKLAS
    return [(0, w, y, virsus if y < h / 3 else vidurys if y < 2 * h / 3 else apacia) for y in range(h)]


def ekskav_stiklo_vieta(Pe, kaire):
    """Stiklo stačiakampis sprite viduje (x1, y1, x2, y2), taškais – kaip piks_piesti apvalina langelių ribas."""
    c, r, w, h = EKSKAV_LANGAS
    if kaire:
        c = EKSKAV_PLOTIS - c - w
    return round(c * Pe), round(r * Pe), round((c + w) * Pe), round((r + h) * Pe)


def ekskavatoriaus_tinklelis(ratai, kaire, pakeltas=0, korpusas=0):
    """Buldozeriukas su švyturėliu ir verstuvu priekyje; korpusas – EKSKAV_KORPUSAI spalvos numeris.
    pakeltas – keliais langeliais pakeltas verstuvas (0…EKSKAV_PAKELIMAS; pravažiuojant pro sniego senį)."""
    Y, y = EKSKAV_KORPUSAI[korpusas % len(EKSKAV_KORPUSAI)]
    spalvos = dict(EKSKAV_SPALVOS, Y=Y, y=y)
    eil = [list(e if e is not None else EKSKAV_RATAI[ratai]) for e in EKSKAV_RASTAS]
    kiek = int(pakeltas)
    if kiek:
        a, b = EKSKAV_VERSTUVAS
        for r in range(len(eil)):
            for c in range(a, b):
                eil[r][c] = eil[r + kiek][c] if r + kiek < len(eil) else "."
    t = []
    for e in eil:
        r = [None if ch == "." else spalvos[ch] for ch in e]
        t.append(r[::-1] if kaire else r)
    return t


class DrobesPiesejas:
    def __init__(self, drobe):
        self.c = drobe

    def staciakampis(self, x1, y1, x2, y2, spalva):
        self.c.create_rectangle(x1, y1, x2, y2, fill=spalva, outline="")


class ParuostukoPlyta:
    """Spalvota paruoštuko plytelė: pavadinimas (paryškintas) ir trumpas aprašymas. Spustelėjus (ar Tarpas /
    Enter) – komanda; galiojantis – su ✓ ir tamsiu rėmeliu."""

    def __init__(self, tevas, pav, aprasymas, fonas, tekstas, komanda):
        self.pav, self.fonas, self.komanda = pav, fonas, komanda
        sviesus = sum(int(fonas[i:i + 2], 16) for i in (1, 3, 5)) > 3 * 128
        self.uzvesta = _maisyti(fonas, "#000000" if sviesus else "#ffffff", 0.07)
        self.remas = tk.Frame(tevas, bg=fonas, highlightthickness=2, highlightbackground=fonas,
                              highlightcolor=fonas, cursor="hand2", takefocus=1, padx=8, pady=3)
        self.l1 = tk.Label(self.remas, text=pav, bg=fonas, fg=tekstas, font=("Segoe UI", 9, "bold"), anchor="w")
        self.l2 = tk.Label(self.remas, text=aprasymas, bg=fonas, fg=_maisyti(tekstas, fonas, 0.25),
                           font=("Segoe UI", 8), anchor="w")
        # vienoje eilutėje – kad stulpelis nepailgėtų; plytelės ištempiamos per likusį aukštį
        self.l1.pack(side="left")
        self.l2.pack(side="left", padx=(8, 0))
        for w in (self.remas, self.l1, self.l2):
            w.bind("<Button-1>", lambda e: self.invoke())
            w.bind("<Enter>", lambda e: self._spalva(self.uzvesta))
            w.bind("<Leave>", lambda e: self._spalva(self.fonas))
        for k in ("<space>", "<Return>"):
            self.remas.bind(k, lambda e: self.invoke())
        # atėjus klaviatūra (Tab) – mėlynas rėmelis; išėjus – vėl pagal tai, ar galioja
        self.remas.bind("<FocusIn>", lambda e: self.remas.configure(highlightbackground=PARUOSTUKO_FOKUSAS,
                                                                    highlightcolor=PARUOSTUKO_FOKUSAS))
        self.remas.bind("<FocusOut>", lambda e: self.zymeti(self.aktyvus))
        self.aktyvus = False

    def _spalva(self, c):
        for w in (self.remas, self.l1, self.l2):
            w.configure(bg=c)
        self.zymeti(self.aktyvus)  # rėmelis: fokusas / galiojantis / fono spalvos

    def zymeti(self, aktyvus):
        self.aktyvus = aktyvus
        try:
            fokusas = self.remas.focus_get() is self.remas
        except (tk.TclError, KeyError):
            fokusas = False
        c = PARUOSTUKO_FOKUSAS if fokusas else PARUOSTUKO_REMAS if aktyvus else self.remas.cget("bg")
        self.remas.configure(highlightbackground=c, highlightcolor=c)
        self.l1.configure(text=("✓ " if aktyvus else "") + self.pav)

    def invoke(self):
        self.komanda()


class Patarimas:
    """Užrašas šalia valdiklio: užvedus pelę (po DELSA ms) arba atėjus į jį klaviatūra (Tab). Tekstas gali būti
    funkcija – tada perskaitomas rodant (pvz. „naudojamas / nenaudojamas“). Langas kuriamas tik rodant."""
    DELSA = 600
    # Pagal fokusą rodoma tik naršant klaviatūra (Tab, rodyklės): kitaip spustelėtas valdiklis (pvz. „120“) fokusą
    # gauna iš naujo kiekvieną kartą, kai langas grįžta į priekį, ir užrašas iššokdavo be priežasties.
    KLAVIATURA_S = 0.5
    paskutinis_klavisas = 0.0
    _susieti_interpretatoriai = set()
    # Vienas užrašo langas programai: kiekvienas „visada viršuje“ lango sukūrimas ir sunaikinimas
    # verčia Windows perpiešti perdangą (sniegas sumirksėdavo užvedus pelę ant valdiklio). Todėl langas
    # nenaikinamas, o tik nustumiamas už ekrano – kaip senio pagavimo langelis (atnaujinti_senio_langa).
    _bendri = {}  # interpretatorius → [langas, užrašas, kieno rodomas, HWND užregistruoti]
    ISSLEPTAS = "+-20000+-20000"
    hwnds = set()  # užrašo lango HWND: jo perkėlimas – ne kitų langų judėjimas (Sniegas._lango_ivykis)
    perdanga_iskelta = True  # perdanga iškelta į viršų – kitą kartą rodomas užrašas iškeliamas virš jos

    def __init__(self, w, tekstas):
        self.w, self.tekstas, self.langas, self.laukia = w, tekstas, None, None
        w.bind("<Enter>", self.uzvesta, add="+")
        for ivykis in ("<Leave>", "<ButtonPress>", "<FocusOut>", "<Destroy>"):
            w.bind(ivykis, self.slepti, add="+")
        w.bind("<FocusIn>", self.fokusas, add="+")
        if id(w.tk) not in Patarimas._susieti_interpretatoriai:  # vienas bendras klavišų stebėjimas programai
            Patarimas._susieti_interpretatoriai.add(id(w.tk))
            w.bind_all("<KeyPress>", Patarimas._klavisas, add="+")

    NARSYMO_KLAVISAI = ("Tab", "ISO_Left_Tab", "Left", "Right", "Up", "Down", "Home", "End")

    @staticmethod
    def _klavisas(e=None):
        # tik naršymas: uždarius pranešimą Enter / Escape fokusas grįžta į langą – tai ne naršymas
        if e is None or getattr(e, "keysym", None) in Patarimas.NARSYMO_KLAVISAI:
            Patarimas.paskutinis_klavisas = time.perf_counter()

    def fokusas(self, _=None):
        if time.perf_counter() - Patarimas.paskutinis_klavisas < self.KLAVIATURA_S:
            self.rodyti(prie_valdiklio=True)

    def uzvesta(self, _=None):
        self.slepti()
        self.laukia = self.w.after(self.DELSA, self.rodyti)

    def rodyti(self, prie_valdiklio=False):
        self.laukia = None
        self.slepti()
        try:
            tekstas = self.tekstas() if callable(self.tekstas) else self.tekstas
            if not tekstas:
                return
            w = self.w
            if prie_valdiklio:  # klaviatūra – po valdikliu (pelė gali būti bet kur)
                x, y = w.winfo_rootx(), w.winfo_rooty() + w.winfo_height() + 4
            else:  # šiek tiek žemiau pelės – kad langelis neatsidurtų po ja (tada būtų <Leave> ir mirgėtų)
                x, y = w.winfo_pointerx() + 12, w.winfo_pointery() + 20
            b = self._bendras(w)
            l, b[2] = b[0], self
            b[1].configure(text=tekstas)
            self.langas = l
            l.update_idletasks()
            if not b[3]:
                b[3] = True
                try:
                    vidinis = int(l.winfo_id())
                    Patarimas.hwnds.add(vidinis)
                    Patarimas.hwnds.add(user32.GetAncestor(vidinis, GA_ROOT) or vidinis)  # išorinis (tikrasis)
                except Exception:
                    pass
            x = max(0, min(x, w.winfo_screenwidth() - l.winfo_reqwidth() - 4))
            if y + l.winfo_reqheight() > w.winfo_screenheight():
                y = w.winfo_rooty() - l.winfo_reqheight() - 4
            l.geometry(f"+{x}+{y}")
            if Patarimas.perdanga_iskelta:  # geometry() Z tvarkos nekeičia – kitaip liktų po sniegu
                Patarimas.perdanga_iskelta = False
                l.lift()
        except tk.TclError:
            self.langas = None

    def slepti(self, _=None):
        if self.laukia is not None:
            try:
                self.w.after_cancel(self.laukia)
            except tk.TclError:
                pass
            self.laukia = None
        if self.langas is not None:
            b = Patarimas._bendri.get(id(self.w.tk))
            if b is not None and b[2] is self:  # tik savo – kitas valdiklis galbūt jau rodo savąjį
                b[2] = None
                try:
                    self.langas.geometry(self.ISSLEPTAS)
                except tk.TclError:
                    pass
            self.langas = None

    @classmethod
    def _bendras(cls, w):
        b = cls._bendri.get(id(w.tk))
        if b is not None:
            try:
                if b[0].winfo_exists():
                    return b
            except tk.TclError:
                pass
        l = tk.Toplevel(w._root())
        l.wm_overrideredirect(True)
        l.geometry(cls.ISSLEPTAS)
        l.attributes("-topmost", True)
        u = tk.Label(l, bg="#ffffe1", fg="#000000", relief="solid", bd=1, padx=6, pady=3,
                     justify="left", wraplength=340, font=("Segoe UI", 9))
        u.pack()
        b = cls._bendri[id(w.tk)] = [l, u, None, False]
        return b


class BlukstantisPiesejas(DrobesPiesejas):
    """Kaip DrobesPiesejas, tik visos spalvos priartinamos prie fono (dalis 0 – nepakitusios)."""

    def __init__(self, drobe, fonas, dalis):
        super().__init__(drobe)
        self.fonas, self.dalis = fonas, dalis

    def staciakampis(self, x1, y1, x2, y2, spalva):
        if self.dalis and len(spalva) == 7:
            spalva = _maisyti(spalva, self.fonas, self.dalis)
        super().staciakampis(x1, y1, x2, y2, spalva)


class PaveikslelioJungiklis:
    """Pixel art paveikslėlis kaip varnelė (bumbuliukų raštai ir spalvos). Pažymėtas – ryškus, tamsiu rėmeliu;
    nepažymėtas – išblukęs į skilties foną; papilkėjęs (išjungus bumbuliukus) – dar labiau išblukęs.
    state() – kaip ttk valdiklio, kad jį papilkintų tos pačios taisyklės (valdiklio_busena)."""

    def __init__(self, drobe, v, tinklas, fonas, remelis):
        self.drobe = self.master = drobe
        self.v, self.tinklas, self.fonas, self.remelis = v, tinklas, fonas, remelis
        self.aktyvus, self.fokusas = True, False
        v.trace_add("write", lambda *_: self.piesti())
        drobe.bind("<FocusIn>", lambda e: self.fokusuoti(True), add="+")
        drobe.bind("<FocusOut>", lambda e: self.fokusuoti(False), add="+")
        self.piesti()

    def fokusuoti(self, yra):
        self.fokusas = yra
        self.piesti()

    def state(self, busena=None):
        if busena is None:
            return () if self.aktyvus else ("disabled",)
        self.aktyvus = "disabled" not in busena
        self.drobe.configure(cursor="hand2" if self.aktyvus else "", takefocus=1 if self.aktyvus else 0)
        self.piesti()

    def piesti(self):
        try:
            pazymetas = bool(self.v.get())
        except tk.TclError:
            return
        blukti = (0.0 if self.aktyvus else 0.5) if pazymetas else (0.6 if self.aktyvus else 0.72)
        f, c = self.fonas, self.drobe
        remas = (self.remelis if self.aktyvus else _maisyti(self.remelis, f, 0.55)) if pazymetas else f
        c.configure(bg=_maisyti(DANGUS, f, blukti), highlightbackground=remas, highlightcolor=remas)
        c.delete("all")
        piks_piesti(BlukstantisPiesejas(c, f, blukti), self.tinklas, 3, 3, 2)  # 2 – rėmelis (highlightthickness), +1 – paraštė
        if self.fokusas:  # atėjus klaviatūra (Tab) – baltas vidinis rėmelis
            plotis = int(c.cget("width"))
            c.create_rectangle(3, 3, plotis + 1, plotis + 1, outline="#ffffff", width=1)


def _sesiakampis(r, kampas, cx=0.0, cy=0.0):
    return [(cx + r * math.cos(kampas + i * math.pi / 3), cy + r * math.sin(kampas + i * math.pi / 3)) for i in range(6)]


def _plokstele(r, kampas):
    """Šešiakampė plokštelė: kraštas, vidinė šešiakampė briauna ir šešios trumpos briaunos tarp jų."""
    v, iv = _sesiakampis(r, kampas), _sesiakampis(r * 0.5, kampas)
    kel = v + [v[0]]
    for i in range(6):
        j = (i + 1) % 6
        kel += [iv[i], iv[j], v[j]]
    return kel


def _sektorine(r, kampas):
    """Sektorinė plokštelė: šešiakampis, briaunomis iš centro padalintas į šešis sektorius."""
    v = _sesiakampis(r, kampas)
    kel = v + [v[0]]
    for i in range(6):
        kel += [(0.0, 0.0), v[(i + 1) % 6]]
    return kel


def _zvaigzdine_plokstele(r, kampas):
    """Žvaigždinė plokštelė: šeši spinduliai, kiekvieno gale – plati šešiakampė plokštelė."""
    kel = [(0.0, 0.0)]
    for i in range(6):
        a = kampas + i * math.pi / 3
        ca, sa = math.cos(a), math.sin(a)
        pagr = (ca * r * 0.45, sa * r * 0.45)
        h = _sesiakampis(r * 0.28, a + math.pi, ca * r * 0.72, sa * r * 0.72)  # pirmas kampas – arčiausiai centro
        kel += [pagr] + h + [h[0], pagr, (0.0, 0.0)]
    return kel


def _dvylikasake(r, kampas):
    """Dvylikašakė: dvi suaugusios šešiaspindulės žvaigždės, pasuktos 30°; antrosios spinduliai kiek trumpesni."""
    kel = [(0.0, 0.0)]
    for i in range(12):
        a = kampas + i * math.pi / 6
        ilgis = r if i % 2 == 0 else r * 0.82
        ca, sa = math.cos(a), math.sin(a)
        px, py = ca * ilgis * 0.55, sa * ilgis * 0.55
        kel.append((px, py))
        for z in (1, -1):
            b = a + z * math.pi / 3
            kel += [(px + math.cos(b) * ilgis * 0.22, py + math.sin(b) * ilgis * 0.22), (px, py)]
        kel += [(ca * ilgis, sa * ilgis), (0.0, 0.0)]
    return kel


def _stulpelis(r, kampas):
    """Stulpelis su kepurėlėmis: trumpa kolonėlė, abiejuose galuose – plokštelės (iš šono matyti kaip brūkšniai)."""
    c, w, h = r * 0.24, r * 0.85, r * 0.62
    taskai = [(-w, -h), (w, -h), (c, -h), (c, h), (w, h), (-w, h), (-c, h), (-c, -h), (-w, -h)]
    ca, sa = math.cos(kampas), math.sin(kampas)
    return [(x * ca - y * sa, x * sa + y * ca) for x, y in taskai]


SNAIGIU_FORMOS = {"plokstele": _plokstele, "sektorine": _sektorine, "zvaigzdine_plokstele": _zvaigzdine_plokstele,
                  "dvylikasake": _dvylikasake, "stulpelis": _stulpelis}


def formos_taskai(rusis, forma, r, kampas=0.0):
    """Įprasto stiliaus snaigės kontūras – viena laužtė [x0, y0, x1, y1, …] aplink (0, 0)."""
    if rusis == "kristalas":
        return kristalo_taskai(r, forma[1], forma[2], kampas)
    return [k for xy in SNAIGIU_FORMOS[forma[2]](r, kampas) for k in xy]


def kristalo_taskai(r, spinduliai, sakos, kampas=0.0):
    """Visa snaigė viena laužte: nuo centro į spindulio galą ir atgal, šakos – tuo pačiu keliu."""
    pts = [0.0, 0.0]
    for i in range(spinduliai):
        a = kampas + i * 2 * math.pi / spinduliai
        ca, sa = math.cos(a), math.sin(a)
        for vieta, ilgis in sakos:
            px, py = ca * r * vieta, sa * r * vieta
            pts += (px, py)
            for zenklas in (1, -1):
                b = a + zenklas * math.pi / 3
                pts += (px + math.cos(b) * r * ilgis, py + math.sin(b) * r * ilgis, px, py)
        pts += (ca * r, sa * r, 0.0, 0.0)
    return pts


LEMPUCIU_SPALVOS = {"#ff4d4d": "#5e2020", "#ffd23f": "#5e4f1a", "#4dff88": "#1f5e36",
                    "#4db8ff": "#1f455e", "#ff9f40": "#5e3e1b"}  # įjungta: išjungta
BURBULIUKU_SPALVOS = ("#e63946", "#f4c430", "#3a86ff", "#c0c7d1", "#9b5de5")


def atkurimo_ikonos_pikseliai(dydis, fonas, spalva, ss=3):
    """↺ ikona: apskritimo rodyklė, glotniais kraštais – kiekvienas pikselis iš ss×ss taškų (tkinter linijos
    Windows sistemoje neglotninamos, o šrifto ↺ Segoe UI būna mažytis ir nuleistas). Grąžina eilutes PhotoImage.put()."""
    f = dydis / 16.0
    cx, cy, rad, plotis = 8.0 * f, 8.2 * f, 5.2 * f, 1.8 * f
    nuo, iki = math.radians(100), math.radians(400)  # beveik visas ratas (300°), tarpas ir rodyklė viršuje
    galas = (cx + rad * math.cos(iki), cy - rad * math.sin(iki))
    vx, vy = -math.sin(iki), -math.cos(iki)  # judėjimo kryptis ties galu (prieš laikrodžio rodyklę ekrane)
    nx, ny = math.cos(iki), -math.sin(iki)  # į išorę
    d = 3.4 * f
    trikampis = [(galas[0] + vx * d, galas[1] + vy * d),
                 (galas[0] + nx * d * 0.85 - vx * 0.5 * f, galas[1] + ny * d * 0.85 - vy * 0.5 * f),
                 (galas[0] - nx * d * 0.85 - vx * 0.5 * f, galas[1] - ny * d * 0.85 - vy * 0.5 * f)]

    def viduje(x, y):
        a = math.atan2(cy - y, x - cx)
        a = nuo + (a - nuo) % (2 * math.pi)  # kampas – [nuo; nuo + 360°)
        if a <= iki and abs(math.hypot(x - cx, y - cy) - rad) <= plotis / 2:
            return True
        z = []
        for (x1, y1), (x2, y2) in zip(trikampis, trikampis[1:] + trikampis[:1]):
            z.append((x2 - x1) * (y - y1) - (y2 - y1) * (x - x1) >= 0)
        return all(z) or not any(z)

    def rgb(h):
        return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
    f0, f1 = rgb(fonas), rgb(spalva)
    eil = []
    for py in range(dydis):
        e = []
        for px in range(dydis):
            n = sum(viduje(px + (i + 0.5) / ss, py + (j + 0.5) / ss) for i in range(ss) for j in range(ss)) / (ss * ss)
            e.append("#%02x%02x%02x" % tuple(round(a + (b - a) * n) for a, b in zip(f0, f1)))
        eil.append("{" + " ".join(e) + "}")
    return " ".join(eil)


def _maisyti(a, b, dalis):
    """Spalva tarp a ir b (dalis 0 – a, 1 – b)."""
    return "#" + "".join(f"{round(int(a[i:i + 2], 16) * (1 - dalis) + int(b[i:i + 2], 16) * dalis):02x}"
                         for i in (1, 3, 5))


# Trys lemputės ryškumo lygiai (pixel art – be permatomumo): 0 – užgesusi, 1 – blėsta/įsižiebia, 2 – šviečia
LEMPUCIU_LYGIAI = {sviesi: (tamsi, _maisyti(sviesi, tamsi, 0.5), sviesi) for sviesi, tamsi in LEMPUCIU_SPALVOS.items()}
LEMPUCIU_SPALVU_TVARKA = tuple(LEMPUCIU_SPALVOS)

# Kaip tikras girliandos valdiklis: kiekviena eglė kas 15–40 s pereina į kitą režimą, savo tempu.
MIRKSEJIMO_REZIMAI = ("pakaitom", "begantis", "banga", "pulsuoja", "mirgantis", "kibirkstys", "spalvos", "ramus")
MIRKSEJIMO_DAZNIS = 1 / 15  # lygiai perskaičiuojami ne dažniau kaip 15 kartų per sekundę


def naujas_mirksejimas(rnd, lemp):
    n = len(lemp)
    return {"rezimas": rnd.choice(MIRKSEJIMO_REZIMAI[:-1]), "liko": rnd.uniform(15, 40), "t": rnd.uniform(0, 10),
            "tempas": rnd.uniform(0.35, 0.8), "kaupta": 0.0, "rnd": random.Random(rnd.randrange(1 << 30)),
            "eilutes": [r for r, _, _, _ in lemp],
            "spalvos": [LEMPUCIU_SPALVU_TVARKA.index(sp) for _, _, sp, _ in lemp],
            "periodai": [rnd.uniform(0.9, 2.4) for _ in range(n)], "fazes": [rnd.random() for _ in range(n)],
            "lygiai": (2,) * n}


PAKAITOM_LYGIAI = (2, 2, 2, 2, 1, 0, 0, 0, 0, 1)  # vienas pusperiodis šviečia, kitas – užgesusi, tarp jų – blėsta


def _lygis(v, sviesu, blesta):
    return 2 if v < sviesu else 1 if v < blesta else 0


def lempuciu_lygiai(m):
    """Kiekvienos lemputės ryškumas (0/1/2) pagal eglės režimą ir laiką."""
    t, T, r = m["t"], m["tempas"], m["rezimas"]
    n = len(m["eilutes"])
    if r == "ramus":
        return (2,) * n
    if r == "pakaitom":  # dvi grupės keičiasi, perėjimas per pusiau įjungtą
        return tuple(PAKAITOM_LYGIAI[int((t / T + j % 2) % 2 * 5)] for j in range(n))
    if r == "begantis":  # užgesusi vieta bėga per girliandą
        return tuple((0, 1, 2, 2, 1)[math.floor(j - t / (T * 0.5)) % 5] for j in range(n))
    if r == "banga":  # šviesos banga slenka nuo viršūnės žemyn
        return tuple(_lygis(-math.sin(2 * math.pi * (t / (T * 4) - m["eilutes"][j] / 10)), 0.25, 0.75)
                     for j in range(n))
    if r == "pulsuoja":  # visos kartu lėtai „kvėpuoja“
        v = math.sin(2 * math.pi * t / (T * 5))
        return (2 if v > -0.2 else 1 if v > -0.75 else 0,) * n
    if r == "mirgantis":  # kiekviena lemputė – savo ritmu, kaip senos kaitrinės „mirgančios“ lemputės
        return tuple(_lygis((t / (m["periodai"][j] * T * 2) + m["fazes"][j]) % 1.0, 0.55, 0.68)
                     if (t / (m["periodai"][j] * T * 2) + m["fazes"][j]) % 1.0 < 0.95 else 1 for j in range(n))
    if r == "kibirkstys":  # šviečia, o atskiros lemputės trumpam blyksteli/užgęsta
        laikas = int(t * 6)
        return tuple(1 if ((j * 7919 + (laikas + int(m["fazes"][j] * 9)) * 104729) * 2654435761 >> 9) % 100 < 9
                     else 2 for j in range(n))
    # „spalvos“ – šviečia viena spalva, kaimyninė blėsta, kitos užgesusios
    aktyvi = int(t / (T * 3)) % len(LEMPUCIU_SPALVU_TVARKA)
    return tuple(2 if c == aktyvi else 1 if c == (aktyvi + 1) % len(LEMPUCIU_SPALVU_TVARKA) else 0
                 for c in m["spalvos"])


def mirksejimo_zingsnis(egles, dt):
    """Paslenka kiekvienos eglės girliandą; grąžina [(eglė, pasikeitusių lempučių nr.)]."""
    pasikeite = []
    for e in egles:
        m = e["mirk"]
        m["t"] += dt
        m["liko"] -= dt
        if m["liko"] <= 0:
            m["rezimas"] = m["rnd"].choice([r for r in MIRKSEJIMO_REZIMAI if r != m["rezimas"]])
            m["liko"] = m["rnd"].uniform(15, 40) if m["rezimas"] != "ramus" else m["rnd"].uniform(4, 10)
            m["t"] = 0.0
        m["kaupta"] += dt
        if m["kaupta"] < MIRKSEJIMO_DAZNIS:
            continue
        m["kaupta"] = 0.0
        lygiai = lempuciu_lygiai(m)
        if lygiai != m["lygiai"]:
            seni = m["lygiai"]
            m["lygiai"] = lygiai
            pasikeite.append((e, [j for j in range(len(lygiai)) if lygiai[j] != seni[j]]))
    return pasikeite


# ---------------------------------------------------------------- retro girliandos (C9 lemputės)
# Kaip ~2000 m. darbalaukio programėlės: ekrano kraštuose kabo senoviškos dažyto stiklo lemputės ir mirksi.
GIRL_LEMPUTE = [  # žiūri žemyn: viršuje – tik mažytis laido spaustukas, toliau – stiklas iki smaigalio
    # Stiklas: l – apšviesta pusė, C – stiklas, d – tamsėjanti, c – tamsus kraštas, h – atspindys (blizga ir
    # užgesusi – tai atspindėta šviesa), g – įkaitęs vidurys (šviečia tik degant), r – kaustika: šviesa, praėjusi
    # pro stiklą, susirenka priešingoje pusėje ties smaigaliu
    "...kkk...",
    "..lCCCd..",
    ".lhhCCdc.",
    "lhhCCCCdc",
    "lhCCgCCdc",
    "lCCgggCdc",
    "lCCgggCdc",
    "CCCCgCCrc",
    ".CCCCCrc.",
    ".dCCCCrc.",
    "..dCCrc..",
    "...dcc...",
    "....c....",
]
GIRL_SPALVOS = ("#ff2a2a", "#ffd21a", "#1fe060", "#2f8fff", "#ff8a1a")  # ryškus dažytas stiklas
GIRL_LAIDAS, GIRL_LAIDAS2 = "#1d4d24", "#2f7a3a"  # susukto dvigyslio laido gyslos
GIRL_ILGIS, GIRL_STORIS = len(GIRL_LEMPUTE), len(GIRL_LEMPUTE[0])
GIRL_LYGIAI = 6  # ryškumo pakopos 0…5 (pixel art – be permatomumo)


GIRL_BLYKSNIO_CENTRAS = (3, 2)  # eilutė, stulpelis „žemyn“ piešinyje – ten, kur stiklo atšvaitas


@functools.lru_cache(maxsize=None)
def girliandos_lemputes_tinklelis(spalva, lygis, kryptis, blyksnis=0):
    """spalva – GIRL_SPALVOS indeksas; lygis 0 (užgesusi) … GIRL_LYGIAI−1 (šviečia visu ryškumu);
    kryptis – kur atsuktas smaigalys: „zemyn“, „desinen“ (kairės pusės girlianda) arba „kairen“.
    Silpnai įkaitęs siūlelis šviečia oranžiškai, todėl blėstanti lemputė ne tik tamsėja, bet ir šiltėja."""
    sviesi = GIRL_SPALVOS[spalva]
    tamsi = _maisyti(sviesi, "#000000", 0.7)
    d = lygis / (GIRL_LYGIAI - 1)
    stiklas = _maisyti(_maisyti(tamsi, "#ff7a1a", 0.35 * d * (1 - d) * 4 * 0.5), sviesi, d) if d < 1 else sviesi
    sp = {"k": GIRL_LAIDAS, "C": stiklas,
          "l": _maisyti(stiklas, "#ffffff", 0.12 + 0.1 * d),
          "d": _maisyti(stiklas, "#000000", 0.18 - 0.08 * d),
          "c": _maisyti(stiklas, "#000000", 0.32 - 0.12 * d),
          "h": _maisyti(stiklas, "#ffffff", 0.55 + 0.3 * d),
          "g": _maisyti(stiklas, "#fff6d8", 0.3 * d * d),
          "r": _maisyti(stiklas, "#ffffff", 0.25 + 0.2 * d)}
    t = [[None if ch == "." else sp[ch] for ch in eil] for eil in GIRL_LEMPUTE]
    if blyksnis:  # atspindžio žvaigždutė ant atšvaito: 1 – maža, 2 – su ilgesniais spinduliais
        r0, c0 = GIRL_BLYKSNIO_CENTRAS
        t[r0][c0] = "#ffffff"
        for ilgis in range(1, blyksnis + 1):
            sp_ = "#fffbe6" if ilgis == 1 else "#fff1b8"
            for dr, dc in ((-ilgis, 0), (ilgis, 0), (0, -ilgis), (0, ilgis)):
                if 0 <= r0 + dr < len(t) and 0 <= c0 + dc < len(t[0]):
                    t[r0 + dr][c0 + dc] = sp_
    if kryptis != "zemyn":
        t = [list(e) for e in zip(*t)]  # spaustukas kairėje, smaigalys dešinėje
        if kryptis == "kairen":
            t = [e[::-1] for e in t]
    return tuple(tuple(e) for e in t)


# Mirksėjimas kaip tikrų senų girliandų: kaitrinis siūlelis įkaista per ~0,07 s, o atvėsta per ~0,2 s (lemputė
# užgęsta su „uodega“); „mirgančios“ lemputės turi savo bimetalinį jungiklį – kiekviena įsijungia ir išsijungia
# netolygiais tarpais; kitus režimus kuria valdiklis (bėgantis, pakaitom, visa girlianda, lėtas kvėpavimas).
GIRL_REZIMAI = ("mirgantis", "visa", "begantis", "pakaitom", "kvepuoja", "kibirkstys", "ramus")
GIRL_IKAISTA, GIRL_ATVESTA = 0.07, 0.2


def girliandos_valdiklis(rnd, n):
    return {"rezimas": rnd.choice(GIRL_REZIMAI[:-1]), "liko": rnd.uniform(20, 45), "t": 0.0,
            "rnd": random.Random(rnd.randrange(1 << 30)), "laikas": [rnd.uniform(0, 2) for _ in range(n)],
            "ijungta": [True] * n, "sviesa": [1.0] * n, "lygiai": (GIRL_LYGIAI - 1,) * n,
            "iki_blyksnio": rnd.uniform(0.5, 2.0), "blyksniai": {}, "blyksnio_fazes": [0] * n}


def girliandos_tikslai(m, dt):
    """Kiek galios valdiklis duoda kiekvienai lemputei (0…1); dt – valdiklio laikas (pagal greitį)."""
    r, t, n, rnd = m["rezimas"], m["t"], len(m["sviesa"]), m["rnd"]
    if r == "mirgantis":  # bimetalinės: įjungta 0,8–3 s, išjungta 0,25–1 s, kiekvieną kartą kitaip
        for j in range(n):
            m["laikas"][j] -= dt
            if m["laikas"][j] <= 0:
                m["ijungta"][j] = not m["ijungta"][j]
                m["laikas"][j] = rnd.uniform(0.8, 3.0) if m["ijungta"][j] else rnd.uniform(0.25, 1.0)
        return [1.0 if v else 0.0 for v in m["ijungta"]]
    if r == "kibirkstys":  # šviečia, bet atskiros lemputės trumpam mirkteli (lyg klibantis kontaktas)
        for j in range(n):
            m["laikas"][j] -= dt
            if m["laikas"][j] <= 0:
                m["ijungta"][j] = not m["ijungta"][j]
                m["laikas"][j] = rnd.uniform(1.5, 8.0) if m["ijungta"][j] else rnd.uniform(0.05, 0.15)
        return [1.0 if v else 0.0 for v in m["ijungta"]]
    if r == "visa":  # mirksi visa girlianda kartu (kaip su viena „mirksinčia“ lempute nuosekliame jungime)
        return [1.0 if t % 2.0 < 1.1 else 0.0] * n
    if r == "begantis":  # trijų fazių bėgantis: šviečia dvi iš trijų, tamsi vieta bėga
        faze = int(t / 0.3) % 3
        return [0.0 if j % 3 == faze else 1.0 for j in range(n)]
    if r == "pakaitom":
        faze = int(t / 0.8) % 2
        return [1.0 if j % 2 == faze else 0.0 for j in range(n)]
    if r == "kvepuoja":  # reguliatoriumi lėtai šviesėja ir tamsėja, banga slenka girlianda
        return [0.55 + 0.45 * math.sin(2 * math.pi * (t / 4.0 - j / 12)) for j in range(n)]
    return [1.0] * n


def girliandu_zingsnis(girliandos, dt, greitis, atspindziai=True):
    """Valdiklis (pagal greitį) + siūlelio įkaitimas ir atvėsimas (visada tikru laiku). Grąžina
    [(girlianda, pasikeitusių lempučių nr.)] – perpiešiamos tik jos."""
    pasikeite = []
    for g in girliandos:
        m = g["mirk"]
        dv = dt * greitis
        m["t"] += dv
        m["liko"] -= dv
        if m["liko"] <= 0:
            m["rezimas"] = m["rnd"].choice([r for r in GIRL_REZIMAI if r != m["rezimas"]])
            m["liko"] = m["rnd"].uniform(20, 45) if m["rezimas"] != "ramus" else m["rnd"].uniform(5, 12)
            m["t"] = 0.0
            m["ijungta"] = [True] * len(m["ijungta"])
        tikslai = girliandos_tikslai(m, dv) if greitis > 0 else [1.0] * len(m["sviesa"])
        sv = m["sviesa"]
        kI, kA = 1 - math.exp(-dt / GIRL_IKAISTA), 1 - math.exp(-dt / GIRL_ATVESTA)
        for j, tk_ in enumerate(tikslai):
            sv[j] += (tk_ - sv[j]) * (kI if tk_ > sv[j] else kA)
        lygiai = tuple(min(GIRL_LYGIAI - 1, int(v * (GIRL_LYGIAI - 1) + 0.5)) for v in sv)
        js = set()
        if lygiai != m["lygiai"]:
            seni = m["lygiai"]
            m["lygiai"] = lygiai
            js.update(j for j in range(len(lygiai)) if lygiai[j] != seni[j])
        # Atspindys: kartais ant kurios nors šviečiančios lemputės stiklo trumpam blyksteli žvaigždutė
        # (kaip šviesa nuo blizgančio stiklo) – tarp mirksėjimų girlianda „gyva“.
        bl, fazes, pilna = m["blyksniai"], m["blyksnio_fazes"], GIRL_LYGIAI - 1
        if atspindziai:
            m["iki_blyksnio"] -= dt
            if m["iki_blyksnio"] <= 0:
                m["iki_blyksnio"] = m["rnd"].uniform(0.6, 2.2)
                kandidatai = [j for j, v in enumerate(lygiai) if v == pilna and j not in bl]
                if kandidatai:
                    bl[m["rnd"].choice(kandidatai)] = 0.0
        for j in list(bl):
            bl[j] += dt
            t_ = bl[j]
            faze = 0 if not atspindziai or lygiai[j] < pilna else \
                1 if t_ < 0.07 else 2 if t_ < 0.2 else 1 if t_ < 0.3 else 0
            if faze != fazes[j]:
                fazes[j] = faze
                js.add(j)
            if faze == 0:
                del bl[j]
        if js:
            pasikeite.append((g, sorted(js)))
    return pasikeite


def piesti_girlianda(p, g, sritis):
    """Piešia tik tai, kas patenka į sritį – kad mirktelėjus vienai lemputei nereikėtų perpiešti visos girliandos."""
    l, t, r, b = sritis
    laidas, ys = g["laidas"], g["laido_y"]  # laidas surikiuotas pagal y – imama tik srities atkarpa
    d0 = laidas[0][2] if laidas else 0
    for x, y, d, spalva in laidas[bisect.bisect_right(ys, t - d0):bisect.bisect_left(ys, b)]:
        if t - d < y < b and l - d < x < r:
            p.staciakampis(x, y, x + d, y + d, spalva)
    lygiai, fazes = g["mirk"]["lygiai"], g["mirk"]["blyksnio_fazes"]
    kryptis = "desinen" if g["kaire"] else "kairen"
    for j, (x0, y0, spalva, rb) in enumerate(g["vietos"]):
        if rb[2] > l and rb[0] < r and rb[3] > t and rb[1] < b:
            piks_piesti(p, girliandos_lemputes_tinklelis(spalva, lygiai[j], kryptis, fazes[j]), x0, y0, g["Pg"])


def piesti_egle(p, e, n):
    G = PIKS_SPALVOS["G"]
    t = piks_tinklelis(EGLIU_SABLONAI[e.get("sab", 2)], {"1": G, "o": G, "g": G})
    for r, c in e["tams"]:
        t[r][c] = PIKS_SPALVOS["g"]
    if n["egliu_burbuliukai"]:
        for r, c, spalva in e["burb"]:
            t[r][c] = spalva
    if n["egliu_lemputes"]:
        for r, c, spalva, j in e["lemp"]:
            lygis = e["mirk"]["lygiai"][j] if n["egliu_mirksi"] else 2
            t[r][c] = LEMPUCIU_LYGIAI[spalva][lygis]
    piks_piesti(p, t, e["x0"], e["y0"], e["s"])
    if n.get("sniegas_ant_egliu", False):
        # lengvas sniego pabarstymas – plona juostelė tik ant atvirų šakų viršų (ne visas langelis)
        s, x0, y0 = e["s"], e["x0"], e["y0"]
        for r, c, dalis, kr, ds in e.get("snieg", ()):
            xa, xb = x0 + round((c + kr) * s), x0 + round((c + ds) * s)
            ya = y0 + round(r * s)
            if xb > xa:
                p.staciakampis(xa, ya, xb, ya + max(1, round(s * dalis)), SNIEGAS)


# ---------------------------------------------------------------- pixel art eglutės
PIKS_SPALVOS = {"G": "#18a020", "g": "#0a5c14", "n": "#5c3010", "W": SNIEGAS, "w": "#a9c8ea"}

# '1' – lemputė, 'o' – burbuliukas
PIKS_EGLE = [
    "......G......",
    ".....GGG.....",
    ".....GGG.....",
    "....GG1GG....",
    "...GoGGGgG...",
    "..G1GGGG1GG..",
    "....GGGGG....",
    "...GG1GoGG...",
    "..GGgGGGG1G..",
    ".G1GGoGGGGgG.",
    "...GGGGGGG...",
    "..GGgG1GGoG..",
    ".GGoGGGGgG1G.",
    "G1GGG1GGGoG1G",
    "......n......",
    "......n......",
]

# Siauresnės eglės (9 ir 11 langelių vietoj 13) – tokio pat aukščio. Puošmenų skaičius – pagal šakų plotą.
PIKS_EGLE_SIAURA = [
    "....G....",
    "...GGG...",
    "...GGG...",
    "..GGGGG..",
    "...GGG...",
    "..GGGGG..",
    ".GGGGGGG.",
    "..GGGGG..",
    ".GGGGGGG.",
    ".GGGGGGG.",
    "..GGGGG..",
    ".GGGGGGG.",
    "GGGGGGGGG",
    "GGGGGGGGG",
    "....n....",
    "....n....",
]
PIKS_EGLE_VIDUTINE = [
    ".....G.....",
    "....GGG....",
    "....GGG....",
    "...GGGGG...",
    "...GGGGG...",
    "..GGGGGGG..",
    "...GGGGG...",
    "..GGGGGGG..",
    "..GGGGGGG..",
    ".GGGGGGGGG.",
    "..GGGGGGG..",
    ".GGGGGGGGG.",
    ".GGGGGGGGG.",
    "GGGGGGGGGGG",
    ".....n.....",
    ".....n.....",
]
EGLIU_SABLONAI = (PIKS_EGLE_SIAURA, PIKS_EGLE_VIDUTINE, PIKS_EGLE)  # 0 – siaura, 1 – siauresnė, 2 – įprasta


EGLIU_PLOCIAI = (69, 85, 100)  # šablonų plotis, % įprastos (9, 11, 13 langelių) – tik šie pasirinkimai ką nors keičia


def egliu_plocio_zingsnis(v):
    """Siauriausių eglių plotis – iki artimiausio tikro pasirinkimo (senose bylose – bet kuri reikšmė
    60–100 %; šablonai tik trijų pločių)."""
    return next((p for p in EGLIU_PLOCIAI if v <= p), 100)


def egliu_auksciai(us, a, b, ref_a, ref_b):
    """Atsitiktinio aukščio eglių aukščiai. us – kiekvienos eglės pastovus atsitiktinis skaičius 0…1 (eilė pagal
    dydį), [a, b] – „Mažiausias“ ir „Didžiausias“, [ref_a, ref_b] – ribos, kai eglės buvo išdėliotos. Ne a + u·(b − a)
    (tada pakeitus bet kurią ribą keistųsi visų eglių aukščiai), o:
    – vidurinės eglės, kurios telpa į [a, b], lieka savo („pradinio“) aukščio;
    – vidurinės, atsidūrusios už ribų, tolygiai išsidėsto tarp ribos ir artimiausios likusios (o ne sulimpa į ribą);
    – mažiausių ketvirtis – iki „Mažiausio“, didžiausių – iki „Didžiausio“: mažiausia eglė lygiai a, didžiausia – b.
    Grąžinus ribas – vėl tie patys aukščiai."""
    a, b = sorted((a, b))
    n = len(us)
    h0 = [ref_a + u * (ref_b - ref_a) for u in us]
    if n < 2:
        return [float(min(b, max(a, x))) for x in h0]
    eile = sorted(range(n), key=lambda i: us[i])
    k = min(max(1, round(n * 0.25)), n // 2)
    vid = eile[k:n - k]
    h = list(h0)
    telpa = [i for i in vid if a <= h0[i] <= b]
    zemiau = [i for i in vid if h0[i] < a]  # jau surikiuotos pagal dydį
    auksciau = [i for i in vid if h0[i] > b]
    vidurys = (a + b) / 2
    virsus_z = min((h0[i] for i in telpa), default=vidurys if auksciau else b)
    for j, i in enumerate(zemiau):  # tarp a ir žemiausios likusios
        h[i] = a + (virsus_z - a) * (j + 1) / (len(zemiau) + 1)
    apacia_a = max((h0[i] for i in telpa), default=vidurys if zemiau else a)
    for j, i in enumerate(reversed(auksciau)):  # tarp aukščiausios likusios ir b
        h[i] = b - (b - apacia_a) * (j + 1) / (len(auksciau) + 1)
    inkaras = h[eile[k]] if k < n else b
    for j in range(k):  # mažiausios: a … iki pirmos vidurinės
        h[eile[j]] = a + (inkaras - a) * j / k
    inkaras = h[eile[n - 1 - k]]
    for j in range(k):  # didžiausios: b … iki paskutinės vidurinės
        h[eile[n - 1 - j]] = b - (b - inkaras) * j / k
    return [float(min(b, max(a, x))) for x in h]


def egliu_sablonai_pagal_ploti(min_proc):
    """Kurie šablonai leidžiami: ne siauresni nei min_proc % įprastos eglės pločio."""
    rez = [i for i, sab in enumerate(EGLIU_SABLONAI) if len(sab[0]) / len(PIKS_EGLE[0]) * 100 + 0.5 >= min_proc]
    return rez or [2]


# Pixel art snaigės – po vieną kiekvienai TIPAI rūšiai, ta pačia tvarka
PIKS_SNAIGES = [
    ["W"],
    ["WW", "WW"],
    [".W.", "WWW", ".W."],
    ["..W..", "W.W.W", ".WWW.", "W.W.W", "..W.."],
    ["W.W.W", ".WWW.", "WWwWW", ".WWW.", "W.W.W"],
    ["...W...", ".W.W.W.", "..WWW..", "WWWwWWW", "..WWW..", ".W.W.W.", "...W..."],
    ["....W....", ".W.wWw.W.", "..W.W.W..", ".w.WWW.w.", "WWWWwWWWW", ".w.WWW.w.", "..W.W.W..", ".W.wWw.W.",
     "....W...."],
    [".....W.....", "..W.wWw.W..", "...W.W.W...", "..w.WWW.w..", ".W..wWw..W.", "WWWWWwWWWWW",
     ".W..wWw..W.", "..w.WWW.w..", "...W.W.W...", "..W.wWw.W..", ".....W....."],
    ["..WWWWW..", ".WwwwwwW.", "WwwWWWwwW", "WwWwwwWwW", "WwWwwwWwW", "WwwWWWwwW", ".WwwwwwW.", "..WWWWW.."],  # Šešiakampė plokštelė
    ["..WWWWW..", ".WWwwwWW.", "WwwWwWwwW", "WwwwWwwwW", "WWWWWWWWW", "WwwwWwwwW", "WwwWwWwwW", ".WWwwwWW.", "..WWWWW.."],  # Sektorinė plokštelė
    ["....WWW....", "...WwwwW...", ".WW.WwW.WW.", "WwwW.W.WwwW", ".WwWWWWWwW.", "....WwW....", ".WwWWWWWwW.", "WwwW.W.WwwW", ".WW.WwW.WW.", "...WwwwW...", "....WWW...."],  # Žvaigždinė plokštelė
    [".....W.....", "..W..W..W..", "...W.W.W...", "W...WWW...W", ".WW.WwW.WW.", "..WWWwWWW..", ".WW.WwW.WW.", "W...WWW...W", "...W.W.W...", "..W..W..W..", ".....W....."],  # Dvylikašakė
    ["WWWWWWW", ".wWwWw.", "..WwW..", "..WwW..", "..WwW..", ".wWwWw.", "WWWWWWW"],  # Stulpelis su kepurėlėmis
]


def transponuoti(rastas):
    return ["".join(rastas[y][x] for y in range(len(rastas))) for x in range(len(rastas[0]))]


# Pixel art snaigės sukasi šuoliukais: kaitaliojami du piešiniai. Šešiakampėms (Žvaigždutė, Plunksninė)
# pasukimas 90° atrodo kaip 30°, todėl antras piešinys – tas pats, apverstas per įstrižainę; kitos nupieštos ranka.
PIKS_SNAIGES_PASUKTOS = {
    3: transponuoti(PIKS_SNAIGES[3]),
    4: [".W.W.", "W.W.W", ".WwW.", "W.W.W", ".W.W."],
    5: ["W.....W", ".W.W.W.", "..WWW..", ".WWwWW.", "..WWW..", ".W.W.W.", "W.....W"],
    6: ["W.w...w.W", ".W..W..W.", "w.W.W.W.w", "...WWW...", ".WWWwWWW.", "...WWW...", "w.W.W.W.w", ".W..W..W.",
        "W.w...w.W"],
    7: transponuoti(PIKS_SNAIGES[7]),
    8: transponuoti(PIKS_SNAIGES[8]),    # plokštelės: 90° atrodo kaip 30°
    9: transponuoti(PIKS_SNAIGES[9]),
    11: transponuoti(PIKS_SNAIGES[11]),
    12: transponuoti(PIKS_SNAIGES[12]),  # stulpelis vartosi
}
# Pixel art langelio dydis (taškais, kai ekrano mastelis 1 ir dydis 100 %) parinktas taip, kad pixel art snaigės
# būtų tokio pat skersmens kaip įprastos: didžiausia (Plunksninė) – 11 langelių, įprasta – 2 × 9,5 taško.
PIKS_SNAIGES_LANGELIS = 2 * 9.5 / 11
PIKS_SUKIMO_ZINGSNIS = {3: 30.0, 4: 22.5, 5: 45.0, 6: 45.0, 7: 30.0, 8: 30.0, 9: 30.0, 11: 15.0, 12: 90.0}  # kiek laipsnių „pasisuka“ vienu šuoliuku


def piks_tinklelis(eilutes, pakeitimai=None):
    pakeitimai = pakeitimai or {}
    return [[None if c == "." else pakeitimai.get(c, PIKS_SPALVOS.get(c)) for c in e] for e in eilutes]


def piks_piesti(p, tinklas, x0, y0, mastelis):
    """Tinklelį piešia stačiakampiais; gretimi tos pačios spalvos pikseliai eilutėje sujungiami.
    Mastelis gali būti ir trupmeninis – langelių ribos tada apvalinamos."""
    for r, eil in enumerate(tinklas):
        c = 0
        n = len(eil)
        y1, y2 = y0 + round(r * mastelis), y0 + round((r + 1) * mastelis)
        while c < n:
            spalva = eil[c]
            if spalva is None:
                c += 1
                continue
            c1 = c
            while c < n and eil[c] == spalva:
                c += 1
            p.staciakampis(x0 + round(c1 * mastelis), y1, x0 + round(c * mastelis), y2, spalva)


def egles_puosimas(rnd, sablonas=PIKS_EGLE):
    """Kiekvienai eglei atsitiktinės lempučių, burbuliukų ir tamsių šakų vietos (įprastoje eglėje – tiek, kiek
    pažymėta šablone; siauresnėse – proporcingai šakų plotui). Puošmenos neliečia viena kitos (net įstrižai),
    viršūnė lieka tuščia; tamsios šakos – tik eglės viduje (ant krašto jos atrodytų kaip skylės)."""
    egle = {(r, c) for r, eil in enumerate(sablonas) for c, ch in enumerate(eil) if ch in "G1og"}
    iprasta = sum(ch in "G1og" for eil in PIKS_EGLE for ch in eil)
    kiek = {ch: round(sum(eil.count(ch) for eil in PIKS_EGLE) * len(egle) / iprasta) for ch in "1og"}
    vietos = sorted((r, c) for r, c in egle if r > 0)
    rnd.shuffle(vietos)
    uzimta = set()

    def parinkti(kiekis, tinka):
        rez = []
        for r, c in vietos:
            if len(rez) >= kiekis:
                break
            if (r, c) in uzimta or not tinka(r, c):
                continue
            if any((r + dr, c + dc) in uzimta for dr in (-1, 0, 1) for dc in (-1, 0, 1)):
                continue
            uzimta.add((r, c))
            rez.append((r, c))
        return rez

    # pirma tamsios šakos – joms tinka mažiau vietų
    tams = parinkti(kiek["g"], lambda r, c: all((r + dr, c + dc) in egle for dr in (-1, 0, 1) for dc in (-1, 0, 1)))
    lemp_v = sorted(parinkti(kiek["1"], lambda r, c: True))
    burb_v = parinkti(kiek["o"], lambda r, c: True)
    return lemp_v, burb_v, tams


def sukurti_piks_egle(x, y, aukstis, rnd, sab=2):
    """Pikselinė eglė: langelio dydis – pagal norimą aukštį; sab – plotis (EGLIU_SABLONAI). Langelis
    trupmeninis (langelių ribos apvalinamos, kaip senio ir girliandų): aukštis lygiai toks, koks nustatytas
    (su sveiku langeliu aukštis keistųsi tik kas 16 px)."""
    sablonas = EGLIU_SABLONAI[sab]
    s = max(1.0, aukstis / len(sablonas))
    plotis = len(sablonas[0])
    lemp, burb = [], []
    spalvos = list(LEMPUCIU_SPALVOS)
    rnd.shuffle(spalvos)
    lemp_v, burb_v, tams = egles_puosimas(rnd, sablonas)
    for r, c in lemp_v:
        lemp.append((r, c, spalvos[len(lemp) % len(spalvos)], len(lemp)))
    for r, c in burb_v:
        burb.append((r, c, rnd.choice(BURBULIUKU_SPALVOS)))
    x0 = int(round(x - plotis * s / 2))
    y0 = int(y) - round(len(sablonas) * s)
    # Sniegas ant šakų: tik dalis atvirų šakų viršų (virš jų – tuščia), kiekvienai eglei kitaip.
    # Juostelė – 25–45 % langelio aukščio, kartais ne per visą plotį, kad neatrodytų kaip lygus kraštas.
    sr = random.Random(x0 * 7919 + y0 * 31 + round(s * 16))  # nevartoja rnd – eglių išdėstymas nesikeičia
    snieg = []
    for r, eil in enumerate(sablonas):
        for c, ch in enumerate(eil):
            if ch in ".n" or (r > 0 and sablonas[r - 1][c] != "."):
                continue
            if sr.random() < 0.45:
                kr, ds = (0.0, 1.0) if sr.random() < 0.6 else sr.choice(((0.0, 0.6), (0.4, 1.0)))
                snieg.append((r, c, sr.uniform(0.25, 0.45), kr, ds))
    return {"sab": sab, "x0": x0, "y0": y0, "s": s, "lemp": lemp, "burb": burb, "tams": tams, "snieg": snieg,
            "ribos": (x0 - 1, y0 - 1, x0 + round(plotis * s) + 1, int(y) + 1), "mirk": naujas_mirksejimas(rnd, lemp)}


# ---------------------------------------------------------------- pixel art riedantys bumbuliukai
BUMBULU_SPALVOS = (("#e63946", "#9e1b24", "#ff9aa0"), ("#2fa84f", "#196b2f", "#9ae6ad"),
                   ("#f4b400", "#a87400", "#ffe08a"), ("#3a86ff", "#1d4fb0", "#a3c6ff"),
                   ("#9b5de5", "#5c2e9e", "#d3b3f7"), ("#c9d1db", "#7d8896", "#ffffff"),
                   ("#ff6fa8", "#b0306a", "#ffc0da"), ("#2a9d8f", "#16645b", "#86e3d8"))  # pagrindinė, šešėlis, blizgesys
BUMBULU_SPALVU_PAVADINIMAI = ("Raudona", "Žalia", "Auksinė", "Mėlyna", "Violetinė", "Sidabrinė", "Rožinė", "Turkio")
BUMBULU_RASTAI = ("vienspalvis", "juosta", "dvi_juostos", "taskai", "zigzagas", "langeliai", "zvaigzde", "snaige",
                  "saulute", "ausrine", "rutele", "rombai")
# paskutiniai keturi – baltiški ženklai: Saulutė, Aušrinė (aštuonkampė žvaigždė), keturlapis žiedelis, juostų rombai
BUMBULU_RASTU_PAVADINIMAI = ("Lygus", "Juosta", "Dvi juostos", "Taškai", "Zigzagas", "Langeliai", "Žvaigždė", "Snaigė",
                             "Saulutė", "Aušrinė", "Žiedelis", "Rombai")
BUMBULU_KADRAI = 8  # sukimosi kadrai
BUMBULU_BLYKSNIAI = 3  # pradingimo / atsiradimo žiežirbų kadrai


def _rasto_taskas(rastas, xr, yr, R):
    """Ar burbulo koordinačių taškas (xr, yr) priklauso raštui."""
    r = math.hypot(xr, yr)
    if rastas == "juosta":
        return abs(yr) < R * 0.24
    if rastas == "dvi_juostos":
        return abs(abs(yr) - R * 0.42) < R * 0.13
    if rastas == "taskai":
        return any(math.hypot(xr - px, yr - py) < R * 0.18
                   for px, py in ((0, 0), (R * 0.62, 0), (-R * 0.62, 0), (0, R * 0.62), (0, -R * 0.62)))
    if rastas == "zigzagas":
        return abs(yr - R * 0.3 * (abs(((xr / R * 2.5) % 2) - 1) * 2 - 1)) < R * 0.16
    if rastas == "langeliai":
        dydis = R * 0.55
        return (math.floor(xr / dydis) + math.floor(yr / dydis)) % 2 == 0 and r < R * 0.8
    if rastas == "zvaigzde":
        kampas = math.atan2(yr, xr) + math.pi / 2
        return r < R * (0.3 + 0.32 * max(0.0, math.cos(5 * kampas)))
    if rastas == "snaige":
        if r > R * 0.68:
            return False
        storis = max(0.55, R * 0.09)
        return any(abs(xr * math.sin(a) - yr * math.cos(a)) < storis for a in (0, math.pi / 3, 2 * math.pi / 3))
    if rastas == "saulute":  # Saulė: taškas centre, ratas ir aštuoni spinduliai-taškeliai
        if r < R * 0.2 or R * 0.38 < r < R * 0.54:
            return True
        kampas = math.atan2(yr, xr) % (math.pi / 4)
        return R * 0.66 < r < R * 0.86 and min(kampas, math.pi / 4 - kampas) * r < max(0.6, R * 0.1)
    if rastas == "ausrine":  # Aušrinė (Auseklis) – aštuonkampė žvaigždė iš dviejų kvadratų, su akute viduryje
        ax, ay = abs(xr), abs(yr)
        return (max(ax, ay) <= R * 0.36 or ax + ay <= R * 0.56) and r > R * 0.15
    if rastas == "rutele":  # Žiedelis: keturi rombo formos lapeliai aplink taškelį
        if r < R * 0.16:
            return True
        for px, py in ((R * 0.46, 0), (-R * 0.46, 0), (0, R * 0.46), (0, -R * 0.46)):
            ilg, plt = (R * 0.34, R * 0.24) if px else (R * 0.24, R * 0.34)
            if abs(xr - px) / ilg + abs(yr - py) / plt <= 1:
                return True
        return False
    if rastas == "rombai":  # tautinės juostos rombas su kryželiu viduje
        ax, ay = abs(xr), abs(yr)
        if R * 0.46 <= ax + ay <= R * 0.66:
            return True
        return ax + ay < R * 0.3 and (ax < R * 0.09 or ay < R * 0.09)
    return False


@functools.lru_cache(maxsize=1024)  # visų derinių – ~5500 (~18 MB); vienam išbarstymui reikia ~300
def bumbulo_matmenys(R0, P, dydis):
    """(sveikas pikselis Pb, spindulys R langeliais, tikslus langelio dydis Pf) bumbuliukui, kurio „įprastas“
    spindulys R0 (5–7), esant ekrano pikseliui P ir dydžiui dydis %. Keičiant tik sveiką pikselį dydis
    keistųsi laiptais (1920×1080 ekrane 40–74 % – 1 px, 75–100 % – 2 px), todėl: pikselis – round, tinklelio dydis R parenkamas pagal norimą skersmenį, o langelis Pf – toks, kad skersmuo būtų lygiai
    norimas (Pf nuo Pb skiriasi ≤ ~10 %, langeliai – ne daugiau kaip 1 px skirtumu). Bumbuliukas didėja tolygiai
    ir niekada nesumažėja didinant; 100 % – lygiai kaip anksčiau."""
    Pd = P * dydis / 100
    Pb = max(1, int(round(Pd)))
    D = (2 * R0 + 5) * Pd  # norimas skersmuo, px
    R = max(3, min(16, int(round((D / Pb - 5) / 2))))
    while R > 3 and D < 2 * R + 5:  # langelis ne mažesnis už 1 px (kitaip skersmuo būtų didesnis už norimą)
        R -= 1
    return Pb, R, max(1.0, D / (2 * R + 5))


def bumbulo_tinklelis(R, spalva, rastas, kadras, langelis=None):
    """Pixel art žaisliukas-burbulas: raštas ir kepurėlė sukasi kartu su juo, blizgesys lieka vietoje.
    langelis – tinklelio kraštinė (kad mažesni pradingimo kadrai būtų tame pačiame dydyje)."""
    pagr, tamsi, sviesi = BUMBULU_SPALVOS[spalva]
    puosimas = "#d62828" if spalva in (2, 5) else "#fff4d6"
    k = kadras * 2 * math.pi / BUMBULU_KADRAI
    cs, sn = math.cos(k), math.sin(k)
    n = langelis or 2 * R + 5
    c = n / 2
    t = [[None] * n for _ in range(n)]
    # Stiklas: keturi tonai pagal rutulio normalę (šviesa iš viršaus kairės), lango atspindžio lankas ir
    # baltas blizgesys viršuje kairėje, o apačioje dešinėje – šviesus pusmėnulis: šviesa, praėjusi pro stiklą
    # (kaustika). Be jo burbulas atrodė kaip matinis plastikinis rutulys.
    tonai = (tamsi, _maisyti(pagr, tamsi, 0.45), pagr, _maisyti(pagr, sviesi, 0.45))
    kaustika, puos_seselis = _maisyti(pagr, sviesi, 0.6), _maisyti(puosimas, tamsi, 0.45)
    lx, ly, lz = -0.55, -0.6, 0.58
    for y in range(n):
        for x in range(n):
            dx, dy = x + 0.5 - c, y + 0.5 - c
            xr, yr = dx * cs + dy * sn, -dx * sn + dy * cs  # taškas burbulo koordinatėse
            atstumas = math.hypot(dx, dy)
            if R >= 3 and abs(xr) <= 1.7 and -R - 1.8 <= yr <= -R + 0.9:  # auksinė kepurėlė
                t[y][x] = "#c99a00" if abs(xr) > 0.9 else "#f2c94c"
                continue
            if atstumas > R:
                continue
            nx, ny = dx / R, dy / R
            sviesa = nx * lx + ny * ly + math.sqrt(max(0.0, 1 - nx * nx - ny * ny)) * lz
            tonas = 0 if sviesa < 0.05 else 1 if sviesa < 0.35 else 2 if sviesa < 0.8 else 3
            spalva_px = tonai[tonas]
            if R >= 3 and _rasto_taskas(rastas, xr, yr, R):
                spalva_px = puosimas if tonas >= 2 else puos_seselis
            kampas = math.degrees(math.atan2(dy, dx)) % 360
            if 0.55 * R < atstumas < 0.85 * R and abs((kampas - 45 + 180) % 360 - 180) < 32:
                spalva_px = kaustika
            if 0.5 * R < atstumas < 0.78 * R and 195 < kampas < 250:  # lango atspindys
                spalva_px = sviesi
            if math.hypot(dx + R * 0.42, dy + R * 0.42) < max(0.7, R * 0.13):
                spalva_px = "#ffffff"
            if atstumas > R - 0.9:  # kontūras – kad matytųsi ir ant balto sniego
                spalva_px = tamsi
            t[y][x] = spalva_px
    return tuple(tuple(e) for e in t)


@functools.lru_cache(maxsize=None)
def blyksnio_tinklelis(n, kadras):
    """Žiežirbos, kai bumbuliukas pradingsta ar atsiranda: blyksnis centre, paskui tolstantys taškeliai."""
    t = [[None] * n for _ in range(n)]
    c = n // 2

    def taskas(x, y, spalva):
        if 0 <= x < n and 0 <= y < n:
            t[y][x] = spalva

    if kadras == 0:
        for d in range(-2, 3):
            taskas(c + d, c, "#ffffff")
            taskas(c, c + d, "#ffffff")
        for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            taskas(c + dx, c + dy, "#ffe08a")
    else:
        spindulys = (n // 2 - 2) * (0.55 if kadras == 1 else 0.95)
        for i in range(8):
            a = i * math.pi / 4
            x, y = round(c + math.cos(a) * spindulys), round(c + math.sin(a) * spindulys)
            spalva = ("#ffffff", "#ffe08a")[i % 2] if kadras == 1 else ("#ffe08a", "#c9d1db")[i % 2]
            taskas(x, y, spalva)
            if kadras == 1 and i % 2 == 0:
                taskas(x + round(math.cos(a)), y + round(math.sin(a)), "#ffe08a")
    return tuple(tuple(e) for e in t)


BUMBULU_DINGIMAI = ("susitraukia", "suduzta", "istirpsta", "ismenga")
BUMBULU_DINGIMU_PAVADINIMAI = ("Susitraukia", "Sudūžta", "Ištirpsta", "Įsmenga į sniegą")
# kaip atsiranda, jei įjungtas atitinkamas dingimas (sudužęs – nukrenta iš dangaus)
BUMBULU_ATSIRADIMAI = {"susitraukia": "isauga", "suduzta": "nukrenta", "istirpsta": "susidaro",
                       "ismenga": "isnyra"}
TIRPIMO_KADRAI = 6


def bumbulo_animacijos_trukme(anim, R):
    """Kiek trunka dingimas ar atsiradimas (ekrane ir peržiūroje – tas pats). R – bumbuliuko spindulys langeliais."""
    return {"susitraukia": 0.06 * (R - 1) + 0.08 * BUMBULU_BLYKSNIAI, "suduzta": 0.16, "istirpsta": 0.5,
            "ismenga": 0.6, "isauga": 0.08 + 0.06 * (R - 1), "susidaro": 0.5, "isnyra": 0.6}[anim]


@functools.lru_cache(maxsize=512)
def tirpimo_tinklelis(R, spalva, rastas, lygis):
    """Burbulas, iš kurio atsitiktine (bet pastovia) tvarka dingsta pikseliai – „ištirpimas“."""
    t = [list(e) for e in bumbulo_tinklelis(R, spalva, rastas, 0)]
    riba = (lygis + 1) / (TIRPIMO_KADRAI + 1)
    for y, eil in enumerate(t):
        for x in range(len(eil)):
            if ((x * 73856093 ^ y * 19349663) % 1009) / 1009 < riba:
                eil[x] = None
    return tuple(tuple(e) for e in t)


# Ženkliukas: mėlyname suapvalintame kvadrate – sniego kalniukas ir krentančios snaigės. Snaigių vietos – kvadrato dalimis; 16 px – po vieną tašką, didesniems – kryželiai.
LOGO_FONAS, LOGO_KRASTAS, LOGO_SESELIS = "#8db6e6", "#2f5d9c", "#dbe7f5"
LOGO_SNAIGES = ((0.28, 0.22), (0.66, 0.16), (0.80, 0.40), (0.47, 0.36), (0.20, 0.47), (0.58, 0.52))
LOGO_SNAIGES_16 = ((4, 4), (10, 3), (7, 7), (12, 8))


def logo_tinklelis(dydis=16):
    """Ženkliuko tinklelis dydis×dydis (vienas langelis – vienas taškas)."""
    n = dydis
    t = [[None] * n for _ in range(n)]
    r, bw, c = n * 0.22, max(1, round(n / 24)), (n - 1) / 2
    for y in range(n):
        for x in range(n):
            dx, dy = max(0.0, abs(x - c) - (c - r)), max(0.0, abs(y - c) - (c - r))
            d = math.hypot(dx, dy)
            if d <= r + 0.3:
                krastas = abs(x - c) > c - bw + 0.5 or abs(y - c) > c - bw + 0.5 or d > r - bw + 0.3
                t[y][x] = LOGO_KRASTAS if krastas else LOGO_FONAS

    def taskas(x, y, spalva):
        if 0 <= x < n and 0 <= y < n and t[y][x] == LOGO_FONAS:
            t[y][x] = spalva
    virsune = n * 0.42  # kalniukas: parabolė, šešėlis – siaura juosta dešiniajame šlaite (saulė iš kairės)
    for x in range(n):
        h = virsune * max(0.0, 1 - ((x - c) / (n * 0.62)) ** 2)
        ytop = n - 1 - h
        for y in range(n):
            if y >= ytop:
                gyl = y - ytop
                sesel = x > c + n * 0.08 and max(1, n / 16) <= gyl <= max(2, n / 7)
                taskas(x, y, LOGO_SESELIS if sesel else SNIEGAS)
    if n < 24:
        for x, y in LOGO_SNAIGES_16:
            taskas(x, y, SNIEGAS)
    else:
        u = max(1, n // 32)  # kryželio „pikselis“ – dideliuose ženkliukuose (128, 256 px) snaigės ne taškeliai
        for fx, fy in LOGO_SNAIGES[:5 if n < 48 else 6]:
            x, y = round(fx * (n - 1)), round(fy * (n - 1))
            for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                for yy in range(u):
                    for xx in range(u):
                        taskas(x + dx * u + xx - u // 2, y + dy * u + yy - u // 2, SNIEGAS)
    return t


def logo_png(s):
    """Pixel art ženkliukas PNG formatu (be papildomų bibliotekų): didinamas sveiku kartotiniu, centruojamas."""
    t = logo_tinklelis(s)
    n = len(t)
    m = max(1, s // n)
    poslinkis = (s - n * m) // 2
    eilutes = []
    for y in range(s):
        eil = bytearray(b"\0")
        for x in range(s):
            tx, ty = (x - poslinkis) // m, (y - poslinkis) // m
            spalva = t[ty][tx] if 0 <= tx < n and 0 <= ty < n else None
            if spalva is None:
                eil += b"\0\0\0\0"
            else:
                eil += bytes((int(spalva[1:3], 16), int(spalva[3:5], 16), int(spalva[5:7], 16), 255))
        eilutes.append(bytes(eil))

    def gabalas(tipas, duom):
        return struct.pack(">I", len(duom)) + tipas + duom + struct.pack(">I", zlib.crc32(tipas + duom) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n" + gabalas(b"IHDR", struct.pack(">IIBBBBB", s, s, 8, 6, 0, 0, 0))
            + gabalas(b"IDAT", zlib.compress(b"".join(eilutes), 9)) + gabalas(b"IEND", b""))


def logo_ico(dydziai=(16, 32, 48)):
    """.ico su PNG vaizdais (Windows Vista+) – sistemos dėklo piktogramai."""
    pngs = [logo_png(d) for d in dydziai]
    antraste = struct.pack("<HHH", 0, 1, len(pngs))
    poslinkis = 6 + 16 * len(pngs)
    irasai, duomenys = b"", b""
    for d, png in zip(dydziai, pngs):
        irasai += struct.pack("<BBBBHHII", d % 256, d % 256, 0, 0, 1, 32, len(png), poslinkis + len(duomenys))
        duomenys += png
    return antraste + irasai + duomenys


# ---------------------------------------------------------------- autostartas

def autostarto_komanda():
    if SUKOMPILIUOTA:
        return f'"{Path(sys.executable).resolve()}" --sumazinta'
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    exe = pythonw if pythonw.exists() else Path(sys.executable)
    return f'"{exe}" "{Path(__file__).resolve()}" --sumazinta'


def autostartas_ijungtas():
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTARTO_RAKTAS) as r:
            return winreg.QueryValueEx(r, AUTOSTARTO_VARDAS)[0]
    except OSError:
        return None


def nustatyti_autostarta(ijungti):
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTARTO_RAKTAS, 0, winreg.KEY_SET_VALUE) as r:
        if ijungti:
            winreg.SetValueEx(r, AUTOSTARTO_VARDAS, 0, winreg.REG_SZ, autostarto_komanda())
        else:
            try:
                winreg.DeleteValue(r, AUTOSTARTO_VARDAS)
            except FileNotFoundError:
                pass


# ---------------------------------------------------------------- sniego sluoksnis

SVORIAI = ((-2, 0.3), (-1, 0.7), (0, 1.0), (1, 0.7), (2, 0.3))
SVORIU_SUMA = sum(w for _, w in SVORIAI)  # perkeliant esamą sniegą – kad jo neatsirastų daugiau nei paimta


def nusodinti(h, c, kiekis, maks, krastai=False, profilis=None, sust=None):
    """Snaigė nusėda; profilis – kiekvieno stulpelio didžiausio aukščio dalis (kopos), kad sniegas
    niekada nevirstų lygia juosta. sust – buldozerių sustumti kauburiai: jiems kopų riba netaikoma
    (kitaip pirmoji šalia nukritusi snaigė nukirptų visą kauburį)."""
    n = len(h)
    for dc, w in SVORIAI:
        j = c + dc
        if 0 <= j < n:
            riba = maks * profilis[j] if profilis and not (sust and sust[j]) else maks
            v = h[j] + kiekis * w
            if v > riba:
                v = max(h[j], riba)
            h[j] = v
    # Sniegas nesilaiko stačiais stulpais – perteklius nuslenka į šonus.
    a, b = max(1, c - 6), min(n, c + 7)
    for _ in range(2):
        for j in range(a, b):
            d = h[j] - h[j - 1]
            if d > 2.5:
                m = (d - 2.5) / 2
                h[j] -= m
                h[j - 1] += m
            elif d < -2.5:
                m = (-d - 2.5) / 2
                h[j - 1] -= m
                h[j] += m
    if profilis:
        for j in range(a - 1, b):
            riba = maks if sust and sust[j] else maks * profilis[j]
            if h[j] > riba:
                h[j] = riba
    if krastai:  # nuo lango kraštų sniegas nubyra – kraštai suapvalėja
        for j in range(min(4, n)):
            riba = (j + 1) * 1.5
            if h[j] > riba:
                h[j] = riba
            if h[n - 1 - j] > riba:
                h[n - 1 - j] = riba


def kopu_bangos(rnd, ilgiai):
    """Atsitiktinės „kopų“ bangos: (bangos ilgis px, fazė, amplitudė)."""
    return [(ilgis * rnd.uniform(0.8, 1.25), rnd.uniform(0, 2 * math.pi), amplitude) for ilgis, amplitude in ilgiai]


def kopu_profilis(n, bangos, poslinkis=0.0, kalneliai=False):
    """Kiekvieno stulpelio didžiausio sniego aukščio dalis (0,25–1): bangų suma per minkštą ribą
    (sigmoidę) – be plokščių ruožų. Vidurkis 0,625.
    kalneliai – ekrano apačios pusnims (jų buldozeriukai nevalo): atskiri kalneliai su žemais tarpais
    (0,08–1, vidurkis ~0,4), kad pusnys neužkloštų visos apačios (užduočių juostos, pranešimų srities)."""
    S = STULPELIS
    rez = []
    for c in range(n):
        x = c * S + poslinkis
        v = sum(a * math.sin(x / l + f) for l, f, a in bangos)
        if kalneliai:
            sg = 1.0 / (1.0 + math.exp(-6.0 * v))
            rez.append(0.08 + 0.92 * sg * sg)
        else:
            rez.append(0.25 + 0.75 / (1.0 + math.exp(-5.0 * v)))
    return rez


def atimti(intervalai, a, b):
    rez = []
    for x1, x2 in intervalai:
        if b <= x1 or a >= x2:
            rez.append((x1, x2))
            continue
        if a > x1:
            rez.append((x1, a))
        if b < x2:
            rez.append((b, x2))
    return rez


def sluoksnio_atkarpos(h, a, b, slenkstis):
    """Ištisinės stulpelių atkarpos, kuriose sniego yra bent tiek, kad jį verta piešti."""
    j = a
    while j < b:
        if h[j] < slenkstis:
            j += 1
            continue
        c1 = j
        while j < b and h[j] >= slenkstis:
            j += 1
        yield c1, j


# ---------------------------------------------------------------- pixel art fejerverkai
# Kiekviena spalva – 5 atspalviai: įkaitęs, ryškus, pagrindinis, tamsus, gęstantis.
FJ_PALETES = {
    "raudona": ("#fff0f0", "#ff5a5a", "#e8202c", "#9c1020", "#501018"),
    "oranžinė": ("#fff4dc", "#ffb048", "#ff7a14", "#b04c0a", "#5a2806"),
    "auksinė": ("#fffce4", "#ffe274", "#f8b800", "#a87000", "#5c3c04"),
    "geltona": ("#ffffec", "#fffa80", "#f0e428", "#a09c14", "#50500c"),
    "žalia": ("#ecffec", "#78ff78", "#24d444", "#10842c", "#084416"),
    "žydra": ("#ecffff", "#88f4ff", "#20ccf4", "#107c9c", "#08404e"),
    "mėlyna": ("#eef4ff", "#7898ff", "#2c58ec", "#1c3496", "#0e1a4c"),
    "violetinė": ("#f8ecff", "#d488ff", "#a844dc", "#6a2a8c", "#361648"),
    "rožinė": ("#ffecf6", "#ff98cc", "#ff44a4", "#ac2a6c", "#561636"),
    "sidabrinė": ("#ffffff", "#f2f4ff", "#c8d0e4", "#8a92a6", "#464a56"),
}
FJ_SPALVOS = tuple(k for k in FJ_PALETES if k not in ("auksinė", "sidabrinė"))
FJ_SIGNALAS = ("#ffffff", "#ff7050", "#ff2a10", "#b01808", "#580c04")
FJ_DUMAI = ("#a4acbc", "#8c94a4", "#727a8a", "#5a606e", "#444852")


class Kibirkstis:
    __slots__ = ("x", "y", "vx", "vy", "t", "gyv", "pal", "pal2", "oras", "trauka", "uodega", "dydis",
                 "mirks", "spragsi", "skyla", "zuvis", "blizga")

    def __init__(self, x, y, vx, vy, gyv, pal, oras=1.6, trauka=40.0, uodega=0, dydis=1, pal2=None,
                 mirks=False, spragsi=False, skyla=0.0, zuvis=False, blizga=False):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.t, self.gyv, self.pal, self.pal2 = 0.0, gyv, pal, pal2
        self.oras, self.trauka, self.uodega, self.dydis = oras, trauka, uodega, dydis
        self.mirks, self.spragsi, self.skyla, self.zuvis, self.blizga = mirks, spragsi, skyla, zuvis, blizga


class FjGrupe:
    """Viena raketa su savo sprogimu (ar fontanas, žvakė, signalinė raketa) – piešiama vienu stačiakampiu."""
    __slots__ = ("dalys", "eiga", "sena")

    def __init__(self):
        self.dalys, self.eiga, self.sena = [], None, None


def fj_sfera(n, rnd):
    """Rutulio paviršius, žiūrint iš šono (Fibonačio taškai) – pakraščiuose tankiau, kaip tikro sprogimo."""
    pasuk = rnd.uniform(0, 2 * math.pi)
    rez = []
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(max(0.0, 1 - z * z))
        a = i * 2.399963 + pasuk
        rez.append((r * math.cos(a), r * math.sin(a)))
    return rez


def fj_ziedas(n, rnd, posvyris=None, kampas=None):
    posvyris = rnd.uniform(0.2, 1.2) if posvyris is None else posvyris
    kampas = rnd.uniform(-0.6, 0.6) if kampas is None else kampas
    ca, sa, cp = math.cos(kampas), math.sin(kampas), math.cos(posvyris)
    rez = []
    for i in range(n):
        a = 2 * math.pi * i / n
        x, y = math.cos(a), math.sin(a) * cp
        rez.append((x * ca - y * sa, x * sa + y * ca))
    return rez


def fj_linija(a, b, n):
    return [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n)]


def fj_lauzte(taskai, n):
    """n taškų tolygiai išdėstytų uždaroje laužtėje."""
    ilgiai = [math.dist(taskai[i], taskai[(i + 1) % len(taskai)]) for i in range(len(taskai))]
    viso = sum(ilgiai)
    if viso <= 0:  # visi taškai sutampa – dabartiniuose šablonuose taip nebūna, tik apsauga
        return [tuple(taskai[0])] * n if taskai else []
    rez = []
    for i, ilgis in enumerate(ilgiai):
        k = max(1, round(n * ilgis / viso))
        rez += fj_linija(taskai[i], taskai[(i + 1) % len(taskai)], k)
    return rez


def fj_sirdele(n):
    rez = []
    for i in range(n):
        t = 2 * math.pi * i / n
        rez.append((16 * math.sin(t) ** 3 / 17,
                    -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) / 17 - 0.1))
    return rez


def fj_zvaigzde(n):
    v = [((1.0 if i % 2 == 0 else 0.42) * math.cos(-math.pi / 2 + i * math.pi / 5),
          (1.0 if i % 2 == 0 else 0.42) * math.sin(-math.pi / 2 + i * math.pi / 5)) for i in range(10)]
    return fj_lauzte(v, n)


def fj_sypsenele():
    rez = [(math.cos(2 * math.pi * i / 28), math.sin(2 * math.pi * i / 28)) for i in range(28)]
    for ax in (-0.36, 0.36):
        rez += [(ax, -0.32), (ax, -0.22), (ax + 0.07, -0.27), (ax - 0.07, -0.27)]
    rez += [(0.58 * math.cos(a), 0.58 * math.sin(a))
            for a in (math.radians(25 + 130 * i / 13) for i in range(14))]
    return rez


def fj_snaige():
    rez = [(0.0, 0.0)]
    for k in range(6):
        a = k * math.pi / 3 - math.pi / 2
        ca, sa = math.cos(a), math.sin(a)
        for i in range(1, 7):
            rez.append((ca * i / 6, sa * i / 6))
        for vieta, ilgis in ((0.5, 0.32), (0.78, 0.2)):
            for s in (-1, 1):
                b = a + s * math.radians(42)
                for j in (1, 2):
                    rez.append((ca * vieta + math.cos(b) * ilgis * j / 2, sa * vieta + math.sin(b) * ilgis * j / 2))
    return rez


def fj_eglute():
    rez = fj_lauzte([(0.0, -1.0), (0.72, 0.55), (-0.72, 0.55)], 40)
    rez += fj_linija((0.0, 0.55), (0.0, 0.9), 3)
    return rez


def fj_spirale(n):
    rez = []
    rankos = 3
    for k in range(rankos):
        for i in range(1, n // rankos + 1):
            r = i / (n // rankos)
            a = k * 2 * math.pi / rankos + r * 4.2
            rez.append((r * math.cos(a), r * math.sin(a)))
    return rez


def raketos_greitis(aukstis, G, C):
    """Pradinis greitis ir laikas iki viršūnės, kad raketa su oro pasipriešinimu C pakiltų į aukštį.
    Viršūnės aukštis: h(v) = v/C − G/C²·ln(1 + C·v/G); v randamas dalijant intervalą pusiau."""
    def h(v):
        return v / C - G / C ** 2 * math.log(1 + C * v / G)
    lo, hi = 0.0, math.sqrt(2 * G * aukstis) * 3
    for _ in range(40):
        vid = (lo + hi) / 2
        if h(vid) < aukstis:
            lo = vid
        else:
            hi = vid
    v = (lo + hi) / 2
    return v, math.log(1 + C * v / G) / C


class Fejerverkai:
    """Pixel art fejerverkų „variklis“: šou planas, raketos, sprogimai ir kibirkštys.
    Su GDI nesusijęs – piešimui kiekvienam kvadratėliui kviečia perduotą funkciją."""

    MAKS_DALIU = 2600

    def __init__(self, k, P, zeme=None, vejas=None, rnd=None):
        self.k, self.P = k, P
        self.zeme = zeme or (lambda x: None)   # sniego paviršiaus y ties x (arba None)
        self.vejas = vejas or (lambda: 0.0)    # vėjo greitis, px/s
        self.rnd = rnd or random.Random()
        self.grupes = []
        self.planas = []
        self.laikas = 0.0
        self.sritys = []
        self.daliu = 0
        self.didinimas = 1.0   # didžiajame šou sprogimai stambesni
        self.kalibras = 1.0    # šiuo metu sprogstančio sviedinio dydis (raketa) – didesnio ir raketa didesnė
        self.detales = False   # didžiajame šou – dūmų debesėliai po sprogimų
        self.pabaiga = 0.0     # kada baigsis dabartinis šou (šou laiku)

    @property
    def aktyvus(self):
        return bool(self.grupes or self.planas)

    def sustabdyti(self):
        senos = [g.sena for g in self.grupes if g.sena]
        self.grupes, self.planas = [], []
        self.didinimas, self.detales = 1.0, False
        self.daliu = 0  # kitaip nutraukus šou per finalą kitame trūktų dalelių (riba – daliu)
        return senos

    # ------------------------------------------------ kibirkštys

    def nauja(self, g, x, y, vx, vy, gyv, pal, **kw):
        if self.daliu >= self.MAKS_DALIU:
            return None
        p = Kibirkstis(x, y, vx, vy, gyv, pal, **kw)
        g.dalys.append(p)
        self.daliu += 1
        return p

    def spalva(self):
        return FJ_PALETES[self.rnd.choice(FJ_SPALVOS)]

    def is_formos(self, g, x, y, taskai, R, pal, oras, trauka, gyv, uodega=0, **kw):
        rnd = self.rnd
        for dx, dy in taskai:
            j = rnd.uniform(0.94, 1.06)
            self.nauja(g, x, y, dx * R * oras * j, dy * R * oras * j, gyv * rnd.uniform(0.85, 1.12), pal,
                       oras=oras, trauka=trauka, uodega=uodega, **kw)

    # ------------------------------------------------ sprogimai (23 rūšys)

    def s_bijunas(self, g, x, y):
        self.is_formos(g, x, y, fj_sfera(100, self.rnd), self.R(150), self.spalva(), 1.7, 40 * self.k, 1.6, 1)

    def s_chrizantema(self, g, x, y):
        self.is_formos(g, x, y, fj_sfera(80, self.rnd), self.R(165), self.spalva(), 1.5, 45 * self.k, 1.7, 4)

    def s_gluosnis(self, g, x, y):
        self.is_formos(g, x, y, fj_sfera(90, self.rnd), self.R(140), FJ_PALETES["auksinė"], 2.3, 75 * self.k,
                       3.4, 5)

    def s_palme(self, g, x, y):
        rnd = self.rnd
        n = rnd.randint(7, 10)
        for i in range(n):
            a = -math.pi / 2 + (i - (n - 1) / 2) * (2.4 / n) + rnd.uniform(-0.1, 0.1)
            R = self.R(150) * rnd.uniform(0.85, 1.1)
            self.nauja(g, x, y, math.cos(a) * R * 1.4, math.sin(a) * R * 1.4, 2.4, FJ_PALETES["auksinė"],
                       oras=1.4, trauka=95 * self.k, uodega=7, dydis=2)
        self.is_formos(g, x, y, fj_sfera(20, rnd), self.R(60), FJ_PALETES["žalia"], 2.0, 30 * self.k, 1.0)

    def s_ziedas(self, g, x, y):
        self.is_formos(g, x, y, fj_ziedas(50, self.rnd), self.R(150), self.spalva(), 1.9, 25 * self.k, 1.7, 1)

    def s_dvigubas_ziedas(self, g, x, y):
        rnd = self.rnd
        p, k = rnd.uniform(0.3, 1.0), rnd.uniform(-0.5, 0.5)
        a, b = rnd.sample(FJ_SPALVOS, 2)
        self.is_formos(g, x, y, fj_ziedas(46, rnd, p, k), self.R(165), FJ_PALETES[a], 1.9, 25 * self.k, 1.8, 1)
        self.is_formos(g, x, y, fj_ziedas(32, rnd, p, k + 1.57), self.R(100), FJ_PALETES[b], 1.9, 25 * self.k,
                       1.8, 1)

    def s_sirdele(self, g, x, y):
        pal = FJ_PALETES[self.rnd.choice(("raudona", "rožinė"))]
        self.is_formos(g, x, y, fj_sirdele(56), self.R(130), pal, 2.6, 18 * self.k, 2.0)

    def s_zvaigzde(self, g, x, y):
        self.is_formos(g, x, y, fj_zvaigzde(60), self.R(145), FJ_PALETES["auksinė"], 2.6, 18 * self.k,
                       2.0)

    def s_kryzmine(self, g, x, y):
        rnd = self.rnd
        pal = self.spalva()
        for dx, dy in fj_ziedas(6, rnd, 0.0, rnd.uniform(0, 1)):
            self.nauja(g, x, y, dx * self.R(110) * 1.6, dy * self.R(110) * 1.6, 0.75, pal, oras=1.6,
                       trauka=40 * self.k, uodega=3, skyla=0.7)

    def s_spragsiukai(self, g, x, y):
        self.is_formos(g, x, y, fj_sfera(55, self.rnd), self.R(130), FJ_PALETES["auksinė"], 1.8, 50 * self.k,
                       1.3, 2, spragsi=True)

    def s_mirksintis(self, g, x, y):
        self.is_formos(g, x, y, fj_sfera(84, self.rnd), self.R(140), FJ_PALETES["sidabrinė"], 1.8, 45 * self.k,
                       2.6, 0, mirks=True)

    def s_ivairiaspalvis(self, g, x, y):
        rnd = self.rnd
        R = self.R(155)
        for dx, dy in fj_sfera(100, rnd):
            self.nauja(g, x, y, dx * R * 1.7, dy * R * 1.7, rnd.uniform(1.4, 1.9), self.spalva(), oras=1.7,
                       trauka=40 * self.k, uodega=1)

    def s_spalva_keicia(self, g, x, y):
        a, b = self.rnd.sample(FJ_SPALVOS, 2)
        self.is_formos(g, x, y, fj_sfera(90, self.rnd), self.R(150), FJ_PALETES[a], 1.7, 40 * self.k, 2.0, 2,
                       pal2=FJ_PALETES[b])

    def s_sypsenele(self, g, x, y):
        self.is_formos(g, x, y, fj_sypsenele(), self.R(130), FJ_PALETES["geltona"], 2.6, 15 * self.k,
                       2.0)

    def s_snaige(self, g, x, y):
        pal = FJ_PALETES[self.rnd.choice(("žydra", "sidabrinė"))]
        self.is_formos(g, x, y, fj_snaige(), self.R(140), pal, 2.6, 15 * self.k, 2.1)

    def s_eglute(self, g, x, y):
        rnd = self.rnd
        self.is_formos(g, x, y, fj_eglute(), self.R(140), FJ_PALETES["žalia"], 2.6, 15 * self.k, 2.1)
        self.is_formos(g, x, y, [(0.0, -1.12)], self.R(140), FJ_PALETES["auksinė"], 2.6, 15 * self.k, 2.1,
                       dydis=2)
        for _ in range(9):  # lemputės eglutės viduje
            v = rnd.uniform(-0.75, 0.45)
            plotis = (v + 1.0) / 1.55 * 0.6
            self.is_formos(g, x, y, [(rnd.uniform(-plotis, plotis), v)], self.R(140),
                           FJ_PALETES[rnd.choice(("raudona", "auksinė", "mėlyna", "rožinė"))], 2.6, 15 * self.k,
                           2.1, mirks=rnd.random() < 0.5)

    def s_spirale(self, g, x, y):
        self.is_formos(g, x, y, fj_spirale(60), self.R(150), self.spalva(), 2.4, 20 * self.k, 1.9, 1)

    def s_saturnas(self, g, x, y):
        a, b = self.rnd.sample(FJ_SPALVOS, 2)
        self.is_formos(g, x, y, fj_sfera(40, self.rnd), self.R(70), FJ_PALETES[a], 2.0, 25 * self.k, 1.9)
        self.is_formos(g, x, y, fj_ziedas(44, self.rnd, 1.25, self.rnd.uniform(-0.4, 0.4)), self.R(160),
                       FJ_PALETES[b], 2.0, 25 * self.k, 1.9, 1)

    def s_krioklys(self, g, x, y):
        rnd = self.rnd
        for dx, dy in fj_sfera(60, rnd):
            R = self.R(100)
            self.nauja(g, x, y, dx * R * 1.3, (dy * 0.6 + 0.3) * R * 1.3, rnd.uniform(2.2, 2.8),
                       FJ_PALETES["sidabrinė"], oras=1.0, trauka=160 * self.k, uodega=5)

    def s_zuvytes(self, g, x, y):
        self.is_formos(g, x, y, fj_sfera(36, self.rnd), self.R(110), self.spalva(), 1.6, 30 * self.k, 2.2, 3,
                       zuvis=True)

    def s_jurginas(self, g, x, y):
        rnd = self.rnd
        spalvos = rnd.sample(FJ_SPALVOS, 3)
        for i, (dx, dy) in enumerate(fj_sfera(30, rnd)):
            a = math.atan2(dy, dx)
            pal = FJ_PALETES[spalvos[int((a + math.pi) / (2 * math.pi) * 3) % 3]]
            self.nauja(g, x, y, dx * self.R(150) * 1.7, dy * self.R(150) * 1.7, rnd.uniform(1.6, 2.0), pal,
                       oras=1.7, trauka=40 * self.k, uodega=2, dydis=2)

    def s_su_serdimi(self, g, x, y):
        a, b = self.rnd.sample(FJ_SPALVOS, 2)
        self.is_formos(g, x, y, fj_sfera(30, self.rnd), self.R(65), FJ_PALETES[a], 1.8, 40 * self.k, 1.5)
        self.is_formos(g, x, y, fj_sfera(80, self.rnd), self.R(160), FJ_PALETES[b], 1.7, 40 * self.k, 1.7, 1)

    def s_kamuras(self, g, x, y):
        pal = FJ_PALETES[self.rnd.choice(("auksinė", "sidabrinė"))]
        self.is_formos(g, x, y, fj_sfera(80, self.rnd), self.R(150), pal, 2.0, 55 * self.k, 3.2, 3, blizga=True)

    def R(self, r):
        return r * self.k * self.didinimas * self.kalibras * self.rnd.uniform(0.93, 1.07)

    # Kiek didelis kiekvienos rūšies sprogimas (didžiausias jo R) – pagal jį ir sviedinio kalibrą – raketos dydis
    SPROGIMO_DYDIS = {"s_chrizantema": 165, "s_dvigubas_ziedas": 165, "s_saturnas": 160, "s_su_serdimi": 160,
                      "s_ivairiaspalvis": 155, "s_zvaigzde": 145, "s_gluosnis": 140, "s_mirksintis": 140,
                      "s_snaige": 140, "s_eglute": 140, "s_sirdele": 130, "s_spragsiukai": 130,
                      "s_sypsenele": 130, "s_kryzmine": 110, "s_zuvytes": 110, "s_krioklys": 100}

    # ------------------------------------------------ kibirkščių fizika

    def zingsnis(self, dt):
        """Grąžina stačiakampius, kuriuos reikia atstatyti (pasibaigusių grupių vietos)."""
        self.laikas += dt
        while self.planas and self.planas[0][0] <= self.laikas:
            _, veiksmas = self.planas.pop(0)
            self.vykdyti(veiksmas)
        rnd = self.rnd
        exp, cos, sin, random_ = math.exp, math.cos, math.sin, rnd.random
        vejas = self.vejas() * 0.6  # aukštai vėjas kiek stipresnis nei prie žemės
        senos = []
        likusios = []
        daliu = 0
        maks = self.MAKS_DALIU - self.daliu  # antrinėms kibirkštims irgi taikoma bendra riba
        for g in self.grupes:
            if g.eiga is not None:
                try:
                    g.eiga.send(dt)
                except StopIteration:
                    g.eiga = None
            naujos = []
            gyvos = []
            for p in g.dalys:
                p.t += dt
                if p.t >= p.gyv:
                    if p.spragsi and len(naujos) < maks:
                        for _ in range(3):
                            a = rnd.uniform(0, 2 * math.pi)
                            v = rnd.uniform(40, 90) * self.k
                            naujos.append(Kibirkstis(p.x, p.y, cos(a) * v, sin(a) * v, rnd.uniform(0.12, 0.3),
                                                     FJ_PALETES["sidabrinė"], oras=3.0, trauka=0.0, mirks=True))
                    continue
                if p.skyla and p.t >= p.skyla:
                    if len(naujos) >= maks:
                        continue
                    a0 = rnd.uniform(0, math.pi / 2)
                    v = 120 * self.k
                    for j in range(4):
                        a = a0 + j * math.pi / 2
                        naujos.append(Kibirkstis(p.x, p.y, cos(a) * v + p.vx * 0.3, sin(a) * v + p.vy * 0.3,
                                                 rnd.uniform(1.1, 1.4), p.pal, oras=1.8, trauka=45 * self.k,
                                                 uodega=2))
                    continue
                # oro pasipriešinimas veikia greitį oro atžvilgiu – kibirkštys palaipsniui „pagauna“ vėją
                f = exp(-p.oras * dt)
                p.vx = vejas + (p.vx - vejas) * f
                p.vy = p.vy * f + p.trauka * dt
                if p.zuvis:
                    a = rnd.uniform(-7, 7) * dt
                    ca, sa = cos(a), sin(a)
                    p.vx, p.vy = p.vx * ca - p.vy * sa, p.vx * sa + p.vy * ca
                p.x += p.vx * dt
                p.y += p.vy * dt
                if p.blizga and len(naujos) < maks and random_() < 5 * dt:
                    naujos.append(Kibirkstis(p.x, p.y, 0.0, 0.0, rnd.uniform(0.25, 0.45), FJ_PALETES["sidabrinė"],
                                             oras=2.0, trauka=30 * self.k, mirks=True))
                gyvos.append(p)
            maks -= len(naujos)
            gyvos += naujos
            g.dalys = gyvos
            daliu += len(gyvos)
            if gyvos or g.eiga is not None:
                likusios.append(g)
            elif g.sena:
                senos.append(g.sena)
        self.grupes = likusios
        self.daliu = daliu
        return senos

    # ------------------------------------------------ piešimas

    def piesti_grupe(self, g, kvadratas, rnd=None):
        """Kiekvieną kibirkštį piešia kvadratėliu (pixel art). Grąžina (l, t, r, b) arba None."""
        P = self.P
        random_ = (rnd or self.rnd).random
        l = t = 10 ** 9
        r = b = -10 ** 9
        for p in g.dalys:
            u = p.t / p.gyv
            if p.mirks and int(p.t * 22) & 1:
                continue
            if u > 0.72 and random_() < (u - 0.72) * 1.8:  # gęsdamos kibirkštys mirga
                continue
            pal = p.pal2 if p.pal2 is not None and u > 0.5 else p.pal
            i = 0 if u < 0.07 else 1 if u < 0.45 else 2 if u < 0.78 else 3 if u < 0.93 else 4
            d = P * p.dydis
            x = int(p.x) - d // 2
            y = int(p.y) - d // 2
            kvadratas(x, y, d, pal[i])
            if x < l:
                l = x
            if y < t:
                t = y
            if x + d > r:
                r = x + d
            if y + d > b:
                b = y + d
            if p.uodega:
                # uodegos kvadratėliai ne tankiau nei kas P taškų – lėtėjančios kibirkšties uodega trumpėja,
                # o ne piešiama daug kartų toje pačioje vietoje
                greitis = abs(p.vx) + abs(p.vy)
                if greitis * 0.022 >= P:
                    kiek, tarpas = p.uodega, 0.022
                else:
                    kiek = int(greitis * 0.022 * p.uodega / P)
                    tarpas = P / greitis if kiek else 0.0
                h = P // 2
                for j in range(1, kiek + 1):
                    s = tarpas * j
                    tx = int(p.x - p.vx * s) - h
                    ty = int(p.y - p.vy * s) - h
                    kvadratas(tx, ty, P, pal[min(4, i + 1 + j // 3)])
                    if tx < l:
                        l = tx
                    if ty < t:
                        t = ty
                    if tx + P > r:
                        r = tx + P
                    if ty + P > b:
                        b = ty + P
        return (l, t, r, b) if r > l else None

    # ------------------------------------------------ šou planas ir paleidimai

    SPROGIMAI = (
        ("Bijūnas", "s_bijunas"), ("Chrizantema", "s_chrizantema"), ("Gluosnis", "s_gluosnis"),
        ("Palmė", "s_palme"), ("Žiedas", "s_ziedas"), ("Dvigubas žiedas", "s_dvigubas_ziedas"),
        ("Širdelė", "s_sirdele"), ("Žvaigždė", "s_zvaigzde"), ("Kryžminė", "s_kryzmine"),
        ("Spragsiukai", "s_spragsiukai"), ("Mirksintis", "s_mirksintis"), ("Įvairiaspalvis", "s_ivairiaspalvis"),
        ("Spalvą keičiantis", "s_spalva_keicia"), ("Šypsenėlė", "s_sypsenele"), ("Snaigė", "s_snaige"),
        ("Eglutė", "s_eglute"), ("Spiralė", "s_spirale"), ("Saturnas", "s_saturnas"),
        ("Krioklys", "s_krioklys"), ("Žuvytės", "s_zuvytes"), ("Jurginas", "s_jurginas"),
        ("Su šerdimi", "s_su_serdimi"), ("Kamuras", "s_kamuras"),
    )
    YPATINGI = (("Signalinė raketa", "signalas"), ("Romėniška žvakė", "zvake"), ("Fontanas", "fontanas"))
    VISI = SPROGIMAI + YPATINGI

    def pradeti(self, trukme, sritys):
        """Šou: raketos kas 0,8–2 s, kartais salvės, viena signalinė raketa, pabaigoje – finalas."""
        rnd = self.rnd
        self.sritys = [s for s in sritys if s[2] - s[0] > 200 and s[3] - s[1] > 200] or sritys
        self.laikas = 0.0
        self.didinimas, self.detales = 1.0, False
        planas = []
        kalade = []

        def kitas():
            if not kalade:
                kalade.extend(rnd.sample(range(len(self.SPROGIMAI)), len(self.SPROGIMAI)))
                kalade.insert(rnd.randint(0, 6), "zvake")
                kalade.insert(rnd.randint(4, 14), "fontanas")
            return kalade.pop(0)

        t = 0.0
        signalas = rnd.uniform(0, max(0.0, trukme - 14)) if rnd.random() < 0.5 else 0.0
        planas.append((signalas, ("signalas",)))
        if signalas == 0.0:
            t = 1.5
        while t < trukme - 4:
            tipas = kitas()
            if isinstance(tipas, str):
                planas.append((t, (tipas,)))
            elif rnd.random() < 0.2:  # salvė – tas pats sprogimas 2–3 vietose
                for j in range(rnd.randint(2, 3)):
                    planas.append((t + j * 0.12, ("raketa", tipas)))
            else:
                planas.append((t, ("raketa", tipas)))
            t += rnd.uniform(0.8, 2.0)
        pradzia = max(t, trukme - 4)
        for j in range(rnd.randint(7, 10)):
            planas.append((pradzia + j * rnd.uniform(0.25, 0.45), ("raketa", rnd.randrange(len(self.SPROGIMAI)))))
        planas.sort(key=lambda v: v[0])
        self.planas = planas
        self.pabaiga = planas[-1][0] + 4 if planas else 0.0

    def nr(self, vardas):
        return next(i for i, (v, _) in enumerate(self.SPROGIMAI) if v == vardas)

    def pradeti_didiji(self, sritys):
        """Slaptas didysis šou (~2 min): veiksmai su bangomis, formų paradu, aukso lietumi ir finalu."""
        rnd = self.rnd
        self.sritys = [s for s in sritys if s[2] - s[0] > 200 and s[3] - s[1] > 200] or sritys
        self.laikas = 0.0
        self.didinimas, self.detales = 1.2, True
        p = []
        nr = self.nr
        kalade = []

        def atsitiktinis():
            if not kalade:
                kalade.extend(rnd.sample(range(len(self.SPROGIMAI)), len(self.SPROGIMAI)))
            return kalade.pop(0)

        def tankiai(nuo, iki, tarpas, salves=0.3):
            t = nuo
            while t < iki:
                tipas = atsitiktinis()
                if rnd.random() < salves:
                    for j in range(rnd.randint(2, 4)):
                        p.append((t + j * 0.1, ("raketa", tipas, None, None)))
                else:
                    p.append((t, ("raketa", tipas, None, None)))
                t += rnd.uniform(*tarpas)

        def banga(nuo, vardas, kiek, tarpas, atgal=False, aukstis=0.3):
            for j in range(kiek):
                frac = 0.08 + 0.84 * j / (kiek - 1)
                p.append((nuo + j * tarpas, ("raketa", nr(vardas), 1 - frac if atgal else frac, aukstis)))

        # 1. Atidarymas: trys signalinės raketos ir fontanų eilė
        for j, frac in enumerate((0.2, 0.5, 0.8)):
            p.append((j * 0.7, ("signalas", frac)))
        for j, frac in enumerate((0.08, 0.3, 0.7, 0.92)):
            p.append((1.5 + j * 0.4, ("fontanas", frac)))
        banga(7.0, "Bijūnas", 3, 0.25, aukstis=0.25)
        # 2. Tankus mišinys
        tankiai(9, 29, (0.35, 0.8))
        # 3. Formų paradas iš kairės į dešinę
        for j, vardas in enumerate(("Širdelė", "Žvaigždė", "Snaigė", "Šypsenėlė", "Eglutė", "Širdelė", "Žvaigždė",
                                    "Snaigė", "Eglutė")):
            p.append((30 + j * 1.4, ("raketa", nr(vardas), 0.1 + 0.8 * j / 8, rnd.uniform(0.22, 0.32))))
        # 4. Aukso kaskada ir romėniškos žvakės kraštuose
        for j in range(15):
            vardas = ("Palmė", "Gluosnis", "Kamuras")[j % 3]
            p.append((43 + j * 0.9, ("raketa", nr(vardas), None, None)))
        for t in (43, 50):
            p.append((t, ("zvake", 0.04)))
            p.append((t + 0.3, ("zvake", 0.96)))
        # 5. Bangos
        banga(58, "Žiedas", 9, 0.18)
        banga(62.5, "Dvigubas žiedas", 7, 0.22, atgal=True, aukstis=0.22)
        banga(66.5, "Kryžminė", 7, 0.2, aukstis=0.35)
        # 6. Dar tankesnis mišinys su signaline raketa ir fontanais
        tankiai(70, 91, (0.3, 0.7), 0.35)
        p.append((72, ("signalas", 0.85)))
        for j, frac in enumerate((0.1, 0.3, 0.5, 0.7, 0.9)):
            p.append((82 + j * 0.3, ("fontanas", frac)))
        # 7. Spalvų lietus ir kriokliai
        lietus = ("Įvairiaspalvis", "Spalvą keičiantis", "Mirksintis", "Spragsiukai", "Žuvytės", "Jurginas")
        for j in range(22):
            p.append((92 + j * 0.5, ("raketa", nr(lietus[j % len(lietus)]), None, None)))
        banga(98, "Krioklys", 6, 0.3, aukstis=0.2)
        banga(101, "Su šerdimi", 6, 0.25, atgal=True)
        # 8. Finalas
        t = 104.0
        while t < 112:
            tipas = atsitiktinis()
            for j in range(rnd.choice((1, 2, 2, 4))):
                p.append((t + j * 0.08, ("raketa", tipas, None, None)))
            t += rnd.uniform(0.15, 0.3)
        p.append((112.5, ("raketa", nr("Kamuras"), 0.5, 0.22)))
        p.append((114.0, ("raketa", nr("Kamuras"), 0.22, 0.25)))
        p.append((114.0, ("raketa", nr("Kamuras"), 0.78, 0.25)))
        for j, frac in enumerate((0.3, 0.5, 0.7)):
            p.append((116.5 + j * 0.15, ("raketa", nr("Mirksintis"), frac, 0.3)))
        p.sort(key=lambda v: v[0])
        self.planas = p
        self.pabaiga = p[-1][0] + 5

    def vieta(self, frac=None):
        """Paleidimo vieta: atsitiktinė, arba frac (0–1) – vieta per visų ekranų plotį iš kairės į dešinę."""
        rnd = self.rnd
        if frac is None:
            l, t, r, b = rnd.choices(self.sritys, weights=[s[2] - s[0] for s in self.sritys])[0]
            x = rnd.uniform(l + (r - l) * 0.1, r - (r - l) * 0.1)
        else:
            sritys = sorted(self.sritys)
            liko = frac * sum(s[2] - s[0] for s in sritys)
            for l, t, r, b in sritys:
                if liko <= r - l:
                    break
                liko -= r - l
            x = min(r - (r - l) * 0.04, max(l + (r - l) * 0.04, l + liko))
        zeme = self.zeme(x)
        y0 = zeme if zeme is not None and t < zeme <= b else b
        return x, y0, (l, t, r, b)

    def vykdyti(self, veiksmas):
        g = FjGrupe()
        rusis = veiksmas[0]
        rnd = self.rnd
        if rusis == "raketa":
            tipas = veiksmas[1]
            frac = veiksmas[2] if len(veiksmas) > 2 else None
            aukstis = veiksmas[3] if len(veiksmas) > 3 else None
            x, y0, (l, t, r, b) = self.vieta(frac)
            xt = x + (rnd.uniform(-0.06, 0.06) if frac is None else rnd.uniform(-0.01, 0.01)) * (r - l)
            yt = t + (b - t) * (rnd.uniform(0.12, 0.42) if aukstis is None else aukstis + rnd.uniform(-0.02, 0.02))
            # retkarčiais (tik atsitiktinėse vietose, ne didžiojo šou rikiuotėse) raketa sprogsta vos pakilusi
            g.eiga = self.raketa(g, x, y0, xt, yt, self.SPROGIMAI[tipas][1],
                                 ankstyva=frac is None and rnd.random() < 0.12)
        else:
            x, y0, (l, t, r, b) = self.vieta(veiksmas[1] if len(veiksmas) > 1 else None)
            if rusis == "signalas":
                g.eiga = self.signalas(g, x, y0, t + (b - t) * rnd.uniform(0.3, 0.45))
            elif rusis == "zvake":
                g.eiga = self.zvake(g, x, y0)
            else:
                g.eiga = self.fontanas(g, x, y0)
        next(g.eiga)
        self.grupes.append(g)

    def paleisti_viena(self, indeksas, x, y0, xt, yt):
        """Peržiūrai: vienas konkretus fejerverkas."""
        g = FjGrupe()
        vardas = self.VISI[indeksas][1]
        if vardas == "signalas":
            g.eiga = self.signalas(g, x, y0, yt)
        elif vardas == "zvake":
            g.eiga = self.zvake(g, x, y0)
        elif vardas == "fontanas":
            g.eiga = self.fontanas(g, x, y0)
        else:
            g.eiga = self.raketa(g, x, y0, xt, yt, vardas)
        next(g.eiga)
        self.grupes.append(g)

    # ------------------------------------------------ eigos (generatoriai; kiekvieną kadrą gauna dt)

    def raketa(self, g, x0, y0, xt, yt, sprogimas, ankstyva=False):
        """Raketa skrenda balistiškai: paleidžiama tokiu greičiu, kad viršūnė būtų norimame aukštyje, ją lėtina
        sunkis ir oras, neša vėjas, ji šiek tiek blaškosi. Sprogsta, kai sudega degiklis – paprastai prie viršūnės,
        o „ankstyva“ – vos pakilusi. Sprogimas paveldi dalį raketos greičio.
        Kalibras: sviediniai būna mažesni ir didesni – didesnio ir sprogimas didesnis, ir kylanti raketa
        stambesnė (didesnė galvutė, tankesnis ir ilgesnis šleifas); mažo – plona, trumpu šleifu."""
        rnd = self.rnd
        kalibras = rnd.uniform(0.75, 1.3)
        dyd = kalibras * self.didinimas * self.SPROGIMO_DYDIS.get(sprogimas, 150) / 150  # raketos dydis
        G, C = 480 * self.k, 0.2  # sunkis ir oro pasipriešinimas
        # Į šonus raketa pasiduoda vėjui stipriau (CX) – kitaip per 1–2 s skrydį nunešdavo vos 5–10 taškų
        # ir gūsio nesimatydavo. Ramiu oru vis tiek pataiko į tikslą: vx skaičiuojamas su tuo pačiu CX.
        CX, VEJO_DALIS = 0.9, 0.8
        v0, T = raketos_greitis(max(40 * self.k, y0 - yt), G, C)  # su oru – kad tikrai pakiltų iki tikslo
        vy = -v0
        vx = (xt - x0) * CX / (1 - math.exp(-CX * T))
        degiklis = T * (rnd.uniform(0.25, 0.5) if ankstyva else rnd.uniform(0.96, 1.0))
        blaskymas, faze = rnd.uniform(6, 16) * self.k, rnd.uniform(0, 2 * math.pi)
        galva = self.nauja(g, x0, y0, 0.0, 0.0, degiklis + 1, FJ_PALETES["auksinė"], oras=0.0, trauka=0.0,
                           dydis=2 if dyd >= 1.12 else 1)
        t = 0.0
        x, y = x0, y0
        dt = yield
        while t < degiklis:
            t += dt
            px, py = x, y
            w = self.vejas() * VEJO_DALIS
            vx = w + (vx - w) * math.exp(-CX * dt)
            vy = vy * math.exp(-C * dt) + G * dt
            x += (vx + math.sin(t * 11 + faze) * blaskymas) * dt
            y += vy * dt
            if galva is not None:
                galva.x, galva.y, galva.t = x, y, 0.3 if int(t * 30) & 1 else 0.0
            # šleifas tolygiai per visą kadro nuskridtą atkarpą – kitaip greita raketa palieka tik taškus
            kiek = max(2, int(math.hypot(x - px, y - py) / max(1, self.P) * min(1.6, dyd)))
            for j in range(kiek):
                v = rnd.random()
                self.nauja(g, px + (x - px) * v + rnd.uniform(-1, 1) * dyd, py + (y - py) * v,
                           vx * 0.15 + rnd.uniform(-15, 15) * self.k * dyd, rnd.uniform(10, 40) * self.k,
                           rnd.uniform(0.15, 0.4) * dyd, FJ_PALETES["auksinė"], oras=2.0, trauka=60 * self.k)
            dt = yield
        if galva is not None:
            galva.gyv = 0.0
        xt, yt = x, y
        pries = len(g.dalys)
        self.kalibras = kalibras
        try:
            getattr(self, sprogimas)(g, xt, yt)
        finally:
            self.kalibras = 1.0
        for p in g.dalys[pries:]:  # sprogimas skrenda toliau ta pačia kryptimi kaip raketa
            p.vx += vx * 0.6
            p.vy += vy * 0.6
        # blyksnis sprogimo vietoje
        for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
            self.nauja(g, xt + dx * self.P * 2, yt + dy * self.P * 2, 0.0, 0.0, 0.09, FJ_PALETES["sidabrinė"],
                       oras=0.0, trauka=0.0, dydis=2)
        if self.detales:  # dūmų debesėlis, kurį lėtai nuneša vėjas
            for _ in range(8):
                self.nauja(g, xt + rnd.uniform(-20, 20) * self.k, yt + rnd.uniform(-20, 20) * self.k,
                           rnd.uniform(-6, 6) * self.k, rnd.uniform(-4, 4) * self.k, rnd.uniform(2.5, 4.0),
                           FJ_DUMAI[1:] + FJ_DUMAI[-1:], oras=1.0, trauka=-2 * self.k)

    def signalas(self, g, x0, y0, yt):
        """Lėtai kylanti signalinė raketa: ryški raudona liepsna, dūmų šleifas, viršuje lėtai leidžiasi."""
        rnd = self.rnd
        galva = self.nauja(g, x0, y0, 0.0, 0.0, 1e9, FJ_SIGNALAS, oras=0.0, trauka=0.0, dydis=3)
        x, y, t = x0, y0, 0.0
        greitis = rnd.uniform(55, 70) * self.k
        dt = yield
        leidziasi = 0.0
        while True:
            t += dt
            if y > yt and not leidziasi:
                y -= greitis * dt
                x += math.sin(t * 2.3) * 6 * self.k * dt
            else:
                leidziasi += dt
                if leidziasi > 5.0:
                    break
                y += 16 * self.k * dt
                x += (math.sin(t * 1.4) * 10 * self.k + self.vejas() * 0.15) * dt
            if galva is not None:
                gesta = leidziasi > 4.0
                galva.x, galva.y = x, y
                galva.t = rnd.choice((0.0, 0.2, 0.5)) if not gesta else rnd.choice((0.5, 0.75, 0.85))
                galva.gyv = 1.0
            if rnd.random() < 20 * dt:
                self.nauja(g, x + rnd.uniform(-2, 2) * self.k, y + 3 * self.k, rnd.uniform(-8, 8) * self.k,
                           rnd.uniform(-6, 4) * self.k, rnd.uniform(1.6, 2.6), FJ_DUMAI, oras=1.5,
                           trauka=-4 * self.k)
            if rnd.random() < 22 * dt:
                self.nauja(g, x, y, rnd.uniform(-25, 25) * self.k, rnd.uniform(0, 30) * self.k,
                           rnd.uniform(0.4, 0.8), FJ_SIGNALAS, oras=1.2, trauka=140 * self.k)
            dt = yield
        if galva is not None:
            galva.gyv = 0.0

    def zvake(self, g, x, y0):
        """Romėniška žvakė: iš vienos vietos vienas po kito iššauna 5–7 spalvoti kamuoliukai."""
        rnd = self.rnd
        dt = yield
        for _ in range(rnd.randint(5, 7)):
            pal = self.spalva()
            self.nauja(g, x, y0, rnd.uniform(-30, 30) * self.k, -rnd.uniform(380, 480) * self.k, rnd.uniform(1.2, 1.5),
                       pal, oras=0.5, trauka=230 * self.k, uodega=4, dydis=2)
            for _ in range(6):
                self.nauja(g, x, y0, rnd.uniform(-40, 40) * self.k, -rnd.uniform(20, 70) * self.k,
                           rnd.uniform(0.2, 0.4), FJ_PALETES["auksinė"], oras=2.0, trauka=80 * self.k)
            laukti = rnd.uniform(0.4, 0.6)
            while laukti > 0:
                laukti -= dt
                dt = yield

    def fontanas(self, g, x, y0):
        """Fontanas ant sniego: ~4 s purškia auksines ir sidabrines kibirkštis."""
        rnd = self.rnd
        t = 0.0
        pal = FJ_PALETES[rnd.choice(("auksinė", "sidabrinė"))]
        dt = yield
        while t < 4.5:
            t += dt
            for _ in range(int(70 * dt) + (rnd.random() < (70 * dt) % 1)):
                self.nauja(g, x, y0, rnd.uniform(-55, 55) * self.k, -rnd.uniform(240, 360) * self.k,
                           rnd.uniform(0.8, 1.2), pal, oras=0.8, trauka=380 * self.k, uodega=1)
            dt = yield


def sujungti_staciakampius(sar):
    """Persidengiančius stačiakampius sujungia, jei bendras plotas ne didesnis už jų plotų sumą –
    kad ta pati sritis nebūtų kopijuojama kelis kartus."""
    rez = []
    for l, t, r, b in sar:
        i = 0
        while i < len(rez):
            ql, qt, qr, qb = rez[i]
            if l < qr and ql < r and t < qb and qt < b:
                nl, nt, nr, nb = min(l, ql), min(t, qt), max(r, qr), max(b, qb)
                if (nr - nl) * (nb - nt) <= (r - l) * (b - t) + (qr - ql) * (qb - qt):
                    l, t, r, b = nl, nt, nr, nb
                    rez.pop(i)
                    i = 0
                    continue
            i += 1
        rez.append((l, t, r, b))
    return rez


class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + \
               [(v, ctypes.c_size_t) for v in ("PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                                               "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage",
                                               "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]


class _ENERGIJOS_RIBOJIMAS(ctypes.Structure):
    _fields_ = [("Version", wintypes.ULONG), ("ControlMask", wintypes.ULONG), ("StateMask", wintypes.ULONG)]


def isjungti_energijos_ribojima():
    """Windows 11 (ypač nešiojamuose) foniniams procesams be aktyvaus lango įjungia „efektyvumo režimą“
    (EcoQoS): procesorius lėtesnis, o 1 ms laikmačio prašymas (timeBeginPeriod) ignoruojamas – kadrai
    tada vėluoja nevienodai. Perdanga visada fone, todėl šis ribojimas šiam procesui išjungiamas
    (SetProcessInformation, ProcessPowerThrottling). True – pavyko; senesniame Windows – False."""
    try:
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.GetCurrentProcess.restype = wintypes.HANDLE
        k32.SetProcessInformation.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        st = _ENERGIJOS_RIBOJIMAS(1, 0x1 | 0x4, 0)  # EXECUTION_SPEED | IGNORE_TIMER_RESOLUTION – abu išjungti
        if k32.SetProcessInformation(k32.GetCurrentProcess(), 4, ctypes.byref(st), ctypes.sizeof(st)):
            return True
        st = _ENERGIJOS_RIBOJIMAS(1, 0x1, 0)  # Windows 10 nežino IGNORE_TIMER_RESOLUTION
        return bool(k32.SetProcessInformation(k32.GetCurrentProcess(), 4, ctypes.byref(st), ctypes.sizeof(st)))
    except Exception:
        return False


def mmcss_ijungti():
    """Windows multimedijos planuoklis (MMCSS, užduotis „Games“): gijai, kuri turi spėti iki ekrano atnaujinimo,
    Windows teikia pirmenybę – kaip vaizdo grotuvams ir žaidimams. Be jo nešiojamuose kartais kadras pažadinamas
    80–100 ms per vėlai, nors programa tuo metu nieko nedaro (diagnostika rodė: „gija dirbo 0 ms“). MMCSS pats
    palieka kitiems procesams ≥ 20 % procesoriaus, tad sistema neužstringa. Grąžina rankenėlę arba None."""
    try:
        avrt = ctypes.WinDLL("avrt", use_last_error=True)
        avrt.AvSetMmThreadCharacteristicsW.restype = wintypes.HANDLE
        avrt.AvSetMmThreadCharacteristicsW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(wintypes.DWORD)]
        indeksas = wintypes.DWORD(0)
        h = avrt.AvSetMmThreadCharacteristicsW("Games", ctypes.byref(indeksas))
        return h or None
    except Exception:
        return None


def mmcss_isjungti(h):
    try:
        if h:
            avrt = ctypes.WinDLL("avrt")
            avrt.AvRevertMmThreadCharacteristics.argtypes = [wintypes.HANDLE]
            avrt.AvRevertMmThreadCharacteristics(h)
    except Exception:
        pass


class _MAITINIMAS(ctypes.Structure):
    _fields_ = [("ACLineStatus", ctypes.c_ubyte), ("BatteryFlag", ctypes.c_ubyte), ("BatteryLifePercent", ctypes.c_ubyte),
                ("SystemStatusFlag", ctypes.c_ubyte), ("BatteryLifeTime", wintypes.DWORD),
                ("BatteryFullLifeTime", wintypes.DWORD)]


def maitinimo_busena():
    """„tinklas“ / „baterija 63 %“ (+ „taupymas“, jei įjungtas energijos taupymas) – nešiojamame tai keičia greitį."""
    try:
        m = _MAITINIMAS()
        if not ctypes.WinDLL("kernel32").GetSystemPowerStatus(ctypes.byref(m)):
            return "?"
        tekstas = "tinklas" if m.ACLineStatus == 1 else \
            f"baterija {m.BatteryLifePercent} %" if m.BatteryLifePercent <= 100 else "baterija"
        return tekstas + (", taupymas" if m.SystemStatusFlag & 1 else "")
    except Exception:
        return "?"


def ekrano_daznis():
    """Pagrindinio ekrano atnaujinimo dažnis, Hz (0 – nežinomas)."""
    try:
        u32, g32 = ctypes.WinDLL("user32"), ctypes.WinDLL("gdi32")
        # be argtypes 64 bitų HDC būtų perduotas kaip 32 bitų int – kartais klaida, ir rodydavo „0 Hz“
        u32.GetDC.argtypes, u32.GetDC.restype = [wintypes.HWND], wintypes.HDC
        u32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
        g32.GetDeviceCaps.argtypes, g32.GetDeviceCaps.restype = [wintypes.HDC, ctypes.c_int], ctypes.c_int
        dc = u32.GetDC(None)
        try:
            return int(g32.GetDeviceCaps(dc, 116))  # VREFRESH
        finally:
            u32.ReleaseDC(None, dc)
    except Exception:
        return 0


class _SANTYKIS(ctypes.Structure):
    _fields_ = [("skaitiklis", ctypes.c_uint32), ("vardiklis", ctypes.c_uint32)]


_DWM_LAIKO_LAUKAI = [("cbSize", ctypes.c_uint32), ("rateRefresh", _SANTYKIS), ("qpcRefreshPeriod", ctypes.c_uint64),
                     ("rateCompose", _SANTYKIS), ("qpcVBlank", ctypes.c_uint64), ("cRefresh", ctypes.c_uint64),
                     ("cDXRefresh", ctypes.c_uint32), ("qpcCompose", ctypes.c_uint64), ("cFrame", ctypes.c_uint64),
                     ("cDXPresent", ctypes.c_uint32), ("cRefreshFrame", ctypes.c_uint64),
                     ("cFrameSubmitted", ctypes.c_uint64), ("cDXPresentSubmitted", ctypes.c_uint32),
                     ("cFrameConfirmed", ctypes.c_uint64), ("cDXPresentConfirmed", ctypes.c_uint32),
                     ("cRefreshConfirmed", ctypes.c_uint64), ("cDXRefreshConfirmed", ctypes.c_uint32),
                     ("cFramesLate", ctypes.c_uint64), ("cFramesOutstanding", ctypes.c_uint32)] + \
    [(v, ctypes.c_uint64) for v in (
        "cFrameDisplayed", "qpcFrameDisplayed", "cRefreshFrameDisplayed", "cFrameComplete", "qpcFrameComplete",
        "cFramePending", "qpcFramePending", "cFramesDisplayed", "cFramesComplete", "cFramesPending", "cFramesAvailable",
        "cFramesDropped", "cFramesMissed", "cRefreshNextDisplayed", "cRefreshNextPresented", "cRefreshesDisplayed",
        "cRefreshesPresented", "cRefreshStarted", "cPixelsReceived", "cPixelsDrawn", "cBuffersEmpty")]


class _DWM_LAIKAS_1(ctypes.Structure):  # dwmapi.h – #pragma pack(1): 292 baitai
    _pack_ = 1
    _fields_ = _DWM_LAIKO_LAUKAI


class _DWM_LAIKAS_8(ctypes.Structure):  # jei kada nors būtų be pack(1) – bandoma ir taip
    _fields_ = _DWM_LAIKO_LAUKAI


class EkranoRitmas:
    """Ekrano atnaujinimo ritmas iš Windows (DWM): periodas ir paskutinio atnaujinimo (vblank) laikas
    time.perf_counter() skalėje. Nepavykus – None, ir kadrai planuojami kaip anksčiau (pagal laikmatį)."""

    def __init__(self):
        self.veikia = None
        try:
            self.dwm = ctypes.WinDLL("dwmapi")
            self.dwm.DwmGetCompositionTimingInfo.argtypes = [wintypes.HWND, ctypes.c_void_p]
            self.dwm.DwmGetCompositionTimingInfo.restype = ctypes.c_long
            self.k32 = ctypes.WinDLL("kernel32")
            self.k32.QueryPerformanceCounter.argtypes = [ctypes.POINTER(ctypes.c_int64)]
            self.k32.QueryPerformanceFrequency.argtypes = [ctypes.POINTER(ctypes.c_int64)]
            f = ctypes.c_int64()
            self.k32.QueryPerformanceFrequency(ctypes.byref(f))
            self.daznis = f.value
            self.struktura = None
            for kl in (_DWM_LAIKAS_1, _DWM_LAIKAS_8):
                self.struktura = kl
                if self.gauti() is not None:
                    self.veikia = True
                    return
            self.veikia = False
        except Exception:
            self.veikia = False

    def gauti(self):
        """(periodas s, paskutinis vblank perf_counter skalėje) arba None."""
        try:
            info = self.struktura()
            info.cbSize = ctypes.sizeof(info)
            if self.dwm.DwmGetCompositionTimingInfo(None, ctypes.byref(info)) != 0 or not self.daznis:
                return None
            periodas = info.qpcRefreshPeriod / self.daznis
            if not 0.002 < periodas < 0.1:  # ekranas išjungtas, nuotolinis darbalaukis ir pan.
                return None
            q = ctypes.c_int64()
            self.k32.QueryPerformanceCounter(ctypes.byref(q))
            dabar = time.perf_counter()
            return periodas, dabar - (q.value - info.qpcVBlank) / self.daznis
        except Exception:
            return None


def proceso_busena():
    """(atmintis MB, GDI objektų, USER objektų, procesoriaus laikas s) – nutekėjimams ir apkrovai matyti."""
    try:
        k32 = ctypes.WinDLL("kernel32")
        u32 = ctypes.WinDLL("user32")
        k32.GetCurrentProcess.restype = wintypes.HANDLE
        h = k32.GetCurrentProcess()
        pmc = PROCESS_MEMORY_COUNTERS()
        pmc.cb = ctypes.sizeof(pmc)
        k32.K32GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD]
        k32.K32GetProcessMemoryInfo(h, ctypes.byref(pmc), pmc.cb)
        u32.GetGuiResources.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        gdi, usr = u32.GetGuiResources(h, 0), u32.GetGuiResources(h, 1)
        laikai = [wintypes.FILETIME() for _ in range(4)]
        k32.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.c_void_p] * 4
        k32.GetProcessTimes(h, *[ctypes.byref(t) for t in laikai])
        cpu = sum((t.dwHighDateTime << 32 | t.dwLowDateTime) for t in laikai[2:]) / 1e7
        return pmc.WorkingSetSize / 1048576, gdi, usr, cpu
    except Exception:
        return None


_GIJOS_LAIKAI = None


def gijos_cpu_ms():
    """Kiek procesoriaus laiko (ms) sunaudojo ši (tkinter) gija – stabtelėjimų diagnostikai: jei per stabtelėjimą
    gija dirbo, laiką užėmė jos pačios darbas (tkinter, Windows pranešimai); jei ne – ji laukė (laikmatis pavėlavo
    arba Windows nedavė procesoriaus). Tikslumas – Windows laiko kvantas (~15,6 ms)."""
    global _GIJOS_LAIKAI
    try:
        if _GIJOS_LAIKAI is None:
            k32 = ctypes.WinDLL("kernel32")
            k32.GetCurrentThread.restype = wintypes.HANDLE
            k32.GetThreadTimes.argtypes = [wintypes.HANDLE] + [ctypes.c_void_p] * 4
            _GIJOS_LAIKAI = (k32, [wintypes.FILETIME() for _ in range(4)])
        k32, laikai = _GIJOS_LAIKAI
        k32.GetThreadTimes(k32.GetCurrentThread(), *[ctypes.byref(t) for t in laikai])
        return sum((t.dwHighDateTime << 32 | t.dwLowDateTime) for t in laikai[2:]) / 1e4
    except Exception:
        return 0.0


def kaupia(n, kur):
    """Ar kaupti sniegą („kaupti_apacioje“ / „kaupti_languose“): vieta pažymėta IR įjungta visa skiltis."""
    return n["kaupimasis"] and n[kur]


def vejo_kreive(n):
    """Vienas vėjo ciklas peržiūrai: ramu (pauzė) → gūsis → nurimsta. Skaičiuojama tomis pačiomis lygtimis kaip
    Sniegas.vejo_zingsnis, tik be atsitiktinumo (vidutinės reikšmės). Ilga pauzė rodoma sutrumpinta.
    Grąžina taškus (t, stiprumas) – pagal juos peržiūroje kinta vėjas; „gusis“ – kad „Gūsis dabar“ peršoktų į jį."""
    pucia = n["vejas_ijungtas"]
    c = n["vejas"] * 0.29 * pucia  # vidutinis ramaus vėjo stiprumas: |U(-0,2; 0,7)| vidurkis, bet kuriai krypčiai
    g = n["gusio_stiprumas"] * pucia
    trukme = GUSIO_TRUKME
    r_kyla, r_rimsta = 0.8 * GUSIO_KILIMAS / 100, 0.8 * GUSIO_RIMIMAS / 100
    if g <= 0:
        return {"taskai": [(0.0, c), (10.0, c)], "c": c, "g": 0, "gusis": None, "T": 10.0}
    # gūsio pabaigoje pasiektas stiprumas ir laikas iki 90 % (analitiškai – eksponentinis artėjimas)
    r_g = r_kyla if g > c else r_rimsta
    pasiekta = c + (g - c) * (1 - math.exp(-r_g * trukme))
    iki90 = math.log(10) / r_g
    nurimimas = min(40.0, math.log(max(1.0, abs(pasiekta - c) / (0.03 * max(1.0, g)))) / r_rimsta + 0.3)
    pauze = GUSIU_PAUZE
    rodoma_pauze = min(pauze, max(4.0, 0.8 * (trukme + nurimimas)))
    pabaiga = 0.12 * (rodoma_pauze + trukme + nurimimas)
    t0, t1, t2 = rodoma_pauze, rodoma_pauze + trukme, rodoma_pauze + trukme + nurimimas
    T = t2 + pabaiga
    taskai = [(0.0, c), (t0, c)]
    k = 60
    for i in range(1, k + 1):
        t = trukme * i / k
        taskai.append((t0 + t, c + (g - c) * (1 - math.exp(-r_g * t))))
    for i in range(1, k + 1):
        t = nurimimas * i / k
        taskai.append((t1 + t, c + (pasiekta - c) * math.exp(-r_rimsta * t)))
    taskai.append((T, c))
    return {"taskai": taskai, "c": c, "g": g, "T": T, "pauze": pauze, "sutrumpinta": rodoma_pauze < pauze,
            "gusis": (t0, min(t1, t0 + iki90), t1, t2), "nespeja": iki90 > trukme * 1.05}


# ------------------------------------------------------------ sniego senis (mažylis)
# Du apvalūs gumulai, galvoje – šakelės (SENIO_PUOSMENOS), mėlynas šalikas. Juda slysdamas pasilenkęs, už jo – sniego dulkės.
# Pačiumpamas pele už šaliko (pakarpos) – kabo, apatinis gumulas švytuoja; paleistas nukrenta ir susispaudžia.
SENIO_W, SENIO_H = 26, 36  # langeliais
SENIO_SPALVOS = {"W": "#ffffff", "w": "#cddef0", "g": "#788ea8", "K": "#1e1e22", "O": "#f5801e", "o": "#be550f",
                 "B": "#6e4826", "b": "#462c16", "R": "#c82832", "C": "#3478d2",
                 "c": "#18468c", "k": "#f4aaaf", "Y": "#ffd21a", "y": "#ff8a1a",
                 "T": "#8a5a2b", "Q": "#6e4826", "q": "#a0703a", "Z": "#5a3a1c",
                 "L": "#2f9a44", "l": "#1d6a2c", "M": "#e02a2a", "m": "#9a1414"}  # šluota: kotas, rykštės; lapeliai, uogos
SENIO_RANKA_METANT = (23, 24)   # langelis, iš kurio išskrenda gniūžtė (žiūrint į dešinę)
# Visas senis piešinyje nuleistas 1 langeliu (SENIO_POSLINKIS): apatinis gumulas baigdavosi priešpaskutinėje
# eilutėje, o šluotos kotas – paskutinėje, todėl senis visada kabojo 1 langeliu virš sniego, „pasirėmęs ant šluotos“.
# Žemiau esančios piešinio koordinatės – iki poslinkio (tinklelio viduje pridedamas pabaigoje).
SENIO_POSLINKIS = 1
SENIO_TUTA = (25, 19)           # konfeti „pabūklo“ anga
SENIO_RANKA_SEMIANT = (22, 32)  # sauja prie žemės, kai grebia sniegą
KONFETI_SPALVOS = ("#ff3b30", "#ffcc00", "#34c759", "#1e90ff", "#af52de", "#ff2d92", "#5ac8fa", "#ff9500")
# Galvos papuošimai: seniai paeiliui gauna vis kitą.
# trys šakelės / bugienio šakelė su uogomis / viena palinkusi šaka / šakelė galvos šone / be nieko.
# Tiek pat, kiek daugiausia senių įprastose ribose (RIBOS["senio_kiekis"]) – visi seniai vienu metu skirtingi.
SENIO_PUOSMENOS = ("trys", "uogos", "viena", "sonu", "plika")
# Sagos (iš viršaus į apačią): 1-o senio – anglys, 2-o – trispalvė, kitų – raudonos, mėlynos, spalvotos
SENIO_SAGOS = (("#1e1e22", "#1e1e22", "#1e1e22"), ("#fdb913", "#006a44", "#c1272d"),
               ("#c82832", "#c82832", "#c82832"), ("#18468c", "#18468c", "#18468c"),
               ("#ffd21a", "#ff2d92", "#1e90ff"))
# Konfeti pabūklo (tūtos) dryžiai: (1 dryžis, jo šešėlis, 2 dryžis, jo šešėlis) – kiekvieną kartą šaunant
# atsitiktinai kitos spalvos (senio_tuta)
SENIO_TUTOS = (("#c82832", "#82141e", "#ffd21a", "#ff8a1a"), ("#3478d2", "#18468c", "#f0f0f0", "#b8c4d0"),
               ("#3f9e4d", "#236330", "#ff8fc7", "#d0569a"), ("#8e44ad", "#5b2c6f", "#ff8a1c", "#b35300"),
               ("#1fb5a8", "#127a71", "#ffd21a", "#c9a100"))
SENIO_EINA_KADRAI = 6
# Kabančio už šaliko apatinė dalis atsilenkia -2…+2 langelius (kadras 0…4, 2 – tiesiai) – pagal švytuoklės kampą
# (senio_svyruoti), o ne laikmatį: nejudinamas senis kabo ramiai, patempus – atsilieka iš inercijos
SENIO_KABO_KADRAI = 5
# Kabančio / krentančio rankos mostaguoja: kiekvienam atsilenkimui – 5 rankų padėtys, posūkis
# laipsniais (kairė ranka +, dešinė −, t. y. viena kyla, kita leidžiasi).
SENIO_RANKU_POSUKIS = (-30, -15, 0, 15, 30)
SENIO_KABO_RANKOS = len(SENIO_RANKU_POSUKIS)
# Senio „pikselis“ = P × SENIO_MASTELIS × dydis % – trupmeninis (dydis keičiasi tolygiai). 1,15 – be kepurės senis
# atrodė mažesnis. Kad einant ir kabant akys ir galva „nepulsuotų“, pasislinkusi dalis piešiama atskirai (senio_poslinkis).
SENIO_MASTELIS = 1.15
# Ekrano „pikselis“ P apvalinamas (max(2, round(2,4 × aukštis / 1080))): 1080 eilučių ekrane P = 2, o 1200 ir 1440 –
# jau 3, todėl 1080p ekrane senis būdavo trečdaliu mažesnis (fiziškai – ir 24" monitoriuje). Seniui P ne mažesnis
# už šį: 1080p – kaip ~1200p, didesniuose ekranuose niekas nesikeičia.
SENIO_MIN_P = 2.6


def senio_pikselis(P, dydis):
    """Senio „pikselis“ ekrane – trupmeninis (pvz. 3,45: langeliai pakaitomis 3 ir 4 taškų), dydis keičiasi tolygiai."""
    return max(1.0, max(P, SENIO_MIN_P) * SENIO_MASTELIS * dydis / 100)


@functools.lru_cache(maxsize=None)
def senio_poslinkis(poza, kadras):
    """Kuri piešinio dalis kadre pasislinkusi visais langeliais (kaip senio_tinklelis): (riba, dx, virsuje) – eilutės
    iki ribos imtinai (virsuje) arba žemiau jos pasislinkusios dx langelių į dešinę; None – niekas. Einant galva
    pasilenkia 1–2 langeliais, kabant apačia siūbuoja ±2: su trupmeniniu pikseliu (3,45) pasislinkę langeliai
    patekdavo ant kitokio pločio taškų ir akys ar gumulas „pulsuodavo“ (3 ↔ 4 taškai). Todėl ta dalis piešiama
    atskirai – savo langelių pločiais, perstumta sveiku taškų skaičiumi (senio_x)."""
    if poza.endswith(SENIO_BE_SLUOTOS):
        poza = poza[:-len(SENIO_BE_SLUOTOS)]
    sy = round(35.5 - 18.5) + 5 + SENIO_POSLINKIS  # šaliko eilutė galutiniame tinklelyje (kaip senio_tinklelis)
    if poza == "eina":
        f = kadras / SENIO_EINA_KADRAI
        return sy, round(1.5 + 0.5 * math.sin(2 * math.pi * f)), True
    if poza == "kabo":
        sw = kadras // SENIO_KABO_RANKOS - SENIO_KABO_KADRAI // 2
        return (sy, sw, False) if sw else None
    return None


def senio_x(posl, i_kaire, Ps):
    """Langelio (x, y) kairysis kraštas taškais nuo piešinio kairės – su senio_poslinkis (žr. ten). Į kairę žiūrintis
    senis – tikslus veidrodinis į dešinę žiūrinčio atvaizdas taškais (kitaip apsisukus akys pakisdavo 3 ↔ 4 taškai)."""
    viso = round(SENIO_W * Ps)
    if posl:
        riba, dx, virsuje = posl
        baze = round(dx * Ps)

        def Xd(x, y):
            # pasislinkusios dalies kraštinis stulpelis dėl apvalinimo gali išlįsti 1 tašku už kadro – į gretimą
            # juostos kadrą (kabant, siūbuojant rankoms ties kraštu); apribojama kadro ribomis
            if (y <= riba) == virsuje:
                return min(viso, max(0, baze + round((x - dx) * Ps)))
            return round(x * Ps)
    else:
        def Xd(x, y):
            return round(x * Ps)
    if not i_kaire:
        return Xd
    return lambda x, y: viso - Xd(SENIO_W - x, y)


def piesti_senio_kadra(p, tinklas, x0, y0, Ps, X):
    """Kaip piks_piesti, bet langelių kraštai x – pagal X(x, y) (senio_x)."""
    for r, eil in enumerate(tinklas):
        c, n = 0, len(eil)
        y1, y2 = y0 + round(r * Ps), y0 + round((r + 1) * Ps)
        while c < n:
            spalva = eil[c]
            if spalva is None:
                c += 1
                continue
            c1 = c
            while c < n and eil[c] == spalva:
                c += 1
            p.staciakampis(x0 + X(c1, r), y1, x0 + X(c, r), y2, spalva)
SENIO_SVYRUOKLE = 12  # langeliais: nuo šaliko iki apatinio gumulo vidurio (švytuoklės ilgis)
SENIO_INERCIJA = 0.2  # kiek pelės pagreitis atlenkia kabantį senį (1 – kaip tikra švytuoklė; per jautru)


def _sn_elipse(t, cx, cy, rx, ry):
    """Sniego gumulas su savo kontūru (viršutinis, nupieštas ant apatinio, palieka aiškią ribą) ir šešėliu."""
    vidus = set()
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0:
                vidus.add((x, y))
    for (x, y) in vidus:
        if any((x + dx, y + dy) not in vidus for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            t[(x, y)] = "g"
        else:
            t[(x, y)] = "w" if (x + 0.5 - cx) / rx * 0.55 + (y + 0.5 - cy) / ry * 0.85 > 0.5 else "W"


def _sn_linija(t, x0, y0, x1, y1, ch):
    n = max(1, int(round(max(abs(x1 - x0), abs(y1 - y0)))))
    for i in range(n + 1):
        t[(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n))] = ch


def _sn_ranka(t, x0, y0, kampas, ilgis, kryptis):
    a = math.radians(kampas)
    x1, y1 = x0 + kryptis * math.cos(a) * ilgis, y0 - math.sin(a) * ilgis
    _sn_linija(t, x0, y0, x1, y1, "B")
    mx, my = x0 + (x1 - x0) * 0.75, y0 + (y1 - y0) * 0.75
    _sn_linija(t, mx, my, mx + kryptis * math.cos(a + 0.9) * 2, my - math.sin(a + 0.9) * 2, "b")
    _sn_linija(t, x1, y1, x1 + kryptis * math.cos(a - 0.6) * 2, y1 - math.sin(a - 0.6) * 2, "b")


SENIO_SLUOTA_X = 21  # šluotos koto stulpelis (žiūrint į dešinę); kuokštas telpa iki SENIO_W - 1
SENIO_SU_SLUOTA = ("stovi", "dairosi", "rankos", "mojuoja")  # šluota – tik stovint
# Kai senis vaikšto (ne „Tik stovi vietoje“), trumpai sustojęs jis šluotos neturi – kitaip ji atsirasdavo ir
# dingdavo „iš niekur“. Tos pačios pozos be šluotos – su priesaga „_be“.
SENIO_BE_SLUOTOS = "_be"


def _sn_sluota(t, x, y_apacia, ilgis=20, rykstes=10, plotis=4.0):
    """Rykštinė šluota kuokštu į viršų (kaip klasikinio sniego senio): kotas nuo y_apacia aukštyn,
    rykštės išsiskleidžia vėduokle, po jomis raudonas raištis."""
    yv = y_apacia - ilgis
    for y in range(yv, y_apacia + 1):
        t[(x, y)] = "T"
    n = 7  # retos rykštės – tarp jų matosi tarpai (ne vientisas gumulas)
    for i, (ilg, ch) in enumerate(zip((0.8, 0.95, 0.88, 1.0, 0.9, 0.97, 0.82), "QqZqQZq")):
        v = -plotis + 2 * plotis * i / (n - 1)
        _sn_linija(t, x, yv - 1, x + v, yv - rykstes * ilg, ch)
    for dx in (-1, 0, 1):
        t[(x + dx, yv)] = "R"


def _sn_puosmena(t, gx, gy, puosmena):
    """Galvos papuošimas – į galvą įbestos šakelės (SENIO_PUOSMENOS)."""
    th = gy - 6  # galvos viršutinė (kontūro) eilutė – šakelės įbestos čia
    if puosmena == "trys":  # trys įbestos šakelės (Gemini)
        _sn_linija(t, gx - 1, th, gx - 3, th - 3, "b")
        _sn_linija(t, gx + 1, th, gx + 2, th - 3, "B")
        _sn_linija(t, gx, th, gx, th - 2, "b")
    elif puosmena == "viena":  # viena šaka su dviem atšakėlėmis, palinkusi atgal (nuo šluotos)
        th += 1  # įbesta 1 langeliu giliau – kitaip atrodė per aukštai
        _sn_linija(t, gx - 1, th, gx - 3, th - 5, "B")
        _sn_linija(t, gx - 2, th - 2, gx, th - 4, "b")
        _sn_linija(t, gx - 3, th - 4, gx - 5, th - 5, "b")
    elif puosmena == "uogos":  # bugienio šakelė su lapeliais ir uogomis, pasvirusi į kairę (atgal)
        th += 1  # įbesta 1 langeliu giliau
        _sn_linija(t, gx, th, gx - 2, th - 3, "B")
        for x_, y_ in ((-4, -2), (-3, -2), (-5, -3), (-4, -3), (0, -4), (1, -4), (1, -5), (2, -5)):
            t[(gx + x_, th + y_)] = "L"
        t[(gx - 5, th - 2)] = t[(gx + 2, th - 4)] = "l"
        t[(gx - 2, th - 4)] = t[(gx - 1, th - 5)] = "M"
        t[(gx - 1, th - 4)] = "m"
    elif puosmena == "sonu":  # šakelė įbesta galvos šone, styro atgal ir aukštyn (kaip plunksna)
        _sn_linija(t, gx - 4, th + 1, gx - 7, th - 3, "B")
        _sn_linija(t, gx - 6, th - 1, gx - 8, th - 1, "b")
        t[(gx - 5, th - 2)] = "b"


@functools.lru_cache(maxsize=None)
def senio_tinklelis(poza, kadras, i_kaire, bumbulas=0, tuta=0, puosmena="plika"):
    """poza: „eina“ (kadras 0…5), „stovi“, „kabo“ (atsilenkimas × rankų padėtis, žr. senio_kabo_kadras), „nukrenta“, „meta“, „sauna“, „semia“, „mojuoja“,
    „rankos“, „dairosi“ (galva atsukta į kitą pusę). Žiūri į dešinę (i_kaire – veidrodiškai).
    Grąžina eilutes su spalvomis (None – permatoma). Priesaga „_be“ – ta pati poza be šluotos."""
    sluota = not poza.endswith(SENIO_BE_SLUOTOS)
    if not sluota:
        poza = poza[:-len(SENIO_BE_SLUOTOS)]
    t = {}
    cx, gx = 12.5, 12
    f = kadras / (SENIO_EINA_KADRAI if poza == "eina" else SENIO_KABO_KADRAI)
    sq = 1.3 if poza == "nukrenta" else 0.0
    # apatinis gumulas – apvalus iki paskutinės eilutės (35,5 nukirstų jį plokščiai – ant nuvalyto kelio
    # senis stovėjo nukirsta apačia); galvos centras – sveikame langelyje (17), kitaip apvalinant (16,5 → 16)
    # galva gautų kampuotą „ausų“ eilutę
    _sn_elipse(t, cx, 35 - 7.2 + sq, 8.2 + sq, 7.2 - sq)
    gy = 35.5 - 18.5 + sq * 2
    _sn_elipse(t, cx, gy, 6.0, 5.6)
    gy = round(gy)
    # „dairosi“ – galva atsukta į kitą pusę (veidas veidrodiškai galvos centro, langelio gx, atžvilgiu)
    v = (lambda x: 2 * gx - x) if poza == "dairosi" else (lambda x: x)
    for ax in (gx - 3, gx + 1):  # akys
        t[(v(ax), gy - 1)] = t[(v(ax), gy)] = "K"
    t[(v(gx - 4), gy + 2)] = t[(v(gx + 3), gy + 2)] = "k"  # skruostai
    for i, ch in enumerate("OOo"):
        t[(v(gx + i), gy + 2)] = ch
    if poza == "kabo":  # nustebęs
        t[(gx - 1, gy + 4)] = "K"
    else:
        t[(v(gx - 2), gy + 3)] = t[(v(gx + 1), gy + 3)] = "K"
        t[(v(gx - 1), gy + 4)] = t[(v(gx), gy + 4)] = "K"
    # anglies sagos ant apatinio gumulo (po šaliku) – trys, kaip tikro sniego senio
    apat_cy, apat_ry = 35 - 7.2 + sq, 7.2 - sq
    for i, k_ in enumerate((-0.5, -0.1, 0.3)):
        t[(gx, round(apat_cy + apat_ry * k_))] = "123"[i]  # spalvos – SENIO_SAGOS (kiekvieno senio savos)
    _sn_puosmena(t, gx, gy, puosmena)  # galvos šakelės
    sy = gy + 5  # šalikas
    for x in range(gx - 5, gx + 6):
        t[(x, sy)] = "C" if x % 2 else "c"
    for i in range(4):
        t[(gx - 4 - (i if poza == "eina" else 0), sy + 1 + i)] = "C" if i % 2 == 0 else "c"
    # kabo: kadras = atsilenkimas * SENIO_KABO_RANKOS + rankų padėtis
    sw = kadras // SENIO_KABO_RANKOS - SENIO_KABO_KADRAI // 2 if poza == "kabo" else 0  # apatinės dalies atsilenkimas
    most = SENIO_RANKU_POSUKIS[kadras % SENIO_KABO_RANKOS] if poza == "kabo" else 0  # rankų mostas
    kamp = {"kabo": 55 - 6 * sw, "nukrenta": 25}.get(poza, -10)
    _sn_ranka(t, gx - 7, sy + 3, (35 if kadras == 0 else -25) if poza == "rankos" else kamp + most, 4, -1)
    if poza == "meta":  # 0 – užsimoja (gniūžtė rankoje virš peties), 1 – meta (ranka į priekį)
        _sn_ranka(t, gx + 7, sy + 3, 100 if kadras == 0 else 15, 4, 1)
        if kadras == 0:
            for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
                t[(gx + 6 + dx, sy - 3 + dy)] = "W"
            for dx, dy in ((-1, 0), (-1, 1), (2, 0), (2, 1), (0, -1), (1, -1)):
                t[(gx + 6 + dx, sy - 3 + dy)] = "g"
    elif poza == "semia":  # pasilenkęs grebia sniego gniūžtei – ranka iki žemės, saujoje sniegas
        _sn_ranka(t, gx + 7, sy + 3, -70, 6, 1)
        for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
            t[(SENIO_RANKA_SEMIANT[0] + dx - 1, SENIO_RANKA_SEMIANT[1] + dy - 1)] = "W"
    elif poza in SENIO_SU_SLUOTA and sluota:  # stovėdamas laiko šluotą; pamojuodamas ją kilsteli
        kilst = 3 if poza == "mojuoja" and kadras == 1 else 0
        xs, yr = SENIO_SLUOTA_X, sy + 2 - kilst
        _sn_sluota(t, xs, 35 - kilst)
        _sn_linija(t, gx + 7, sy + 3, xs - 1, yr, "B")  # ranka iki koto
        t[(xs + 1, yr - 1)] = t[(xs + 1, yr + 1)] = "b"  # pirštai apie kotą
    elif poza == "sauna":  # laiko konfeti pabūklą (dryžuotą tūtą); 1 – iššovė (žiežirbos)
        _sn_ranka(t, gx + 7, sy + 3, 35, 4, 1)
        for i in range(4):
            t[(gx + 10 + i, sy + 1 - i)] = "4" if i % 2 == 0 else "6"  # dryžiai – kas šūvį kitų spalvų (tuta)
            t[(gx + 10 + i, sy - i)] = "5" if i % 2 == 0 else "7"
        if kadras == 1:
            for dx, dy in ((0, -1), (-1, -2), (1, -2), (0, -3)):
                t[(SENIO_TUTA[0] + dx, SENIO_TUTA[1] + dy)] = "Y" if dy != -2 else "y"
    elif poza == "mojuoja":  # be šluotos – pamojuoja ranka
        _sn_ranka(t, gx + 7, sy + 3, 110 if kadras == 1 else 60, 4, 1)
    elif poza == "rankos":  # be šluotos – abi rankos kartu
        _sn_ranka(t, gx + 7, sy + 3, 35 if kadras == 0 else -25, 4, 1)
    else:
        _sn_ranka(t, gx + 7, sy + 3, kamp if poza != "kabo" else 100 - kamp - most, 4, 1)
    if poza == "eina":  # galva pasilenkusi į priekį ir linksi, už nugaros – sniego dulkės. Kad keli seniai
        # neatrodytų kaip žąsys, kiekvienas eina savo greičiu ir tempu („greitis“)
        lenk = round(1.5 + 0.5 * math.sin(2 * math.pi * f))
        t = {(x + (lenk if y <= sy else 0), y): v for (x, y), v in t.items()}
        for i in range(4):
            t[(gx - 9 - i * 2 - round(f * 2), 34 - (i % 2) - round(f))] = "w" if i % 2 else "W"
    elif poza == "semia":  # galva (su šakelėmis) pasilenkia į priekį ir žemyn
        t = {(x + (2 if y <= sy else 0), y + (1 if y <= sy else 0)): v for (x, y), v in sorted(t.items(), key=lambda q: -q[0][1])}
    elif poza == "kabo":  # kabo už šaliko: žemiau jo kūnas atsilenkęs pagal švytuoklę (senio_svyruoti)
        t = {(x + (sw if y > sy else 0), y): v for (x, y), v in t.items()}
    # gumulo apačia – paskutinėje eilutėje (ant sniego), šluotos koto galas už piešinio nukerpamas
    t = {(x, y + SENIO_POSLINKIS): v for (x, y), v in t.items()}
    eil = [[None] * SENIO_W for _ in range(SENIO_H)]
    for (x, y), ch in t.items():
        if 0 <= x < SENIO_W and 0 <= y < SENIO_H:
            if ch in "123":
                spalva = SENIO_SAGOS[bumbulas % len(SENIO_SAGOS)][int(ch) - 1]
            elif ch in "4567":
                spalva = SENIO_TUTOS[tuta % len(SENIO_TUTOS)][int(ch) - 4]
            else:
                spalva = SENIO_SPALVOS[ch]
            eil[y][SENIO_W - 1 - x if i_kaire else x] = spalva
    return eil


# sprite juostos kadrai: (poza, kadras) – kiekvienas abiem kryptimis
SENIO_KADRAI = ([("eina", i) for i in range(SENIO_EINA_KADRAI)] + [("stovi", 0)] +
                [("kabo", i) for i in range(SENIO_KABO_KADRAI * SENIO_KABO_RANKOS)] + [("nukrenta", 0)] +
                [("meta", 0), ("meta", 1), ("sauna", 0), ("sauna", 1), ("semia", 0), ("mojuoja", 0), ("mojuoja", 1),
                 ("rankos", 0), ("rankos", 1), ("dairosi", 0)] +
                [(p_ + SENIO_BE_SLUOTOS, k_) for p_, k_ in (("stovi", 0), ("mojuoja", 0), ("mojuoja", 1),
                                                            ("rankos", 0), ("rankos", 1), ("dairosi", 0))])


@functools.lru_cache(maxsize=None)
def senio_puosmenos_langeliai(poza, kadras, i_kaire, puosmena):
    """Galvos papuošimo langeliai [(x, y, plotis, spalva)]: juostoje senis be papuošimo, šie užpiešiami ant viršaus.
    Gretimi vienodos spalvos langeliai eilutėje sujungti (mažiau FillRect)."""
    if puosmena == "plika":
        return ()
    a, b = senio_tinklelis(poza, kadras, i_kaire), senio_tinklelis(poza, kadras, i_kaire, 0, 0, puosmena)
    rez = []
    for y in range(SENIO_H):
        x = 0
        while x < SENIO_W:
            sp = b[y][x]
            if sp and sp != a[y][x]:
                w = 1
                while x + w < SENIO_W and b[y][x + w] == sp and sp != a[y][x + w]:
                    w += 1
                rez.append((x, y, w, sp))
                x += w
            else:
                x += 1
    return tuple(rez)


@functools.lru_cache(maxsize=None)
def senio_bumbulo_langeliai(poza, kadras, i_kaire):
    """Kiekvieno senio savų spalvų langeliai (sagos): [(x, y, plotis, (spalva kiekvienam seniui))] – tik tie,
    kurie tarp senių skiriasi (juostoje – 1-o senio spalvos, kitiems jie užpiešiami)."""
    g = [senio_tinklelis(poza, kadras, i_kaire, b) for b in range(len(SENIO_SAGOS))]
    rez = []
    for y in range(SENIO_H):
        x = 0
        while x < SENIO_W:
            sp = tuple(gb[y][x] for gb in g)
            if any(c != sp[0] for c in sp[1:]):
                w = 1
                while x + w < SENIO_W and tuple(gb[y][x + w] for gb in g) == sp:
                    w += 1
                rez.append((x, y, w, sp))
                x += w
            else:
                x += 1
    return rez


@functools.lru_cache(maxsize=None)
def senio_tutos_langeliai(poza, kadras, i_kaire):
    """Konfeti tūtos langeliai, kurių spalva priklauso nuo tūtos (kaip senio_bumbulo_langeliai – bumbulo)."""
    g = [senio_tinklelis(poza, kadras, i_kaire, 0, j) for j in range(len(SENIO_TUTOS))]
    return [(x, y, tuple(gj[y][x] for gj in g)) for y in range(SENIO_H) for x in range(SENIO_W)
            if any(gj[y][x] != g[0][y][x] for gj in g[1:])]


def senio_tuta(s_):
    """Kurios spalvos tūta šauna dabar: kiekvieną kartą pradėjus šaudyti – atsitiktinė, bet ne tokia pat kaip
    praeitą kartą. Grąžina SENIO_TUTOS numerį (0 – kai nešauna)."""
    if s_["busena"] != "sauna":
        if s_.get("tuta") is not None:
            s_["tuta_pask"], s_["tuta"] = s_["tuta"], None
        return 0
    if s_.get("tuta") is None:
        s_["tuta"] = random.choice([j for j in range(len(SENIO_TUTOS)) if j != s_.get("tuta_pask")])
    return s_["tuta"]


SENIO_SNIEGUOJA = ("stovi", "dairosi", "rankos", "mojuoja")  # tada ant senio prisninga; kitaip – nubyra
SENIO_SNIEGO_LAIKAS = 45.0  # s, per kiek prisninga iki galo
SENIO_SNIEGO_DALIS = 1.0    # kiek galimų vietų ilgainiui apsninga (pasirinktas variantas B – visos)


@functools.lru_cache(maxsize=None)
def senio_sniego_langeliai(poza, kadras, i_kaire, puosmena="plika"):
    """Kur ant senio gali gulėti sniegas: tušti langeliai tiesiai virš šluotos, rankų, galvos šakelių ir galvos viršaus
    (dviejų viršutinių kontūro eilių – ant šonų sniegas atrodytų kaip baltas kontūras; ant balto kūno – nesimatytų).
    [(x, y, slenkstis)], surikiuota pagal slenkstį: langelis apsninga, kai kaupimas viršija jo slenkstį (taip
    prisninga pamažu). Slenkstis pagal vietą (veidrodiškai – vienodas abiem kryptims), todėl sniegas nemirga
    keičiantis kadrams, o pakeltose rankose lieka tose pačiose šakelėse."""
    t = senio_tinklelis(poza, kadras, i_kaire, 0, 0, puosmena)
    medis = {SENIO_SPALVOS[k] for k in "BbTQqZLl"}  # šakos, šluota, lapeliai ir spygliai
    # galvos viršus. Matuojama nuo galvos vidurio (einant / semiant galva pasislenka):
    # su šakelėmis – kontūras ±3 langeliai nuo vidurio; plikam – tik 3 pavieniai taškai pačiame viršuje
    # (per visą galvą sniegas atrodė kaip perukas ant plikės)
    kontur = SENIO_SPALVOS["g"]
    kont_eil = [y for y in range(SENIO_H) if any(c == kontur for c in t[y])]
    galva = set()
    if kont_eil:
        y0 = kont_eil[0]
        kr = [x for x in range(SENIO_W) if t[y0][x] == kontur]
        c = (kr[0] + kr[-1]) / 2
        if puosmena == "plika":  # tik keli pavieniai balti taškai (ištisinis sniegas atrodė kaip perukas)
            kr_ = -1 if i_kaire else 1
            for x in (round(c + kr_ * d) for d in (-3, -1, 2)):  # ant galvos lanko – viršutinis langelis stulpelyje
                y_ = next((y for y in range(y0, y0 + 3) if t[y][x] is not None), None)
                if y_ is not None:
                    galva.add((x, y_))
        else:
            galva = {(x, y) for y in (y0, y0 + 1) for x in range(SENIO_W) if t[y][x] == kontur and abs(x - c) <= 3}
    rez = []
    for y in range(1, SENIO_H):
        for x in range(SENIO_W):
            v = t[y][x]
            if t[y - 1][x] is None and (v in medis or (x, y) in galva):
                xs = SENIO_W - 1 - x if i_kaire else x
                rez.append((x, y - 1, random.Random(xs * 7919 + y * 104729).random()))
    return tuple(sorted(rez, key=lambda a: a[2]))


SENIO_SLUOTOS_LEMPUTES = 5  # kiek girliandos lempučių ant šluotos kuokšto


@functools.lru_cache(maxsize=None)
def senio_sluotos_lemputes(poza, kadras, i_kaire):
    """Girliandos lemputės ant šluotos kuokšto (kaip ant eglučių): [(x, y, spalvos nr.)] – ant rykščių, tolygiai
    nuo apačios iki viršaus ir pakaitomis į abi puses. Pozose be šluotos – tuščia."""
    t = senio_tinklelis(poza, kadras, i_kaire, 0)
    rykstes = {SENIO_SPALVOS[k] for k in "QqZ"}
    langeliai = sorted(((x, y) for y in range(SENIO_H) for x in range(SENIO_W) if t[y][x] in rykstes),
                       key=lambda a: (-a[1], a[0]))  # nuo apačios (raiščio) į viršų
    if len(langeliai) < SENIO_SLUOTOS_LEMPUTES * 2:
        return ()
    rez, n = [], len(langeliai)
    for j in range(SENIO_SLUOTOS_LEMPUTES):
        # ne pačioje apačioje (ten rykštės susispaudusios prie raudono raiščio) – nuo ~30 % iki viršūnės
        x, y = langeliai[int((0.3 + 0.7 * j / (SENIO_SLUOTOS_LEMPUTES - 1)) * (n - 1))]
        rez.append((x, y, j))
    return tuple(rez)


def senio_lemputes_sviesumas(animacija, laikas, j, n, senis=0):
    """Šluotos lemputės j (iš n) šviesumas 0…1 pagal animaciją. „lieja“ – 6 lygiai (tiek teptukų spalvų)."""
    if animacija == "sviecia":
        return 1.0
    if animacija == "lieja":  # lėtai įsižiebia ir užgęsta, kiekviena savo fazėje (~3 s ciklas)
        v = 0.5 - 0.5 * math.cos(2 * math.pi * (laikas / 3.0 + j * 0.23 + senis * 0.17))
        return round(v * 5) / 5
    if animacija == "bega":  # šviesa bėga iš apačios į viršų, už jos – blėstanti uodegėlė
        k = (laikas * 5 + senis * 2) % (n + 2)
        d = k - j
        return 1.0 if 0 <= d < 1 else 0.4 if 1 <= d < 2 else 0.0
    return 1.0 if (laikas * 0.9 + j * 0.37 + senis * 0.21) % 1.0 < 0.6 else 0.0  # mirksi


def senio_lemputes_spalva(j, senis, sviesumas):
    """Lemputės spalva: įjungta – kaip eglučių; tarpiniai lygiai – tarp užgesusios ir įjungtos."""
    spalvos = tuple(LEMPUCIU_SPALVOS)
    sp = spalvos[(j + senis) % len(spalvos)]
    if sviesumas >= 1.0:
        return sp
    if sviesumas <= 0.0:
        return LEMPUCIU_SPALVOS[sp]
    return _maisyti(LEMPUCIU_SPALVOS[sp], sp, sviesumas)


# Stovintis senis nekyla, kai aplink jį prisninga (apsninga), bet nusileidžia, kai sniegas po juo suslūgsta
SENIO_GNIUZTE, SENIO_GNIUZTES_PUS = 12.0, 8  # apatinės gniūžtės vidurys ir pusplotis langeliais (žiūrint į dešinę)
SENIO_NUSESDA = 40  # px/s (×k): kaip greitai stovintis senis nusileidžia, kai sniegas po juo suslūgsta
SENIO_KELIO_GYLIS = 3  # langeliai: tiek senio apačios uždengia prisnigtas kelias priešais jį – giliau senis kyla
SENIO_KYLA = 6  # px/s (×k): kaip greitai stovintis senis ekrano apačioje kyla, kai priešais jį kaupiasi kelio sniegas
SENIO_STOVINT = ("stovi", "dairosi", "rankos", "mojuoja", "meta", "sauna", "nukrenta")
# būsenos, kai senis stovi ant paviršiaus (gali būti taikinys, pagaunamas spragtelėjimu ir pan.)
SENIO_ANT_PAVIRSIAUS = ("eina", "stovi", "meta", "sauna", "mojuoja", "rankos", "dairosi")


SENIO_SNIEGO_SPALVOS = {SENIO_SPALVOS["W"]: SENIO_SPALVOS["W"], SENIO_SPALVOS["w"]: SENIO_SPALVOS["w"],
                        SENIO_SPALVOS["g"]: SENIO_SPALVOS["w"]}  # kūno sniegas (kontūras byra kaip šešėlinis sniegas)


def senio_nuolauzos(tinklelis, x0, y0, Ps, kryptis, k, riba_x, riba_y):
    """Subyrėjęs senis byra smulkiai, kaip visa programa – pikseliais: kūnas – 2×2 langelių sniego grumsteliais
    (nusileidę susilieja su sniegu), šakelės, šalikas, morka, akys, rankos – po vieną langelį (guli ilgiau).
    Viskas lekia į šalis – labiau nuo to, su kuo susidūrė (kryptis -1/0/1) – ir krenta ant sniego."""
    out, cx = [], SENIO_W / 2

    def gabalas(x, y, dydis, spalva, sniegas):
        aukstai = 1 - y / SENIO_H  # viršutiniai gabalai (galva, šakelės) lekia aukščiau
        # ribos – kaip piks_piesti (Ps trupmeninis): gabalai iš pradžių guli tiksliai ten, kur buvo senio pikseliai
        out.append({"tipas": "gabalas", "x": x0 + round(x * Ps), "y": y0 + round((y + dydis) * Ps),
                    "d": round((x + dydis) * Ps) - round(x * Ps),
                    "spalva": spalva, "sniegas": sniegas, "guli": False, "gyv": random.uniform(3.5, 6.0),
                    "vx": ((x + dydis / 2 - cx) / cx * random.uniform(40, 160) + kryptis * random.uniform(10, 100)) * k,
                    "vy": -random.uniform(50, 220) * (0.4 + aukstai) * k, "sena": None,
                    "riba_x": riba_x, "riba_y": riba_y})
    for by in range(0, SENIO_H, 2):
        for bx in range(0, SENIO_W, 2):
            sniegas, kita = [], []
            for y in range(by, min(by + 2, SENIO_H)):
                for x in range(bx, min(bx + 2, SENIO_W)):
                    c = tinklelis[y][x]
                    if c in SENIO_SNIEGO_SPALVOS:
                        sniegas.append(SENIO_SNIEGO_SPALVOS[c])
                    elif c:
                        kita.append((x, y, c))
            for x, y, c in kita:
                gabalas(x, y, 1, c, False)
            if len(sniegas) >= 2:
                gabalas(bx, by, 2 if len(sniegas) == 4 else 1, max(sniegas, key=sniegas.count), True)
    return out


def _gulinti_ant_sniego(d, zeme):
    """Gulintis gabalas ar popieriukas lieka ant sniego paviršiaus: sniegui nuslūgus (kauburys nusėda, vėjas
    nupučia) – vėl krenta, pasnigus – pakyla kartu. Kitaip likdavo kaboti ore."""
    pav = zeme(d["x"], d["y"] - 3)
    if pav is None or pav > d["y"] + 1:
        d.update(guli=False, vy=0.0, vx=0.0)
    elif pav < d["y"]:
        d["y"] = pav


GNIUZTES_VEJAS = 0.25  # 1/s – kokia vėjo greičio dalis per sekundę pridedama gniūžtei


def senio_daleliu_zingsnis(daleles, dt, k, zeme, vejas_px=0.0):
    """Sniego gniūžtės, konfeti ir subyrėjusio senio gabalai (ekrane ir peržiūroje – tos pačios taisyklės).
    zeme(x, y) – sniego paviršiaus ties x, esančio ne aukščiau už y, aukštis (arba None). Grąžina (likusios, [(x, y) – kur gniūžtė sudužo])."""
    likusios, suduzo = [], []
    for d in daleles:
        if d["tipas"] == "gniuzte":
            y0 = d["y"]
            # tanki gniūžtė – vėjas ją neša nedaug: prieš vėją skrieja kiek trumpiau, pavėjui – toliau.
            # Tik vėjo stūmimas, be oro pasipriešinimo – ramiu oru skrenda kaip anksčiau (taikymas lieka tikslus)
            d["vx"] += vejas_px * GNIUZTES_VEJAS * dt
            d["vy"] += TRAUKA * k * dt
            d["x"] += d["vx"] * dt
            d["y"] += d["vy"] * dt
            pav = zeme(d["x"], y0)
            if d["vy"] > 0 and pav is not None and y0 <= pav <= d["y"] + 1:
                suduzo.append((d["x"], pav))
                continue
            if d.get("i_seni"):
                suduzo.append((d["x"], d["y"]))
                continue
            if d["y"] > d["riba_y"] or not -50 < d["x"] < d["riba_x"] + 50:
                continue
        elif d["tipas"] == "gabalas":  # krenta, kartą kitą atšoka, guli ir pradingsta
            d["gyv"] -= dt
            if not d["guli"]:
                y0 = d["y"]
                d["vy"] += TRAUKA * k * dt
                d["x"] += d["vx"] * dt
                d["y"] += d["vy"] * dt
                pav = zeme(d["x"], y0)
                if pav is not None and d["y"] >= pav and d["vy"] > 0:
                    if d["vy"] > 160 * k:
                        d.update(y=pav, vy=-d["vy"] * 0.3, vx=d["vx"] * 0.5)
                    else:  # sniego grumstelis netrukus susilieja su sniegu, spalvoti gabalėliai guli ilgiau
                        d.update(y=pav, vy=0.0, guli=True,
                                 gyv=min(d["gyv"], random.uniform(0.3, 1.5) if d.get("sniegas") else d["gyv"]))
            else:
                _gulinti_ant_sniego(d, zeme)
            if d["gyv"] <= 0 or d["y"] > d["riba_y"] or not -50 < d["x"] < d["riba_x"] + 50:
                continue
        else:  # konfeti: popieriukai sklando – didelis oro pasipriešinimas, siūbuoja, neša vėjas
            d["gyv"] -= dt
            if not d["guli"]:
                d["faze"] += dt * 9
                d["vx"] += (vejas_px * 0.5 - d["vx"]) * min(1.0, dt * 2.5)
                d["vy"] = min(d["vy"] + 350 * k * dt, 38 * k) if d["vy"] > 0 else d["vy"] + 600 * k * dt
                y0 = d["y"]
                d["x"] += (d["vx"] + math.sin(d["faze"]) * 18 * k) * dt
                d["y"] += d["vy"] * dt
                pav = zeme(d["x"], y0)
                if pav is not None and d["y"] >= pav and d["vy"] > 0:
                    d.update(y=pav, guli=True, gyv=min(d["gyv"], random.uniform(2.5, 5.0)))
            else:
                _gulinti_ant_sniego(d, zeme)
            if d["gyv"] <= 0 or d["y"] > d["riba_y"] or not -50 < d["x"] < d["riba_x"] + 50:
                continue
        likusios.append(d)
    return likusios, suduzo


def senio_pauze():
    """Ką senis veikia sustojęs: dažniausiai tiesiog stovi ar apsidairo, kartais meta gniūžtę ar šauna konfeti."""
    return random.choices(("stovi", "dairosi", "meta", "sauna"), weights=(32, 18, 32, 18))[0]


def senio_dairytis(s_):
    """Pasuka galvą į kitą pusę ir po kiek laiko atsuka atgal."""
    s_.update(busena="dairosi", t=0.0, dairytis=random.uniform(1.2, 2.6))


def senio_stovint(s_, trukme=(3, 8)):
    """„Tik stovi vietoje“: kartais pajudina rankas, pamojuoja, pasuka galvą ar tiesiog stovi toliau."""
    b = random.choices(("rankos", "mojuoja", "dairosi", "stovi"), weights=(30, 14, 36, 20))[0]
    if b == "dairosi":
        senio_dairytis(s_)
    else:
        s_.update(busena=b, t=0.0)
    s_["stoveti"] = random.uniform(*trukme)


def senio_trumpo_veiksmo_trukme(s_):
    """Kiek trunka pamojavimas, rankų pajudinimas ar apsidairymas."""
    return {"mojuoja": 1.3, "rankos": 1.2}.get(s_["busena"]) or s_.get("dairytis", 2.0)


# Gniūžtės metimai: užsimojimo trukmė, greitis į priekį ir aukštyn (px/s, kai mastelis 1)
METIMAI = {"silpnai": (0.25, (110, 190), (120, 200)), "vidutiniskai": (0.35, (260, 420), (180, 320)),
           "stipriai": (0.55, (520, 720), (230, 360))}
METIMU_SVORIAI = {"silpnai": 30, "vidutiniskai": 45, "stipriai": 25}
# Konfeti rinkiniai (spalvos) ir šūvio formos
KONFETI_RINKINIAI = {
    "vaivorykste": KONFETI_SPALVOS,
    "auksas": ("#ffd700", "#f5c542", "#ffe680", "#c0c0c0", "#e8e8e8", "#b8860b"),
    "kaledos": ("#d62828", "#ff4d4d", "#1f9e3a", "#2ecc71", "#ffffff", "#ffd700"),
    "trispalve": ("#fdb913", "#006a44", "#c1272d"),
    "ledas": ("#ffffff", "#bfe6ff", "#5ac8fa", "#1e90ff", "#8fd3ff"),
    "rozine": ("#ff2d92", "#ff8fc7", "#af52de", "#ffb3e6", "#ffffff"),
}
KONFETI_FORMOS = {  # (kampai nuo horizonto, greitis, kiekis šūvyje, šūvių laikai)
    "platus": ((25, 80), (180, 360), 40, (0.3,)),
    "fontanas": ((72, 88), (260, 420), 40, (0.3,)),
    "dvigubas": ((40, 80), (170, 330), 26, (0.3, 0.58)),
}


def nauji_konfeti(x, y, kryptis, k, riba_x, riba_y, kiek=40, spalvos=KONFETI_SPALVOS, kampai=(40, 80),
                  greitis=(180, 360)):
    out = []
    for _ in range(kiek):
        a = math.radians(random.uniform(*kampai))
        v = random.uniform(*greitis) * k
        out.append({"tipas": "konfeti", "x": x, "y": y, "vx": kryptis * math.cos(a) * v, "vy": -math.sin(a) * v,
                    "spalva": random.choice(spalvos), "faze": random.uniform(0, 6.3), "guli": False,
                    "gyv": 12.0, "sena": None, "riba_x": riba_x, "riba_y": riba_y})
    return out


SEMIMAS = 0.45  # tiek laiko senis pasilenkęs grebia sniegą prieš užsimodamas


def senio_veiksmo_eiga(s_, ranka, k, riba_x, riba_y, daleles, maks_nauju=40, taikinys=None, semti=None):
    """Gniūžtė ar konfeti – ekrane ir peržiūroje tos pačios taisyklės. ranka(langelis) → (x, y).
    Gniūžtė: pasilenkia ir susigrebia sniego (semti() – paima iš sniego sluoksnio; False – sniego nėra, tada
    nemeta), užsimoja ir meta. taikinys() → (x, y) arba None: jei yra – atsisuka į jį ir meta taikydamas lanku
    (su nedidele paklaida), stiprumas – pagal atstumą; jei ne – atsitiktiniu stiprumu į priekį.
    Konfeti – skirtingų spalvų rinkinių ir formų. True – veiksmas baigtas."""
    t = s_["t"]
    if s_["busena"] == "meta":
        if not s_.get("jega"):
            tk_ = taikinys() if taikinys else None
            s_["taiko"] = tk_ is not None
            if tk_ is not None:
                dx = tk_[0] - s_["x"]
                s_["kryptis"] = 1 if dx >= 0 else -1
                s_["jega"] = "silpnai" if abs(dx) < 220 * k else ("vidutiniskai" if abs(dx) < 520 * k else "stipriai")
            else:
                s_["jega"] = random.choices(list(METIMU_SVORIAI), weights=list(METIMU_SVORIAI.values()))[0]
        if not s_.get("pasemta") and t >= SEMIMAS * 0.6:
            s_["pasemta"] = True
            if semti is not None and not semti():
                s_.update(jega=None, konfeti=None, suviai=0, pasemta=False, taiko=False)
                return True  # sniego nėra – nemeta
        uzs, vx_, vy_ = METIMAI[s_["jega"]]
        if not s_.get("suviai") and t >= SEMIMAS + uzs:
            s_["suviai"] = 1
            x, y = ranka(SENIO_RANKA_METANT)
            tk_ = taikinys() if (taikinys and s_.get("taiko")) else None
            if tk_ is not None:  # balistinis lankas į taikinį: skrydžio laikas pagal atstumą
                dx, dy = tk_[0] - x, tk_[1] - y
                T = max(0.35, min(1.3, abs(dx) / (420 * k)))
                vx = dx / T * random.uniform(0.95, 1.05)  # nedidelė paklaida – kartais nepataiko
                vy = (dy - 0.5 * TRAUKA * k * T * T) / T
            else:
                vx, vy = s_["kryptis"] * random.uniform(*vx_) * k, -random.uniform(*vy_) * k
            daleles.append({"tipas": "gniuzte", "x": x, "y": y, "sena": None, "savininkas": s_, "vx": vx, "vy": vy,
                            "riba_x": riba_x, "riba_y": riba_y})
        baigta = t >= SEMIMAS + uzs + 0.35
    else:
        if not s_.get("konfeti"):
            s_["konfeti"] = (random.choice(list(KONFETI_RINKINIAI)), random.choice(list(KONFETI_FORMOS)))
        rinkinys, forma = s_["konfeti"]
        kampai, greitis, kiek, laikai = KONFETI_FORMOS[forma]
        n = s_.get("suviai") or 0
        if n < len(laikai) and t >= laikai[n]:
            s_["suviai"] = n + 1
            x, y = ranka((SENIO_TUTA[0], SENIO_TUTA[1] + SENIO_POSLINKIS))
            daleles += nauji_konfeti(x, y, s_["kryptis"], k, riba_x, riba_y, min(kiek, maks_nauju),
                                     KONFETI_RINKINIAI[rinkinys], kampai, greitis)
        baigta = t >= laikai[-1] + 0.7
    if baigta:
        s_.update(jega=None, konfeti=None, suviai=0, pasemta=False, taiko=False)
    return baigta


def senio_svyruoti(s_, dt, Ps, k):
    """Už šaliko pakabintas senis – švytuoklė: kampas keičiasi nuo pakabinimo taško (šaliko) pagreičio, o sunkis
    grąžina žemyn, sniegas sunkus – svyravimas greit nurimsta. Nejudinamas kabo tiesiai; patemptas į šoną –
    apatinė dalis iš inercijos atsilieka, sustojus švysteli ir nusvyra."""
    if dt <= 0:
        return
    x = s_["x"]
    px = s_.get("sv_x")
    # Naujas kabėjimas / kritimas (sv_x=None) ar peršokimas – iš naujo ir švytuoklė, ir rankos: kitaip rankos
    # mostaguotų pagal seną (pvz., prieš kelias minutes buvusio kritimo) greitį ir vietą
    if px is None or abs(x - px) > 3000 * k * dt:
        s_.update(sv_x=x, sv_v=0.0, sv_kampas=0.0, sv_omega=0.0, rk_xy=(x, s_.get("y", 0.0)), rk_gr=0.0,
                  rk_mostas=min(s_.get("rk_mostas", 0.7), 0.7))
        return
    senio_mostaguoti(s_, dt, k)
    v_pries = s_["sv_v"]
    v = v_pries + ((x - px) / dt - v_pries) * min(1.0, dt * 15)  # pelės įvykiai netolygūs – išlyginama
    a = max(-20000.0 * k, min(20000.0 * k, (v - v_pries) / dt))
    L = SENIO_SVYRUOKLE * Ps
    th, om = s_["sv_kampas"], s_["sv_omega"]
    # SENIO_INERCIJA < 1: sunkus, standokas senis – ramiai tempiant atsilenkia 1 langeliu, staigiai – 2
    om += (-(TRAUKA * k / L) * math.sin(th) - 7.0 * om - SENIO_INERCIJA * a / L * math.cos(th)) * dt  # slopinimas ~0,7
    th = max(-0.5, min(0.5, th + om * dt))
    s_.update(sv_x=x, sv_v=v, sv_kampas=th, sv_omega=om)


def senio_mostaguoti(s_, dt, k):
    """Kabančio už šaliko ar krentančio senio rankos mostaguoja. Kabant ramiai – vos kruta (±15°,
    lėtai), tempiant pele – kuo greičiau, tuo smarkiau ir dažniau, krentant – kapanojasi visu mostu."""
    x, y = s_["x"], s_.get("y", 0.0)
    pr = s_.get("rk_xy")
    s_["rk_xy"] = (x, y)
    if pr is None:
        return
    gr = math.hypot(x - pr[0], y - pr[1]) / dt / max(k, 1e-6)
    if gr > 3000:  # peršoko (pagautas kitoje vietoje, iškrito iš dangaus) – ne judesys: ir sena vertė numetama
        s_["rk_gr"] = gr = 0.0
    g = s_.get("rk_gr", 0.0)
    g += (gr - g) * min(1.0, dt * 5)  # pelės įvykiai netolygūs – išlyginama
    s_["rk_gr"] = g
    if s_.get("busena") == "krenta":
        daznis, mostas = 1.7, 2.0
    else:
        j = min(1.0, g / 400)
        daznis, mostas = 0.6 + 1.2 * j, 0.7 + 1.3 * j  # dažniau – rankos mirgėtų
    s_["rk_faze"] = (s_.get("rk_faze", 0.0) + dt * daznis) % 1.0
    s_["rk_mostas"] = mostas


def senio_kabo_kadras(s_):
    """Kabančio (ar krentančio) senio kadras: atsilenkimas pagal švytuoklės kampą (langeliais, piešinio – žiūrint
    į dešinę – koordinatėmis) ir rankų padėtis pagal mostagavimą (senio_mostaguoti)."""
    d = SENIO_SVYRUOKLE * math.sin(s_.get("sv_kampas", 0.0)) * (1 if s_["kryptis"] > 0 else -1)
    puse = SENIO_KABO_KADRAI // 2
    atsil = puse + max(-puse, min(puse, int(round(d))))
    rp = SENIO_KABO_RANKOS // 2
    ranka = rp + max(-rp, min(rp, int(round(s_.get("rk_mostas", 0.0) * math.sin(2 * math.pi * s_.get("rk_faze", 0.0))))))
    return atsil * SENIO_KABO_RANKOS + ranka


def senio_veiksmo_kadras(s_):
    """Kuris piešinys (0/1) dabar rodomas metant ar šaunant."""
    t = s_["t"]
    if s_["busena"] == "meta":
        if t < SEMIMAS:
            return ("semia", 0)
        return ("meta", 0 if t < SEMIMAS + METIMAI[s_.get("jega") or "vidutiniskai"][0] else 1)
    if s_["busena"] == "mojuoja":
        return ("mojuoja", int(t / 0.22) % 2)
    if s_["busena"] == "rankos":
        return ("rankos", int(t / 0.3) % 2)
    if s_["busena"] == "dairosi":
        return ("dairosi", 0)
    laikai = KONFETI_FORMOS[(s_.get("konfeti") or (None, "platus"))[1]][3]
    return ("sauna", 1 if any(0 <= t - l < 0.2 for l in laikai) else 0)


SENIO_KADRO_NR = {k: i for i, k in enumerate(SENIO_KADRAI)}


class Sniegas:
    plociu_praejimas = False  # sąsaja perkuriama su platesnėmis peržiūromis (pritaikyti_perziuru_plocius)
    perziuru_plociai = {}  # (kalba, ribos) → išmatuoti peržiūrų pločiai
    slinkties_stilius_sukurtas = False
    # stabtelėjimų diagnostikos skaitikliai (klasės lygiu – kad Windows žinutė, atėjusi dar prieš __init__ pabaigą,
    # nesukeltų klaidos; += sukuria objekto kintamąjį)
    _ivykiai_n = _zinutes_n = _zinuciu_gylis = 0
    _ivykiai_ms = _zinutes_ms = _gc_ms = 0.0
    _fizikos_dalys = {}  # tik skaitoma; kas kadrą priskiriamas naujas žodynas
    _ekrano_kv = 0

    def __init__(self, root, sumazinta):
        self.root = root
        self.matuoti_darbus()  # diagnostikai: kas užima laiką tarp kadrų (stabtelėjimai)
        self.n = self.ikelti_nustatymus()
        nustatyti_kalba(self.n["kalba"])
        ZURNALAS.ijungtas = self.n["diagnostika"]
        ZURNALAS.rasyti(f"===== PALEISTA {PAVADINIMAS} | Python {platform.python_version()} | "
                        f"{platform.platform()} | {'exe' if SUKOMPILIUOTA else 'pyw'} | nustatymai: {NUSTATYMU_BYLA}")
        root.report_callback_exception = self.tk_klaida
        self.energijos_ribojimas_isjungtas = isjungti_energijos_ribojima()  # prieš antraštę – kad ji tai parodytų
        self.mmcss = mmcss_ijungti()  # tkinter (pagrindinė) gija – ta pati, kuri piešia kadrus
        self.ekrano_ritmas = EkranoRitmas()
        self.vsync_periodas, self.vsync_kas = 0.0, 1
        self.diag_nulis()
        self.diag_nustatymai = dict(self.n)
        self.diag_proc = proceso_busena()
        self.diag_laikas = time.perf_counter()
        self.atidetos = {}
        self.klaida_parodyta = False
        self.saugojimo_klaida_parodyta = False
        self.g = Priemones()

        monitoriai = gauti_monitorius()
        if not monitoriai:
            raise RuntimeError("Nepavyko nustatyti ekranų.")
        self.nustatyti_ekranus(monitoriai)
        self.ekranu_tikrinimas = 0
        self.deklas = None
        self.deklo_ivykiai = []
        self.meniu_komandos = []
        self.meniu_atidarytas = False
        self.tikslus_laikmatis = False

        self.snaiges = []
        self.langai = {}
        self.segmentu_dezes = []
        self.langu_segmentai = []  # (viršus, x1, x2, aukščiai, kairė, st) – matomos langų viršaus dalys
        self.blizgesiai = []
        self.langu_sarasas = []
        self._enum_cb = WNDENUMPROC(self._enum_langas)
        self.langai_judejo = False
        self.paskutinis_langu_skaitymas = 0.0
        self.windows_trynimai = 0  # kiek kartų Windows liepė perdangą perpiešti (rodoma būsenoje)
        self.statiniu_blitas = False  # nejudančias sritis (eglės, žemės ir langų sniegas) vėl nukopijuoti į ekraną
        self.paskutinis_judejimas = 0.0  # kada paskutinį kartą pajudėjo koks nors langas
        self.laukia_pilno_blito = False  # langams nurimus – vienas viso kadro kopijavimas
        self.kurti_langu_kabliukus()
        self.topmost_skaitliklis = 0
        self.statinio_skaitliklis = 0

        # Kas perpieština statiniame sluoksnyje (žemė, langų sniegas, eglės) ir ką nuvalyti nuo ekrano.
        self.pilnas_perpiesimas = True
        self.zemes_nesvaru = False
        self.nesvarus_langai = []
        self.nesvarios_sritys = []
        self.papildomos = []

        self.vejas = 0.0  # tikrasis stiprumas nustatymų vienetais (0–10), ženklas – kryptis
        self.vejo_tikslas = 0.0
        self.vejo_kryptis = random.choice((-1, 1))
        self.vejo_laikas = 0.0
        self.oro_poslinkis = 0.0  # kiek vėjas nunešė turbulencijos raštą (px, artimų snaigių masteliu)
        self.oro_modos = None  # (mastelis, bangos) – perskaičiuojama pasikeitus masteliui
        self.gusio_liko = 0.0  # > 0 – vyksta gūsis
        self.iki_gusio = random.uniform(5, 20)  # pirmas gūsis – netrukus po paleidimo

        self.bumbulai = []
        self.skeveldros = []
        self.pustomos = []  # vėjo pakeltos sniego dalelės („pustymas“) ir bumbuliukų išmuštas sniegas
        self.snaigiu_atlasas = None  # pixel art snaigės, nupieštos vieną kartą; kadre tik kopijuojamos

        self.rodoma = True
        self.vartotojas_paslepe = False  # „Paslėpti viską“ – visa perdanga
        self.pilnas_ekranas = False
        self.kadru_skaitliklis = 0
        self.darbo_ms = 0.0
        self.b_fizika = self.b_buferis = self.b_ekranas = 0.0  # kadro laiko skaidinys (būsenos eilutei)
        self.b_atstatymas = 0.0
        self._atstatymo_ms = 0.0  # paskutinio kadro fono atstatymas (kopijavimas iš statinio buferio), ms
        self.b_kopijos = 0
        self._ekrano_ms, self._ekrano_kv = 0.0, 0  # paskutinio kadro kopijavimas į ekraną: ms ir BitBlt kiekis
        # Išmatuotos kopijavimo į ekraną kainos (slenkantys vidurkiai): vieno mažo stačiakampio ir viso kadro.
        self.kaina_staciakampio = 0.02  # ms; tikslinama kiekvieną dalinį kadrą
        self.kaina_pilno = None         # ms; nežinoma iki pirmo viso kadro kopijavimo
        self.pilni_is_eiles = 0
        # Tas pats fono atstatymui buferyje: vieno stačiakampio ir viso buferio kopijavimo kaina.
        self.kaina_atstatymo = 0.005    # ms
        self.kaina_pilno_atst = None    # ms
        self.pilni_atst_is_eiles = 0
        self.atst_pilno_laikas = 0.0    # kada paskutinį kartą atstatytas visas buferis (kainai patikslinti)
        self.paskutine_klaida = ""

        self.girliandos = []
        self.kurti_perdanga()
        self.kurti_zeme()
        self.kurti_egles()
        self.kurti_girliandas()
        self.kurti_bumbulus()
        self.ekskavatoriai, self.ekskav_daleles, self.ekskav_sprite = [], [], None
        self.seniai, self.senio_sprite, self.senio_hwnd, self.senio_daleles = [], None, set(), []
        self.kurti_ekskavatorius()
        self.kurti_senius()
        self.kurti_snaigiu_atlasa()
        self.fj = Fejerverkai(self.k, self.fejerverku_P(), zeme=self.sniego_pavirsius,
                              vejas=lambda: self.vejas * 12 * self.k)
        self.kitas_fj = self.kitas_fejerverku_laikas(time.time())
        self.kurti_nustatymu_langa()
        self.pritaikyti_kieki(visame_ekrane=True)
        self.diag_antraste()

        self.atnaujinti_autostarto_kelia()
        self.kurti_dekla()
        self.root.after(100, self.tikrinti_deklo_ivykius)
        if sumazinta:
            if self.deklas:
                self.root.withdraw()
            else:
                self.root.iconify()
        else:
            # main() langą paslepia, kol nustatoma piktograma ir sukuriama sąsaja: jei langas pasirodo anksčiau,
            # užduočių juostos mygtukas sukuriamas su tkinter plunksna ir ji ten lieka iki kito parodymo.
            self.root.deiconify()

        # Be to Windows laikmačio žingsnis ~15,6 ms – kadrai ateina netolygiai ir sniegas trūkčioja.
        self.laikmacio_tikslumas(True)
        self.paskutinis = self.kitas_kadras = time.perf_counter()
        self.root.after(50, self.kadras)
        # Paleidimas (langai, atlasai, pirmas pilnas perpiešimas) užtrunka ir iškreiptų pirmąją suvestinę
        # (didžiausias vėlavimas ~140 ms, mažiau kadrų per sekundę) – matuojama tik nuo 3-osios sekundės.
        self.root.after(3000, self.diag_po_paleidimo)
        self.root.after(100, self.atnaujinti_langus)
        self.root.after(60000, self.diagnostikos_suvestine)
        self.root.after(1000, self.atnaujinti_busena)

    # ------------------------------------------------------------ nustatymai

    def ikelti_nustatymus(self, importuojama=None):
        """Kiekvienas raktas tikrinamas atskirai: netinkama reikšmė pakeičiama numatytąja, skaičiai apribojami.
        importuojama – naudotojo pasirinkta byla (Importuoti…): jos neperskaičius grąžinama None (nieko nekeičiama)."""
        n = numatytieji()
        # Jei savo bylos dar nėra, bet šalia programos padėti (tik skaitymui) nustatymai – pradedame nuo jų.
        byla = NUSTATYMU_BYLA if importuojama is None else Path(importuojama)
        if importuojama is None and not byla.exists() and byla != VIETINE_BYLA and VIETINE_BYLA.exists():
            byla = VIETINE_BYLA
        if importuojama is None and not byla.exists():
            return n
        try:
            # utf-8-sig – priima ir bylą su BOM (pvz. išsaugotą PowerShell 5.1 ar Notepad)
            duom = json.loads(byla.read_text(encoding="utf-8-sig"))
            if not isinstance(duom, dict):
                raise ValueError("ne JSON objektas")
        except Exception as e:
            if importuojama is not None:
                messagebox.showerror(PAVADINIMAS, T("Nepavyko perskaityti nustatymų bylos:") + f"\n\n{byla}\n\n{e!r}")
                return None
            atsargine = ""
            if byla == NUSTATYMU_BYLA:  # sugadinta byla neperrašoma be pėdsakų – pasiliekama „.bad“ kopija
                try:
                    byla.replace(byla.with_suffix(byla.suffix + ".bad"))
                    atsargine = f"\n\n→ {byla.name}.bad"
                except OSError:
                    pass
            messagebox.showwarning(PAVADINIMAS, T("Nepavyko perskaityti nustatymų bylos – naudojami numatytieji.")
                                   + f"\n\n{byla}\n\n{e!r}{atsargine}")
            return n
        blogi = []
        laisvai = duom.get("be_apribojimu") is True
        ribos = RIBOS_LAISVOS if laisvai else RIBOS
        maks_tipo = MAKS_SNAIGIU_LAISVAI if laisvai else MAKS_SNAIGIU_TIPO
        maks_viso = MAKS_SNAIGIU_LAISVAI if laisvai else MAKS_SNAIGIU_IS_VISO
        for raktas, numatyta in NUMATYTI.items():
            if raktas not in duom:
                continue
            v = duom[raktas]
            try:
                if isinstance(numatyta, list):
                    virsus = maks_tipo if raktas == "tipai" else 1
                    v = [min(virsus, max(0, int(x))) for x in v]
                    if raktas == "bumbulu_rastai" and len(v) < len(numatyta):  # senesnė byla – nauji raštai įjungti
                        v += [1] * (len(numatyta) - len(v))
                    if raktas == "tipai" and len(v) < len(numatyta):  # senose bylose rūšių mažiau – trūkstamos numatytais
                        v += numatyta[len(v):]
                    if len(v) != len(numatyta):
                        raise ValueError
                    if raktas == "tipai" and sum(v) > maks_viso:  # proporcingai sumažinama iki ribos
                        v = [x * maks_viso // sum(v) for x in v]
                elif isinstance(numatyta, bool):
                    if not isinstance(v, bool):
                        raise ValueError
                elif isinstance(numatyta, int):
                    nuo, iki = ribos[raktas]
                    v = min(iki, max(nuo, int(v)))
                    if raktas == "fps":  # tik 30, 60 arba 120 (kadrai sinchronizuojami su ekranu)
                        v = 120 if v >= 90 else 60 if v >= 45 else 30
                elif raktas in TEKSTINES_REIKSMES and v not in TEKSTINES_REIKSMES[raktas]:
                    raise ValueError
                n[raktas] = v
            except (TypeError, ValueError, OverflowError):
                blogi.append(raktas)
        n["egliu_plotis_min"] = egliu_plocio_zingsnis(n["egliu_plotis_min"])  # sena byla (60–100) – elgsena ta pati
        if blogi:
            if importuojama is None:  # paleidžiant – jau vartotojo kalba (importuojant – dabartine sąsajos kalba)
                nustatyti_kalba(n["kalba"])
            messagebox.showwarning(PAVADINIMAS, T("Kai kurie nustatymai byloje netinkami – jiems naudojamos numatytosios reikšmės:")
                                   + f"\n{', '.join(blogi)}\n\n{byla}")
        return n

    def issaugoti(self):
        """Atomiškai: laikina byla įrašoma iki disko (fsync) ir pakeičia senąją. Jei bylą trumpam laiko atidariusi
        kita programa (antivirusinė, OneDrive, paieškos indeksas), keitimas pakartojamas."""
        self.atnaujinti_paruostukus()  # bet koks pakeitimas (ir ne per pakeista()) – paruoštuko žymė teisinga
        laikina = NUSTATYMU_BYLA.with_suffix(NUSTATYMU_BYLA.suffix + ".tmp")
        try:
            with open(laikina, "w", encoding="utf-8") as f:
                f.write(json.dumps(self.n, ensure_ascii=False, indent=2))
                f.flush()
                os.fsync(f.fileno())
            for bandymas in range(4):
                try:
                    laikina.replace(NUSTATYMU_BYLA)
                    break
                except PermissionError:
                    if bandymas == 3:
                        raise
                    time.sleep(0.05)
        except Exception as e:
            try:
                laikina.unlink(missing_ok=True)
            except OSError:
                pass
            ZURNALAS.rasyti(f"KLAIDA: nepavyko išsaugoti nustatymų {NUSTATYMU_BYLA}: {e!r}")
            if not self.saugojimo_klaida_parodyta:
                self.saugojimo_klaida_parodyta = True
                messagebox.showerror(PAVADINIMAS,
                                     T("Nepavyko išsaugoti nustatymų. Gal programos aplankas tik skaitymui?")
                                     + f"\n\n{NUSTATYMU_BYLA}\n\n{e!r}")

    def atideti(self, vardas, ms, funkcija):
        senas = self.atidetos.get(vardas)
        if senas:
            self.root.after_cancel(senas)
        self.atidetos[vardas] = self.root.after(ms, funkcija)

    # ------------------------------------------------------------ perdanga ir buferiai

    def nustatyti_ekranus(self, monitoriai):
        self.monitoriai = monitoriai
        self.vx = min(m[0][0] for m in monitoriai)
        self.vy = min(m[0][1] for m in monitoriai)
        self.vw = max(m[0][2] for m in monitoriai) - self.vx
        self.vh = max(m[0][3] for m in monitoriai) - self.vy
        pagrindinis = next((m for m in monitoriai if m[0][0] <= 0 < m[0][2] and m[0][1] <= 0 < m[0][3]), monitoriai[0])
        self.k = max(1.0, (pagrindinis[0][3] - pagrindinis[0][1]) / 1080)
        self.P = max(2, int(round(2.4 * self.k)))  # pixel art „pikselio“ dydis ekrane

    def kurti_kadro_buferius(self):
        # Du viso ekrano buferiai: statinis (žemė, langų sniegas, eglės) ir kadro (statinis + snaigės).
        wdc = user32.GetDC(self.piesimo_hwnd)
        try:
            self.sdc = gdi32.CreateCompatibleDC(wdc)
            self.fdc = gdi32.CreateCompatibleDC(wdc)
            self.sbmp = gdi32.CreateCompatibleBitmap(wdc, self.vw, self.vh)
            self.fbmp = gdi32.CreateCompatibleBitmap(wdc, self.vw, self.vh)
        finally:
            user32.ReleaseDC(self.piesimo_hwnd, wdc)
        if not (self.sdc and self.fdc and self.sbmp and self.fbmp):
            for bmp in (self.sbmp, self.fbmp):
                if bmp:
                    gdi32.DeleteObject(bmp)
            for dc in (self.sdc, self.fdc):
                if dc:
                    gdi32.DeleteDC(dc)
            self.buferiai = False
            raise RuntimeError("Nepavyko sukurti piešimo buferių (per mažai atminties?).")
        self.buferiai = True
        self.s_senas = gdi32.SelectObject(self.sdc, self.sbmp)
        self.f_senas = gdi32.SelectObject(self.fdc, self.fbmp)
        self.statinis = GdiPiesejas(self.g, self.sdc)

    def naikinti_kadro_buferius(self):
        if not getattr(self, "buferiai", False):
            return
        self.buferiai = False
        gdi32.SelectObject(self.sdc, self.s_senas)
        gdi32.SelectObject(self.fdc, self.f_senas)
        gdi32.DeleteObject(self.sbmp)
        gdi32.DeleteObject(self.fbmp)
        gdi32.DeleteDC(self.sdc)
        gdi32.DeleteDC(self.fdc)

    def tikrinti_ekranus(self):
        """Prijungus/atjungus monitorių ar pakeitus skiriamąją gebą – viskas perkuriama naujiems matmenims."""
        monitoriai = gauti_monitorius()
        if not monitoriai or (monitoriai == self.monitoriai and not getattr(self, "ekranu_klaida", False)):
            return
        # Jei patys ekranai tie patys, o pasikeitė tik darbo sritis (užduočių juosta) – sniegas apačioje
        # išsaugomas, eglės lieka vietose (jų išdėstymą lemia sėkla), perkuriamas tik pagrindas.
        self.ekranu_perkurimai = getattr(self, "ekranu_perkurimai", 0) + (1 if self.monitoriai else 0)
        tie_patys = bool(self.monitoriai) and [m for m, _ in monitoriai] == [m for m, _ in self.monitoriai]
        ZURNALAS.rasyti(f"ĮVYKIS: ekranai pasikeitė ({'tik darbo sritis' if tie_patys else 'perkuriama viskas'}): "
                        f"{self.diag_ekranai()} -> {self.diag_ekranai(monitoriai)}")
        senas_sniegas = list(self.aukstis) if tie_patys else None
        senas_kelias = list(getattr(self, "kelias", ())) if tie_patys else None
        self.nustatyti_ekranus(monitoriai)
        self.perdanga.geometry(f"{self.vw}x{self.vh}+{self.vx}+{self.vy}")
        self.taikyti_stilius()
        self.naikinti_kadro_buferius()
        try:
            self.kurti_kadro_buferius()
        except Exception:
            # po 2 s bandysime dar kartą; self.monitoriai lieka galiojantis (jį naudoja ir kiti metodai)
            self.ekranu_klaida = True
            raise
        self.ekranu_klaida = False
        self.langai, self.skeveldros, self.nesvarus_langai = {}, [], []
        self.pustomos = []
        self.segmentu_dezes = []
        self.langu_segmentai = []
        self.blizgesiai = []
        self.nesvarios_sritys = []
        self.kurti_zeme()
        if senas_sniegas is not None and len(senas_sniegas) == len(self.aukstis):
            self.aukstis = [v if b is not None else 0.0 for v, b in zip(senas_sniegas, self.pagrindas)]
            if senas_kelias is not None and len(senas_kelias) == len(self.kelias):
                self.kelias = [v if b is not None else 0.0 for v, b in zip(senas_kelias, self.pagrindas)]
        self.kurti_egles()
        self.kurti_girliandas()
        self.kurti_bumbulus()
        self.kurti_ekskavatorius()
        self.kurti_senius()
        self.kurti_snaigiu_atlasa()
        self.fj.sustabdyti()
        self.fj.k, self.fj.P = self.k, self.fejerverku_P()
        self.pritaikyti_kieki(perkurti=True)
        self.papildomos = []
        self.pilnas_perpiesimas = True

    def kurti_perdanga(self):
        o = tk.Toplevel(self.root)
        o.overrideredirect(True)
        o.configure(bg=PERMATOMA)
        o.geometry(f"{self.vw}x{self.vh}+{self.vx}+{self.vy}")
        o.attributes("-transparentcolor", PERMATOMA)
        o.attributes("-topmost", True)
        o.update()
        self.perdanga = o
        # Išorinis (viršutinio lygio) langas. Jei tkinter jo nepasakytų – ieškome per Windows, kad stiliai
        # (permatomumas, „kiaurai spustelėjama“) nebūtų tyliai taikomi langui 0.
        try:
            self.perdangos_hwnd = int(o.wm_frame(), 16)
        except (ValueError, tk.TclError):
            self.perdangos_hwnd = 0
        if not self.perdangos_hwnd:
            self.perdangos_hwnd = user32.GetAncestor(o.winfo_id(), GA_ROOT) or o.winfo_id()
        self.piesimo_hwnd = o.winfo_id()
        self.taikyti_stilius()
        self.pilnas_blitas = False
        self.blito_laikas = 0.0
        # Kai Windows liepia perpiešti perdangą (pvz., tempiant langus), tkinter užpildydavo ją fono spalva –
        # t. y. ištrindavo viską, kas nupiešta. Perimame WM_PAINT: tkinter jo nebegauna, o mes iš karto
        # nukopijuojame visą paruoštą kadrą.
        self._lango_proc = WNDPROC(self._perdangos_procedura)
        self._senoji_proc = SetWindowLong(self.piesimo_hwnd, GWLP_WNDPROC,
                                          ctypes.cast(self._lango_proc, ctypes.c_void_p).value)
        # Tą patį darome ir išoriniam tkinter „rėmo“ langui: jo perpiešimas taip pat galėjo ištrinti vaizdą
        # (labiausiai matėsi eglėse – jos vienintelės niekada pačios nepersipiešia).
        self._remo_proc = WNDPROC(self._remo_procedura)
        self._senoji_remo_proc = None
        if self.perdangos_hwnd and self.perdangos_hwnd != self.piesimo_hwnd:
            self._senoji_remo_proc = SetWindowLong(self.perdangos_hwnd, GWLP_WNDPROC,
                                                   ctypes.cast(self._remo_proc, ctypes.c_void_p).value)

        self.kurti_kadro_buferius()

    def _perdangos_procedura(self, hwnd, zinute, wparam, lparam):
        return self._matuota_zinute(self._perdangos_procedura_, hwnd, zinute, wparam, lparam)

    def _remo_procedura(self, hwnd, zinute, wparam, lparam):
        return self._matuota_zinute(self._remo_procedura_, hwnd, zinute, wparam, lparam)

    def _matuota_zinute(self, proc, hwnd, zinute, wparam, lparam):
        """Perdangos langų žinutės su tkinter apdorojimu (CallWindowProc) – kiek laiko užima (diagnostikai)."""
        self._zinuciu_gylis += 1
        t0 = time.perf_counter()
        try:
            return proc(hwnd, zinute, wparam, lparam)
        finally:
            self._zinuciu_gylis -= 1
            if not self._zinuciu_gylis:  # tik išorinė – įdėtinės jau įskaičiuotos
                self._zinutes_n += 1
                self._zinutes_ms += (time.perf_counter() - t0) * 1000

    def _perdangos_procedura_(self, hwnd, zinute, wparam, lparam):
        try:
            if zinute == WM_TASKBARCREATED and WM_TASKBARCREATED:  # jei rėmo lango nėra – žinutė ateina čia
                self.deklas_atkurti = True
            if zinute == WM_ERASEBKGND:
                return 1
            if zinute == WM_PAINT:
                user32.ValidateRect(hwnd, None)
                self.blitas_po_trynimo()
                self.windows_trynimai += 1
                return 0
            if zinute == WM_DEKLAS:
                # Čia negalima kviesti tkinter (įskaitant root.after): lango procedūra vykdoma tkinter įvykių
                # ciklo viduje, ir toks kvietimas užstringa ar nulaužia programą. Tik pažymime – apdoroja
                # tikrinti_deklo_ivykius().
                pele = lparam & 0xFFFF
                if pele in (WM_LBUTTONUP, WM_RBUTTONUP, WM_MBUTTONUP):
                    self.deklo_ivykiai.append(pele)
                return 0
        except Exception:
            pass
        return user32.CallWindowProcW(self._senoji_proc, hwnd, zinute, wparam, lparam)

    def _remo_procedura_(self, hwnd, zinute, wparam, lparam):
        try:
            if zinute == WM_TASKBARCREATED and WM_TASKBARCREATED:
                self.deklas_atkurti = True  # tik pažymime – tkinter / Shell čia nekviečiame (žr. WM_DEKLAS)
            if zinute == WM_ERASEBKGND:
                return 1
            if zinute == WM_PAINT:
                user32.ValidateRect(hwnd, None)
                self.blitas_po_trynimo()
                self.windows_trynimai += 1
                return 0
        except Exception:
            pass
        return user32.CallWindowProcW(self._senoji_remo_proc, hwnd, zinute, wparam, lparam)

    _piesiama = False  # kadras šiuo metu piešiamas į buferį (jis dar nebaigtas – į ekraną nekopijuoti)

    def blitas_po_trynimo(self):
        """Windows liepė perpiešti perdangą (WM_PAINT) – paruoštas kadras į ekraną kopijuojamas iškart, o ne kitame
        kadre (iki 33 ms): tiek laiko perdanga būdavo tuščia ir sumirksėdavo. Čia tik GDI, ne tkinter."""
        if self._piesiama or not getattr(self, "buferiai", None) or not getattr(self, "rodoma", False):
            self.pilnas_blitas = True
            return
        wdc = user32.GetDC(self.piesimo_hwnd)
        if not wdc:
            self.pilnas_blitas = True
            return
        try:
            gdi32.BitBlt(wdc, 0, 0, self.vw, self.vh, self.fdc, 0, 0, SRCCOPY)
        finally:
            user32.ReleaseDC(self.piesimo_hwnd, wdc)

    def atstatyti_lango_procedura(self):
        if getattr(self, "_senoji_proc", None):
            SetWindowLong(self.piesimo_hwnd, GWLP_WNDPROC, self._senoji_proc)
            self._senoji_proc = None
        if getattr(self, "_senoji_remo_proc", None):
            SetWindowLong(self.perdangos_hwnd, GWLP_WNDPROC, self._senoji_remo_proc)
            self._senoji_remo_proc = None

    # ------------------------------------------------------------ sistemos dėklas (prie laikrodžio)

    def kurti_dekla(self):
        """Piktograma prie laikrodžio: kairys spustelėjimas – nustatymai, dešinys – meniu."""
        try:
            if not getattr(self, "_deklo_ikona", None):
                kelias = Path(tempfile.gettempdir()) / f"sniegas_{os.getpid()}.ico"
                kelias.write_bytes(logo_ico())
                try:
                    self._deklo_ikona = user32.LoadImageW(None, str(kelias), IMAGE_ICON,
                                                          user32.GetSystemMetrics(SM_CXSMICON),
                                                          user32.GetSystemMetrics(SM_CYSMICON), LR_LOADFROMFILE)
                finally:
                    kelias.unlink(missing_ok=True)  # piktograma jau atmintyje
                if not self._deklo_ikona:
                    self.deklas = None  # bandysime vėl per kitą tikrinimą
                    return
            d = NOTIFYICONDATAW()
            d.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
            d.hWnd = self.piesimo_hwnd
            d.uID = 1
            d.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
            d.uCallbackMessage = WM_DEKLAS
            d.hIcon = self._deklo_ikona
            d.szTip = PAVADINIMAS + "\n" + T("Vidurinis pelės mygtukas – paslėpti / rodyti")
            ok = shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(d))
            if not ok:
                # Užimta užduočių juosta (pvz. prisijungiant) NIM_ADD gali grąžinti klaidą, nors piktograma jau
                # pridėta – tada pakartotinis NIM_ADD visada nepavyktų. Patikriname per NIM_MODIFY.
                ok = shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(d))
            self.deklas = d if ok else None
        except Exception:
            self.deklas = None

    def tikrinti_dekla(self):
        # Persikrovus explorer.exe piktograma dingsta – tada NIM_MODIFY nepavyksta ir ją pridedame iš naujo.
        # Paleidus kartu su Windows užduočių juosta gali būti dar neparengta – tada bandome vėl.
        if self.deklas:
            self.deklas.uFlags = NIF_TIP
            if shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(self.deklas)):
                return
            ZURNALAS.rasyti("ĮVYKIS: piktograma prie laikrodžio dingo (persikrovė explorer.exe?) – kuriama iš naujo")
        self.kurti_dekla()

    def naikinti_dekla(self):
        if self.deklas:
            shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(self.deklas))
            self.deklas = None
        if getattr(self, "_deklo_ikona", None):
            user32.DestroyIcon(self._deklo_ikona)
            self._deklo_ikona = None

    def deklo_pranesimas(self, tekstas):
        if not self.deklas:
            return
        d = self.deklas
        d.uFlags = NIF_INFO
        d.szInfoTitle = "Sniegas"
        d.szInfo = tekstas
        shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(d))

    def rodyti_nustatymus(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def tikrinti_deklo_ivykius(self):
        # Kitas tikrinimas suplanuojamas visada (finally) – viena klaida neturi visam laikui „atjungti“ piktogramos.
        try:
            while self.deklo_ivykiai:
                pele = self.deklo_ivykiai.pop(0)
                if pele == WM_LBUTTONUP:
                    self.rodyti_nustatymus()
                elif pele == WM_RBUTTONUP:
                    self.deklo_meniu()
                elif pele == WM_MBUTTONUP:  # vidurinis – greitai paslėpti / rodyti viską
                    self.perjungti_rodyma()
                elif pele == "i_dekla":
                    self.i_dekla()
            while self.meniu_komandos:
                komanda = self.meniu_komandos.pop(0)
                if komanda == 1:
                    self.rodyti_nustatymus()
                elif komanda == 2:
                    self.perjungti_sniega()
                elif komanda == 4:
                    self.perjungti_rodyma()
                elif komanda == 5:
                    self.nuvalyti()
                elif komanda == 3:
                    self.baigti()
        except Exception as e:
            self.klaida(e)
        finally:
            if not getattr(self, "baigiama", False):
                self.root.after(100, self.tikrinti_deklo_ivykius)

    def deklo_meniu(self):
        if self.meniu_atidarytas:
            return
        self.meniu_atidarytas = True
        tekstai = (T("Nustatymai…"), T("Įjungti sniegą" if self.sniegas_isjungtas else "Išjungti sniegą"),
                   T("Rodyti viską" if self.vartotojas_paslepe else "Paslėpti viską"), T("Išjungti"),
                   T("Nuvalyti sniegą"))
        threading.Thread(target=self._meniu_gija, args=(tekstai,), daemon=True).start()

    def _meniu_gija(self, tekstai):
        """Windows meniu prie piktogramos – atskiroje gijoje su savo nematomu langu.
        Meniu yra modalinis: tkinter gijoje jis sustabdytų sniegą, kol atidarytas. Pasirinkimą perduodame
        per meniu_komandos sąrašą; tkinter iš šios gijos nekviečiame."""
        komanda, langas, meniu = 0, None, None
        try:
            langas = user32.CreateWindowExW(0, "STATIC", "", WS_POPUP, 0, 0, 0, 0, None, None, None, None)
            meniu = user32.CreatePopupMenu()
            user32.AppendMenuW(meniu, MF_STRING, 1, tekstai[0])
            user32.AppendMenuW(meniu, MF_STRING, 2, tekstai[1])
            user32.AppendMenuW(meniu, MF_STRING, 4, tekstai[2])
            user32.AppendMenuW(meniu, MF_STRING, 5, tekstai[4])
            user32.AppendMenuW(meniu, MF_SEPARATOR, 0, None)
            user32.AppendMenuW(meniu, MF_STRING, 3, tekstai[3])
            taskas = wintypes.POINT()
            user32.GetCursorPos(ctypes.byref(taskas))
            # be šito meniu neužsidarytų spustelėjus šalia jo (žinoma Windows dėklo meniu ypatybė)
            user32.SetForegroundWindow(langas)
            komanda = user32.TrackPopupMenu(meniu, TPM_RETURNCMD | TPM_RIGHTBUTTON | TPM_NONOTIFY,
                                            taskas.x, taskas.y, 0, langas, None)
            user32.PostMessageW(langas, 0, 0, 0)
        except Exception:
            pass
        finally:
            if meniu:
                user32.DestroyMenu(meniu)
            if langas:
                user32.DestroyWindow(langas)
            if komanda:
                self.meniu_komandos.append(komanda)
            self.meniu_atidarytas = False

    def uzdaryti_langa(self):
        """Išjungimo mygtukas (X): pagal nustatymą klausia, slepia į dėklą arba baigia. Be dėklo piktogramos – baigia."""
        if not self.deklas:
            self.baigti()
            return
        veiksmas = self.n["kryzelis"]
        if veiksmas == "klausti":
            veiksmas = self.klausti_uzdarant()
        if veiksmas == "baigti":
            self.baigti()
        elif veiksmas == "deklas":
            self.i_dekla()

    def klausti_uzdarant(self):
        """Mažas langas: į dėklą / baigti / atšaukti, su „Daugiau neklausti“. Grąžina veiksmą arba None."""
        senas = getattr(self, "_uzdarymo_klausimas", None)
        if senas is not None and senas.winfo_exists():  # jau atvertas – tik iškeliame
            senas.lift()
            senas.focus_force()
            return None
        d = self._uzdarymo_klausimas = tk.Toplevel(self.root)
        d.title(PAVADINIMAS)
        d.resizable(False, False)
        d.transient(self.root)
        rez = {"veiksmas": None}
        neklausti = tk.BooleanVar(value=False)
        f = ttk.Frame(d, padding=14)
        f.pack(fill="both", expand=True)
        ttk.Label(f, text=T("Ką daryti paspaudus išjungimo mygtuką?"), font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Label(f, text=T("Sistemos dėkle sniegas veikia toliau – nustatymus atversite\n"
                            "spustelėję piktogramą prie laikrodžio."), foreground="#555555").pack(anchor="w", pady=(4, 10))
        mygtukai = ttk.Frame(f)
        mygtukai.pack(fill="x")

        def baigti(veiksmas):
            rez["veiksmas"] = veiksmas
            d.destroy()

        pirmas = ttk.Button(mygtukai, text=T("Į sistemos dėklą"), command=lambda: baigti("deklas"))
        pirmas.pack(side="left")
        ttk.Button(mygtukai, text=T("Išjungti programą"), command=lambda: baigti("baigti")).pack(side="left", padx=6)
        ttk.Button(mygtukai, text=T("Atšaukti"), command=lambda: baigti(None)).pack(side="left")
        ttk.Checkbutton(f, text=T("Daugiau neklausti (pakeisti galima skiltyje „Kita“)"),
                        variable=neklausti).pack(anchor="w", pady=(10, 0))
        d.protocol("WM_DELETE_WINDOW", lambda: baigti(None))
        d.bind("<Escape>", lambda e: baigti(None))
        d.bind("<Return>", lambda e: baigti("deklas"))
        d.update_idletasks()
        d.geometry("+%d+%d" % self.dialogo_vieta(d.winfo_reqwidth(), d.winfo_reqheight()))
        pirmas.focus_set()
        d.grab_set()
        self.root.wait_window(d)
        if rez["veiksmas"] and neklausti.get():
            self.n["kryzelis"] = rez["veiksmas"]
            self.kryzelio_kint.set(T(KRYZELIO_TEKSTAI[KRYZELIO_VEIKSMAI.index(rez["veiksmas"])]))
            self.issaugoti()
        return rez["veiksmas"]

    def i_dekla(self):
        if not self.deklas:
            return
        self.root.withdraw()
        if not getattr(self, "_pranesta_apie_dekla", False):
            self._pranesta_apie_dekla = True
            self.deklo_pranesimas(T("Sniegas veikia toliau. Nustatymai ir išjungimas – per piktogramą prie laikrodžio."))

    def atlaisvinti_buferius(self):
        self.naikinti_ekskavatorius()
        self.naikinti_senius()
        try:
            # DC naikinami pirma – tada į juos parinkti pieštukai/teptukai atlaisvinami ir juos galima ištrinti
            self.naikinti_kadro_buferius()
            self.naikinti_bumbulus()
            self.naikinti_snaigiu_atlasa()
            self.g.naikinti()
        except Exception:
            pass

    def naujas_dc(self, plotis, aukstis):
        wdc = user32.GetDC(self.piesimo_hwnd)
        try:
            dc = gdi32.CreateCompatibleDC(wdc)
            bmp = gdi32.CreateCompatibleBitmap(wdc, plotis, aukstis)
        finally:
            user32.ReleaseDC(self.piesimo_hwnd, wdc)
        if not bmp:  # per didelis – kitaip tas efektas tiesiog tyliai nesimatytų
            ZURNALAS.rasyti(f"KLAIDA: nepavyko sukurti {plotis}×{aukstis} paveikslėlio (per mažai atminties?)", visada=True)
        senas = gdi32.SelectObject(dc, bmp)
        user32.FillRect(dc, ctypes.byref(wintypes.RECT(0, 0, plotis, aukstis)), self.g.teptukas(SPRAITO_FONAS))
        return {"dc": dc, "bmp": bmp, "senas": senas}

    @staticmethod
    def naikinti_dc(d):
        gdi32.SelectObject(d["dc"], d["senas"])
        gdi32.DeleteObject(d["bmp"])
        gdi32.DeleteDC(d["dc"])

    def kurti_snaigiu_atlasa(self):
        """Pixel art snaigės nupiešiamos vieną kartą į atminties juostą (atlasą); kadre jos tik kopijuojamos.
        Padėtis NEprilyginama prie „pikselių“ tinklelio – snaigė juda po 1 tašką, todėl krenta tolygiai."""
        self.naikinti_snaigiu_atlasa()
        if self.n["snaigiu_stilius"] != "pikseliai":
            self.kurti_iprastu_atlasa()
            return
        # „Pikselis“ gali būti trupmeninis (pvz. 1,5 taško): langelių ribos apvalinamos, todėl dydis tikslus
        # bet kokiame ekrane, tik kai kurie langeliai 1 tašku siauresni.
        P = max(1.0, PIKS_SNAIGES_LANGELIS * self.k * self.n["dydis"] / 100)
        # Mažas pikselinis piešinys sklandžiai pasuktas virsta dėme, todėl sukama šuoliukais: du piešiniai.
        kadrai = [[rastas] + ([PIKS_SNAIGES_PASUKTOS[i]] if i in PIKS_SNAIGES_PASUKTOS else [])
                  for i, rastas in enumerate(PIKS_SNAIGES)]
        vietos, x = [], 0
        for tipo_kadrai in kadrai:
            sar = []
            for rastas in tipo_kadrai:
                w, h = round(len(rastas[0]) * P), round(len(rastas) * P)
                sar.append((x, w, h))
                x += w + 2
            vietos.append(sar)
        a = self.naujas_dc(x, max(v[2] for sar in vietos for v in sar))
        p = GdiPiesejas(self.g, a["dc"])
        for tipas, (sar, tipo_kadrai) in enumerate(zip(vietos, kadrai)):
            for (ax, w, h), rastas in zip(sar, tipo_kadrai):
                piks_piesti(p, piks_tinklelis(rastas, {"W": TIPU_SPALVOS[tipas]}), ax, 0, P)
        a["vietos"] = vietos
        self.snaigiu_atlasas = a

    def kurti_iprastu_atlasa(self):
        """Įprastos snaigės irgi nupiešiamos iš anksto – su šešėliu, visi SUKIMO_KADRAI posūkiai. Kadre vietoj
        keturių GDI kvietimų (2× SetViewportOrgEx + 2× Polyline/Ellipse) – vienas TransparentBlt (matuota:
        1000 snaigių piešimas ~14,6 ms). Dydis suapvalinamas iki žingsnio (0,5 px; dideliems – stambesnio),
        pradinis pasukimas – iki artimiausio kadro (akimi neatskiriama). Ko atlase nėra – piešiama kaip anksčiau."""
        dk0 = self.k * self.n["dydis"] / 100
        langeliai = []  # (tipas, kadrų taškai arba None (taškas), skersmuo, c – centras langelyje, plotis)
        vietos = {}
        plotas, MAKS_PLOTAS = 0, 6_000_000  # ~24 MB; didžiulės (išplėstos ribos) snaigės – tiesiogiai, be atlaso
        for tipas, (_, rusis, forma) in enumerate(TIPAI):
            pries = len(langeliai)
            if rusis in ("kristalas", "kontura"):
                r0, simetrija = forma[0], forma[1]
                lo, hi = r0 * dk0 * 0.85, r0 * dk0 * 1.15
                zingsnis = max(0.5, round(hi * 0.04 * 2) / 2)  # dideliems – stambesnis, kad atlasas neišpūstų
                periodas = 2 * math.pi / simetrija
                mapa = {}
                for q in range(max(1, int(lo / zingsnis)), int(math.ceil(hi / zingsnis)) + 1):
                    r = q * zingsnis
                    d = int(math.ceil(r * (1.1 if rusis == "kontura" else 1.0))) + 1
                    kadrai = [[int(round(v)) for v in formos_taskai(rusis, forma, r, periodas * k_ / SUKIMO_KADRAI)]
                              for k_ in range(SUKIMO_KADRAI)]
                    mapa[q] = len(langeliai)
                    langeliai.append((tipas, kadrai, 0, d + 1, 2 * d + 4))
                vietos[tipas] = (zingsnis, mapa)
            else:
                lo, hi = forma * dk0 * 0.85, forma * dk0 * 1.15
                mapa = {}
                for D in range(max(1, int(round(2 * lo))), max(1, int(round(2 * hi))) + 1):
                    d = D // 2 + 2
                    mapa[D] = len(langeliai)
                    langeliai.append((tipas, None, D, d + 1, 2 * d + 4))
                vietos[tipas] = (0, mapa)
            naujas = sum((len(l_[1]) if l_[1] else 1) * l_[4] * l_[4] for l_ in langeliai[pries:])
            if plotas + naujas > MAKS_PLOTAS:
                del langeliai[pries:]
                del vietos[tipas]
            else:
                plotas += naujas
        # išdėstymas eilėmis (ne viena labai ilga juosta)
        EIL_PLOTIS = 4096
        x = y = eil_h = plotis = 0
        padetys = []
        for tipas, kadrai, D, c, w in langeliai:
            kiek = len(kadrai) if kadrai else 1
            sar = []
            for _ in range(kiek):
                if x + w > EIL_PLOTIS:
                    x, y, eil_h = 0, y + eil_h + 1, 0
                sar.append((x, y))
                x += w + 1
                eil_h = max(eil_h, w)
                plotis = max(plotis, x)
            padetys.append(sar)
        if not langeliai:
            return
        a = self.naujas_dc(plotis, y + eil_h)
        dc, g = a["dc"], self.g
        for (tipas, kadrai, D, c, w), sar in zip(langeliai, padetys):
            for poslinkis, spalva in ((1, SNAIGES_SESELIS), (0, TIPU_SPALVOS[tipas])):
                gdi32.SelectObject(dc, g.piestukas(spalva))
                gdi32.SelectObject(dc, g.teptukas(spalva))
                for i, (ax, ay) in enumerate(sar):
                    ox, oy = ax + c + poslinkis, ay + c + poslinkis
                    if kadrai:
                        pts = kadrai[i]
                        pts = [v + (ox if j % 2 == 0 else oy) for j, v in enumerate(pts)]
                        gdi32.Polyline(dc, (ctypes.c_long * len(pts))(*pts), len(pts) // 2)
                    else:
                        h_ = D // 2
                        if D <= 2:
                            gdi32.PatBlt(dc, ox - h_, oy - h_, D, D, PATCOPY)
                        else:
                            gdi32.Ellipse(dc, ox - h_, oy - h_, ox + D - h_, oy + D - h_)
        a["iprastos"] = {t: (vietos[t][0], {k_: (langeliai[i][4], langeliai[i][3], padetys[i])
                                             for k_, i in vietos[t][1].items()}) if t in vietos else (0, {})
                         for t in range(len(TIPAI))}
        self.snaigiu_atlasas = a

    def naikinti_snaigiu_atlasa(self):
        if self.snaigiu_atlasas:
            self.naikinti_dc(self.snaigiu_atlasas)
            self.snaigiu_atlasas = None

    def permatomas_kopijavimas(self, dydis, kur_x, kur_y, saltinis, sx, sy, x_min=0, x_max=None, y_max=None):
        """TransparentBlt su apkirpimu – už ekrano (ar nurodytų ribų) jis nekopijuoja nieko."""
        r = self.ribos(max(kur_x, x_min), kur_y, min(kur_x + dydis[0], self.vw if x_max is None else x_max),
                       min(kur_y + dydis[1], self.vh if y_max is None else y_max))
        if r is None:
            return None
        l, t, rr, b = r
        msimg32.TransparentBlt(self.fdc, l, t, rr - l, b - t, saltinis, sx + (l - kur_x), sy + (t - kur_y),
                               rr - l, b - t, SPRAITO_FONAS_RGB)
        return r

    def taikyti_stilius(self):
        h = self.perdangos_hwnd
        ex = GetWindowLong(h, GWL_EXSTYLE)
        # LAYERED+TRANSPARENT – pelė eina kiaurai; TOOLWINDOW – nėra Alt+Tab; NOACTIVATE – nevagia fokuso.
        SetWindowLong(h, GWL_EXSTYLE, ex | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE)
        # SWP_SHOWWINDOW – tik kai turi būti matoma: kitaip pasikeitus ekranams per žaidimą perdanga iššoktų
        user32.SetWindowPos(h, HWND_TOPMOST, self.vx, self.vy, self.vw, self.vh,
                            SWP_NOACTIVATE | SWP_FRAMECHANGED | (SWP_SHOWWINDOW if self.rodoma else 0))
        Patarimas.perdanga_iskelta = True

    def laikmacio_tikslumas(self, tikslus):
        # 1 ms laikmatis neleidžia procesoriui „užmigti“ – reikalingas tik kol sniegas rodomas
        if tikslus == self.tikslus_laikmatis:
            return
        self.tikslus_laikmatis = tikslus
        try:
            (winmm.timeBeginPeriod if tikslus else winmm.timeEndPeriod)(1)
        except Exception:
            pass

    def taikyti_matomuma(self):
        rodyti = not (self.vartotojas_paslepe or self.pilnas_ekranas)
        if rodyti == self.rodoma:
            return
        self.rodoma = rodyti
        ZURNALAS.rasyti("ĮVYKIS: " + ("vėl rodoma" if rodyti else
                                     "paslėpta naudotojo" if self.vartotojas_paslepe else
                                     f"pristabdyta – per visą ekraną: {getattr(self, 'diag_pilno_klase', '?')}"))
        self.laikmacio_tikslumas(rodyti)
        if rodyti:
            self.perdanga.deiconify()
            self.taikyti_stilius()
            self.pilnas_perpiesimas = True
            self.paskutinis = self.kitas_kadras = time.perf_counter()
        else:
            self.perdanga.withdraw()
            self.fj.sustabdyti()  # paslėpus šou nutraukiamas, kad nepasirodytų pavėluotai
        for s_ in self.seniai:  # sniego senių pagavimo langeliai – kartu su perdanga
            if s_["busena"] == "kabo" and not rodyti:
                s_.update(busena="krenta", tempimas=None, vx=0.0, vy=0.0)
            self.atnaujinti_senio_langa(s_)

    def ribos(self, l, t, r, b):
        if l < 0:
            l = 0
        if t < 0:
            t = 0
        if r > self.vw:
            r = self.vw
        if b > self.vh:
            b = self.vh
        return (l, t, r, b) if r > l and b > t else None

    # ------------------------------------------------------------ žemė ir eglės

    def kurti_zeme(self):
        S = STULPELIS
        ncol = self.vw // S + 1
        self.pagrindas = [None] * ncol
        for c in range(ncol):
            x = self.vx + c * S + S // 2
            apacia = None
            for m, w in self.monitoriai:
                if m[0] <= x < m[2] and (apacia is None or w[3] > apacia):
                    apacia = w[3]
            self.pagrindas[c] = None if apacia is None else apacia - self.vy
        self.aukstis = [0.0] * ncol
        self.kelias = [0.0] * ncol  # kelio sniegas priešais egles (jį valo buldozeriukai)
        # smulkūs kauburiukai ir patirpimai kelyje (kitaip jis – lygi juosta)
        self.kelio_profilis = kopu_profilis(ncol, kopu_bangos(random, ((45 * self.k, 0.22), (17 * self.k, 0.16))))
        self.zemes_kauke = bytearray(ncol)  # kurie žemės stulpeliai pasikeitė nuo paskutinio perpiešimo
        self.zemes_nesvaru = False
        self.sustumta = bytearray(ncol)  # valytuvų sustumti kauburiai – jų kopų riba nenukerpa
        self.suspausta = [0.0] * ncol  # kada bumbuliukas paskutinį kartą suspaudė stulpelį (vėžė)
        # daugiau ir trumpesnių kalnelių – pusnų buldozeriukai nebevalo
        self.kopu_bangos = kopu_bangos(random, ((140 * self.k, 0.16), (55 * self.k, 0.22), (28 * self.k, 0.06)))
        self.kopu_poslinkis = 0.0
        self.kopu_laikas = 0.0
        self.pustymo_laikas = 0.0
        self.egles = []
        self.skaiciuoti_kopas()
        self.min_pagrindas = min(b for b in self.pagrindas if b is not None)

        self.zemes_ruozai = []
        c = 0
        while c < ncol:
            b = self.pagrindas[c]
            if b is None:
                c += 1
                continue
            c1 = c
            while c < ncol and self.pagrindas[c] == b:
                c += 1
            self.zemes_ruozai.append((c1, c, b))

    def girliandu_Pg(self):
        # Lemputės „pikselis“ – trupmeninis: lemputė didėja tolygiai po 1 px (piks_piesti langelių ribas
        # apvalina). Anksčiau jis buvo sveikas, todėl lemputės ilgai nesikeisdavo, o tada staiga padidėdavo pusantro
        # karto (pvz. 74 → 75 %), kartu ir laidas dvigubai storėjo.
        return max(1.0, self.P * 1.12 * self.n["girliandu_dydis"] / 100)

    def girliandu_telpa(self):
        """Kiek lempučių telpa vienoje pusėje (žemesniame iš kairiausio ir dešiniausio ekrano) dabartiniu dydžiu;
        None – ekranai dar nežinomi. Patarimui ir įspėjimui."""
        monitoriai = getattr(self, "monitoriai", None)
        if not monitoriai or not hasattr(self, "P"):
            return None
        Pg = self.girliandu_Pg()
        kair = min(monitoriai, key=lambda m: m[0][0])
        des = max(monitoriai, key=lambda m: m[0][2])
        return min(girl_telpa(m[1][1], m[1][3], Pg) for m in (kair, des))

    ISPEJIMU_RAKTAI = ("gusio_stiprumas", "girliandu_kiekis", "egliu_min", "egliu_max")

    def ispejimas(self, raktas):
        """Kodėl nustatymas (dalinai) neveikia – tekstas patarimui; None – viskas gerai."""
        n = self.n
        if raktas == "gusio_stiprumas" and gusis_silpnas(n):
            return T("⚠ Gūsis ({g}) silpnesnis už įprastą vėją, kuris pučia iki {v}: gūsiai beveik nesijaus, o stipriai "
                     "pučiant gūsis vėją net susilpnina. Padidinkite „Gūsio stiprumą“ bent iki {n} arba sumažinkite "
                     "„Įprastą vėją“.").format(g=n["gusio_stiprumas"], v=skaicius_tekstu(0.7 * n["vejas"]),
                                               n=math.ceil(0.7 * n["vejas"] - 1e-9))
        if raktas == "girliandu_kiekis" and n["girliandos"]:
            telpa = self.girliandu_telpa()
            if telpa is not None and n["girliandu_kiekis"] > telpa:
                return T("⚠ Nustatyta {k} lempučių, bet šiame ekrane su dydžiu {d} % telpa tik {n} – daugiau nerodoma. "
                         "Sumažinkite dydį arba lempučių kiekį.").format(k=n["girliandu_kiekis"],
                                                                        d=n["girliandu_dydis"], n=telpa)
        if raktas in ("egliu_min", "egliu_max") and n["egles"] and n["egliu_atsitiktinis"] \
                and n["egliu_min"] > n["egliu_max"]:
            return T("⚠ Mažiausias aukštis ({a}) didesnis už didžiausią ({b}) – kitas pakoreguojamas po akimirkos.").format(
                a=n["egliu_min"], b=n["egliu_max"])
        return None

    def atnaujinti_ispejimus(self):
        """Nustatymų, kurių reikšmė (dalinai) neveikia, pavadinimai – ISPEJIMO_SPALVA; kodėl – patarime ant
        pavadinimo, laukelio ir juostos (ispejimas)."""
        et = getattr(self, "etiketes", None)
        if not et:
            return
        for raktas in self.ISPEJIMU_RAKTAI:
            w = et.get(raktas)
            if w is not None:
                try:
                    w.configure(foreground=ISPEJIMO_SPALVA if self.ispejimas(raktas) else "")
                except tk.TclError:
                    pass

    def suderinti_egliu_ribas(self):
        """Mažiausias eglių aukštis didesnis už didžiausią – kitas (ne ką tik keistas) pakoreguojamas, kad sutaptų.
        Ne iškart: renkant skaičių („1“ → „15“ → „150“) tarpinės reikšmės kitos ribos nesugadina."""
        try:
            fokusas = self.root.focus_get()
        except (tk.TclError, KeyError):
            fokusas = None
        if fokusas is not None and fokusas in (self.valdikliai.get("egliu_min"), self.valdikliai.get("egliu_max")):
            self.atideti("egliu_ribos", 600, self.suderinti_egliu_ribas)  # dar renkama – palaukiama
            return
        a, b = self.n["egliu_min"], self.n["egliu_max"]
        if a <= b:
            return
        if self.__dict__.get("paskutine_egliu_riba") == "egliu_max":
            self.kint["egliu_min"].set(str(b))
        else:
            self.kint["egliu_max"].set(str(a))

    def kurti_girliandas(self):
        """Po girliandą kairiausio ekrano kairėje ir dešiniausio – dešinėje, nuo viršaus iki užduočių juostos.
        Laidas – susuktas dvigyslis, ištisinis, prie pat ekrano krašto; lemputės prisegtos prie jo."""
        self.atnaujinti_ispejimus()  # pasikeitė ekranai ar dydis – kiek telpa lempučių
        for g in getattr(self, "girliandos", ()):
            self.nesvarios_sritys.append(g["ribos"])
        self.girliandos = []
        if not self.n["girliandos"] or not self.monitoriai:
            return
        Pg = self.girliandu_Pg()
        d = max(1, int(round(Pg * 0.5)))  # laido gyslos storis
        rnd = random.Random(getattr(self, "egliu_sekla", 0) + 7)
        kair = min(self.monitoriai, key=lambda m: m[0][0])
        des = max(self.monitoriai, key=lambda m: m[0][2])
        pus = GIRL_STORIS * Pg / 2
        for kaire, (_, darbas) in ((True, kair), (False, des)):
            l, t, r, b = darbas[0] - self.vx, darbas[1] - self.vy, darbas[2] - self.vx, darbas[3] - self.vy
            y0, y1 = t + pus + 2 * Pg, b - pus - 3 * Pg
            n_l = min(self.n["girliandu_kiekis"], girl_telpa(t, b, Pg))
            if n_l < 2:
                continue
            tarpas = (y1 - y0) / (n_l - 1)
            laido_x = l + d if kaire else r - 2 * d  # laido vidurys – vos per gyslą nuo krašto
            laidas = []
            vija = 4 * Pg  # susukimo žingsnis
            for y in range(int(t), int(y1 + pus), d):
                faze = math.sin(2 * math.pi * y / vija)
                for zenklas, spalva in ((1, GIRL_LAIDAS), (-1, GIRL_LAIDAS2)):
                    laidas.append((int(laido_x + zenklas * faze * d * 0.9), y, d, spalva))
            vietos = []
            lw, lh = int(math.ceil(GIRL_ILGIS * Pg)), int(math.ceil(GIRL_STORIS * Pg))  # lemputės dydis, px
            for j in range(n_l):
                y = int(round(y0 + j * tarpas))
                x0 = int(laido_x) if kaire else int(round(laido_x - GIRL_ILGIS * Pg + d))
                yb = int(round(y - GIRL_STORIS * Pg / 2))
                spalva = j % len(GIRL_SPALVOS)
                vietos.append((x0, yb, spalva, (x0 - 1, yb - 1, x0 + lw + 1, yb + lh + 1)))
            xs = [x for x, _, _, _ in laidas] + [v[3][0] for v in vietos] + [v[3][2] for v in vietos]
            ribos = (max(0, min(xs) - 2), int(t), min(self.vw, max(xs) + d + 2),
                     max(int(y1 + pus) + d, max(v[3][3] for v in vietos)) + 1)
            g = {"kaire": kaire, "Pg": Pg, "laidas": laidas, "laido_y": [y for _, y, _, _ in laidas],
                 "vietos": vietos, "ribos": ribos,
                 "mirk": girliandos_valdiklis(rnd, len(vietos))}
            self.girliandos.append(g)
            self.nesvarios_sritys.append(ribos)

    def egliu_auksciai_ir_vietos(self, us):
        """(aukščiai, aukščiai išdėstymui): atsitiktinio aukščio – egliu_auksciai pagal ribas, buvusias išdėliojant
        (sėklai pasikeitus – dabartinės); išdėstymas – pagal tas pradines, kad keičiant ribas eglės nesikilnotų."""
        n = self.n
        if not n["egliu_atsitiktinis"]:
            return [float(n["egliu_aukstis"])] * len(us), [float(n["egliu_aukstis"])] * len(us)
        a, b = sorted((n["egliu_min"], n["egliu_max"]))
        ref = self.__dict__.get("_egliu_ref")
        if ref is None or ref[0] != getattr(self, "egliu_sekla", None):
            ref = self._egliu_ref = (getattr(self, "egliu_sekla", None), a, b)
        _, ra, rb = ref
        return egliu_auksciai(us, a, b, ra, rb), [ra + u * (rb - ra) for u in us]

    def kurti_egles(self):
        """Eglės išdėliojamos atsitiktinai per visų ekranų apačią, kiek įmanoma neužgulant viena kitos.
        Išdėstymas priklauso nuo sėklos: perkūrus (pvz. pasikeitus užduočių juostai) eglės lieka savo vietose,
        naujai išdėliojamos tik paspaudus „Išdėlioti iš naujo“."""
        S = STULPELIS
        if not hasattr(self, "egliu_sekla"):
            self.egliu_sekla = random.randrange(1 << 30)
        rnd = random.Random(self.egliu_sekla)
        self.egles = []
        if not self.n["egles"]:
            return
        ruozai = [(c1 * S + 30, c2 * S - 30, b) for c1, c2, b in self.zemes_ruozai if (c2 - c1) * S > 120]
        if not ruozai:
            return
        svoriai = [r - l for l, r, _ in ruozai]
        padetys = []
        # plotis – atskira atsitiktinė seka, kad pločio nustatymas nepakeistų eglių vietų
        rnd_p = random.Random(self.egliu_sekla + 11)
        galimi = egliu_sablonai_pagal_ploti(self.n["egliu_plotis_min"])
        # aukščiai – atskira seka (kaip ir plotis): keičiant ribas eglės nesikilnoja
        rnd_h = random.Random(self.egliu_sekla + 23)
        auksciai, vietai = self.egliu_auksciai_ir_vietos([rnd_h.random() for _ in range(self.n["egliu_kiekis"])])
        for i in range(self.n["egliu_kiekis"]):
            aukstis = auksciai[i]
            sab = rnd_p.choice(galimi)
            plotis = vietai[i] * len(EGLIU_SABLONAI[sab][0]) / len(PIKS_EGLE)
            geriausia = None
            for _bandymas in range(25):
                l, r, b = rnd.choices(ruozai, weights=svoriai)[0]
                x = rnd.uniform(l, r)
                tarpas = min((abs(x - px) - (plotis + pp) / 2 for px, pp, pb in padetys if pb == b), default=1e9)
                if geriausia is None or tarpas > geriausia[0]:
                    geriausia = (tarpas, x, b)
                if tarpas > 0:
                    break
            _, x, b = geriausia
            padetys.append((x, plotis, b))
            self.egles.append(sukurti_piks_egle(x, b, aukstis, rnd, sab))
        self.skaiciuoti_kopas()

    def skaiciuoti_kopas(self):
        """Kiekvieno žemės stulpelio didžiausias sniego aukštis kaip dalis (kopos). Eglės piešiamos sniego
        priekyje, todėl prie jų sniego nekeičiame – jos nebeužpustomos."""
        self.zemes_profilis = kopu_profilis(len(self.aukstis), self.kopu_bangos, self.kopu_poslinkis, kalneliai=True)

    def piesti_sluoksni(self, h, a, b, x0, pagrindas, slenkstis, konturas, spalvos=None):
        """Sniego sluoksnis su faktūra, kad nebūtų vientisas baltas blynas:
        – giliau sniegas melsvesnis (du klodai, jų ribos seka paviršių – matosi, kaip snigo sluoksniais);
        – šviesa iš viršaus kairės, todėl į dešinę besileidžiantys šlaitai – melsvame šešėlyje;
        – viršuje – kontūras (jei įjungtas)."""
        S = STULPELIS
        p = self.statinis
        baltas, klodai, seselis = spalvos or (SNIEGAS, SNIEGO_SLUOKSNIAI, SNIEGO_SESELIS)
        k = self.k
        nh = len(h)
        for c1, c2 in sluoksnio_atkarpos(h, a, b, slenkstis):
            virsus = []
            for q in range(c1, c2):
                virsus.append(x0 + q * S)
                virsus.append(int(pagrindas - h[q]))
            virsus += (x0 + c2 * S, virsus[-1])  # paskutinis stulpelis irgi S pločio
            p.poligonas([x0 + c1 * S, pagrindas] + virsus + [x0 + c2 * S, pagrindas], baltas)
            # klodai: stulpeliai su vienodu viršumi sujungiami į vieną stačiakampį
            for dalis, spalva in ((0.42, klodai[0]), (0.18, klodai[1])):
                pradzia, y0 = None, None
                for q in range(c1, c2 + 1):
                    y = int(pagrindas - h[q] * dalis) if q < c2 and h[q] >= 5 * k else None
                    if y != y0:
                        if y0 is not None:
                            p.staciakampis(x0 + pradzia * S, y0, x0 + q * S, pagrindas, spalva)
                        pradzia, y0 = q, y
            # šešėlis: išlygintas nuolydis per ±3 stulpelius (pavieniai „laipteliai“ nešešėliuojami)
            # (kaimynai imami iš viso masyvo, ne iš perpiešiamos atkarpos – kitaip dalinis perpiešimas skirtųsi)
            for q in range(c1, c2):
                d = h[min(nh - 1, q + 3)] - h[max(0, q - 3)]
                if d < -0.6 * k:
                    gylis = min(h[q] * 0.55, (1.5 + min(8.0, -d * 1.2)) * k)
                    if gylis >= 1:
                        y = int(pagrindas - h[q])
                        p.staciakampis(x0 + q * S, y, x0 + q * S + S, y + int(gylis) + 1, seselis)
            if konturas:
                p.linija(virsus, konturas)

    def egliu_kauke(self):
        """Žemės stulpeliai, kuriuos dengia eglės (bytearray; podėlyje, kol eglės nepasikeitė)."""
        S = STULPELIS
        n = len(self.aukstis)
        raktas = (n, tuple(eg["ribos"] for eg in getattr(self, "egles", ())))
        if self.__dict__.get("_egliu_kauke") is None or self._egliu_kauke[0] != raktas:
            k_ = bytearray(n)
            for el, _, er, _ in raktas[1]:
                for c in range(max(0, int(el // S)), min(n, int(-(-er // S)))):
                    k_[c] = 1
            self._egliu_kauke = (raktas, k_)
        return self._egliu_kauke[1]

    def piesti_kelia(self, a, b, pagr, konturas, p=None):
        """Kelio sniegas (self.kelias) – ištisa balta juosta priešais pusnis (jos – šiek tiek melsvesnės) ir egles.
        Kontūras ir šlaito šešėlis – tik kur kelias aukštesnis už pusnį (ant pusnų jo linijos atrodė kaip šešėlių
        likučiai). Gretimi vienodi stulpeliai sujungiami."""
        S, k = STULPELIS, self.k
        h, kel = self.aukstis, self.kelias
        nh = len(kel)
        p = p or self.statinis
        sluoksniai = [[], [], [], [], []]  # (x1, x2, y1, y2) – baltas, du klodai, šešėlis, kontūras

        def deti(i, c, y1, y2):
            sar = sluoksniai[i]
            if sar and sar[-1][1] == c * S and sar[-1][2] == y1 and sar[-1][3] == y2:
                sar[-1][1] = c * S + S
            else:
                sar.append([c * S, c * S + S, y1, y2])
        for c in range(max(0, a), min(nh, b)):
            v = kel[c]
            if v < 1.0:
                continue
            virsuje = v >= h[c] - 0.5
            virsus = int(pagr - v)
            deti(0, c, virsus, pagr)  # ištisai – kitaip ties eglės ar pusnies kraštu atsirasdavo stačiakampiai
            if v >= 5 * k:
                for i, dalis in ((1, 0.42), (2, 0.18)):
                    y = max(virsus, int(pagr - v * dalis))
                    if y < pagr:
                        deti(i, c, y, pagr)
            if virsuje:
                nuol = kel[min(nh - 1, c + 3)] - kel[max(0, c - 3)]  # kaip piesti_sluoksni
                if nuol < -0.6 * k:
                    gylis = min(v * 0.55, (1.5 + min(8.0, -nuol * 1.2)) * k)
                    if gylis >= 1:
                        deti(3, c, virsus, virsus + int(gylis) + 1)
                if konturas:
                    deti(4, c, virsus, virsus + 1)
        baltas, klodai, seselis = KELIO_SPALVOS
        for i, spalva in enumerate((baltas, klodai[0], klodai[1], seselis, konturas)):
            for x1, x2, y1, y2 in sluoksniai[i]:
                p.staciakampis(x1, y1, x2, y2, spalva)

    def perpiesti_statini(self, sritis):
        """Perpiešia statinį sluoksnį nurodytoje srityje (None – visame ekrane). Grąžina tikrąją sritį."""
        dc = self.sdc
        S = STULPELIS
        if sritis is None:
            l, t, r, b = 0, 0, self.vw, self.vh
        else:
            sritis = self.ribos(*sritis)
            if sritis is None:
                return None
            l, t, r, b = sritis
            gdi32.SaveDC(dc)
            gdi32.IntersectClipRect(dc, l, t, r, b)
        try:
            user32.FillRect(dc, ctypes.byref(wintypes.RECT(l, t, r, b)), self.g.teptukas(PERMATOMA))
            # išjungus sniegą nelieka ir sniego ant šakų
            n_egl = dict(self.n, sniegas_ant_egliu=False) if self.sniegas_isjungtas else self.n
            konturas = SNIEGO_KONTURAS if self.n["sniego_konturas"] else None
            a0, b0 = l // S - 1, r // S + 2
            maks = self.n["max_aukstis"] * self.k + 3
            for c1, c2, pagrindas in self.zemes_ruozai:
                a, bb = max(c1, a0), min(c2, b0)
                if a < bb and pagrindas >= t and pagrindas - maks <= b:
                    self.piesti_sluoksni(self.aukstis, a, bb, 0, pagrindas, 0.7, konturas, PUSNU_SPALVOS)
            # Eglės – pusnų priekyje (kitaip sniegas užkloja apatines šakas), o priešais eglės – kelio sniegas
            for e in self.egles:
                el, et, er, eb = e["ribos"]
                if er > l and el < r and eb > t and et < b:
                    piesti_egle(self.statinis, e, n_egl)
            for c1, c2, pagrindas in self.zemes_ruozai:
                a, bb = max(c1, a0), min(c2, b0)
                if a < bb and pagrindas >= t and pagrindas - maks <= b:
                    self.piesti_kelia(a, bb, pagrindas, konturas)
            for st in self.langai.values():
                sl, stt, sr, sb = st["sritis"]
                if sr <= l or sl >= r or sb <= t or stt >= b:
                    continue
                for c1, c2 in st["matomi"]:
                    a = max(c1, (l - st["l"]) // S - 1)
                    bb = min(c2, (r - st["l"]) // S + 2)
                    if a < bb:
                        self.piesti_sluoksni(st["h"], a, bb, st["l"], st["t"], 1.0, SNIEGO_KONTURAS)
            for g in getattr(self, "girliandos", ()):  # girliandos – ant viršaus (lyg kabėtų ant ekrano)
                gl, gt, gr, gb = g["ribos"]
                if gr > l and gl < r and gb > t and gt < b:
                    piesti_girlianda(self.statinis, g, (l, t, r, b))
        finally:
            if sritis is not None:
                gdi32.RestoreDC(dc, -1)
        return (l, t, r, b)

    def surinkti_statinius(self, visi):
        """Perpiešia nešvarias statinio sluoksnio sritis; grąžina jų sąrašą."""
        S = STULPELIS
        sritys = []
        for s in self.nesvarios_sritys:
            r = self.perpiesti_statini(s)
            if r:
                sritys.append(r)
        self.nesvarios_sritys = []
        if not visi:  # kaupimasis – kas trečią kadrą, užtenka
            return sritys
        if self.zemes_nesvaru:
            self.zemes_nesvaru = False
            kauke = self.zemes_kauke
            maks = int(self.n["max_aukstis"] * self.k * 1.05)
            # Perpiešiamos tik pasikeitusių stulpelių atkarpos (artimos – kartu), atskirai kiekvienam ekranų apačios
            # ruožui. Anksčiau – visa juosta nuo kairiausio iki dešiniausio pakitimo, net jei tarp jų nieko nebuvo.
            for c1, c2, pagrindas in self.zemes_ruozai:
                i = kauke.find(1, c1, c2)
                while i >= 0:
                    j = kauke.find(0, i, c2)
                    if j < 0:
                        j = c2
                    while True:  # tarpai iki 6 stulpelių sujungiami
                        k_ = kauke.find(1, j, c2)
                        if k_ < 0 or k_ - j > 6:
                            break
                        j = kauke.find(0, k_, c2)
                        if j < 0:
                            j = c2
                    # ±4 stulpeliai: šlaito šešėlis priklauso nuo kaimynų (±3)
                    r = self.perpiesti_statini((i * S - 4 * S, pagrindas - maks - 3, j * S + 4 * S, pagrindas + 1))
                    if r:
                        sritys.append(r)
                    i = kauke.find(1, j, c2)
            kauke[:] = bytes(len(kauke))
        for st in self.nesvarus_langai:
            st["nesvarus"] = False
            r = self.perpiesti_statini(st["sritis"])
            if r:
                sritys.append(r)
        self.nesvarus_langai = []
        return sritys

    def nuvalyti(self, tik_zeme=False):
        """Nuvalo sukauptą sniegą. tik_zeme – tik ekrano apačioje (išjungus „Kaupti ekrano apačioje“)."""
        self.papildomos += [p["sena"] for p in self.pustomos if p["sena"]]
        self.pustomos = []
        self.aukstis = [0.0] * len(self.aukstis)
        self.kelias = [0.0] * len(self.aukstis)
        self.sustumta[:] = bytes(len(self.sustumta))  # valytuvų kauburių nebeliko
        if not tik_zeme:
            for st in self.langai.values():
                st["h"][:] = [0.0] * len(st["h"])
        for s_ in self.seniai:  # stovintis senis – ant naujo (nuvalyto) paviršiaus, sniegas nuo jo irgi nuvalomas
            if tik_zeme and not (s_.get("pav") and s_["pav"][0] == "zeme"):
                continue
            s_["y_fiks"] = None
            if not tik_zeme:
                s_["sniegas"] = 0.0
        self.pilnas_perpiesimas = True

    # ------------------------------------------------------------ snaigės

    def sukurti_snaige(self, tipas, visame_ekrane=False):
        dk = self.k * self.n["dydis"] / 100 * random.uniform(0.85, 1.15)
        _, rusis, forma = TIPAI[tipas]
        x = random.uniform(0, self.vw)
        y = random.uniform(-20, self.min_pagrindas * 0.95) if visame_ekrane else random.uniform(-40, -5)
        if rusis in ("kristalas", "kontura"):
            r0, simetrija = forma[0], forma[1]
            r = r0 * dk
            # posūkiai apskaičiuojami vieną kartą; kadre tik parenkamas vienas iš jų – procesoriui nieko nekainuoja
            pradzia, periodas = random.uniform(0, math.pi), 2 * math.pi / simetrija
            taskai = []
            for k in range(SUKIMO_KADRAI):
                pts = [int(round(v)) for v in formos_taskai(rusis, forma, r, pradzia + periodas * k / SUKIMO_KADRAI)]
                taskai.append(((ctypes.c_long * len(pts))(*pts), len(pts) // 2))
            dydis = int(math.ceil(r * (1.1 if rusis == "kontura" else 1.0))) + 1
        else:
            r = forma * dk
            taskai = None
            dydis = max(1, int(round(r))) + 1
        z = TIPU_GYLIS[tipas] * random.uniform(0.9, 1.1)
        vy = random.uniform(*TIPU_GREITIS[tipas])
        skersmuo = max(1, int(round(2 * r)))  # taškai ir rutuliukai – tikro skersmens, kaip pixel art
        kristalas = taskai is not None
        return [x, y, vy * self.k, r, random.uniform(0, 2 * math.pi),
                # svyravimas į šonus: kristalai – kaip krentantis lapelis, kruopos – vos vos; arti – labiau matosi
                random.uniform(6, 14) * z * self.k if kristalas else random.uniform(1, 4) * z * self.k,
                random.uniform(1.0, 2.4) if kristalas else random.uniform(0.6, 1.4), taskai, dydis, None, tipas,
                random.random(), random.choice((-1, 1)) * random.uniform(15, 60),  # sukimasis, laipsniai per s
                self.vejo_dreifas(z),  # dabartinis horizontalus greitis
                # snaigės beveik neturi inercijos (prisitaiko per ~0,2 s); kiek lėčiau – tik stambiausios
                6.0 - min(r, 9.5) * 0.25,
                0.22 if kristalas else 0.0,  # kristalai krisdami „plasnoja“ kaip lapas
                skersmuo, z]

    def pritaikyti_kieki(self, perkurti=False, visame_ekrane=True):
        if perkurti:
            self.papildomos += [f[SSENA] for f in self.snaiges if f[SSENA]]
            self.snaiges = []
        pagal_tipa = [[] for _ in TIPAI]
        for f in self.snaiges:
            pagal_tipa[f[STIPAS]].append(f)
        nauji = []
        # Padidinus kiekį naujos snaigės ne visos iš karto ties ekrano viršumi (krisdavo kaip lavina, viena banga),
        # o išbarstomos virš ekrano tokiame aukštyje, kad pasirodytų palaipsniui per kelias sekundes – kuo daugiau
        # pridėta, tuo ilgiau (iki SNAIGIU_IBEGIMAS s).
        pridedama = 0 if visame_ekrane else sum(
            max(0, (0 if self.sniegas_isjungtas else norima) - len(pagal_tipa[t]))
            for t, norima in enumerate(self.n["tipai"]))
        ibegimas = SNAIGIU_IBEGIMAS * min(1.0, 0.3 + pridedama / 400) if pridedama > 20 else 0.0
        gk = self.n["greitis"] / 100
        for tipas, norima in enumerate(self.n["tipai"]):
            if self.sniegas_isjungtas:
                norima = 0
            sar = pagal_tipa[tipas]
            while len(sar) < norima:
                f = self.sukurti_snaige(tipas, visame_ekrane)
                if ibegimas:
                    f[SY] -= f[SVY] * gk * random.uniform(0, ibegimas)
                sar.append(f)
            while len(sar) > norima:
                f = sar.pop()
                if f[SSENA]:
                    self.papildomos.append(f[SSENA])
            nauji += sar
        self.snaiges = nauji

    def vejo_dreifas(self, z):
        """Horizontalus greitis ekrane, kurį snaigė pasiektų dabartiniame vėjyje. Vėjas visas neša vienodai,
        bet tolimos ekrane juda lėčiau (paralaksas)."""
        return self.vejas * 12 * self.k * (0.4 + 0.6 * z)

    def i_virsu(self, f, vejas_px, gk):
        # Stipriai pučiant dalis snaigių atskrenda iš šono – kitaip pavėjui ekrano kraštas liktų tuščias.
        vy = 35 * self.k * gk
        sonu = abs(vejas_px) * self.min_pagrindas
        p_sonas = sonu / (sonu + vy * self.vw) if vejas_px else 0.0
        if random.random() < p_sonas:
            f[SX] = -10.0 if vejas_px > 0 else self.vw + 10.0
            f[SY] = random.uniform(0, self.min_pagrindas * 0.8)
        else:
            f[SX] = random.uniform(0, self.vw)
            f[SY] = random.uniform(-30, -5)
        f[SVX] = self.vejo_dreifas(f[SGYLIS])

    def nubyrinti(self, st):
        # Lango sniegas nekrenta į niekur: kelios snaigės perkeliamos ten, kur jis gulėjo.
        S = STULPELIS
        h = st["h"]
        taskai = [(st["l"] + j * S, st["t"] - h[j] * random.random())
                  for j in range(0, len(h), 2) if h[j] > 1.5]
        kiek = min(len(taskai), 40, len(self.snaiges) // 3)
        if kiek > 0:
            for f, (x, y) in zip(random.sample(self.snaiges, kiek), random.sample(taskai, kiek)):
                f[SX], f[SY] = x, y
        self.nesvarios_sritys.append(st["sritis"])

    # ------------------------------------------------------------ vėjas

    def vejo_zingsnis(self, dt):
        """Ramus laikas (pauzė) → gūsis (įsibėgėja, laikosi, nurimsta) → vėl ramu.
        Visi laikai turi atsitiktinį ±, kad vėjas nebūtų mechaniškas."""
        n = self.n
        if not n["vejas_ijungtas"]:  # vėjas išjungtas – esamas nurimsta (ne nutrūksta vienu kadru)
            self.gusio_liko = 0.0
            self.vejo_tikslas = 0.0
            self.vejas -= self.vejas * min(1.0, dt * 0.8 * GUSIO_RIMIMAS / 100)
            return
        kintanti = n["vejo_kryptis"] == "kintanti"
        if not kintanti:
            self.vejo_kryptis = 1 if n["vejo_kryptis"] == "desine" else -1
        if self.gusio_liko > 0:
            self.gusio_liko -= dt
            if self.gusio_liko <= 0:
                self.iki_gusio = GUSIU_PAUZE * random.uniform(0.5, 1.5)
                self.vejo_laikas = 0.0  # iškart parenkamas ramus vėjas – ir gūsis ima rimti
        elif n["gusio_stiprumas"] > 0:
            self.iki_gusio -= dt
            if self.iki_gusio <= 0:
                self.pradeti_gusi()
        if self.gusio_liko <= 0:
            self.vejo_laikas -= dt
            if self.vejo_laikas <= 0:
                if kintanti and random.random() < 0.15:
                    self.vejo_kryptis = -self.vejo_kryptis
                # Kintančio vėjo ramiu metu kartais trumpam pučia ir atgal; pastovios krypties – ne (ženklas
                # nuimamas), bet stiprumų pasiskirstymas tas pats – kad kryptis nekeistų vėjo stiprumo.
                u = random.uniform(-0.2, 0.7)
                self.vejo_tikslas = self.vejo_kryptis * n["vejas"] * (u if kintanti else abs(u))
                self.vejo_laikas = random.uniform(5, 12)
        stipreja = abs(self.vejo_tikslas) > abs(self.vejas)
        greitis = 0.8 * (GUSIO_KILIMAS if stipreja else GUSIO_RIMIMAS) / 100
        self.vejas += (self.vejo_tikslas - self.vejas) * min(1.0, dt * greitis)

    def pradeti_gusi(self):
        n = self.n
        kryptis = self.vejo_kryptis
        if n["vejo_kryptis"] == "kintanti" and random.random() < 0.2:
            kryptis = -kryptis
        self.vejo_tikslas = kryptis * n["gusio_stiprumas"] * random.uniform(0.8, 1.2)
        self.gusio_liko = GUSIO_TRUKME * random.uniform(0.7, 1.3)

    def gusis_dabar(self):
        if self.n["vejas_ijungtas"] and self.n["gusio_stiprumas"] > 0:
            self.pradeti_gusi()
            pz = getattr(self, "vejo_perz", None)
            if pz and pz["kreive"] and pz["kreive"]["gusis"]:
                pz["t"] = pz["kreive"]["gusis"][0]

    # ------------------------------------------------------------ riedantys bumbuliukai

    def naikinti_bumbulus(self):
        for b in self.bumbulai:
            self.naikinti_dc(b["sprite"])
            if b["sena"]:
                self.papildomos.append(b["sena"])
        self.bumbulai = []

    def pasirinkti(self, raktas, kiek, visi_jei_nieko=True):
        """Įjungtų tipų indeksai; jei nuimtos visos varnelės – visi (dingimo būdams) arba nė vieno (raštams ir
        spalvoms: nuėmus visas, bumbuliukų nebelieka)."""
        sar = [i for i, v in enumerate(self.n[raktas]) if v]
        return sar or (list(range(kiek)) if visi_jei_nieko else [])

    def bumbulu_pavirsiai(self):
        """Kur gali riedėti bumbuliukai: (raktas, langas, kairė x, dešinė x)."""
        S = STULPELIS
        sar = [(("zeme", i), None, c1 * S, c2 * S) for i, (c1, c2, _) in enumerate(self.zemes_ruozai)
               if (c2 - c1) * S >= 200]
        if self.n["bumbulai_languose"]:
            for hwnd, st in self.langai.items():
                for c1, c2 in st["matomi"]:
                    if (c2 - c1) * S >= 120:
                        sar.append((("langas", hwnd), st, st["l"] + c1 * S, st["l"] + c2 * S))
        return sar

    def bumbulo_vieta(self, b):
        """Atsitiktinė vieta (ekranų apačioje arba ant langų), kiek įmanoma ne ant kito bumbuliuko."""
        pav = self.bumbulu_pavirsiai()
        if not pav:
            b.update(y=None, pav=None, st=None)
            return
        for _ in range(20):
            raktas, st, l, r = random.choices(pav, weights=[d - a for _, _, a, d in pav])[0]
            x = random.uniform(l + b["r"], r - b["r"])
            if all(o is b or o.get("pav") != raktas or abs(o["x"] - x) > o["r"] + b["r"] + 4 for o in self.bumbulai):
                break
        b.update(pav=raktas, st=st, x=x, ore=False, v=0.0, vy=0.0, aukstis=0.0)
        a = self.bumbulo_pavirsius(b, x)
        b["y"] = a[0] if a else None
        self.bumbulo_ribos(b)

    def bumbulo_ribos(self, b):
        """Iki kur piešti (ant žemės – ruožo ribos, kitur – visas ekranas)."""
        S = STULPELIS
        if b.get("pav") and b["pav"][0] == "zeme" and b["pav"][1] < len(self.zemes_ruozai) and not b["ore"]:
            c1, c2, _ = self.zemes_ruozai[b["pav"][1]]
            b["l"], b["rr"] = c1 * S, c2 * S
        else:
            b["l"], b["rr"] = 0, self.vw

    def kurti_bumbulus(self):
        """Bumbuliukai išbarstomi po ekranų apačią; kiekvienas – savos spalvos, rašto ir dydžio."""
        self.naikinti_bumbulus()
        if not self.n["bumbulai"]:
            return
        S = STULPELIS
        if not any((c2 - c1) * S >= 200 for c1, c2, _ in self.zemes_ruozai):
            return
        rastai = self.pasirinkti("bumbulu_rastai", len(BUMBULU_RASTAI), visi_jei_nieko=False)
        spalvos = self.pasirinkti("bumbulu_spalvos", len(BUMBULU_SPALVOS), visi_jei_nieko=False)
        if not rastai or not spalvos:
            return
        random.shuffle(spalvos)
        for i in range(self.n["bumbulu_kiekis"]):
            Pb, R, Pf = bumbulo_matmenys(random.choice((5, 6, 7)), self.P, self.n["bumbulu_dydis"])
            spalva, rastas = spalvos[i % len(spalvos)], BUMBULU_RASTAI[random.choice(rastai)]
            n = 2 * R + 5
            W = round(n * Pf)
            # kadrai: 8 sukimosi, mažėjantys, žiežirbos, tirpstantys
            kadrai = ([bumbulo_tinklelis(R, spalva, rastas, k) for k in range(BUMBULU_KADRAI)]
                      + [bumbulo_tinklelis(r, spalva, rastas, 0, n) for r in range(R - 1, 0, -1)]
                      + [blyksnio_tinklelis(n, k) for k in range(BUMBULU_BLYKSNIAI)]
                      + [tirpimo_tinklelis(R, spalva, rastas, k) for k in range(TIRPIMO_KADRAI)])
            sp = self.naujas_dc(W * len(kadrai), W)
            p = GdiPiesejas(self.g, sp["dc"])
            for k, t in enumerate(kadrai):
                piks_piesti(p, t, k * W, 0, Pf)
            b = {"sprite": sp, "W": W, "R": R, "Pb": Pb, "spalva": spalva, "r": R * Pf, "c": W / 2,
                 "v": 0.0, "v0": random.uniform(40, 90) * self.k, "kryptis": random.choice((-1, 1)),
                 "kampas": random.uniform(0, 2 * math.pi), "aukstis": 0.0, "vy": 0.0, "sena": None,
                 "busena": "rieda", "laikas": random.uniform(10, 60), "anim": None, "t": 0.0, "trukme": 0.0,
                 "ore": False, "w": 0.0, "pav": None, "st": None, "stumt": random.uniform(0.5, 3.0)}
            self.bumbulai.append(b)
            self.bumbulo_vieta(b)
            fj = getattr(self, "fj", None)  # paleidžiant bumbuliukai sukuriami anksčiau nei fejerverkai
            if fj is not None and fj.aktyvus:  # per fejerverkų šou bumbuliukai slepiasi – sukurti dabar atsiras po šou
                b["busena"], b["laikas"] = "nera", random.uniform(0.5, 2.5)

    def sudauzyti(self, b):
        """Bumbuliukas sudūžta: šukės išlekia, nukrenta ant sniego, pagulėjusios pamirksi ir dingsta."""
        pagr, tamsi, sviesi = BUMBULU_SPALVOS[b["spalva"]]
        spalvos = (pagr, pagr, tamsi, sviesi, "#f2c94c", "#ffffff")
        cx, cy = b["x"], b["y"] - b["r"]
        for _ in range(random.randint(12, 18)):
            a = random.uniform(0, 2 * math.pi)
            greitis = random.uniform(60, 200) * self.k
            self.skeveldros.append({
                "x": cx + math.cos(a) * b["r"] * 0.6, "y": cy + math.sin(a) * b["r"] * 0.6,
                "vx": math.cos(a) * greitis, "vy": math.sin(a) * greitis - random.uniform(100, 220) * self.k,
                "spalva": random.choice(spalvos), "d": b["Pb"] * random.choice((1, 1, 2)),
                "laikas": random.uniform(1.5, 2.5), "nusileido": False, "sena": None, "l": b["l"], "rr": b["rr"]})

    def zemes_virsus(self, c):
        """Matomo sniego aukštis ekrano apačioje stulpelyje c: aukštesnysis iš pusnies ir priekinio kelio sniego.
        Ant jo stovi seniai ir bumbuliukai (kitaip kelias, piešiamas ant jų, uždengdavo apačią)."""
        kel = self.__dict__.get("kelias")
        h = self.aukstis[c]
        return kel[c] if kel and c < len(kel) and kel[c] > h else h

    def virsus_be_kruvu(self, c):
        """Kur stovi ir rieda tai, kas pusnyse, už kelio (seniai, bumbuliukai, jų gabalai), stulpelyje c: kaip
        zemes_virsus, bet buldozeriukų stumiamos krūvos jų nekelia ir nestumdo – krūva juda kelyje priešais juos
       . Kelias be krūvų skaičiuojamas kartą per kadrą (kelias_be_kruvu)."""
        kel = self.__dict__.get("kelias")
        h = self.aukstis[c]
        if not kel or c >= len(kel):
            return h
        bk = self.__dict__.get("_kelias_bk")
        # tik jei skaičiuota iš to paties kelio (pasikeitus ekranams, nuvalius, sumažinus ribą – kelias naujas)
        v = bk[1][c] if bk is not None and bk[0] is kel else kel[c]
        return v if v > h else h

    def kelias_be_kruvu(self, dt):
        """Kartą per kadrą (po buldozeriukų ir kelio žingsnio): kelio sniegas be dabar stumiamų krūvų. Stulpelyje, kurį
        pasiekia stumiama krūva (kelio_kruvos jį pažymi kiek anksčiau, nei krūva atvažiuoja), įsimenamas tuometinis
        kelio aukštis; kol krūva ten – ne aukščiau jo (nuvalyta vieta už verstuvo – kaip yra). Krūvą palikus
        (buldozeriukas apsisuko) – ant jos kylama pamažu. Rezultatas – self._kelias_bk (None – kaip kelias)."""
        kel = self.__dict__.get("kelias")
        if not kel:
            self._kelias_bk = None
            return
        n = len(kel)
        kr = self.kelio_kruvos(0, n) if getattr(self, "ekskavatoriai", None) else None
        pries = self.__dict__.get("_kelias_pries_kruva")
        if pries is None or pries[0] is not kel:  # naujas kelias (ekranai, nuvalymas) – senos atminties nebelieka
            pries = self._kelias_pries_kruva = (kel, [None] * n)
        pries = pries[1]
        if (kr is None or not any(kr)) and all(v is None for v in pries):
            self._kelias_bk = None
            return
        kyla = SENIO_KYLA * 2 * self.k * min(0.1, dt)
        rez = list(kel)
        for c in range(n):
            p_ = pries[c]
            if kr is not None and kr[c]:
                if p_ is None or kel[c] < p_:  # nuvalyta – taip ir lieka
                    p_ = kel[c]
            elif p_ is not None:
                p_ = None if kel[c] <= p_ + kyla else p_ + kyla
            pries[c] = p_
            if p_ is not None and p_ < kel[c]:
                rez[c] = p_
        self._kelias_bk = (kel, rez)

    def sniego_pavirsius(self, x):
        c = int(x // STULPELIS)
        if 0 <= c < len(self.aukstis) and self.pagrindas[c] is not None:
            return self.pagrindas[c] - self.virsus_be_kruvu(c)  # bumbuliukų skeveldros – už kelio, kaip bumbuliukai
        return None

    def skeveldru_zingsnis(self, dt):
        trauka = TRAUKA * self.k
        likusios = []
        for sk in self.skeveldros:
            sk["laikas"] -= dt
            if not sk["nusileido"]:
                sk["vy"] += trauka * dt
                sk["x"] += sk["vx"] * dt
                sk["y"] += sk["vy"] * dt
                pav = self.sniego_pavirsius(sk["x"])
                if pav is not None and sk["y"] >= pav and sk["vy"] > 0:
                    sk["y"], sk["nusileido"] = pav, True
            if sk["laikas"] <= 0 or not sk["l"] <= sk["x"] < sk["rr"] or sk["y"] > self.vh:
                if sk["sena"]:
                    self.papildomos.append(sk["sena"])
            else:
                likusios.append(sk)
        self.skeveldros = likusios

    def pradeti_dingima(self, b):
        b["anim"] = random.choice([BUMBULU_DINGIMAI[i] for i in self.pasirinkti("bumbulu_dingimai", 4)])
        b["busena"], b["t"] = "nyksta", 0.0
        b["trukme"] = bumbulo_animacijos_trukme(b["anim"], b["R"])
        if b["anim"] == "suduzta":
            self.sudauzyti(b)

    def pradeti_atsiradima(self, b):
        self.bumbulo_vieta(b)
        if b["y"] is None:
            b["busena"], b["laikas"] = "nera", 2.0
            return
        b["anim"] = BUMBULU_ATSIRADIMAI[random.choice([BUMBULU_DINGIMAI[i]
                                                       for i in self.pasirinkti("bumbulu_dingimai", 4)])]
        b["t"] = 0.0
        if b["anim"] == "nukrenta":  # iškrenta iš dangaus ir atšoka – tai jau įprastas riedėjimas
            b["busena"], b["laikas"] = "rieda", random.uniform(15, 60)
            b["y"] -= random.uniform(180, 320) * self.k
            b.update(ore=True, vy=0.0, w=random.uniform(-3, 3))
            self.bumbulo_ribos(b)
            return
        b["busena"] = "atsiranda"
        b["trukme"] = bumbulo_animacijos_trukme(b["anim"], b["R"])

    def bumbulo_atrama(self, b, x):
        """Paviršius tiesiai po tašku x tame paviršiuje, ant kurio bumbuliukas: (y, kairė, dešinė, sniego gylis)."""
        pav, S = b.get("pav"), STULPELIS
        if pav is None:
            return None
        if pav[0] == "zeme":
            if pav[1] >= len(self.zemes_ruozai):
                return None
            c1, c2, _ = self.zemes_ruozai[pav[1]]
            c = int(x // S)
            if not c1 <= c < c2 or self.pagrindas[c] is None:
                return None
            v = self.virsus_be_kruvu(c)  # ant matomo paviršiaus – ir ant kelio sniego, bet ne ant krūvų
            return self.pagrindas[c] - v, c1 * S, c2 * S, v
        st = self.langai.get(pav[1])
        if st is None or not self.n["bumbulai_languose"]:
            return None
        j = int((x - st["l"]) // S)
        for c1, c2 in st["matomi"]:
            if c1 <= j < c2:
                return st["t"] - st["h"][j], st["l"] + c1 * S, st["l"] + c2 * S, st["h"][j]
        return None

    def bumbulo_pavirsius(self, b, x):
        """Kur rutuliukas liečia paviršių: aukščiausias taškas po juo (jis remiasi į iškilimus, o ne įsmenga)."""
        centras = self.bumbulo_atrama(b, x)
        if centras is None:
            return None
        y = centras[0]
        for dx in (-0.5, 0.5):
            a = self.bumbulo_atrama(b, x + dx * b["r"])
            if a is not None and a[0] < y:
                y = a[0]
        return y, centras[1], centras[2], centras[3]

    def bumbulo_nuolydis(self, b):
        k_, d_ = self.bumbulo_atrama(b, b["x"] - 0.8 * b["r"]), self.bumbulo_atrama(b, b["x"] + 0.8 * b["r"])
        if k_ is None or d_ is None:
            return 0.0
        return max(-1.0, min(1.0, (d_[0] - k_[0]) / (1.6 * b["r"])))

    def bumbulo_nusileidimas(self, b, y0):
        """Krentantis bumbuliukas – ar kirto kokį nors paviršių (langą ar žemę). Grąžina (raktas, langas, y)."""
        x, y1, S = b["x"], b["y"], STULPELIS
        if self.n["bumbulai_languose"]:
            for hwnd, st in self.langai.items():
                if st["l"] <= x < st["r"]:
                    j = int((x - st["l"]) // S)
                    if any(c1 <= j < c2 for c1, c2 in st["matomi"]):
                        yp = st["t"] - st["h"][j]
                        if y0 <= yp <= y1:
                            return ("langas", hwnd), st, yp
        c = int(x // S)
        if 0 <= c < len(self.pagrindas) and self.pagrindas[c] is not None:
            yp = self.pagrindas[c] - self.virsus_be_kruvu(c)
            if y1 >= yp:
                for i, (c1, c2, _) in enumerate(self.zemes_ruozai):
                    if c1 <= c < c2:
                        return ("zeme", i), None, yp
        return None

    def bumbulu_zingsnis(self, dt):
        self.skeveldru_zingsnis(dt)
        if not self.bumbulai:
            return
        juda = self.n["bumbulu_juda"]  # išjungus bumbuliukai tiesiog stovi vietoje
        sou = self.fj.aktyvus  # per fejerverkus bumbuliukai pradingsta, po šou vėl atsiranda
        # laikas skaičiuojamas iš kadrų (ne laikrodžio) – kad elgsena nepriklausytų nuo stabtelėjimų
        self.bumbulu_laikas = dabar = getattr(self, "bumbulu_laikas", 0.0) + dt
        for b in self.bumbulai:
            # pradingimas ir atsiradimas kitoje vietoje
            b["laikas"] -= dt
            b["t"] += dt
            if sou:
                if b["busena"] == "rieda" and not b["ore"] and b["y"] is not None:
                    self.pradeti_dingima(b)
                elif b["busena"] == "nera":
                    b["laikas"] = random.uniform(0.5, 2.5)  # po šou atsiras ne visi vienu metu
            if b["busena"] == "rieda" and b["laikas"] <= 0 and self.n["bumbulu_dingsta"] and not b["ore"]:
                self.pradeti_dingima(b)
            elif b["busena"] == "nyksta" and b["t"] >= b["trukme"]:
                b["busena"], b["laikas"] = "nera", random.uniform(1.5, 4)
            elif b["busena"] == "nera" and b["laikas"] <= 0:
                self.pradeti_atsiradima(b)
            elif b["busena"] == "atsiranda" and b["t"] >= b["trukme"]:
                b["busena"], b["laikas"] = "rieda", random.uniform(15, 60)
            if b["busena"] != "nera" and b["y"] is not None:
                self.bumbulo_fizika(b, dt, dabar, juda and b["busena"] == "rieda")
        self.bumbulu_susidurimai()

    def bumbulo_fizika(self, b, dt, dabar, juda):
        """Rutuliuko riedėjimas: nuokalnėje įsibėgėja (g·sinα·0,6 – tuščiaviduris rutulys), riedėjimo pasipriešinimas
        didesnis giliame sniege, vėjas pučia, nuo lango krašto nurieda ir krenta, nukritęs atšoka.
        Kad visai nesustingtų – kartais jį stumteli vėjo gūsis (ar „nematoma ranka“), retkarčiais pašoka."""
        k, r = self.k, b["r"]
        g = TRAUKA * k
        gk = self.n["bumbulu_greitis"] / 100
        vejas = self.vejas * 12 * k * 0.5  # prie žemės vėjas silpnesnis
        pav = b.get("pav")
        if pav and pav[0] == "langas":  # langas pajudėjo – gulintis važiuoja kartu (ore esantis – ne)
            st = self.langai.get(pav[1])
            if st is not None and b["st"] is not None and st is not b["st"]:
                if not b["ore"]:
                    b["x"] += st["l"] - b["st"]["l"]
                    b["y"] += st["t"] - b["st"]["t"]
                b["st"] = st
        if b["ore"]:
            y0 = b["y"]
            b["vy"] += g * dt
            b["v"] += (vejas - b["v"]) * 0.1 * dt
            b["x"] += b["v"] * dt
            b["y"] += b["vy"] * dt
            b["kampas"] += b["w"] * dt
            if b["x"] < r or b["x"] > self.vw - r:  # ekrano kraštas – atsimuša
                b["x"] = max(r, min(self.vw - r, b["x"]))
                b["v"] = -b["v"] * 0.5
            if b["vy"] > 0:
                kur = self.bumbulo_nusileidimas(b, y0)
                if kur is not None:
                    smugis = b["vy"]
                    b.update(pav=kur[0], st=kur[1], y=kur[2])
                    if kur[0][0] == "zeme" and smugis > 150 * k:
                        self.bumbulas_aria(b, dabar, smugis=True)
                    if smugis > 90 * k:  # atšoka (stiklas į sniegą – nedaug)
                        b["vy"] = -smugis * 0.35
                    else:
                        b["ore"], b["vy"] = False, 0.0
                    b["v"] *= 0.85
                    self.bumbulo_ribos(b)
                elif b["y"] > self.vh + 4 * r:  # nukrito už ekrano – atsiras kitur
                    self.pradeti_atsiradima(b)
            return
        a = self.bumbulo_pavirsius(b, b["x"])
        if a is None or a[0] > b["y"] + 3 * k:  # nuriedėjo nuo krašto arba po juo nebeliko atramos – krenta
            # nebe ant to lango – kitaip krisdamas „šokinėtų“ kartu su tempiamu langu
            b.update(ore=True, vy=0.0, w=b["v"] / r, pav=None, st=None)
            self.bumbulo_ribos(b)
            return
        b["y"], lo, hi, gylis = a
        if not juda:
            b["v"] = 0.0
            return
        nuol = self.bumbulo_nuolydis(b)
        sin_a = nuol / math.sqrt(1 + nuol * nuol)
        pagreitis = 0.6 * g * sin_a + 0.5 * (vejas - b["v"])
        trintis = (0.012 + 0.05 * min(1.0, gylis / (2 * r))) * g  # giliame purve – kaip giliame sniege
        v = b["v"] + pagreitis * dt
        if v:
            v -= math.copysign(min(abs(v), trintis * dt), v)
        b["v"] = v
        N = b["v0"] * gk
        b["stumt"] -= dt
        if b["stumt"] <= 0:
            b["stumt"] = random.uniform(1.5, 3.5)
            if abs(v) < 0.5 * N:  # beveik stovi – stumtelėjimas (kartais į kitą pusę)
                if random.random() < 0.3:
                    b["kryptis"] = -b["kryptis"]
                b["v"] += b["kryptis"] * N * random.uniform(1.5, 2.5)
                # įstrigęs duobėje – stipresnis, kad išriedėtų per šlaitą
                if abs(b["x"] - b.get("stovejo_ties", -1e9)) < 2 * r:
                    b["v"] = b["kryptis"] * max(abs(b["v"]), math.sqrt(2 * 0.6 * g * 1.2 * r) * 1.3)
                b["stovejo_ties"] = b["x"]
        for e in getattr(self, "ekskavatoriai", ()):  # buldozeriukas stumia priešais save
            # (tik ant langų: ekrano apačioje bumbuliukai rieda pusnimis už eglių, o buldozeriukai valo kelią priešais)
            if e["pav"] == pav and pav[0] != "zeme" and e["busena"] == "vaziuoja" and e.get("atgal", 0) <= 0:
                verst = e["x"] + e["kryptis"] * self.ekskav_pus()
                if -2 * r < (b["x"] - verst) * e["kryptis"] < r:
                    b["x"] = verst + e["kryptis"] * r
                    b["v"] = e["kryptis"] * max(abs(b["v"]), 60 * k)
        dx = b["v"] * dt
        b["x"] += dx
        b["kampas"] += dx / r  # rieda, o ne slysta: pasisukimas atitinka nuriedėtą kelią
        if pav[0] == "zeme":  # ekrano kraštai – sienos; kitur (ruožo, lango kraštas) – nurieda
            if b["x"] - r < 0 or (b["x"] - r < lo and lo <= 0):
                b["x"], b["v"], b["kryptis"] = max(lo, 0) + r, abs(b["v"]) * 0.5, 1
            elif b["x"] + r > self.vw or (b["x"] + r > hi and hi >= self.vw):
                b["x"], b["v"], b["kryptis"] = min(hi, self.vw) - r, -abs(b["v"]) * 0.5, -1
            if abs(b["v"]) > 5 * k:
                self.bumbulas_aria(b, dabar)
        if random.random() < 0.06 * dt:  # kartais pašoka
            b.update(ore=True, vy=-random.uniform(150, 250) * k, w=b["v"] / r)
            self.bumbulo_ribos(b)

    def bumbulu_susidurimai(self):
        """Susidūrę rutuliukai (vienodos masės) atšoka pagal smūgio kryptį; nebelieka „suklijuotų“."""
        bs = [b for b in self.bumbulai if b["busena"] == "rieda" and b["y"] is not None]
        for i in range(len(bs)):
            a = bs[i]
            for c in bs[i + 1:]:
                dx = c["x"] - a["x"]
                dy = (c["y"] - c["r"]) - (a["y"] - a["r"])
                riba = a["r"] + c["r"]
                if abs(dx) >= riba or abs(dy) >= riba:
                    continue
                atst = math.hypot(dx, dy)
                if atst >= riba or atst == 0:
                    continue
                nx, ny = dx / atst, dy / atst
                sant = (c["v"] - a["v"]) * nx + (c["vy"] - a["vy"]) * ny
                if sant < 0:
                    j = -(1 + 0.8) * sant / 2
                    a["v"] -= j * nx
                    c["v"] += j * nx
                    if a["ore"] or c["ore"]:
                        a["vy"] -= j * ny
                        c["vy"] += j * ny
                    for x_ in (a, c):
                        if abs(x_["v"]) > 2 * self.k:
                            x_["kryptis"] = -1 if x_["v"] < 0 else 1
                persidengia = riba - atst
                a["x"] -= nx * persidengia / 2
                c["x"] += nx * persidengia / 2

    @staticmethod
    def bumbulo_vaizdas(b):
        """(kadras sprite juostoje, poslinkis žemyn px, ar apkirpti ties sniegu) pagal būseną ir animaciją."""
        mazejantys = b["R"] - 1
        pr_maz = BUMBULU_KADRAI
        pr_blyk = pr_maz + mazejantys
        pr_tirp = pr_blyk + BUMBULU_BLYKSNIAI
        sukimasis = int(b["kampas"] / (2 * math.pi / BUMBULU_KADRAI)) % BUMBULU_KADRAI
        if b["busena"] not in ("nyksta", "atsiranda"):
            return sukimasis, 0, False
        t, a = b["t"], b["anim"]
        p = min(1.0, t / b["trukme"]) if b["trukme"] else 1.0
        gylis = 2.2 * b["r"]
        if b["busena"] == "nyksta":
            if a == "susitraukia":
                if t < 0.06 * mazejantys:
                    return pr_maz + int(t / 0.06), 0, False
                return pr_blyk + min(BUMBULU_BLYKSNIAI - 1, int((t - 0.06 * mazejantys) / 0.08)), 0, False
            if a == "suduzta":
                return pr_blyk + (0 if p < 0.5 else 1), 0, False
            if a == "istirpsta":
                return pr_tirp + min(TIRPIMO_KADRAI - 1, int(p * TIRPIMO_KADRAI)), 0, False
            return sukimasis, p * gylis, True  # įsmenga
        if a == "isauga":
            if t < 0.08:
                return pr_blyk, 0, False
            return pr_maz + max(0, mazejantys - 1 - int((t - 0.08) / 0.06)), 0, False
        if a == "susidaro":
            return pr_tirp + max(0, TIRPIMO_KADRAI - 1 - int(p * TIRPIMO_KADRAI)), 0, False
        return sukimasis, (1 - p) * gylis, True  # išnyra

    def piesti_fejerverkus(self, i_langa, visas):
        fj = self.fj
        if not fj.grupes:
            return
        fdc = self.fdc
        SelectObject, PatBlt, teptukas = gdi32.SelectObject, gdi32.PatBlt, self.g.teptukas
        dabartine = [None]

        def kvadratas(x, y, d, spalva):
            if spalva is not dabartine[0]:
                SelectObject(fdc, teptukas(spalva))
                dabartine[0] = spalva
            PatBlt(fdc, x, y, d, d, PATCOPY)

        pakite = []
        plotai = []
        TB = msimg32.TransparentBlt

        def uzdengti(nauja):
            # toli danguje – už eglių, sniego, girliandų: kur jie kertasi, statinis sluoksnis vėl uždedamas ant
            # viršaus (kitaip raketos pėdsakas eidavo per eglę)
            if not plotai:
                plotai.extend(self.statiniai_plotai() or [None])
            l, t, r, b = nauja
            for pl in plotai:
                if pl is None:
                    continue
                pl, pt, pr, pb = pl
                il, it, ir_, ib = max(l, pl), max(t, pt), min(r, pr), min(b, pb)
                if il < ir_ and it < ib:
                    TB(fdc, il, it, ir_ - il, ib - it, self.sdc, il, it, ir_ - il, ib - it, PERMATOMA_RGB)

        def pakito(sena, nauja):
            if visas:
                return
            if sena and nauja:
                pakite.append((min(sena[0], nauja[0]), min(sena[1], nauja[1]),
                               max(sena[2], nauja[2]), max(sena[3], nauja[3])))
            elif sena or nauja:
                pakite.append(sena or nauja)

        # Niekas nepiešiama ant užduočių juostų (monitoriaus dalis už darbo srities): ten anksčiau matydavosi
        # krentančios kylančių raketų kibirkštys ir fontanų purslai.
        gdi32.SaveDC(fdc)
        try:
            for m, w in self.monitoriai:
                ml, mt, mr, mb = m[0] - self.vx, m[1] - self.vy, m[2] - self.vx, m[3] - self.vy
                wl, wt, wr, wb = w[0] - self.vx, w[1] - self.vy, w[2] - self.vx, w[3] - self.vy
                for juosta in ((ml, mt, mr, wt), (ml, wb, mr, mb), (ml, wt, wl, wb), (wr, wt, mr, wb)):
                    if juosta[2] > juosta[0] and juosta[3] > juosta[1]:
                        gdi32.ExcludeClipRect(fdc, *juosta)
            for g in fj.grupes:
                nauja = fj.piesti_grupe(g, kvadratas)
                if nauja:
                    nauja = self.ribos(*nauja)
                if nauja:
                    uzdengti(nauja)
                pakito(g.sena, nauja)
                g.sena = nauja
        finally:
            gdi32.RestoreDC(fdc, -1)
        i_langa += sujungti_staciakampius(pakite)

    def fejerverku_P(self):
        return int(self.P * 1.5 + 0.5)  # fejerverkų „pikselis“ stambesnis – kitaip danguje jie per smulkūs

    def fejerverku_sritys(self):
        """Monitorių darbo sritys (be užduočių juostos) perdangos koordinatėmis."""
        return [(w[0] - self.vx, w[1] - self.vy, w[2] - self.vx, w[3] - self.vy) for _, w in self.monitoriai]

    def paleisti_fejerverkus(self):
        ZURNALAS.rasyti(f"ĮVYKIS: fejerverkų šou, {self.n['fejerverku_trukme']} s")
        self.fj.pradeti(self.n["fejerverku_trukme"], self.fejerverku_sritys())

    def kitas_fejerverku_laikas(self, dabar):
        """Artimiausias laikas, kuris dalijasi iš intervalo, skaičiuojant nuo vietinio vidurnakčio pagal sieninį
        laikrodį – ir tą dieną, kai laikrodis persukamas (vasaros / žiemos laikas), šou lieka „apvaliomis“ valandomis."""
        zingsnis = max(1, self.n["fejerverku_intervalas"]) * 60
        lt = time.localtime(dabar)
        Y, M, D = lt.tm_year, lt.tm_mon, lt.tm_mday
        kitas_vidurnaktis = time.mktime((Y, M, D + 1, 0, 0, 0, 0, 0, -1))
        sekundes = lt.tm_hour * 3600 + lt.tm_min * 60 + lt.tm_sec
        k = sekundes // zingsnis + 1
        while k * zingsnis < 86400:  # valandos ir minutės nurodomos atskirai (ne sekundžių pertekliumi), kad
            # mktime jas suprastų kaip sieninį laiką; dvigubą valandą rudenį praleidžiame (kada > dabar)
            h, liek = divmod(k * zingsnis, 3600)
            kada = time.mktime((Y, M, D, h, liek // 60, liek % 60, 0, 0, -1))
            if kada > dabar:
                return min(kada, kitas_vidurnaktis)
            k += 1
        return kitas_vidurnaktis

    # ------------------------------------------------------------ ribos („Išplėstos ribos“)

    def leistinos(self, raktas):
        return (RIBOS_LAISVOS if self.n["be_apribojimu"] else RIBOS)[raktas]

    def maks_tipo(self):
        return MAKS_SNAIGIU_LAISVAI if self.n["be_apribojimu"] else MAKS_SNAIGIU_TIPO

    def maks_viso(self):
        return MAKS_SNAIGIU_LAISVAI if self.n["be_apribojimu"] else MAKS_SNAIGIU_IS_VISO

    def perjungti_apribojimus(self):
        ijungti = self.be_apribojimu_kint.get()
        if ijungti and not messagebox.askyesno(PAVADINIMAS, T(
                "Išplėstos ribos leidžia nustatyti daug didesnius kiekius ir dydžius (ribos vis tiek lieka – kad programa "
                "neužstrigtų visai). Kompiuteris gali pradėti stipriai strigti, o nustatymų langas – lėtai reaguoti."
                "\n\nĮjungti?"), icon="warning"):
            self.be_apribojimu_kint.set(False)
            return
        self.n["be_apribojimu"] = ijungti
        ZURNALAS.rasyti("ĮVYKIS: išplėstos ribos " + ("ĮJUNGTOS" if ijungti else "išjungtos"))
        if not ijungti:  # grąžinamos įprastos ribos – per didelės reikšmės sumažinamos
            apriboti_iprastai(self.n)
            self.kurti_snaigiu_atlasa()
            self.pritaikyti_kieki(perkurti=True)
            self.kurti_egles()
            self.kurti_girliandas()
            self.kurti_bumbulus()
            self.kurti_ekskavatorius()
            self.kurti_senius()
            self.apriboti_sniega()
            self.kitas_fj = self.kitas_fejerverku_laikas(time.time())
        self.issaugoti()
        self.root.after_idle(self.kurti_sasaja)  # laukelių ribos pasikeitė – valdikliai sukuriami iš naujo

    # ------------------------------------------------------------ buldozeriukai (sniego valytuvai)

    def naikinti_ekskavatorius(self):
        for e in getattr(self, "ekskavatoriai", []):
            if e["sena"]:
                self.papildomos.append(e["sena"])
        for d in getattr(self, "ekskav_daleles", []):
            if d["sena"]:
                self.papildomos.append(d["sena"])
        self.ekskavatoriai, self.ekskav_daleles = [], []
        if getattr(self, "ekskav_sprite", None):
            self.naikinti_dc(self.ekskav_sprite)
        self.ekskav_sprite = None

    def kurti_ekskavatorius(self):
        """Buldozeriukai važinėja ekrano apačioje ir langų viršuje, verstuvu stumia sniegą priešais save ir
        nustumia jį per kraštą. Kai jų paviršius švarus – pradingsta ir nukrenta ten, kur sniego daugiausia."""
        self.naikinti_ekskavatorius()
        if not self.n["ekskavatoriai"]:
            # išjungus – likę kauburiai vėl paklūsta kopų ribai (nuslūgs per kitą kopų žingsnį)
            if getattr(self, "sustumta", None) is not None:
                self.sustumta[:] = bytes(len(self.sustumta))
            return
        # Langelis – trupmeninis: iki tol sveikas, todėl dydis keitėsi laiptais (1920×1080 ekrane per visą
        # 50–200 % – tik 5 dydžiai). 100 % – lygiai kaip anksčiau (round(P·1,5)); sniego gumulams – sveikas (ekskav_Pi).
        Pe = self.ekskav_Pe = max(1.0, max(1, int(round(self.P * 1.5))) * self.n["ekskavatoriu_dydis"] / 100)
        self.ekskav_Pi = max(1, int(round(Pe)))
        W, H = round(EKSKAV_PLOTIS * Pe), round(EKSKAV_AUKSTIS * Pe)
        kiek = self.n["ekskavatoriu_kiekis"]
        korpusai = min(kiek, len(EKSKAV_KORPUSAI))
        # viena juosta: kiekvienai korpuso spalvai – visi kadrai (ratukai × kryptis)
        sp = self.ekskav_sprite = self.naujas_dc(W * len(EKSKAV_KADRAI) * korpusai, H)
        p = GdiPiesejas(self.g, sp["dc"])
        for j in range(korpusai):
            for i, kadras in enumerate(EKSKAV_KADRAI):
                piks_piesti(p, ekskavatoriaus_tinklelis(*kadras, j), (j * len(EKSKAV_KADRAI) + i) * W, 0, Pe)
        for i in range(kiek):
            self.ekskavatoriai.append({"x": 0.0, "y": None, "vy": 0.0, "kryptis": random.choice((-1, 1)),
                                       "busena": "nera", "t": 0.0, "laukti": 0.3 + i * 0.7,
                                       "pav": None, "st": None, "ratai": 0.0, "tikrinti": 2.0, "sena": None,
                                       "korpusas": i % korpusai, "svyt_faze": random.random(),
                                       # kiekvienas savo greičio – kaip seniai
                                       "greitis": 1.0 if i == 0 else random.uniform(0.6, 1.3)})

    # ------------------------------------------------------------ sniego senis

    def senio_puosmena(self, s_):
        """Kas seniui ant galvos (SENIO_PUOSMENOS) – parenkama kuriant senį."""
        return s_.get("puosmena", "plika")

    def senio_Ps(self):
        """Seniai piešiami tuo dydžiu, kuriuo nupiešta juosta (keičiant dydį – iki perkūrimo – ne naujuoju:
        kitaip iš juostos būtų kopijuojamos ne tos vietos ir liktų artefaktai)."""
        if getattr(self, "senio_sprite", None):
            return self.senio_sprite["Ps"]
        return senio_pikselis(self.P, self.n["senio_dydis"])

    def naikinti_senius(self):
        for s_ in getattr(self, "seniai", []):
            if s_["sena"]:
                self.papildomos.append(s_["sena"])
            if s_.get("langas") is not None:
                try:
                    s_["langas"].destroy()
                except tk.TclError:
                    pass
        for d in getattr(self, "senio_daleles", []):
            if d["sena"]:
                self.papildomos.append(d["sena"])
        self.seniai, self.senio_daleles = [], []
        self.senio_hwnd = set()
        if getattr(self, "senio_sprite", None):
            self.naikinti_dc(self.senio_sprite)
        self.senio_sprite = None

    def kurti_senius(self):
        """Sniego seniai (mažyliai) slysta ekrano apačioje ir langų viršumi. Pele pačiumpami už šaliko:
        tam kiekvienam – mažas beveik permatomas langelis virš šaliko (pati perdanga pelei kiaurai).
        Pakeitus dydį ar kiekį esami seniai lieka savo vietose – perpiešiama tik juosta, pridedami/šalinami seniai."""
        if not self.n["sniego_senis"]:
            self.naikinti_senius()
            return
        likti = getattr(self, "seniai", [])
        if getattr(self, "senio_sprite", None):
            self.naikinti_dc(self.senio_sprite)
        Ps = senio_pikselis(self.P, self.n["senio_dydis"])
        W, H, n = round(SENIO_W * Ps), round(SENIO_H * Ps), len(SENIO_KADRAI)  # kadro dydis juostoje, px
        kiek = self.n["senio_kiekis"]
        # Viena juosta: plikas senis su 1-o senio sagomis; kitų senių sagos ir visų galvos šakelės užpiešiamos ant
        # viršaus (piesti_senius) – atskiros juostos kiekvienam seniui dideliame ekrane užimtų šimtus MB.
        # dvi eilutės (į dešinę / į kairę), ne viena: su mostaguojančiomis rankomis kadrų beveik šimtas, o
        # didelis senis dideliame ekrane – iki ~500 px pločio: vienoje eilutėje juosta viršytų 32 767 px
        sp = self.senio_sprite = self.naujas_dc(W * n, H * 2)
        sp["Ps"] = Ps
        p = GdiPiesejas(self.g, sp["dc"])
        for j, kaire in enumerate((False, True)):
            for i, (poza, kadras) in enumerate(SENIO_KADRAI):
                piesti_senio_kadra(p, senio_tinklelis(poza, kadras, kaire, 0), i * W, j * H, Ps,
                                   senio_x(senio_poslinkis(poza, kadras), kaire, Ps))
        for s_ in likti[kiek:]:  # perteklius – pašalinamas
            if s_["sena"]:
                self.papildomos.append(s_["sena"])
            self.senio_hwnd.difference_update(s_.get("hwnds") or ())
            if s_.get("langas") is not None:
                try:
                    s_["langas"].destroy()
                except tk.TclError:
                    pass
        self.seniai = likti[:kiek]
        for s_ in self.seniai:
            s_["geom"] = None  # pagavimo langelis – naujo dydžio
        if not hasattr(self, "senio_daleles"):
            self.senio_daleles = []
        for i in range(len(self.seniai), kiek):
            self.seniai.append({"x": 0.0, "y": None, "vx": 0.0, "vy": 0.0, "kryptis": random.choice((-1, 1)),
                                "busena": "nera", "t": 0.0, "laukti": 0.5 + i * 0.8, "pav": None, "st": None,
                                "faze": random.random(), "iki_pauzes": random.uniform(4, 10), "sena": None,
                                # savas ėjimo greitis ir (atskirai) žingsnių tempas – kitaip keli seniai eidavo
                                # ir linksėdavo kaip vienas, lyg žąsys
                                "greitis": 1.0 if i == 0 else random.uniform(0.45, 1.3),
                                "tempas": 1.0 if i == 0 else random.uniform(0.6, 1.35),
                                "langas": None, "rodomas": False, "geom": None, "tempimas": None,
                                "puosmena": SENIO_PUOSMENOS[(self.__dict__.setdefault(
                                    "puosmenu_pradzia", random.randrange(len(SENIO_PUOSMENOS))) + i)
                                    % len(SENIO_PUOSMENOS)]})

    def senio_pavirsiai(self):
        S = STULPELIS
        sar = [(("zeme", i), None, c1 * S, c2 * S) for i, (c1, c2, _) in enumerate(self.zemes_ruozai)
               if (c2 - c1) * S >= 120]
        for hwnd, st in self.langai.items():
            for c1, c2 in st["matomi"]:
                if (c2 - c1) * S >= 80:
                    sar.append((("langas", hwnd), st, st["l"] + c1 * S, st["l"] + c2 * S))
        return sar

    def senio_atramos_y(self, s_, Ps, y_centre):
        """Kur stovi senis: sniegas minkštas, sunki apatinė gniūžtė į jį įsispaudžia – remiasi ne į aukščiausią
        kauburį po savimi (taip senis „stovėdavo“ ant siauros smailės), o į sniego medianą po visu gniūžtės
        pločiu. Siauras kauburys lieka už senio (įspaustas), nuolydyje senis įsmenga į aukštesnę pusę.
        Gniūžtė – ne piešinio viduryje (dešinėje šluota): jos vidurys – SENIO_GNIUZTE langeliai, pusplotis – 8."""
        S = STULPELIS
        lx = SENIO_GNIUZTE if s_.get("kryptis", 1) > 0 else SENIO_W - 1 - SENIO_GNIUZTE
        x = s_["x"] + (lx + 0.5 - SENIO_W / 2) * Ps
        pus = SENIO_GNIUZTES_PUS * Ps
        ys = []
        dx = -pus
        while dx <= pus:
            a = self.senio_atrama(s_, x + dx)
            if a is not None:
                ys.append(a[0])
            dx += S
        if len(ys) < 3:
            return y_centre
        ys.sort()
        return ys[len(ys) // 2]

    def senio_kelio_tikslas(self, s_, Ps):
        """Kur (y) turi stovėti senis ekrano apačioje, kad prisnigtas kelio sniegas priešais jį uždengtų tik jo kojas
        (SENIO_KELIO_GYLIS langelius), arba None. Skaičiuojama po apatine gniūžte, tik kur kelias aukštesnis už
        pusnį (dėl pusnies – ji už senio – nekyla), be stumiamų krūvų (kelio_kruvos – pravažiuojanti krūva senio
        nekelia, tik uždengia iš priekio) ir ne aukščiau įprasto kelio (kelio_ribos – palikta krūva nekelia aukščiau).
        Be to su buldozeriukais senis ant kelio nekiltų visai – snygis jį apsnigtų iki pusės gniūžtės."""
        if s_["pav"] is None or s_["pav"][0] != "zeme" or not self.__dict__.get("kelias"):
            return None
        S, kel, h, base = STULPELIS, self.kelias, self.aukstis, self.pagrindas
        lx = SENIO_GNIUZTE if s_.get("kryptis", 1) > 0 else SENIO_W - 1 - SENIO_GNIUZTE
        x = s_["x"] + (lx + 0.5 - SENIO_W / 2) * Ps
        pus = SENIO_GNIUZTES_PUS * Ps
        a, b = max(0, int((x - pus) // S)), min(len(kel), int((x + pus) // S) + 1)
        if b - a < 3:
            return None
        kr, rib = self.kelio_kruvos(a, b), self.kelio_ribos()
        gyl = SENIO_KELIO_GYLIS * Ps
        ys = sorted(base[c] - max(h[c], min(kel[c], rib[c]) - gyl) for c in range(a, b)
                    if not kr[c - a] and base[c] is not None and kel[c] > h[c] + 0.5)
        if len(ys) < 3 or len(ys) * 2 < b - a:  # kelias aukščiau pusnies – bent po puse gniūžtės
            return None
        return max(ys[len(ys) // 2], self.senio_kelio_riba(s_))

    def senio_kelio_virsus(self, s_, Ps):
        """Prisnigto kelio viršus (y) po apatine gniūžte – mediana – arba None (ne ekrano apačioje). Kaip
        senio_kelio_tikslas: be stumiamų krūvų (pravažiuojanti krūva tik trumpam uždengia) ir ne aukščiau kelio
        ribos (palikta krūva senio nekelia)."""
        kel = self.__dict__.get("kelias")
        if s_["pav"] is None or s_["pav"][0] != "zeme" or not kel:
            return None
        S, base = STULPELIS, self.pagrindas
        lx = SENIO_GNIUZTE if s_.get("kryptis", 1) > 0 else SENIO_W - 1 - SENIO_GNIUZTE
        x = s_["x"] + (lx + 0.5 - SENIO_W / 2) * Ps
        pus = SENIO_GNIUZTES_PUS * Ps
        a, b = max(0, int((x - pus) // S)), min(len(kel), int((x + pus) // S) + 1)
        if b - a < 3:
            return None
        kr, rib = self.kelio_kruvos(a, b), self.kelio_ribos()
        ys = sorted(base[c] - min(kel[c], rib[c]) for c in range(a, b) if not kr[c - a] and base[c] is not None)
        return ys[len(ys) // 2] if len(ys) >= 3 and len(ys) * 2 >= b - a else None

    def senio_kelio_riba(self, s_):
        """Kiek aukštai (y) senis daugiausia pakyla ant kelio sniego: iki įprastos kelio ribos (kelio_ribos – iki
        tiek prisninga) arba pusnies, jei ji aukštesnė. Buldozeriukų krūvos aukštesnės – dėl jų nekyla."""
        c = int(s_["x"] // STULPELIS)
        rib = self.kelio_ribos()
        if not 0 <= c < len(rib) or self.pagrindas[c] is None:
            return -1e9
        return self.pagrindas[c] - max(self.aukstis[c], rib[c])

    def senio_atrama(self, s_, x):
        """(sniego paviršiaus y, kairė, dešinė) po tašku x tame paviršiuje, ant kurio senis, arba None."""
        pav, S = s_["pav"], STULPELIS
        if pav is None:
            return None
        if pav[0] == "zeme":
            if pav[1] >= len(self.zemes_ruozai):
                return None
            c1, c2, _ = self.zemes_ruozai[pav[1]]
            c = int(x // S)
            if not c1 <= c < c2 or self.pagrindas[c] is None:
                return None
            # stovi ant matomo paviršiaus: jei priekinis kelio sniegas aukštesnis už pusnį – ant jo (kitaip kelias
            # uždengdavo senio apačią ir jis atrodydavo įdubęs). Nuvalius kelią nusileidžia ant pusnies.
            return self.pagrindas[c] - self.virsus_be_kruvu(c), c1 * S, c2 * S  # senis – už kelio, krūva jo nekelia
        st = self.langai.get(pav[1])
        if st is None:
            return None
        j = int((x - st["l"]) // S)
        for c1, c2 in st["matomi"]:
            if c1 <= j < c2:
                return st["t"] - st["h"][j], st["l"] + c1 * S, st["l"] + c2 * S
        return None

    def senio_atsirasti(self, s_):
        """Iškrenta iš dangaus ant atsitiktinio paviršiaus (dažniau – ekrano apačios). Kai senis tik stovi
        vietoje – ne už eglutės (kitaip taip ir liktų paslėptas): parenkama vieta, kurios eglės neužstoja."""
        pav = self.senio_pavirsiai()
        if not pav:
            s_.update(laukti=s_["t"] + 2.0)
            return
        svoriai = [(r - l) * (3 if raktas[0] == "zeme" else 1) for raktas, _, l, r in pav]
        Ps = self.senio_Ps()
        pus = SENIO_W * Ps * 0.35
        egles = self.n["senio_stovi"] and self.egles
        kiti = [o for o in self.seniai if o is not s_ and o["busena"] != "nera" and o["y"] is not None]
        bandymu = 40 if egles or kiti else 1
        geriausia = None
        for _ in range(bandymu):
            raktas, st, l, r = random.choices(pav, weights=svoriai)[0]
            l, r = self.senio_krastai(l, r, Ps)
            x = random.uniform(l + pus, max(l + pus, r - pus))
            s_.update(pav=raktas, st=st)
            a = self.senio_atrama(s_, x)
            y = a[0] if a else (st["t"] if st else self.vh)
            uz = self.senio_uz_egles(x, y, Ps) if egles else 0.0
            uz += 1000 * sum(1 for o in kiti if abs(o["x"] - x) < SENIO_W * Ps * 1.2
                             and abs(o["y"] - y) < SENIO_H * Ps)  # ne ant kito senio – kitaip abu subyrėtų
            if geriausia is None or uz < geriausia[0]:
                geriausia = (uz, x, y)
            if uz <= 0:
                break
        _, x, y = geriausia
        s_.update(x=x, y=y - 260 * self.k, vx=0.0, vy=0.0, busena="krenta", t=0.0, pav=None, st=None,
                  tikslas_x=None, y_fiks=None, sv_x=None)

    def senio_krastai(self, lo, hi, Ps):
        """Ties ekrano (visų ekranų) kraštu – siauriau: šluota ir rankos kyšo už kūno (piešinys platesnis už
        kūną), todėl prie pat krašto dalis senio atsidurdavo už ekrano."""
        kr = SENIO_W * Ps * 0.18 + 2
        return (lo + kr if lo <= 1 else lo), (hi - kr if hi >= self.vw - 1 else hi)

    def senio_uz_egles(self, x, y, Ps):
        """Kiek pločio (px) senio kūno ties x (stovinčio ant y) užstoja eglutės; 0 – visai neužstoja."""
        pus, H = SENIO_W * Ps * 0.34, SENIO_H * Ps
        l, r, t = x - pus, x + pus, y - H * 0.95
        kiek = 0.0
        for e in self.egles:
            el, et, er, eb = e["ribos"]
            if et < y and t < eb and el < r and l < er:
                kiek += min(r, er) - max(l, el)
        return kiek

    def senio_laisva_vieta(self, s_, lo, hi, pus, Ps):
        """Artimiausia vieta tame pačiame paviršiuje, kurios eglės neužstoja (None – tokios nėra)."""
        x0, S = s_["x"], STULPELIS * 2
        for i in range(1, int((hi - lo) / S) + 2):
            for x in (x0 + i * S, x0 - i * S):
                if lo + pus <= x <= hi - pus:
                    a = self.senio_atrama(s_, x)
                    if a is not None and self.senio_uz_egles(x, a[0], Ps) <= 0 and not any(
                            o is not s_ and o["pav"] == s_["pav"] and abs(o["x"] - x) < SENIO_W * Ps * 0.8
                            for o in self.seniai):
                        return x
        return None

    def senio_toliau(self, s_):
        """Po veiksmo: eina toliau, o kai „tik stovi vietoje“ – stovi (jei už eglės – pirma išeina iš už jos)."""
        if self.n["senio_stovi"]:
            if self.egles and self.senio_uz_egles(s_["x"], s_["y"], self.senio_Ps()) > 0:
                s_.update(busena="eina", t=0.0, tikslas_x=None)
            else:
                s_.update(busena="stovi", t=0.0, stoveti=random.uniform(3, 8))
        else:
            s_.update(busena="eina", t=0.0, iki_pauzes=random.uniform(5, 12))

    def senio_kristi(self, s_, dt):
        k, S = self.k, STULPELIS
        y0 = s_["y"]
        s_["vy"] += TRAUKA * k * dt
        s_["y"] += s_["vy"] * dt
        s_["x"] += s_["vx"] * dt
        s_["vx"] *= max(0.0, 1 - dt * 0.6)
        senio_svyruoti(s_, dt, self.senio_Ps(), k)
        pus = SENIO_W * self.senio_Ps() * 0.3
        if s_["x"] < pus or s_["x"] > self.vw - pus:  # ekrano kraštas – atsimuša
            s_["x"] = max(pus, min(self.vw - pus, s_["x"]))
            s_["vx"] = -s_["vx"] * 0.4
        if s_["vy"] <= 0:  # dar kyla (mestas aukštyn)
            return
        x, y = s_["x"], s_["y"]
        kur = None
        for hwnd, st in self.langai.items():
            if st["l"] <= x < st["r"]:
                j = int((x - st["l"]) // S)
                if any(c1 <= j < c2 for c1, c2 in st["matomi"]) and y0 <= st["t"] - st["h"][j] <= y:
                    kur = (("langas", hwnd), st)
                    break
        if kur is None:
            c = int(x // S)
            if 0 <= c < len(self.pagrindas) and self.pagrindas[c] is not None and \
                    y >= self.pagrindas[c] - self.virsus_be_kruvu(c):
                for i, (c1, c2, _) in enumerate(self.zemes_ruozai):
                    if c1 <= c < c2:
                        kur = (("zeme", i), None)
                        break
        if kur is not None:
            s_.update(pav=kur[0], st=kur[1])
            a = self.senio_atrama(s_, x)
            if a is None:
                s_.update(pav=None, st=None)
                return
            smugis = s_["vy"]
            # iškart ten, kur stovės (sniego mediana po gniūžte) – kitaip kitame kadre šokteltų
            s_.update(y=self.senio_atramos_y(s_, self.senio_Ps(), a[0]), busena="nukrenta", t=0.0, vy=0.0, vx=0.0, tikslas_x=None, y_fiks=None)
            if smugis > 200 * k:  # sniego purslai
                self.ekskav_debesis(x, a[0] - 1, min(14, int(smugis / (60 * k))), -smugis * 0.25,
                                    dydis=max(2, round(self.senio_Ps())))
            Ps = self.senio_Ps()
            for o in self.seniai:  # nukrito (numestas) ant kito senio – abu subyra
                if o is not s_ and o["busena"] in SENIO_ANT_PAVIRSIAUS + ("nukrenta",) and o["pav"] == s_["pav"] \
                        and abs(o["x"] - x) < SENIO_W * Ps * 0.6:
                    self.senio_subyreti(o, Ps, x)
                    self.senio_subyreti(s_, Ps, o["x"])
                    break
        elif y > self.vh + 300 * k:  # nukrito už ekrano – iškris kitur
            s_.update(busena="nera", t=0.0, laukti=1.0, pav=None, st=None)

    def seniu_zingsnis(self, dt):
        if not self.seniai:
            return
        k = self.k
        Ps = self.senio_Ps()
        pus = SENIO_W * Ps * 0.32
        n_ = self.n
        snaigiu_yra = n_["snaiges"] and any(n_["tipai"])
        for s_ in self.seniai:
            s_["t"] += dt
            b = s_["busena"]
            self.senio_sniegas(s_, b, dt, snaigiu_yra, Ps)
            if b == "nera":
                if s_["t"] >= s_["laukti"]:
                    self.senio_atsirasti(s_)
                continue
            if b == "kabo":  # padėtį keičia pelė
                senio_svyruoti(s_, dt, Ps, k)
                continue
            if b == "krenta":
                self.senio_kristi(s_, dt)
                continue
            pav = s_["pav"]
            if pav and pav[0] == "langas":  # langas pajudėjo – senis keliauja kartu
                st = self.langai.get(pav[1])
                if st is not None and s_["st"] is not None and st is not s_["st"]:
                    s_["x"] += st["l"] - s_["st"]["l"]
                    s_["y"] += st["t"] - s_["st"]["t"]
                    s_["st"] = st
            a = self.senio_atrama(s_, s_["x"])
            if a is None:  # langas užsidarė / buvo uždengtas – krenta
                s_.update(busena="krenta", vy=0.0, vx=0.0, pav=None, st=None, y_fiks=None, sv_x=None)
                continue
            _, lo, hi = a
            lo, hi = self.senio_krastai(lo, hi, Ps)
            if hi - lo >= 2 * pus and not lo + pus <= s_["x"] <= hi - pus:  # pvz., nukrito prie ekrano krašto
                s_["x"] = min(max(s_["x"], lo + pus), hi - pus)
            y = self.senio_atramos_y(s_, Ps, a[0])
            if b in SENIO_STOVINT:  # stovintis senis nekyla: aplink jį prisnigus ar privertus sniego jis
                # apsnigtas, o ne pakeliamas (aukštis užfiksuojamas; lange – lango viršaus atžvilgiu). Bet jei
                # sniegas po juo suslūgo ar nustumtas – pamažu nusileidžia (kitaip liktų kaboti ore).
                pagr = s_["st"]["t"] if pav[0] == "langas" and s_["st"] is not None else 0.0
                if s_.get("y_fiks") is None:
                    s_["y_fiks"] = y - pagr
                elif y - pagr > s_["y_fiks"]:
                    s_["y_fiks"] = min(y - pagr, s_["y_fiks"] + SENIO_NUSESDA * k * dt)
                elif pav[0] == "zeme" and y < s_["y_fiks"] and \
                        (tikslas := self.senio_kelio_tikslas(s_, Ps)) is not None and tikslas < s_["y_fiks"]:
                    # ekrano apačioje priešais jį kaupiasi kelio sniegas – jis piešiamas ant senio, todėl senis
                    # pamažu kyla kartu (kitaip atrodydavo įdubęs), kad kelias dengtų tik kojas. Dėl pusnies (ji –
                    # už senio) ir buldozeriukų krūvų nekyla
                    s_["y_fiks"] = max(tikslas, s_["y_fiks"] - SENIO_KYLA * k * dt)
                if pav[0] == "zeme":
                    # Kelio sniegas piešiamas PRIEŠ senį – bet kokiu atveju (ir kai pusnis už jo aukštesnė už kelią)
                    # jis dengia ne daugiau kaip kojas: giliau apsnigtas senis pamažu kyla.
                    kv = self.senio_kelio_virsus(s_, Ps)
                    if kv is not None and s_["y_fiks"] > kv + SENIO_KELIO_GYLIS * Ps:
                        s_["y_fiks"] = max(kv + SENIO_KELIO_GYLIS * Ps, s_["y_fiks"] - SENIO_KYLA * k * dt)
                y = pagr + s_["y_fiks"]
            else:
                s_["y_fiks"] = None
            s_["y"] = y
            if b == "nukrenta":
                if s_["t"] >= 0.3:
                    if s_.get("atsakyti") is not None and s_["atsakyti"] in self.seniai:  # atsako gniūžte
                        s_.update(busena="meta", t=0.0, suviai=0, taikinys_s=s_["atsakyti"], atsakyti=None,
                                  jega=None, pasemta=False)
                    else:
                        s_["atsakyti"] = None
                        self.senio_toliau(s_)
                continue
            if b in ("mojuoja", "rankos", "dairosi"):
                if s_["t"] >= senio_trumpo_veiksmo_trukme(s_):
                    self.senio_toliau(s_)
                continue
            if b == "stovi":
                if s_["t"] >= s_["stoveti"]:
                    if self.n["senio_stovi"]:  # tik stovi: kartais pajudina rankas, pamojuoja, pasuka galvą
                        if self.egles and self.senio_uz_egles(s_["x"], y, Ps) > 0:  # eglės perdėliotos
                            s_.update(busena="eina", t=0.0, tikslas_x=None)
                        else:
                            senio_stovint(s_)
                    else:
                        if random.random() < 0.45:
                            s_["kryptis"] = -s_["kryptis"]
                        s_.update(busena="eina", t=0.0, iki_pauzes=random.uniform(5, 12))
                continue
            if b in ("meta", "sauna"):
                self.senio_veiksmas(s_, Ps)
                continue
            if self.n["senio_stovi"]:  # vietoje ėjimo – stovi; jei už eglės – pirma nueina į laisvą vietą
                tikslas = s_.get("tikslas_x")
                if tikslas is None and self.egles and self.senio_uz_egles(s_["x"], y, Ps) > 0:
                    tikslas = s_["tikslas_x"] = self.senio_laisva_vieta(s_, lo, hi, pus, Ps)
                if tikslas is None or abs(tikslas - s_["x"]) < 1.5:
                    s_.update(busena="stovi", t=0.0, stoveti=random.uniform(2, 6), tikslas_x=None)
                    continue
                s_["kryptis"] = 1 if tikslas > s_["x"] else -1
                gr = s_.get("greitis", 1.0)
                s_["x"] += s_["kryptis"] * min(24 * k * gr * dt, abs(tikslas - s_["x"]))
                s_["faze"] += dt * s_.get("tempas", 1.0) / 0.7
                continue
            if hi - lo < 4 * pus:  # per siaura vaikščioti (pvz. lango dalis tarp kitų langų) – kitaip kas kelis
                # kadrus atsimuštų nuo kraštų ir „maltųsi“ į šonus; stovi viduryje ir tik pajudina rankas ar galvą
                s_["x"] = min(max(s_["x"], lo + pus), hi - pus) if hi - lo >= 2 * pus else (lo + hi) / 2
                senio_stovint(s_, (2, 5))
                continue
            gr = s_.get("greitis", 1.0)
            s_["x"] += s_["kryptis"] * 24 * k * gr * dt
            s_["faze"] += dt * s_.get("tempas", 1.0) / 0.7
            if s_["x"] - pus < lo:
                s_["x"], s_["kryptis"] = lo + pus, 1
            elif s_["x"] + pus > hi:
                s_["x"], s_["kryptis"] = hi - pus, -1
            s_["iki_pauzes"] -= dt
            if s_["iki_pauzes"] <= 0:
                b = senio_pauze()
                s_.update(busena=b, t=0.0, stoveti=random.uniform(1.0, 3.0), suviai=0)
                if b == "dairosi":
                    senio_dairytis(s_)
        if len(self.seniai) > 1:
            self.seniu_susidurimai(Ps)
        self.senio_daleliu_zingsnis(dt)

    def senio_sniegas(self, s_, b, dt, snaigiu_yra, Ps):
        """Stovinčiam (ir kai sninga) – pamažu prisninga; pajudėjus (eina, pagautas, krenta, meta…) – nubyra.
        Tik kai „Tik stovi vietoje“: vaikštantis sustoja trumpam ir be šluotos – išjungus, kas buvo
        prisnigę, nubyra (debesėliu), o ne dingsta akimirksniu."""
        lygis = s_.get("sniegas", 0.0)
        if not (self.n["sniegas_ant_senio"] and self.n["senio_stovi"]):
            s_["sniegas"] = 0.0
            if lygis > 0.15 and b != "nera" and s_["y"] is not None:
                H = SENIO_H * Ps
                self.ekskav_debesis(s_["x"], s_["y"] - H * 0.7, max(2, int(10 * lygis)), -40 * self.k, dydis=max(1, round(Ps)))
        elif b in SENIO_SNIEGUOJA:
            if snaigiu_yra and lygis < 1.0:
                s_["sniegas"] = min(1.0, lygis + dt / SENIO_SNIEGO_LAIKAS)
        elif lygis > 0.0:
            s_["sniegas"] = 0.0
            if lygis > 0.15 and b != "nera" and s_["y"] is not None:  # subyrėjus – sniegas byra kartu su juo
                H = SENIO_H * Ps
                self.ekskav_debesis(s_["x"], s_["y"] - H * 0.7, max(2, int(10 * lygis)), -40 * self.k, dydis=max(1, round(Ps)))

    def seniu_susidurimai(self, Ps):
        """Du seniai eina vienas į kitą: priėjęs arti kartais apsisuka, o jei ne – susidūrę abu subyra."""
        W, H = SENIO_W * Ps, SENIO_H * Ps
        ant = [s_ for s_ in self.seniai if s_["busena"] in SENIO_ANT_PAVIRSIAUS + ("nukrenta",) and s_["pav"]]
        artimas = {}
        for i, a in enumerate(ant):
            for b in ant[i + 1:]:
                if a["busena"] == "nera" or b["busena"] == "nera" or a["pav"] != b["pav"] or \
                        abs(a["y"] - b["y"]) > H * 0.3:
                    continue
                dx = b["x"] - a["x"]
                if abs(dx) > W * 1.1:
                    continue
                artyn = [s_ for s_, o, kr in ((a, b, dx), (b, a, -dx))
                         if s_["busena"] == "eina" and kr * s_["kryptis"] > 0]
                if abs(dx) < W * 0.62 and artyn:  # kūnai (pločio ~0,63 W) susiliečia
                    self.senio_subyreti(a, Ps, b["x"])
                    self.senio_subyreti(b, Ps, a["x"])
                    continue
                for s_ in artyn:
                    artimas[id(s_)] = (s_, b if s_ is a else a)
        for s_ in self.seniai:  # priartėjus – vienąkart nusprendžia: apsisukti ar eiti toliau
            if id(s_) not in artimas:
                s_["susitikimas"] = None
                continue
            o = artimas[id(s_)][1]
            if s_.get("susitikimas") != id(o):
                s_["susitikimas"] = id(o)
                if s_.get("tikslas_x") is None and random.random() < 0.5:
                    s_["kryptis"] = -s_["kryptis"]

    def senio_subyreti(self, s_, Ps, nuo_x=None):
        """Subyra: gabalai išlekia ir nukrenta, vietoje lieka sniego kauburėlis; po kelių sekundžių iš dangaus
        iškrenta naujas senis (kitoje vietoje)."""
        if s_["busena"] == "nera":
            return
        W, H = round(SENIO_W * Ps), round(SENIO_H * Ps)  # kaip piesti_senius – kad nuolaužos sutaptų su seniu
        poza, kadras = SENIO_KADRAI[self.senio_kadras(s_) % len(SENIO_KADRAI)]
        tinkl = senio_tinklelis(poza, kadras, s_["kryptis"] < 0, self.seniai.index(s_) % len(SENIO_SAGOS),
                                s_.get("tuta") or 0, self.senio_puosmena(s_))
        kryptis = 0 if nuo_x is None else (1 if s_["x"] >= nuo_x else -1)
        gabalai = senio_nuolauzos(tinkl, int(s_["x"] - W / 2), int(s_["y"]) - H + 1, Ps, kryptis, self.k,
                                  self.vw, self.vh)
        self.senio_daleles += gabalai[:max(0, MAKS_SENIO_DALELIU - len(self.senio_daleles))]
        self.senio_kauburys(s_, Ps)
        self.ekskav_debesis(s_["x"], s_["y"] - 1, 10, -160 * self.k, gyv=0.7, dydis=max(2, round(Ps)))
        s_.update(busena="nera", t=0.0, laukti=random.uniform(4, 8), pav=None, st=None, jega=None, konfeti=None,
                  suviai=0, pasemta=False, taiko=False, taikinys_s=None, atsakyti=None, tikslas_x=None,
                  susitikimas=None, y_fiks=None, paspausta=None, tempimas=None)

    def senio_kauburys(self, s_, Ps):
        """Subyrėjusio senio sniegas – kauburėlis sniego sluoksnyje (buldozeriukai jį vėliau nustums).
        Ne aukštesnis už nustatytą didžiausią sniego aukštį: aukštesnio sniego dalis nebūtų perpiešiama
        (perpiešimo sritis – iki didžiausio aukščio) ir likdavo „kabantys“ pėdsakai. Kur sniegas nesikaupia
        (išjungta) – kauburėlio nėra (jo niekas nenuvalytų)."""
        pav, S = s_["pav"], STULPELIS
        if pav is None or self.sniegas_isjungtas:
            return
        if pav[0] == "zeme":
            if not kaupia(self.n, "kaupti_apacioje"):
                return
            h, x0, maks = self.aukstis, 0, self.n["max_aukstis"] * self.k
        else:
            st = self.langai.get(pav[1])
            if st is None or not kaupia(self.n, "kaupti_languose"):
                return
            h, x0, maks = st["h"], st["l"], self.n["max_aukstis_languose"] * self.k
        c = int((s_["x"] - x0) // S)
        R = max(2, int(SENIO_W * Ps * 0.38 / S))
        virsus = SENIO_H * Ps * 0.14
        for dc in range(-R, R + 1):
            j = c + dc
            if 0 <= j < len(h) and (pav[0] != "zeme" or self.pagrindas[j] is not None):
                h[j] = max(h[j], min(maks, h[j] + virsus * (1 - (dc / (R + 1)) ** 2)))
                if pav[0] == "zeme":  # kaip buldozeriuko sustumtas – pamažu nuslūgsta, o ne nukerpamas pagal kopas
                    self.sustumta[j] = 1
        if pav[0] == "zeme":
            self.pazymeti_zeme(c - R - 1, c + R + 2)
        elif not st["nesvarus"]:
            st["nesvarus"] = True
            self.nesvarus_langai.append(st)

    def senio_ranka(self, s_, Ps, langelis):
        """Sprite langelio (žiūrint į dešinę) vieta ekrane – atsižvelgiant į kryptį."""
        lx = langelis[0] if s_["kryptis"] > 0 else SENIO_W - 1 - langelis[0]
        return (s_["x"] - SENIO_W * Ps / 2 + (lx + 0.5) * Ps, s_["y"] - SENIO_H * Ps + 1 + (langelis[1] + 0.5) * Ps)

    def senio_veiksmas(self, s_, Ps):
        if senio_veiksmo_eiga(s_, lambda langelis: self.senio_ranka(s_, Ps, langelis), self.k, self.vw, self.vh,
                              self.senio_daleles, max(0, MAKS_SENIO_DALELIU - len(self.senio_daleles)),
                              taikinys=lambda: self.senio_taikinys(s_, Ps), semti=lambda: self.senio_semti(s_, Ps)):
            s_["taikinys_s"] = None
            self.senio_toliau(s_)

    def senio_taikinys(self, s_, Ps):
        """Į ką mesti: atsakant – į tą, kuris pataikė; kitaip dažniausiai į artimiausią kitą senį (60–800 px)."""
        k = self.k
        galimi = SENIO_ANT_PAVIRSIAUS + ("nukrenta",)
        o = s_.get("taikinys_s")
        if o is not None:  # jau pasirinktas (ar atsakoma) – jei dar „gyvas“
            if o in self.seniai and o["busena"] in galimi and o["y"] is not None:
                return o["x"], o["y"] - SENIO_H * Ps * 0.4
            return None
        if s_.get("jega"):  # jau nuspręsta mesti be taikinio
            return None
        kandidatai = [o for o in self.seniai if o is not s_ and o["busena"] in galimi and o["y"] is not None
                      and 60 * k < abs(o["x"] - s_["x"]) < 800 * k and abs(o["y"] - s_["y"]) < 400 * k]
        if not kandidatai or random.random() > 0.8:
            return None
        o = min(kandidatai, key=lambda q: abs(q["x"] - s_["x"]))
        s_["taikinys_s"] = o
        return o["x"], o["y"] - SENIO_H * Ps * 0.4

    def senio_semti(self, s_, Ps):
        """Pasilenkęs susigrebia sniego: po sauja sniego sluoksnyje lieka duobutė. False – sniego nėra."""
        S = STULPELIS
        x, _ = self.senio_ranka(s_, Ps, SENIO_RANKA_SEMIANT)
        pav = s_["pav"]
        if pav is None:
            return False
        if pav[0] == "zeme":
            h, x0 = self.aukstis, 0
        else:
            st = self.langai.get(pav[1])
            if st is None:
                return False
            h, x0 = st["h"], st["l"]
        c = int((x - x0) // S)
        paimta = 0.0
        for dc, kiek in ((-2, 0.8), (-1, 1.8), (0, 2.5), (1, 1.8), (2, 0.8)):
            j = c + dc
            if 0 <= j < len(h):
                d = min(h[j], kiek * Ps / 2)
                h[j] -= d
                paimta += d
        if pav[0] == "zeme":
            self.pazymeti_zeme(c - 3, c + 4)
        elif not st["nesvarus"]:
            st["nesvarus"] = True
            self.nesvarus_langai.append(st)
        return paimta > 0.5

    def senio_daleliu_zingsnis(self, dt):
        if not self.senio_daleles:
            return
        Ps = self.senio_Ps()
        # gniūžtė pataikė į kitą senį – tas susiūbuoja (susispaudžia), gniūžtė sudūžta
        for d in self.senio_daleles:
            if d["tipas"] == "gniuzte":
                for o in self.seniai:
                    if o is not d["savininkas"] and o["busena"] in SENIO_ANT_PAVIRSIAUS and \
                            abs(d["x"] - o["x"]) < SENIO_W * Ps * 0.3 and o["y"] - SENIO_H * Ps * 0.85 < d["y"] < o["y"]:
                        d["i_seni"] = True
                        # pataikytasis susiūbuoja ir dažnai atsako tuo pačiu (jei mesti yra iš ko)
                        o.update(busena="nukrenta", t=0.0, jega=None, konfeti=None, suviai=0, pasemta=False,
                                 taiko=False, taikinys_s=None, tikslas_x=None,
                                 atsakyti=d["savininkas"] if random.random() < 0.6 else None)

        def zeme(x, y):
            """Artimiausias paviršius PO dalele: lango viršus, esantis aukščiau dalelės, netinka – kitaip
            šalia lango skriejantys gabalai ar konfeti „peršoka“ ant jo viršaus."""
            S = STULPELIS
            v = None
            for st in self.langai.values():
                if st["l"] <= x < st["r"]:
                    j = int((x - st["l"]) // S)
                    if any(c1 <= j < c2 for c1, c2 in st["matomi"]):
                        pv = st["t"] - st["h"][j]
                        if pv >= y - 2 and (v is None or pv < v):
                            v = pv
            if v is not None:
                return v
            c = int(x // S)
            if 0 <= c < len(self.pagrindas) and self.pagrindas[c] is not None:
                return self.pagrindas[c] - self.virsus_be_kruvu(c)
            return None
        vejas_px = self.vejas * 12 * self.k if isinstance(getattr(self, "vejas", None), float) else 0.0
        likusios, suduzo = senio_daleliu_zingsnis(self.senio_daleles, dt, self.k, zeme, vejas_px)
        gyvos = {id(d) for d in likusios}  # ne „d in likusios“ – tai lygintų žodynus (O(n²))
        self.papildomos += [d["sena"] for d in self.senio_daleles if d["sena"] and id(d) not in gyvos]
        self.senio_daleles = likusios
        for x, y in suduzo:  # gniūžtė sudužo – sniego purslai
            self.ekskav_debesis(x, y - 1, 8, -140 * self.k, gyv=0.6, dydis=max(2, round(Ps)))

    def senio_kadras(self, s_):
        poza = "kabo" if s_["busena"] == "krenta" else s_["busena"]
        if poza in ("meta", "sauna", "mojuoja", "rankos", "dairosi"):
            poza, kadras = senio_veiksmo_kadras(s_)
        elif poza == "eina":
            kadras = int(s_["faze"] * SENIO_EINA_KADRAI) % SENIO_EINA_KADRAI
        elif poza == "kabo":
            kadras = senio_kabo_kadras(s_)
        else:
            kadras = 0
        if poza in SENIO_SU_SLUOTA and not self.n["senio_stovi"]:  # vaikšto – trumpai sustojęs be šluotos
            poza += SENIO_BE_SLUOTOS
        return (len(SENIO_KADRAI) if s_["kryptis"] < 0 else 0) + SENIO_KADRO_NR[(poza, kadras)]

    def uzdengti_daug(self, sritys, i_langa):
        """Daug smulkių dalelių (senio gabalai, konfeti, purslai) – uždengiama keliais stačiakampiais, ne kiekviena
        atskirai: kiekvienas uždengimas – SaveDC, kirpimas, kelio perpiešimas (gulint ~100 gabalų – ~100 kartų per
        kadrą). Sujungiamos arti viena kitos (x) esančios sritys; didesnė sritis nieko nesugadina – egles ir kelią
        ji uždeda tik ant to, kas už jų (seniai, tolimos snaigės). Bet ji didesnė už dalelių sritis, kurios kitą kadrą
        atstatomos iš statinio sluoksnio – todėl sujungta sritis pati įtraukiama į kopijavimą į ekraną ir atstatymą
        kitą kadrą (kitaip buferyje likdavo senas kelio vaizdas – buldozeriukams nustūmus krūvą, ekrane likdavo jos
        „vaiduoklis“ su stačiu kraštu)."""
        if not sritys:
            return
        sritys.sort()

        def dengti(sr, viena):
            self.uzdengti_eglemis(sr)
            if not viena:
                i_langa.append(sr)
                self.papildomos.append(sr)
        l, t, r, b = sritys[0]
        viena = True
        for nl, nt, nr, nb in sritys[1:]:
            if nl <= r + 16:
                if (nl, nt, nr, nb) != (l, t, r, b):
                    viena = False
                t, r, b = min(t, nt), max(r, nr), max(b, nb)
            else:
                dengti((l, t, r, b), viena)
                l, t, r, b = nl, nt, nr, nb
                viena = True
        dengti((l, t, r, b), viena)

    def uzdengti_girliandomis(self, i_langa, visas):
        """Girliandos – ant viso, kas šį kadrą nupiešta: perpiešiamos tik ten, kur pasikeitė (i_langa), o pilno
        perpiešimo kadre – visos. Artimos sritys sujungiamos; viena sritis – vienas kirpimas ir piesti_girlianda."""
        girl = getattr(self, "girliandos", None)
        if not girl:
            return
        fdc = self.fdc
        for g in girl:
            gl, gt, gr, gb = g["ribos"]
            if visas:
                sritys = [g["ribos"]]
            else:
                sritys = sorted(((max(l, gl), max(t, gt), min(r, gr), min(b, gb)) for l, t, r, b in i_langa
                                 if l < gr and r > gl and t < gb and b > gt), key=lambda q: q[1])
                sujungtos = []
                for q in sritys:
                    if sujungtos and q[1] <= sujungtos[-1][3] + 4:
                        p_ = sujungtos[-1]
                        sujungtos[-1] = (min(p_[0], q[0]), p_[1], max(p_[2], q[2]), max(p_[3], q[3]))
                    else:
                        sujungtos.append(q)
                sritys = sujungtos
            for sr in sritys:
                gdi32.SaveDC(fdc)
                try:
                    gdi32.IntersectClipRect(fdc, *sr)
                    piesti_girlianda(GdiPiesejas(self.g, fdc), g, sr)
                finally:
                    gdi32.RestoreDC(fdc, -1)

    def uzdengti_eglemis(self, sritis):
        """Senis eina UŽ eglučių: kur jo vieta kertasi su egle, eglė iš statinio sluoksnio uždedama ant viršaus
        (permatoma spalva – tik eglės pikseliai), o ant jos – kelio sniegas. Pagautas pele – priekyje visko."""
        l, t, r, b = sritis
        for e in self.egles:
            el, et, er, eb = e["ribos"]
            il, it, ir_, ib = max(l, el), max(t, et), min(r, er), min(b, eb)
            if il < ir_ and it < ib:
                msimg32.TransparentBlt(self.fdc, il, it, ir_ - il, ib - it, self.sdc, il, it, ir_ - il, ib - it,
                                       PERMATOMA_RGB)
        self.uzdengti_keliu(sritis)

    def kelio_kruvos(self, a, b):
        """Kurie kelio stulpeliai a…b-1 – dabar stumiamos buldozeriukų krūvos (nuo buldozeriuko galo iki krūvos
        priekio, su šlaitais), o ne prisnigtas kelias: [bool]. Paliktos krūvos – ne (jos ribojamos kelio riba)."""
        S, kel = STULPELIS, self.kelias
        stumia = [(e["x"] - e["kryptis"] * self.ekskav_pus(),
                   e["x"] + e["kryptis"] * (self.ekskav_pus() + (e.get("kruvos_ilgis", 0) + 6) * S))
                  for e in getattr(self, "ekskavatoriai", ()) if e["busena"] != "nera"
                  and e.get("pav") is not None and e["pav"][0] == "zeme"]
        if not stumia:
            return [False] * (b - a)
        n = len(kel)
        a0, b0 = max(0, a - 40), min(n, b + 40)  # su paraštėmis – krūvos šlaitai gali prasidėti už senio
        zym = [False] * (b0 - a0)
        for p1, p2 in stumia:  # stulpeliai, kurių vidurys (c + 0,5)·S tarp p1 ir p2
            ca, cb = max(a0, math.ceil(min(p1, p2) / S - 0.5)), min(b0, math.floor(max(p1, p2) / S - 0.5) + 1)
            if ca < cb:
                zym[ca - a0:cb - a0] = [True] * (cb - ca)
        # krūvos šlaitai (žemesni už kelio ribą) – ta pati krūva: nuo pažymėtų stulpelių į šalis, kol kelias vis žemėja
        # (kitaip ant šlaito senis matėsi PRIEŠ krūvą, o jos viršūnė – priešais jį)
        for kryptis in (1, -1):
            rng = range(a0, b0) if kryptis > 0 else range(b0 - 1, a0 - 1, -1)
            ankst = None
            for c in rng:
                i = c - a0
                if zym[i]:
                    ankst = kel[c]
                elif ankst is not None and 1.0 < kel[c] < ankst - 0.2:  # tik žemėjantis (lygus kelias – ne)
                    zym[i], ankst = True, kel[c]
                else:
                    ankst = None
        # siauri tarpai tarp krūvų (du buldozeriukai stumia vienas priešais kitą – viršūnė tarp jų) – ta pati krūva
        i, nz = 0, len(zym)
        while i < nz:
            if not zym[i]:
                j = i
                while j < nz and not zym[j]:
                    j += 1
                if 0 < i and j < nz and j - i <= 3:
                    zym[i:j] = [True] * (j - i)
                i = j
            else:
                i += 1
        return [zym[c - a0] if a0 <= c < b0 else False for c in range(a, b)]

    def uzdengti_keliu(self, sritis):
        """Kelio sniegas (ir buldozeriukų krūvos) – priešais senius ir bumbuliukus (jie – pusnyse, toliau už eglių):
        jų vietoje kelias kadro buferyje nupiešiamas dar kartą ant viršaus."""
        kel = getattr(self, "kelias", None)
        if not kel:
            return
        S = STULPELIS
        l, t, r, b = sritis
        konturas = SNIEGO_KONTURAS if self.n["sniego_konturas"] else None
        for c1, c2, pagr in self.zemes_ruozai:
            a, bb = max(c1, int(l // S)), min(c2, int(r // S) + 1)
            if a >= bb or b <= pagr - max(kel[a:bb]) + 1 or t >= pagr:  # kelio nesiekia (dažniausiai) – nieko
                continue
            gdi32.SaveDC(self.fdc)
            try:
                gdi32.IntersectClipRect(self.fdc, l, t, r, b)
                self.piesti_kelia(a, bb, pagr, konturas, GdiPiesejas(self.g, self.fdc))
            finally:
                gdi32.RestoreDC(self.fdc, -1)

    def senio_apacia(self, s_):
        """Žemiau kur senio nepiešti (y, neįskaitytinai): ant paviršiaus stovinčio – iki pagrindo (užduočių juostos
        ar lango viršaus). Įsmegusi apačia dengiama sniegu, bet žemiau pagrindo sniego nėra – ji matydavosi ant
        užduočių juostos. Krentantis, pagautas – be ribos."""
        pav = s_.get("pav")
        if pav is None or s_["busena"] not in SENIO_ANT_PAVIRSIAUS + ("nukrenta",):
            return None
        if pav[0] == "zeme":
            c = int(s_["x"] // STULPELIS)
            base = self.pagrindas
            return base[c] if 0 <= c < len(base) else None
        st = s_.get("st")
        return st["t"] if st is not None else None

    def piesti_senius(self, i_langa, visas):
        if not self.senio_sprite or not (self.seniai or self.senio_daleles):
            return
        Ps = self.senio_Ps()
        W, H = round(SENIO_W * Ps), round(SENIO_H * Ps)  # kaip juostoje (kurti_senius)
        n = len(SENIO_KADRAI)

        def L(v):  # langelio riba px – kaip piks_piesti (Ps gali būti trupmeninis)
            return round(v * Ps)
        for i, s_ in enumerate(self.seniai):
            nauja = None
            if s_["busena"] != "nera" and s_["y"] is not None:
                nr = self.senio_kadras(s_)
                x0, y0 = int(s_["x"] - W / 2), int(s_["y"]) - H + 1
                nauja = self.permatomas_kopijavimas((W, H), x0, y0, self.senio_sprite["dc"],
                                                    nr % n * W, nr // n * H,  # juostoje – 2 eilutės (kryptys)
                                                    y_max=self.senio_apacia(s_))
                X = senio_x(senio_poslinkis(*SENIO_KADRAI[nr % n]), nr >= n, Ps)  # kaip juostoje
                spalva = i % len(SENIO_SAGOS)
                puosmena = self.senio_puosmena(s_)
                if nauja and puosmena != "plika":  # šakelės galvoje (juostoje senis be jų)
                    poza, kadras = SENIO_KADRAI[nr % n]
                    for x, y, w, sp in senio_puosmenos_langeliai(poza, kadras, nr >= n, puosmena):
                        user32.FillRect(self.fdc, ctypes.byref(wintypes.RECT(x0 + X(x, y), y0 + L(y),
                                                                             x0 + X(x + w, y), y0 + L(y + 1))),
                                        self.g.teptukas(sp))
                if nauja and spalva:  # 2-o ir kitų senių sagos – savos spalvos
                    poza, kadras = SENIO_KADRAI[nr % n]
                    for x, y, w, spalvos in senio_bumbulo_langeliai(poza, kadras, nr >= n):
                        user32.FillRect(self.fdc, ctypes.byref(wintypes.RECT(x0 + X(x, y), y0 + L(y),
                                                                             x0 + X(x + w, y), y0 + L(y + 1))),
                                        self.g.teptukas(spalvos[spalva]))
                tuta = senio_tuta(s_)
                if nauja and tuta:  # juostoje – 0-ė tūta; kitos spalvos užpiešiamos
                    poza, kadras = SENIO_KADRAI[nr % n]
                    for x, y, spalvos in senio_tutos_langeliai(poza, kadras, nr >= n):
                        user32.FillRect(self.fdc, ctypes.byref(wintypes.RECT(x0 + X(x, y), y0 + L(y), x0 + X(x + 1, y),
                                                                             y0 + L(y + 1))),
                                        self.g.teptukas(spalvos[tuta]))
                lygis = s_.get("sniegas", 0.0) * SENIO_SNIEGO_DALIS
                if nauja and lygis > 0:  # sniegas ant galvos, šakelių, rankų, šluotos
                    poza, kadras = SENIO_KADRAI[nr % n]
                    baltas = self.g.teptukas(SNIEGAS)
                    for x, y, slenkstis in senio_sniego_langeliai(poza, kadras, nr >= n, puosmena):
                        if slenkstis >= lygis:
                            break
                        user32.FillRect(self.fdc, ctypes.byref(wintypes.RECT(x0 + X(x, y), y0 + L(y), x0 + X(x + 1, y),
                                                                             y0 + L(y + 1))), baltas)
                if nauja and self.n["senio_lemputes"]:  # girliandos lemputės ant šluotos (ir apsnigtos – matosi)
                    poza, kadras = SENIO_KADRAI[nr % n]
                    lemp = senio_sluotos_lemputes(poza, kadras, nr >= n)
                    if lemp:
                        laikas, anim = time.perf_counter(), self.n["senio_lempuciu_animacija"]
                        for x, y, j in lemp:
                            sp = senio_lemputes_spalva(j, i, senio_lemputes_sviesumas(anim, laikas, j, len(lemp), i))
                            user32.FillRect(self.fdc, ctypes.byref(wintypes.RECT(
                                x0 + X(x, y), y0 + L(y), x0 + X(x + 1, y), y0 + L(y + 1))), self.g.teptukas(sp))
                if nauja and s_["busena"] != "kabo":
                    self.uzdengti_eglemis(nauja)
            if not visas:
                if s_["sena"]:
                    i_langa.append(s_["sena"])
                if nauja:
                    i_langa.append(nauja)
            s_["sena"] = nauja
            self.atnaujinti_senio_langa(s_)
        # gniūžtės (baltos su kontūru) ir konfeti (spalvoti popieriukai, krisdami vartaliojasi)
        Ps = self.senio_Ps()
        kontur, baltas = self.g.teptukas(SENIO_SPALVOS["g"]), self.g.teptukas(SNIEGAS)
        FillRect, RECT = user32.FillRect, wintypes.RECT
        dengti = []  # uždengiama kartu, ne kiekviena dalelė atskirai
        for d in self.senio_daleles:
            x, y = int(d["x"]), int(d["y"])
            if d["tipas"] == "gniuzte":
                r = max(2, round(Ps))
                nauja = self.ribos(x - r - 1, y - r - 1, x + r + 1, y + r + 1)
                if nauja:
                    FillRect(self.fdc, ctypes.byref(RECT(*nauja)), kontur)
                    vidus = self.ribos(x - r, y - r, x + r, y + r)
                    if vidus:
                        FillRect(self.fdc, ctypes.byref(RECT(*vidus)), baltas)
            elif d["tipas"] == "gabalas":  # smulkūs pikseliai, be kontūro – kaip pats senis ir sniegas
                a_ = max(1, round(d["d"]))
                nauja = self.ribos(x, y - a_, x + a_, y)
                if nauja:
                    FillRect(self.fdc, ctypes.byref(RECT(*nauja)), self.g.teptukas(d["spalva"]))
            else:
                if d["gyv"] < 0.6 and d["guli"] and int(d["gyv"] * 12) % 2 == 0:  # prieš dingdami pamirksi
                    nauja = None
                else:
                    plac = int(math.sin(d["faze"]) * 2) != 0 or d["guli"]  # „vartaliojasi“: plokščias / briauna
                    w_, h_ = (round(2 * Ps), max(1, round(Ps))) if plac else (max(1, round(Ps)), round(2 * Ps))
                    nauja = self.ribos(x, y - h_, x + w_, y)
                    if nauja:
                        FillRect(self.fdc, ctypes.byref(RECT(*nauja)), self.g.teptukas(d["spalva"]))
            if nauja:  # gabalėliai, gniūžtės, konfeti – senio gylyje, t. y. irgi už eglučių ir kelio
                dengti.append(nauja)
            if not visas:
                if d["sena"]:
                    i_langa.append(d["sena"])
                if nauja:
                    i_langa.append(nauja)
            d["sena"] = nauja
        self.uzdengti_daug(dengti, i_langa)


    # pagavimas pele: mažas langelis virš šaliko
    SENIO_GRIEBIMAS = (6, 19 + SENIO_POSLINKIS, 14, 6)  # langeliais: x, y, plotis, aukštis (šalikas ir kaklas)

    def atnaujinti_senio_langa(self, s_):
        """Pagavimo langelis seka senį. Kai senio nėra (subyrėjo, dar neiškrito) – langelis nepaslepiamas, o tik
        nustumiamas už ekrano: kiekvienas „visada viršuje“ lango paslėpimas ir parodymas verčia Windows
        perkomponuoti ekraną – su keliais byrančiais seniais tai matėsi kaip perdangos mirgėjimas.
        Paslepiamas tik tada, kai paslėpta visa perdanga."""
        if not self.rodoma:
            if s_["rodomas"] and s_.get("langas") is not None:
                s_["langas"].withdraw()
                s_["rodomas"] = False
            return
        nera = s_["busena"] == "nera" or s_["y"] is None
        if nera and s_.get("langas") is None:
            return
        try:
            l = s_.get("langas") or self.kurti_senio_langa(s_)
            Ps = self.senio_Ps()
            gx, gy, gw, gh = self.SENIO_GRIEBIMAS
            if nera:
                x0, y0 = self.vx - 10000, self.vy - 10000
            else:
                x0 = int(s_["x"] - round(SENIO_W * Ps) / 2) + round(gx * Ps) + self.vx
                y0 = int(s_["y"]) - round(SENIO_H * Ps) + 1 + round(gy * Ps) + self.vy
            # langelis perkeliamas tik pasislinkus ≥ 2 langelius (jis per visą šaliką) – mažiau lango perkėlimų
            g0, slenkstis = s_["geom"], max(2, 2 * Ps)
            lw, lh = max(1, round(gw * Ps)), max(1, round(gh * Ps))
            if g0 is None or g0[0] != lw or abs(g0[1] - x0) >= slenkstis or abs(g0[2] - y0) >= slenkstis:
                l.geometry(f"{lw}x{lh}+{x0}+{y0}")
                s_["geom"] = (lw, x0, y0)
            if not s_["rodomas"]:
                l.deiconify()
                l.attributes("-topmost", True)
                s_["rodomas"] = True
                if not s_["hwnds"]:
                    self.registruoti_senio_langa(s_, l)
        except tk.TclError:
            s_["langas"] = None

    def kurti_senio_langa(self, s_):
        l = tk.Toplevel(self.root)
        l.withdraw()  # parodomas tik nustačius vietą (kitaip akimirkai atsirastų kampe 200×200)
        l.overrideredirect(True)
        l.configure(bg=SENIO_SPALVOS["C"], cursor="hand2")
        try:
            l.attributes("-alpha", 0.02)  # beveik permatomas, bet pelę gaudo
        except tk.TclError:
            pass
        l.attributes("-topmost", True)
        l.bind("<ButtonPress-1>", lambda e: self.senis_paimtas(s_, e))
        l.bind("<B1-Motion>", lambda e: self.senis_tempiamas(s_, e))
        l.bind("<ButtonRelease-1>", lambda e: self.senis_paleistas(s_, e))
        s_["langas"], s_["rodomas"], s_["geom"], s_["hwnds"] = l, False, None, []
        return l

    def registruoti_senio_langa(self, s_, l):
        """Po pirmo parodymo: tikrasis (viršutinis) lango HWND – tik tada jis jau sukurtas. Anksčiau, kol langas
        dar nerodytas, wm_frame grąžindavo vidinio lango HWND, todėl savas langelis atrodė kaip svetimas:
        kiekvienas senio žingsnis buvo palaikomas kitų langų judėjimu (langų skaitymas kas 30 ms, papildomi
        perpiešimai), o perdanga vis iš naujo kelta į viršų (mirgėjimas – juo labiau, kuo daugiau senių).
        Langelis – ne užduočių juostoje ir nevagia fokuso."""
        try:
            l.update_idletasks()
            vidinis = int(l.winfo_id())
            virsutinis = user32.GetAncestor(vidinis, GA_ROOT) or vidinis
        except Exception:
            return
        for h in dict.fromkeys((virsutinis, vidinis)):
            self.senio_hwnd.add(h)
            s_["hwnds"].append(h)
        try:
            SetWindowLong(virsutinis, GWL_EXSTYLE,
                          GetWindowLong(virsutinis, GWL_EXSTYLE) | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE)
        except Exception:
            pass

    def senis_paimtas(self, s_, e):
        """Paspaudus dar nežinia – spragtelėjimas ar tempimas: tempti pradedama pajudinus pelę ≥ 4 px."""
        mx, my = e.x_root - self.vx, e.y_root - self.vy
        s_["paspausta"] = (time.perf_counter(), mx, my, s_["x"] - mx, s_["y"] - my)

    def senis_tempiamas(self, s_, e):
        mx, my = e.x_root - self.vx, e.y_root - self.vy
        pr = s_.get("paspausta")
        if pr is not None:
            if abs(mx - pr[1]) < 4 and abs(my - pr[2]) < 4:
                return
            s_["paspausta"] = None
            s_.update(busena="kabo", pav=None, st=None, vx=0.0, vy=0.0, t=0.0, jega=None, konfeti=None, suviai=0,
                      pasemta=False, taiko=False, taikinys_s=None, atsakyti=None, tikslas_x=None, y_fiks=None,
                      tempimas=(pr[3], pr[4]), istorija=[(pr[0], pr[1], pr[2])], sv_x=None)
        if s_["busena"] != "kabo" or not s_.get("tempimas"):
            return
        dx, dy = s_["tempimas"]
        s_["x"], s_["y"] = max(0.0, min(float(self.vw), mx + dx)), my + dy
        s_["istorija"] = (s_["istorija"] + [(time.perf_counter(), mx, my)])[-6:]
        self.atnaujinti_senio_langa(s_)

    def senis_paleistas(self, s_, e):
        if s_.get("paspausta") is not None:  # nepajudinus – spragtelėjimas
            s_["paspausta"] = None
            if s_["busena"] in ("eina", "stovi", "mojuoja", "rankos", "dairosi"):
                dvigubas = time.perf_counter() - s_.get("spragt_laikas", -9) < 0.4
                s_["spragt_laikas"] = time.perf_counter()
                if dvigubas:  # dukart – pasveikina konfeti
                    s_.update(busena="sauna", t=0.0, suviai=0, konfeti=None)
                else:
                    s_.update(busena="mojuoja", t=0.0)
            return
        if s_["busena"] != "kabo":
            return
        ist = s_.get("istorija") or []
        vx = vy = 0.0
        if len(ist) >= 2 and ist[-1][0] - ist[0][0] > 0.01 and time.perf_counter() - ist[-1][0] < 0.1:
            d = ist[-1][0] - ist[0][0]
            vx, vy = (ist[-1][1] - ist[0][1]) / d, (ist[-1][2] - ist[0][2]) / d
        riba = 1200 * self.k  # galima ir mesti
        s_.update(busena="krenta", vx=max(-riba, min(riba, vx)), vy=max(-riba, min(riba, vy)), tempimas=None, t=0.0)

    def ekskav_pus(self):
        return EKSKAV_PLOTIS / 2 * self.ekskav_Pe

    def ekskav_tarpas(self):
        """Mažiausias atstumas tarp dviejų buldozeriukų centrų – kad niekada nebūtų vienas ant kito."""
        return (EKSKAV_PLOTIS + 3) * self.ekskav_Pe

    def ekskav_pavirsiai(self):
        """Paviršiai, kuriais galima važinėti: (raktas, langas, kairė x, dešinė x, pagrindo y, aukščiai, x0)."""
        S = STULPELIS
        min_plotis = 3 * self.ekskav_tarpas()
        sar = []
        for i, (c1, c2, pagr) in enumerate(self.zemes_ruozai):
            if (c2 - c1) * S >= min_plotis:
                sar.append((("zeme", i), None, c1 * S, c2 * S, pagr, self.kelias, 0))
        for hwnd, st in self.langai.items():
            for c1, c2 in st["matomi"]:
                if (c2 - c1) * S >= min_plotis:
                    sar.append((("langas", hwnd), st, st["l"] + c1 * S, st["l"] + c2 * S, st["t"], st["h"], st["l"]))
        return sar

    def ekskav_pavirsius(self, e):
        """Paviršius po buldozeriuku (aukščiai, x0, pagrindo y, kairė x, dešinė x) arba None, jei jo nebėra."""
        S = STULPELIS
        if e["pav"] is None:
            return None
        if e["pav"][0] == "zeme":
            if e["pav"][1] >= len(self.zemes_ruozai):
                return None
            c1, c2, pagr = self.zemes_ruozai[e["pav"][1]]
            return self.kelias, 0, pagr, c1 * S, c2 * S  # žemėje buldozeriukai valo tik kelią (priešais egles)
        st = self.langai.get(e["pav"][1])
        if st is None:
            return None
        if st is not e["st"]:  # langas pajudėjo – važiuojame kartu su juo
            e["x"] += st["l"] - e["st"]["l"]
            e["st"] = st
        xr = e["x"] - st["l"]
        for c1, c2 in st["matomi"]:
            if c1 * S <= xr <= c2 * S and (c2 - c1) * S >= 2 * self.ekskav_tarpas():
                return st["h"], st["l"], st["t"], st["l"] + c1 * S, st["l"] + c2 * S
        return None

    @staticmethod
    def ekskav_sniego_kiekis(h, x0, xa, xb):
        """Sniego kiekis tarp xa ir xb bei stulpelis, kur jo daugiausia."""
        S = STULPELIS
        a, b = max(0, int((min(xa, xb) - x0) // S)), min(len(h), int((max(xa, xb) - x0) // S) + 1)
        if b <= a:
            return 0.0, a
        dalis = h[a:b]
        return sum(dalis), a + dalis.index(max(dalis))

    def ekskav_pazymeti(self, e, a, b):
        if e["pav"][0] == "zeme":
            self.pazymeti_zeme(a - 1, b + 1)
            return
        e["st"]["kruvos"] = True  # kelio_slinkimas: lange liko krūva – jos stati siena nuslinks
        if not e["st"]["nesvarus"]:
            e["st"]["nesvarus"] = True
            self.nesvarus_langai.append(e["st"])

    def ekskav_stumti(self, e, pav, priekis, krastas):
        """Verstuvas stumia sniegą priešais save kauburiu (stumti_kauburi). Pasiekus kraštą – nustumiama žemyn."""
        h, x0, pagr, lo, hi = pav
        S, k, d = STULPELIS, self.k, e["kryptis"]
        if e.get("kruvos_kryptis") != d:  # apsisuko – senas kauburys lieka, kur buvo
            e["kruvos_kryptis"], e["kruvos_ilgis"] = d, 0
        c_lo, c_hi = max(0, int((lo - x0) // S)), min(len(h), int((hi - x0) // S))
        c_priekis = int((priekis - x0) // S)
        c_galas = int((e["x"] - d * self.ekskav_pus() - x0) // S)
        maks = (self.n["max_aukstis"] if e["pav"][0] == "zeme" else self.n["max_aukstis_languose"]) * k
        H_maks = max(2.0, min(maks, EKSKAV_VERSTUVO_AUKSTIS * self.ekskav_Pe * 0.85))
        rez = stumti_kauburi(h, d, c_galas, c_priekis, c_lo, c_hi, e["kruvos_ilgis"], H_maks, S, krastas, atmintis=e,
                             griuti_iki=maks if e["pav"][0] != "zeme" else 0.0)
        if rez is None:
            e["kruvos_ilgis"] = 0
            return
        n_telpa, pilti, perteklius, nuo, iki = rez
        if perteklius > 0:  # tik purslai – sniegas dingsta
            # pagal kiekį, ne kas kadrą: giliame sniege perteklius būna kiekviename kadre, ir prie verstuvo
            # nuolat virpėdavo iki 3 gumulų per kadrą (~90 per sekundę)
            vnt = EKSKAV_PURSLO_KIEKIS * k
            kaupas = e.get("purslu_kaupas", 0.0) + perteklius
            n_ = min(2, int(kaupas // vnt))
            if n_:
                self.ekskav_purslai(priekis, pagr - H_maks, n_, 0.5)
            e["purslu_kaupas"] = min(kaupas - n_ * vnt, 2 * vnt)
        e["kruvos_ilgis"] = n_telpa
        self.ekskav_pazymeti(e, nuo, iki)
        if pilti > 0.05:
            self.ekskav_pilti(hi if d > 0 else lo, pagr, pilti, d, H_maks, e)

    def ekskav_pilti(self, x, y, kiek, d, maks, e=None):
        """Per kraštą byrantis sniegas. Gumulai – ne daugiau kaip 2 per kadrą, kiekvienas neša ~savo dydžio sniego
        (e["pilti_kaupas"] kaupia, kas dar nenubyrėjo): anksčiau prie krašto kiekvienas kadras išberdavo iki 14
        gumulų (~200 per sekundę) – byrėjo tankiu stulpu, o jų nusileidimai perpiešinėjo žemę ir stabdė kadrus.
        Tarp gumulų – smulkūs trupiniai (tik vaizdas, sniego nekelia)."""
        k, S = self.k, STULPELIS
        Pe = getattr(self, "ekskav_Pi", None) or max(1, int(round(self.P * 1.5)))
        gabalas = max(1.0, Pe * Pe / S)  # vieno gumulo sniego kiekis (stulpelio px)
        kaupas = kiek + (e.get("pilti_kaupas", 0.0) if e is not None else 0.0)
        vietos = max(0, MAKS_EKSKAV_DALELIU - len(self.ekskav_daleles))
        n = min(2, int(kaupas // gabalas), vietos)
        if n == 0 and vietos and (e is None or kaupas > 4 * gabalas):  # be atminties ar riba – vienas neša viską
            n = 1
        if n:
            for _ in range(n):
                self.ekskav_daleles.append({
                    "x": x + d * random.uniform(0, 5) * k, "y": y - random.uniform(0, maks + 2),
                    "vx": d * random.uniform(12, 65) * k, "vy": -random.uniform(0, 45) * k,
                    "gyv": 5.0, "kiekis": kaupas / n, "sena": None, "dyd": random.choice((Pe, Pe, max(2, Pe - 1)))})
            kaupas = 0.0
        if e is not None:
            e["pilti_kaupas"] = kaupas
        smulkus = max(1, Pe // 2)
        for _ in range(min(random.choice((0, 1, 1, 2)), max(0, vietos - n))):  # trupiniai – tik vaizdas
            self.ekskav_daleles.append({
                "x": x + d * random.uniform(0, 7) * k, "y": y - random.uniform(0, maks + 2),
                "vx": d * random.uniform(8, 90) * k, "vy": -random.uniform(0, 70) * k,
                "gyv": 15.0, "oras": True, "kiekis": 0.0, "sena": None,  # krenta iki žemės (ar kito lango)
                "dyd": random.choice((smulkus, max(1, smulkus - 1)))})

    def ekskav_purslai(self, x, y, kiek, stiprumas=1.0):
        """Sniego purslai (tik vaizdas): išlekia į viršų ir į šonus, nukritę dingsta."""
        k = self.k
        kiek = min(kiek, max(0, MAKS_EKSKAV_DALELIU - len(self.ekskav_daleles)))  # daug buldozerių giliame sniege – riba
        for _ in range(kiek):
            # gyv – tik atsarga: purslai nukrenta atgal ant lango / žemės, o nulėkę už lango krašto – krenta iki
            # apačios (anksčiau po ~1 s dingdavo ore)
            dyd, smulkus = self.ekskav_gumulo_dydis()
            self.ekskav_daleles.append({"x": x + random.uniform(-4, 4) * k, "y": y,
                                        "vx": random.uniform(-90, 90) * k * stiprumas * (1.3 if smulkus else 1.0),
                                        "vy": -random.uniform(120, 260) * k * stiprumas,
                                        "gyv": 8.0, "kiekis": 0.0, "sena": None, "dyd": dyd, "oras": smulkus})

    def ekskav_gumulo_dydis(self):
        """Purslų / debesėlių gumulas: (dydis px, ar smulkus trupinys). Pusė – smulkūs trupiniai (lėčiau krenta),
        kiti – įvairaus dydžio gumulai."""
        Pe = getattr(self, "ekskav_Pi", None) or max(1, int(round(self.P * 1.5)))
        if random.random() < 0.5:
            return random.choice((max(1, Pe // 2), max(1, Pe // 2 - 1))), True
        return random.choice((Pe, Pe, max(2, Pe - 1))), False

    def ekskav_susidurimas(self, e, o, pav):
        """Du valytuvai sustūmė sniegą vienas į kitą: tarp jų iškyla kalnelis, pažyra purslai, abu atsitraukia."""
        h, x0, pagr, lo, hi = pav
        S, d = STULPELIS, e["kryptis"]
        pus = self.ekskav_pus()
        xa, xb = sorted((e["x"] + d * pus, o["x"] - d * pus))
        a, b = max(0, int((xa - x0) // S)), min(len(h), int((xb - x0) // S) + 1)
        c_lo, c_hi = max(0, int((lo - x0) // S)), min(len(h), int((hi - x0) // S))
        V = sum(h[a:b]) if b > a else 0.0
        vidurys = (xa + xb) / 2
        if V > 0.5:
            for c in range(a, b):
                h[c] = 0.0
            maks = (self.n["max_aukstis"] if e["pav"][0] == "zeme" else self.n["max_aukstis_languose"]) * self.k
            H = min(maks, EKSKAV_VERSTUVO_AUKSTIS * self.ekskav_Pe * 1.2)  # kalnelis kiek aukštesnis už verstuvus
            aukst, netilpo = kalnelio_profilis(V, H, S, max(2, (b - a) // 2 + 2))
            if aukst:
                f = (V - netilpo) / sum(aukst)
                c0 = int((vidurys - x0) // S) - len(aukst) // 2
                for i, v in enumerate(aukst):
                    if c_lo <= c0 + i < c_hi:
                        h[c0 + i] = min(maks, h[c0 + i] + v * f)
                self.ekskav_pazymeti(e, min(a, c0), max(b, c0 + len(aukst)) + 1)
            self.ekskav_purslai(vidurys, pagr - min(V, 2 * H) * 0.3, min(24, 6 + int(V / (4 * self.k))))
        for x in (e, o):
            x["atgal"] = random.uniform(0.7, 1.1)
            x["kruvos_ilgis"] = 0

    def ekskav_debesis(self, x, y, kiek, vy, gyv=0.8, dydis=None):
        """Sniego debesėlis atsirandant, pradingstant ar nusileidžiant (be sniego kiekio – tik vaizdas).
        dydis – gumulėlio dydis px (seniams – pagal senio dydį; numatytai – pagal buldozeriuko). Senių purslai
        (su dydžiu) piešiami už eglučių, kaip ir patys seniai."""
        k = self.k
        kiek = min(kiek, max(0, MAKS_EKSKAV_DALELIU - len(self.ekskav_daleles)))
        for _ in range(kiek):
            d = {"x": x + random.uniform(-8, 8) * k, "y": y, "vx": random.uniform(-60, 60) * k,
                 "vy": vy * random.uniform(0.6, 1.2), "gyv": gyv * random.uniform(0.6, 1), "kiekis": 0.0, "sena": None}
            if dydis:
                d["d"] = dydis
            else:  # buldozeriuko debesėlis – įvairaus dydžio, kaip purslai
                d["dyd"], d["oras"] = self.ekskav_gumulo_dydis()
            self.ekskav_daleles.append(d)

    def ekskav_laisva_vieta(self, e, pv, x):
        """Kur daug sniego, bet ne ant kito buldozeriuko."""
        S = STULPELIS
        tarpas = self.ekskav_tarpas()
        kiti = [o["x"] for o in self.ekskavatoriai if o is not e and o["pav"] == pv[0]] + \
               [o["tikslas"][0] for o in self.ekskavatoriai if o is not e and o.get("tikslas") and o["tikslas"][2] == pv[0]]
        if not kiti:
            return x
        h, x0 = pv[5], pv[6]
        a, b = max(0, int((pv[2] - x0) // S)), min(len(h), int((pv[3] - x0) // S))
        for c in sorted(range(a, b), key=lambda c: -h[c])[:400]:
            xc = x0 + c * S
            if all(abs(xc - o) > tarpas for o in kiti):
                return xc
        return x

    def ekskav_atstumti(self, e, lo, hi):
        """Nusileidęs ant kito – pasislenka į artimiausią laisvą vietą. False – vietos nėra."""
        tarpas, pus = self.ekskav_tarpas(), self.ekskav_pus()
        kiti = [o["x"] for o in self.ekskavatoriai
                if o is not e and o["pav"] == e["pav"] and o["busena"] not in ("nera", "krenta")]
        vietos = [e["x"]] + [ox + z * tarpas for ox in kiti for z in (-1, 1)]
        for x in sorted(vietos, key=lambda v: abs(v - e["x"])):
            if lo + pus <= x <= hi - pus and all(abs(x - ox) >= tarpas - 0.5 for ox in kiti):
                e["x"] = x
                return True
        return False

    def ekskav_ieskoti(self, e, privaloma=False):
        """Ieško paviršiaus su daugiausia sniego (kitų užimtų vengia). True – iškeliauja ten."""
        S = STULPELIS
        uzimti = {o["pav"] for o in self.ekskavatoriai if o is not e and o["pav"] is not None}
        kandidatai = []
        for pv in self.ekskav_pavirsiai():
            kiek, c = self.ekskav_sniego_kiekis(pv[5], pv[6], pv[2], pv[3])
            if kiek > 15 * self.k:
                kandidatai.append((kiek * (0.2 if pv[0] in uzimti else 1.0), pv, pv[6] + c * S))
        if kandidatai:
            _, pv, x = random.choices(kandidatai, weights=[w for w, _, _ in kandidatai])[0]
            if pv[0] == e["pav"] and not privaloma:
                return False
            x = self.ekskav_laisva_vieta(e, pv, x)
        elif privaloma:
            visi = self.ekskav_pavirsiai()
            zeme = [pv for pv in visi if pv[0][0] == "zeme"] or visi
            if not zeme:
                return False
            pv = random.choice(zeme)
            x = self.ekskav_laisva_vieta(e, pv, random.uniform(pv[2], pv[3]))
        else:
            return False
        pus = self.ekskav_pus()
        if e["busena"] != "nera" and e["y"] is not None:  # pradingsta su sniego debesėliu
            self.ekskav_debesis(e["x"], e["y"] - 4 * self.ekskav_Pe, 14, -120 * self.k)
            if e["sena"]:
                self.papildomos.append(e["sena"])
        e.update(busena="nera", t=0.0, laukti=random.uniform(0.6, 1.4), pav=None, st=None,
                 kruvos_ilgis=0, kruvos_kryptis=None, tikslas=(max(pv[2] + pus, min(pv[3] - pus, x)), pv[4], pv[0]))
        return True

    def ekskav_atsirasti(self, e):
        if not e.get("tikslas"):
            if not self.ekskav_ieskoti(e, privaloma=True):
                e["laukti"] = e["t"] + 2.0
                return
        x, pagr, _ = e.pop("tikslas")
        e.update(x=x, y=pagr - 260 * self.k, vy=0.0, busena="krenta", t=0.0)

    def ekskav_kristi(self, e, dt):
        S = STULPELIS
        y0 = e["y"]
        e["vy"] += TRAUKA * self.k * dt
        e["y"] += e["vy"] * dt
        x = e["x"]
        pav = None
        for hwnd, st in self.langai.items():
            if st["l"] <= x < st["r"] and y0 <= st["t"] <= e["y"]:
                e.update(pav=("langas", hwnd), st=st)
                pav = self.ekskav_pavirsius(e)
                if pav is not None:
                    break
                e.update(pav=None, st=None)
        else:
            c = int(x // S)
            if 0 <= c < len(self.pagrindas) and self.pagrindas[c] is not None and e["y"] >= self.pagrindas[c]:
                for i, (c1, c2, pagr) in enumerate(self.zemes_ruozai):
                    if c1 <= c < c2:
                        e.update(pav=("zeme", i), st=None)
                        pav = self.ekskav_pavirsius(e)
                        break
        if pav is not None:
            if not self.ekskav_atstumti(e, pav[3], pav[4]):  # vietos nėra – keliauja kitur
                e["pav"] = None
                self.ekskav_ieskoti(e, privaloma=True)
                return
            # naujame paviršiuje dar nieko nestumia – kitaip priekyje gulintį sniegą palaikytų savo kauburiu
            e.update(busena="vaziuoja", t=0.0, vy=0.0, tikrinti=1.0, y=pav[2], kruvos_ilgis=0, kruvos_kryptis=None,
                     atgal=0)
            self.ekskav_debesis(e["x"], e["y"] - 1, 8, -90 * self.k)
        elif e["y"] > self.vh + 300 * self.k:
            e.update(busena="nera", t=0.0, laukti=0.5, pav=None, st=None, tikslas=None)

    def kelio_prof(self):
        """Kelio profilis (kauburiukai) – visada tokio pat ilgio kaip kelias."""
        kel = self.kelias
        prof = self.__dict__.get("kelio_profilis")
        if prof is None or len(prof) != len(kel):
            prof = self.kelio_profilis = kopu_profilis(len(kel), kopu_bangos(random, ((45 * self.k, 0.22),
                                                                                     (17 * self.k, 0.16))))
        return prof

    def kelio_ribos(self):
        """Kiek kiekviename stulpelyje gali pripustyti kelio sniego (px): kelio riba × kauburiukų profilis, o prie
        eglių kamienų – mažiau (kaip tikrai: po eglės šakomis sniego mažiau), kad kamienas matytųsi.
        Podėlyje, kol nepasikeitė eglės, riba ar profilis."""
        S = STULPELIS
        prof, maks = self.kelio_prof(), self.kelio_maks()
        egles = getattr(self, "egles", ())
        raktas = (len(prof), maks, id(prof), tuple(e["ribos"] for e in egles))
        pod = self.__dict__.get("_kelio_ribos")
        if pod is not None and pod[0] == raktas:
            return pod[1]
        rib = [maks * p for p in prof]
        n = len(rib)
        for e in egles:
            el, _, er, _ = e["ribos"]
            s_ = e.get("s") or max(1.0, (er - el) / 13)
            sab = EGLIU_SABLONAI[e.get("sab", 2)]
            cx = e["x0"] + len(sab[0]) * s_ / 2 if "x0" in e else (el + er) / 2
            w = max(2.5 * s_, 2 * S)  # duobutė apie kamieną
            kam = 0.5 * s_  # prie pat kamieno – tik pusė langelio (kamienas – 2 langeliai)
            for c in range(max(0, int((cx - w) // S)), min(n, int((cx + w) // S) + 1)):
                u = abs(c * S + S / 2 - cx) / w
                if u < 1:
                    rib[c] = min(rib[c], kam + (rib[c] - kam) * u * u)
        self._kelio_ribos = (raktas, rib)
        return rib

    def kelio_slinkimas(self, dt=0.0):
        """Kelio sniegas nesilaiko stačia siena: palikto kauburio galas (kur buvo verstuvas) pamažu nuslenka iki
        KELIO_NUOLYDIS šlaito – kitaip apsisukus buldozeriukui (ar jį išjungus) priešais eglę likdavo stati balta
        briauna, kuri ją perkirsdavo. Tik ten, kur verstuvas jo neremia. Vienas perėjimas per kadrą – nuslenka per
        keliolika kadrų. Be to, kas pusę sekundės paliktos krūvos pamažu patirpsta iki kelio ribos (KELIO_TIRPIMAS)."""
        kel = getattr(self, "kelias", None)
        if not kel:
            return
        S, n = STULPELIS, len(kel)
        self.kelio_tirpimo_laikas = self.__dict__.get("kelio_tirpimo_laikas", 0.0) + dt
        if self.kelio_tirpimo_laikas >= 0.5:
            tirpsta = KELIO_TIRPIMAS * self.k * self.kelio_tirpimo_laikas
            self.kelio_tirpimo_laikas = 0.0
            ribos = self.kelio_ribos()
            ta = tb = None
            for c in range(n):
                v, rb = kel[c], ribos[c]
                if v > rb + 0.01:
                    kel[c] = max(rb, v - tirpsta)
                    ta = c if ta is None else ta
                    tb = c
            if ta is not None:
                self.pazymeti_zeme(ta - 1, tb + 2)
        riba = KELIO_NUOLYDIS * S

        def remia(pav, x0):  # verstuvo (stumiančio) stulpeliai – ten krūva remiasi į jį ir neslenka
            sar = set()
            for e in self.ekskavatoriai:
                if e["busena"] == "vaziuoja" and e.get("pav") == pav and e.get("atgal", 0) <= 0 \
                        and e.get("verstuvas", 0.0) <= 0:
                    cp = int((e["x"] + e["kryptis"] * self.ekskav_pus() - x0) // S)
                    sar.update((cp, cp + e["kryptis"]))
            return sar
        zemes = {("zeme", i) for i in range(len(self.zemes_ruozai))}
        rem = set()
        for pav in zemes:
            rem |= remia(pav, 0)
        ab = nuslinkti(kel, 1, n, riba, rem)
        if ab:
            self.pazymeti_zeme(ab[0] - 1, ab[1] + 2)
        # Ir langų viršuje: ten buldozeriukų krūvos irgi lieka stačia siena: apsisukus
        # buldozeriukui ar jam nuvažiavus lange stūksojo verstuvo aukščio „pleištas“ su stačiu šonu. Tikrinami tik
        # langai, kuriuose buldozeriukai stūmė sniegą (st["kruvos"]), kol juose dar yra ką nuslinkti.
        for hwnd, st in self.langai.items():
            if not st.get("kruvos"):
                continue
            h, rem, pakito = st["h"], remia(("langas", hwnd), st["l"]), False
            for c1, c2 in st["matomi"]:  # tik matomose atkarpose (uždengtose sniegas lieka 0)
                if nuslinkti(h, c1 + 1, c2, riba, rem):
                    pakito = True
            if not pakito:
                if not rem:
                    st["kruvos"] = False
            elif not st["nesvarus"]:
                st["nesvarus"] = True
                self.nesvarus_langai.append(st)

    def ekskavatoriu_zingsnis(self, dt):
        self.ekskav_daleliu_zingsnis(dt)
        if not self.ekskavatoriai:
            return
        k = self.k
        pus, tarpas = self.ekskav_pus(), self.ekskav_tarpas()
        for e in self.ekskavatoriai:
            e["t"] += dt
            if e["busena"] == "nera":
                if e["t"] >= e["laukti"]:
                    self.ekskav_atsirasti(e)
                continue
            if e["busena"] == "krenta":
                self.ekskav_kristi(e, dt)
                continue
            pav = self.ekskav_pavirsius(e)
            if pav is None:  # langas uždarytas, sumažintas ar uždengtas – buldozeriukas nukrenta
                e.update(busena="krenta", vy=0.0, pav=None, st=None)
                continue
            h, x0, pagr, lo, hi = pav
            e["y"] = pagr
            if hi - lo < 3 * tarpas:  # per siaura (langą iš dalies uždengė kitas) – vos pavažiavęs atsimuštų nuo
                # kraštų ir „maltųsi“ į šonus; išvažiuoja kitur (kaip ieškodamas sniego), o jei nėra kur – stovi
                if not self.ekskav_ieskoti(e, privaloma=True):
                    e["x"] = min(max(e["x"], lo + pus), hi - pus) if hi - lo >= 2 * pus else (lo + hi) / 2
                continue
            v = 55 * k * e.get("greitis", 1.0)
            d = e["kryptis"]
            if e.get("atgal", 0) > 0:  # atsitraukia atbuline eiga, tada apsisuka
                e["atgal"] -= dt
                e["x"] = max(lo + pus, min(hi - pus, e["x"] - d * v * 0.6 * dt))
                e["ratai"] -= v * 0.6 * dt
                if e["atgal"] <= 0:
                    e["kryptis"], e["kruvos_ilgis"] = -d, 0
                continue
            S = STULPELIS
            for o in self.ekskavatoriai:
                if o is e or o["pav"] != e["pav"] or o["busena"] in ("nera", "krenta"):
                    continue
                dx = o["x"] - e["x"]
                if abs(dx) < tarpas * 0.9:  # jei kaip nors užvažiavo vienas ant kito – prasiskiria
                    e["x"] -= math.copysign((tarpas * 0.9 - abs(dx)) / 2, dx or 1)
                if dx * d <= 0:
                    continue
                priespriesa = o["kryptis"] == -d and o.get("atgal", 0) <= 0
                # tarp verstuvų (ar iki kito galo) liko mažiau nei abiejų kauburiai – susitiko
                laisva = abs(dx) - 2 * pus - e.get("kruvos_ilgis", 0) * S - \
                    (o.get("kruvos_ilgis", 0) * S if priespriesa else 0)
                if laisva < 2 * self.ekskav_Pe:
                    if priespriesa:
                        self.ekskav_susidurimas(e, o, pav)
                    else:
                        e["atgal"] = random.uniform(0.5, 0.9)
                    break
            if e.get("atgal", 0) > 0:
                continue
            e["x"] += e["kryptis"] * v * dt
            e["ratai"] += v * dt
            e["x"] = max(lo + pus, min(hi - pus, e["x"]))
            priekis = e["x"] + e["kryptis"] * pus
            krastas = priekis >= hi - 0.5 if e["kryptis"] > 0 else priekis <= lo + 0.5
            # Pro sniego senį ar eglutę – sklandžiai pakelia verstuvą ir pravažiuoja, po juo sniego neliečia. Kol pakeltas,
            # tikrinama su kauburio ilgiu, buvusiu pakeliant (kitaip kauburiui „dingus“ verstuvas trūkčiotų aukštyn-žemyn).
            v_ = e.get("verstuvas", 0.0)
            if v_ > 0:
                reikia = self.ekskav_po_seniu(e, priekis, e.get("kruva_pakeliant", 0))
            else:
                reikia = self.ekskav_po_seniu(e, priekis)
                if reikia:
                    e["kruva_pakeliant"] = e.get("kruvos_ilgis", 0)
            zings = dt / EKSKAV_VERSTUVO_LAIKAS
            v_ = e["verstuvas"] = min(1.0, v_ + zings) if reikia else max(0.0, v_ - zings)
            e["pakeltas"] = int(round(v_ * EKSKAV_PAKELIMAS))
            if v_ > 0:
                e["kruvos_ilgis"] = 0
            else:
                self.ekskav_stumti(e, pav, priekis, krastas)
            if krastas:
                e["kryptis"] = -e["kryptis"]
            e["tikrinti"] -= dt
            if e["tikrinti"] <= 0:
                e["tikrinti"] = random.uniform(3.0, 5.0)
                if self.ekskav_sniego_kiekis(h, x0, lo, hi)[0] < 15 * k or random.random() < 0.1:
                    self.ekskav_ieskoti(e)  # švaru – arba kartais tiesiog keliauja ten, kur sniego daugiau

    def kelio_maks(self):
        """Kelio sniego riba (px): snygis kelio aukštesnio nepripusto (sustumti kauburiai – aukštesni)."""
        return min(KELIO_AUKSTIS, self.n["max_aukstis"]) * self.k

    def ekskav_po_seniu(self, e, priekis, kruva=None):
        """Ar verstuvas dabar ties sniego seniu (tame pačiame paviršiuje). Tada buldozeriukas važiuoja toliau
        (už senio), bet sniego nestumia – kitaip stovintis senis liktų kabėti virš nuvalytos vietos."""
        seniai = getattr(self, "seniai", None)
        if not seniai or (e["pav"] is not None and e["pav"][0] == "zeme"):  # žemėje seniai – ant pusnų, ne kelyje
            return False
        senio_pus = SENIO_W * self.senio_Ps() * 0.36 + 2 * STULPELIS
        # visas buldozeriukas (jis valo ir po savimi – nuo galo iki verstuvo) ir priešais stumiamas kauburys
        d = e["kryptis"]
        kruva = e.get("kruvos_ilgis", 0) if kruva is None else kruva
        a, b = sorted((e["x"] - d * self.ekskav_pus(), priekis + d * (kruva + 2) * STULPELIS))
        for s_ in seniai:
            if s_["pav"] == e["pav"] and s_["busena"] in SENIO_ANT_PAVIRSIAUS + ("nukrenta",) and \
                    a < s_["x"] + senio_pus and s_["x"] - senio_pus < b:
                return True
        return False

    def ekskav_daleliu_zingsnis(self, dt):
        if not self.ekskav_daleles:
            return
        trauka = 700 * self.k
        base = self.pagrindas
        maks = self.n["max_aukstis"] * self.k
        S = STULPELIS
        # Krentantys gumulai ir trupiniai nusileidžia ant langų viršaus (ten, kur ir snaigės) arba ant žemės – ne
        # dingsta ore
        dezes = getattr(self, "segmentu_dezes", None) or ()
        nd = len(dezes)
        maks_l = self.n["max_aukstis_languose"] * self.k
        langams = kaupia(self.n, "kaupti_languose")
        oro_riba = 260 * self.k  # smulkūs trupiniai krenta lėčiau (oro pasipriešinimas)
        likusios = []
        for d in self.ekskav_daleles:
            y0 = d["y"]
            d["vy"] += trauka * dt
            if d.get("oras"):
                d["vx"] *= max(0.0, 1 - 1.5 * dt)
                if d["vy"] > oro_riba:
                    d["vy"] = oro_riba
            d["x"] += d["vx"] * dt
            d["y"] += d["vy"] * dt
            d["gyv"] -= dt
            if d["vy"] > 0 and nd:
                di = int(d["x"]) >> 6
                ant_lango = False
                for sy, x1, x2, hl, lx, st in (dezes[di] if 0 <= di < nd else ()):
                    if x1 <= d["x"] < x2:
                        ci = int((d["x"] - lx) // S)
                        # atkrito iš viršaus (nuo lango viršaus linijos): ir tada, kai sniegas tame stulpelyje ką tik
                        # pakilo virš dalelės (gumulai krenta vienas po kito) – kitaip ji „perlįsdavo“ per sniegą
                        if 0 <= ci < len(hl) and y0 < sy and sy - hl[ci] <= d["y"]:
                            pl = st["profilis"]
                            if d["kiekis"] > 0 and langams and hl[ci] < maks_l * pl[ci]:
                                nusodinti(hl, ci, d["kiekis"] / SVORIU_SUMA, maks_l, krastai=True, profilis=pl)
                                if not st["nesvarus"]:
                                    st["nesvarus"] = True
                                    self.nesvarus_langai.append(st)
                            ant_lango = True
                            break
                if ant_lango:
                    if d["sena"]:
                        self.papildomos.append(d["sena"])
                    continue
            c = int(d["x"] // S)
            kel = self.kelias  # buldozeriukų sniegas – ant kelio (priešais egles), ne į pusnis
            pav = base[c] - kel[c] if 0 <= c < len(kel) and base[c] is not None else None
            if d["gyv"] <= 0 or d["y"] > self.vh or (d["vy"] > 0 and pav is not None and d["y"] >= pav):
                if d["kiekis"] > 0 and pav is not None and d["y"] >= pav and kaupia(self.n, "kaupti_apacioje"):
                    nusodinti(kel, c, d["kiekis"] / SVORIU_SUMA, maks)  # nustumtas nuo lango
                    self.pazymeti_zeme(c - 8, c + 9)
                if d["sena"]:
                    self.papildomos.append(d["sena"])
            else:
                likusios.append(d)
        self.ekskav_daleles = likusios

    def piesti_gumulus(self, i_langa, visas, senio):
        """Sniego gumulai – su kontūru, kad matytųsi ir ant balto lango. senio=True – senių purslai („d“): senio
        gylyje, už eglučių (piešiami kartu su seniais); False – buldozeriukų sniegas (priešais, po jų)."""
        if not self.ekskav_daleles:
            return
        Pe = getattr(self, "ekskav_Pi", None) or max(1, int(round(self.P * 1.5)))
        d_ = max(2, Pe)
        kontur, baltas = self.g.teptukas(SNIEGO_KONTURAS), self.g.teptukas(SNIEGAS)
        dengti = []
        for d in self.ekskav_daleles:
            if ("d" in d) != senio:
                continue
            x, y, dd = int(d["x"]), int(d["y"]), d.get("d") or d.get("dyd", d_)
            nauja = self.ribos(x - 1, y - dd - 1, x + dd + 1, y + 1)
            if nauja:
                user32.FillRect(self.fdc, ctypes.byref(wintypes.RECT(*nauja)), kontur)
                vidus = self.ribos(x, y - dd, x + dd, y)
                if vidus:
                    user32.FillRect(self.fdc, ctypes.byref(wintypes.RECT(*vidus)), baltas)
                if senio:
                    dengti.append(nauja)
            if not visas:
                if d["sena"]:
                    i_langa.append(d["sena"])
                if nauja:
                    i_langa.append(nauja)
            d["sena"] = nauja
        self.uzdengti_daug(dengti, i_langa)

    def piesti_ekskavatorius(self, i_langa, visas):
        if not self.ekskavatoriai and not self.ekskav_daleles:
            return
        Pe = getattr(self, "ekskav_Pe", None) or max(1, int(round(self.P * 1.5)))  # buldozeriukų gali ir nebūti
        W, H = round(EKSKAV_PLOTIS * Pe), round(EKSKAV_AUKSTIS * Pe)  # kaip juostoje (kurti_ekskavatorius)
        for e in self.ekskavatoriai:
            nauja = None
            if e["busena"] != "nera" and e["y"] is not None:
                nr = EKSKAV_KADRO_NR[(int(e["ratai"] / (2 * Pe)) % 2, e["kryptis"] < 0, e.get("pakeltas", 0))]
                x0 = int(e["x"] - W / 2)
                nauja = self.permatomas_kopijavimas((W, H), x0, int(e["y"]) - H + 1, self.ekskav_sprite["dc"],
                                                    (e.get("korpusas", 0) * len(EKSKAV_KADRAI) + nr) * W, 0)
                if nauja:
                    self.piesti_svyturely(e, x0, int(e["y"]) - H + 1, Pe)
                    self.piesti_stikla(e, x0, int(e["y"]) - H + 1, Pe)
            if not visas:
                if e["sena"]:
                    i_langa.append(e["sena"])
                if nauja:
                    i_langa.append(nauja)
            e["sena"] = nauja
        self.piesti_gumulus(i_langa, visas, senio=False)  # buldozeriukų sniegas – priešais juos

    def piesti_stikla(self, e, x0, y0, Pe):
        """Kabinos stiklas: šviesesnis viršus, tamsesnė apačia, kartais blyksteli."""
        kaire = e["kryptis"] < 0
        sx1, sy1, sx2, sy2 = ekskav_stiklo_vieta(Pe, kaire)
        w, h = sx2 - sx1, sy2 - sy1
        if "stiklo_faze" not in e:
            e["stiklo_faze"] = random.uniform(0, EKSKAV_BLYKSNIO_PERIODAS)
        blyksi = (time.perf_counter() + e["stiklo_faze"]) % EKSKAV_BLYKSNIO_PERIODAS < 0.12
        FillRect, RECT, tept = user32.FillRect, wintypes.RECT, self.g.teptukas
        for x1, x2, y, spalva in ekskav_stiklo_juostos(w, h, blyksi):
            rr = self.ribos(x0 + sx1 + x1, y0 + sy1 + y, x0 + sx1 + x2, y0 + sy1 + y + 1)
            if rr:
                FillRect(self.fdc, ctypes.byref(RECT(*rr)), tept(spalva))

    def piesti_svyturely(self, e, x0, y0, Pe):
        """Mirksintis švyturėlis ant buldozeriuko kabinos (piešiama ant jau nupiešto buldozeriuko, jo ribose)."""
        u = (time.perf_counter() / EKSKAV_SVYT_PERIODAS + e.get("svyt_faze", 0.0)) % 1.0
        c = EKSKAV_SVYT_STULPELIS if e["kryptis"] >= 0 else EKSKAV_PLOTIS - 1 - EKSKAV_SVYT_STULPELIS
        rr = self.ribos(x0 + round(c * Pe), y0, x0 + round((c + 1) * Pe), y0 + round(Pe))  # Pe – trupmeninis
        if rr:
            user32.FillRect(self.fdc, ctypes.byref(wintypes.RECT(*rr)),
                            self.g.teptukas(EKSKAV_SVYT_SPALVOS[0 if u < EKSKAV_SVYT_SVIECIA else 1]))

    def statiniai_plotai(self):
        """Kur statiniame sluoksnyje kas nors nupiešta (eglės, pusnys, langų sniegas, girliandos)."""
        S = STULPELIS
        maks = int(self.n["max_aukstis"] * self.k) + 4
        sar = [e["ribos"] for e in self.egles] + [g["ribos"] for g in getattr(self, "girliandos", ())]
        sar += [(c1 * S, pagr - maks, c2 * S, pagr + 2) for c1, c2, pagr in self.zemes_ruozai]
        sar += [st["sritis"] for st in self.langai.values()]
        return sar

    @staticmethod
    def supimo_kadrai(f, laikas, supimas, sin):
        """Kiek posūkio kadrų pasvirusi nesisukanti snaigė: svyrimas – pagal tą patį netolygų svyravimą kaip
        zingsnis() (šoninis greitis), t. y. pasvyra į tą pusę, į kurią tuo metu slenka."""
        fz = laikas * f[SDAZN] + f[SFAZE]
        sfz = ((sin(fz) + 0.45 * sin(fz * 2.37 + f[SFAZE] * 3.1))
               * (0.775 + 0.225 * sin(laikas * f[SDAZN] * 0.23 + f[SFAZE] * 1.7)) * 0.69)
        return int(sfz * supimas / TIPU_PERIODAI[f[STIPAS]] * SUKIMO_KADRAI + 100.5) - 100

    def piesti_snaiges(self, i_langa, visas, toli):
        """toli=True – tolimos snaigės: po jų statinio sluoksnio daiktai (eglės, pusnys, girliandos) vėl
        uždedami ant viršaus (TransparentBlt su permatoma spalva), todėl snaigės atrodo krentančios už jų."""
        fdc, ribos = self.fdc, self.ribos
        plotai = self.statiniai_plotai() if toli else None
        # aukščiau už visus statinius daiktus esančioms snaigėms uždengimo tikrinti nereikia (dauguma snaigių)
        plotu_virsus = min(pt for _, pt, _, _ in plotai) if plotai else 0
        # Snaigė visa ekrane (beveik visada) – TransparentBlt tiesiai, be permatomas_kopijavimas() ir ribos()
        # kvietimų ir kortežų: 1000 snaigių – 2000 Python kvietimų per kadrą mažiau. Kraštuose –
        # kaip anksčiau, su apkirpimu; rezultatas tas pats.
        TB, vw, vh, fonas = msimg32.TransparentBlt, self.vw, self.vh, SPRAITO_FONAS_RGB
        sukimo_k = SUKIMO_KADRAI / (2 * math.pi)
        g = self.g
        Ellipse, Polyline, SetViewportOrgEx, PatBlt = gdi32.Ellipse, gdi32.Polyline, gdi32.SetViewportOrgEx, gdi32.PatBlt
        atlasas = self.snaigiu_atlasas
        sukasi = self.n["snaiges_sukasi"]
        laikas = time.perf_counter()
        # supimasis (tik nesisukant): kampas laipsniais pagal svyravimą; 0 – išjungta
        supimas = 0.0 if sukasi else min(SUPIMOSI_MAX, SUPIMOSI_KAMPAS * self.n["svyravimas"] / NUMATYTI["svyravimas"])
        sin = math.sin
        esamas_tipas = -1
        iprastos = None
        if atlasas:
            adc, kopijuoti = atlasas["dc"], self.permatomas_kopijavimas
            iprastos = atlasas.get("iprastos")
            if iprastos is not None:
                atlasas = None  # įprastos snaigės – atskiras kelias žemiau
            else:
                vietos = atlasas["vietos"]
        # sukimasis: kadras parenkamas pagal laiką – snaigės būsenoje nieko nekeičiama
        uzdengti = []
        piesti = []  # įprastos snaigės: pirma visi šešėliai, tada visos snaigės (šešėlis neužgula kitos snaigės)
        for f in self.snaiges:
            if (f[SGYLIS] < GILUMO_RIBA) != toli:
                continue
            ix, iy, d = int(f[SX]), int(f[SY]), f[SDYDIS]
            langelis = None
            if atlasas:
                kadrai = vietos[f[STIPAS]]
                if len(kadrai) > 1 and sukasi:
                    # pixel art šuoliukai kiek greitesni – kitaip lėta snaigė persijungtų tik kas kelias sekundes
                    ax, w, h = kadrai[int(laikas * 1.5 * abs(f[SSUKIMAS]) / PIKS_SUKIMO_ZINGSNIS[f[STIPAS]]
                                          + f[SSUK_FAZE] * 2) & 1]
                else:
                    ax, w, h = kadrai[0]
                kx, ky = ix - w // 2, iy - h // 2
                if kx >= 0 and ky >= 0 and kx + w <= vw and ky + h <= vh and w > 0 and h > 0:
                    TB(fdc, kx, ky, w, h, adc, ax, 0, w, h, fonas)
                    nauja = (kx, ky, kx + w, ky + h)
                else:
                    nauja = kopijuoti((w, h), kx, ky, adc, ax, 0)
            else:
                if iprastos is not None:
                    zingsnis, mapa = iprastos[f[STIPAS]]
                    langelis = mapa.get(int(f[SR] / zingsnis + 0.5) if zingsnis else f[SSKERSMUO])
                if langelis is not None:
                    w, c, kadrai = langelis
                    if len(kadrai) > 1:
                        # pradinis pasukimas – iš SFAZE (atsitiktinė, 0…2π), sukimasis – kaip piešiant tiesiogiai
                        k_ = int(f[SFAZE] * sukimo_k)
                        if sukasi:
                            k_ += int((laikas * f[SSUKIMAS] / TIPU_PERIODAI[f[STIPAS]] + f[SSUK_FAZE]) % 1.0
                                      * SUKIMO_KADRAI)
                        elif supimas:
                            k_ += self.supimo_kadrai(f, laikas, supimas, sin)
                        ax, ay = kadrai[k_ % SUKIMO_KADRAI]
                    else:
                        ax, ay = kadrai[0]
                    kx, ky = ix - c, iy - c
                    if kx >= 0 and ky >= 0 and kx + w <= vw and ky + w <= vh and w > 0:
                        TB(fdc, kx, ky, w, w, adc, ax, ay, w, w, fonas)
                        nauja = (kx, ky, kx + w, ky + w)
                    else:
                        nauja = kopijuoti((w, w), kx, ky, adc, ax, ay)
                else:
                    # +3 dešinėje/apačioje – šešėlis pastumtas 1 tašku
                    nauja = ribos(ix - d - 1, iy - d - 1, ix + d + 3, iy + d + 3)
            if nauja and not atlasas and langelis is None:
                taskai = f[STASKAI]
                if taskai is not None:
                    if sukasi:
                        taskai = taskai[int((laikas * f[SSUKIMAS] / TIPU_PERIODAI[f[STIPAS]] + f[SSUK_FAZE])
                                            % 1.0 * SUKIMO_KADRAI)]
                    elif supimas:
                        taskai = taskai[self.supimo_kadrai(f, laikas, supimas, sin) % SUKIMO_KADRAI]
                    else:
                        taskai = taskai[0]
                piesti.append((ix, iy, f[STIPAS], taskai, f[SSKERSMUO]))
            if not visas:
                sena = f[SSENA]
                if sena and nauja and abs(sena[0] - nauja[0]) < 24 and abs(sena[1] - nauja[1]) < 24:
                    i_langa.append((min(sena[0], nauja[0]), min(sena[1], nauja[1]),
                                    max(sena[2], nauja[2]), max(sena[3], nauja[3])))
                else:
                    if sena:
                        i_langa.append(sena)
                    if nauja:
                        i_langa.append(nauja)
            f[SSENA] = nauja
            if toli and nauja and plotai and nauja[3] > plotu_virsus:
                l_, t_, r_, b_ = nauja
                for pl, pt, pr, pb in plotai:
                    if r_ > pl and l_ < pr and b_ > pt and t_ < pb:
                        uzdengti.append(nauja)
                        break


        if piesti:
            SelectObject = gdi32.SelectObject
            # Koordinatės – nuo snaigės centro (SetViewportOrgEx); pradžia grąžinama tik pabaigoje.
            for poslinkis in (1, 0):
                if poslinkis:
                    SelectObject(fdc, g.piestukas(SNAIGES_SESELIS))
                    SelectObject(fdc, g.teptukas(SNAIGES_SESELIS))
                for ix, iy, tipas, taskai, D in piesti:
                    if not poslinkis and tipas != esamas_tipas:
                        esamas_tipas = tipas
                        SelectObject(fdc, g.piestukas(TIPU_SPALVOS[tipas]))
                        SelectObject(fdc, g.teptukas(TIPU_SPALVOS[tipas]))
                    SetViewportOrgEx(fdc, ix + poslinkis, iy + poslinkis, None)
                    if taskai is not None:
                        Polyline(fdc, taskai[0], taskai[1])
                    else:
                        a = D // 2
                        if D <= 2:  # 1–2 taškų „rutuliukas“ – kvadratėlis (Ellipse tokio mažo tvarkingai nenupiešia)
                            PatBlt(fdc, -a, -a, D, D, PATCOPY)
                        else:
                            Ellipse(fdc, -a, -a, D - a, D - a)
            SetViewportOrgEx(fdc, 0, 0, None)

        if uzdengti:
            TB = msimg32.TransparentBlt
            for l_, t_, r_, b_ in uzdengti:
                TB(fdc, l_, t_, r_ - l_, b_ - t_, self.sdc, l_, t_, r_ - l_, b_ - t_, PERMATOMA_RGB)

    def piesti_pustomas(self, i_langa, visas):
        if not self.pustomos:
            return
        d = max(1, int(round(self.P * 0.7)))
        teptukas = self.g.teptukas(SNIEGAS)
        for p in self.pustomos:
            x, y = int(p["x"]), int(p["y"])
            nauja = self.ribos(x, y - d, x + d, y)
            if nauja:
                user32.FillRect(self.fdc, ctypes.byref(wintypes.RECT(*nauja)), teptukas)
            if not visas:
                if p["sena"]:
                    i_langa.append(p["sena"])
                if nauja:
                    i_langa.append(nauja)
            p["sena"] = nauja

    def piesti_bumbulus_kadre(self, i_langa, visas):
        for b in self.bumbulai:
            nauja = None
            if b["y"] is not None and b["busena"] != "nera":
                kadras, zemyn, apkirpti = self.bumbulo_vaizdas(b)
                x0 = int(b["x"] - b["c"])
                y0 = int(b["y"] - b["aukstis"] - b["r"] - b["c"] + zemyn) + 1
                # Niekas – žemiau paviršiaus pagrindo (užduočių juostos, lango viršaus): riedant pasisukęs žemyn
                # snapelis išlįsdavo už ekrano apačios linijos.
                atr = self.bumbulo_atrama(b, b["x"]) if b.get("pav") else None
                riba = int(atr[0] + atr[3]) if atr is not None else None
                if apkirpti:
                    riba = int(b["y"]) + 1 if riba is None else min(riba, int(b["y"]) + 1)
                nauja = self.permatomas_kopijavimas((b["W"], b["W"]), x0, y0, b["sprite"]["dc"],
                                                    kadras * b["W"], 0, b["l"], b["rr"], riba)
                if nauja:  # toli, kaip seniai: už eglių ir kelio
                    self.uzdengti_eglemis(nauja)
            if not visas:
                if b["sena"]:
                    i_langa.append(b["sena"])
                if nauja:
                    i_langa.append(nauja)
            b["sena"] = nauja
        for sk in self.skeveldros:
            nauja = None
            if not (sk["laikas"] < 0.5 and int(sk["laikas"] * 12) % 2 == 0):  # prieš dingdamos pamirksi
                x, y, d = int(sk["x"]), int(sk["y"]), sk["d"]
                nauja = self.ribos(x, y - d, x + d, y)
                if nauja:
                    user32.FillRect(self.fdc, ctypes.byref(wintypes.RECT(*nauja)), self.g.teptukas(sk["spalva"]))
            if not visas:
                if sk["sena"]:
                    i_langa.append(sk["sena"])
                if nauja:
                    i_langa.append(nauja)
            sk["sena"] = nauja

    # ------------------------------------------------------------ pagrindinis ciklas

    def matuoti_darbus(self):
        """Stabtelėjimų diagnostika. Visi tkinter laikmačio darbai (ne kadrai), įjungus diagnostiką, matuojami:
        kada prasidėjo ir baigėsi. Kadrui pavėlavus > 40 ms žurnale matyti, kuris darbas tuo metu vyko, kiek truko
        Python šiukšlių surinkimas ir kiek lieka nepaaiškinta (tada laiką užėmė Windows ar pats tkinter)."""
        self._kitu_darbai = []  # (pavadinimas, pradžia, pabaiga) nuo paskutinio kadro
        self._gc_ms, self._gc_pradzia = 0.0, 0.0
        # Windows pranešimai, kurie vykdo mūsų Python kodą tkinter įvykių ciklo viduje (ne laikmačiuose):
        # langų įvykių kabliukas (kiekvienas kitų programų lango pajudėjimas) ir perdangos langų procedūros
        self._ivykiai_n, self._ivykiai_ms = 0, 0.0
        self._zinutes_n, self._zinutes_ms, self._zinuciu_gylis = 0, 0.0, 0
        self._kadro_pabaiga, self._gijos_cpu_pab = time.perf_counter(), 0.0
        tikras = self.root.after

        def after(ms, func=None, *args):
            if func is None or not ZURNALAS.ijungtas or func == self.kadras:
                return tikras(ms, func, *args)

            def matuojamas(*a):
                t = time.perf_counter()
                try:
                    return func(*a)
                finally:
                    if len(self._kitu_darbai) < 200:
                        self._kitu_darbai.append((getattr(func, "__qualname__", "?").replace("Sniegas.", ""), t,
                                                  time.perf_counter()))
            return tikras(ms, matuojamas, *args)
        self.root.after = after

        def gc_matas(faze, info):
            if not ZURNALAS.ijungtas:
                self._gc_pradzia = 0.0
                return
            if faze == "start":
                self._gc_pradzia = time.perf_counter()
            elif self._gc_pradzia:
                self._gc_ms += (time.perf_counter() - self._gc_pradzia) * 1000
        gc.callbacks.append(gc_matas)

    def stabtelejimas(self, planuota, pradzia):
        """Kadras pavėlavo > 40 ms: kas vyko tarp suplanuoto laiko ir tikrosios pradžios."""
        velavo = (pradzia - planuota) * 1000
        darbai = []
        for pav, a, b in self._kitu_darbai:
            persidengia = (min(b, pradzia) - max(a, planuota)) * 1000  # kiek šis darbas užėmė vėlavimo laiko
            if persidengia > 0.5:
                darbai.append((persidengia, pav))
        darbai.sort(reverse=True)
        paaiskinta = sum(ms for ms, _ in darbai)
        self.d_stabtelejimai += 1
        if self.d_stabt_irasyta >= 20:  # per vieną suvestinės laikotarpį – ne daugiau (kad žurnalas neišpūstų)
            return
        self.d_stabt_irasyta += 1
        tarp = (pradzia - self._kadro_pabaiga) * 1000
        gija = gijos_cpu_ms() - self._gijos_cpu_pab
        ZURNALAS.rasyti(f"STABTELĖJIMAS: kadras pavėlavo {velavo:.0f} ms | programos darbai tuo metu {paaiskinta:.0f} ms"
                        + (": " + ", ".join(f"{pav} {ms:.0f} ms" for ms, pav in darbai[:4]) if darbai else "")
                        + f" | šiukšlių surinkimas {self._gc_ms:.0f} ms | nepaaiškinta (Windows / tkinter) "
                        f"{max(0.0, velavo - paaiskinta):.0f} ms | langai judėjo: {'taip' if self.langai_judejo else 'ne'}"
                        f" | langų įvykiai {self._ivykiai_n} ({self._ivykiai_ms:.0f} ms), perdangos žinutės "
                        f"{self._zinutes_n} ({self._zinutes_ms:.0f} ms) | gija dirbo {gija:.0f} ms iš {tarp:.0f} ms tarp kadrų")

    def letas_kadras(self, darbas, langai, fizika, atstatymas, piesimas, ekranas, pilnas):
        """Kadras pats užtruko > 33 ms (2 ekrano atnaujinimai): kuri jo dalis. Tai mūsų kodas – jį galima taisyti."""
        self.d_leti_kadrai += 1
        if self.d_leti_irasyta >= 20:
            return
        self.d_leti_irasyta += 1
        dalys = sorted(self._fizikos_dalys.items(), key=lambda kv: -kv[1])[:4]
        ZURNALAS.rasyti(f"LĖTAS KADRAS: {darbas:.0f} ms | langų skaitymas {langai:.1f} | fizika {fizika:.1f} ("
                        + ", ".join(f"{k} {v:.1f}" for k, v in dalys) + f") | atstatymas {atstatymas:.1f} | piešimas "
                        f"{piesimas:.1f} | ekranas {ekranas:.1f} ms ({self._ekrano_kv} kop.) | pilnas perpiešimas: "
                        f"{'taip' if pilnas else 'ne'} | šiukšlių surinkimas {self._gc_ms:.0f} ms | snaigės {len(self.snaiges)}"
                        f" | langai {len(self.langai)}")

    def kadras(self):
        pradzia = time.perf_counter()
        intervalas = pradzia - self.paskutinis
        dt = min(0.1, intervalas)
        P = self.vsync_periodas
        if P:  # ekranas sniegą parodo tik atnaujinimo metu – judėjimas tiksliai tiek, kiek ekrano atnaujinimų praėjo
            dt = min(0.1, max(1, round(intervalas / P)) * P)
        self.paskutinis = pradzia
        try:
            # langas pajudėjo – perskaitome iškart (bet ne dažniau kaip kas 30 ms, kai tempiama)
            if self.langai_judejo and pradzia - self.paskutinis_langu_skaitymas >= 0.03:
                self.perskaityti_langus()
                # Tempiant langą Windows kartais „pameta“ perdangos vaizdo dalis – matėsi tose vietose, kurios
                # pačios retai persipiešia (eglės, sniegas ekrano apačioje). Kol langas juda – šios sritys
                # kas kadrą kopijuojamos iš naujo, o jam nurimus – vieną kartą visas kadras.
                self.statiniu_blitas = True
                self.paskutinis_judejimas = pradzia
                self.laukia_pilno_blito = True
            langu_ms = (time.perf_counter() - pradzia) * 1000  # be stabtelėjimo įrašymo į žurnalą (žr. žemiau)
            if self.rodoma and self.buferiai:
                tarpas = pradzia - self.kitas_kadras  # kiek vėliau nei suplanuota (užstrigo programa ar Windows)
                if tarpas > self.d_velavimas:
                    self.d_velavimas = tarpas
                # > 2 s – greičiausiai kompiuteris miegojo ar ekranas buvo užrakintas, tai ne stabtelėjimas
                if 0.04 < tarpas < 2.0 and ZURNALAS.ijungtas and getattr(self, "diag_laikas", None):
                    self.stabtelejimas(self.kitas_kadras, pradzia)
                # Tolygumas: kiek tarpas tarp kadrų nukrypsta nuo idealaus (1/fps). Net kai kadrų per sekundę
                # pakanka, nevienodi tarpai akiai atrodo kaip trūkčiojimas.
                if intervalas < 0.5:
                    nuokr = (intervalas - (self.vsync_kas * P if P else 1 / self.n["fps"])) * 1000
                    self.d_nuokr_kv += nuokr * nuokr
                    self.d_nuokr_n += 1
                    if nuokr > 0.5 * 1000 / self.n["fps"]:
                        self.d_velu_kadrai += 1
                # Laiko skaidinys: fizika (judėjimas, kaupimas), buferis (piešimas atmintyje) ir ekranas
                # (kopijavimas į langą) – kad optimizuotume tai, kas iš tikrųjų lėta, o ne spėliotume.
                t0 = time.perf_counter()
                buvo_pilnas = self.pilnas_perpiesimas
                self.zingsnis(dt, pradzia)
                t1 = time.perf_counter()
                self._piesiama = True
                try:
                    self.piesti()
                finally:
                    self._piesiama = False
                t2 = time.perf_counter()
                fizika = (t1 - t0) * 1000
                ekranas = self._ekrano_ms
                atstatymas = self._atstatymo_ms
                buferis = (t2 - t1) * 1000 - ekranas - atstatymas  # piešimas (be atstatymo)
                self.b_fizika += fizika
                self.b_buferis += buferis
                self.b_atstatymas += atstatymas
                self.b_ekranas += ekranas
                self.b_kopijos += self._ekrano_kv
                self.d_fizika += fizika
                self.d_buferis += buferis
                self.d_atstatymas += atstatymas
                self.d_ekranas += ekranas
                self.d_kopijos += self._ekrano_kv
                self.kadru_skaitliklis += 1
                darbas = langu_ms + (t2 - t0) * 1000  # be stabtelėjimo įrašymo į žurnalą – tai ne kadro darbas
                self.darbo_ms += darbas
                self.d_kadrai += 1
                self.d_darbas += darbas
                if darbas > self.d_darbas_max:
                    self.d_darbas_max = darbas
                if darbas > 33 and ZURNALAS.ijungtas and getattr(self, "diag_laikas", None):
                    self.letas_kadras(darbas, langu_ms, fizika, atstatymas, buferis, ekranas, buvo_pilnas)
        except Exception as e:
            self.klaida(e)
        self._kitu_darbai.clear()
        self._gc_ms = 0.0
        self._ivykiai_n, self._ivykiai_ms, self._zinutes_n, self._zinutes_ms = 0, 0.0, 0, 0.0
        if ZURNALAS.ijungtas:
            self._kadro_pabaiga, self._gijos_cpu_pab = time.perf_counter(), gijos_cpu_ms()
        if not self.rodoma:  # paslėpta – tik retkarčiais patikriname, ar vėl rodyti
            self.kitas_kadras = time.perf_counter()
            self.root.after(250, self.kadras)
            return
        # Tvarkaraštis pagal fiksuotą žingsnį, o ne „laukti N ms po kadro“ – tolygesnis tempas.
        periodas = 1 / self.n["fps"]
        dabar = time.perf_counter()
        ritmas = self.ekrano_ritmas.gauti() if self.ekrano_ritmas.veikia else None
        if ritmas:
            # Sinchronizuota su ekranu: kadras pradedamas ~2 ms po ekrano atnaujinimo (vblank) ir kas n atnaujinimų
            # (30 kadrų/s 60 Hz ekrane – kas antrą). Tada jis visada spėja iki kito atnaujinimo ir kiekvienas
            # kadras ekrane išbūna vienodai. Be to 30 kadrų/s su 59,94 Hz „slysta“: kadras kartais rodomas 1,
            # kartais 3 atnaujinimus – tai ir matėsi kaip trūkčiojimas (60 kadrų/s atrodė sklandžiau).
            P, vblank = ritmas
            n = max(1, round(periodas / P))
            self.vsync_periodas, self.vsync_kas = P, n
            anksciausiai = pradzia + n * P - P * 0.5
            faze = min(VSYNC_FAZE, P * 0.15)  # 120 Hz ir daugiau – arčiau atnaujinimo, kad liktų laiko darbui
            k = math.ceil((anksciausiai - vblank - faze) / P)
            self.kitas_kadras = vblank + k * P + faze
        else:
            self.vsync_periodas = 0.0
            self.kitas_kadras += periodas
        if self.kitas_kadras < dabar:
            self.kitas_kadras = dabar
        self.root.after(max(1, int(round((self.kitas_kadras - dabar) * 1000))), self.kadras)

    def sniego_vejas(self, dt, vejas_px):
        """Kopos lėtai slenka pavėjui, o stipresnis vėjas nupučia sniegą nuo keterų į pavėjinę pusę."""
        if not kaupia(self.n, "kaupti_apacioje"):
            return
        h, base, prof = self.aukstis, self.pagrindas, self.zemes_profilis
        n = len(h)
        maks = self.n["max_aukstis"] * self.k
        self.kopu_laikas += dt
        if self.kopu_laikas >= 2.0:
            self.kopu_poslinkis -= vejas_px * 0.05 * self.kopu_laikas
            self.kopu_laikas = 0.0
            self.skaiciuoti_kopas()
            prof = self.zemes_profilis
            kauke = self.zemes_kauke
            sust = self.sustumta
            for c in range(n):
                riba = maks * prof[c]
                if h[c] > riba:
                    if sust[c]:  # valytuvo sustumtas kauburys – jis tik pamažu nuslūgsta, o ne nukerpamas
                        continue
                    h[c] = riba
                    kauke[c] = 1
                    self.zemes_nesvaru = True
                elif sust[c]:
                    sust[c] = 0
        self.pustymo_laikas += dt
        if self.pustymo_laikas < 0.5:
            return
        self.pustymo_laikas = 0.0
        # Sniegas „sėda“: per statūs šlaitai pamažu nuslūgsta (natūralus byrėjimo kampas) – be aštrių smailių.
        kauke = self.zemes_kauke
        pakito = False
        riba = 1.3 * self.k  # didžiausias aukščių skirtumas tarp gretimų stulpelių (~25°)
        kryptis = self.slugimo_kryptis = -getattr(self, "slugimo_kryptis", 1)
        for c in (range(n - 1) if kryptis > 0 else range(n - 2, -1, -1)):
            j = c + 1
            if base[c] is None or base[j] != base[c]:
                continue
            skirt = h[c] - h[j]
            if skirt > riba + 0.2:  # mažesni nei ~0,05 px pokyčiai ekrane nesimato – jų neskaičiuojame ir neperpiešiame
                m = (skirt - riba) * 0.25
                h[c] -= m
                h[j] += m
            elif skirt < -riba - 0.2:
                m = (-skirt - riba) * 0.25
                h[j] -= m
                h[c] += m
            else:
                continue
            kauke[c] = kauke[j] = 1
            pakito = True
        if pakito:
            self.zemes_nesvaru = True
        stiprumas = abs(self.vejas) / 10
        if stiprumas < 0.2:
            return
        d = 1 if self.vejas > 0 else -1
        kiekis = 0.6 * stiprumas
        # einama prieš vėją, kad tas pats sniegas per vieną kartą nenukeliautų per kelis stulpelius
        for c in (range(n - 2, -1, -1) if d == 1 else range(1, n)):
            j = c + d
            if base[c] is None or base[j] != base[c] or h[c] < 1:
                continue
            m = min(kiekis * min(1.0, h[c] / 10), maks * prof[j] - h[j])
            if m > 0.05:
                h[c] -= m
                h[j] += m
                kauke[c] = kauke[j] = 1
                pakito = True
        if pakito:
            self.zemes_nesvaru = True

    def pustymo_zingsnis(self, dt, vejas_px):
        """Pūstant vėjui nuo kopų keterų pakeliamos sniego dalelės: jos šokuoja pavėjui palei paviršių ir nusėda
        ten, kur yra vietos (įdubose, už kliūčių) – sniegas apačioje nuolat keičiasi, o ne sustingsta."""
        h, base, prof = self.aukstis, self.pagrindas, self.zemes_profilis
        n = len(h)
        S, k = STULPELIS, self.k
        maks = self.n["max_aukstis"] * k
        gyvos = []
        for p in self.pustomos:
            p["vx"] += (vejas_px * 1.3 - p["vx"]) * min(1.0, dt * 3)
            p["vy"] += 220 * k * dt
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["gyv"] -= dt
            c = int(p["x"] // S)
            if not 0 <= c < n or base[c] is None or p["gyv"] <= 0:
                if p["sena"]:
                    self.papildomos.append(p["sena"])
                continue  # išskrido už ekrano – sniegas „išpustytas“, jį papildys snygis
            pav = base[c] - h[c]
            if p["y"] >= pav and p["vy"] > 0:
                if h[c] < maks * prof[c] or p["gyv"] < 0.4:
                    if kaupia(self.n, "kaupti_apacioje"):
                        nusodinti(h, c, p["kiekis"] / SVORIU_SUMA, maks, profilis=prof, sust=self.sustumta)
                    self.pazymeti_zeme(c - 8, c + 9)
                    if p["sena"]:
                        self.papildomos.append(p["sena"])
                    continue
                p["y"] = pav  # vietos nėra – atšoka ir skrenda toliau
                p["vy"] = -p["vy"] * 0.5 - random.uniform(10, 30) * k
            gyvos.append(p)
        self.pustomos = gyvos
        stiprumas = abs(self.vejas) / 10
        if stiprumas < 0.06 or not kaupia(self.n, "kaupti_apacioje") or len(gyvos) > 220:
            return
        norma = (stiprumas - 0.04) * 50 * dt * n / 640
        for _ in range(int(norma) + (random.random() < norma % 1)):
            # iš trijų atsitiktinių vietų pučiama aukščiausia – vėjas pirmiausia „nugraužia“ keteras
            c = max((random.randrange(n) for _ in range(3)), key=h.__getitem__)
            if base[c] is None or h[c] < 2:
                continue
            kiekis = min(h[c] * 0.3, 0.8 + stiprumas)
            h[c] -= kiekis
            self.pazymeti_zeme(c - 1, c + 2)
            self.pustomos.append({"x": c * S + S / 2, "y": base[c] - h[c] - 1,
                                  "vx": vejas_px * random.uniform(0.6, 1.2), "vy": -random.uniform(15, 45) * k,
                                  "gyv": random.uniform(2, 5), "kiekis": kiekis, "sena": None})

    def blizgesiu_zingsnis(self, dt):
        """Kartais ant sukaupto sniego (apačioje ir ant langų) ar ant krentančios snaigės sužiba kibirkštėlė:
        įsižiebia, trumpam išskleidžia spindulius ir užgęsta. Vieta renkama atsitiktinai, todėl ten, kur sniego
        daugiau, žiba dažniau, o kur jo nėra – nežiba visai."""
        gyvos = []
        for b in self.blizgesiai:
            b["t"] += dt
            f = b.get("snaige")
            persikele = False
            if f is not None:  # nusileidusi snaigė perkeliama į viršų – tada ir blizgesys baigiasi
                persikele = f[SY] < b["y"] - 20 or abs(f[SX] - b["x"]) > 60
                b["x"], b["y"] = f[SX], f[SY]
            if b["t"] >= b["trukme"] or persikele:
                if b["sena"]:
                    self.papildomos.append(b["sena"])
                continue
            gyvos.append(b)
        self.blizgesiai = gyvos
        if not self.n["sniegas_blizga"] or len(gyvos) >= BLIZG_MAKS:
            return

        def kiek(norma):  # Puasono skirstinys mažai normai: dažniausiai 0, kartais 1
            return int(norma) + (random.random() < norma % 1)

        def naujas(x, y, snaige=None):
            self.blizgesiai.append({"x": x, "y": y, "t": 0.0, "trukme": random.uniform(0.45, 0.9),
                                    "snaige": snaige, "sena": None})

        S = STULPELIS
        h, base = self.aukstis, self.pagrindas
        kel = self.__dict__.get("kelias") or ()
        egl = self.egliu_kauke()
        for _ in range(kiek(BLIZG_DAZNIS_PAVIRSIUS * self.vw / 1000 * dt)):
            c = random.randrange(len(h))
            if base[c] is None:
                continue
            # ant matomo paviršiaus: kur kelio sniegas aukštesnis – ant jo (priekyje), kitaip ant pusnies,
            # bet ne ten, kur ją dengia eglė, ir ne žemiau kelio sniego viršaus (jis priešais pusnį)
            kv = kel[c] if c < len(kel) else 0.0
            v = max(h[c], kv)
            if v < 1.5 or (h[c] >= kv and egl[c]):
                continue
            y = base[c] - v * random.uniform(0.75, 1.0)
            if h[c] > kv:
                y = min(y, base[c] - kv - 1)
            naujas(c * S + random.uniform(0, S), y)
        segs = self.langu_segmentai
        plotis = sum(x2 - x1 for _, x1, x2, _, _, _ in segs)
        for _ in range(kiek(BLIZG_DAZNIS_PAVIRSIUS * plotis / 1000 * dt)):
            ct, x1, x2, hl, cl, _ = random.choice(segs)
            x = random.uniform(x1, x2)
            c = int((x - cl) // S)
            if 0 <= c < len(hl) and hl[c] >= 1.5:
                naujas(x, ct - hl[c] * random.uniform(0.75, 1.0))
        for _ in range(kiek(BLIZG_DAZNIS_SNAIGES * len(self.snaiges) * dt)):
            f = random.choice(self.snaiges)
            if f[SGYLIS] > 0.5:  # tik artimesnės – tolimų blyksnis būtų per smulkus
                naujas(f[SX], f[SY], f)

    def piesti_blizgesius(self, i_langa, visas):
        if not self.blizgesiai:
            return
        P = max(1, int(round(self.P * 0.8)))
        serdis, spinduliai = self.g.teptukas(BLIZG_SERDIS), self.g.teptukas(BLIZG_SPINDULIAI)
        FillRect, RECT, byref, ribos = user32.FillRect, wintypes.RECT, ctypes.byref, self.ribos
        # Sniegas po seniais, bumbuliukais ir buldozeriukais jų uždengtas – ten blizgesys nepiešiamas (krentančių
        # snaigių – piešiamas: jos arti, priekyje visko).
        dengia = [o["sena"] for vardas in ("seniai", "bumbulai", "ekskavatoriai")
                  for o in getattr(self, vardas, ()) if o.get("sena")]
        for b in self.blizgesiai:
            if dengia and b.get("snaige") is None and \
                    any(l <= b["x"] < r and t <= b["y"] < bb for l, t, r, bb in dengia):
                if b["sena"] and not visas:
                    i_langa.append(b["sena"])
                b["sena"] = None
                continue
            # įsižiebia → spinduliai 1, 2 → atgal 1 → užgęsta (taškas)
            faze = b["t"] / b["trukme"]
            ilgis = (0, 1, 2, 2, 1, 0)[min(5, int(faze * 6))]
            x, y = int(b["x"] - P / 2), int(b["y"] - P / 2)
            nauja = ribos(x - ilgis * P, y - ilgis * P, x + (ilgis + 1) * P, y + (ilgis + 1) * P)
            if nauja:
                for i in range(1, ilgis + 1):
                    for dx, dy in ((i, 0), (-i, 0), (0, i), (0, -i)):
                        rr = ribos(x + dx * P, y + dy * P, x + (dx + 1) * P, y + (dy + 1) * P)
                        if rr:
                            FillRect(self.fdc, byref(RECT(*rr)), spinduliai)
                rr = ribos(x, y, x + P, y + P)
                if rr:
                    FillRect(self.fdc, byref(RECT(*rr)), serdis)
            if not visas:
                if b["sena"]:
                    i_langa.append(b["sena"])
                if nauja:
                    i_langa.append(nauja)
            b["sena"] = nauja

    def bumbulas_aria(self, b, dabar, smugis=False):
        """Riedantis bumbuliukas suspaudžia sniegą (lieka vėžė), dalį jo stumia priešais save.
        Nusileidęs po šuolio – išmuša duobutę ir pažeria sniego."""
        if not kaupia(self.n, "kaupti_apacioje"):
            return
        h, base = self.aukstis, self.pagrindas
        n, S, r = len(h), STULPELIS, b["r"]
        gylis = r * (0.35 if smugis else 0.18)
        c0, c1 = max(0, int((b["x"] - r * 0.55) // S)), min(n - 1, int((b["x"] + r * 0.55) // S))
        if smugis:  # duobutė – tik jei toje vietoje ką tik nebuvo spausta (kitaip vietoje šokinėjantis kasa šulinį)
            vid = min(n - 1, max(0, int(b["x"] // S)))
            if dabar - self.suspausta[vid] < 1.0:
                return
        stumiama = 0.0
        kel = self.__dict__.get("kelias") or ()
        for c in range(c0, c1 + 1):
            if base[c] is None or h[c] < 0.5 or (not smugis and dabar - self.suspausta[c] < 2.5):
                continue
            if c < len(kel) and self.virsus_be_kruvu(c) > h[c]:  # rieda kelio sniegu (jo neara) – pusnies neliesti
                continue
            kiek = min(h[c], gylis)
            h[c] -= kiek
            self.suspausta[c] = dabar
            stumiama += kiek * 0.25  # likusi dalis – suslėgta
        if stumiama <= 0:
            return
        self.pazymeti_zeme(c0 - 2, c1 + 3)
        if smugis:  # sniegas pažyra į šalis
            dalis = stumiama / 6
            for _ in range(6):
                self.pustomos.append({"x": b["x"] + random.uniform(-r, r), "y": b["y"] - 1,
                                      "vx": random.uniform(-70, 70) * self.k, "vy": -random.uniform(60, 130) * self.k,
                                      "gyv": 2.0, "kiekis": dalis, "sena": None})
            return
        # sniegas stumiamas už bumbuliuko pėdsako (ne po juo) ir ne aukščiau kopų ribos
        priekis = int((b["x"] + (r + 3 * S) * (1 if b["v"] >= 0 else -1)) // S)
        if 0 <= priekis < n and base[priekis] is not None:
            nusodinti(h, priekis, stumiama / SVORIU_SUMA, self.n["max_aukstis"] * self.k,
                      profilis=self.zemes_profilis, sust=self.sustumta)
            self.pazymeti_zeme(priekis - 8, priekis + 9)

    def pazymeti_zeme(self, a, b):
        """Žemės stulpeliai [a, b) pasikeitė – perpiešiami artimiausiu kaupimo kadru (tik jie, ne visa juosta)."""
        a, b = max(0, a), min(len(self.zemes_kauke), b)
        if a < b:
            self.zemes_kauke[a:b] = b"\x01" * (b - a)
            self.zemes_nesvaru = True

    def zingsnis(self, dt, t):
        n = self.n
        S = STULPELIS
        pc = time.perf_counter
        t_ = pc()
        self.vejo_zingsnis(dt)
        vejas_px = self.vejas * 12 * self.k
        gk = n["greitis"] / 100
        maks_z = n["max_aukstis"] * self.k
        maks_l = n["max_aukstis_languose"] * self.k
        kiekio_k = n["kaupimo_greitis"] / 100
        kaupti_z = kaupia(n, "kaupti_apacioje")
        dezes = self.segmentu_dezes if kaupia(n, "kaupti_languose") else None
        nd = len(dezes) if dezes else 0
        base = self.pagrindas
        h = self.aukstis
        ncol = len(h)
        kel, kel_rib = self.kelias, self.kelio_ribos()
        vw, vh = self.vw, self.vh
        sin, cos = math.sin, math.cos
        kauke = self.zemes_kauke
        nusileido_z = False
        prof = self.zemes_profilis
        # Oro sūkuriai: stiprumas – pagal „Sūkurius“ (0 – sūkurių visai nėra)
        sukurys = n["gusiai"] * 6 * self.k * n["vejas_ijungtas"]
        # gūsio banga keliauja per ekraną: vėjas vietomis stipresnis, vietomis silpnesnis
        banga_k, banga_t = 1 / (260 * self.k), t * 0.6
        svyr, plasn = n["svyravimas"] / 100, n["plasnojimas"] / 100
        # Tikroviškas oras: 6 bangos; stiprumas – pagal „Sūkurius“, pučiant stipriau – ir sūkuriai stipresni.
        # Raštą neša vėjas: fazėje – vėjo nuneštas atstumas (tolimoms dėl k/z mastelio tas pats).
        turb = sukurys > 0
        vk = 0.6
        if turb:
            if self.oro_modos is None or self.oro_modos[0] != self.k:
                self.oro_modos = (self.k, oro_modos(self.k, self.k))
            self.oro_poslinkis += vejas_px * dt
            stipr = n["gusiai"] * 4 * self.k * (1 + 0.1 * abs(self.vejas))  # ne „S“ – tai stulpelio plotis!
            off = self.oro_poslinkis
            ((k1x, k1y, a1x, a1y, p1, z1), (k2x, k2y, a2x, a2y, p2, z2), (k3x, k3y, a3x, a3y, p3, z3),
             (k4x, k4y, a4x, a4y, p4, z4), (k5x, k5y, a5x, a5y, p5, z5), (k6x, k6y, a6x, a6y, p6, z6)) = [
                (kx, ky, ux * stipr, uy * stipr, ph - kx * off - w * t, zf)
                for kx, ky, ux, uy, w, ph, zf in self.oro_modos[1]]
            vk = 1.0  # bangos jau beveik gulsčios – vertikalaus judėjimo nebemažiname

        for f in self.snaiges:
            x, y, r = f[SX], f[SY], f[SR]
            zz = f[SGYLIS]
            z = 0.4 + 0.6 * zz  # paralaksas: tolimų snaigių judėjimas ekrane mažesnis
            if turb:
                iz = 1.0 / z  # tolimų sūkuriai ekrane mažesni
                xs, ys = x * iz, y * iz
                c = cos(k1x * xs + k1y * ys + p1 + z1 * zz)
                u, v = a1x * c, a1y * c
                c = cos(k2x * xs + k2y * ys + p2 + z2 * zz)
                u += a2x * c
                v += a2y * c
                c = cos(k3x * xs + k3y * ys + p3 + z3 * zz)
                u += a3x * c
                v += a3y * c
                c = cos(k4x * xs + k4y * ys + p4 + z4 * zz)
                u += a4x * c
                v += a4y * c
                c = cos(k5x * xs + k5y * ys + p5 + z5 * zz)
                u += a5x * c
                v += a5y * c
                c = cos(k6x * xs + k6y * ys + p6 + z6 * zz)
                u = (u + a6x * c) * z
                v = (v + a6y * c) * z
            else:  # sūkurių nėra („Sūkuriai“ 0)
                u = v = 0.0
            fz = t * f[SDAZN] + f[SFAZE]
            # snaigė prie vėjo prisitaiko greitai, bet ne akimirksniu
            tikslas = vejas_px * z * (1 + 0.35 * sin(x * banga_k - banga_t)) + u
            vx = f[SVX]
            k_ = dt * f[SREAKCIJA]
            vx += (tikslas - vx) * (k_ if k_ < 1 else 1)
            f[SVX] = vx
            # Svyravimas – ne viena sinusoidė (tada snaigė juda kaip švytuoklė, „pririšta už siūlo“), o dvi
            # nekartotinio santykio bangos (2,37 karto dažnesnė, 0,45 amplitudės) ir lėtai kintantis mostų dydis
            # (0,55–1): kiekvienas mostas kitoks, judesys nesikartoja. Nauji laukai nereikalingi – antros bangos
            # fazė ir mostų kitimas išvedami iš SDAZN ir SFAZE.
            fz2 = fz * 2.37 + f[SFAZE] * 3.1
            mostas = 0.775 + 0.225 * sin(t * f[SDAZN] * 0.23 + f[SFAZE] * 1.7)
            sfz = (sin(fz) + 0.45 * sin(fz2)) * mostas * 0.69  # 0,69 ≈ 1 / 1,45 – didžiausia vertė ~1
            nx = x + (vx + sfz * f[SAMP] * svyr) * dt
            # kristalai lėtėja, kai „pasvyra“ į šoną, ir greitėja grįždami – kaip krentantis lapas; 0,358 – kad
            # vidutiniškai (per ilgą laiką) kritimo greitis nepasikeistų: vidutinis 2·sfz² ≈ 0,358
            ny = y + (f[SVY] * gk * (1 - f[SPLASNOJIMAS] * plasn * (0.358 - 2.0 * sfz * sfz)) + v * vk) * dt
            nusileido = False
            di = int(nx) >> 6
            for sy, x1, x2, hl, lx, st in (dezes[di] if 0 <= di < nd else ()):
                if x1 <= nx < x2:
                    ci = int((nx - lx) // S)
                    if 0 <= ci < len(hl):
                        pav = sy - hl[ci]
                        if y < pav <= ny:
                            pl = st["profilis"]
                            if hl[ci] < maks_l * pl[ci]:
                                nusodinti(hl, ci, (1.0 + min(r, 6) * 0.2) * kiekio_k, maks_l, krastai=True,
                                          profilis=pl)
                                if not st["nesvarus"]:
                                    st["nesvarus"] = True
                                    self.nesvarus_langai.append(st)
                            nusileido = True
                            break
            if not nusileido:
                ci = int(nx // S)
                if 0 <= ci < ncol:
                    b = base[ci]
                    if b is not None:
                        if ny >= b - h[ci]:
                            if kaupti_z and h[ci] < maks_z * prof[ci]:
                                nusodinti(h, ci, (1.0 + min(r, 6) * 0.2) * kiekio_k, maks_z, profilis=prof,
                                          sust=self.sustumta)
                                a_, b_ = (ci - 8 if ci > 8 else 0), (ci + 9 if ci + 9 < ncol else ncol)
                                kauke[a_:b_] = b"\x01" * (b_ - a_)
                                nusileido_z = True
                            if kaupti_z and kel[ci] < kel_rib[ci]:  # ir ant kelio priešais egles
                                # riba – šio stulpelio (be profilio apkarpymo: jis nukirptų buldozeriukų kruvas)
                                a_, b_ = (ci - 7 if ci > 7 else 0), (ci + 8 if ci + 8 < ncol else ncol)
                                pries = kel[a_:b_]
                                nusodinti(kel, ci, (1.0 + min(r, 6) * 0.2) * kiekio_k, kel_rib[ci])
                                for j in range(a_, b_):  # kaimynai – ne aukščiau savo ribos (duobutės prie kamienų)
                                    if kel[j] > kel_rib[j] and kel[j] > pries[j - a_]:
                                        kel[j] = max(pries[j - a_], kel_rib[j])
                                a_, b_ = (ci - 8 if ci > 8 else 0), (ci + 9 if ci + 9 < ncol else ncol)
                                kauke[a_:b_] = b"\x01" * (b_ - a_)
                                nusileido_z = True
                            nusileido = True
                    elif ny > vh:
                        nusileido = True
                elif nx < -80 or nx > vw + 80 or ny > vh:
                    nusileido = True
            if nusileido:
                self.i_virsu(f, vejas_px, gk)
            else:
                f[SX] = nx
                f[SY] = ny

        if nusileido_z:
            self.zemes_nesvaru = True

        # fizikos išskaidymas – tik lėtų kadrų žurnalui (keli laiko matavimai per kadrą – nereikšminga)
        dalys = {}
        t1_ = pc()
        dalys["snaigės"] = (t1_ - t_) * 1000
        self.sniego_vejas(dt, vejas_px)
        t_ = pc()
        dalys["kopos"] = (t_ - t1_) * 1000
        self.pustymo_zingsnis(dt, vejas_px)
        t1_ = pc()
        dalys["pustymas"] = (t1_ - t_) * 1000
        self.blizgesiu_zingsnis(dt)
        self.bumbulu_zingsnis(dt)
        t_ = pc()
        dalys["blizgesiai+bumbuliukai"] = (t_ - t1_) * 1000
        self.ekskavatoriu_zingsnis(dt)
        self.kelio_slinkimas(dt)
        self.kelias_be_kruvu(dt)
        self.seniu_zingsnis(dt)
        t1_ = pc()
        dalys["buldozeriai+seniai"] = (t1_ - t_) * 1000
        self._fizikos_dalys = dalys

        # Fejerverkai pagal laikrodį (kas N minučių nuo vidurnakčio)
        if n["fejerverkai"]:
            dabar = time.time()
            if self.kitas_fj - dabar > n["fejerverku_intervalas"] * 60 + 5:  # laikrodis atsuktas atgal
                self.kitas_fj = self.kitas_fejerverku_laikas(dabar)
            if dabar >= self.kitas_fj:
                if dabar - self.kitas_fj < 90 and not self.fj.aktyvus:  # po miego pavėluoto šou nerodome
                    self.paleisti_fejerverkus()
                self.kitas_fj = self.kitas_fejerverku_laikas(dabar)
        if self.fj.aktyvus:
            self.papildomos += self.fj.zingsnis(dt)

        # Mirksinčios lemputės: kiekviena eglė savo ritmu; perpiešiamos tik pasikeitusių eglių sritys.
        if n["egles"] and n["egliu_lemputes"] and n["egliu_mirksi"] and self.egles:
            # pasikeitus lemputėms perpiešiama visa eglė (dalinis perpiešimas Windows sistemoje „nukirpdavo“ eglių dalis)
            for e, _ in mirksejimo_zingsnis(self.egles, dt):
                self.nesvarios_sritys.append(e["ribos"])
        if getattr(self, "girliandos", None):  # girliandose perpiešiamos tik pasikeitusios lemputės
            for g, js in girliandu_zingsnis(self.girliandos, dt, n["girliandu_mirksejimas"] / 100,
                                            n["girliandu_atspindziai"]):
                for j in js:
                    self.nesvarios_sritys.append(g["vietos"][j][3])

    def piesti(self):
        sdc, fdc = self.sdc, self.fdc
        BitBlt = gdi32.BitBlt
        ribos = self.ribos
        i_langa = []

        visas = self.pilnas_perpiesimas
        if visas:
            self.pilnas_perpiesimas = False
            self.zemes_nesvaru = False
            self.zemes_kauke[:] = bytes(len(self.zemes_kauke))
            for st in self.nesvarus_langai:
                st["nesvarus"] = False
            self.nesvarus_langai = []
            self.nesvarios_sritys = []
            self.papildomos = []
            self.perpiesti_statini(None)
            a0 = time.perf_counter()
            BitBlt(fdc, 0, 0, self.vw, self.vh, sdc, 0, 0, SRCCOPY)
            self._atstatymo_ms = ms = (time.perf_counter() - a0) * 1000
            self.kaina_pilno_atst = ms if self.kaina_pilno_atst is None else self.kaina_pilno_atst * 0.7 + ms * 0.3
            self.atst_pilno_laikas = a0
        else:
            self.statinio_skaitliklis += 1
            kaupimas = self.statinio_skaitliklis >= 3
            if kaupimas:
                self.statinio_skaitliklis = 0
            # 1) atstatome kadro buferį iš statinio ten, kur buvo snaigės ar pasikeitė sniegas
            statiniai = self.surinkti_statinius(kaupimas) + self.papildomos
            self.papildomos = []
            a0 = time.perf_counter()
            atstatyti = list(statiniai)
            for f in self.snaiges:
                s = f[SSENA]
                if s:
                    atstatyti.append(s)
            for bu in itertools.chain(self.bumbulai, self.skeveldros, self.pustomos, self.ekskavatoriai,
                                      self.ekskav_daleles, self.blizgesiai, self.seniai, self.senio_daleles):
                if bu["sena"]:
                    atstatyti.append(bu["sena"])
            atstatyti += sujungti_staciakampius([g.sena for g in self.fj.grupes if g.sena])
            # Kaip ir kopijuojant į ekraną: daug mažų kopijavimų gali kainuoti daugiau nei vienas viso buferio.
            # Visas buferis atstatomas saugiai – visi judantys objektai vis tiek piešiami kiekvieną kadrą,
            # o už senų jų vietų buferis ir taip sutampa su statiniu.
            pilnas_atst = False
            if self.kaina_pilno_atst is not None:
                dalinis = len(atstatyti) * self.kaina_atstatymo
                pilnas_atst = dalinis > self.kaina_pilno_atst * 1.15
                if pilnas_atst and self.pilni_atst_is_eiles >= 60 and dalinis < self.kaina_pilno_atst * 3:
                    pilnas_atst = False
            # Viso buferio kaina kitaip matuojama tik per pilną perpiešimą (paleidus – „šaltą“, kelis kartus
            # didesnę), todėl kas 5 s visas buferis atstatomas ir taip – tai pigu ir visada teisinga.
            if not pilnas_atst and a0 - self.atst_pilno_laikas >= 5:
                pilnas_atst = True
            if pilnas_atst:
                BitBlt(fdc, 0, 0, self.vw, self.vh, sdc, 0, 0, SRCCOPY)
            else:
                for l, t, r, b in atstatyti:
                    BitBlt(fdc, l, t, r - l, b - t, sdc, l, t, SRCCOPY)
            self._atstatymo_ms = ms = (time.perf_counter() - a0) * 1000
            if pilnas_atst:
                self.kaina_pilno_atst = ms if self.kaina_pilno_atst is None else self.kaina_pilno_atst * 0.7 + ms * 0.3
                self.pilni_atst_is_eiles += 1
                self.atst_pilno_laikas = a0
            elif atstatyti:
                self.kaina_atstatymo = self.kaina_atstatymo * 0.9 + ms / len(atstatyti) * 0.1
                self.pilni_atst_is_eiles = 0
            i_langa += statiniai

        # 2) fejerverkai (toli danguje – už viso kito), tolimos snaigės (už eglučių, pusnių ir kt.), seniai ir
        #    jų sniego purslai (už eglučių: eglė uždedama iš statinio sluoksnio – todėl jie turi būti nupiešti
        #    PRIEŠ tai, kas priešais egles, kitaip eglės kopija uždengtų ir tai), tada bumbuliukai, pustomas
        #    sniegas ir buldozeriukai – arčiausiai
        self.piesti_fejerverkus(i_langa, visas)
        self.piesti_snaiges(i_langa, visas, toli=True)
        self.piesti_senius(i_langa, visas)
        self.piesti_gumulus(i_langa, visas, senio=True)
        self.piesti_bumbulus_kadre(i_langa, visas)
        self.piesti_pustomas(i_langa, visas)
        self.piesti_ekskavatorius(i_langa, visas)

        # 3) arti esančios snaigės – priekyje visko, išskyrus girliandas
        self.piesti_snaiges(i_langa, visas, toli=False)
        self.piesti_blizgesius(i_langa, visas)
        # 3a) girliandos kabo ant ekrano krašto – arčiausiai žiūrinčiojo, todėl ant viršaus visko (ir
        #     bumbuliukų, senių, buldozeriukų bei artimų snaigių)
        self.uzdengti_girliandomis(i_langa, visas)

        # 4) į ekraną – tik pasikeitę stačiakampiai, jau galutiniai, todėl niekas nemirga.
        # Visas kadras kopijuojamas, kai Windows perdangą „ištrynė“, langams nurimus ir dar kas 5 s – dėl visa ko.
        dabar = time.perf_counter()
        if self.laukia_pilno_blito and dabar - self.paskutinis_judejimas >= 0.3:
            self.laukia_pilno_blito = False
            self.pilnas_blitas = True
        if dabar - self.blito_laikas >= 5:  # atsarginis viso kadro kopijavimas – jei kas nors „nuslydo“
            self.pilnas_blitas = True
        if self.pilnas_blitas:
            self.blito_laikas = dabar
        if self.statiniu_blitas:
            self.statiniu_blitas = False
            for e in self.egles:
                s_ = ribos(*e["ribos"])
                if s_:
                    i_langa.append(s_)
            # žemės sniegas (su ant jo gulinčiais bumbuliukais) – siauros juostos, kopijuoti pigu
            S = STULPELIS
            virsus = int(self.n["max_aukstis"] * self.k * 1.05) + max((b["W"] for b in self.bumbulai), default=0) + 4
            for c1, c2, pagrindas in self.zemes_ruozai:
                s_ = ribos(c1 * S - S, pagrindas - virsus, c2 * S + S, pagrindas + 2)
                if s_:
                    i_langa.append(s_)
            for st in self.langai.values():
                s_ = ribos(*st["sritis"])
                if s_:
                    i_langa.append(s_)
        if self.pilnas_blitas:
            self.pilnas_blitas = False
            visas = True
        plotas = 0
        if not visas:
            # Smulkių stačiakampių kopijavimas pigesnis už viso ekrano (dešimtys MB per kadrą). Bet jei
            # pasikeitė daugiau nei pusė ekrano (pvz. fejerverkų finalas), vienas kopijavimas – pigiau.
            for l, t, r, b in i_langa:
                plotas += (r - l) * (b - t)
            visas = plotas > self.vw * self.vh // 2
            # Permatomame sluoksniuotame lange kopijavimas į ekraną kainuoja daugiausia už KVIETIMĄ (Windows ir DWM
            # kiekvieną stačiakampį apdoroja atskirai), ne už pikselius: 1000 snaigių – ~900 kvietimų po ~29 µs.
            # Todėl lyginamos išmatuotos kainos: n mažų kopijavimų prieš vieną viso kadro. Kas 60 viso kadro
            # kopijavimų iš eilės padaromas vienas dalinis – kad mažo kopijavimo kaina neliktų pasenusi, bet tik
            # kai kainos artimos: kitaip tas vienas kadras būtų kelis kartus lėtesnis ir sniegas trūktelėtų.
            if not visas and self.kaina_pilno is not None:
                dalinis = len(i_langa) * self.kaina_staciakampio
                visas = dalinis > self.kaina_pilno * 1.15
                if visas and self.pilni_is_eiles >= 60 and dalinis < self.kaina_pilno * 3:
                    visas = False
        if visas:
            self.d_pilni += 1
        else:
            self.d_plotas += plotas
        e0 = time.perf_counter()
        wdc = user32.GetDC(self.piesimo_hwnd)
        pavyko = True
        try:
            if visas:
                pavyko = bool(BitBlt(wdc, 0, 0, self.vw, self.vh, fdc, 0, 0, SRCCOPY))
            else:
                for l, t, r, b in i_langa:
                    pavyko &= bool(BitBlt(wdc, l, t, r - l, b - t, fdc, l, t, SRCCOPY))
        finally:
            user32.ReleaseDC(self.piesimo_hwnd, wdc)
            self._ekrano_ms = ms = (time.perf_counter() - e0) * 1000
            self._ekrano_kv = 1 if visas else len(i_langa)
        if not pavyko:  # užrakintas ekranas (Win+L), UAC: BitBlt iškart nepavyksta – kainos vidurkiai neliečiami
            return
        if visas:
            self.kaina_pilno = ms if self.kaina_pilno is None else self.kaina_pilno * 0.7 + ms * 0.3
            self.pilni_is_eiles += 1
        elif i_langa:
            self.kaina_staciakampio = self.kaina_staciakampio * 0.9 + ms / len(i_langa) * 0.1
            self.pilni_is_eiles = 0

    # ------------------------------------------------------------ langai

    def _enum_langas(self, hwnd, lp):
        try:
            if hwnd == self.perdangos_hwnd:
                return True
            if not user32.IsWindowVisible(hwnd) or user32.IsIconic(hwnd):
                return True
            if GetWindowLong(hwnd, GWL_EXSTYLE) & (WS_EX_TOOLWINDOW | WS_EX_TRANSPARENT):
                return True
            if user32.GetWindowTextLengthW(hwnd) == 0 or paslepta_dwm(hwnd):
                return True
            if lango_klase(hwnd) in ISIMTOS_KLASES:
                return True
            st = lango_staciakampis(hwnd)
            if st and st[2] > st[0] and st[3] > st[1]:
                self.langu_sarasas.append((hwnd, st, bool(user32.IsZoomed(hwnd))))
        except Exception:
            pass
        return True

    def ant_ekrano(self, x, y):
        return any(m[0] <= x < m[2] and m[1] <= y < m[3] for m, _ in (self.monitoriai or ()))

    def tikrinti_pilna_ekrana(self):
        pilnas = False
        if self.n["slepti_pilname_ekrane"]:
            fg = user32.GetForegroundWindow()
            if fg and fg != self.perdangos_hwnd and not user32.IsZoomed(fg) \
                    and lango_klase(fg) not in ISIMTOS_KLASES:
                r = wintypes.RECT()
                mi = MONITORINFO()
                mi.cbSize = ctypes.sizeof(MONITORINFO)
                if user32.GetWindowRect(fg, ctypes.byref(r)) and \
                        user32.GetMonitorInfoW(user32.MonitorFromWindow(fg, MONITOR_DEFAULTTONEAREST), ctypes.byref(mi)):
                    m = mi.rcMonitor
                    pilnas = r.left <= m.left and r.top <= m.top and r.right >= m.right and r.bottom >= m.bottom
                    if pilnas:  # tik klasė, ne pavadinimas – jame gali būti dokumentų vardai
                        self.diag_pilno_klase = lango_klase(fg)
        if pilnas != self.pilnas_ekranas:
            self.pilnas_ekranas = pilnas
            self.taikyti_matomuma()

    def kurti_langu_kabliukus(self):
        """Windows praneša, kai langas pajuda, keičia dydį, iškyla, sumažinamas ar uždaromas – tada langų
        sniegas perskaičiuojamas iškart, o ne po 0,4 s. Pranešimo funkcijoje tik pažymime – tkinter čia nekviečiame."""
        self._ivykio_cb = WINEVENTPROC(self._lango_ivykis)
        self._kabliukai = []
        for nuo, iki in ((EVENT_SYSTEM_FOREGROUND, EVENT_SYSTEM_MINIMIZEEND),
                         (EVENT_OBJECT_DESTROY, EVENT_OBJECT_LOCATIONCHANGE),
                         (EVENT_OBJECT_CLOAKED, EVENT_OBJECT_UNCLOAKED)):  # Windows 11 skydeliai iš anksto sukurti,
            # parodomi „atidengiant“ (uncloak), be EVENT_OBJECT_SHOW
            try:
                h = user32.SetWinEventHook(nuo, iki, None, self._ivykio_cb, 0, 0, WINEVENT_OUTOFCONTEXT)
                if h:
                    self._kabliukai.append(h)
            except Exception:
                pass

    def _lango_ivykis(self, kabliukas, ivykis, hwnd, objektas, vaikas, gija, laikas):
        t0 = time.perf_counter()
        # tik patys pagrindiniai langai – ne žymeklis, ne mygtukai ar vaizdo grotuvai jų viduje (jie juda nuolat)
        # sniego senių pagavimo langeliai juda kone kas kadrą – tai ne kitų langų judėjimas
        if objektas == 0 and vaikas == 0 and hwnd and not self.langai_judejo and hwnd not in self.senio_hwnd \
                and hwnd not in Patarimas.hwnds:
            try:
                if user32.GetAncestor(hwnd, GA_ROOT) == hwnd:
                    self.langai_judejo = True
            except Exception:
                pass
        if hwnd and hwnd == self.__dict__.get("nuleista_po") and ivykis in (
                EVENT_OBJECT_HIDE, EVENT_OBJECT_DESTROY, EVENT_OBJECT_CLOAKED):
            try:
                self.grazinti_virsuje()
            except Exception:
                pass
        # parodymo pranešimai ateina ir dėl žymeklio, karetės, vidinių valdiklių (objektas ≠ 0) – juos praleidžiame
        # iškart, be lango klasės ir dydžio klausimų kitam procesui
        if ivykis in (EVENT_SYSTEM_FOREGROUND, EVENT_SYSTEM_MENUPOPUPSTART, EVENT_OBJECT_SHOW,
                      EVENT_OBJECT_UNCLOAKED) and hwnd \
                and (objektas == 0 or ivykis in (EVENT_SYSTEM_MENUPOPUPSTART, EVENT_SYSTEM_FOREGROUND)) \
                and hwnd not in self.senio_hwnd and hwnd not in Patarimas.hwnds:
            try:
                self.po_iskylancio(hwnd)
            except Exception:
                pass
        self._ivykiai_n += 1
        self._ivykiai_ms += (time.perf_counter() - t0) * 1000

    def naikinti_langu_kabliukus(self):
        for h in getattr(self, "_kabliukai", ()):
            user32.UnhookWinEvent(h)
        self._kabliukai = []

    def atnaujinti_langus(self):
        """Kas 0,4 s: langų sąrašas (atsarginis, jei pranešimas pražuvo), ekranai, dėklas, „visada viršuje“."""
        self.perskaityti_langus()
        try:
            # Kiti „visada viršuje“ langai gali užlįsti ant viršaus – kartkartėmis grįžtame.
            self.ekranu_tikrinimas += 1
            if self.ekranu_tikrinimas >= 5:
                self.ekranu_tikrinimas = 0
                self.tikrinti_ekranus()
                self.deklo_tikrinimas = getattr(self, "deklo_tikrinimas", 0) + 1
                # Dėklas: persikrovus explorer.exe – iškart (WM_TASKBARCREATED); atsarginis tikrinimas – kas 5 min
                # (buvo kas 30 s; NIM_MODIFY kaskart perpiešia užduočių juostą). Kol piktogramos nėra – kas 2 s.
                if self.deklo_tikrinimas >= 150 or not self.deklas:
                    self.deklo_tikrinimas = 0
                    self.tikrinti_dekla()
            if self.__dict__.get("deklas_atkurti"):
                self.deklas_atkurti = False
                ZURNALAS.rasyti("ĮVYKIS: užduočių juosta persikrovė (TaskbarCreated) – piktograma kuriama iš naujo")
                self.deklas = None
                self.kurti_dekla()
            self.topmost_skaitliklis += 1
            if self.rodoma and self.topmost_skaitliklis >= 5:
                self.topmost_skaitliklis = 0
                self.kelti_perdanga()
        except Exception as e:
            self.klaida(e)
        self.root.after(400, self.atnaujinti_langus)

    def kas_nors_virs_perdangos(self):
        """Kuris tikrai matomas kitos programos langas yra virš perdangos (HWND arba None)? Tik tada ją
        keliame – kiekvienas iškėlimas verčia Windows perpiešti visą perdangą (matosi kaip mirgėjimas).
        Neskaičiuojami: savi langai, „cloaked“ (nematomi), kiaurai spaudžiami (kitų programų perdangos),
        tušti ir už ekrano esantys, ir tie, kurių iškėlimas nieko nepakeitė (sistemos langai, esantys
        aukščiau už bet kurį „visada viršuje“ – pvz., „Start“ meniu, pranešimai)."""
        iskyl = self.__dict__.get("iskylantys_nuo")
        if iskyl:  # uždaryti (paslėpti) iškylantys langai pamirštami – atidarius vėl, minutė skaičiuojama iš naujo
            for hw in [hw for hw in iskyl if not user32.IsWindowVisible(hw) or paslepta_dwm(hw)]:
                del iskyl[hw]
        h = user32.GetWindow(self.perdangos_hwnd, GW_HWNDPREV)
        pid = wintypes.DWORD()
        nekelti = self.__dict__.setdefault("nekelti_del", {})
        while h:
            if user32.IsWindowVisible(h) and h not in self.senio_hwnd and nekelti.get(h, 0) < 3 \
                    and not GetWindowLong(h, GWL_EXSTYLE) & WS_EX_TRANSPARENT and not paslepta_dwm(h):
                user32.GetWindowThreadProcessId(h, ctypes.byref(pid))
                st = lango_staciakampis(h) if pid.value != os.getpid() else None
                if st and st[2] - st[0] > 2 and st[3] - st[1] > 2 and st[0] < self.vx + self.vw and \
                        st[2] > self.vx and st[1] < self.vy + self.vh and st[3] > self.vy:
                    if not self.sistemos_iskylantis(h):
                        return h
                    klase = lango_klase(h)
                    # atidarytas sistemos iškylantis langas – kol jis atidarytas (bet ne ilgiau nei minutę: jei
                    # koks nors toks langas lieka matomas visada, perdanga vis tiek keliama), jo neuždengiame
                    iskyl = self.__dict__.setdefault("iskylantys_nuo", {})
                    if h not in iskyl:
                        try:
                            ZURNALAS.rasyti(f"iškylantis sistemos langas „{klase}“ – perdanga jo neuždengia")
                        except Exception:
                            pass
                    pirma = iskyl.setdefault(h, time.monotonic())
                    if len(iskyl) > 100:
                        iskyl.clear()
                    if time.monotonic() - pirma < 60:
                        return None
                    return h
            h = user32.GetWindow(h, GW_HWNDPREV)
        return None

    def sistemos_iskylantis(self, h):
        """Ar langas – sistemos iškylantis (meniu, paslėptų piktogramų sąrašas, „Start“…): pagal klasę, arba
        sistemos apvalkalo procesų (SISTEMOS_PROCESAI) mažas iškylantis langas be antraštės."""
        klase = lango_klase(h)
        if klase in ISKYLANTYS_LANGAI:
            return True
        if klase in NE_ISKYLANTYS:
            return False
        stilius = GetWindowLong(h, GWL_STYLE) & 0xFFFFFFFF
        if stilius & WS_CAPTION == WS_CAPTION:
            return False
        st = lango_staciakampis(h)
        if not st or (st[2] - st[0]) * (st[3] - st[1]) > self.vw * self.vh / 4:
            return False
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(h, ctypes.byref(pid))
        if proceso_vardas(pid.value) in SISTEMOS_PROCESAI:
            return bool(stilius & WS_POPUP)
        # Kitų programų iškylantys skydeliai prie užduočių juostos (pvz., EarTrumpet garsumo skydelis): be
        # antraštės (WS_POPUP nebūtinas – WPF langai be rėmelio jo neturi) ir „visada viršuje“ (aktyvumas
        # nesvarbus), arba aktyvus įrankio langas. Visada matomi tokie valdikliai uždengiami po minutės.
        if pid.value == os.getpid():
            return False
        ex = GetWindowLong(h, GWL_EXSTYLE)
        return bool(ex & WS_EX_TOPMOST) or (user32.GetForegroundWindow() == h and bool(ex & WS_EX_TOOLWINDOW))

    def po_iskylancio(self, h):
        """Atsirado sistemos iškylantis langas (meniu ir pan.), bet jis ŽEMIAU perdangos (pvz., Windows 11
        užduočių juostos dešiniojo klavišo meniu – ne „visada viršuje“): perdanga perkeliama tiesiai po juo.
        Jam užsidarius perdanga vėl iškeliama (kelti_perdanga, ≤2 s)."""
        ph = self.__dict__.get("perdangos_hwnd")
        if not ph or not self.rodoma or h == ph or user32.GetAncestor(h, GA_ROOT) != h \
                or not user32.IsWindowVisible(h) or not self.sistemos_iskylantis(h):
            return
        sh = lango_staciakampis(h)
        if not sh:
            return
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(h, ctypes.byref(pid))
        jo_pid = pid.value
        w, n = user32.GetWindow(h, GW_HWNDPREV), 0
        while w and n < 3000:  # ar perdanga – aukščiau jo?
            if w == ph:
                # Nebūtinai „visada viršuje“ langas – tada ir perdanga juo nebebus (ji lieka virš visų įprastų
                # langų, nes šis meniu – aukščiausias iš jų); ją vėl iškels kelti_perdanga, meniu užsidarius.
                # Sniego senių pagavimo langeliai – irgi po meniu, kitaip paspaudimą meniu punkte „suvalgytų“.
                for hw in [ph] + [x for s_ in self.seniai for x in (s_.get("hwnds") or ())[:1]]:
                    user32.SetWindowPos(hw, h, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
                self.seniai_nuleisti = True
                self.nuleista_po = h  # kai jis užsidarys – perdanga iškart grąžinama „visada viršuje“
                try:
                    ZURNALAS.rasyti(f"iškylantis sistemos langas „{lango_klase(h)}“ po perdanga – perdanga "
                                    f"perkelta po juo")
                except Exception:
                    pass
                return
            # Jei virš jo yra įprastas (ne „visada viršuje“) KITOS programos langas, kuris jį dengia, – tai ne
            # atidarytas meniu, o koks nors pagalbinis apvalkalo langas apačioje: perdangos nekišame po juo, kitaip
            # sniegas iki 2 s pradingtų už programų langų. To paties proceso langai (Windows 11 meniu sudarytas iš
            # kelių langų) ir kiti iškylantys langai – neskaičiuojami.
            if user32.IsWindowVisible(w) and w not in self.senio_hwnd and not paslepta_dwm(w) \
                    and not GetWindowLong(w, GWL_EXSTYLE) & WS_EX_TOPMOST:
                user32.GetWindowThreadProcessId(w, ctypes.byref(pid))
                sw = lango_staciakampis(w) if pid.value not in (os.getpid(), jo_pid) else None
                if sw and sw[0] < sh[2] and sw[2] > sh[0] and sw[1] < sh[3] and sw[3] > sh[1] \
                        and not self.sistemos_iskylantis(w):
                    try:
                        ZURNALAS.rasyti(f"iškylantis langas „{lango_klase(h)}“ po perdanga, bet jį dengia "
                                        f"„{lango_klase(w)}“ ({proceso_vardas(pid.value) or '?'}) – perdanga nekeliama")
                    except Exception:
                        pass
                    return
            w, n = user32.GetWindow(w, GW_HWNDPREV), n + 1

    def grazinti_virsuje(self):
        """Perdanga buvo pakišta po ne „visada viršuje“ meniu (po_iskylancio) ir taip neteko „visada viršuje“
        būsenos – meniu užsidarius ji iškart grąžinama. Kitaip išdidintas ar aktyvuotas langas atsidurdavo virš
        jos ir sniegas pradingdavo (iki minutės, kol virš jos buvo matomas koks nors iškylantis langas)."""
        self.nuleista_po = None
        ph = self.__dict__.get("perdangos_hwnd")
        if not ph or not self.rodoma:
            return
        user32.SetWindowPos(ph, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
        if self.__dict__.get("seniai_nuleisti"):
            self.seniai_nuleisti = False
            for s_ in self.seniai:
                for hw in (s_.get("hwnds") or ())[:1]:
                    user32.SetWindowPos(hw, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
        try:
            ZURNALAS.rasyti("iškylantis langas užsidarė – perdanga vėl „visada viršuje“")
        except Exception:
            pass

    def kelti_perdanga(self):
        """Kas 2 s: jei virš perdangos atsirado kitas langas – iškeliame. Jei tas pats langas lieka viršuje ir
        po trijų iškėlimų iš eilės (jo aukščiau neperšoksi arba jis pats nuolat keliasi) – jo nebepaisome:
        kitaip perdanga būtų keliama kas 2 s ir visa mirgėtų."""
        # Atsarginis: meniu, po kuriuo perdanga pakišta, jau nebematomas (pranešimas galėjo pražūti), arba perdanga
        # kitaip neteko „visada viršuje“ – grąžinama iškart, nelaukiant, kol virš jos kas nors atsiras.
        np_ = self.__dict__.get("nuleista_po")
        ph = self.__dict__.get("perdangos_hwnd")
        if np_ and (not user32.IsWindowVisible(np_) or paslepta_dwm(np_)):
            self.grazinti_virsuje()
        elif not np_ and ph and self.rodoma and not GetWindowLong(ph, GWL_EXSTYLE) & WS_EX_TOPMOST:
            self.grazinti_virsuje()
        h = self.kas_nors_virs_perdangos()
        nekelti = self.__dict__.setdefault("nekelti_del", {})
        if h is None:
            self.paskutinis_virsuje = None
            return
        if h == getattr(self, "paskutinis_virsuje", None):
            nekelti[h] = nekelti.get(h, 0) + 1
            if nekelti[h] >= 3:
                try:
                    ZURNALAS.rasyti(f"virš perdangos nuolat lieka langas „{lango_klase(h)}“ – nebekeliama dėl jo")
                except Exception:
                    pass
                return
        else:
            nekelti[h] = 1
        if len(nekelti) > 200:  # seni (uždaryti) langai
            nekelti.clear()
        self.paskutinis_virsuje = h
        self.d_topmost += 1
        if ZURNALAS.ijungtas:  # kas atsidūrė virš perdangos – kad būtų aišku, kodėl ji keliama
            try:
                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(h, ctypes.byref(pid))
                st = lango_staciakampis(h) or (0, 0, 0, 0)
                ZURNALAS.rasyti(
                    f"perdanga keliama virš „{lango_klase(h)}“ ({proceso_vardas(pid.value) or '?'}, "
                    f"stilius 0x{GetWindowLong(h, GWL_STYLE) & 0xFFFFFFFF:08x}, "
                    f"ex 0x{GetWindowLong(h, GWL_EXSTYLE) & 0xFFFFFFFF:08x}, {st[2] - st[0]}×{st[3] - st[1]}, "
                    f"aktyvus: {'taip' if user32.GetForegroundWindow() == h else 'ne'})")
            except Exception:
                pass
        user32.SetWindowPos(self.perdangos_hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
        if self.__dict__.get("seniai_nuleisti"):  # po sistemos meniu nuleisti senių langeliai – vėl į viršų
            self.seniai_nuleisti = False
            for s_ in self.seniai:
                for hw in (s_.get("hwnds") or ())[:1]:
                    user32.SetWindowPos(hw, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
        Patarimas.perdanga_iskelta = True

    def perskaityti_langus(self):
        self.langai_judejo = False
        self.paskutinis_langu_skaitymas = time.perf_counter()
        try:
            self.langu_sarasas = []
            user32.EnumWindows(self._enum_cb, 0)
            self.tikrinti_pilna_ekrana()

            S = STULPELIS
            maks_l = self.n["max_aukstis_languose"] * self.k
            kaupti = kaupia(self.n, "kaupti_languose")
            uzdengia = []
            nauji = {}
            segs = []
            # EnumWindows grąžina langus nuo viršutinio – todėl žinome, kas ką dengia.
            for hwnd, (l, t, r, b), padidintas in self.langu_sarasas:
                cl, ct, cr, cb = l - self.vx, t - self.vy, r - self.vx, b - self.vy
                if kaupti and not padidintas and cr - cl >= 80 and ct > 10 and self.ant_ekrano((l + r) // 2, t):
                    intervalai = [(max(cl, 0), min(cr, self.vw))]
                    for ol, ot, orr, ob in uzdengia:
                        if ot <= ct + 1 and ob > ct - maks_l - 2:
                            intervalai = atimti(intervalai, ol, orr)
                            if not intervalai:
                                break
                    if intervalai:
                        st = self.langai.get(hwnd)
                        if st is not None and (st["l"], st["t"], st["r"]) != (cl, ct, cr):
                            self.nubyrinti(st)
                            self.langai.pop(hwnd, None)  # kad žemiau nebūtų nubyrintas antrą kartą
                            st = None
                        naujas = st is None
                        if naujas:
                            nst_ = max(1, (cr - cl) // S)
                            st = {"l": cl, "t": ct, "r": cr, "h": [0.0] * nst_, "matomi": [], "nesvarus": False,
                                  "profilis": kopu_profilis(nst_, kopu_bangos(random, ((90 * self.k, 0.22),
                                                                                       (35 * self.k, 0.12))))}
                        st["sritis"] = (cl - 2, ct - int(maks_l) - 4, cr + 2, ct + 1)
                        h = st["h"]
                        nst = len(h)
                        matomi = []
                        kauke = bytearray(nst)
                        for a, bb in intervalai:
                            c1 = max(0, math.ceil((a - cl) / S))
                            c2 = min(nst, int((bb - cl) // S))
                            if c2 - c1 >= 4:
                                matomi.append((c1, c2))
                                kauke[c1:c2] = b"\x01" * (c2 - c1)
                                segs.append((ct, cl + c1 * S, cl + c2 * S, h, cl, st))
                        if matomi:
                            if naujas or matomi != st["matomi"]:
                                for j in range(nst):
                                    if not kauke[j]:
                                        h[j] = 0.0
                                st["matomi"] = matomi
                                self.nesvarios_sritys.append(st["sritis"])
                            nauji[hwnd] = st
                uzdengia.append((cl, ct, cr, cb))
            for hwnd, st in self.langai.items():
                if hwnd not in nauji:  # uždarytas, sumažintas ar visiškai uždengtas
                    self.nubyrinti(st)
            self.langai = nauji
            # snaigei tikrinami tik tie langų kraštai, kurie yra jos 64 px juostoje
            dezes = [[] for _ in range((self.vw >> 6) + 1)]
            for seg in segs:
                for i in range(max(0, seg[1] >> 6), min(len(dezes) - 1, (seg[2] - 1) >> 6) + 1):
                    dezes[i].append(seg)
            self.segmentu_dezes = dezes
            self.langu_segmentai = segs
        except Exception as e:
            self.klaida(e)

    # ------------------------------------------------------------ klaidos ir būsena

    def diag_nulis(self):
        self.d_kadrai = 0
        self.d_darbas = 0.0
        self.d_darbas_max = 0.0
        self.d_fizika = self.d_buferis = self.d_ekranas = 0.0
        self.d_atstatymas = 0.0
        self.d_kopijos = 0
        self.d_velavimas = 0.0
        self.d_stabtelejimai = self.d_stabt_irasyta = 0
        self.d_leti_kadrai = self.d_leti_irasyta = 0
        self.d_nuokr_kv, self.d_nuokr_n, self.d_velu_kadrai = 0.0, 0, 0
        self.d_pilni = 0
        self.d_plotas = 0
        self.d_topmost = 0
        self.d_trynimai0 = getattr(self, "windows_trynimai", 0)
        self.d_klaidos = getattr(self, "d_klaidos", 0)

    def diag_po_paleidimo(self):
        self.diag_nulis()
        self.diag_proc, self.diag_laikas = proceso_busena(), time.perf_counter()

    def diag_ekranai(self, monitoriai=None):
        return " + ".join(f"{r - l}x{b - t}@{l},{t}" for (l, t, r, b), _ in (monitoriai or self.monitoriai or []))

    def diag_antraste(self):
        ZURNALAS.rasyti(f"ekranai: {self.diag_ekranai()} @ {ekrano_daznis()} Hz | mastelis k={self.k:.2f} | "
                        f"procesorius: {platform.processor() or '?'}, {os.cpu_count()} gijos | maitinimas "
                        f"{maitinimo_busena()} | energijos ribojimas išjungtas: "
                        f"{getattr(self, 'energijos_ribojimas_isjungtas', '?')} | MMCSS: "
                        f"{'Games' if getattr(self, 'mmcss', None) else 'ne'} | ekrano ritmas (DWM): "
                        f"{getattr(getattr(self, 'ekrano_ritmas', None), 'veikia', '?')} | perdanga {self.perdangos_hwnd:#x}/"
                        f"{self.piesimo_hwnd:#x} | langų pranešimai: {len(getattr(self, '_kabliukai', []))}/2 | "
                        f"nustatymai: {json.dumps(self.n, ensure_ascii=False)}")

    def ijungta_diagnostika(self):
        """Įjungus veikiant – iškart antraštė (versija, ekranai, nustatymai), skaitikliai nuo nulio, o pirmoji
        suvestinė – po 15 s (ne po iki minutės, kaip anksčiau: atrodė, kad žurnalas nesirašo)."""
        ZURNALAS.rasyti(f"===== DIAGNOSTIKA ĮJUNGTA {PAVADINIMAS} | Python {platform.python_version()} | "
                        f"{platform.platform()} | {'exe' if SUKOMPILIUOTA else 'pyw'}")
        self.diag_antraste()
        self.diag_nulis()
        self._kadro_pabaiga, self._gijos_cpu_pab = time.perf_counter(), gijos_cpu_ms()  # kitaip – nuo paleidimo
        self.diag_nustatymai = dict(self.n)
        self.diag_proc, self.diag_laikas = proceso_busena(), time.perf_counter()
        self.diag_karta = getattr(self, "diag_karta", 0) + 1  # senas minutės ciklas baigiasi
        k = self.diag_karta
        self.root.after(15000, lambda: self.diagnostikos_suvestine(k))

    def diagnostikos_suvestine(self, karta=0, paskutine=False):
        """Kas minutę viena eilutė: iš jų matyti, kada ir kas pradėjo strigti, augti ar perpiešinėti.
        paskutine – baigiant programą (kitaip trumpiau nei minutę veikusi programa nepaliktų nė vienos)."""
        if not paskutine and karta != getattr(self, "diag_karta", 0):
            return
        try:
            dabar = time.perf_counter()
            trukme = max(1e-6, dabar - self.diag_laikas)
            proc = proceso_busena()
            if self.rodoma:
                bukle = "rodoma"
            elif self.vartotojas_paslepe:
                bukle = "PASLĖPTA naudotojo"
            else:
                bukle = "PRISTABDYTA (per visą ekraną)"
            eil = [bukle,
                   f"kadrai {self.d_kadrai / trukme:.1f}/s (tikslas {self.n['fps']})",
                   f"darbas vid {self.d_darbas / max(1, self.d_kadrai):.1f} ms, max {self.d_darbas_max:.0f} ms",
                   f"iš jo fizika {self.d_fizika / max(1, self.d_kadrai):.1f} / atstatymas "
                   f"{self.d_atstatymas / max(1, self.d_kadrai):.1f} / piešimas {self.d_buferis / max(1, self.d_kadrai):.1f}"
                   f" / ekranas {self.d_ekranas / max(1, self.d_kadrai):.1f} ms",
                   f"kopijavimų į ekraną {self.d_kopijos / max(1, self.d_kadrai):.0f}/kadrą",
                   f"kaina į ekraną: viso kadro ≈ {self.kaina_pilno or 0:.1f} ms, stačiakampio ≈ "
                   f"{self.kaina_staciakampio * 1000:.0f} µs",
                   f"atstatymo: viso buferio ≈ {self.kaina_pilno_atst or 0:.1f} ms, stačiakampio ≈ "
                   f"{self.kaina_atstatymo * 1000:.0f} µs",
                   f"didžiausias vėlavimas {self.d_velavimas * 1000:.0f} ms, stabtelėjimų > 40 ms "
                   f"{getattr(self, 'd_stabtelejimai', 0)}, lėtų kadrų > 33 ms {getattr(self, 'd_leti_kadrai', 0)}",
                   f"tolygumas ±{math.sqrt(self.d_nuokr_kv / max(1, self.d_nuokr_n)):.1f} ms, vėluojančių kadrų "
                   f"{self.d_velu_kadrai} ({100 * self.d_velu_kadrai / max(1, self.d_nuokr_n):.1f} %)",
                   f"maitinimas {maitinimo_busena()}",
                   (f"sinchronizuota su ekranu: {1 / self.vsync_periodas:.2f} Hz, kadras kas {self.vsync_kas}"
                    if getattr(self, "vsync_periodas", 0) else "sinchronizuota su ekranu: ne"),
                   f"snaigės {len(self.snaiges)}",
                   f"langai su sniegu {sum(1 for st in self.langai.values() if max(st['h']) > 0.5)}/{len(self.langai)}",
                   f"pilni kopijavimai {self.d_pilni}",
                   f"daliniai {self.d_plotas / trukme / 1e6:.2f} Mpx/s",
                   f"Windows trynė {self.windows_trynimai - self.d_trynimai0}",
                   f"iškelta į viršų {self.d_topmost}"]
            if proc and self.diag_proc:
                eil.append(f"CPU {(proc[3] - self.diag_proc[3]) / trukme * 100:.1f} %")
            if proc:
                eil.append(f"RAM {proc[0]:.0f} MB, GDI {proc[1]}, USER {proc[2]}")
            if self.fj.aktyvus:
                eil.append("vyksta fejerverkai")
            if self.d_klaidos:
                eil.append(f"klaidų iš viso {self.d_klaidos}")
            ZURNALAS.rasyti(" | ".join(eil))
            pakeisti = [f"{k} {self.diag_nustatymai.get(k)}→{v}" for k, v in self.n.items()
                        if self.diag_nustatymai.get(k) != v]
            if pakeisti:
                ZURNALAS.rasyti("NUSTATYMAI pakeisti: " + ", ".join(pakeisti))
                self.diag_nustatymai = dict(self.n)
            self.diag_proc, self.diag_laikas = proc, dabar
            self.diag_nulis()
        except Exception as e:
            ZURNALAS.rasyti(f"KLAIDA diagnostikoje: {e!r}")
        if not paskutine:
            self.root.after(60000, lambda: self.diagnostikos_suvestine(karta))

    def tk_klaida(self, tipas, reiksme, eiga):
        """Klaidos tkinter atgaliniuose kvietimuose (mygtukai, laikmačiai) – kitaip jos dingsta be pėdsakų."""
        self.paskutine_klaida = repr(reiksme)
        ZURNALAS.rasyti("KLAIDA (tkinter): " + "".join(traceback.format_exception(tipas, reiksme, eiga)))

    def atverti_zurnala(self):
        if not DIAGNOSTIKOS_BYLA.exists():
            messagebox.showinfo(PAVADINIMAS, T("Žurnalo dar nėra.") + f"\n\n{DIAGNOSTIKOS_BYLA}")
            return
        try:
            os.startfile(DIAGNOSTIKOS_BYLA)
        except Exception as e:
            messagebox.showerror(PAVADINIMAS, T("Nepavyko atverti žurnalo.") + f"\n\n{DIAGNOSTIKOS_BYLA}\n\n{e!r}")

    def klaida(self, e):
        self.paskutine_klaida = repr(e)
        self.d_klaidos += 1
        if self.d_klaidos <= 20 or self.d_klaidos % 100 == 0:  # pasikartojanti klaida neužpildo žurnalo
            ZURNALAS.rasyti(f"KLAIDA #{self.d_klaidos}: {repr(e)}\n{traceback.format_exc()}")
        if not self.klaida_parodyta:
            self.klaida_parodyta = True
            messagebox.showerror(PAVADINIMAS,
                                 T("Įvyko klaida, bet programa bando dirbti toliau. "
                                   "Jei sniegas elgiasi keistai – paleiskite programą iš naujo.") + f"\n\n{e!r}")

    def isvalyti_busena(self):
        """Dukart spustelėjus būsenos juostą: klaida ir skaitikliai joje – nuo nulio (žurnalo skaitikliai lieka)."""
        self.paskutine_klaida = ""
        self.busenos_trynimai0 = self.windows_trynimai
        self.busenos_perkurimai0 = getattr(self, "ekranu_perkurimai", 0)
        try:  # tekstas atsinaujina per ≤ 1 s (atnaujinti_busena neiškviečiama – ji nunulintų kadrų skaitiklius)
            self.busena.configure(text=self.busena.cget("text").split(T("   Windows trynė vaizdą: {n} k.").split("{")[0])[0]
                                  .split(T("   Ekranai keitėsi: {n} k.").split("{")[0])[0]
                                  .split(T("   Klaida: {e}").split("{")[0])[0])
        except tk.TclError:
            pass

    def atnaujinti_busena(self):
        try:
            if self.vartotojas_paslepe:
                tekstas = T("Viskas paslėpta.")
            elif self.pilnas_ekranas:
                tekstas = T("Pristabdyta – programa per visą ekraną.")
            else:
                su_sniegu = sum(1 for st in self.langai.values() if max(st["h"]) > 0.5)
                vid = self.darbo_ms / self.kadru_skaitliklis if self.kadru_skaitliklis else 0
                tekstas = T("Snaigių: {a}   Kadrų per sek.: {b}   Kadrui: {c} ms   Langų su sniegu: {d}").format(
                    a=len(self.snaiges), b=self.kadru_skaitliklis, c=f"{vid:.1f}", d=su_sniegu)
                if self.kadru_skaitliklis:
                    k_ = self.kadru_skaitliklis
                    tekstas += T("   Fizika / atstatymas / piešimas / ekranas: {a} / {r} / {b} / {c} ms ({n} kop.)").format(
                        a=f"{self.b_fizika / k_:.1f}", r=f"{self.b_atstatymas / k_:.1f}",
                        b=f"{self.b_buferis / k_:.1f}", c=f"{self.b_ekranas / k_:.1f}", n=round(self.b_kopijos / k_))
            trynimai = self.windows_trynimai - self.__dict__.get("busenos_trynimai0", 0)
            perkurimai = getattr(self, "ekranu_perkurimai", 0) - self.__dict__.get("busenos_perkurimai0", 0)
            if trynimai:
                tekstas += T("   Windows trynė vaizdą: {n} k.").format(n=trynimai)
            if perkurimai:  # padeda suprasti, jei vaizdas „be priežasties“ perpiešiamas
                tekstas += T("   Ekranai keitėsi: {n} k.").format(n=perkurimai)
            if self.paskutine_klaida:
                tekstas += T("   Klaida: {e}").format(e=self.paskutine_klaida[:60])
            self.busena.configure(text=tekstas)
        except Exception:
            pass
        try:
            self.atnaujinti_fejerverku_valdiklius()
        except Exception:
            pass
        self.kadru_skaitliklis = 0
        self.darbo_ms = 0.0
        self.b_fizika = self.b_buferis = self.b_ekranas = 0.0
        self.b_atstatymas = 0.0
        self.b_kopijos = 0
        self.root.after(1000, self.atnaujinti_busena)

    # ------------------------------------------------------------ nustatymų langas

    def kurti_logo(self):
        self.logo = {}
        for s in (64, 48, 32, 16):
            try:
                self.logo[s] = tk.PhotoImage(data=base64.b64encode(logo_png(s)).decode("ascii"))
            except tk.TclError:
                pass
        self.nustatyti_lango_ikona()

    def nustatyti_lango_ikona(self):
        """Lango ir užduočių juostos piktograma – sniego senis. Vien iconphoto Windows sistemoje nepakako: užduočių
        juostoje likdavo tkinter plunksna (ji – Tk lango klasės piktograma). Todėl .ico įkeliamas per Windows ir
        nustatomas ir langui (WM_SETICON: didelė ir maža), ir visai Tk langų klasei, ir kaip tkinter numatytoji."""
        kelias = Path(tempfile.gettempdir()) / f"sniegas_langas_{os.getpid()}.ico"
        try:
            kelias.write_bytes(logo_ico((16, 20, 24, 32, 40, 48, 64, 128, 256)))
            try:
                self.root.iconbitmap(default=str(kelias))
            except tk.TclError:
                if self.logo:
                    self.root.iconphoto(True, *self.logo.values())
            self.root.update_idletasks()
            h = user32.GetAncestor(self.root.winfo_id(), GA_ROOT) or self.root.winfo_id()
            ikonos = []
            for dydis, kuri, klases in ((SM_CXICON, ICON_BIG, GCLP_HICON), (SM_CXSMICON, ICON_SMALL, GCLP_HICONSM)):
                d = user32.GetSystemMetrics(dydis)
                ik = user32.LoadImageW(None, str(kelias), IMAGE_ICON, d, d, LR_LOADFROMFILE)
                if ik:
                    user32.SendMessageW(h, WM_SETICON, kuri, ik)
                    SetClassLong(h, klases, ik)
                    ikonos.append(ik)
            self._lango_ikonos = ikonos  # laikomos iki programos pabaigos
        except Exception as e:
            ZURNALAS.rasyti(f"KLAIDA: lango piktograma nenustatyta: {e!r}")
        finally:
            try:
                kelias.unlink(missing_ok=True)  # piktogramos jau atmintyje
            except OSError:
                pass

    def kurti_nustatymu_langa(self):
        r = self.root
        r.title(PAVADINIMAS)
        r.resizable(False, False)
        r.protocol("WM_DELETE_WINDOW", self.uzdaryti_langa)
        r.bind("<Map>", lambda e: self.perimti_sumazinima() if e.widget is r else None, add="+")
        r.bind("<Unmap>", lambda e: self.sumazintas_langas() if e.widget is r else None, add="+")
        self.kurti_logo()
        self.sasaja = None
        self.sasajos_karta = 0  # perjungus kalbą sąsaja sukuriama iš naujo; seni animacijų ciklai pagal tai baigiasi
        self.kurti_sasaja()
        r.update_idletasks()
        w, h = r.winfo_reqwidth(), r.winfo_reqheight()
        r.geometry(f"+{max(0, (r.winfo_screenwidth() - w) // 2)}+{max(0, (r.winfo_screenheight() - h) // 2)}")

    def perimti_sumazinima(self):
        """Mygtukas „Sumažinti“ nustatymų langą slepia į dėklą (kaip X), o ne į užduočių juostą: atkuriant
        sumažintą langą Windows rodo seną paveiksliuką ir juodą, dar nenupieštą langą (mirga), o iš dėklo
        parodytas – švarus. Perimama WM_SYSCOMMAND/SC_MINIMIZE išoriniame lange."""
        try:
            h = user32.GetAncestor(self.root.winfo_id(), GA_ROOT) or self.root.winfo_id()
            if not h or h == getattr(self, "_nust_hwnd", None):
                return
            proc = WNDPROC(self._nustatymu_procedura)
            self._nust_procs = getattr(self, "_nust_procs", []) + [proc]  # atgaliniai kvietimai neturi išnykti
            senoji = SetWindowLong(h, GWLP_WNDPROC, ctypes.cast(proc, ctypes.c_void_p).value)
            if senoji:
                self._nust_hwnd, self._senoji_nust_proc = h, senoji
        except Exception as e:
            ZURNALAS.rasyti(f"sumažinimo į dėklą perimti nepavyko: {e!r}")

    def _nustatymu_procedura(self, hwnd, zinute, wparam, lparam):
        try:
            if zinute == WM_SYSCOMMAND and (wparam & 0xFFF0) == SC_MINIMIZE and self.deklas:
                # Čia tkinter kviesti negalima (žr. _perdangos_procedura_): langas paslepiamas iš karto per
                # Windows, o tkinter būsena (withdraw) sutvarkoma tikrinti_deklo_ivykius().
                user32.ShowWindow(hwnd, SW_HIDE)
                self.deklo_ivykiai.append("i_dekla")
                return 0
        except Exception:
            pass
        return user32.CallWindowProcW(self._senoji_nust_proc, hwnd, zinute, wparam, lparam)

    def sumazintas_langas(self):
        """Atsarginis kelias: jei langas vis tiek sumažintas ne per mygtuką (pvz., Win+M) – irgi į dėklą."""
        try:
            if self.deklas and self.root.state() == "iconic":
                self.root.after_idle(self.i_dekla)
        except tk.TclError:
            pass

    def atstatyti_nustatymu_procedura(self):
        if getattr(self, "_senoji_nust_proc", None) and user32.IsWindow(self._nust_hwnd):
            SetWindowLong(self._nust_hwnd, GWLP_WNDPROC, self._senoji_nust_proc)
        self._senoji_nust_proc = None

    def kurti_sasaja(self):
        """Visi nustatymų lango valdikliai – viename rėmelyje, kad pakeitus kalbą juos būtų galima perkurti."""
        if self.sasaja is not None:
            self.sasaja.destroy()
        if not self.plociu_praejimas:
            # pirmas praėjimas – mažiausi pločiai, paskui (pritaikyti_perziuru_plocius) – pagal skilčių plotį, ir
            # sąsaja statoma antrą kartą. Išmatuoti pločiai įsimenami: kitą kartą (ta pati kalba ir ribų režimas)
            # iškart teisingi – sąsaja statoma vieną kartą (~2 kartus greičiau atsiveria)
            PERZ_PLOCIAI.clear()
            nustatyti_perziuru_plocius(self.perziuru_plociai.get(self.perziuru_raktas(), {}))
        self.sasajos_karta += 1
        self.kint = {}
        self.uzvesta = set()  # peržiūros, virš kurių dabar pelė – tik jos animuojamos
        self.valdikliai = {}
        self.etiketes = {}  # slankiklių pavadinimai (įspėjimo spalvai)
        self.papildomi_aprasai = {}  # raktas → funkcija: kintanti patarimo dalis (pvz. „šiame ekrane – iki N px“)
        self.valdikliu_grupes = {}  # varnelių ir mygtukų grupės, kurias reikia (de)aktyvuoti kartu
        self.skiltys = {}  # skilties rėmelio vardas (str) → įjungimo raktas
        r = self.sasaja = ttk.Frame(self.root)
        r.pack(fill="both", expand=True)

        antraste = ttk.Frame(r, padding=(10, 8, 10, 0))
        antraste.pack(fill="x")
        # Kairėje – apsnigtas pixel art „SNIEGAS“ (vietoj logotipo, pavadinimo, versijos ir datos – jie lange
        # „Apie“ ir lango antraštėje); dešinėje „Apie…“ ir kalba – vienoje eilėje, sulygiuoti per vidurį
        self.piesti_piks_uzrasa(antraste, "SNIEGAS").pack(side="left")
        desine = ttk.Frame(antraste)
        desine.pack(side="right")
        ttk.Button(desine, text=T("Apie…"), command=self.rodyti_apie).pack(side="left", padx=(0, 16))
        ttk.Label(desine, text=T("Kalba")).pack(side="left", padx=(0, 4))
        self.kalbos_kint = tk.StringVar(value=self.n["kalba"])
        for k in KALBOS:
            ttk.Radiobutton(desine, text=k.upper(), value=k, variable=self.kalbos_kint, style="Toolbutton", width=3,
                            command=self.pakeista_kalba).pack(side="left", padx=1)

        virsus = ttk.Frame(r, padding=8)
        virsus.pack(fill="both", expand=True)
        # Išdėstymas: kairėje – sniegas ir oras (snaigės ir po jomis „Kita“; vėjas, sniego kaupimasis), tada
        # vertikali skirtukė, dešinėje – puošmenos (eglutės, girliandos, fejerverkai; bumbuliukai, sniego senis,
        # buldozeriukai). Grupės skiriasi ir fonu (SKILCIU_SPALVOS).
        stulpeliai = [ttk.Frame(virsus) for _ in range(4)]
        for i, s in enumerate(stulpeliai):
            s.grid(row=0, column=i + (i >= 2), sticky="n", padx=(0 if i in (0, 2) else 8, 0))
        ttk.Separator(virsus, orient="vertical").grid(row=0, column=2, sticky="ns", padx=12)
        self.kurti_snaigiu_skilti(stulpeliai[0])
        g = self.skilties_remas(stulpeliai[1], "Vėjas", "vejas_ijungtas")
        g.pack(fill="x")
        self.kurti_vejo_skilti(g)

        g = self.skilties_remas(stulpeliai[1], "Sniego kaupimasis", "kaupimasis")
        g.pack(fill="x")
        self.zymimasis(g, "kaupti_apacioje", "Kaupti ekrano apačioje", 0)
        self.slankiklis(g, "max_aukstis", "Didžiausias aukštis apačioje, px", 1)
        self.zymimasis(g, "kaupti_languose", "Kaupti ant langų viršaus", 2)
        self.slankiklis(g, "max_aukstis_languose", "Didžiausias aukštis languose, px", 3)
        for raktas in ("max_aukstis", "max_aukstis_languose"):
            self.papildomi_aprasai[raktas] = (lambda raktas=raktas: T(
                "Taškais 1920×1080 ekrane; didesniame – proporcingai daugiau (šiame ekrane ×{k}, t. y. iki {px} px).")
                .format(k=f"{self.k:.2f}".rstrip("0").rstrip("."), px=round(self.n[raktas] * self.k)))
        self.slankiklis(g, "kaupimo_greitis", "Kaupimosi greitis, %", 4)
        ttk.Button(g, text=T("Nuvalyti sniegą"), command=self.nuvalyti).grid(row=5, column=0, columnspan=2,
                                                                         sticky="w", padx=4, pady=(4, 0))

        # Paruoštukai – virš „Kita“; jų plytelės ištempiamos per
        # likusį stulpelio aukštį
        g = self.paruostuku_remas = ttk.LabelFrame(stulpeliai[1], text=T("Paruoštukai"), padding=6)
        g.pack(fill="x")
        self.paruostuku_kint = tk.IntVar(value=-1)
        self.paruostuku_mygtukai = []
        for i, apr, fonas, tekstas in PARUOSTUKU_PLYTOS:
            pav = NUMATYTUJU_PAV if i == NUMATYTIEJI else PARUOSTUKAI[i][0]
            veiksmas = self.atkurti_numatytuosius if i == NUMATYTIEJI else (lambda i=i: self.pritaikyti_paruostuka(i))
            pl = ParuostukoPlyta(g, T(pav), T(apr), fonas, tekstas, lambda f=veiksmas: self.root.after_idle(f))
            pl.remas.pack(fill="both", expand=True, pady=1)
            Patarimas(pl.remas, (T("Grąžina visus nustatymus į numatytuosius (kalba lieka).") if i == NUMATYTIEJI else
                                 T("Paruošti nustatymų rinkiniai. Keičia tik savo nustatymus – kiti lieka tavo."))
                      + "\n" + T("Pažymėtas ✓ – šiuo metu galiojantis; pakeitus jo nustatymą, žymė dingsta."))
            pl.paruostukas = i
            self.paruostuku_mygtukai.append(pl)

        g = ttk.LabelFrame(stulpeliai[1], text=T("Kita"), padding=6)
        g.pack(fill="x")
        # Tik 30, 60 arba 120: kadrai sinchronizuojami su ekrano atnaujinimu (60 Hz ekrane – kas antrą arba
        # kiekvieną; 120 Hz – kas 4, 2 ar kiekvieną); kitos reikšmės vis tiek būtų suapvalintos iki vienos iš šių.
        ttk.Label(g, text=T("Kadrų per sekundę")).grid(row=0, column=0, sticky="w", padx=4, pady=1)
        v = self.kint["fps"] = tk.IntVar(value=self.n["fps"])
        kadrai = ttk.Frame(g)
        kadrai.grid(row=0, column=1, sticky="w", padx=4, pady=1)
        patarimai = {30: "30 – mažiausia apkrova.",
                     60: "60 – sklandžiau, bet procesorius dirba maždaug dvigubai daugiau.",
                     120: "120 – tik 120 Hz ar greitesniam ekranui (60 Hz ekrane veiks kaip 60). "
                          "Procesorius dirba maždaug 4 kartus daugiau nei su 30."}
        for reiksme in (30, 60, 120):
            rb = ttk.Radiobutton(kadrai, text=str(reiksme), value=reiksme, variable=v,
                                 command=lambda: self.pakeista("fps"))
            rb.pack(side="left", padx=(0, 10))
            Patarimas(rb, T(patarimai[reiksme]))
        self.zymimasis(g, "slepti_pilname_ekrane", "Slėpti sniegą, kai kita programa per visą ekraną", 1)
        self.autostartas = tk.BooleanVar(value=autostartas_ijungtas() is not None)
        cb = ttk.Checkbutton(g, text=T("Paleisti kartu su Windows"), variable=self.autostartas,
                             command=self.perjungti_autostarta)
        cb.grid(row=2, column=0, columnspan=2, sticky="w", padx=4, pady=2)
        Patarimas(cb, T("Programa pasileidžia automatiškai prisijungus prie Windows."))
        et = ttk.Label(g, text=T("Išjungimo mygtukas"))
        et.grid(row=3, column=0, sticky="w", padx=4, pady=(2, 0))
        self.patarimas_nustatymui(et, "kryzelis")
        self.kryzelio_kint = tk.StringVar(value=T(KRYZELIO_TEKSTAI[KRYZELIO_VEIKSMAI.index(self.n["kryzelis"])]))
        kb = self.kryzelio_kb = ttk.Combobox(g, textvariable=self.kryzelio_kint, values=[T(t) for t in KRYZELIO_TEKSTAI],
                                             state="readonly", width=15)
        kb.grid(row=3, column=1, sticky="w", padx=4, pady=(2, 0))
        kb.bind("<<ComboboxSelected>>", lambda e: self.pakeistas_kryzelis())
        self.patarimas_nustatymui(kb, "kryzelis")
        self.zymimasis(g, "diagnostika", "Diagnostikos žurnalas", 4)
        ttk.Button(g, text=T("Atverti"), command=self.atverti_zurnala, width=10).grid(row=4, column=1, sticky="e",
                                                                                     padx=4, pady=2)
        # „Išplėstos ribos“ – čia, ne apatinėje mygtukų juostoje (ten atrodė kaip pagrindinis mygtukas)
        self.be_apribojimu_kint = tk.BooleanVar(value=self.n["be_apribojimu"])
        cb = ttk.Checkbutton(g, text=T("Išplėstos ribos"), variable=self.be_apribojimu_kint,
                             command=self.perjungti_apribojimus)
        cb.grid(row=5, column=0, columnspan=2, sticky="w", padx=4, pady=2)
        Patarimas(cb, T("Leidžia nustatyti daug didesnius kiekius ir dydžius. Kompiuteris gali pradėti strigti."))
        ttk.Label(g, text=T("Nustatymai")).grid(row=6, column=0, sticky="w", padx=4, pady=(2, 0))
        bylos = ttk.Frame(g)
        bylos.grid(row=6, column=1, sticky="e", padx=4, pady=(2, 0))
        b = ttk.Button(bylos, text=T("Eksportuoti…"), command=self.eksportuoti_nustatymus)
        b.pack(side="left", padx=(0, 4))
        Patarimas(b, T("Išsaugoti visus nustatymus į bylą (pvz., perkelti į kitą kompiuterį)."))
        b = ttk.Button(bylos, text=T("Importuoti…"), command=self.importuoti_nustatymus)
        b.pack(side="left")
        Patarimas(b, T("Įkelti nustatymus iš bylos. Kalba lieka dabartinė; byloje nesantys nustatymai – numatytieji."))

        self.kurti_egliu_skilti(stulpeliai[2])
        self.kurti_girliandu_skilti(stulpeliai[2])
        self.kurti_fejerverku_skilti(stulpeliai[2])
        self.kurti_bumbulu_skilti(stulpeliai[3])
        self.kurti_senio_skilti(stulpeliai[3])
        self.kurti_ekskavatoriu_skilti(stulpeliai[3])
        # tarpai tarp skilčių – vienodi, nepriklausomai nuo to, kuri skiltis stulpelyje kelinta
        for stulpelis in stulpeliai:
            for j, w in enumerate(stulpelis.winfo_children()):
                w.pack_configure(pady=(8 if j else 0, 0))
        # puošmenų stulpeliai – vienodo aukščio: paskutinė skiltis ištempiama iki apačios (apačios sulygiuotos)
        for stulpelis in stulpeliai[1:]:  # ir 2-asis (vėjas, kaupimasis, paruoštukai, kita)
            stulpelis.grid_configure(sticky="ns")
            ist = self.paruostuku_remas if stulpelis is stulpeliai[1] else stulpelis.winfo_children()[-1]
            ist.pack_configure(fill="both", expand=True)

        mygtukai = ttk.Frame(r, padding=(8, 0, 8, 8))
        mygtukai.pack(fill="x")
        # pastovus plotis – kad keičiantis užrašui mygtukai nešokinėtų
        # Sniegas ir kiti efektai įjungiami varnelėmis skilčių pavadinimuose; čia – tik laikinas paslėpimas.
        self.rodymo_mygtukas = ttk.Button(mygtukai, text=T("Rodyti viską" if self.vartotojas_paslepe else "Paslėpti viską"),
                                          width=16, command=self.perjungti_rodyma)
        self.rodymo_mygtukas.pack(side="left")
        # Atskiro mygtuko „Į sistemos dėklą“ nebėra: tą patį daro „Sumažinti“ ir X.
        # „Išplėstos ribos“ – skiltyje „Kita“.
        ttk.Button(mygtukai, text=T("Išjungti"), command=self.baigti).pack(side="right")
        self.atnaujinti_paruostukus()

        self.busena = ttk.Label(r, text="", anchor="w", relief="sunken", padding=(6, 2))
        self.busena.pack(fill="x", side="bottom")
        self.busena.bind("<Double-Button-1>", lambda e: self.isvalyti_busena())
        Patarimas(self.busena, lambda: T("Dukart spustelėkite – išvalyti klaidą ir skaitiklius.")
                  if (self.paskutine_klaida or self.windows_trynimai > self.__dict__.get("busenos_trynimai0", 0)
                      or getattr(self, "ekranu_perkurimai", 0) > self.__dict__.get("busenos_perkurimai0", 0)) else None)

        for stulpelis in stulpeliai:
            for g in stulpelis.winfo_children():
                for vardas, (fonas, antraste) in SKILCIU_SPALVOS.items():
                    if g.winfo_class() == "TLabelframe" and getattr(g, "sk_vardas", g.cget("text")) in (vardas, T(vardas)):
                        self.spalvinti_skilti(g, fonas, antraste)

        self.atnaujinti_skiltis()
        self.atnaujinti_ispejimus()
        self.pritaikyti_perziuru_plocius()

    def perziuru_raktas(self):
        return self.n["kalba"], self.n["be_apribojimu"]

    def pritaikyti_perziuru_plocius(self):
        """Kiekviena peržiūra – per visą savo skilties plotį (stulpeliai skirtingo pločio, todėl ir peržiūros).
        Jei reikia platesnių – sąsaja perkuriama kartą."""
        if self.plociu_praejimas:
            return
        try:
            self.sasaja.update_idletasks()

            def laisva(drobe):
                g = drobe.master  # skilties rėmelis: jo vidaus plotis = stulpelio plotis − paraštės
                stulpelis = g.master
                return stulpelis.winfo_reqwidth() - (g.winfo_reqwidth() - g.grid_bbox()[2])

            drobes = {"vejas": self.vejo_drobe, "fejerverkai": self.fj_drobe, "egles": self.egliu_drobe,
                      "girliandos": self.girl_drobe, "ekskavatoriai": self.ekskav_drobe, "bumbulai": self.bumbulu_drobe,
                      "seniai": self.senio_drobe}
            nauji = {k: laisva(d) for k, d in drobes.items()}
        except (tk.TclError, AttributeError):
            return
        if all(v <= pp(k) for k, v in nauji.items()):  # tik platinama – kad nesuktų perkūrimo ratu
            self.perziuru_plociai[self.perziuru_raktas()] = dict(PERZ_PLOCIAI)
            return
        nustatyti_perziuru_plocius({k: max(v, pp(k)) for k, v in nauji.items()})
        self.plociu_praejimas = True
        try:
            self.kurti_sasaja()
        finally:
            self.plociu_praejimas = False
        self.perziuru_plociai[self.perziuru_raktas()] = dict(PERZ_PLOCIAI)

    def skilties_remas(self, tevas, vardas, raktas):
        """Skiltis, kurios pavadinimas – varnelė: ja įjungiamas / išjungiamas visas efektas. Išjungus visi
        skilties nustatymai papilkėja (lieka matomi, kad langas nešokinėtų). Taip – visose skiltyse vienodai."""
        g = ttk.LabelFrame(tevas, padding=6)
        g.sk_vardas = vardas
        v = tk.BooleanVar(value=self.n[raktas])
        self.kint[raktas] = v
        antr = ttk.Frame(g)  # varnelė ir ↺ (skilties nustatymai – į numatytuosius)
        cb = ttk.Checkbutton(antr, text=T(vardas), variable=v, command=lambda: self.pakeista(raktas))
        cb.pack(side="left")
        self.patarimas_nustatymui(cb, raktas)
        if raktas in SKILCIU_NUSTATYMAI:
            at = ttk.Label(antr, cursor="hand2", padding=(4, 0, 0, 0))
            at.pack(side="left")
            at.visada_aktyvus = True  # ir išjungtos skilties nustatymus galima atkurti
            at.configure(image=self.atkurimo_ikona(vardas))  # neryški (pilka) – kaip naudotojui patiko
            at.bind("<Button-1>", lambda e: self.root.after_idle(lambda: self.atkurti_skilti(raktas, vardas)))
            Patarimas(at, lambda: T("Grąžinti šios skilties nustatymus į numatytuosius (įjungimo varnelė nekeičiama).")
                      if self.skiltis_pakeista(raktas) else T("Visi šios skilties nustatymai – numatytieji."))
        g.configure(labelwidget=antr)
        cb.antraste = True
        self.valdikliai[raktas] = cb
        self.skiltys[str(g)] = raktas
        return g

    def skilties_ijungta(self, w):
        """Ar įjungta skiltis, kurioje yra valdiklis w (ne skiltyje – visada įjungta)."""
        while w is not None:
            raktas = self.skiltys.get(str(w))
            if raktas is not None:
                return self.n[raktas]
            w = w.master
        return True

    def valdiklio_busena(self, w, ijungta):
        """Valdiklio būsena: aktyvus tik jei jo sąlyga tenkinama IR jo skiltis įjungta (laukelis ir jo juosta)."""
        busena = ("!disabled",) if ijungta and self.skilties_ijungta(w) else ("disabled",)
        w.state(busena)
        if getattr(w, "slankiklis", None) is not None:
            w.slankiklis.state(busena)

    def atnaujinti_skiltis(self):
        """Pirma visi skilties valdikliai – pagal skilties varnelę, tada – priklausomi nustatymai."""
        if not getattr(self, "skiltys", None):
            return
        try:
            for kelias, raktas in self.skiltys.items():
                ijungta = self.n[raktas]
                stekas = list(self.root.nametowidget(kelias).winfo_children())
                while stekas:
                    w = stekas.pop()
                    stekas.extend(w.winfo_children())
                    if isinstance(w, ttk.Widget) and not getattr(w, "antraste", False) and \
                            not getattr(w, "visada_aktyvus", False):
                        w.state(("!disabled",) if ijungta else ("disabled",))
        except (tk.TclError, KeyError):
            return  # nustatymų langas uždarytas / perkuriamas
        self.atnaujinti_egliu_valdiklius()
        self.atnaujinti_bumbulu_valdiklius()
        self.atnaujinti_fejerverku_valdiklius()
        self.atnaujinti_senio_valdiklius()

    def atnaujinti_senio_valdiklius(self):
        """Lempučių animacijos pasirinkimas – tik kai lemputės įjungtos (ir įjungta senio skiltis)."""
        kb = self.__dict__.get("senio_lempuciu_kb")
        if kb is None:
            return
        try:
            ijungta = self.n["sniego_senis"] and self.n["senio_lemputes"]
            kb.state(("!disabled", "readonly") if ijungta else ("disabled",))
        except tk.TclError:
            pass

    def spalvinti_skilti(self, g, fonas, antraste=None):
        """Skilties fonas ir antraštė: ttk valdikliai fono nepaveldi, todėl kiekvienai spalvai sukuriami savi
        stiliai (rėmeliui, etiketėms, žymimiesiems langeliams, perjungikliams, vidiniams rėmeliams, slinkties
        juostoms) ir priskiriami visiems skilties valdikliams. Mygtukai ir įvedimo laukai lieka įprasti.
        fonas None – skiltis be fono; antraste – antraštės (skilties pavadinimo) spalva, paryškinta."""
        st = ttk.Style(self.root)
        pr = "Sk" + (fonas or "be").lstrip("#") + (antraste or "").lstrip("#")
        klases = ("TLabelframe", "TLabel", "TCheckbutton", "TRadiobutton", "TFrame")
        sviesumas = sum(int(fonas[i:i + 2], 16) for i in (1, 3, 5)) / (3 * 255) if fonas else 1.0
        tamsus, vidutinis = sviesumas < 0.4, 0.4 <= sviesumas < 0.85
        if fonas:
            for kl in klases + ("TLabelframe.Label",):
                st.configure(f"{pr}.{kl}", background=fonas)
                if tamsus:  # tamsiame fone – šviesus tekstas, papilkėjęs – blankiai šviesus
                    st.configure(f"{pr}.{kl}", foreground=SKILTIES_TAMSI_TEKSTAS)
                    st.map(f"{pr}.{kl}", foreground=[("disabled", SKILTIES_TAMSI_PILKA)])
                elif vidutinis:  # vidutinio šviesumo fone įprastas pilkas (papilkėjęs) tekstas beveik nesimatytų
                    st.map(f"{pr}.{kl}", foreground=[("disabled", _maisyti(fonas, "#000000", 0.45))])
            for kl in ("TCheckbutton", "TRadiobutton", "TLabel", "TLabelframe", "TFrame", "TLabelframe.Label"):
                # kad užvedus pelę / papilkėjus fonas neparbaltų (tamsiame fone tai labai matytųsi)
                st.map(f"{pr}.{kl}", background=[("active", fonas), ("disabled", fonas)])
            # slinkties juostos takelis – kiek tamsesnis (tamsiame fone – šviesesnis) skilties fono atspalvis
            takelis = _maisyti(fonas, "#ffffff", 0.22) if tamsus else \
                "#%02x%02x%02x" % tuple(int(int(fonas[i:i + 2], 16) * 0.86) for i in (1, 3, 5))
            st.configure(f"{pr}.{SLINKTIES_STILIUS}", troughcolor=takelis)
            st.map(f"{pr}.{SLINKTIES_STILIUS}", troughcolor=[("disabled", takelis)])
        if antraste:
            st.configure(f"{pr}.Antraste.TCheckbutton", foreground=antraste, font=("Segoe UI", 9, "bold"))
            st.configure(f"{pr}.Antraste.TLabelframe.Label", foreground=antraste, font=("Segoe UI", 9, "bold"))
            if fonas:
                st.configure(f"{pr}.Antraste.TCheckbutton", background=fonas)
                st.map(f"{pr}.Antraste.TCheckbutton", background=[("active", fonas)])
                st.configure(f"{pr}.Antraste.TLabelframe.Label", background=fonas)
            if not getattr(g, "cget", None) or not str(g.cget("labelwidget")):
                g.configure(style=f"{pr}.Antraste.TLabelframe")
                st.configure(f"{pr}.Antraste.TLabelframe", **({"background": fonas} if fonas else {}))

        def per(w):
            kl = w.winfo_class()
            if getattr(w, "antraste", False) and antraste:
                w.configure(style=f"{pr}.Antraste.TCheckbutton")
            elif kl == "TScale" and fonas:
                w.configure(style=f"{pr}.{SLINKTIES_STILIUS}")
            elif kl in klases and not str(w.cget("style")) and fonas:
                w.configure(style=f"{pr}.{kl}")
            for v in w.winfo_children():
                per(v)
        per(g)

    def pakeista_kalba(self):
        kalba = self.kalbos_kint.get()
        if kalba == self.n["kalba"]:
            return
        self.n["kalba"] = kalba
        nustatyti_kalba(kalba)
        self.issaugoti()
        # perkuriama ne mygtuko paspaudimo viduje – tada jis pats dar „gyvas“
        self.root.after_idle(self.kurti_sasaja)

    def dialogo_vieta(self, plotis, aukstis):
        """Dialogo (x, y): nustatymų lango viduryje, bet visas to ekrano darbo srityje – net jei nustatymų langas
        nustumtas į kraštą. Kitame ekrane koordinatės gali būti neigiamos (todėl ne max(0, …))."""
        r = self.root
        x = r.winfo_rootx() + (r.winfo_width() - plotis) // 2
        y = r.winfo_rooty() + (r.winfo_height() - aukstis) // 3
        rl, rt = r.winfo_rootx(), r.winfo_rooty()
        rr, rb = rl + r.winfo_width(), rt + r.winfo_height()

        def bendra(m):  # kiek nustatymų lango yra tame ekrane (jo centras gali būti ir už ekrano)
            ml, mt, mr, mb = m[0]
            return max(0, min(rr, mr) - max(rl, ml)) * max(0, min(rb, mb) - max(rt, mt))
        monitoriai = getattr(self, "monitoriai", None) or ()
        if monitoriai:
            dl, dt, dr, db = max(monitoriai, key=bendra)[1]
            x = max(dl, min(x, dr - plotis))
            y = max(dt, min(y, db - aukstis))
        return x, y

    def rodyti_apie(self):
        """Langas „Apie“: pavadinimas, versija, autorius, testuotojas ir kuo kurta.
        Vienas – antrą kartą paspaudus iškeliamas esamas."""
        senas = getattr(self, "apie_langas", None)
        if senas is not None and senas.winfo_exists():
            senas.deiconify()
            senas.lift()
            senas.focus_force()
            return
        w = self.apie_langas = tk.Toplevel(self.root)
        w.title(T("Apie") + " – Sniegas")
        w.resizable(False, False)
        w.transient(self.root)
        r = ttk.Frame(w, padding=16)
        r.pack(fill="both", expand=True)
        kaire = ttk.Frame(r)
        kaire.grid(row=0, column=0, sticky="nw")
        self.piesti_piks_uzrasa(kaire, "SNIEGAS").pack(anchor="w", pady=(0, 4))
        ttk.Label(kaire, text=T("versija {v} ({d})").format(v=VERSIJA, d=DATA), foreground="#555555").pack(anchor="w")
        ttk.Separator(kaire).pack(fill="x", pady=10)
        for antr, reiksme in ((T("Autorius"), AUTORIUS), (T("Testuotojas"), TESTUOTOJAS)):
            e = ttk.Frame(kaire)
            e.pack(anchor="w", pady=1)
            ttk.Label(e, text=antr + ":", foreground="#555555").pack(side="left")
            ttk.Label(e, text=" " + reiksme, font=("Segoe UI", 9, "bold")).pack(side="left")
        ttk.Label(kaire, text=T("Sukurta su Claude (Anthropic) pagalba"), foreground="#555555").pack(anchor="w", pady=(10, 0))
        licencija = ttk.Label(kaire, text=T("Laisva programa – GNU GPL 3.0 licencija"), foreground="#1a5fb4", cursor="hand2")
        licencija.pack(anchor="w", pady=(2, 0))
        licencija.bind("<Button-1>", lambda e: webbrowser.open(LICENCIJOS_NUORODA))
        Patarimas(licencija, T("Galima laisvai naudoti, keisti ir platinti; pakeistos versijos – irgi su atviru kodu pagal "
                               "tą pačią licenciją. Spustelėkite – licencijos tekstas."))
        ttk.Button(r, text=T("Uždaryti"), command=w.destroy).grid(row=1, column=0, sticky="e", pady=(14, 0))
        w.bind("<Escape>", lambda e: w.destroy())
        w.update_idletasks()
        w.geometry("+%d+%d" % self.dialogo_vieta(w.winfo_reqwidth(), w.winfo_reqheight()))
        w.focus_force()

    def piesti_piks_uzrasa(self, tevas, tekstas, P=4):
        """Užrašas pixel art raidėmis (PIKS_RAIDES): tamsiai žalios raidės, ant jų viršaus – sniego kepurėlės
        (baltas taškas su pilku kontūru virš kiekvieno viršutinio raidės taško). Grąžina drobę."""
        fonas = ttk.Style(self.root).lookup("TFrame", "background") or "#f0f0f0"
        raides = [PIKS_RAIDES[c] for c in tekstas]
        plotis = sum(len(r_[0]) + 1 for r_ in raides) - 1
        virsus = 2  # vieta sniegui
        c = tk.Canvas(tevas, width=plotis * P + 2, height=(7 + virsus) * P + 2, bg=fonas, highlightthickness=0)
        x0 = 1
        for r_ in raides:
            w_ = len(r_[0])
            for y, eil in enumerate(r_):
                for x, ch in enumerate(eil):
                    if ch != "#":
                        continue
                    X, Y = x0 + x * P, 1 + (y + virsus) * P
                    c.create_rectangle(X, Y, X + P, Y + P, fill="#243508", outline="")
                    if y == 0 or r_[y - 1][x] != "#":  # viršutinis taškas – ant jo prisnigo
                        c.create_rectangle(X, Y - P, X + P, Y, fill="#ffffff", outline="")
                        c.create_line(X, Y - P - 1, X + P, Y - P - 1, fill="#9fb3c8")
            x0 += (w_ + 1) * P
        return c

    def kurti_snaigiu_skilti(self, tevas):
        g = self.skilties_remas(tevas, "Snaigės", "snaiges")
        g.pack(fill="x")
        ttk.Label(g, text=T("Rūšis")).grid(row=0, column=1, sticky="w", padx=4)
        ttk.Label(g, text=T("Kiek (0–{m})").format(m=self.maks_tipo())).grid(row=0, column=2, sticky="w", padx=4)
        self.tipu_kint = []
        self.tipu_drobes = []
        for i, (pavadinimas, _, _) in enumerate(TIPAI):
            drobe = tk.Canvas(g, width=IKONA, height=IKONA, bg=DANGUS, highlightthickness=0)
            drobe.grid(row=i + 1, column=0, pady=1)
            self.tipu_drobes.append(drobe)
            self.animuoti_uzvedus(drobe, "snaiges", lambda: self.piesti_tipu_perziuras())
            etikete = ttk.Label(g, text=T(pavadinimas))
            etikete.grid(row=i + 1, column=1, sticky="w", padx=4)
            v = tk.StringVar(value=str(self.n["tipai"][i]))
            etikete.bind("<Double-Button-1>", lambda e, v=v, i=i: v.set(str(NUMATYTI["tipai"][i])))
            v.trace_add("write", lambda *_: self.pakeisti_tipai())
            remas, sb = self.skaicius_su_juosta(g, v, 0, self.maks_tipo(), lambda i=i: self.n["tipai"][i], 5)
            remas.grid(row=i + 1, column=2, sticky="w", padx=4)
            sb.bind("<FocusOut>", lambda e, v=v, i=i: v.set(str(self.n["tipai"][i])))  # tuščią – atkuria
            self.tipu_kint.append(v)
        self.piesti_tipu_perziuras()
        # Vienas tinklelis visai skilčiai: 0 – piktograma, 1 – pavadinimas, 2 – juosta ir skaičius,
        # 3 – prierašas. Visos juostos (rūšių, bendro kiekio, dydžio ir kt.) – viename stulpelyje, lygiai po viena kita.
        e = len(TIPAI) + 1
        ttk.Separator(g, orient="horizontal").grid(row=e, column=0, columnspan=4, sticky="we", padx=4, pady=(10, 8))
        # Bendras kiekis: patempus – atsitiktinai paskirstomas po rūšis (matosi rūšių eilutėse)
        self.is_viso_kint = tk.StringVar(value=str(sum(self.n["tipai"])))
        etikete = ttk.Label(g, text=T("Iš viso snaigių"), font=("Segoe UI", 9, "bold"))
        etikete.grid(row=e + 1, column=0, columnspan=2, sticky="w", padx=4)
        remas, sb = self.skaicius_su_juosta(g, self.is_viso_kint, 0, self.maks_viso(), lambda: sum(self.n["tipai"]),
                                            10)
        remas.grid(row=e + 1, column=2, sticky="w", padx=4)
        self.is_viso = ttk.Label(g, text="", foreground="#666666")  # „iš 1000“
        self.is_viso.grid(row=e + 1, column=3, sticky="w", padx=(0, 4))
        self.is_viso_kint.trace_add("write", lambda *_: self.pakeistas_is_viso())
        sb.bind("<FocusOut>", lambda e_: self.is_viso_kint.set(str(sum(self.n["tipai"]))))
        aprasas = T("Bendras snaigių kiekis. Pakeitus jį čia, kiekis atsitiktinai paskirstomas po rūšis (kiek "
                    "kurios – matosi rūšių eilutėse aukščiau). Vėl pakeitus po pertraukos – parenkamas naujas "
                    "atsitiktinis rūšių mišinys.")
        aprasas += "\n" + T("Dukart spustelėkite pavadinimą – numatytieji ({v}, įprastas rūšių mišinys)").format(
            v=sum(NUMATYTI["tipai"]))
        for w in (etikete, remas):
            Patarimas(w, aprasas)
        etikete.bind("<Double-Button-1>", lambda e_: self.numatytas_snaigiu_kiekis())
        self.atnaujinti_is_viso()
        ttk.Separator(g, orient="horizontal").grid(row=e + 2, column=0, columnspan=4, sticky="we", padx=4, pady=(8, 6))

        e += 3
        self.slankiklis(g, "dydis", "Dydis, %", e, ilgis=2)
        self.slankiklis(g, "greitis", "Kritimo greitis, %", e + 1, ilgis=2)
        self.slankiklis(g, "svyravimas", "Svyravimas į šonus, %", e + 2, ilgis=2)
        self.slankiklis(g, "plasnojimas", "Plasnojimas, %", e + 3, ilgis=2)
        et = ttk.Label(g, text=T("Stilius"))
        et.grid(row=e + 4, column=0, columnspan=2, sticky="w", padx=4, pady=(6, 2))
        self.patarimas_nustatymui(et, "snaigiu_stilius")
        stilius = ttk.Frame(g)
        stilius.grid(row=e + 4, column=2, columnspan=2, sticky="w", padx=4, pady=(6, 2))
        v = tk.StringVar(value=self.n["snaigiu_stilius"])
        self.kint["snaigiu_stilius"] = v
        for tekstas, reiksme in (("Įprastos", "iprastos"), ("Pixel art", "pikseliai")):
            rb = ttk.Radiobutton(stilius, text=T(tekstas), variable=v, value=reiksme,
                                 command=lambda: self.pakeista("snaigiu_stilius"))
            rb.pack(side="left", padx=(0, 8))
            self.patarimas_nustatymui(rb, "snaigiu_stilius")
        self.zymimasis(g, "snaiges_sukasi", "Snaigės sukasi", e + 5, ilgis=4)
        self.zymimasis(g, "sniego_konturas", "Sniego kontūras ekrano apačioje", e + 6, ilgis=4)
        self.zymimasis(g, "sniegas_blizga", "Sniegas kartais sužiba", e + 7, ilgis=4)

    def kurti_girliandu_skilti(self, tevas):
        g = self.skilties_remas(tevas, "Girliandos", "girliandos")
        g.pack(fill="x")
        self.girl_drobe = tk.Canvas(g, width=pp("girliandos"), height=PERZ_MAZA[1], bg=DANGUS, highlightthickness=0)
        self.animuoti_uzvedus(self.girl_drobe, "girliandos", lambda: self.piesti_girl_perziura())
        self.girl_drobe.grid(row=0, column=0, columnspan=2, pady=(0, 6))
        self.slankiklis(g, "girliandu_kiekis", "Lempučių vienoje pusėje", 2)
        self.papildomi_aprasai["girliandu_kiekis"] = lambda: None if self.girliandu_telpa() is None else T(
            "Šiame ekrane su dabartiniu dydžiu telpa iki {n} lempučių – daugiau nebus.").format(n=self.girliandu_telpa())
        self.slankiklis(g, "girliandu_dydis", "Dydis, %", 3)
        self.slankiklis(g, "girliandu_mirksejimas", "Mirksėjimas, % (0 – nemirksi)", 4)
        self.zymimasis(g, "girliandu_atspindziai", "Atspindžiai stikle (kartais blyksteli)", 5)
        self.girl_perziura = {"mirk": girliandos_valdiklis(random.Random(3), self.girl_perz_lemputes())}
        self.piesti_girl_perziura()

    @staticmethod
    def girl_perz_lemputes():
        return max(8, (pp("girliandos") - 40) // 37 + 1)  # tarpas 37 px, kraštuose po ~20 px

    def piesti_girl_perziura(self):
        """Peržiūroje – klasikiškai: laidas per viršų nusvyra tarp lempučių, lemputės kabo žemyn."""
        c = self.girl_drobe
        c.delete("all")
        n = self.girl_perz_lemputes()
        # lemputė – tikro dydžio, bet ne stambesnė nei 2 px langelis (kaip kitose peržiūrose)
        P, tarpas = min(2.0, self.perziuros_mastelis("girliandu_dydis", 1.12, trupmeninis=True)[1]), 37
        x0 = (pp("girliandos") - (n - 1) * tarpas) // 2
        for x in range(0, pp("girliandos"), 1):
            y = 4 + 5 * (0.5 - 0.5 * math.cos(2 * math.pi * (x - x0) / tarpas))
            faze = math.sin(2 * math.pi * x / 8)
            c.create_rectangle(x, int(y + faze), x + 1, int(y + faze) + 1, fill=GIRL_LAIDAS, outline="")
            c.create_rectangle(x, int(y - faze), x + 1, int(y - faze) + 1, fill=GIRL_LAIDAS2, outline="")
        uzvesta = "girliandos" in self.uzvesta
        lygiai = self.girl_perziura["mirk"]["lygiai"] if uzvesta else (GIRL_LYGIAI - 1,) * n
        fazes = self.girl_perziura["mirk"]["blyksnio_fazes"] if uzvesta else (0,) * n
        p = DrobesPiesejas(c)
        for j in range(n):
            piks_piesti(p, girliandos_lemputes_tinklelis(j % len(GIRL_SPALVOS), lygiai[j], "zemyn", fazes[j]),
                        x0 + j * tarpas - round(GIRL_STORIS * P / 2), 4, P)
        bb = c.bbox("all")  # girlianda – per peržiūros vidurį
        c.move("all", 0, (PERZ_MAZA[1] - bb[1] - bb[3]) // 2)

    def kurti_vejo_skilti(self, g):
        self.vejo_drobe = tk.Canvas(g, width=VEJO_PERZ_W, height=VEJO_PERZ_H, bg=DANGUS, highlightthickness=0)
        self.vejo_drobe.grid(row=0, column=0, columnspan=2, pady=(0, 4))
        self.vejo_skiltis = g
        # Tik pagrindiniai: pauzė tarp gūsių, jų trukmė, įsibėgėjimas ir nurimimas – pastovūs.
        self.slankiklis(g, "vejas", "Įprastas vėjas", 1)
        vienetai = T("Vėjo skaičiai – sąlyginiai vienetai, ne m/s. 1 – artimos snaigės nunešamos į šoną apie 12 taškų "
                     "per sekundę (1920×1080 ekrane; didesniame – proporcingai), 3 – apie 36 ir t. t.; tolimos – lėčiau.")
        self.papildomi_aprasai["vejas"] = lambda: vienetai
        Patarimas(self.vejo_drobe, T("Peržiūroje – dabartinis vėjas: kryptis, stiprumas ir ar dabar ramu, gūsis, "
                                     "ar jis rimsta.") + "\n\n" + vienetai)
        self.slankiklis(g, "gusio_stiprumas", "Gūsio stiprumas", 2)
        # Skalės skirtingos: įprastas vėjas pučia iki 0,7 × „Įprastas vėjas“, gūsis – „Gūsio stiprumas“ (±20 %), todėl
        # silpnas gūsis prie stipraus vėjo beveik nesijaučia (ar net vėją susilpnina) – apie tai įspėjama.
        self.papildomi_aprasai["gusio_stiprumas"] = lambda: T(
            "Įprastas vėjas pučia iki maždaug 0,7 savo reikšmės (dabar – iki {v}); gūsis – maždaug tiek, kiek nustatyta "
            "čia.").format(v=skaicius_tekstu(0.7 * self.n["vejas"])) + "\n\n" + vienetai
        krypties_etikete = ttk.Label(g, text=T("Kryptis"))
        krypties_etikete.grid(row=3, column=0, sticky="w", padx=4, pady=1)
        kryptys = ttk.Frame(g)
        kryptys.grid(row=3, column=1, sticky="w", padx=4, pady=1)
        v = tk.StringVar(value=self.n["vejo_kryptis"])
        self.kint["vejo_kryptis"] = v
        kb = ttk.Combobox(kryptys, values=[T(t) for t in VEJO_KRYPCIU_TEKSTAI], state="readonly", width=10)
        kb.set(T(VEJO_KRYPCIU_TEKSTAI[VEJO_KRYPTYS.index(self.n["vejo_kryptis"])]))
        kb.pack(side="left")
        self.vejo_krypties_kb = kb
        for w in (krypties_etikete, kb):
            self.patarimas_nustatymui(w, "vejo_kryptis")

        def pasirinkta(_):
            v.set(VEJO_KRYPTYS[kb.current()])
            self.pakeista("vejo_kryptis")
        kb.bind("<<ComboboxSelected>>", pasirinkta)

        def numatytoji_kryptis(_):
            kb.current(VEJO_KRYPTYS.index(NUMATYTI["vejo_kryptis"]))
            pasirinkta(None)
        krypties_etikete.bind("<Double-Button-1>", numatytoji_kryptis)
        self.slankiklis(g, "gusiai", "Sūkuriai", 4)
        b = ttk.Button(g, text=T("Gūsis dabar"), command=self.gusis_dabar)
        b.grid(row=5, column=0, sticky="w", padx=4, pady=(4, 0))
        self.valdikliai["gusis_dabar"] = b

        # Peržiūra juda, kol pelė virš vėjo skilties arba įvedama jos laukelyje (fokusas).
        self.vejo_fokusas = False

        def susieti(w):
            w.bind("<FocusIn>", lambda e: setattr(self, "vejo_fokusas", True), add="+")
            w.bind("<FocusOut>", lambda e: setattr(self, "vejo_fokusas", False), add="+")
            for vaikas in w.winfo_children():
                susieti(vaikas)
        for w in g.grid_slaves():
            susieti(w)
        self.vejo_perz = {"t": 0.0, "zenklas": 1, "kreive": None, "zyma": "-", "laikas": 0.0,
                          "snaiges": [[random.uniform(0, VEJO_PERZ_W), random.uniform(VEJO_SCENA[0], VEJO_SCENA[1]),
                                       random.random(), random.uniform(0, 6.3), 0.0] for _ in range(90)]}
        self.piesti_vejo_perziura()
        self.root.after(50, self.animuoti_vejo_perziura, self.sasajos_karta)

    def pele_virs_vejo_skilties(self):
        g = self.vejo_skiltis
        px, py = self.root.winfo_pointerxy()
        x, y = g.winfo_rootx(), g.winfo_rooty()
        return x <= px < x + g.winfo_width() and y <= py < y + g.winfo_height()

    def animuoti_vejo_perziura(self, karta):
        if karta != self.sasajos_karta:  # sąsaja perkurta – šį ciklą pakeitė naujas
            return
        try:
            if self.root.state() not in ("iconic", "withdrawn"):
                if self.pele_virs_vejo_skilties() or self.vejo_fokusas:
                    self.vejo_perziuros_zingsnis(0.05)
                    self.piesti_vejo_perziura(judama=True)
                elif self.vejo_perz["zyma"] != "ramu" or self.vejo_perz["kreive"] is None:
                    self.piesti_vejo_perziura()
        except tk.TclError:
            return
        self.root.after(50, self.animuoti_vejo_perziura, karta)

    def vejo_perziuros_stiprumas(self):
        """Vėjo stiprumas peržiūros ciklo vietoje t (tiesinė interpoliacija tarp vejo_kreive taškų)."""
        taskai = self.vejo_perz["kreive"]["taskai"]
        t = self.vejo_perz["t"]
        for (ta, va), (tb, vb) in zip(taskai, taskai[1:]):
            if ta <= t <= tb:
                return va + (vb - va) * ((t - ta) / (tb - ta) if tb > ta else 0)
        return taskai[-1][1]

    def vejo_perziuros_zingsnis(self, dt):
        pz = self.vejo_perz
        if pz["kreive"] is None:
            pz["kreive"] = vejo_kreive(self.n)
        T = pz["kreive"]["T"]
        pz["t"] += dt * T / VEJO_CIKLAS_S  # visas ciklas peržiūroje trunka ~VEJO_CIKLAS_S s
        if pz["t"] >= T:
            pz["t"] -= T
            if self.n["vejo_kryptis"] == "kintanti":
                pz["zenklas"] = -pz["zenklas"]  # kintanti kryptis – kas antrą ciklą į kitą pusę
        if self.n["vejo_kryptis"] != "kintanti":
            pz["zenklas"] = 1 if self.n["vejo_kryptis"] == "desine" else -1
        pz["laikas"] += dt
        # snaigės – tos pačios formulės kaip ekrane (vėjas ×12 px/s, sūkurių laukas), tik mažesniu masteliu
        k = 0.55
        vejas = pz["zenklas"] * self.vejo_perziuros_stiprumas() * 12 * k
        sukurys = self.n["gusiai"] * 6 * k * self.n["vejas_ijungtas"]  # kaip ekrane
        t = pz["laikas"]
        virsus, apacia = VEJO_SCENA
        turb = sukurys > 0
        if turb:  # tas pats laukas kaip ekrane, sūkuriai – peržiūros masteliu (90 / 520)
            if "modos" not in pz:
                pz["modos"], pz["poslinkis"] = oro_modos(90 / 520, k), 0.0
            pz["poslinkis"] += vejas * dt
            stipr = self.n["gusiai"] * 4 * k * (1 + 0.1 * self.vejo_perziuros_stiprumas())
            modos = [(kx, ky, ux * stipr, uy * stipr, ph - kx * pz["poslinkis"] - w * t, zf)
                     for kx, ky, ux, uy, w, ph, zf in pz["modos"]]
        for f in pz["snaiges"]:
            x, y, z = f[0], f[1], 0.4 + 0.6 * f[2]
            if turb:
                u = v = 0.0
                for kx, ky, ax, ay, p, zf in modos:
                    c = math.cos((kx * x + ky * y) / z + p + zf * f[2])
                    u += ax * c
                    v += ay * c
                u, v, vk = u * z, v * z, 1.0
            else:
                u = v = 0.0
                vk = 0.6
            f[4] += (vejas * z + u - f[4]) * min(1.0, dt * 2.5)
            f[0] = (x + (f[4] + (math.sin(t * 1.7 + f[3]) + 0.45 * math.sin(t * 4.03 + f[3] * 5.47)) * 3 * z * self.n["svyravimas"] / 55) * dt) % VEJO_PERZ_W
            f[1] = y + ((14 + 16 * z) + v * vk) * dt
            if f[1] > apacia:
                f[1] = virsus - 2
            elif f[1] < virsus - 3:
                f[1] = apacia

    def piesti_vejo_perziura(self, judama=False):
        """Tik snaigės (be vėjo grafiko – jis mažai informatyvus): užvedus pelę ant vėjo skilties
        jos juda pagal nustatymus, kampe – dabartinė kryptis ir stiprumas."""
        c = self.vejo_drobe
        pz = self.vejo_perz
        if pz["kreive"] is None:
            pz["kreive"] = vejo_kreive(self.n)
        W = VEJO_PERZ_W
        busena = "juda" if judama else "ramu"
        if busena != pz["zyma"] or pz.get("pasenusi", True):
            pz["zyma"], pz["pasenusi"] = busena, False
            c.delete("statine")
            if not judama:
                c.create_text(4, 2, text=T("Užveskite pelę ant nustatymo"), anchor="nw", fill="#cfd8e3",
                              font=("Segoe UI", 8), tags="statine")
        c.delete("dinamine")
        stipr = self.vejo_perziuros_stiprumas()
        for f in pz["snaiges"]:
            d = 2 if f[2] < 0.6 else 3
            spalva = "#c8d6e5" if f[2] < 0.6 else "#ffffff"
            c.create_rectangle(int(f[0]), int(f[1]), int(f[0]) + d, int(f[1]) + d, fill=spalva, outline="",
                               tags="dinamine")
        # stiprumas – ta pati sąlyginė skalė kaip slankiklių (ne m/s); šalia – kas dabar vyksta
        gs = pz["kreive"]["gusis"]
        tt = pz["t"]
        vejo_busena = ("gūsis" if gs[0] <= tt < gs[2] else "rimsta" if gs[2] <= tt < gs[3] else "ramu") if gs else "ramu"
        rodykle = (T("vėjas {r} {v}").replace("{r}", "→" if pz["zenklas"] > 0 else "←")
                   .replace("{v}", skaicius_tekstu(stipr)) + " · " + T(vejo_busena))
        c.create_text(W - 4, 2, text=rodykle, anchor="ne", font=("Segoe UI", 9, "bold"), fill="#f1faee",
                      tags="dinamine")
        c.tag_raise("dinamine")
        c.tag_lower("statine")

    def kurti_fejerverku_skilti(self, tevas):
        g = self.skilties_remas(tevas, "Fejerverkai", "fejerverkai")
        g.pack(fill="x")
        self.fj_drobe = tk.Canvas(g, width=pp("fejerverkai"), height=PERZ_DIDELE[1], bg=DANGUS, highlightthickness=0)
        self.animuoti_uzvedus(self.fj_drobe, "fejerverkai")
        self.fj_drobe.grid(row=0, column=0, columnspan=2, pady=(0, 6))
        self.fj_pavadinimas = ""  # rūšies pavadinimas – peržiūros kampe (ne atskira eilutė)
        self.slankiklis(g, "fejerverku_intervalas", "Kas kiek minučių", 3)
        self.slankiklis(g, "fejerverku_trukme", "Trukmė, s", 4)
        # Užrašas ir mygtukas – atskiroje eilutėje per abu stulpelius, užrašas pastovaus pločio (pagal ilgiausią
        # galimą tekstą): anksčiau jis buvo slankiklių pavadinimų stulpelyje ir, keičiantis tekstui („Kitas šou…“ ↔
        # „Didysis šou! Liko…“, net minutėms 10 → 9), keitė to stulpelio plotį – pajudėdavo laukeliai ir mygtukas
        eil = ttk.Frame(g)
        eil.grid(row=5, column=0, columnspan=2, sticky="we", padx=4, pady=(4, 0))
        b = self.fj_mygtukas = ttk.Button(eil, text=T("Paleisti dabar"), command=self.fejerverku_mygtukas,
                                          width=max(len(T("Paleisti dabar")), len(T("Sustabdyti"))) + 2)
        b.pack(side="right")
        ilgiausias = max(len(T("Didysis šou! Liko {m}:{s}").format(m=59, s="59")),
                         len(T("Kitas šou: {kada} (po {min} min)").format(
                             kada="23:59", min=self.leistinos("fejerverku_intervalas")[1])),
                         len(T("Išjungta")))
        self.fj_kitas = ttk.Label(eil, text="", width=ilgiausias + 1, anchor="w")
        self.fj_kitas.pack(side="left")
        b.visada_aktyvus = True  # rankinis paleidimas veikia ir išjungus šou pagal laikrodį
        # peržiūra: visos rūšys paeiliui, mažu masteliu
        # vėjas – tas pats, kuris dabar pučia ekrane (peržiūros masteliu)
        self.fj_perziura = Fejerverkai(0.42, 2, rnd=random.Random(7), vejas=lambda: (
            self.vejas * 12 * 0.42 if isinstance(getattr(self, "vejas", None), float) else 0.0))
        self.fj_piesimo_rnd = random.Random(3)  # piešimas atskira seka – tada sprogimo aukštį galima nuspėti tiksliai
        self.fj_perziuros_nr = -1
        self.fj_perziuros_laikas = 99.0
        # kol pelė neužvesta – rodomas sustingęs pirmo fejerverko kadras
        self.fejerverku_perziuros_zingsnis()
        for _ in range(int(1.7 / 0.05)):
            self.fj_perziura.zingsnis(0.05)
        self.piesti_fejerverku_perziura()
        self.atnaujinti_fejerverku_valdiklius()
        self.root.after(50, self.animuoti_fejerverku_perziura, self.sasajos_karta)

    def zymeti_bumbulu_sou(self):
        """Kol vyksta fejerverkų šou, bumbuliukai ekrane pasislepia (pradingsta) – peržiūroje tai parašoma, kad
        nekiltų klausimas, kodėl įjungti ar iš naujo išbarstyti bumbuliukai nesimato."""
        c = getattr(self, "bumbulu_drobe", None)
        if c is None:
            return
        try:
            c.delete("sou")
            if getattr(getattr(self, "fj", None), "aktyvus", False) and self.n["bumbulai"]:
                W = pp("bumbulai")
                yc = PERZ_ZEME // 2  # vidurinė juosta: viršuje – mygtukas „Išbarstyti iš naujo“, apačioje rieda bumbuliukai
                c.create_rectangle(0, yc - 9, W, yc + 9, fill="#12233f", outline="", tags="sou")
                c.create_text(W // 2, yc, text=T("Per fejerverkus bumbuliukai slepiasi – pasirodys po šou"),
                              fill="#ffd166", font=("Segoe UI", 8), tags="sou")
        except tk.TclError:
            pass

    def atnaujinti_fejerverku_valdiklius(self):
        ijungta = self.n["fejerverkai"]
        for raktas in ("fejerverku_intervalas", "fejerverku_trukme"):
            w = self.valdikliai.get(raktas)
            if w is not None:
                self.valdiklio_busena(w, ijungta)
        self.zymeti_bumbulu_sou()
        if getattr(self, "fj_mygtukas", None) is not None:  # vykstant šou – „Sustabdyti“
            self.fj_mygtukas.configure(text=T("Sustabdyti" if self.fj.aktyvus else "Paleisti dabar"))
        if self.fj.detales and self.fj.aktyvus:
            liko = max(0, int(self.fj.pabaiga - self.fj.laikas))
            self.fj_kitas.configure(text=T("Didysis šou! Liko {m}:{s}").format(m=liko // 60, s=f"{liko % 60:02d}"))
        elif ijungta:
            iki = self.kitas_fj - time.time()
            kada = time.strftime("%H:%M", time.localtime(self.kitas_fj))
            self.fj_kitas.configure(text=T("Kitas šou: {kada} (po {min} min)").format(kada=kada, min=max(0, int(iki // 60))))
        else:
            self.fj_kitas.configure(text=T("Išjungta"))

    def fejerverku_mygtukas(self):
        if self.fj.aktyvus:
            self.papildomos += self.fj.sustabdyti()
            ZURNALAS.rasyti("ĮVYKIS: fejerverkai sustabdyti ranka")
        else:
            self.fejerverkai_dabar()
        try:
            self.atnaujinti_fejerverku_valdiklius()
        except tk.TclError:
            pass

    def fejerverkai_dabar(self):
        if not self.rodoma:
            messagebox.showinfo(PAVADINIMAS, T("Fejerverkai rodomi tik tada, kai sniegas matomas."))
            return
        self.papildomos += self.fj.sustabdyti()
        self.paleisti_fejerverkus()

    def fejerverku_perziuros_zingsnis(self):
        fj = self.fj_perziura
        fj.zingsnis(0.05)
        self.fj_perziuros_laikas += 0.05
        if not fj.grupes and self.fj_perziuros_laikas > 0.4 or self.fj_perziuros_laikas > 14:
            fj.sustabdyti()
            self.fj_perziuros_nr = (self.fj_perziuros_nr + 1) % len(Fejerverkai.VISI)
            self.fj_perziuros_laikas = 0.0
            xv, ya = pp("fejerverkai") // 2, PERZ_DIDELE[1] - 4
            fj.paleisti_viena(self.fj_perziuros_nr, xv, ya, xv, self.fj_perziuros_aukstis(self.fj_perziuros_nr))
            self.fj_pavadinimas = (f"{self.fj_perziuros_nr + 1}/{len(Fejerverkai.VISI)}: "
                                   f"{T(Fejerverkai.VISI[self.fj_perziuros_nr][0])}")

    def fj_perziuros_aukstis(self, nr):
        """Sprogimo aukštis peržiūroje. Rūšys skirtingo dydžio, todėl su ta pačia atsitiktine seka iš anksto
        „sugrojama“ (~5 ms) ir parenkama, kad aukščiausia kibirkštis būtų 2–12 px nuo viršaus. Kitas aukštis
        pakeičia ir atsitiktinumus (raketa skrenda kitą laiką), todėl bandoma kelis kartus ir imamas
        geriausias iš tikrai sugrotų."""
        busena = self.fj_perziura.rnd.getstate()

        def virsus(yt):
            bandomas = Fejerverkai(0.42, 2, rnd=random.Random())
            bandomas.rnd.setstate(busena)
            bandomas.paleisti_viena(nr, pp("fejerverkai") // 2, PERZ_DIDELE[1] - 4, pp("fejerverkai") // 2, yt)
            v, t = None, 0.0
            while bandomas.grupes and t < 14:
                bandomas.zingsnis(0.05)
                t += 0.05
                for g in bandomas.grupes:
                    for d in g.dalys:
                        y = d.y - bandomas.P * d.dydis / 2
                        if v is None or y < v:
                            v = y
            return v

        yt, geriausias = 58, None
        for _ in range(5):
            v = virsus(yt)
            if v is None:
                return 58
            bauda = abs(v - 6) + (20 if v < 0 else 0)  # nukirpta viršūnė blogiau nei keli tušti taškai
            if geriausias is None or bauda < geriausias[0]:
                geriausias = (bauda, yt)
            if 2 <= v <= 12:
                break
            naujas = max(8, min(80, int(yt - (v - 6))))
            if naujas == yt:
                break
            yt = naujas
        return geriausias[1]

    def piesti_fejerverku_perziura(self):
        fj, c = self.fj_perziura, self.fj_drobe
        c.delete("all")
        for g in fj.grupes:
            fj.piesti_grupe(g, lambda x, y, d, spalva: c.create_rectangle(x, y, x + d, y + d, fill=spalva,
                                                                           outline=""), rnd=self.fj_piesimo_rnd)
        # apačioje kairėje – ten tik raketos pėdsakas viduryje, kibirkštys retai nusileidžia taip žemai
        c.create_text(4, PERZ_DIDELE[1] - 3, text=self.fj_pavadinimas, fill="#9fb3c8", anchor="sw",
                      font=("Segoe UI", 8))

    def animuoti_fejerverku_perziura(self, karta):
        if karta != self.sasajos_karta:  # sąsaja perkurta – šį ciklą pakeitė naujas
            return
        try:
            if "fejerverkai" in self.uzvesta and self.root.state() not in ("iconic", "withdrawn"):
                self.fejerverku_perziuros_zingsnis()
                self.piesti_fejerverku_perziura()
        except tk.TclError:
            return
        self.root.after(50, self.animuoti_fejerverku_perziura, karta)

    def animuoti_uzvedus(self, drobe, vardas, isejus=None):
        """Peržiūra animuojama tik kol virš jos pelė – kitaip nustatymų lange viskas nuolat juda."""
        def uzvesta(_):
            self.uzvesta.add(vardas)

        def nuvesta(_):
            self.uzvesta.discard(vardas)
            if isejus:
                isejus()

        drobe.bind("<Enter>", uzvesta)
        drobe.bind("<Leave>", nuvesta)

    def kurti_bumbulu_skilti(self, tevas):
        g = self.skilties_remas(tevas, "Bumbuliukai", "bumbulai")
        g.pack(fill="x")
        self.bumbulu_drobe = tk.Canvas(g, width=pp("bumbulai"), height=PERZ_MAZA[1], bg=DANGUS, highlightthickness=0)
        self.animuoti_uzvedus(self.bumbulu_drobe, "bumbulai", lambda: self.atstatyti_bumbulu_perziura())
        self.bumbulu_drobe.grid(row=0, column=0, columnspan=2, pady=(0, 6))
        self.zymimasis(g, "bumbulu_juda", "Rieda ir pašokinėja (išjungus – tiesiog stovi)", 2)
        self.zymimasis(g, "bumbulai_languose", "Rieda ir ant langų (nuo jų nurieda ir nukrenta)", 3)
        self.papildomi_aprasai["bumbulai_languose"] = lambda: None if kaupia(self.n, "kaupti_languose") else T(
            "⚠ Reikia įjungti „Kaupti ant langų viršaus“ (skiltyje „Sniego kaupimasis“).")
        self.tipu_varneles = {"bumbulu_rastai": [], "bumbulu_spalvos": [], "bumbulu_dingimai": []}
        # „Kartais pradingsta…“ – varnelė rėmelio antraštėje, po ja – kaip pradingsta (eilute žemiau nei buvo)
        dg = ttk.LabelFrame(g, padding=(4, 2))
        dg.grid(row=4, column=0, columnspan=2, sticky="we", padx=4, pady=(2, 4))
        v = self.kint["bumbulu_dingsta"] = tk.BooleanVar(value=self.n["bumbulu_dingsta"])
        cb = self.valdikliai["bumbulu_dingsta"] = ttk.Checkbutton(
            dg, text=T("Kartais pradingsta ir atsiranda kitur"), variable=v,
            command=lambda: self.pakeista("bumbulu_dingsta"))
        dg.configure(labelwidget=cb)
        self.patarimas_nustatymui(cb, "bumbulu_dingsta")
        for i, pavadinimas in enumerate(BUMBULU_DINGIMU_PAVADINIMAI):
            v = tk.BooleanVar(value=bool(self.n["bumbulu_dingimai"][i]))
            self.tipu_varneles["bumbulu_dingimai"].append(v)
            cb = ttk.Checkbutton(dg, text=T(pavadinimas), variable=v, command=lambda: self.pakeisti_dingimus())
            cb.grid(row=i // 2, column=i % 2, sticky="w", padx=(0, 12))
            Patarimas(cb, lambda v=v: (T("⚠ Bent vienas pradingimo būdas turi likti (norint, kad nepradingtų – nuimkite "
                                         "varnelę viršuje).") + "\n\n" if v.get() and sum(
                x.get() for x in self.tipu_varneles["bumbulu_dingimai"]) == 1 else "") + T(
                "Vienas iš būdų, kaip bumbuliukas pradingsta (ir atitinkamai atsiranda). Parenkamas atsitiktinai iš "
                "pažymėtų."))
            self.valdikliu_grupes.setdefault("bumbulu_dingimai", []).append(cb)
        self.slankiklis(g, "bumbulu_kiekis", "Kiek bumbuliukų", 6)
        self.slankiklis(g, "bumbulu_dydis", "Dydis, %", 7)
        self.slankiklis(g, "bumbulu_greitis", "Judrumas, %", 8)

        # Raštai (2 eilės po 6) ir spalvos (1 eilė) – viename rėmelyje; paveikslėliai patys yra jungikliai
        # (be varnelių po jais – kad skiltis nebūtų aukšta). Rašto pavadinimas – antraštėje užvedus pelę.
        r = ttk.LabelFrame(g, text=T("Raštai ir spalvos"), padding=(4, 2))
        r.grid(row=9, column=0, columnspan=2, sticky="we", padx=4, pady=(6, 0))
        for i, pavadinimas in enumerate(BUMBULU_RASTU_PAVADINIMAI):
            self.tipo_varnele(r, "bumbulu_rastai", i, 36,
                              bumbulo_tinklelis(6, (i + 3) % len(BUMBULU_SPALVOS), BUMBULU_RASTAI[i], 0),
                              pavadinimas, r).grid(row=i // 6, column=i % 6, padx=1, pady=1)
        sp = ttk.Frame(r)
        sp.grid(row=2, column=0, columnspan=6, sticky="w", pady=(3, 1))
        for i, pavadinimas in enumerate(BUMBULU_SPALVU_PAVADINIMAI):
            self.tipo_varnele(sp, "bumbulu_spalvos", i, 28, bumbulo_tinklelis(4, i, "vienspalvis", 0),
                              pavadinimas, r).grid(row=0, column=i, padx=1)

        # peržiūros dešiniajame viršutiniame kampe (ten tik dangus) – ne atskira eilutė po skiltimi
        mygtukas = ttk.Button(g, text=T("Išbarstyti iš naujo"), command=self.kurti_bumbulus)
        mygtukas.place(in_=self.bumbulu_drobe, relx=1.0, x=-4, y=4, anchor="ne")
        self.valdikliu_grupes["bumbulu_mygtukas"] = [mygtukas]
        self.kurti_bumbulu_perziura()
        self.atnaujinti_bumbulu_valdiklius()

    def atnaujinti_bumbulu_valdiklius(self):
        """Išjungus funkciją jos nustatymai papilkėja (ne paslepiami – kad langas nešokinėtų).
        Eglutėms ir fejerverkams tai daro atskiri metodai."""
        n = self.n
        bumb, juda = n["bumbulai"], n["bumbulai"] and n["bumbulu_juda"]
        taisykles = {
            "max_aukstis": kaupia(n, "kaupti_apacioje"),
            "max_aukstis_languose": kaupia(n, "kaupti_languose"),
            "kaupimo_greitis": kaupia(n, "kaupti_apacioje") or kaupia(n, "kaupti_languose"),
            "girliandu_kiekis": n["girliandos"], "girliandu_dydis": n["girliandos"],
            "girliandu_mirksejimas": n["girliandos"], "girliandu_atspindziai": n["girliandos"],
            "ekskavatoriu_kiekis": n["ekskavatoriai"], "ekskavatoriu_dydis": n["ekskavatoriai"],
            "bumbulu_juda": bumb, "bumbulai_languose": bumb and kaupia(n, "kaupti_languose"), "bumbulu_dingsta": bumb,
            "bumbulu_kiekis": bumb, "bumbulu_dydis": bumb, "bumbulu_greitis": juda,
            "gusis_dabar": n["gusio_stiprumas"] > 0,
            "sniegas_ant_senio": n["senio_stovi"],  # prisninga tik stovinčiam
        }
        grupes = {"bumbulu_dingimai": bumb and n["bumbulu_dingsta"], "bumbulu_rastai": bumb,
                  "bumbulu_spalvos": bumb, "bumbulu_mygtukas": bumb}
        for raktas, ijungta in taisykles.items():
            w = self.valdikliai.get(raktas)
            if w is not None:
                self.valdiklio_busena(w, ijungta)
        for vardas, ijungta in grupes.items():
            for w in self.valdikliu_grupes.get(vardas, ()):
                self.valdiklio_busena(w, ijungta)

    def tipo_varnele(self, tevas, raktas, i, dydis, tinklas, pavadinimas, remelis_antraste):
        """Paveikslėlis-jungiklis: spustelėjus (arba Tab + Tarpas) raštas / spalva įjungiama arba išjungiama.
        Užvedus pelę – pavadinimas rėmelio antraštėje ir patarimas su būsena. Grąžina drobę."""
        v = tk.BooleanVar(value=bool(self.n[raktas][i]))
        self.tipu_varneles[raktas].append(v)
        fonas, remelis = SKILCIU_SPALVOS.get("Bumbuliukai", ("#f0f0f0", "#444444"))
        drobe = tk.Canvas(tevas, width=dydis, height=dydis, highlightthickness=2, cursor="hand2", takefocus=1)
        jungiklis = PaveikslelioJungiklis(drobe, v, tinklas, fonas, remelis)
        self.valdikliu_grupes.setdefault(raktas, []).append(jungiklis)
        rastas = raktas == "bumbulu_rastai"
        rusis = T("Raštas" if rastas else "Spalva")

        def vienintelis():
            return v.get() and sum(x.get() for x in self.tipu_varneles[raktas]) == 1

        def perjungti(e=None):
            if jungiklis.aktyvus and vienintelis():  # nuėmus visus bumbuliukų nebeliktų
                pat.rodyti(prie_valdiklio=e is not None and e.type == tk.EventType.KeyPress)  # kodėl nieko nevyksta
                return "break"
            if jungiklis.aktyvus:  # išjungus bumbuliukus paveikslėliai nereaguoja
                v.set(not v.get())
                self.pakeisti_tipus(raktas)
                if e is not None and e.type == tk.EventType.KeyPress and pat.langas is not None:
                    pat.rodyti(prie_valdiklio=True)  # klaviatūra – patarimas parodo naują būseną
            return "break"
        drobe.bind("<Button-1>", perjungti)
        drobe.bind("<space>", perjungti)
        drobe.bind("<Return>", perjungti)

        def tik_sis(e=None):  # dešinys spustelėjimas: tik šis vienas; jei jau tik jis – vėl visi
            if jungiklis.aktyvus:
                visi = self.tipu_varneles[raktas]
                vienas = v.get() and sum(x.get() for x in visi) == 1
                for x in visi:
                    x.set(True if vienas else x is v)
                self.pakeisti_tipus(raktas)
            return "break"
        drobe.bind("<Button-3>", tik_sis)

        def patarimas():
            busena = T(("naudojamas" if v.get() else "nenaudojamas") if rastas else
                       ("naudojama" if v.get() else "nenaudojama"))
            uzuomina = T("Tai vienintelis pasirinktas – bent vienas turi likti.") if jungiklis.aktyvus and vienintelis() \
                else T("Spustelėkite (arba Tarpas), kad pakeistumėte. Dešiniuoju – tik šis / vėl visi.") \
                if jungiklis.aktyvus else \
                T("Bumbuliukai išjungti – įjunkite skilties antraštėje.")
            return f"{rusis}: {T(pavadinimas)} – {busena}\n{uzuomina}"
        pat = Patarimas(drobe, patarimas)
        for ivykis in ("<Enter>", "<FocusIn>"):
            drobe.bind(ivykis, lambda e: remelis_antraste.configure(text=f"{rusis}: {T(pavadinimas)}"), add="+")
        for ivykis in ("<Leave>", "<FocusOut>"):
            drobe.bind(ivykis, lambda e: remelis_antraste.configure(text=T("Raštai ir spalvos")), add="+")
        return drobe

    def pakeisti_tipus(self, raktas):
        self.n[raktas] = [int(v.get()) for v in self.tipu_varneles[raktas]]
        self.kurti_bumbulu_perziura()
        self.atideti("bumbulai", 400, self.kurti_bumbulus)
        self.atideti("saugoti", 1000, self.issaugoti)

    def pakeisti_dingimus(self):
        # nauji dingimo būdai taikomi nuo kito karto, perkurti bumbuliukų nereikia
        varneles = self.tipu_varneles["bumbulu_dingimai"]
        if not any(v.get() for v in varneles):  # nuėmus visus programa vis tiek naudotų visus – grąžinama
            for v, buvo in zip(varneles, self.n["bumbulu_dingimai"]):
                if buvo:
                    v.set(True)
            return
        self.n["bumbulu_dingimai"] = [int(v.get()) for v in varneles]
        self.atideti("saugoti", 1000, self.issaugoti)

    # ---- bumbuliukų peržiūra: tos pačios taisyklės kaip ekrane (bumbulo_fizika, bumbulu_zingsnis), tik:
    #  * plokščia žemė, 3 bumbuliukai, be langų ir vėžių sniege;
    #  * pradingimo ciklas suspaustas (rieda 3–8 s, o ne 15–60 s), kad užvedus pelę jį būtų galima pamatyti;
    #  * dydis tikras (kaip ekrane), bet ne didesnis nei 2 taškų „pikselis“ – tada visas pasaulis sumažinamas.

    def perziuros_mastelis(self, dydzio_raktas, daugiklis=1.0, trupmeninis=False, min_P=0):
        """(k, ekrano „pikselis“, peržiūros „pikselis“, f) – peržiūroje tikras dydis, bet ne stambesnis nei 2;
        tada visi greičiai ir atstumai sumažinami f kartų. Bumbuliukams, seniams ir buldozeriukams – vienodai."""
        k = self.k if isinstance(getattr(self, "k", None), (int, float)) else 1.0
        P = self.P if isinstance(getattr(self, "P", None), int) else max(2, int(round(2.4 * k)))
        Pe = max(P, min_P) * daugiklis * self.n[dydzio_raktas] / 100
        Pe = max(1.0, Pe) if trupmeninis else max(1, int(round(Pe)))
        Pp = min(2, max(1, round(Pe))) if trupmeninis else min(2, Pe)  # peržiūroje – sveikas „pikselis“
        return k, Pe, Pp, Pp / Pe

    def bumbulu_perziuros_mastelis(self):
        return self.perziuros_mastelis("bumbulu_dydis")

    def kurti_bumbulu_perziura(self):
        rastai = self.pasirinkti("bumbulu_rastai", len(BUMBULU_RASTAI), visi_jei_nieko=False)
        spalvos = self.pasirinkti("bumbulu_spalvos", len(BUMBULU_SPALVOS), visi_jei_nieko=False)
        k, Pb, Pp, f = self.bumbulu_perziuros_mastelis()
        rnd = random.Random(5)
        self.bumbulu_perziura, self.bumbulu_perz_skeveldros = [], []
        P_ = self.P if isinstance(getattr(self, "P", None), int) else max(2, int(round(2.4 * k)))
        for i in range(3 if rastai and spalvos else 0):
            R = bumbulo_matmenys((6, 5, 7)[i], P_, self.n["bumbulu_dydis"])[1]  # kaip ekrane
            spalva, rastas = spalvos[i % len(spalvos)], BUMBULU_RASTAI[rastai[i % len(rastai)]]
            n = 2 * R + 5
            kadrai = ([bumbulo_tinklelis(R, spalva, rastas, kk) for kk in range(BUMBULU_KADRAI)]
                      + [bumbulo_tinklelis(r, spalva, rastas, 0, n) for r in range(R - 1, 0, -1)]
                      + [blyksnio_tinklelis(n, kk) for kk in range(BUMBULU_BLYKSNIAI)]
                      + [tirpimo_tinklelis(R, spalva, rastas, kk) for kk in range(TIRPIMO_KADRAI)])
            self.bumbulu_perziura.append({
                "R": R, "r": R * Pp, "c": n * Pp / 2, "spalva": spalva, "kadrai": kadrai,
                "x": pp("bumbulai") * (1 + 2 * i) / 6, "y": float(PERZ_ZEME), "v": 0.0, "vy": 0.0, "w": 0.0, "ore": False,
                "v0": rnd.uniform(40, 90) * k * f, "kryptis": rnd.choice((-1, 1)), "kampas": rnd.uniform(0, 6.3),
                "busena": "rieda", "laikas": rnd.uniform(3, 8), "t": 0.0, "trukme": 0.0, "anim": None,
                "stumt": rnd.uniform(0.3, 1.5)})
        self.piesti_bumbulu_perziura()

    def atstatyti_bumbulu_perziura(self):
        """Nuvedus pelę – visi bumbuliukai vėl matomi (kitaip galėtų likti „pradingę“)."""
        for b in self.bumbulu_perziura:
            if b["busena"] != "rieda" or b["ore"]:
                b.update(busena="rieda", ore=False, y=float(PERZ_ZEME), vy=0.0, t=0.0, laikas=random.uniform(3, 8))
        self.bumbulu_perz_skeveldros = []
        self.piesti_bumbulu_perziura()

    def piesti_bumbulu_perziura(self):
        c = self.bumbulu_drobe
        c.delete("all")
        W, H = pp("bumbulai"), PERZ_MAZA[1]
        c.create_rectangle(0, PERZ_ZEME, W, H, fill=SNIEGAS, outline="")
        Pp = self.bumbulu_perziuros_mastelis()[2]
        if not self.bumbulu_perziura:
            c.create_text(W // 2, PERZ_ZEME - 4, fill="#cfd8e3", font=("Segoe UI", 9), anchor="s",
                          text=T("Nėra nė vieno rašto ar spalvos – bumbuliukų nebus"))
        p = DrobesPiesejas(c)
        for b in self.bumbulu_perziura:
            if b["busena"] == "nera":
                continue
            kadras, zemyn, apkirpti = self.bumbulo_vaizdas(b)
            x0 = int(b["x"] - b["c"])
            y0 = int(b["y"] - b["r"] - b["c"] + zemyn) + 1
            piks_piesti(p, b["kadrai"][kadras], x0, y0, Pp)
            if apkirpti:  # įsmenga / išnyra – dalis po sniegu
                c.create_rectangle(x0, int(b["y"]) + 1, x0 + int(2 * b["c"]) + 1, H, fill=SNIEGAS, outline="")
        for sk in self.bumbulu_perz_skeveldros:
            if not (sk["laikas"] < 0.5 and int(sk["laikas"] * 12) % 2 == 0):  # prieš dingdamos pamirksi
                x, y, d = int(sk["x"]), int(sk["y"]), sk["d"]
                c.create_rectangle(x, y - d, x + d, y, fill=sk["spalva"], outline="")
        self.zymeti_bumbulu_sou()

    def animuoti_bumbulu_perziura(self, dt):
        for _ in range(3):  # smulkesni žingsniai – nusileidimai ir susidūrimai tikslesni
            self.bumbulu_perziuros_zingsnis(dt / 3)
        self.piesti_bumbulu_perziura()

    def bumbulu_perziuros_zingsnis(self, dt):
        n = self.n
        k, Pb, Pp, f = self.bumbulu_perziuros_mastelis()
        kf = k * f
        W = pp("bumbulai")
        g = TRAUKA * kf
        juda = n["bumbulu_juda"]
        dingimai = [BUMBULU_DINGIMAI[i] for i in self.pasirinkti("bumbulu_dingimai", 4)]
        # vėjas – tas pats, kuris dabar pučia ekrane (prie žemės silpnesnis)
        vejas = self.vejas * 12 * kf * 0.5 if isinstance(getattr(self, "vejas", None), float) else 0.0
        for b in self.bumbulu_perziura:
            b["laikas"] -= dt
            b["t"] += dt
            if b["busena"] == "rieda" and b["laikas"] <= 0 and n["bumbulu_dingsta"] and not b["ore"]:
                b["anim"] = random.choice(dingimai)
                b["busena"], b["t"] = "nyksta", 0.0
                b["trukme"] = bumbulo_animacijos_trukme(b["anim"], b["R"])
                if b["anim"] == "suduzta":
                    self.bumbulu_perz_sudauzyti(b, kf, Pp)
            elif b["busena"] == "nyksta" and b["t"] >= b["trukme"]:
                b["busena"], b["laikas"] = "nera", random.uniform(0.6, 1.5)
            elif b["busena"] == "nera" and b["laikas"] <= 0:
                kiti = [o["x"] for o in self.bumbulu_perziura if o is not b]
                for _ in range(20):
                    b["x"] = random.uniform(b["r"] + 2, W - b["r"] - 2)
                    if all(abs(x - b["x"]) > 3 * b["r"] for x in kiti):
                        break
                b.update(y=float(PERZ_ZEME), v=0.0, vy=0.0, ore=False, t=0.0)
                b["anim"] = BUMBULU_ATSIRADIMAI[random.choice(dingimai)]
                if b["anim"] == "nukrenta":  # iškrenta iš dangaus ir atšoka
                    b.update(busena="rieda", laikas=random.uniform(3, 8), ore=True,
                             w=random.uniform(-3, 3))
                    b["y"] -= random.uniform(180, 320) * kf
                else:
                    b["busena"] = "atsiranda"
                    b["trukme"] = bumbulo_animacijos_trukme(b["anim"], b["R"])
            elif b["busena"] == "atsiranda" and b["t"] >= b["trukme"]:
                b["busena"], b["laikas"] = "rieda", random.uniform(3, 8)
            if b["busena"] == "nera":
                continue
            r = b["r"]
            if b["ore"]:
                b["vy"] += g * dt
                b["v"] += (vejas - b["v"]) * 0.1 * dt
                b["x"] += b["v"] * dt
                b["y"] += b["vy"] * dt
                b["kampas"] += b["w"] * dt
                if b["x"] < r or b["x"] > W - r:
                    b["x"] = max(r, min(W - r, b["x"]))
                    b["v"] = -b["v"] * 0.5
                if b["vy"] > 0 and b["y"] >= PERZ_ZEME:
                    smugis = b["vy"]
                    b["y"] = float(PERZ_ZEME)
                    if smugis > 90 * kf:  # atšoka (stiklas į sniegą – nedaug)
                        b["vy"] = -smugis * 0.35
                    else:
                        b["ore"], b["vy"] = False, 0.0
                    b["v"] *= 0.85
                continue
            if not (juda and b["busena"] == "rieda"):
                b["v"] = 0.0
                continue
            gylis = (PERZ_MAZA[1] - PERZ_ZEME) / f  # tiek sniego, kiek matosi peržiūroje
            pagreitis = 0.5 * (vejas - b["v"])
            trintis = (0.012 + 0.05 * min(1.0, gylis / (2 * r / f))) * g
            v = b["v"] + pagreitis * dt
            if v:
                v -= math.copysign(min(abs(v), trintis * dt), v)
            b["v"] = v
            N = b["v0"] * n["bumbulu_greitis"] / 100
            b["stumt"] -= dt
            if b["stumt"] <= 0:
                b["stumt"] = random.uniform(1.5, 3.5)
                if abs(v) < 0.5 * N:  # beveik stovi – stumtelėjimas (kartais į kitą pusę)
                    if random.random() < 0.3:
                        b["kryptis"] = -b["kryptis"]
                    b["v"] += b["kryptis"] * N * random.uniform(1.5, 2.5)
                    # vos pajudėjo nuo praeito stumtelėjimo – stipresnis (ekrane – išriedėti iš duobės)
                    if abs(b["x"] - b.get("stovejo_ties", -1e9)) < 2 * r:
                        b["v"] = b["kryptis"] * max(abs(b["v"]), math.sqrt(2 * 0.6 * g * 1.2 * r) * 1.3)
                    b["stovejo_ties"] = b["x"]
            dx = b["v"] * dt
            b["x"] += dx
            b["kampas"] += dx / r
            if b["x"] - r < 0:
                b["x"], b["v"], b["kryptis"] = r, abs(b["v"]) * 0.5, 1
            elif b["x"] + r > W:
                b["x"], b["v"], b["kryptis"] = W - r, -abs(b["v"]) * 0.5, -1
            if random.random() < 0.06 * dt:  # kartais pašoka
                b.update(ore=True, vy=-random.uniform(150, 250) * kf, w=b["v"] / r)
        # susidūrimai – kaip bumbulu_susidurimai
        bs = [b for b in self.bumbulu_perziura if b["busena"] == "rieda"]
        for i in range(len(bs)):
            a = bs[i]
            for c in bs[i + 1:]:
                dx, dy = c["x"] - a["x"], (c["y"] - c["r"]) - (a["y"] - a["r"])
                riba = a["r"] + c["r"]
                atst = math.hypot(dx, dy)
                if atst >= riba or atst == 0:
                    continue
                nx, ny = dx / atst, dy / atst
                sant = (c["v"] - a["v"]) * nx + (c["vy"] - a["vy"]) * ny
                if sant < 0:
                    j = -(1 + 0.8) * sant / 2
                    a["v"] -= j * nx
                    c["v"] += j * nx
                    if a["ore"] or c["ore"]:
                        a["vy"] -= j * ny
                        c["vy"] += j * ny
                    for x_ in (a, c):
                        if abs(x_["v"]) > 2 * kf:
                            x_["kryptis"] = -1 if x_["v"] < 0 else 1
                a["x"] -= nx * (riba - atst) / 2
                c["x"] += nx * (riba - atst) / 2
        # šukės – kaip skeveldru_zingsnis
        likusios = []
        for sk in self.bumbulu_perz_skeveldros:
            sk["laikas"] -= dt
            if not sk["nusileido"]:
                sk["vy"] += g * dt
                sk["x"] += sk["vx"] * dt
                sk["y"] += sk["vy"] * dt
                if sk["y"] >= PERZ_ZEME and sk["vy"] > 0:
                    sk["y"], sk["nusileido"] = float(PERZ_ZEME), True
            if sk["laikas"] > 0 and 0 <= sk["x"] < W:
                likusios.append(sk)
        self.bumbulu_perz_skeveldros = likusios

    def bumbulu_perz_sudauzyti(self, b, kf, Pp):
        pagr, tamsi, sviesi = BUMBULU_SPALVOS[b["spalva"]]
        spalvos = (pagr, pagr, tamsi, sviesi, "#f2c94c", "#ffffff")
        cx, cy = b["x"], b["y"] - b["r"]
        for _ in range(random.randint(12, 18)):
            a = random.uniform(0, 2 * math.pi)
            greitis = random.uniform(60, 200) * kf
            self.bumbulu_perz_skeveldros.append({
                "x": cx + math.cos(a) * b["r"] * 0.6, "y": cy + math.sin(a) * b["r"] * 0.6,
                "vx": math.cos(a) * greitis, "vy": math.sin(a) * greitis - random.uniform(100, 220) * kf,
                "spalva": random.choice(spalvos), "d": Pp * random.choice((1, 1, 2)),
                "laikas": random.uniform(1.5, 2.5), "nusileido": False})

    def kurti_egliu_skilti(self, tevas):
        g = self.skilties_remas(tevas, "Eglutės", "egles")
        g.pack(fill="x")
        self.egliu_drobe = tk.Canvas(g, width=pp("egles"), height=PERZ_MAZA[1], bg=DANGUS, highlightthickness=0)
        # nuvedus pelę lemputės vėl visos dega
        self.animuoti_uzvedus(self.egliu_drobe, "egles", lambda: self.piesti_egliu_perziura(perkurti=False))
        self.egliu_drobe.bind("<Button-1>", self.paspausta_egle)
        self.velykiu_paspaudimai = []
        self.egliu_drobe.grid(row=0, column=0, columnspan=2, pady=(0, 6))
        self.slankiklis(g, "egliu_kiekis", "Kiek eglučių", 2)
        v = tk.BooleanVar(value=self.n["egliu_atsitiktinis"])
        self.kint["egliu_atsitiktinis"] = v
        rb = ttk.Radiobutton(g, text=T("Vienodo aukščio"), variable=v, value=False,
                             command=lambda: self.pakeista("egliu_atsitiktinis"))
        rb.grid(row=3, column=0, sticky="w", padx=4)
        self.patarimas_nustatymui(rb, "egliu_atsitiktinis")
        self.slankiklis(g, "egliu_aukstis", "   Aukštis, px", 4)
        rb = ttk.Radiobutton(g, text=T("Atsitiktinio aukščio"), variable=v, value=True,
                             command=lambda: self.pakeista("egliu_atsitiktinis"))
        rb.grid(row=5, column=0, sticky="w", padx=4)
        self.patarimas_nustatymui(rb, "egliu_atsitiktinis")
        self.slankiklis(g, "egliu_min", "   Mažiausias, px", 6)
        self.slankiklis(g, "egliu_max", "   Didžiausias, px", 7)
        ttk.Label(g, text=T("Eglių plotis")).grid(row=8, column=0, sticky="w", padx=4, pady=1)
        v = self.kint["egliu_plotis_min"] = tk.IntVar(value=egliu_plocio_zingsnis(self.n["egliu_plotis_min"]))
        plociai = ttk.Frame(g)
        plociai.grid(row=8, column=1, sticky="w", padx=4, pady=1)
        for reiksme, tekstas in zip(EGLIU_PLOCIAI, ("Įvairus", "Be siaurų", "Vienodas")):
            rb = ttk.Radiobutton(plociai, text=T(tekstas), value=reiksme, variable=v,
                                 command=lambda: self.pakeista("egliu_plotis_min"))
            rb.pack(side="left", padx=(0, 8))
            Patarimas(rb, T("Siauros, vidutinės ir plačios eglės (siauriausios – {p} % įprasto pločio).").format(p=reiksme)
                      if reiksme == EGLIU_PLOCIAI[0] else
                      T("Vidutinės ir plačios eglės (siauriausios – {p} % įprasto pločio).").format(p=reiksme)
                      if reiksme < 100 else T("Visos eglės – įprasto pločio."))
        puosimas = ttk.LabelFrame(g, text=T("Papuošimai"), padding=(4, 2))
        puosimas.grid(row=9, column=0, columnspan=2, sticky="we", padx=4, pady=(6, 0))
        for i, (raktas, tekstas) in enumerate((("egliu_lemputes", "Lemputės"), ("egliu_mirksi", "Lemputės mirksi"),
                                               ("egliu_burbuliukai", "Burbuliukai"), ("sniegas_ant_egliu", "Sniegas ant šakų"))):
            v = tk.BooleanVar(value=self.n[raktas])
            self.kint[raktas] = v
            cb = ttk.Checkbutton(puosimas, text=T(tekstas), variable=v, command=lambda k=raktas: self.pakeista(k))
            cb.grid(row=i // 2, column=i % 2, sticky="w", padx=(0, 12), pady=1)
            self.valdikliai[raktas] = cb
            self.patarimas_nustatymui(cb, raktas)
        ttk.Button(g, text=T("Išdėlioti iš naujo"), command=lambda: self.perdelioti_egles(nauja_sekla=True)).grid(
            row=10, column=0, columnspan=2, sticky="w", padx=4, pady=(6, 0))
        self.piesti_egliu_perziura()
        self.root.after(90, self.animuoti_perziura, self.sasajos_karta)

    def kurti_senio_skilti(self, tevas):
        g = self.skilties_remas(tevas, "Sniego senis", "sniego_senis")
        g.pack(fill="x")
        self.senio_drobe = tk.Canvas(g, width=pp("seniai"), height=PERZ_MAZA[1], bg=DANGUS, highlightthickness=0,
                                     cursor="hand2")
        self.animuoti_uzvedus(self.senio_drobe, "senis")
        self.senio_drobe.grid(row=0, column=0, columnspan=2, pady=(0, 2))
        self.slankiklis(g, "senio_kiekis", "Kiek sniego senių", 2)
        self.slankiklis(g, "senio_dydis", "Dydis, %", 3)
        self.zymimasis(g, "senio_stovi", "Tik stovi vietoje (pajudina rankas, pasuka galvą)", 4)
        self.zymimasis(g, "sniegas_ant_senio", "Stovinčiam prisninga ant galvos ir šluotos", 5)
        self.papildomi_aprasai["sniegas_ant_senio"] = lambda: None if self.n["senio_stovi"] else T(
            "⚠ Veikia tik kai įjungta „Tik stovi vietoje“.")
        # varnelė ir animacija – vienoje eilutėje: „☑ Lemputės ant šluotos [Mirksi ▾]“
        self.zymimasis(g, "senio_lemputes", "Lemputės ant šluotos", 6, ilgis=1)
        v = tk.StringVar(value=self.n["senio_lempuciu_animacija"])
        self.kint["senio_lempuciu_animacija"] = v
        kb = ttk.Combobox(g, values=[T(t) for t in SENIO_LEMPUCIU_TEKSTAI], state="readonly", width=26)
        kb.set(T(SENIO_LEMPUCIU_TEKSTAI[SENIO_LEMPUCIU_ANIMACIJOS.index(self.n["senio_lempuciu_animacija"])]))
        kb.grid(row=6, column=1, sticky="w", padx=4, pady=1)
        self.senio_lempuciu_kb = kb
        self.valdikliai["senio_lempuciu_animacija"] = kb
        self.patarimas_nustatymui(kb, "senio_lempuciu_animacija")

        def pasirinkta(_):
            v.set(SENIO_LEMPUCIU_ANIMACIJOS[kb.current()])
            self.pakeista("senio_lempuciu_animacija")
            self.piesti_senio_perziura()
        kb.bind("<<ComboboxSelected>>", pasirinkta)
        # peržiūroje seniuką irgi galima pačiupti ir numesti
        self.senio_perziura = {"x": pp("seniai") * 0.3, "y": float(PERZ_ZEME), "kryptis": 1, "faze": 0.0,
                               "busena": "eina", "t": 0.0, "iki_pauzes": 2.0, "vy": 0.0, "vx": 0.0, "daleles": [],
                               "puosmena": random.choice(SENIO_PUOSMENOS[:-1])}  # peržiūroje – su papuošimu
        c = self.senio_drobe
        c.bind("<ButtonPress-1>", self.senio_perz_paimtas)
        c.bind("<B1-Motion>", self.senio_perz_tempiamas)
        c.bind("<ButtonRelease-1>", self.senio_perz_paleistas)
        self.piesti_senio_perziura()

    def senio_perziuros_mastelis(self):
        return self.perziuros_mastelis("senio_dydis", SENIO_MASTELIS, trupmeninis=True, min_P=SENIO_MIN_P)

    def animuoti_senio_perziura(self, dt):
        """Ta pati elgsena kaip ekrane (seniu_zingsnis): slysta, kartais sustoja ir apsisuka; pagautas kabo,
        paleistas krenta ir susispaudžia. Vienas paviršius – peržiūros žemė."""
        p = self.senio_perziura
        k, Ps, Pp, f = self.senio_perziuros_mastelis()
        W = pp("seniai")
        pus = SENIO_W * Pp * 0.32
        p["t"] += dt
        b = p["busena"]
        # sniegas ant senio – kaip ekrane, tik prisninga per ~5 s (kad užvedus pelę būtų matyti)
        p["sniegas"] = (min(1.0, p.get("sniegas", 0.0) + dt / 5)
                        if b in SENIO_SNIEGUOJA and self.n["senio_stovi"] else 0.0)
        if b == "kabo":
            senio_svyruoti(p, dt, Pp, k * f)
        elif b == "krenta":  # kaip ekrane (senio_kristi): oro pasipriešinimas, nuo krašto atsimuša
            p["vy"] += TRAUKA * k * f * dt
            p["y"] += p["vy"] * dt
            p["x"] += p["vx"] * dt
            p["vx"] *= max(0.0, 1 - dt * 0.6)
            if not pus <= p["x"] <= W - pus:
                p["x"], p["vx"] = max(pus, min(W - pus, p["x"])), -p["vx"] * 0.4
            senio_svyruoti(p, dt, Pp, k * f)
            if p["y"] >= PERZ_ZEME:
                p.update(y=float(PERZ_ZEME), busena="nukrenta", t=0.0, vy=0.0, vx=0.0)
        elif b in ("nukrenta", "mojuoja", "rankos", "dairosi"):
            if p["t"] >= (0.3 if b == "nukrenta" else senio_trumpo_veiksmo_trukme(p)):
                self.senio_perz_toliau(p)
        elif b == "stovi":
            if p["t"] >= p["stoveti"]:
                if self.n["senio_stovi"]:
                    senio_stovint(p, (1.5, 4))
                else:
                    if random.random() < 0.45:
                        p["kryptis"] = -p["kryptis"]
                    p.update(busena="eina", t=0.0, iki_pauzes=random.uniform(3, 6))  # peržiūroje – dažniau
        elif b in ("meta", "sauna"):  # ta pati eiga kaip ekrane (senio_veiksmo_eiga)
            if senio_veiksmo_eiga(p, lambda langelis: self.senio_ranka(p, Pp, langelis), k * f, W, PERZ_MAZA[1],
                                  p["daleles"], 30):
                self.senio_perz_toliau(p)
        elif self.n["senio_stovi"]:
            p.update(busena="stovi", t=0.0, stoveti=random.uniform(1, 3))
        else:
            p["x"] += p["kryptis"] * 24 * k * f * dt
            p["faze"] += dt / 0.7
            if p["x"] - pus < 0:
                p["x"], p["kryptis"] = pus, 1
            elif p["x"] + pus > W:
                p["x"], p["kryptis"] = W - pus, -1
            p["iki_pauzes"] -= dt
            if p["iki_pauzes"] <= 0:
                b = senio_pauze()
                p.update(busena=b, t=0.0, stoveti=random.uniform(1.0, 3.0), suviai=0)
                if b == "dairosi":
                    senio_dairytis(p)
        p["daleles"], _ = senio_daleliu_zingsnis(p["daleles"], dt, k * f, lambda x, y: float(PERZ_ZEME))
        self.piesti_senio_perziura()

    def senio_perz_toliau(self, p):
        if self.n["senio_stovi"]:
            p.update(busena="stovi", t=0.0, stoveti=random.uniform(1.5, 4))
        else:
            p.update(busena="eina", t=0.0, iki_pauzes=random.uniform(3, 6))

    def piesti_senio_perziura(self):
        c, p = self.senio_drobe, self.senio_perziura
        Pp = self.senio_perziuros_mastelis()[2]
        c.delete("all")
        c.create_rectangle(0, PERZ_ZEME, pp("seniai"), PERZ_MAZA[1], fill=SNIEGAS, outline="")
        nr = self.senio_kadras(p)
        n = len(SENIO_KADRAI)
        poza, kadras = SENIO_KADRAI[nr % n]
        # patarimas – toje pusėje, kur seniuko nėra
        kaireje = p["x"] > pp("seniai") / 2
        c.create_text(4 if kaireje else pp("seniai") - 4, 3, text=T("Pačiupk už šaliko!"),
                      anchor="nw" if kaireje else "ne", fill="#cfd8e3", font=("Segoe UI", 8))
        x0, y0 = int(p["x"] - SENIO_W * Pp / 2), int(p["y"]) - SENIO_H * Pp + 1
        piks_piesti(DrobesPiesejas(c), senio_tinklelis(poza, kadras, nr >= n, 0, senio_tuta(p), self.senio_puosmena(p)),
                    x0, y0, Pp)
        lygis = p.get("sniegas", 0.0) * SENIO_SNIEGO_DALIS if self.n["sniegas_ant_senio"] else 0.0
        for x, y, slenkstis in senio_sniego_langeliai(poza, kadras, nr >= n, self.senio_puosmena(p)) if lygis else ():
            if slenkstis >= lygis:
                break
            c.create_rectangle(x0 + x * Pp, y0 + y * Pp, x0 + (x + 1) * Pp, y0 + (y + 1) * Pp, fill=SNIEGAS, outline="")
        if self.n["senio_lemputes"]:
            lemp = senio_sluotos_lemputes(poza, kadras, nr >= n)
            laikas, anim = time.perf_counter(), self.n["senio_lempuciu_animacija"]
            for x, y, j in lemp:
                sp = senio_lemputes_spalva(j, 0, senio_lemputes_sviesumas(anim, laikas, j, len(lemp)))
                c.create_rectangle(x0 + x * Pp, y0 + y * Pp, x0 + (x + 1) * Pp, y0 + (y + 1) * Pp, fill=sp, outline="")
        for d in p.get("daleles", ()):
            x, y = int(d["x"]), int(d["y"])
            if d["tipas"] == "gniuzte":
                c.create_rectangle(x - 3, y - 3, x + 3, y + 3, fill=SNIEGAS, outline=SENIO_SPALVOS["g"])
            elif not (d["guli"] and d["gyv"] < 0.6 and int(d["gyv"] * 12) % 2 == 0):
                w_, h_ = (2 * Pp, Pp) if (int(math.sin(d["faze"]) * 2) != 0 or d["guli"]) else (Pp, 2 * Pp)
                c.create_rectangle(x, y - h_, x + w_, y, fill=d["spalva"], outline="")

    def senio_perz_griebimo_sritis(self):
        p, Pp = self.senio_perziura, self.senio_perziuros_mastelis()[2]
        gx, gy, gw, gh = self.SENIO_GRIEBIMAS
        x0 = int(p["x"] - SENIO_W * Pp / 2) + gx * Pp
        y0 = int(p["y"]) - SENIO_H * Pp + 1 + gy * Pp
        return x0 - 3, y0 - 3, x0 + gw * Pp + 3, y0 + gh * Pp + 3  # peržiūroje – kiek didesnė (senis mažas)

    def senio_perz_paimtas(self, e):
        if "disabled" in self.valdikliai["senio_kiekis"].state():
            return
        l, t, r, b = self.senio_perz_griebimo_sritis()
        p = self.senio_perziura
        if l <= e.x <= r and t <= e.y <= b:
            p.update(busena="kabo", t=0.0, tempiamas=(p["x"] - e.x, p["y"] - e.y), ist=[(time.perf_counter(), e.x, e.y)],
                     sv_x=None)

    def senio_perz_tempiamas(self, e):
        p = self.senio_perziura
        if p.get("tempiamas"):
            dx, dy = p["tempiamas"]
            p["x"] = max(0.0, min(float(pp("seniai")), e.x + dx))
            p["y"] = min(float(PERZ_ZEME), e.y + dy)
            p["ist"] = (p["ist"] + [(time.perf_counter(), e.x, e.y)])[-6:]
            self.piesti_senio_perziura()

    def senio_perz_paleistas(self, e):
        p = self.senio_perziura
        if p.get("tempiamas"):
            ist = p["ist"]
            vx = (ist[-1][1] - ist[0][1]) / max(0.02, ist[-1][0] - ist[0][0]) if len(ist) > 1 else 0.0
            p.update(tempiamas=None, busena="krenta", vy=0.0, vx=max(-300.0, min(300.0, vx)), t=0.0)

    def kurti_ekskavatoriu_skilti(self, tevas):
        g = self.skilties_remas(tevas, "Buldozeriukai", "ekskavatoriai")
        g.pack(fill="x")
        self.ekskav_drobe = tk.Canvas(g, width=pp("ekskavatoriai"), height=PERZ_MAZA[1], bg=DANGUS, highlightthickness=0)
        self.animuoti_uzvedus(self.ekskav_drobe, "ekskavatoriai")
        self.ekskav_drobe.grid(row=0, column=0, columnspan=2, pady=(0, 6))
        self.slankiklis(g, "ekskavatoriu_kiekis", "Kiek buldozeriukų", 2)
        self.slankiklis(g, "ekskavatoriu_dydis", "Dydis, %", 3)
        self.ekskav_perziura = {"x": 80.0, "kryptis": 1, "ratai": 0.0,
                                "h": [3.0 + (i % 7) * 0.5 for i in range(pp("ekskavatoriai") // 3)], "daleles": []}
        self.piesti_ekskav_perziura()

    def ekskav_perziuros_mastelis(self):
        """Kaip perziuros_mastelis, bet ekrano langelis – lygiai kaip kurti_ekskavatorius (round(P·1,5)·dydis)."""
        k, _, _, _ = self.perziuros_mastelis("ekskavatoriu_dydis", 1.5, trupmeninis=True)
        P = self.P if isinstance(getattr(self, "P", None), int) else max(2, int(round(2.4 * k)))
        Pe = max(1.0, max(1, int(round(P * 1.5))) * self.n["ekskavatoriu_dydis"] / 100)
        Pp = min(2, max(1, round(Pe)))
        return k, Pe, Pp, Pp / Pe

    def animuoti_ekskav_perziura(self, dt):
        """Peržiūroje – ta pati elgsena kaip ekrane (ekskav_stumti, ekskav_pilti, ekskav_purslai): tas pats
        greitis, kauburio aukštis ir sniego gumulų skrydis. Supaprastinta: vienas buldozeriukas, vis prisninga."""
        p, h = self.ekskav_perziura, self.ekskav_perziura["h"]
        k, Pe, Pp, f = self.ekskav_perziuros_mastelis()
        kf, S, W, zeme = k * f, 3, pp("ekskavatoriai"), PERZ_ZEME
        v = 55 * kf
        H_maks = max(2.0, min(self.n["max_aukstis"] * k, EKSKAV_VERSTUVO_AUKSTIS * Pe * 0.85)) * f
        pus, d = EKSKAV_PLOTIS / 2 * Pp, p["kryptis"]
        p["x"] = max(pus, min(W - pus, p["x"] + d * v * dt))
        p["ratai"] += v * dt
        priekis = p["x"] + d * pus
        if p.get("kryptis_kruvos") != d:
            p["kryptis_kruvos"], p["ilgis"] = d, 0
        krastas = priekis >= W - 0.5 or priekis <= 0.5
        rez = stumti_kauburi(h, d, int((p["x"] - d * pus) // S), int(priekis // S), 0, len(h), p["ilgis"],
                             H_maks, S, krastas, atmintis=p)  # ta pati funkcija kaip ekrane
        p["ilgis"] = rez[0] if rez else 0
        Pd = max(2, int(round(max(2, Pe) * f)))  # gumulo dydis peržiūroje; smulkūs trupiniai – perpus
        if rez and rez[2] > 0 and random.random() < 0.5:  # netelpa prieš verstuvą – purslai (kaip ekrane)
            for _ in range(min(3, 1 + int(rez[2] / (3 * kf)))):
                smulkus = random.random() < 0.5
                p["daleles"].append([priekis + random.uniform(-4, 4) * kf, zeme - H_maks,
                                     random.uniform(-90, 90) * kf * 0.5 * (1.3 if smulkus else 1.0),
                                     -random.uniform(120, 260) * kf * 0.5,
                                     max(1, Pd // 2) if smulkus else random.choice((Pd, max(2, Pd - 1)))])
        if rez and rez[1] > 0.05:  # nustumiama per kraštą – kaip ekrane (ekskav_pilti): ≤ 2 gumulai ir trupiniai
            p["pilti_kaupas"] = p.get("pilti_kaupas", 0.0) + rez[1]
            gabalas = max(1.0, Pd * Pd / S)  # peržiūros mastu (kauburio aukštis – irgi peržiūros px)
            n = min(2, int(p["pilti_kaupas"] // gabalas))
            if n:
                p["pilti_kaupas"] = 0.0
            for i in range(n + random.choice((0, 1, 1, 2))):
                p["daleles"].append([(W if d > 0 else 0.0) + d * random.uniform(0, 5) * kf,
                                     zeme - random.uniform(0, H_maks + 2),
                                     d * random.uniform(12, 80) * kf, -random.uniform(0, 60) * kf,
                                     Pd if i < n else max(1, Pd // 2)])
        if priekis >= W - 0.5 or priekis <= 0.5:
            p["kryptis"] = -d
        for _ in range(3):  # prisninga
            c = random.randrange(len(h))
            h[c] = min(H_maks * 1.2, h[c] + 0.4)
        for dd in p["daleles"]:
            dd[3] += 700 * kf * dt
            if len(dd) > 4 and dd[4] < Pd:  # smulkūs trupiniai – oro pasipriešinimas, kaip ekrane
                dd[2] *= max(0.0, 1 - 1.5 * dt)
                dd[3] = min(dd[3], 260 * kf)
            dd[0] += dd[2] * dt
            dd[1] += dd[3] * dt
        p["daleles"] = [dd for dd in p["daleles"] if dd[1] < PERZ_MAZA[1] + 4 and -5 < dd[0] < W + 5]
        self.piesti_ekskav_perziura()

    def piesti_ekskav_perziura(self):
        c, p = self.ekskav_drobe, self.ekskav_perziura
        k, Pe, Pp, f = self.ekskav_perziuros_mastelis()
        W, H, zeme = pp("ekskavatoriai"), PERZ_MAZA[1], PERZ_ZEME
        c.delete("all")
        c.create_rectangle(0, zeme, W, H, fill=SNIEGAS, outline="")
        # kelias – kaip ekrane (piesti_kelia): baltas, du beveik balti klodai, šlaito šešėlis, kontūras
        h, nh = p["h"], len(p["h"])
        baltas, klodai, seselis = KELIO_SPALVOS
        konturas = SNIEGO_KONTURAS if self.n["sniego_konturas"] else None
        for i, v in enumerate(h):
            if v < 0.5:
                continue
            x, virsus = i * 3, zeme - int(v)
            c.create_rectangle(x, virsus, x + 3, zeme, fill=baltas, outline="")
            if v >= 5 * k * f:
                for dalis, sp in ((0.42, klodai[0]), (0.18, klodai[1])):
                    c.create_rectangle(x, max(virsus, int(zeme - v * dalis)), x + 3, zeme, fill=sp, outline="")
            nuol = h[min(nh - 1, i + 3)] - h[max(0, i - 3)]
            if nuol < -0.6 * k * f:
                gylis = min(v * 0.55, (1.5 + min(8.0, -nuol * 1.2)) * k * f)
                if gylis >= 1:
                    c.create_rectangle(x, virsus, x + 3, virsus + int(gylis) + 1, fill=seselis, outline="")
            if konturas:
                c.create_rectangle(x, virsus, x + 3, virsus + 1, fill=konturas, outline="")
        x0, y0 = int(p["x"] - EKSKAV_PLOTIS / 2 * Pp), zeme - EKSKAV_AUKSTIS * Pp + 1
        piks_piesti(DrobesPiesejas(c), ekskavatoriaus_tinklelis(int(p["ratai"] / (2 * Pp)) % 2, p["kryptis"] < 0, 0),
                    x0, y0, Pp)
        # švyturėlis mirksi kaip ekrane (piesti_svyturely)
        u = (time.perf_counter() / EKSKAV_SVYT_PERIODAS) % 1.0
        cs = EKSKAV_SVYT_STULPELIS if p["kryptis"] >= 0 else EKSKAV_PLOTIS - 1 - EKSKAV_SVYT_STULPELIS
        c.create_rectangle(x0 + cs * Pp, y0, x0 + cs * Pp + Pp, y0 + Pp, outline="",
                           fill=EKSKAV_SVYT_SPALVOS[0 if u < EKSKAV_SVYT_SVIECIA else 1])
        # stiklas – kaip ekrane (piesti_stikla)
        kaire = p["kryptis"] < 0
        sx1, sy1, sx2, sy2 = ekskav_stiklo_vieta(Pp, kaire)
        blyksi = time.perf_counter() % EKSKAV_BLYKSNIO_PERIODAS < 0.12
        for x1, x2, y, spalva in ekskav_stiklo_juostos(sx2 - sx1, sy2 - sy1, blyksi):
            c.create_rectangle(x0 + sx1 + x1, y0 + sy1 + y, x0 + sx1 + x2, y0 + sy1 + y + 1, fill=spalva, outline="")
        d_ = max(2, int(round(max(2, Pe) * f)))
        for x, y, _, _, *dyd in p["daleles"]:
            dd = dyd[0] if dyd else d_
            c.create_rectangle(int(x) - 1, int(y) - dd - 1, int(x) + dd + 1, int(y) + 1, fill=SNIEGO_KONTURAS,
                               outline="")
            c.create_rectangle(int(x), int(y) - dd, int(x) + dd, int(y), fill=SNIEGAS, outline="")

    def piesti_tipu_perziuras(self, laikas=0.0):
        """Snaigių rūšių paveikslėliai. laikas > 0 – sukasi kaip ekrane: pixel art šuoliukais (du piešiniai),
        įprastos – sklandžiai; kiekviena rūšis savu greičiu ir kryptimi."""
        pikseliai = self.n["snaigiu_stilius"] == "pikseliai"
        for i, (drobe, (_, rusis, forma), rastas, spalva) in enumerate(zip(self.tipu_drobes, TIPAI, PIKS_SNAIGES,
                                                                           TIPU_SPALVOS)):
            sukimasis = (28 + 6 * i) * (1 if i % 2 else -1)  # laipsniai per sekundę
            drobe.delete("all")
            if pikseliai:
                if laikas and i in PIKS_SNAIGES_PASUKTOS and \
                        int(laikas * 1.5 * abs(sukimasis) / PIKS_SUKIMO_ZINGSNIS[i]) & 1:
                    rastas = PIKS_SNAIGES_PASUKTOS[i]
                m = 3 if max(len(rastas), len(rastas[0])) * 3 <= IKONA else 2
                piks_piesti(DrobesPiesejas(drobe), piks_tinklelis(rastas, {"W": spalva}),
                            IKONA // 2 - len(rastas[0]) * m // 2, IKONA // 2 - len(rastas) * m // 2, m)
            elif rusis in ("kristalas", "kontura"):
                rr = min(IKONA / 2 - 2.5, forma[0] * 1.6) / (1.1 if rusis == "kontura" else 1.0)
                kampas = -math.pi / 2 + math.radians(sukimasis * laikas)
                pts = [v + IKONA // 2 for v in formos_taskai(rusis, forma, rr, kampas)]
                drobe.create_line(*[v + 1 for v in pts], fill=SNAIGES_SESELIS, width=1)
                drobe.create_line(*pts, fill=spalva, width=1)
            else:
                rr = max(1.5, forma * 1.6)
                c_ = IKONA // 2
                drobe.create_oval(c_ + 1 - rr, c_ + 1 - rr, c_ + 1 + rr, c_ + 1 + rr, fill=SNAIGES_SESELIS,
                                  outline=SNAIGES_SESELIS)
                drobe.create_oval(c_ - rr, c_ - rr, c_ + rr, c_ + rr, fill=spalva, outline=spalva)

    def animuoti_perziura(self, karta):
        # Eglučių lemputės peržiūroje mirksi taip pat kaip ekrane – kiekviena eglė savaip; bumbuliukai rieda,
        # snaigės sukasi (jei įjungta „Snaigės sukasi“).
        if karta != self.sasajos_karta:
            return
        try:
            if self.root.state() not in ("iconic", "withdrawn"):
                if "egles" in self.uzvesta and self.n["egliu_lemputes"] and self.n["egliu_mirksi"] and \
                        mirksejimo_zingsnis(self.perziuros_egles, 0.09):
                    self.piesti_egliu_perziura(perkurti=False)
                if "bumbulai" in self.uzvesta:
                    self.animuoti_bumbulu_perziura(0.09)
                if "snaiges" in self.uzvesta and self.n["snaiges_sukasi"]:
                    self.snaigiu_perziuros_laikas = getattr(self, "snaigiu_perziuros_laikas", 0.0) + 0.09
                    self.piesti_tipu_perziuras(self.snaigiu_perziuros_laikas)
                if "ekskavatoriai" in self.uzvesta:
                    self.animuoti_ekskav_perziura(0.09)
                if "senis" in self.uzvesta or self.senio_perziura.get("tempiamas"):
                    self.animuoti_senio_perziura(0.09)
                if "girliandos" in self.uzvesta and girliandu_zingsnis(
                        [self.girl_perziura], 0.09, self.n["girliandu_mirksejimas"] / 100,
                        self.n["girliandu_atspindziai"]):
                    self.piesti_girl_perziura()
        except tk.TclError:
            return
        self.root.after(90, self.animuoti_perziura, karta)

    def piesti_egliu_perziura(self, perkurti=True):
        c = self.egliu_drobe
        c.delete("all")
        n = self.n
        auksciai = self.egliu_auksciai_ir_vietos((0.0, 0.5, 1.0, 0.75, 0.25))[0]  # kaip ekrane
        pagrindas = PERZ_ZEME
        mastelis = min(1.0, (pagrindas - 8) / max(auksciai))
        c.create_rectangle(0, pagrindas, pp("egles"), PERZ_MAZA[1], fill=SNIEGAS, outline="")
        p = DrobesPiesejas(c)
        if perkurti or not getattr(self, "perziuros_egles", None):
            # pastovus atsitiktinumas – kad burbuliukai peržiūroje nešokinėtų kaskart perpiešiant
            galimi = egliu_sablonai_pagal_ploti(n["egliu_plotis_min"])
            self.perziuros_egles = [sukurti_piks_egle(int(pp("egles") * (1 + 2 * i) / 10), pagrindas, a * mastelis, random.Random(i),
                                                      galimi[(i * 2 + 1) % len(galimi)])
                                    for i, a in enumerate(auksciai)]
        if self.sniegas_isjungtas:  # kaip ekrane: be sniego – ir ant šakų jo nėra
            n = dict(n, sniegas_ant_egliu=False)
        for e in self.perziuros_egles:
            piesti_egle(p, e, n if "egles" in self.uzvesta else dict(n, egliu_mirksi=False))
        if mastelis < 1:
            c.create_text(pp("egles") - 4, 4, text=T("mastelis {p}").format(p=f"{mastelis:.0%}"), fill="#9fb3c8", anchor="ne", font=("Segoe UI", 8))

    def paspausta_egle(self, e):
        """Slaptas didysis šou: 5 kartus greitai spustelėti didžiausią vidurinę eglutę."""
        egles = getattr(self, "perziuros_egles", None)
        if not egles or len(egles) < 3:
            return
        l, t, r, b = egles[2]["ribos"]
        if not (l <= e.x <= r and t <= e.y <= b):
            self.velykiu_paspaudimai = []
            return
        dabar = time.monotonic()
        self.velykiu_paspaudimai = [v for v in self.velykiu_paspaudimai if dabar - v < 3.0] + [dabar]
        if len(self.velykiu_paspaudimai) >= 5:
            self.velykiu_paspaudimai = []
            self.didysis_sou()

    def didysis_sou(self):
        if not self.rodoma:
            messagebox.showinfo(PAVADINIMAS, T("Fejerverkai rodomi tik tada, kai sniegas matomas."))
            return
        self.papildomos += self.fj.sustabdyti()
        self.fj.pradeti_didiji(self.fejerverku_sritys())
        self.atnaujinti_fejerverku_valdiklius()

    def atnaujinti_egliu_valdiklius(self):
        atsitiktinis = self.n["egliu_atsitiktinis"]
        rodyti = self.n["egles"]
        for raktas, ijungta in (("egliu_kiekis", rodyti), ("egliu_plotis_min", rodyti),
                                ("egliu_aukstis", rodyti and not atsitiktinis),
                                ("egliu_min", rodyti and atsitiktinis), ("egliu_max", rodyti and atsitiktinis)):
            w = self.valdikliai.get(raktas)
            if w is not None:
                self.valdiklio_busena(w, ijungta)
        for raktas, ijungta in (("egliu_lemputes", rodyti), ("egliu_mirksi", rodyti and self.n["egliu_lemputes"]),
                                ("egliu_burbuliukai", rodyti), ("sniegas_ant_egliu", rodyti)):
            w = self.valdikliai.get(raktas)
            if w is not None:
                self.valdiklio_busena(w, ijungta)

    def perdelioti_egles(self, nauja_sekla=False):
        if nauja_sekla:
            self.egliu_sekla = random.randrange(1 << 30)
        self.kurti_egles()
        self.pilnas_perpiesimas = True

    def ribu_tikrinimas(self, iki):
        """Laukelyje leidžiama vesti tik skaitmenis ir ne daugiau nei didžiausia reikšmė
        (mažiausia pritaikoma išėjus iš laukelio – kitaip nebūtų galima pradėti rinkti „1“, kai riba 10)."""
        # Vienai ribai – viena Tcl komanda (kitaip kiekvienas sąsajos perkūrimas palieka naujų komandų).
        # isascii(): isdigit() praleistų pvz. „²“, o int() tada mestų klaidą ir Tk išjungtų tikrinimą.
        tikrinimai = self.__dict__.setdefault("_tikrinimai", {})
        if iki not in tikrinimai:
            def tikrinti(naujas):
                return naujas == "" or (naujas.isascii() and naujas.isdigit() and int(naujas) <= iki)
            tikrinimai[iki] = self.root.register(tikrinti)
        return (tikrinimai[iki], "%P")

    def slankiklis(self, tevas, raktas, tekstas, eil, ilgis=1):
        """Skaičiaus laukelis su rodyklėmis (kaip snaigių kiekiai): rodyklės, pelės ratukas, ↑/↓ arba įvedimas.
        Ribos parodomos prie pavadinimo, o daugiau nei leidžiama įvesti neįmanoma. ilgis – kiek tinklelio stulpelių
        užima pavadinimas (kad juostos lygiuotųsi su kitomis to paties tinklelio eilutėmis)."""
        nuo, iki = self.leistinos(raktas)
        etikete = ttk.Label(tevas, text=f"{T(tekstas)} ({nuo}–{iki})")
        etikete.grid(row=eil, column=0, columnspan=ilgis, sticky="w", padx=4, pady=1)
        self.etiketes[raktas] = etikete
        v = tk.StringVar(value=str(self.n[raktas]))
        self.kint[raktas] = v
        v.trace_add("write", lambda *_: self.pakeista(raktas))
        remas, sb = self.skaicius_su_juosta(tevas, v, nuo, iki, lambda: self.n[raktas])
        remas.grid(row=eil, column=ilgis, sticky="w", padx=4, pady=1)
        sb.bind("<FocusOut>", lambda e: v.set(str(self.n[raktas])))  # įvedus per daug – parodo apribotą

        def ratukas(e):
            if "disabled" not in sb.state():
                v.set(str(max(nuo, min(iki, self.n[raktas] + (1 if e.delta > 0 else -1)))))
            return "break"

        sb.bind("<MouseWheel>", ratukas)
        sb.slankiklis.bind("<MouseWheel>", ratukas)
        self.valdikliai[raktas] = sb

        # Dukart spustelėjus pavadinimą – numatytoji reikšmė. Ne laukelyje: ten du greiti paspaudimai
        # ant rodyklių irgi būtų „dvigubas spustelėjimas“.
        def numatytoji(_):
            if "disabled" not in sb.state():
                v.set(str(NUMATYTI[raktas]))
        etikete.bind("<Double-Button-1>", numatytoji)
        # Tas pats patarimas ant pavadinimo, laukelio ir juostos: įspėjimas (jei oranžinis), ką daro, numatytoji
        for w in (etikete, sb, sb.slankiklis):
            Patarimas(w, lambda: self.slankiklio_patarimas(raktas))

    def numatytoji_tekstu(self, raktas):
        v = NUMATYTI[raktas]
        if raktas == "egliu_atsitiktinis":
            return T("Numatytoji reikšmė – „{t}“.").format(t=T("Atsitiktinio aukščio" if v else "Vienodo aukščio"))
        if isinstance(v, bool):
            return T("Numatytoji reikšmė – įjungta." if v else "Numatytoji reikšmė – išjungta.")
        tekstai = {"snaigiu_stilius": (SNAIGIU_STILIAI, ("Pixel art", "Įprastos")),
                   "vejo_kryptis": (VEJO_KRYPTYS, VEJO_KRYPCIU_TEKSTAI),
                   "kryzelis": (KRYZELIO_VEIKSMAI, KRYZELIO_TEKSTAI),
                   "senio_lempuciu_animacija": (SENIO_LEMPUCIU_ANIMACIJOS, SENIO_LEMPUCIU_TEKSTAI)}.get(raktas)
        if tekstai:
            return T("Numatytoji reikšmė – „{t}“.").format(t=T(tekstai[1][tekstai[0].index(v)]))
        if raktas in RIBOS:
            return T("Numatytoji reikšmė – {v}. Dukart spustelėkite pavadinimą, kad ją grąžintumėte.").format(v=v)
        return None

    def patarimas_nustatymui(self, w, raktas):
        """Varnelei, pasirinkimui ar pavadinimui – tas pats patarimas kaip slankikliams."""
        Patarimas(w, lambda: self.slankiklio_patarimas(raktas))

    def slankiklio_patarimas(self, raktas):
        """Įspėjimas (jei yra) → ką daro (APRASAI) → kintanti dalis (papildomi_aprasai) → numatytoji reikšmė."""
        dalys = [self.ispejimas(raktas)]
        aprasas = APRASAI.get(raktas)
        if aprasas:
            dalys.append(" ".join(T(a) for a in ((aprasas,) if isinstance(aprasas, str) else aprasas)))
        papildoma = self.__dict__.get("papildomi_aprasai", {}).get(raktas)
        if papildoma:
            x = papildoma()
            if x and x.startswith("⚠"):  # kodėl neveikia / papilkėjęs – pirmiausia
                dalys.insert(1, x)
            else:
                dalys.append(x)
        dalys.append(self.numatytoji_tekstu(raktas))
        return "\n\n".join(d for d in dalys if d) or None

    def slinkties_stilius(self):
        """Windows (vista) juosta stambi – jos rankenėlė aukštesnė už skaičiaus laukelį, todėl eilutės išsiplečia.
        Juosta sudedama iš „default“ temos elementų (jie yra visose temose): plonas takelis ir maža rankenėlė."""
        st = ttk.Style(self.root)
        if not self.slinkties_stilius_sukurtas:
            self.slinkties_stilius_sukurtas = True
            try:
                for el in ("trough", "slider"):
                    st.element_create(f"Maza.Horizontal.Scale.{el}", "from", "default")
            except tk.TclError:
                pass  # jau sukurti
            st.layout(SLINKTIES_STILIUS, [("Maza.Horizontal.Scale.trough", {"sticky": "nswe", "children": [
                ("Maza.Horizontal.Scale.slider", {"side": "left", "sticky": ""})]})])
            st.configure(SLINKTIES_STILIUS, sliderlength=9, sliderthickness=11, sliderrelief="flat", borderwidth=0,
                         troughcolor="#c6cfdb", troughrelief="flat", background="#2f6fbf")
            st.map(SLINKTIES_STILIUS, background=[("disabled", "#b9c1cb"), ("active", "#1f5aa6")])
        return SLINKTIES_STILIUS

    def skaicius_su_juosta(self, tevas, v, nuo, iki, dabartine, zingsnis=1):
        """Slinkties juosta (greitai nustatyti tempiant) ir šalia – skaičiaus laukelis (tiksliai įvesti).
        Abu rodo tą pačią reikšmę: tempiant juostą keičiasi skaičius, įvedus skaičių – pasislenka juosta.
        Plačiose ribose (pvz. 0–1000, kai įprasta 5–50) juosta kvadratinė: pradžioje smulkesni žingsniai.
        Grąžina (rėmelis, laukelis); juosta – laukelis.slankiklis (kad papilkėtų kartu su laukeliu)."""
        remas = ttk.Frame(tevas)
        plotis = max(1, iki - nuo)
        kv = plotis > 200

        def is_juostos(p):
            return nuo + plotis * (p * p if kv else p)

        def i_juosta(sk):
            d = min(1.0, max(0.0, (sk - nuo) / plotis))
            return math.sqrt(d) if kv else d

        sc = ttk.Scale(remas, from_=0.0, to=1.0, orient="horizontal", length=SLINKTIES_ILGIS,
                       style=self.slinkties_stilius())
        sc.set(i_juosta(float(dabartine())))
        sb = ttk.Spinbox(remas, from_=nuo, to=iki, increment=zingsnis, width=4, textvariable=v, validate="key",
                         validatecommand=self.ribu_tikrinimas(iki))
        sc.pack(side="left")
        sb.pack(side="left", padx=(4, 0))

        def tempiama(p):
            sk = str(int(round(is_juostos(float(p)))))
            if sk != v.get():
                v.set(sk)

        def pasikeite():
            try:
                sk = float(dabartine())
                if abs(is_juostos(float(sc.get())) - sk) >= 0.5:  # juosta – ten, kur tikroji (apribota) reikšmė
                    sc.set(i_juosta(sk))
            except (tk.TclError, ValueError):
                pass
        sc.configure(command=tempiama)
        v.trace_add("write", lambda *_: remas.after_idle(pasikeite))
        sb.slankiklis = sc
        return remas, sb

    def zymimasis(self, tevas, raktas, tekstas, eil, ilgis=2):
        v = tk.BooleanVar(value=self.n[raktas])
        self.kint[raktas] = v
        cb = ttk.Checkbutton(tevas, text=T(tekstas), variable=v, command=lambda k=raktas: self.pakeista(k))
        cb.grid(row=eil, column=0, columnspan=ilgis, sticky="w", padx=4, pady=2)
        self.valdikliai[raktas] = cb
        self.patarimas_nustatymui(cb, raktas)

    def atnaujinti_is_viso(self):
        self.is_viso.configure(text=T("iš {m}").format(m=self.maks_viso()))
        v = self.__dict__.get("is_viso_kint")
        if v is not None and not self.__dict__.get("viso_keiciama"):  # bendro kiekio juosta – pagal rūšis
            try:
                if v.get() != str(sum(self.n["tipai"])):
                    self.viso_sinchronizuojama = True
                    try:
                        v.set(str(sum(self.n["tipai"])))
                    finally:
                        self.viso_sinchronizuojama = False
            except tk.TclError:
                pass

    def numatytas_snaigiu_kiekis(self):
        """Dukart spustelėjus „Iš viso snaigių“ – numatytieji rūšių kiekiai (iš viso 200)."""
        if not self.n["snaiges"]:  # skiltis išjungta (papilkėjusi)
            return
        self.viso_svoriai = None  # kitą kartą patempus juostą – nauja atsitiktinė proporcija
        self.viso_keiciama = True
        try:
            self.nustatyti_snaigiu_kieki(sum(NUMATYTI["tipai"]), svoriai=list(NUMATYTI["tipai"]))
        finally:
            self.viso_keiciama = False
        self.atnaujinti_is_viso()
        self.atnaujinti_paruostukus()
        self.atideti("saugoti", 1000, self.issaugoti)

    def pakeistas_is_viso(self):
        """Bendro kiekio juosta: kiekis atsitiktinai paskirstomas po rūšis. Tempiant – ta pati atsitiktinė
        proporcija (kad snaigės nesikeistų kiekvienu žingsniu); po ≥ 2 s pertraukos – nauja."""
        if getattr(self, "atkuriama", False) or self.__dict__.get("viso_sinchronizuojama"):
            return
        try:
            kiek = max(0, min(self.maks_viso(), int(self.is_viso_kint.get())))
        except (ValueError, tk.TclError):
            return  # laukelis tuščias ar renkamas
        if kiek == sum(self.n["tipai"]):
            return
        dabar = time.monotonic()
        if dabar - self.__dict__.get("viso_laikas", -10.0) > 2.0 or not self.__dict__.get("viso_svoriai"):
            # skirtingos rūšys – nevienodai: kelios gausios, kitų mažai (kvadratas), bet kiekvienos šiek tiek
            self.viso_svoriai = [random.random() ** 2 + 0.03 for _ in TIPAI]
        self.viso_laikas = dabar
        self.viso_keiciama = True
        try:
            self.nustatyti_snaigiu_kieki(kiek, svoriai=self.viso_svoriai)
        finally:
            self.viso_keiciama = False
        self.atnaujinti_paruostukus()
        self.atideti("saugoti", 1000, self.issaugoti)

    def pakeisti_tipai(self):
        if getattr(self, "atkuriama", False):  # „Atkurti numatytuosius“ – reikšmės jau teisingos
            return
        nauji = []
        for i, v in enumerate(self.tipu_kint):
            try:
                nauji.append(max(0, min(self.maks_tipo(), int(v.get()))))
            except ValueError:
                # laukelis tuščias ar renkamas – laikoma esama reikšmė (kiti laukeliai vis tiek veikia)
                nauji.append(self.n["tipai"][i])
        if nauji == self.n["tipai"]:
            return
        if sum(nauji) > self.maks_viso():
            # viršijus bendrą ribą – pakeistas laukelis sumažinamas tiek, kiek dar telpa
            for i, (naujas, senas) in enumerate(zip(nauji, self.n["tipai"])):
                if naujas != senas:
                    nauji[i] = max(0, self.maks_viso() - (sum(nauji) - naujas))
                    self.root.after_idle(lambda v=self.tipu_kint[i], k=nauji[i]: v.set(str(k)))
                    break
            self.is_viso.configure(foreground="#c0392b")
            self.root.after(1500, lambda: self.is_viso.configure(foreground="#666666"))
        self.n["tipai"] = nauji
        self.atnaujinti_is_viso()
        self.atnaujinti_paruostukus()
        self.atideti("kiekis", 250, lambda: self.pritaikyti_kieki(visame_ekrane=False))
        self.atideti("saugoti", 1000, self.issaugoti)

    def pakeista(self, raktas):
        try:
            nauja = type(NUMATYTI[raktas])(self.kint[raktas].get())
        except (tk.TclError, ValueError):
            return  # laukelis tuščias ar dar renkamas
        if raktas in RIBOS:
            nuo, iki = self.leistinos(raktas)
            nauja = max(nuo, min(iki, nauja))
        if nauja == self.n[raktas]:
            return
        self.n[raktas] = nauja
        self.atnaujinti_paruostukus()
        if raktas in SKILCIU_RAKTAI:
            self.atnaujinti_skiltis()  # visa skiltis papilkėja / atsiranda
        elif raktas in ("kaupti_apacioje", "kaupti_languose", "bumbulu_dingsta", "gusio_stiprumas", "gusiai",
                        "senio_stovi"):
            self.atnaujinti_bumbulu_valdiklius()  # priklausomi nustatymai papilkėja / atsiranda
        if raktas in ("vejas", "vejas_ijungtas", "gusio_stiprumas", "girliandos", "girliandu_kiekis", "girliandu_dydis",
                      "egles", "egliu_atsitiktinis", "egliu_min", "egliu_max"):
            self.atnaujinti_ispejimus()
        if raktas in ("egliu_min", "egliu_max"):
            self.paskutine_egliu_riba = raktas
            if self.n["egliu_min"] > self.n["egliu_max"]:
                self.atideti("egliu_ribos", 1200, self.suderinti_egliu_ribas)
        if raktas == "senio_lemputes":
            self.atnaujinti_senio_valdiklius()
            if getattr(self, "senio_drobe", None) is not None:
                self.piesti_senio_perziura()
        if raktas == "snaiges":
            self.pritaikytas_sniegas()
        elif raktas == "kaupimasis" and not nauja:
            self.nuvalyti()  # išjungus – sukauptas sniegas dingsta, kaip ir kiti išjungti efektai
        elif raktas == "kaupti_apacioje" and not nauja:
            self.nuvalyti(tik_zeme=True)  # kitaip apačioje likdavo „sustingusi“ pusnis (ant langų – dingsta pati)
        elif raktas == "vejas_ijungtas":
            self.vejo_laikas = 0.0
        if raktas in VEJO_RAKTAI and getattr(self, "vejo_perz", None):
            self.vejo_perz["kreive"] = None
            self.vejo_perz["pasenusi"] = True
            self.vejo_perz["t"] = min(self.vejo_perz["t"], vejo_kreive(self.n)["T"] * 0.999)
            self.piesti_vejo_perziura(self.vejo_perz["zyma"] == "juda")
        if raktas in ("vejas", "vejo_kryptis"):
            self.vejo_laikas = 0.0  # naujas ramus vėjas parenkamas iškart, o ne po 5–12 s
            if raktas == "vejo_kryptis" and nauja != "kintanti":
                self.vejo_kryptis = 1 if nauja == "desine" else -1
                self.vejo_tikslas = abs(self.vejo_tikslas) * self.vejo_kryptis  # ir vykstantis gūsis apsisuka
        elif raktas == "gusio_stiprumas" and self.gusio_liko > 0:
            self.pradeti_gusi()  # vykstantis gūsis iškart pagal naują stiprumą
        if raktas == "dydis":
            self.atideti("perkurti", 300, lambda: (self.kurti_snaigiu_atlasa(), self.pritaikyti_kieki(perkurti=True)))
        elif raktas == "sniego_konturas":
            self.pilnas_perpiesimas = True
            if getattr(self, "ekskav_drobe", None) is not None:
                self.piesti_ekskav_perziura()  # jos kelias – su kontūru
        elif raktas == "snaigiu_stilius":
            self.kurti_snaigiu_atlasa()
            self.piesti_tipu_perziuras()
        elif raktas in ("egles", "egliu_kiekis", "egliu_atsitiktinis", "egliu_aukstis", "egliu_min", "egliu_max",
                        "egliu_plotis_min"):
            self.atnaujinti_egliu_valdiklius()
            self.piesti_egliu_perziura()
            self.atideti("egles", 300, self.perdelioti_egles)
        elif raktas == "fejerverkai":
            if not nauja:
                self.papildomos += self.fj.sustabdyti()
            self.kitas_fj = self.kitas_fejerverku_laikas(time.time())
            self.atnaujinti_fejerverku_valdiklius()
        elif raktas == "fejerverku_intervalas":
            self.kitas_fj = self.kitas_fejerverku_laikas(time.time())
            self.atnaujinti_fejerverku_valdiklius()
        elif raktas == "bumbulu_juda":
            self.atnaujinti_bumbulu_valdiklius()
        elif raktas in ("bumbulai", "bumbulu_kiekis", "bumbulu_dydis"):
            self.atideti("bumbulai", 300, self.kurti_bumbulus)
            if raktas == "bumbulu_dydis":
                self.kurti_bumbulu_perziura()  # peržiūroje – tikras dydis
        elif raktas in ("egliu_lemputes", "egliu_mirksi", "egliu_burbuliukai", "sniegas_ant_egliu"):
            self.atnaujinti_egliu_valdiklius()
            self.piesti_egliu_perziura()
            self.pilnas_perpiesimas = True
        elif raktas in ("max_aukstis", "max_aukstis_languose"):
            # Atidėta: renkant „100“ pirmas klavišas „1“ (apribotas iki 5) kitaip negrįžtamai nukirptų sniegą.
            # Kopų profilis perskaičiuojamas, nes duobės po eglėmis gylis priklauso nuo didžiausio aukščio.
            self.atideti("ribos", 800, lambda: (self.skaiciuoti_kopas(), self.apriboti_sniega()))
        elif raktas in ("girliandos", "girliandu_dydis", "girliandu_kiekis"):
            self.atideti("girliandos", 300, self.kurti_girliandas)
            if raktas == "girliandu_dydis" and getattr(self, "girl_drobe", None) is not None:
                self.piesti_girl_perziura()
        elif raktas in ("sniego_senis", "senio_kiekis", "senio_dydis"):
            self.atideti("seniai", 300, self.kurti_senius)
            if raktas == "senio_dydis":
                self.piesti_senio_perziura()
        elif raktas in ("senio_stovi", "sniegas_ant_senio"):
            self.piesti_senio_perziura()  # peržiūra – iškart pagal naują nustatymą (ir kai pelė ne ant jos)
        elif raktas in ("ekskavatoriai", "ekskavatoriu_kiekis", "ekskavatoriu_dydis"):
            self.atideti("ekskavatoriai", 300, self.kurti_ekskavatorius)
            if raktas == "ekskavatoriu_dydis":
                self.piesti_ekskav_perziura()  # peržiūroje – tikras dydis
        elif raktas == "diagnostika":
            ZURNALAS.rasyti("diagnostika " + ("įjungta" if nauja else "išjungta"), visada=True)
            ZURNALAS.ijungtas = nauja
            if nauja:
                self.ijungta_diagnostika()
        self.atideti("saugoti", 1000, self.issaugoti)

    def pakeistas_kryzelis(self):
        i = self.kryzelio_kb.current()
        if i < 0:
            return
        self.n["kryzelis"] = KRYZELIO_VEIKSMAI[i]
        self.atideti("saugoti", 1000, self.issaugoti)

    def apriboti_sniega(self):
        """Sumažinus didžiausią aukštį – esamas sniegas nupjaunamas, kad neliktų „užstrigusių“ pikselių."""
        riba = self.n["max_aukstis"] * self.k
        self.aukstis = [min(v, riba * p) for v, p in zip(self.aukstis, self.zemes_profilis)]
        self.kelias = [min(v, riba) for v in self.kelias]
        riba = self.n["max_aukstis_languose"] * self.k
        for st in self.langai.values():
            st["h"][:] = [min(v, riba * p) for v, p in zip(st["h"], st["profilis"])]
        for s_ in self.seniai:  # stovintis senis nusileidžia ant nupjautos pusnies (kitaip liktų kaboti ore)
            s_["y_fiks"] = None
        self.pilnas_perpiesimas = True

    def atkurti_numatytuosius(self):
        if not messagebox.askyesno(PAVADINIMAS, T("Grąžinti visus nustatymus į numatytuosius?")):
            self.atnaujinti_paruostukus()  # mygtukas jau nuspaustas – grąžinama tikroji žymė
            return
        nauji = numatytieji()
        nauji["kalba"] = self.n["kalba"]  # kalba – ne „nustatymas“, kurį norėtųsi atkurti
        self.taikyti_nustatymus(nauji)

    def atkurimo_ikona(self, vardas):
        """↺ ikona (neryški, pilkšva) skilties fone; dydis – pagal antraštės šriftą (didesniame ekrano maste – didesnė)."""
        fonas = SKILCIU_SPALVOS.get(vardas, (None, None))[0]
        if not fonas:
            fonas = ttk.Style(self.root).lookup("TFrame", "background") or "#f0f0f0"
            if not fonas.startswith("#") or len(fonas) != 7:
                fonas = "#%02x%02x%02x" % tuple(c >> 8 for c in self.root.winfo_rgb(fonas))
        sviesumas = sum(int(fonas[i:i + 2], 16) for i in (1, 3, 5)) / (3 * 255)
        pilka = SKILTIES_TAMSI_PILKA if sviesumas < 0.4 else _maisyti(fonas, "#000000", 0.38) if sviesumas < 0.85 \
            else _maisyti(fonas, "#000000", 0.33)
        try:
            from tkinter import font as tkfont
            dydis = max(14, min(32, tkfont.Font(root=self.root, family="Segoe UI", size=9, weight="bold")
                                .metrics("linespace")))
        except tk.TclError:
            dydis = 16
        talpykla = self.__dict__.setdefault("_atkurimo_ikonos", {})
        raktas = (dydis, fonas, pilka)
        if raktas not in talpykla:
            img = tk.PhotoImage(master=self.root, width=dydis, height=dydis)
            img.put(atkurimo_ikonos_pikseliai(dydis, fonas, pilka))
            talpykla[raktas] = img
        return talpykla[raktas]

    def skiltis_pakeista(self, raktas):
        """Ar bent vienas skilties nustatymas skiriasi nuo numatytojo (↺ be pakeitimų nieko neklausia)."""
        return any(self.n[k] != NUMATYTI[k] for k in SKILCIU_NUSTATYMAI[raktas])

    def atkurti_skilti(self, raktas, vardas):
        """↺ skilties pavadinime: tik tos skilties nustatymai (SKILCIU_NUSTATYMAI) – į numatytuosius."""
        if not self.skiltis_pakeista(raktas):  # nėra ką atkurti – ir neklausiama
            return
        if not messagebox.askyesno(PAVADINIMAS, T("Grąžinti skilties „{s}“ nustatymus į numatytuosius?").format(
                s=T(vardas))):
            return
        nauji = dict(self.n)
        for k in SKILCIU_NUSTATYMAI[raktas]:
            v = NUMATYTI[k]
            nauji[k] = list(v) if isinstance(v, list) else v
        self.taikyti_nustatymus(nauji)

    def eksportuoti_nustatymus(self):
        from tkinter import filedialog
        kelias = filedialog.asksaveasfilename(parent=self.root, title=T("Eksportuoti…"), defaultextension=".json",
                                              initialfile=f"Sniegas_nustatymai_{time.strftime('%Y%m%d')}.json",
                                              filetypes=[(T("Nustatymų byla"), "*.json")])
        if not kelias:
            return
        try:
            Path(kelias).write_text(json.dumps(self.n, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError as e:
            messagebox.showerror(PAVADINIMAS, T("Nepavyko išsaugoti:") + f"\n\n{kelias}\n\n{e!r}")
            return
        ZURNALAS.rasyti(f"ĮVYKIS: nustatymai eksportuoti į {kelias}")
        messagebox.showinfo(PAVADINIMAS, T("Nustatymai išsaugoti:") + f"\n\n{kelias}")

    def importuoti_nustatymus(self):
        from tkinter import filedialog
        kelias = filedialog.askopenfilename(parent=self.root, title=T("Importuoti…"),
                                            filetypes=[(T("Nustatymų byla"), "*.json"), ("*.*", "*.*")])
        if not kelias or not messagebox.askyesno(
                PAVADINIMAS, T("Įkelti nustatymus iš šios bylos? Dabartiniai nustatymai bus pakeisti.") + f"\n\n{kelias}"):
            return
        nauji = self.ikelti_nustatymus(importuojama=kelias)
        nustatyti_kalba(self.n["kalba"])  # ikelti_nustatymus perspėjimui galėjo perjungti kalbą
        if nauji is None:
            return
        nauji["kalba"] = self.n["kalba"]
        if nauji["be_apribojimu"] and not self.n["be_apribojimu"] and not messagebox.askyesno(PAVADINIMAS, T(
                "Byloje įjungtos išplėstos ribos – jos leidžia daug didesnius kiekius ir dydžius, kompiuteris gali strigti."
                "\n\nĮjungti? (Ne – reikšmės bus apribotos įprastomis ribomis.)"), icon="warning"):
            nauji["be_apribojimu"] = False
            apriboti_iprastai(nauji)
        ZURNALAS.rasyti(f"ĮVYKIS: nustatymai importuoti iš {kelias}")
        self.taikyti_nustatymus(nauji)

    def taikyti_nustatymus(self, nauji):
        """Pakeičia visus nustatymus (numatytieji, skilties atkūrimas, importas): laukeliai, peržiūros ir viskas, kas
        nuo nustatymų priklauso, perkuriama. Kalbą keičia tik kalbos perjungiklis."""
        senas = self.n
        buvo_laisvai = senas["be_apribojimu"]
        self.n = nauji
        self.atkuriama = True
        try:
            for raktas, v in self.kint.items():
                v.set(self.n[raktas])
            self.kryzelio_kint.set(T(KRYZELIO_TEKSTAI[KRYZELIO_VEIKSMAI.index(self.n["kryzelis"])]))
            self.vejo_krypties_kb.set(T(VEJO_KRYPCIU_TEKSTAI[VEJO_KRYPTYS.index(self.n["vejo_kryptis"])]))
            self.senio_lempuciu_kb.set(T(SENIO_LEMPUCIU_TEKSTAI[SENIO_LEMPUCIU_ANIMACIJOS.index(
                self.n["senio_lempuciu_animacija"])]))
            self.vejo_perz["kreive"] = None  # vėjo peržiūra – pagal atkurtus nustatymus
            self.vejo_perz["pasenusi"] = True
            for v, kiek in zip(self.tipu_kint, self.n["tipai"]):
                v.set(str(kiek))
            for raktas, varneles in self.tipu_varneles.items():
                for v, reiksme in zip(varneles, self.n[raktas]):
                    v.set(bool(reiksme))
        finally:
            self.atkuriama = False
        # pakeista() čia pokyčių nemato (self.n jau pakeistas), todėl jo šalutiniai veiksmai – ranka
        ZURNALAS.ijungtas = self.n["diagnostika"]
        if not self.n["fejerverkai"]:
            self.papildomos += self.fj.sustabdyti()
        self.kurti_bumbulu_perziura()
        self.kurti_snaigiu_atlasa()
        self.piesti_tipu_perziuras()
        self.atnaujinti_is_viso()
        self.kitas_fj = self.kitas_fejerverku_laikas(time.time())
        self.atnaujinti_skiltis()
        self.piesti_egliu_perziura()
        self.pritaikyti_kieki(perkurti=True)
        self.kurti_egles()
        self.kurti_girliandas()
        self.kurti_bumbulus()
        self.kurti_ekskavatorius()
        self.kurti_senius()
        self.apriboti_sniega()
        # oranžiniai pavadinimai – pagal naujus nustatymus (ne per kurti_girliandas šalutinį poveikį); laukiantis eglių
        # ribų suderinimas – nebereikalingas (atkurtos ribos savos)
        senas_laikmatis = self.__dict__.get("atidetos", {}).pop("egliu_ribos", None)
        if senas_laikmatis:
            self.root.after_cancel(senas_laikmatis)
        self.atnaujinti_ispejimus()
        # kaip pakeista(): išjungus sniegą ar kaupimąsi sukauptas sniegas nuvalomas (importuojant tai įmanoma)
        if senas["snaiges"] != self.n["snaiges"]:
            self.pritaikytas_sniegas()
        if not kaupia(self.n, "kaupti_apacioje") and kaupia(senas, "kaupti_apacioje"):
            self.nuvalyti(tik_zeme=kaupia(self.n, "kaupti_languose"))
        # likusios peržiūros – pagal atkurtus nustatymus (kitaip rodytų senus dydžius iki pirmo užvedimo pele)
        self.piesti_vejo_perziura(self.vejo_perz["zyma"] == "juda")
        self.piesti_girl_perziura()
        self.piesti_ekskav_perziura()
        self.piesti_senio_perziura()
        self.issaugoti()
        if buvo_laisvai != self.n["be_apribojimu"]:  # laukelių ribos pasikeitė – valdikliai sukuriami iš naujo
            self.be_apribojimu_kint.set(self.n["be_apribojimu"])
            self.root.after_idle(self.kurti_sasaja)

    def pritaikyti_paruostuka(self, i):
        """Paruoštukas (PARUOSTUKAI[i]): keičiami tik jo nustatymai – per tuos pačius laukelius ir pakeista(), todėl
        šalutiniai veiksmai (perkūrimai, peržiūros, išsaugojimas) – lygiai kaip keičiant ranka."""
        pav, nust = PARUOSTUKAI[i]
        if not messagebox.askyesno(PAVADINIMAS, T("Pritaikyti paruoštuką „{p}“?").format(p=T(pav)) + "\n\n"
                                   + T("Keičiami tik šio paruoštuko nustatymai, kiti lieka tokie, kokie yra.")):
            self.atnaujinti_paruostukus()  # mygtukas jau nuspaustas – grąžinama tikroji žymė
            return
        kiekis = nust.get("kiekis")
        if kiekis is not None:
            self.nustatyti_snaigiu_kieki(kiekis)
        for raktas, reiksme in paruostuko_nustatymai(nust).items():
            v = self.kint.get(raktas)
            if v is None:
                self.n[raktas] = reiksme
                continue
            v.set(reiksme if isinstance(v, tk.BooleanVar) else str(reiksme))
            self.pakeista(raktas)  # varnelės pakeista() kviečia tik spustelėjus – čia ranka
        self.atnaujinti_paruostukus()
        self.atideti("saugoti", 1000, self.issaugoti)

    def aktyvus_paruostukas(self):
        """Kurio paruoštuko nustatymai dabar galioja (−1 – nė vieno: pakeitus bet kurį jo nustatymą, žymė dingsta;
        NUMATYTIEJI – visi nustatymai numatytieji, išskyrus kalbą)."""
        n = self.n
        if all(n.get(k) == v for k, v in NUMATYTI.items() if k != "kalba"):
            return NUMATYTIEJI
        for i, (_, nust) in enumerate(PARUOSTUKAI):
            if "kiekis" in nust and sum(n["tipai"]) != min(nust["kiekis"], self.maks_viso()):
                continue
            if all(n.get(k) == v for k, v in paruostuko_nustatymai(nust).items()):
                return i
        return -1

    def atnaujinti_paruostukus(self):
        """Pritaikytas (galiojantis) paruoštukas – nuspaustas, paryškintas ir su varnele."""
        kint = getattr(self, "paruostuku_kint", None)
        if kint is None:
            return
        i = self.aktyvus_paruostukas()
        try:
            kint.set(i)
            for pl in self.paruostuku_mygtukai:
                pl.zymeti(pl.paruostukas == i)
        except tk.TclError:  # langas jau uždarytas
            pass

    def nustatyti_snaigiu_kieki(self, kiek, svoriai=None):
        """Snaigių iš viso – kiek; rūšių proporcijos lieka (jei visų rūšių 0 – kaip numatytųjų), arba – pagal
        nurodytus svorius (bendro kiekio juosta)."""
        kiek = max(0, min(int(kiek), self.maks_viso()))
        baze = svoriai or (self.n["tipai"] if sum(self.n["tipai"]) > 0 else NUMATYTI["tipai"])
        viso = sum(baze)
        tikslus = [b * kiek / viso for b in baze]
        nauji = [int(x) for x in tikslus]
        for j in sorted(range(len(nauji)), key=lambda j: tikslus[j] - nauji[j], reverse=True)[:kiek - sum(nauji)]:
            nauji[j] += 1
        nauji = [min(self.maks_tipo(), x) for x in nauji]
        self.atkuriama = True  # pakeisti_tipai() kiekvienam laukeliui atskirai nereikia
        try:
            for v, x in zip(getattr(self, "tipu_kint", ()), nauji):
                v.set(str(x))
        finally:
            self.atkuriama = False
        if nauji != self.n["tipai"]:
            self.n["tipai"] = nauji
            if getattr(self, "is_viso", None) is not None:
                self.atnaujinti_is_viso()
            self.atideti("kiekis", 250, lambda: self.pritaikyti_kieki(visame_ekrane=False))

    def perjungti_rodyma(self):
        """Paslepia arba parodo viską: sniegą, eglutes, bumbuliukus ir fejerverkus."""
        self.vartotojas_paslepe = not self.vartotojas_paslepe
        self.rodymo_mygtukas.configure(text=T("Rodyti viską" if self.vartotojas_paslepe else "Paslėpti viską"))
        self.taikyti_matomuma()

    @property
    def sniegas_isjungtas(self):
        return not self.n["snaiges"]

    def perjungti_sniega(self):
        """Dėklo meniu „Išjungti / Įjungti sniegą“ – tas pats, kas varnelė „Snaigės“ nustatymuose."""
        self.n["snaiges"] = not self.n["snaiges"]
        if "snaiges" in getattr(self, "kint", {}):
            try:
                self.kint["snaiges"].set(self.n["snaiges"])
            except tk.TclError:  # nustatymų langas uždarytas
                pass
        self.pritaikytas_sniegas()
        self.atideti("saugoti", 1000, self.issaugoti)

    def pritaikytas_sniegas(self):
        """Išjungus sniegą snaigės nebekrenta, sukauptas sniegas nuvalomas. Eglutės, bumbuliukai ir
        fejerverkai lieka. Įjungus snaigės vėl pradeda kristi iš viršaus."""
        self.pritaikyti_kieki(visame_ekrane=False)
        if self.sniegas_isjungtas:
            self.nuvalyti()
        if self.n["sniegas_ant_egliu"]:
            self.pilnas_perpiesimas = True  # eglės perpiešiamos su sniegu ant šakų arba be jo
            if getattr(self, "perziuros_egles", None):
                try:
                    self.piesti_egliu_perziura(perkurti=False)
                except tk.TclError:  # nustatymų langas uždarytas
                    pass
        self.atnaujinti_skiltis()

    def perjungti_autostarta(self):
        try:
            nustatyti_autostarta(self.autostartas.get())
        except Exception as e:
            self.autostartas.set(autostartas_ijungtas() is not None)
            messagebox.showerror(PAVADINIMAS, T("Nepavyko pakeisti automatinio paleidimo nustatymo.") + f"\n\n{e!r}")

    def atnaujinti_autostarto_kelia(self):
        """Po versijos atnaujinimo bylos vardas pasikeičia – įrašas nukreipiamas į šią bylą. Bet tik tada, kai
        senoji byla dingo arba ji senesnės versijos: vienąkart paleista sena kopija ar kopija iš „Atsisiuntimų“
        neturi perimti automatinio paleidimo."""
        try:
            esama = autostartas_ijungtas()
            if esama is None or esama == autostarto_komanda():
                return
            bylos = [Path(b) for b in re.findall(r'"([^"]+\.(?:pyw|py|exe))"', esama)]
            sena = bylos[-1] if bylos else None
            if sena is not None and sena.exists():
                # dešimtainiai skaičiai, ne (sveikoji, trupmeninė) pora: 12.05 < 12.1, nors 5 > 1 (smulkūs
                # pataisymai – po 0.01)
                v = re.search(r"_v(\d+\.\d+)", sena.name)
                if v is None or float(v.group(1)) >= float(VERSIJA):
                    return  # įrašas rodo į esamą tokią pat ar naujesnę versiją – neliečiame
            nustatyti_autostarta(True)
            ZURNALAS.rasyti(f"ĮVYKIS: automatinis paleidimas nukreiptas į šią bylą (buvo: {esama})")
        except Exception:
            pass

    def baigti(self):
        """Kiekvienas žingsnis atskirai – vieno klaida neturi palikti „vaiduoklio“ piktogramos ar neužsidarančios
        programos. root.destroy() – visada paskutinis."""
        self.baigiama = True
        if ZURNALAS.ijungtas and getattr(self, "d_kadrai", 0):
            self.diagnostikos_suvestine(paskutine=True)
        ZURNALAS.rasyti("===== BAIGTA (naudotojas)")

        def issaugoti():
            senas = self.atidetos.get("saugoti")
            if senas:
                self.root.after_cancel(senas)
            self.issaugoti()

        for zingsnis in (issaugoti, lambda: self.laikmacio_tikslumas(False), lambda: mmcss_isjungti(self.mmcss),
                         self.naikinti_dekla,
                         self.naikinti_langu_kabliukus, self.atstatyti_lango_procedura,
                         self.atstatyti_nustatymu_procedura, self.atlaisvinti_buferius):
            try:
                zingsnis()
            except Exception:
                ZURNALAS.rasyti("KLAIDA baigiant:\n" + traceback.format_exc())
        self.root.destroy()


def nustatyti_tk_ikona(root):
    """Programos piktograma – numatytoji visiems tkinter langams, nustatoma prieš parodant bet kurį langą."""
    kelias = Path(tempfile.gettempdir()) / f"sniegas_tk_{os.getpid()}.ico"
    try:
        kelias.write_bytes(logo_ico((16, 20, 24, 32, 40, 48, 64, 128, 256)))
        root.iconbitmap(default=str(kelias))
    except (OSError, tk.TclError) as e:
        ZURNALAS.rasyti(f"KLAIDA: tkinter piktograma nenustatyta: {e!r}")
    finally:
        try:
            kelias.unlink(missing_ok=True)
        except OSError:
            pass


def kalba_is_nustatymu():
    """Tik kalba iš nustatymų bylos – pranešimui „jau veikia“, kai Sniegas (ir ikelti_nustatymus) dar nesukurtas."""
    for byla in (NUSTATYMU_BYLA, VIETINE_BYLA):
        try:
            duom = json.loads(byla.read_text(encoding="utf-8-sig"))
            if isinstance(duom, dict):
                return duom.get("kalba", "lt")
        except Exception:
            continue
    return "lt"


def sukurti_ikonos_byla(kelias):
    """sniegas.ico kompiliavimui. Jei tokia pat jau yra – neperrašoma: Failų naršyklė, rodanti aplanką su .ico, bylą
    laiko atidariusi (atvaizduotą atmintyje), ir Windows neleidžia jos perrašyti – Python tai rodo kaip
    OSError(22, 'Invalid argument'). Perrašoma per laikiną bylą; nepavykus – aiškus paaiškinimas, ką daryti."""
    duomenys = logo_ico((16, 24, 32, 48, 64, 128, 256))
    try:
        if kelias.exists() and kelias.read_bytes() == duomenys:
            return True  # jau tokia pat – kompiliuoti galima
    except OSError:
        pass
    laikina = kelias.with_name(kelias.name + ".tmp")
    try:
        laikina.write_bytes(duomenys)
        os.replace(laikina, kelias)
        return True
    except OSError as e:
        try:
            laikina.unlink()
        except OSError:
            pass
        r = tk.Tk()
        r.withdraw()
        messagebox.showerror(PAVADINIMAS, f"{kelias}\n\n{e!r}\n\n" + T(
            "Nepavyko perrašyti piktogramos – greičiausiai ją laiko atidariusi kita programa (dažniausiai Failų "
            "naršyklės langas su šiuo aplanku rodo jos paveikslėlį). Uždarykite to aplanko langą arba ištrinkite "
            "sniegas.ico ir paleiskite dar kartą."), parent=r)
        r.destroy()
        return False


def main():
    if sys.platform != "win32":
        print("Ši programa veikia tik Windows. / This program runs only on Windows.")
        return
    if "--ikona" in sys.argv:  # piktograma kompiliavimui: py Sniegas_….pyw --ikona
        sukurti_ikonos_byla(PROGRAMOS_APLANKAS / "sniegas.ico")
        return
    nustatyti_dpi()
    try:
        # Kad užduočių juostoje būtų programos (sniego senio) ženkliukas, o ne Python'o
        f = ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID
        f.argtypes, f.restype = [wintypes.LPCWSTR], ctypes.c_long  # HRESULT; tipai – dėl aiškumo
        f(PROGRAMOS_ID)
    except Exception:
        pass
    mutex = kernel32.CreateMutexW(None, False, "Local\\" + PROGRAMOS_ID)  # laikomas iki programos pabaigos
    try:
        klaida = ctypes.get_last_error()
        # ERROR_ACCESS_DENIED (5) be rankenos – mutex sukūrė kita, administratoriaus teisėmis veikianti kopija
        if klaida == ERROR_ALREADY_EXISTS or (not mutex and klaida == 5):
            nustatyti_kalba(kalba_is_nustatymu())
            r = tk.Tk()
            r.withdraw()
            messagebox.showinfo(PAVADINIMAS, T("„Sniegas“ jau veikia – jo piktogramą rasite prie laikrodžio."),
                                parent=r)
            r.destroy()
            return
        sys.excepthook = lambda t, v, tb: ZURNALAS.rasyti(
            "NEPAGAUTA KLAIDA: " + "".join(traceback.format_exception(t, v, tb)), visada=True)
        threading.excepthook = lambda a: ZURNALAS.rasyti(
            "KLAIDA gijoje: " + "".join(traceback.format_exception(a.exc_type, a.exc_value, a.exc_traceback)),
            visada=True)
        root = tk.Tk()
        root.withdraw()  # parodomas tik nustačius piktogramą (Sniegas.__init__ pabaigoje)
        nustatyti_tk_ikona(root)
        try:
            # nuoroda laikoma iki pabaigos – kad įdiegti ctypes atgaliniai kvietimai (WNDPROC ir kt.) neišnyktų
            root.sniegas = Sniegas(root, "--sumazinta" in sys.argv)
        except Exception as e:
            ZURNALAS.rasyti("KLAIDA paleidžiant: " + traceback.format_exc(), visada=True)
            messagebox.showerror(PAVADINIMAS, T("Nepavyko paleisti programos.") + f"\n\n{e!r}")
            root.destroy()
            return
        root.mainloop()
    finally:
        if mutex:
            kernel32.CloseHandle(mutex)


if __name__ == "__main__":
    main()
