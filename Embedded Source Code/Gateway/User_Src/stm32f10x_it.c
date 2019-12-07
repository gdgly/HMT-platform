/**
  ******************************************************************************
  * @file    ADC/ADC1_DMA/stm32f10x_it.c 
  * @author  MCD Application Team
  * @version V3.5.0
  * @date    08-April-2011
  * @brief   Main Interrupt Service Routines.
  *          This file provides template for all exceptions handler and peripherals
  *          interrupt service routine.
  ******************************************************************************
  * @attention
  *
  * THE PRESENT FIRMWARE WHICH IS FOR GUIDANCE ONLY AIMS AT PROVIDING CUSTOMERS
  * WITH CODING INFORMATION REGARDING THEIR PRODUCTS IN ORDER FOR THEM TO SAVE
  * TIME. AS A RESULT, STMICROELECTRONICS SHALL NOT BE HELD LIABLE FOR ANY
  * DIRECT, INDIRECT OR CONSEQUENTIAL DAMAGES WITH RESPECT TO ANY CLAIMS ARISING
  * FROM THE CONTENT OF SUCH FIRMWARE AND/OR THE USE MADE BY CUSTOMERS OF THE
  * CODING INFORMATION CONTAINED HEREIN IN CONNECTION WITH THEIR PRODUCTS.
  *
  * <h2><center>&copy; COPYRIGHT 2011 STMicroelectronics</center></h2>
  ******************************************************************************
  */ 

/* Includes ------------------------------------------------------------------*/
#include "stm32f10x_it.h"
#include "config.h"


// USB

// Common
volatile u8 time_up = 0;
u8 status_flag = IDLE;
u8 distance_flag = IDLE;
extern u8 Rx_Buff[128];
extern u8 Tx_Buff[128];
extern u8 Sequence_Number;
extern u8 mac[8];
u8 usart_buffer[64];
u8 usart_index;
u8 usart_status;

extern u32 Tx_stp_L;
extern u8 Tx_stp_H;
extern u32 Rx_stp_L;
extern u8 Rx_stp_H;

extern u32 Tx_stp_LT[3];
extern u8 Tx_stp_HT[3];
extern u32 Rx_stp_LT[3];
extern u8 Rx_stp_HT[3];
extern u32 LS_DATA[3];

extern u16 std_noise;
extern	u16 fp_ampl1;
extern	u16 fp_ampl2;
extern	u16 fp_ampl3;
extern	u16 cir_mxg;
extern	u16 rxpacc;
extern	double fppl;
extern	double rxl;
extern const u8 broadcast_addr[8];

extern u32 data[16];
/** @addtogroup STM32F10x_StdPeriph_Examples
  * @{
  */

/** @addtogroup ADC_ADC1_DMA
  * @{
  */ 

/* Private typedef -----------------------------------------------------------*/
/* Private define ------------------------------------------------------------*/
/* Private macro -------------------------------------------------------------*/
/* Private variables ---------------------------------------------------------*/
/* Private function prototypes -----------------------------------------------*/
/* Private functions ---------------------------------------------------------*/

/******************************************************************************/
/*            Cortex-M3 Processor Exceptions Handlers                         */
/******************************************************************************/

/**
  * @brief  This function handles NMI exception.
  * @param  None
  * @retval None
  */
void NMI_Handler(void)
{
}

/**
  * @brief  This function handles Hard Fault exception.
  * @param  None
  * @retval None
  */
void HardFault_Handler(void)
{
  /* Go to infinite loop when Hard Fault exception occurs */
  while (1)
  {
  }
}

/**
  * @brief  This function handles Memory Manage exception.
  * @param  None
  * @retval None
  */
void MemManage_Handler(void)
{
  /* Go to infinite loop when Memory Manage exception occurs */
  while (1)
  {
  }
}

/**
  * @brief  This function handles Bus Fault exception.
  * @param  None
  * @retval None
  */
void BusFault_Handler(void)
{
  /* Go to infinite loop when Bus Fault exception occurs */
  while (1)
  {
  }
}

/**
  * @brief  This function handles Usage Fault exception.
  * @param  None
  * @retval None
  */
void UsageFault_Handler(void)
{
  /* Go to infinite loop when Usage Fault exception occurs */
  while (1)
  {
  }
}

/**
  * @brief  This function handles SVCall exception.
  * @param  None
  * @retval None
  */
void SVC_Handler(void)
{
}

/**
  * @brief  This function handles Debug Monitor exception.
  * @param  None
  * @retval None
  */
void DebugMon_Handler(void)
{
}

/**
  * @brief  This function handles PendSV_Handler exception.
  * @param  None
  * @retval None
  */
void PendSV_Handler(void)
{
}

/**
  * @brief  This function handles SysTick Handler.
  * @param  None
  * @retval None
  */
void SysTick_Handler(void)
{
}

/******************************************************************************/
/*                 STM32F10x Peripherals Interrupt Handlers                   */
/*  Add here the Interrupt Handler for the used peripheral(s) (PPP), for the  */
/*  available peripheral interrupt handler's name please refer to the startup */
/*  file (startup_stm32f10x_xx.s).                                            */
/******************************************************************************/

