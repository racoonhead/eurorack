# Mutable Instruments Eurorack Modules

Source code and hardware design files for Mutable Instruments Eurorack modules, including the updated **Elements v0.4** hardware and firmware revision.

* **[Beads](beads/):** Texture synthesizer (1).
* **[Blades](blades/):** Dual multimode filter.
* **[Blinds](blinds/):** Quad VC-polarizer.
* **[Braids](braids/):** Macro-oscillator.
* **[Branches](branches/):** Dual Bernoulli gate.
* **[Clouds](clouds/):** Texture synthesizer.
* **[Ears](ears/):** Contact microphone.
* **[Edges](edges/):** Quad chiptune digital oscillator.
* **[Elements](elements/):** Modal synthesizer *(Revision v0.4 – STM32H743)*.
* **[Frames](frames/):** Keyframer/mixer.
* **[Grids](grids/):** Topographic drum sequencer.
* **[Kinks](kinks/):** Utility module - rectifier, analog logic, S&H, noise.
* **[Links](links/):** Utility module - buffer, mixer.
* **[Marbles](marbles/):** Random sampler.
* **[Peaks](peaks/):** Dual trigger converter.
* **[Plaits](plaits/):** Macro-oscillator.
* **[Rings](rings/):** Resonator.
* **[Ripples](ripples/):** Liquid 2-pole BP, 2-pole LP and 4-pole LP filter.
* **[Shades](shades/):** Triple attenuverter.
* **[Shelves](shelves/):** EQ filter.
* **[Stages](stages/):** Segment generator.
* **[Streams](streams/):** Dual dynamics gate.
* **[Tides](tides/) / [Tides 2](tides2/):** Tidal modulator.
* **[Veils](veils/):** Quad VCA.
* **[Volts](volts/):** +5V power module.
* **[Warps](warps/):** Meta-modulator.
* **[Yarns](yarns/):** MIDI interface.

(1) Code provided as is, builds on a Desktop platform but not verified to build and run on a module. Install at your own risks.

---

## Elements – Revision v0.4

Hardware and firmware revision (**v0.4**) of the [Elements](elements/) modal synthesizer module:

* **Microcontroller:** Migrated from STM32F405 (Cortex-M4F @ 168 MHz) to **STM32H743VIT6 (Cortex-M7 @ 480 MHz)** with 2 MB Flash and 1 MB RAM.
* **Audio Path:** 24-bit / 48 kHz **TI PCM3060** stereo audio codec (hardware-configured mode) paired with **TI OPA1664D** output op-amps.
* **Signal Acquisition:** 16-bit SAR ADCs for 1V/Oct, CV inputs, and multiplexed potentiometers.
* **Exciter Engine:** 2 selectable modes – *Classic* (Bow, Blow, Strike) and *Industrial* (Friction, Burst, Samples).
* **Resonator Engine:** 8 resonator models (3 original Elements models, 4 ported Rings models, and Kammerl Spectral Clouds).
* **Controls & Hardware:** Dedicated hardware tactile switches for Exciter and Resonator model selection; KiCad v8/v10 schematics and PCB layouts (34 HP unified and 20 HP + 14 HP split front panel options).

Full documentation and design files are located in [`elements/README.md`](elements/README.md).

---

## License

* **Code (AVR projects):** GPL3.0
* **Code (STM32 projects):** MIT license
* **Hardware:** cc-by-sa-3.0

By: Émilie Gillet (emilie.o.gillet@gmail.com)

---

## Guidelines for derivative works

**Mutable Instruments is a registered trademark.**

The name "Mutable Instruments" should not be used on any of the derivative works you create from these files.

We do not recommend you to keep the original name of the Mutable Instruments module for your derivative works.

For example, your 5U adaptation of Mutable Instruments Clouds can be called "Foobar Modular - Particle Generator".
