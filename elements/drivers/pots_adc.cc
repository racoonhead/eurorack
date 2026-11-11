// Copyright 2014 Emilie Gillet.
//
// Author: Emilie Gillet (emilie.o.gillet@gmail.com)
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
// 
// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.
// 
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
// THE SOFTWARE.
// 
// See http://creativecommons.org/licenses/MIT/ for more information.
//
// -----------------------------------------------------------------------------
//
// Driver for ADC2 – STM32H743 HAL, scanning pots via 4× HC4051 multiplexers.
//
// Hardware:
//   ADC2 channel 10 (PC0) – analog input from selected mux output.
//   MUX enable (active-low): PB5 PB6 PB7 PB8  (one per mux IC, 4 chips × 8 ch = 32 ch)
//   MUX address bits A/B/C: PC13 PC15 (see Scan() for bit order)
//
// Note: PC13 / PC15 here are DIGITAL OUTPUTS for mux addressing,
// NOT analog inputs – distinct from the V_OCT / FM schematic issue.

#include "elements/drivers/pots_adc.h"

#include <stm32h7xx_hal.h>

namespace elements {

/* static */
uint8_t PotsAdc::addresses_[POT_LAST] = {
  28,  // POT_EXCITER_ENVELOPE_SHAPE,
  30,  // POT_EXCITER_BOW_LEVEL,
  5,   // POT_EXCITER_BOW_TIMBRE,
  1,   // POT_EXCITER_BOW_TIMBRE_ATTENUVERTER,
  29,  // POT_EXCITER_BLOW_LEVEL,
  31,  // POT_EXCITER_BLOW_META,
  2,   // POT_EXCITER_BLOW_META_ATTENUVERTER,
  7,   // POT_EXCITER_BLOW_TIMBRE,
  11,  // POT_EXCITER_BLOW_TIMBRE_ATTENUVERTER,
  22,  // POT_EXCITER_STRIKE_LEVEL,
  20,  // POT_EXCITER_STRIKE_META,
  8,   // POT_EXCITER_STRIKE_META_ATTENUVERTER,
  6,   // POT_EXCITER_STRIKE_TIMBRE,
  9,   // POT_EXCITER_STRIKE_TIMBRE_ATTENUVERTER,
  23,  // POT_RESONATOR_COARSE,
  26,  // POT_RESONATOR_FINE,
  25,  // POT_RESONATOR_FM_ATTENUVERTER,
  21,  // POT_RESONATOR_GEOMETRY,
  19,  // POT_RESONATOR_GEOMETRY_ATTENUVERTER,
  24,  // POT_RESONATOR_BRIGHTNESS,
  17,  // POT_RESONATOR_BRIGHTNESS_ATTENUVERTER,
  4,   // POT_RESONATOR_DAMPING,
  10,  // POT_RESONATOR_DAMPING_ATTENUVERTER,
  0,   // POT_RESONATOR_POSITION,
  16,  // POT_RESONATOR_POSITION_ATTENUVERTER,
  27,  // POT_SPACE,
  18,  // POT_SPACE_ATTENUVERTER
};

static ADC_HandleTypeDef hadc2;

void PotsAdc::Init() {
  // ---- Clock enables -------------------------------------------------------
  __HAL_RCC_ADC12_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();
  __HAL_RCC_GPIOC_CLK_ENABLE();
  __HAL_RCC_GPIOE_CLK_ENABLE();

  GPIO_InitTypeDef gpio = {};

  // ---- ADC analog input: PC0 = ADC12_INP10 (or analog input pin) ----------
  gpio.Pin  = GPIO_PIN_0;
  gpio.Mode = GPIO_MODE_ANALOG;
  gpio.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(GPIOC, &gpio);

  // ---- MUX enable pins: PB4 PB5 PB6 PB8 (active-low, init HIGH = inhibit) -
  gpio.Pin   = GPIO_PIN_4 | GPIO_PIN_5 | GPIO_PIN_6 | GPIO_PIN_8;
  gpio.Mode  = GPIO_MODE_OUTPUT_PP;
  gpio.Speed = GPIO_SPEED_FREQ_LOW;
  gpio.Pull  = GPIO_NOPULL;
  HAL_GPIO_Init(GPIOB, &gpio);
  HAL_GPIO_WritePin(GPIOB,
      GPIO_PIN_4 | GPIO_PIN_5 | GPIO_PIN_6 | GPIO_PIN_8,
      GPIO_PIN_SET); // inhibit all

  // ---- MUX address bits: PE4 PE3 PE2 (A, B, C) ----------------------------
  gpio.Pin   = GPIO_PIN_2 | GPIO_PIN_3 | GPIO_PIN_4;
  gpio.Mode  = GPIO_MODE_OUTPUT_PP;
  gpio.Speed = GPIO_SPEED_FREQ_LOW;
  gpio.Pull  = GPIO_NOPULL;
  HAL_GPIO_Init(GPIOE, &gpio);
  HAL_GPIO_WritePin(GPIOE,
      GPIO_PIN_2 | GPIO_PIN_3 | GPIO_PIN_4,
      GPIO_PIN_RESET);

  // ---- ADC2 init -----------------------------------------------------------
  hadc2.Instance                      = ADC2;
  hadc2.Init.ClockPrescaler           = ADC_CLOCK_ASYNC_DIV1; // 8 MHz (PER_CK=HSE)
  hadc2.Init.Resolution               = ADC_RESOLUTION_16B;
  hadc2.Init.ScanConvMode             = ADC_SCAN_DISABLE;
  hadc2.Init.EOCSelection             = ADC_EOC_SINGLE_CONV;
  hadc2.Init.LowPowerAutoWait         = DISABLE;
  hadc2.Init.ContinuousConvMode       = DISABLE;
  hadc2.Init.NbrOfConversion          = 1;
  hadc2.Init.DiscontinuousConvMode    = DISABLE;
  hadc2.Init.NbrOfDiscConversion      = 1;
  hadc2.Init.ExternalTrigConv         = ADC_SOFTWARE_START;
  hadc2.Init.ExternalTrigConvEdge     = ADC_EXTERNALTRIGCONVEDGE_NONE;
  hadc2.Init.ConversionDataManagement = ADC_CONVERSIONDATA_DR;
  hadc2.Init.Overrun                  = ADC_OVR_DATA_OVERWRITTEN;
  hadc2.Init.LeftBitShift             = ADC_LEFTBITSHIFT_NONE;
  hadc2.Init.OversamplingMode         = DISABLE;
  hadc2.Init.BoostMode                = ENABLE;
  HAL_ADC_Init(&hadc2);

  HAL_ADCEx_Calibration_Start(&hadc2, ADC_CALIB_OFFSET, ADC_SINGLE_ENDED);

  // Configure single channel: PC0 = ADC2_INP10
  ADC_ChannelConfTypeDef ch = {};
  ch.Channel      = ADC_CHANNEL_10;
  ch.Rank         = ADC_REGULAR_RANK_1;
  ch.SamplingTime = ADC_SAMPLETIME_387CYCLES_5;
  ch.SingleDiff   = ADC_SINGLE_ENDED;
  ch.OffsetNumber = ADC_OFFSET_NONE;
  ch.Offset       = 0;
  HAL_ADC_ConfigChannel(&hadc2, &ch);

  index_     = POT_LAST - 1;
  last_read_ = 0;
  state_     = false;
  Scan();
}

void PotsAdc::DeInit() {
  HAL_ADC_Stop(&hadc2);
  HAL_ADC_DeInit(&hadc2);
}

void PotsAdc::Scan() {
  if (state_) {
    // Read result from previous conversion.
    values_[index_] = static_cast<uint16_t>(HAL_ADC_GetValue(&hadc2));
    last_read_ = index_;
    ++index_;
    if (index_ >= POT_LAST) {
      index_ = 0;
    }

    uint8_t address = addresses_[index_];

    // Inhibit all muxes (PB4, PB5, PB6, PB8).
    HAL_GPIO_WritePin(GPIOB,
        GPIO_PIN_4 | GPIO_PIN_5 | GPIO_PIN_6 | GPIO_PIN_8,
        GPIO_PIN_SET);

    // Write mux address bits (A = PE4, B = PE3, C = PE2).
    HAL_GPIO_WritePin(GPIOE, GPIO_PIN_4,
        (address & 1) ? GPIO_PIN_SET : GPIO_PIN_RESET); // A
    HAL_GPIO_WritePin(GPIOE, GPIO_PIN_3,
        (address & 2) ? GPIO_PIN_SET : GPIO_PIN_RESET); // B
    HAL_GPIO_WritePin(GPIOE, GPIO_PIN_2,
        (address & 4) ? GPIO_PIN_SET : GPIO_PIN_RESET); // C

    // Enable the correct mux (address bits 4..3 select which of the 4 chips: 0=PB4, 1=PB5, 2=PB6, 3=PB8).
    static const uint16_t bank_pins[4] = { GPIO_PIN_4, GPIO_PIN_5, GPIO_PIN_6, GPIO_PIN_8 };
    HAL_GPIO_WritePin(GPIOB, bank_pins[address >> 3], GPIO_PIN_RESET);

  } else {
    HAL_ADC_Start(&hadc2);
  }
  state_ = !state_;
}

}  // namespace elements