/**
  * @brief  This function handles PPP interrupt request.
  * @param  None
  * @retval None
  */
/*void PPP_IRQHandler(void)
{
}*/
u16 i=1;
u16 j=1;
int Timstatus=0;
u8 send_buff[20];
u16 size=7;
int Motionstatus;

void EXTI4_IRQHandler(void)
{
	u32 status;
	u8 tmp;
	// enter interrupt
//	while(GPIO_ReadInputDataBit(GPIOA, GPIO_Pin_4)==0)
//	{
//		read_status(&status);
//		if((status&0x00040000)==0x00040000) // LDE Err
//		{
//			to_IDLE();
//			tmp=0x04;
//			// Clear Flag
//			Write_DW1000(0x0F,0x02,&tmp,1);
//			load_LDE();
//			RX_mode_enable();
//		}
//		if((status&0x00000400)==0x00000400) // LDE Success
//		{
//			
//		}
//		if((status&0x0000C000)==0x00008000) // CRC err
//		{
//			tmp=0xF0;
//			Write_DW1000(0x0F,0x01,&tmp,1);
//			to_IDLE();
//			RX_mode_enable();
//			printf("CRC Failed.\r\n");
//		}
//		if((status&0x00006000)==0x00002000)
//		{
//			tmp=0x20;
//			Write_DW1000(0x0F,0x01,&tmp,1);
//			printf("We got a weird status: 0x%08X\r\n",status);
//			// to_IDLE();
//			// RX_mode_enable();
//		}

//		if((status&0x00000080)==0x00000080) // transmit done
//		{
//			tmp=0x80;
//			Write_DW1000(0x0F,0x00,&tmp,1);
//			to_IDLE();
//			RX_mode_enable();			
//		}
//		else if(((status&0x00004000)==0x00004000)||((status&0x00002000)==0x00002000)) // receive done
//		{
//			tmp=0x60;
//			Write_DW1000(0x0F,0x01,&tmp,1);
//			raw_read(Rx_Buff, &size);
//			to_IDLE();
//			RX_mode_enable();
//		}
//	}
			EXTI_ClearITPendingBit(EXTI_Line4);
}
void EXTI1_IRQHandler(void)
{

	uint8_t temp[4];

			 
  delay_ms(10);    //Ïû¶¶	
	if (STM_EVAL_PBGetState(Button_KEY0) == 0x00)		//°´¼ü°´ÏÂ:µÍµçÆ½ÓÐÐ§
	{  
		
		if(i)
		{  Led1_on;
			i=0;
		}
		else		
		{	Led1_off;
			i=1;
		}	
		
	 if(Motionstatus<0x7fffffff)
		{				
			*(int*)temp=Motionstatus;
			send_buff[0]= 0xfa;
			send_buff[1]= 0xfb;
			send_buff[2]= 0x03;
			send_buff[3]= temp[3];
			send_buff[4]= temp[2];
			send_buff[5]= temp[1];
			send_buff[6]= temp[0];
			raw_write(send_buff, &size);
		}

		 Motionstatus++;
	}
		EXTI_ClearITPendingBit(EXTI_Line1);
}
/**
  * @}
  */ 


//Íâ²¿ÖÐ¶Ï15~10·þÎñ³ÌÐò
void EXTI15_10_IRQHandler(void)
{	  
	delay_ms(10);    //Ïû¶¶	
	if (STM_EVAL_PBGetState(Button_KEY1) == 0x00)		//°´¼ü°´ÏÂ:µÍµçÆ½ÓÐÐ§
	{
		if(j)
		{  Led0_on;
			j=0;
		}
		else		
		{	Led0_off;
			j=1;
		}	
		if(Timstatus==0)
		{
			send_buff[0]= 0xfa;
			send_buff[1]= 0xfb;
			send_buff[2]= 0x01;
			send_buff[3]= 0x00;
			send_buff[4]= 0x00;
			send_buff[5]= 0x00;
			send_buff[6]= 0x00;
			
			raw_write(send_buff, &size);  //¿ªÊ  
			Timstatus=1;
		  //TIM_Cmd(TIM3,ENABLE);
	
		}
		else if(Timstatus==1)
		{
			send_buff[0]= 0xfa;
			send_buff[1]= 0xfb;
			send_buff[2]= 0x02;
			send_buff[3]= 0x00;
			send_buff[4]= 0x00;
			send_buff[5]= 0x00;
			send_buff[6]= 0x00;
			Timstatus=0;
			raw_write(send_buff, &size);//½áÊø
		//	TIM_Cmd(TIM3,DISABLE);
		}
	}
	/* Clear the Key Button EXTI line pending bit */  
	EXTI_ClearITPendingBit(BUTTON1_EXTI_LINE);  //Çå³ýEXTI15ÏßÂ·¹ÒÆðÎ»
}

/**
  * @}
  */ 

/******************* (C) COPYRIGHT 2011 STMicroelectronics *****END OF FILE****/
