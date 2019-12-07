/*
sdcard.c file
编写者：周国旭
编译环境：MDK-Lite  Version: 4.23
初版时间: 2015-08-12
功能：
1.sd卡初始化
2.建立SD卡文件写入缓存区
------------------------------------
*/
#include "sdcard.h"
#include "SPI_MSD_Driver.h"
#include "stdio.h"
#include "delay.h"
/**************************????********************************************

*******************************************************************************/
SDWriteBuf SDWriteBuffer;
float sdwrite_buffer[SDWRITE_BUFFER_SIZE];
void SD_Init(void)
{
	  MSD_SPI_Configuration();
//		if( _card_insert() == 0 )
//    {
//	  printf("-- SD card detected OK \r\n");
//    }
//    else
//    {
//      printf("-- Please connect a SD card \r\n");
//      while( _card_insert() != 0 );
//      printf("-- SD card connection detected \r\n");
//	    Delay(0xffffff);
//    }	
    //初始化环形缓冲区
		SDWriteBuffer.Wd_Indx = 0;
		SDWriteBuffer.Rd_Indx = 0;
		SDWriteBuffer.Mask = SDWRITE_BUFFER_SIZE - 1;
		SDWriteBuffer.pbuf = &sdwrite_buffer[0];		
}

float SDWriteBuf_RD(SDWriteBuf *Ringbuf)
{
  float temp;
  temp = Ringbuf->pbuf[Ringbuf->Rd_Indx & Ringbuf->Mask];
  Ringbuf->Rd_Indx++;
  return temp;
}

void SDWriteBuf_WD(SDWriteBuf *Ringbuf,float DataIn)
{ 
  Ringbuf->pbuf[Ringbuf->Wd_Indx & Ringbuf->Mask] = DataIn;
  Ringbuf->Wd_Indx++;
}

uint16_t SDWriteBuf_Cnt(SDWriteBuf *Ringbuf)
{
  return (Ringbuf->Wd_Indx - Ringbuf->Rd_Indx) & Ringbuf->Mask;
}
