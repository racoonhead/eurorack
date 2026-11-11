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

#ifndef ELEMENTS_DRIVERS_SWITCH_H_
#define ELEMENTS_DRIVERS_SWITCH_H_

#include "stmlib/stmlib.h"

#include <stm32h7xx_hal.h>

namespace elements {

enum SwitchIndex {
  SWITCH_PLAY,      // PC13 (SW_GATE)
  SWITCH_MODEL_1,   // PA9
  SWITCH_MODEL_2,   // PE9
  SWITCH_LAST
};

class Switches {
 public:
  Switches() { }
  ~Switches() { }
  
  void Init();
  void Debounce();
  
  inline bool released(size_t index) const {
    return switch_state_[index] == 0x7f;
  }
  
  inline bool just_pressed(size_t index) const {
    return switch_state_[index] == 0x80;
  }

  inline bool pressed(size_t index) const {
    return switch_state_[index] == 0x00;
  }

  // Compatibility methods for default switch (SWITCH_PLAY)
  inline bool released() const { return released(SWITCH_PLAY); }
  inline bool just_pressed() const { return just_pressed(SWITCH_PLAY); }
  inline bool pressed() const { return pressed(SWITCH_PLAY); }

 private:
  uint8_t switch_state_[3];
  
  DISALLOW_COPY_AND_ASSIGN(Switches);
};

typedef Switches Switch;

}  // namespace elements

#endif  // ELEMENTS_DRIVERS_SWITCH_H_
