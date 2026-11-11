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
// System level initialization – STM32H743.

#include "elements/drivers/system.h"

#include <stm32h7xx_hal.h>

namespace elements {

void System::Init(bool application) {
  if (application) {
    SCB->VTOR = 0x08020000UL;
  }

  // Enable D2/D3 SRAM clocks (required for .dma in SRAM3 and .ramd3 in SRAM4)
  __HAL_RCC_D2SRAM1_CLK_ENABLE();
  __HAL_RCC_D2SRAM2_CLK_ENABLE();
  __HAL_RCC_D2SRAM3_CLK_ENABLE();
  __HAL_RCC_D3SRAM1_CLKAM_ENABLE();

  // Configure uncached MPU region for RAM_D2_DMA (SRAM3 @ 0x30040000, 32 KB)
  HAL_MPU_Disable();
  MPU_Region_InitTypeDef mpu_init = {};
  mpu_init.Enable           = MPU_REGION_ENABLE;
  mpu_init.Number           = MPU_REGION_NUMBER0;
  mpu_init.BaseAddress      = 0x30040000;
  mpu_init.Size             = MPU_REGION_SIZE_32KB;
  mpu_init.SubRegionDisable = 0x0;
  mpu_init.TypeExtField     = MPU_TEX_LEVEL0;
  mpu_init.AccessPermission = MPU_REGION_FULL_ACCESS;
  mpu_init.DisableExec      = MPU_INSTRUCTION_ACCESS_ENABLE;
  mpu_init.IsShareable      = MPU_ACCESS_SHAREABLE;
  mpu_init.IsCacheable      = MPU_ACCESS_NOT_CACHEABLE;
  mpu_init.IsBufferable     = MPU_ACCESS_NOT_BUFFERABLE;
  HAL_MPU_ConfigRegion(&mpu_init);
  HAL_MPU_Enable(MPU_HFNMI_PRIVDEF);

  SCB_EnableICache();
  SCB_EnableDCache();

  HAL_Init();

  // -------------------------------------------------------------------------
  // Power: voltage scaling VOS0 required for 480 MHz operation.
  // -------------------------------------------------------------------------
  HAL_PWREx_ConfigSupply(PWR_LDO_SUPPLY);
  __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE0);
  while (!__HAL_PWR_GET_FLAG(PWR_FLAG_VOSRDY)) {}

  // -------------------------------------------------------------------------
  // PLL1: 8 MHz HSE → 480 MHz CPU
  //   VCO  = HSE / PLLM * PLLN = 8 / 1 * 60 = 480 MHz
  //   SYSCLK = VCO / PLLP = 480 / 1 = 480 MHz
  //   PLLQ   = 480 / 10  = 48 MHz  (USB / SDMMC)
  // -------------------------------------------------------------------------
  RCC_OscInitTypeDef osc_init = {};
  osc_init.OscillatorType      = RCC_OSCILLATORTYPE_HSE;
  osc_init.HSEState            = RCC_HSE_ON;
  osc_init.PLL.PLLState        = RCC_PLL_ON;
  osc_init.PLL.PLLSource       = RCC_PLLSOURCE_HSE;
  osc_init.PLL.PLLM            = 1;
  osc_init.PLL.PLLN            = 60;
  osc_init.PLL.PLLP            = 1;   // → 480 MHz SYSCLK
  osc_init.PLL.PLLQ            = 10;  // → 48 MHz
  osc_init.PLL.PLLR            = 10;  // → 48 MHz
  osc_init.PLL.PLLRGE          = RCC_PLL1VCIRANGE_3;  // 8–16 MHz VCO input
  osc_init.PLL.PLLVCOSEL       = RCC_PLL1VCOWIDE;     // 192–960 MHz VCO range
  osc_init.PLL.PLLFRACN        = 0;
  HAL_RCC_OscConfig(&osc_init);

