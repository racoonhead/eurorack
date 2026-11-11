# Mutable Instruments – Eurorack Modules

Open-source firmware a hardwarové podklady pro modulární syntezátory **Mutable Instruments** v prostředí Eurorack, včetně rozšířené revize modulu **Elements (v0.4)**.

---

## 🌟 Speciální revize: Elements v0.4 (STM32H743 Edition)

Tento repozitář obsahuje modernizovanou hardwarovou i firmwarovou revizi modulu **Elements (v0.4)**, která původní platformu výrazně posouvá po stránce výpočetního výkonu, audio kvality i zvukových možností.

### Hlavní vylepšení Elements v0.4:
* **Výpočetní jádro (MCU):** Přechod z původního STM32F405 (Cortex-M4F @ 168 MHz) na extrémně výkonný **ARM Cortex-M7 (STM32H743VIT6 @ 480 MHz)** s 2 MB Flash a 1 MB RAM.
* **Audio převodník (Codec):** 24-bitový **TI PCM3060** v hardwarovém režimu (bez nutnosti I2C inicializace) se vzorkovací frekvencí 48 kHz a výstupními operačními zesilovači **TI OPA1664D** pro nižší šumové dno.
* **Přesnější převod CV:** 16-bitové SAR ADC pro 1V/Oct a CV vstupy (16× vyšší rozlišení oproti původním 12 bitům) a jemnější snímání potenciometrů.
* **Rozšířený exciter engine (2 režimy):** 
  * *1: Classic* (původní modely Bow, Blow, Strike)
  * *2: Industrial* (metal friction, digital burst a industrial sample set)
* **Rozšířený rezonátor (8 modelů):**
  * Původní modely Elements (Modal, String, Chords)
  * Portované modely z modulu Rings
  * Implementace Kammerl Spectral Clouds
* **Ovládací prvky:** Přidána dedikovaná hardwarová tlačítka pro přímý výběr Exciter a Resonator modelů.
* **Panel:** Podpora pro dvoudílný dělený panel (20 HP Exciter + 14 HP Resonator) i jednotný 34 HP monolitický černý panel (KiCad v8/v10).

> Detailní technickou dokumentaci a schémata naleznete přímo v adresáři [`elements/`](elements/) (popř. [`elements/README.md`](elements/README.md)).

---

## 🎹 Seznam modulů v repozitáři

### Digitální syntéza a zpracování zvuku (STM32)
* **[Elements](elements/):** Modální syntetizér fyzikálního modelování (ve verzi v0.4 na STM32H7).
* **[Beads](beads/):** Granulární texturovací syntetizér nové generace (STM32H7).
* **[Clouds](clouds/):** Granulární texturovací procesor v reálném čase.
* **[Plaits](plaits/):** Všestranný makro-oscilátor (16 syntetických modelů).
* **[Rings](rings/):** Resonátor a fyzikální modelování strun/membrán.
* **[Braids](braids/):** Digitální makro-oscilátor s bohatou paletou vlnových průběhů.
* **[Warps](warps/):** Meta-modulátor, crossfader, wavefolder a kruhový modulátor.
* **[Tides](tides/) / [Tides 2](tides2/):** Přílivový generátor funkcí, LFO a audio oscilátor.
* **[Stages](stages/):** Pokročilý segmentový generátor obálek a modulací.
* **[Marbles](marbles/):** Generátor náhodných napětí, rytmů a kvantizovaných sekvencí.
* **[Frames](frames/):** Maticový keyframer a digitálně řízený mixer.
* **[Yarns](yarns/):** Vícehlasý MIDI interface a sekvencer.

### Analogové a hybridní moduly
* **[Blades](blades/):** Duální analogový multimódový filtr s plynulým přechodem a wavefolderem.
* **[Ripples](ripples/):** Kapalinový analogový 2-pole a 4-pole filtr.
* **[Veils](veils/):** Čtyřnásobný VCA s nastavitelnou exponenciální/lineární křivkou.
* **[Blinds](blinds/):** Čtyřnásobný čtyřkvadrantový násobič / polarizér.
* **[Shelves](shelves/):** Parametrický 4-pásmový ekvalizér.
* **[Ears](ears/):** Kontaktní mikrofon s obálkovým sledovačem a gate detektorem.

### AVR moduly (8-bitové mikrokontroléry)
* **[Peaks](peaks/):** Duální multifunkční bicí generátor, obálka a LFO.
* **[Grids](grids/):** Topografický generátor bicích rytmů založený na mapách.
* **[Branches](branches/):** Duální Bernoulliho gate s pravděpodobnostním směrováním.
* **[Edges](edges/):** Čtyřhlasý chiptune oscilátor.

### Pasivní a pomocné moduly
* **[Links](links/):** Bufferovaný distributor a sčítací mix.
* **[Kinks](kinks/):** Usměrňovač, analogová logika (max/min) a Sample & Hold.
* **[Shades](shades/):** Trojitý atenuátor a offset generátor.
* **[Volts](volts/):** Převodník napájení +5V.

---

## 🛠️ Kompilace firmwaru

Pro pohodlnou kompilaci bez konfliktů závislostí využijte připravené prostředí v sousedním adresáři [`mutable-dev-environment`](../mutable-dev-environment/):

* **Raspberry Pi 5 (Manjaro ARM) / moderní Linux:** Spusťte `./setup-manjaro.sh` a kompilujte nativním `arm-none-eabi-gcc`.
* **Docker:** Spusťte `./docker-build.sh <modul>`.
* **x86 Manjaro / Vagrant:** Pro starší moduly vyžadující přesný toolchain GCC 4.8.3.

Příklad kompilace modulu z kořenové složky `eurorack`:
```bash
# Kompilace Elements v0.4:
make -j4 -f elements/makefile

# Kompilace Clouds nebo Plaits:
make -j4 -f clouds/makefile
make -j4 -f plaits/makefile

# Vytvoření audio bootloader WAV souboru:
make -f elements/makefile wav
```

---

## 📄 Licence a ochranné známky

* **Kód (STM32 projekty):** MIT License
* **Kód (AVR projekty):** GPL v3.0
* **Hardware design:** Creative Commons CC-BY-SA-3.0
* **Původní autor:** Émilie Gillet (pichenettes)

> **Upozornění k ochranné známce:** *Mutable Instruments* je registrovaná ochranná známka. Název nesmí být používán pro komerční odvozená díla bez souhlasu.
