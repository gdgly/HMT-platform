#ifndef __SDCARD_H_
#define __SDCARD_H_

#include "stm32f10x.h"


// SD wirte buffer
#define SDWRITE_BUFFER_SIZE   1024

extern float sdwrite_buffer[SDWRITE_BUFFER_SIZE];

typedef struct 
{
  uint16_t volatile Wd_Indx;
  uint16_t volatile Rd_Indx;
  uint16_t Mask;
  float *pbuf;
}SDWriteBuf;

extern void SD_Init(void);
extern SDWriteBuf SDWriteBuffer;
extern float SDWriteBuf_RD(SDWriteBuf *Ringbuf);
extern void SDWriteBuf_WD(SDWriteBuf *Ringbuf,float DataIn);
extern uint16_t SDWriteBuf_Cnt(SDWriteBuf *Ringbuf);
#endif
