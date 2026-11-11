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
// Driver for ADC1 – STM32H743 HAL, DMA circular mode.
//
// CV channel mapping (ADC1, 16-bit resolution):
//
//   Slot  CvAdcChannel                   GPIO  ADC1 channel
//   ────  ─────────────────────────────  ────  ────────────
//    1    CV_ADC_V_OCT                   PC2   INP12
//    2    CV_ADC_FM                      PC1   INP11
//    3    CV_ADC_PRESSURE                PA0   INP16
//    4    CV_ADC_EXCITER_BOW_TIMBRE      PA1   INP17
//    5    CV_ADC_EXCITER_BLOW_META       PA2   INP14
//    6    CV_ADC_EXCITER_BLOW_TIMBRE     PA3   INP15
//    7    CV_ADC_EXCITER_STRIKE_META     PA4   INP18
//    8    CV_ADC_EXCITER_STRIKE_TIMBRE   PA5   INP19
//    9    CV_ADC_RESONATOR_DAMPING       PA6   INP3
//   10    CV_ADC_RESONATOR_GEOMETRY      PA7   INP7
//   11    CV_ADC_RESONATOR_POSITION      PC5   INP8
//   12    CV_ADC_RESONATOR_BRIGHTNESS    PB0   INP9
//   13    CV_ADC_SPACE                   PB1   INP5
//
//
// ADC clock: PER_CK = HSE = 8 MHz (async, configured in system.cc).
// DMA: DMA2_Stream0, DMAMUX1 request DMA_REQUEST_ADC1.

#include "elements/drivers/cv_adc.h"

#include <stm32h7xx_hal.h>

