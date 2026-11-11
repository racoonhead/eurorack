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
// PCM3060 Codec support – STM32H743 SPI2/I2S2 full-duplex HAL driver.

#ifndef ELEMENTS_DRIVERS_CODEC_H_
#define ELEMENTS_DRIVERS_CODEC_H_

#include <stm32h7xx_hal.h>

#include "stmlib/stmlib.h"
#include "stmlib/utils/ring_buffer.h"

namespace elements {

enum CodecProtocol {
  CODEC_PROTOCOL_PHILIPS  = I2S_STANDARD_PHILIPS,
  CODEC_PROTOCOL_MSB_FIRST = I2S_STANDARD_MSB,
  CODEC_PROTOCOL_LSB_FIRST = I2S_STANDARD_LSB
};

enum CodecFormat {
  CODEC_FORMAT_16_BIT = I2S_DATAFORMAT_16B,
  CODEC_FORMAT_24_BIT = I2S_DATAFORMAT_24B,
  CODEC_FORMAT_32_BIT = I2S_DATAFORMAT_32B
};

// PCM3060: hardware-only codec, no SPI/I2C register access needed.

// Size of one audio chunk in stereo frames (samples). DMA buffer = 2 chunks.
const size_t kAudioChunkSize = 16;

// Extra FIFO chunks (0 = naive double-buffering).
const size_t kNumFIFOChunks = 0;

class Codec {
 public:
  Codec() { }
  ~Codec() { }
  
  typedef struct { short l; short r; } Frame;
  typedef void (*FillBufferCallback)(Frame* rx, Frame* tx, size_t size);
  
  bool Init(uint32_t sample_rate, CodecProtocol protocol, CodecFormat format);
  
  bool Start() {
    return Start(NULL);
  }
  
  bool Start(FillBufferCallback callback);
  void Stop();
  
  void Fill(size_t offset);

  static Codec* GetInstance() { return instance_; }
  
  inline bool available() const {
    return transmitted_ != processed_;
  }
  
  inline size_t Grab(Frame** input, Frame** output) {
    ++processed_;
    *input = client_rx_;
    *output = client_tx_;
    return kAudioChunkSize;
  }

  size_t writable() const { return tx_buffer_.writable(); }
  size_t readable() const { return rx_buffer_.readable(); }
  void ImmediateRead(Frame* destination, size_t size) {
    rx_buffer_.ImmediateRead(destination, size);
  }
  
  void Overwrite(Frame* source, size_t size) {
    tx_buffer_.Overwrite(source, size);
  }
  
 private:
  bool InitializeGPIO();
  bool InitializeAudioInterface(uint32_t, CodecProtocol, CodecFormat);
  bool InitializeDMA();
  
  static Codec* instance_;
  
  size_t transmitted_;
  size_t processed_;
  Frame* client_tx_;
  Frame* client_rx_;
  
  FillBufferCallback callback_;
  
  // DMA buffer placed in D2 SRAM3 (.dma section at 0x30040000) for DMA1 access on H743.
  static Frame tx_dma_buffer_[kAudioChunkSize * 2] __attribute__((section (".dma")));
  static Frame rx_dma_buffer_[kAudioChunkSize * 2] __attribute__((section (".dma")));
  stmlib::RingBuffer<Frame, kAudioChunkSize * kNumFIFOChunks> rx_buffer_;
  stmlib::RingBuffer<Frame, kAudioChunkSize * kNumFIFOChunks> tx_buffer_;

  DISALLOW_COPY_AND_ASSIGN(Codec);
};

}  // namespace elements

#endif  // ELEMENTS_DRIVERS_CODEC_H_
