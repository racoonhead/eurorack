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
// Driver for the 3 LEDs – STM32H743 HAL TIM1 PWM.
//
//   PC7  = GPIO output (GATE LED, digital on/off)
//   PA8  = TIM1_CH1 AF1 (EXCITER LED, PWM)
//   PA11 = TIM1_CH4 AF1 (RESONATOR LED, PWM)
//
// TIM1 runs from APB2 timer clock = 240 MHz (since APB2 divider = 2,
// timer clock doubles: 120 MHz × 2 = 240 MHz).
// Prescaler = 6, Period = 255 → PWM freq ≈ 240 000 000 / (7 × 256) ≈ 133 kHz.

#include "elements/drivers/leds.h"

#include <algorithm>
#include <stm32h7xx_hal.h>

namespace elements {

using namespace std;

static TIM_HandleTypeDef htim1_leds;

void Leds::Init() {
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOC_CLK_ENABLE();
  __HAL_RCC_GPIOE_CLK_ENABLE();
  __HAL_RCC_TIM1_CLK_ENABLE();

  GPIO_InitTypeDef gpio = {};

  // PE6: digital output (GATE LED).
  gpio.Pin   = GPIO_PIN_6;
  gpio.Mode  = GPIO_MODE_OUTPUT_PP;
  gpio.Speed = GPIO_SPEED_FREQ_LOW;
  gpio.Pull  = GPIO_NOPULL;
  HAL_GPIO_Init(GPIOE, &gpio);

  // PA8 (CH1) + PA11 (CH4): TIM1 alternate function.
  gpio.Pin       = GPIO_PIN_8 | GPIO_PIN_11;
  gpio.Mode      = GPIO_MODE_AF_PP;
  gpio.Speed     = GPIO_SPEED_FREQ_LOW;
  gpio.Alternate = GPIO_AF1_TIM1;
  HAL_GPIO_Init(GPIOA, &gpio);

  // TIM1 base: prescaler=6, period=255 (8-bit PWM).
  htim1_leds.Instance               = TIM1;
  htim1_leds.Init.Prescaler         = 6;
  htim1_leds.Init.CounterMode       = TIM_COUNTERMODE_UP;
  htim1_leds.Init.Period            = 255;
  htim1_leds.Init.ClockDivision     = TIM_CLOCKDIVISION_DIV1;
  htim1_leds.Init.RepetitionCounter = 0;
  htim1_leds.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_ENABLE;
  HAL_TIM_PWM_Init(&htim1_leds);

  TIM_OC_InitTypeDef oc = {};
  oc.OCMode      = TIM_OCMODE_PWM1;
  oc.Pulse       = 0;
  oc.OCPolarity  = TIM_OCPOLARITY_HIGH;
  oc.OCNPolarity = TIM_OCNPOLARITY_HIGH;
  oc.OCFastMode  = TIM_OCFAST_DISABLE;
  oc.OCIdleState = TIM_OCIDLESTATE_RESET;
  oc.OCNIdleState = TIM_OCNIDLESTATE_RESET;

  HAL_TIM_PWM_ConfigChannel(&htim1_leds, &oc, TIM_CHANNEL_1);
  HAL_TIM_PWM_ConfigChannel(&htim1_leds, &oc, TIM_CHANNEL_4);

  HAL_TIM_PWM_Start(&htim1_leds, TIM_CHANNEL_1);
  HAL_TIM_PWM_Start(&htim1_leds, TIM_CHANNEL_4);

  // Enable main output (required for advanced timers TIM1/TIM8 on H743).
  __HAL_TIM_MOE_ENABLE(&htim1_leds);
}

void Leds::Write() {
  // Direct register write for minimal latency (same registers as F4).
  HAL_GPIO_WritePin(GPIOE, GPIO_PIN_6,
      gate_ ? GPIO_PIN_SET : GPIO_PIN_RESET);
  TIM1->CCR1 = exciter_;
  TIM1->CCR4 = resonator_;
}

}  // namespace elements