namespace elements {

static ADC_HandleTypeDef hadc1;
static DMA_HandleTypeDef hdma_adc1;

void CvAdc::Init(bool auto_convert) {
  // ---- Clock enables -------------------------------------------------------
  __HAL_RCC_ADC12_CLK_ENABLE();
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();
  __HAL_RCC_GPIOC_CLK_ENABLE();
  __HAL_RCC_DMA2_CLK_ENABLE();

  // ---- GPIO: analog inputs -------------------------------------------------
  GPIO_InitTypeDef gpio = {};
  gpio.Mode = GPIO_MODE_ANALOG;
  gpio.Pull = GPIO_NOPULL;

  // PA0–PA7
  gpio.Pin = GPIO_PIN_0 | GPIO_PIN_1 | GPIO_PIN_2 | GPIO_PIN_3 | GPIO_PIN_4 |
             GPIO_PIN_5 | GPIO_PIN_6 | GPIO_PIN_7;
  HAL_GPIO_Init(GPIOA, &gpio);

  // PB0, PB1
  gpio.Pin = GPIO_PIN_0 | GPIO_PIN_1;
  HAL_GPIO_Init(GPIOB, &gpio);

  // PC1 (ADC_FM = ADC1_INP11), PC2 (ADC_V_OCT = ADC1_INP12), PC5 (ADC_POSITION
  // = ADC1_INP8)
  gpio.Pin = GPIO_PIN_1 | GPIO_PIN_2 | GPIO_PIN_5;
  HAL_GPIO_Init(GPIOC, &gpio);

  // ---- DMA -----------------------------------------------------------------
  // DMA2_Stream0, DMAMUX1 → ADC1
  hdma_adc1.Instance = DMA2_Stream0;
  hdma_adc1.Init.Request = DMA_REQUEST_ADC1;
  hdma_adc1.Init.Direction = DMA_PERIPH_TO_MEMORY;
  hdma_adc1.Init.PeriphInc = DMA_PINC_DISABLE;
  hdma_adc1.Init.MemInc = DMA_MINC_ENABLE;
  hdma_adc1.Init.PeriphDataAlignment = DMA_PDATAALIGN_HALFWORD; // 16-bit ADC
  hdma_adc1.Init.MemDataAlignment = DMA_MDATAALIGN_HALFWORD;
  hdma_adc1.Init.Mode = DMA_CIRCULAR;
  hdma_adc1.Init.Priority = DMA_PRIORITY_HIGH;
  hdma_adc1.Init.FIFOMode = DMA_FIFOMODE_DISABLE;
  HAL_DMA_Init(&hdma_adc1);
  __HAL_LINKDMA(&hadc1, DMA_Handle, hdma_adc1);

  // ---- ADC init ------------------------------------------------------------
  hadc1.Instance = ADC1;
  hadc1.Init.ClockPrescaler = ADC_CLOCK_ASYNC_DIV1; // 8 MHz (PER_CK=HSE)
  hadc1.Init.Resolution = ADC_RESOLUTION_16B;
  hadc1.Init.ScanConvMode = ADC_SCAN_ENABLE;
  hadc1.Init.EOCSelection = ADC_EOC_SEQ_CONV;
  hadc1.Init.LowPowerAutoWait = DISABLE;
  hadc1.Init.ContinuousConvMode = auto_convert ? ENABLE : DISABLE;
  hadc1.Init.NbrOfConversion = CV_ADC_CHANNEL_LAST;
  hadc1.Init.DiscontinuousConvMode = DISABLE;
  hadc1.Init.NbrOfDiscConversion = 1;
  hadc1.Init.ExternalTrigConv = ADC_SOFTWARE_START;
  hadc1.Init.ExternalTrigConvEdge = ADC_EXTERNALTRIGCONVEDGE_NONE;
  hadc1.Init.ConversionDataManagement = ADC_CONVERSIONDATA_DMA_CIRCULAR;
  hadc1.Init.Overrun = ADC_OVR_DATA_OVERWRITTEN;
  hadc1.Init.LeftBitShift = ADC_LEFTBITSHIFT_NONE;
  hadc1.Init.OversamplingMode = DISABLE;
  hadc1.Init.BoostMode = ENABLE; // required for ADC clock > 20 MHz
  HAL_ADC_Init(&hadc1);

  // Calibrate (offset, single-ended) – mandatory after init on H743.
  HAL_ADCEx_Calibration_Start(&hadc1, ADC_CALIB_OFFSET, ADC_SINGLE_ENDED);

  // ---- Channel sequence ----------------------------------------------------
  // Long sampling time (387.5 cy @ 8 MHz ≈ 49 µs/ch) → ~650 µs for 13 ch.
  ADC_ChannelConfTypeDef ch = {};
  ch.SamplingTime = ADC_SAMPLETIME_387CYCLES_5;
  ch.SingleDiff = ADC_SINGLE_ENDED;
  ch.OffsetNumber = ADC_OFFSET_NONE;
  ch.Offset = 0;

  // Slot 1 – CV_ADC_V_OCT – PC2 = ADC1_INP12
  ch.Channel = ADC_CHANNEL_12;
  ch.Rank = ADC_REGULAR_RANK_1;
  HAL_ADC_ConfigChannel(&hadc1, &ch);

  // Slot 2 – CV_ADC_FM – PC1 = ADC1_INP11
  ch.Channel = ADC_CHANNEL_11;
  ch.Rank = ADC_REGULAR_RANK_2;
  HAL_ADC_ConfigChannel(&hadc1, &ch);

  // Slot 3 – CV_ADC_PRESSURE – PA0 = ADC1_INP16
  ch.Channel = ADC_CHANNEL_16;
  ch.Rank = ADC_REGULAR_RANK_3;
  HAL_ADC_ConfigChannel(&hadc1, &ch);

  // Slot 4 – CV_ADC_EXCITER_BOW_TIMBRE – PA1 = ADC1_INP17
  ch.Channel = ADC_CHANNEL_17;
  ch.Rank = ADC_REGULAR_RANK_4;
  HAL_ADC_ConfigChannel(&hadc1, &ch);

  // Slot 5 – CV_ADC_EXCITER_BLOW_META – PA2 = ADC1_INP14
  ch.Channel = ADC_CHANNEL_14;
  ch.Rank = ADC_REGULAR_RANK_5;
  HAL_ADC_ConfigChannel(&hadc1, &ch);

  // Slot 6 – CV_ADC_EXCITER_BLOW_TIMBRE – PA3 = ADC1_INP15
  ch.Channel = ADC_CHANNEL_15;
  ch.Rank = ADC_REGULAR_RANK_6;
  HAL_ADC_ConfigChannel(&hadc1, &ch);

  // Slot 7 – CV_ADC_EXCITER_STRIKE_META – PA4 = ADC1_INP18
  ch.Channel = ADC_CHANNEL_18;
  ch.Rank = ADC_REGULAR_RANK_7;
  HAL_ADC_ConfigChannel(&hadc1, &ch);

  // Slot 8 – CV_ADC_EXCITER_STRIKE_TIMBRE – PA5 = ADC1_INP19
  ch.Channel = ADC_CHANNEL_19;
  ch.Rank = ADC_REGULAR_RANK_8;
  HAL_ADC_ConfigChannel(&hadc1, &ch);

  // Slot 9 – CV_ADC_RESONATOR_DAMPING – PA6 = ADC1_INP3
  ch.Channel = ADC_CHANNEL_3;
  ch.Rank = ADC_REGULAR_RANK_9;
  HAL_ADC_ConfigChannel(&hadc1, &ch);

  // Slot 10 – CV_ADC_RESONATOR_GEOMETRY – PA7 = ADC1_INP7
  ch.Channel = ADC_CHANNEL_7;
  ch.Rank = ADC_REGULAR_RANK_10;
  HAL_ADC_ConfigChannel(&hadc1, &ch);

  // Slot 11 – CV_ADC_RESONATOR_POSITION – PC5 = ADC1_INP8
  ch.Channel = ADC_CHANNEL_8;
  ch.Rank = ADC_REGULAR_RANK_11;
  HAL_ADC_ConfigChannel(&hadc1, &ch);

  // Slot 12 – CV_ADC_RESONATOR_BRIGHTNESS – PB0 = ADC1_INP9
  ch.Channel = ADC_CHANNEL_9;
  ch.Rank = ADC_REGULAR_RANK_12;
  HAL_ADC_ConfigChannel(&hadc1, &ch);

  // Slot 13 – CV_ADC_SPACE – PB1 = ADC1_INP5
  ch.Channel = ADC_CHANNEL_5;
  ch.Rank = ADC_REGULAR_RANK_13;
  HAL_ADC_ConfigChannel(&hadc1, &ch);

  // ---- Start DMA -----------------------------------------------------------
  HAL_ADC_Start_DMA(&hadc1, reinterpret_cast<uint32_t *>(values_),
                    CV_ADC_CHANNEL_LAST);
}

void CvAdc::DeInit() {
  HAL_ADC_Stop_DMA(&hadc1);
  HAL_ADC_DeInit(&hadc1);
  HAL_DMA_DeInit(&hdma_adc1);
}

void CvAdc::Convert() {
  HAL_ADC_Start_DMA(&hadc1, reinterpret_cast<uint32_t *>(values_),
                    CV_ADC_CHANNEL_LAST);
}

} // namespace elements
