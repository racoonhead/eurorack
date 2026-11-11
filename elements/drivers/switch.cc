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
// Driver for front panel switches – STM32H743 HAL GPIO.
//   PC13: SW_PLAY / SW_GATE (active-low, pull-up)
//   PA9:  SW_MODEL_1 (active-high 3.3V, pull-down)
//   PE9:  SW_MODEL_2 (active-high 3.3V, pull-down)

#include "elements/drivers/switch.h"

#include <stm32h7xx_hal.h>
#include <algorithm>

namespace elements {

using namespace std;

void Switches::Init() {
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOC_CLK_ENABLE();
  __HAL_RCC_GPIOE_CLK_ENABLE();

  GPIO_InitTypeDef gpio = {};

  // PC13: active-low (SW_GATE) with pull-up
  gpio.Pin   = GPIO_PIN_13;
  gpio.Mode  = GPIO_MODE_INPUT;
  gpio.Speed = GPIO_SPEED_FREQ_LOW;
  gpio.Pull  = GPIO_PULLUP;
  HAL_GPIO_Init(GPIOC, &gpio);

  // PA9: active-high (3.3V) with pull-down
  gpio.Pin   = GPIO_PIN_9;
  gpio.Mode  = GPIO_MODE_INPUT;
  gpio.Speed = GPIO_SPEED_FREQ_LOW;
  gpio.Pull  = GPIO_PULLDOWN;
  HAL_GPIO_Init(GPIOA, &gpio);

  // PE9: active-high (3.3V) with pull-down
  gpio.Pin   = GPIO_PIN_9;
  gpio.Mode  = GPIO_MODE_INPUT;
  gpio.Speed = GPIO_SPEED_FREQ_LOW;
  gpio.Pull  = GPIO_PULLDOWN;
  HAL_GPIO_Init(GPIOE, &gpio);

  switch_state_[0] = 0xff;
  switch_state_[1] = 0xff;
  switch_state_[2] = 0xff;
}

void Switches::Debounce() {
  // PC13: active-low (0 when pressed -> 0 in state bit)
  switch_state_[0] = (switch_state_[0] << 1) |
      (HAL_GPIO_ReadPin(GPIOC, GPIO_PIN_13) == GPIO_PIN_SET ? 1 : 0);

  // PA9: active-high (1 when pressed -> 0 in state bit when pressed)
  switch_state_[1] = (switch_state_[1] << 1) |
      (HAL_GPIO_ReadPin(GPIOA, GPIO_PIN_9) == GPIO_PIN_SET ? 0 : 1);

  // PE9: active-high (1 when pressed -> 0 in state bit when pressed)
  switch_state_[2] = (switch_state_[2] << 1) |
      (HAL_GPIO_ReadPin(GPIOE, GPIO_PIN_9) == GPIO_PIN_SET ? 0 : 1);
}

}  // namespace elements
