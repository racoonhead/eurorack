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
// PCM3060 Codec – STM32H743 SPI2/I2S2 full-duplex HAL driver.
//
// Pin mapping (SPI2, AF5 – same physical pins as original F4 design):
//   PB12 = I2S2_WS  (LRCK)
//   PB13 = I2S2_CK  (BCK)
//   PB14 = I2S2_SDI (DOUT from codec → RX)
//   PB15 = I2S2_SDO (DIN  to  codec → TX)
//   PC6  = I2S2_MCK (SCKI / MCLK to codec, 12.288 MHz)
//           ↑ verify PC6 AF5 = I2S2_MCK in H743 datasheet Table 9;
//             if not, reroute MCLK to PB10 (AF5) or PB2 (AF5).
//
// DMA:
//   DMA1_Stream0: SPI2_RX  (DMAMUX1 request DMA_REQUEST_SPI2_RX)
//   DMA1_Stream1: SPI2_TX  (DMAMUX1 request DMA_REQUEST_SPI2_TX)

#include "elements/drivers/codec.h"

#include <string.h>
#include <stm32h7xx_hal.h>

// ---------------------------------------------------------------------------
// GPIO / peripheral constants
// ---------------------------------------------------------------------------
#define CODEC_I2S_INSTANCE      SPI2

#define CODEC_I2S_GPIO          GPIOB
#define CODEC_I2S_WS_PIN        GPIO_PIN_12   // I2S2_WS  AF5
#define CODEC_I2S_SCK_PIN       GPIO_PIN_13   // I2S2_CK  AF5
#define CODEC_I2S_SDI_PIN       GPIO_PIN_14   // I2S2_SDI AF5  (codec DOUT → H743 RX)
#define CODEC_I2S_SDO_PIN       GPIO_PIN_15   // I2S2_SDO AF5  (H743 TX → codec DIN)
#define CODEC_I2S_GPIO_AF       GPIO_AF5_SPI2

#define CODEC_I2S_MCK_GPIO      GPIOC
#define CODEC_I2S_MCK_PIN       GPIO_PIN_6    // I2S2_MCK AF5 – verify in H743 Table 9

// DMA streams for SPI2
#define CODEC_DMA_RX_STREAM     DMA1_Stream0
#define CODEC_DMA_TX_STREAM     DMA1_Stream1
#define CODEC_DMA_RX_IRQn       DMA1_Stream0_IRQn
#define CODEC_DMA_TX_IRQn       DMA1_Stream1_IRQn