  // -------------------------------------------------------------------------
  // Bus clocks:
  //   D1: SYSCLK/1 = 480 MHz (CPU)
  //   HCLK:  480 / 2 = 240 MHz (AXI, AHB1/2/3)
  //   APB1..4: 240 / 2 = 120 MHz
  // Flash latency 4 WS + programming delay 2 for 240 MHz AXI @ VOS0.
  // -------------------------------------------------------------------------
  RCC_ClkInitTypeDef clk_init = {};
  clk_init.ClockType      = RCC_CLOCKTYPE_SYSCLK | RCC_CLOCKTYPE_HCLK  |
                             RCC_CLOCKTYPE_D1PCLK1 | RCC_CLOCKTYPE_PCLK1 |
                             RCC_CLOCKTYPE_PCLK2  | RCC_CLOCKTYPE_D3PCLK1;
  clk_init.SYSCLKSource   = RCC_SYSCLKSOURCE_PLLCLK;
  clk_init.SYSCLKDivider  = RCC_SYSCLK_DIV1;   // D1 domain: 480 MHz
  clk_init.AHBCLKDivider  = RCC_HCLK_DIV2;     // HCLK = 240 MHz
  clk_init.APB3CLKDivider = RCC_APB3_DIV2;      // 120 MHz
  clk_init.APB1CLKDivider = RCC_APB1_DIV2;      // 120 MHz
  clk_init.APB2CLKDivider = RCC_APB2_DIV2;      // 120 MHz
  clk_init.APB4CLKDivider = RCC_APB4_DIV2;      // 120 MHz
  HAL_RCC_ClockConfig(&clk_init, FLASH_LATENCY_4);

  // -------------------------------------------------------------------------
  // PLL3: audio I2S clock (SPI2) = 12.288 MHz for 48 kHz / 256x MCLK.
  //   VCO input  = HSE / PLL3M  = 8 / 5 = 1.6 MHz
  //   VCO output = 1.6 * PLL3N  = 1.6 * 192 = 307.2 MHz
  //   PLL3P      = 307.2 / 25   = 12.288 MHz  ✓
  //
  // ADC clock source: PER_CK = HSE = 8 MHz (well within 80 MHz limit).
  // -------------------------------------------------------------------------
  RCC_PeriphCLKInitTypeDef periph_clk = {};
  periph_clk.PeriphClockSelection  = RCC_PERIPHCLK_SPI2 |
                                     RCC_PERIPHCLK_SPI3 |
                                     RCC_PERIPHCLK_ADC;
  periph_clk.Spi123ClockSelection  = RCC_SPI123CLKSOURCE_PLL3;
  periph_clk.AdcClockSelection     = RCC_ADCCLKSOURCE_CLKP; // PER_CK = HSE

  periph_clk.PLL3.PLL3M     = 5;
  periph_clk.PLL3.PLL3N     = 192;
  periph_clk.PLL3.PLL3P     = 25;   // → 12.288 MHz (I2S MCLK / audio clk)
  periph_clk.PLL3.PLL3Q     = 25;
  periph_clk.PLL3.PLL3R     = 25;
  periph_clk.PLL3.PLL3RGE   = RCC_PLL3VCIRANGE_0;   // 1–2 MHz input (1.6 MHz)
  periph_clk.PLL3.PLL3VCOSEL = RCC_PLL3VCOMEDIUM;   // 150–420 MHz (307.2 MHz)
  periph_clk.PLL3.PLL3FRACN  = 0;
  HAL_RCCEx_PeriphCLKConfig(&periph_clk);

  // -------------------------------------------------------------------------
  // Bootloader compatibility: move vector table to application offset.
  // Matches stmlib H7 bootloader convention (128 KB Sector 1 = 0x08020000).
  // -------------------------------------------------------------------------
  if (application) {
    SCB->VTOR = 0x08020000UL;
  }
}

void System::StartTimers() {
  // SysTick ticks at HCLK = 240 MHz → 240 000 ticks per ms.
  HAL_SYSTICK_Config(HAL_RCC_GetHCLKFreq() / 1000);
}

}  // namespace elements
