// Copyright 2012 Emilie Gillet.
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
// Driver for the debug (timing) pin (STM32H743).
// Note: PA9 is used for SWITCH_MODEL_1 on Elements v0.4, so DebugPin is a
// safe no-op unless explicitly mapped to a dedicated test pad.

#ifndef ELEMENTS_DRIVERS_DEBUG_PIN_H_
#define ELEMENTS_DRIVERS_DEBUG_PIN_H_

#include "stmlib/stmlib.h"

#ifndef TEST
#include <stm32h7xx_hal.h>
#endif

namespace elements {

class DebugPin {
 public:
  DebugPin() { }
  ~DebugPin() { }
  static void Init() { }
  static inline void High() { }
  static inline void Low() { }
 private:
  DISALLOW_COPY_AND_ASSIGN(DebugPin);
};

#define TIC DebugPin::High();
#define TOC DebugPin::Low();

}  // namespace elements

#endif  // ELEMENTS_DRIVERS_DEBUG_PIN_H_