namespace elements {

/* static */
Codec* Codec::instance_;

// ---------------------------------------------------------------------------
// HAL handles (file-scope)
// ---------------------------------------------------------------------------
static I2S_HandleTypeDef  hi2s2;
static DMA_HandleTypeDef  hdma_i2s2_rx;
static DMA_HandleTypeDef  hdma_i2s2_tx;

// ---------------------------------------------------------------------------
bool Codec::InitializeGPIO() {
  __HAL_RCC_GPIOB_CLK_ENABLE();
  __HAL_RCC_GPIOC_CLK_ENABLE();

  GPIO_InitTypeDef gpio = {};
  gpio.Mode      = GPIO_MODE_AF_PP;
  gpio.Speed     = GPIO_SPEED_FREQ_HIGH;
  gpio.Pull      = GPIO_NOPULL;
  gpio.Alternate = CODEC_I2S_GPIO_AF;

  // WS + SCK + SDI + SDO on GPIOB
  gpio.Pin = CODEC_I2S_WS_PIN | CODEC_I2S_SCK_PIN |
             CODEC_I2S_SDI_PIN | CODEC_I2S_SDO_PIN;
  HAL_GPIO_Init(CODEC_I2S_GPIO, &gpio);

  // MCK on GPIOC
  gpio.Pin = CODEC_I2S_MCK_PIN;
  HAL_GPIO_Init(CODEC_I2S_MCK_GPIO, &gpio);

  return true;
}

// ---------------------------------------------------------------------------
bool Codec::InitializeAudioInterface(
    uint32_t sample_rate,
    CodecProtocol protocol,
    CodecFormat format) {

  __HAL_RCC_SPI2_CLK_ENABLE();

  hi2s2.Instance              = CODEC_I2S_INSTANCE;
  hi2s2.Init.Mode             = I2S_MODE_MASTER_TX;   // full-duplex via HAL_I2SEx
  hi2s2.Init.Standard         = protocol;
  hi2s2.Init.DataFormat       = format;
  hi2s2.Init.MCLKOutput       = I2S_MCLKOUTPUT_ENABLE;
  hi2s2.Init.AudioFreq        = sample_rate;
  hi2s2.Init.CPOL             = I2S_CPOL_LOW;
  hi2s2.Init.FirstBit         = I2S_FIRSTBIT_MSB;
  hi2s2.Init.WSInversion      = I2S_WS_INVERSION_DISABLE;
  hi2s2.Init.IOSwap           = I2S_IO_SWAP_DISABLE;
  hi2s2.Init.Data24BitAlignment = I2S_DATA_24BIT_ALIGNMENT_RIGHT;
  hi2s2.Init.FifoThreshold    = I2S_FIFO_THRESHOLD_01DATA;
  hi2s2.Init.MasterKeepIOState = I2S_MASTER_KEEP_IO_STATE_DISABLE;
  hi2s2.Init.SlaveExtendedClockDetection = I2S_SLAVE_EXTENDED_CLOCK_DETECTION_DISABLE;

  if (HAL_I2S_Init(&hi2s2) != HAL_OK) {
    return false;
  }
  return true;
}

// ---------------------------------------------------------------------------
bool Codec::InitializeDMA() {
  __HAL_RCC_DMA1_CLK_ENABLE();

  // --- RX DMA (SPI2 → memory) ---
  hdma_i2s2_rx.Instance                  = CODEC_DMA_RX_STREAM;
  hdma_i2s2_rx.Init.Request              = DMA_REQUEST_SPI2_RX;
  hdma_i2s2_rx.Init.Direction            = DMA_PERIPH_TO_MEMORY;
  hdma_i2s2_rx.Init.PeriphInc            = DMA_PINC_DISABLE;
  hdma_i2s2_rx.Init.MemInc               = DMA_MINC_ENABLE;
  hdma_i2s2_rx.Init.PeriphDataAlignment  = DMA_PDATAALIGN_HALFWORD;
  hdma_i2s2_rx.Init.MemDataAlignment     = DMA_MDATAALIGN_HALFWORD;
  hdma_i2s2_rx.Init.Mode                 = DMA_CIRCULAR;
  hdma_i2s2_rx.Init.Priority             = DMA_PRIORITY_HIGH;
  hdma_i2s2_rx.Init.FIFOMode             = DMA_FIFOMODE_DISABLE;
  HAL_DMA_Init(&hdma_i2s2_rx);
  __HAL_LINKDMA(&hi2s2, hdmarx, hdma_i2s2_rx);

  // --- TX DMA (memory → SPI2) ---
  hdma_i2s2_tx.Instance                  = CODEC_DMA_TX_STREAM;
  hdma_i2s2_tx.Init.Request              = DMA_REQUEST_SPI2_TX;
  hdma_i2s2_tx.Init.Direction            = DMA_MEMORY_TO_PERIPH;
  hdma_i2s2_tx.Init.PeriphInc            = DMA_PINC_DISABLE;
  hdma_i2s2_tx.Init.MemInc               = DMA_MINC_ENABLE;
  hdma_i2s2_tx.Init.PeriphDataAlignment  = DMA_PDATAALIGN_HALFWORD;
  hdma_i2s2_tx.Init.MemDataAlignment     = DMA_MDATAALIGN_HALFWORD;
  hdma_i2s2_tx.Init.Mode                 = DMA_CIRCULAR;
  hdma_i2s2_tx.Init.Priority             = DMA_PRIORITY_HIGH;
  hdma_i2s2_tx.Init.FIFOMode             = DMA_FIFOMODE_DISABLE;
  HAL_DMA_Init(&hdma_i2s2_tx);
  __HAL_LINKDMA(&hi2s2, hdmatx, hdma_i2s2_tx);

  // Enable DMA IRQs (RX drives audio callback; TX just keeps the buffer flowing)
  HAL_NVIC_SetPriority(CODEC_DMA_RX_IRQn, 0, 0);
  NVIC_EnableIRQ(CODEC_DMA_RX_IRQn);
  HAL_NVIC_SetPriority(CODEC_DMA_TX_IRQn, 0, 0);
  NVIC_EnableIRQ(CODEC_DMA_TX_IRQn);

  return true;
}

// ---------------------------------------------------------------------------
bool Codec::Init(
    uint32_t sample_rate,
    CodecProtocol protocol,
    CodecFormat format) {

  rx_buffer_.Init();
  tx_buffer_.Init();

  Frame s;
  s.l = s.r = 0;
  for (size_t i = 0; i < rx_buffer_.capacity() >> 1; ++i) {
    rx_buffer_.Overwrite(s);
    tx_buffer_.Overwrite(s);
  }

  instance_ = this;
  callback_ = NULL;

  // PCM3060: purely hardware-configured, no I2C/SPI register init needed.
  return InitializeGPIO() &&
         InitializeAudioInterface(sample_rate, protocol, format) &&
         InitializeDMA();
}

// ---------------------------------------------------------------------------
bool Codec::Start(FillBufferCallback callback) {
  callback_    = callback;
  client_tx_   = NULL;
  client_rx_   = NULL;
  transmitted_ = 0;
  processed_   = 0;

  // DMA buffer size = kAudioChunkSize frames * 2 (stereo) * 2 (double buffer)
  // Expressed in halfwords (each Frame = 2 × short = 2 halfwords).
  const uint16_t dma_size = kAudioChunkSize * 2 * 2; // halfwords

  // HAL_I2SEx_TransmitReceive_DMA starts full-duplex TX + RX simultaneously.
  HAL_I2SEx_TransmitReceive_DMA(
      &hi2s2,
      reinterpret_cast<uint16_t*>(tx_dma_buffer_),
      reinterpret_cast<uint16_t*>(rx_dma_buffer_),
      dma_size);

  return true;
}

// ---------------------------------------------------------------------------
void Codec::Stop() {
  HAL_I2S_DMAStop(&hi2s2);
}

// ---------------------------------------------------------------------------
void Codec::Fill(size_t offset) {
  if (kNumFIFOChunks) {
    rx_buffer_.Overwrite(&rx_dma_buffer_[offset], kAudioChunkSize);
    tx_buffer_.ImmediateRead(&tx_dma_buffer_[offset], kAudioChunkSize);
  } else if (callback_) {
    (*callback_)(
        &rx_dma_buffer_[offset],
        &tx_dma_buffer_[offset],
        kAudioChunkSize);
  } else {
    ++transmitted_;
    client_rx_ = &rx_dma_buffer_[offset];
    client_tx_ = &tx_dma_buffer_[offset];
  }
}

}  // namespace elements

// ---------------------------------------------------------------------------
// HAL callback overrides (weak symbols in stm32h7xx_hal_i2s_ex.c)
// Called from DMA IRQ via HAL_DMA_IRQHandler → HAL_I2SEx_TxRx*Callback.
// ---------------------------------------------------------------------------
extern "C" {

void HAL_I2SEx_TxRxHalfCpltCallback(I2S_HandleTypeDef* hi2s) {
  if (hi2s->Instance == SPI2) {
    elements::Codec::GetInstance()->Fill(0);              // first half ready
  }
}

void HAL_I2SEx_TxRxCpltCallback(I2S_HandleTypeDef* hi2s) {
  if (hi2s->Instance == SPI2) {
    elements::Codec::GetInstance()->Fill(elements::kAudioChunkSize); // second half
  }
}

// DMA IRQ handlers – forward to HAL.
void DMA1_Stream0_IRQHandler(void) {   // SPI2_RX
  HAL_DMA_IRQHandler(&hdma_i2s2_rx);
}

void DMA1_Stream1_IRQHandler(void) {   // SPI2_TX
  HAL_DMA_IRQHandler(&hdma_i2s2_tx);
}

}  // extern "C"
