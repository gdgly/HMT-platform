/*    
      ____                      _____                  +---+
     / ___\                     / __ \                 | R |
    / /                        / /_/ /                 +---+
   / /   ________  ____  ___  / ____/___  ____  __   __
  / /  / ___/ __ `/_  / / _ \/ /   / __ \/ _  \/ /  / /
 / /__/ /  / /_/ / / /_/  __/ /   / /_/ / / / / /__/ /
 \___/_/   \__,_/ /___/\___/_/    \___ /_/ /_/____  /
                                                 / /
                                            ____/ /
                                           /_____/
main.c file
��д�ߣ�С��  (Camel)
����E-mail��375836945@qq.com
���뻷����MDK-Lite  Version: 4.23
����ʱ��: 2014-01-28
���ܣ�
1.�ɻ�Ӳ����ʼ��
2.������ʼ��
3.��ʱ����
4.�ȴ��жϵ���
------------------------------------
*/

#include "config.h"        //�������е�����ͷ�ļ�
void timer_init(void);
/* Private variables ---------------------------------------------------------*/
FATFS fs;         /* Work area (file system object) for logical drive */
/* Private variables ---------------------------------------------------------*/
FIL fsrc;         /* file objects */   
FRESULT res;
UINT br;
float SDWritetemp;
//void TIM_GPIO_Init(void);
void EXTI_init(void);
extern SDWriteBuf SDWriteBuffer;

u16 sze =7;
u8 buff[20];
/********************************************
              �ɿ����������
���ܣ�                                        
1.��ʼ������Ӳ��
2.��ʼ��ϵͳ����
3.����ʱ��4�ȴ������жϵ���
4.����ʱ��3���ڹ㲥ʵʱ��̬�Լ������Ϣ
********************************************/
int main(void)
{
  SystemClock_HSE(9);           //ϵͳʱ�ӳ�ʼ����ʱ��Դ�ⲿ����HSE

  UART1_init(SysClock,115200); 	//����1��ʼ��
	Initial_System_Timer();

  NVIC_INIT();	                //�жϳ�ʼ��
  EXTI_init();
	
  LedInit();		                //IO��ʼ�� 
  delay_init(SysClock);         //�δ���ʱ��ʼ�� 
  IIC_Init();                   //IIC��ʼ��
	SPI2_init();
	
	MPU6050_DMP_Initialize(0);


  HMC5883L_SetUp(0);           //��ʼ��������HMC5883L

	MS561101BA_init();			   	 //��ʼ����ѹ
	
  DW1000_init();               //UWB��ʼ��
  TIM3_Init(SysClock*10,6000);	    //��ʱ��3��ʼ�� 50ms
  SD_Init();                   //SD����ʼ��
//	
	
	to_IDLE();
	f_mount(0,&fs);
  //TIM_GPIO_Init(); //test
  //  TIM4_Init(SysClock,1000);	    //��ʱ��4��ʼ������ʱ�������������ݣ�����PID�������ʱ����ʱ��ʯΪ1us��PID��������Ϊ4ms��������̬����Ƶ�� Ϊ250Hz    
  //TIM_Cmd(TIM3,ENABLE);
	res = f_open( &fsrc , "0:/test.TXT" , FA_CREATE_NEW);
	if (res==FR_EXIST)	
	{
		f_unlink("0:/test.TXT");
    res = f_open( &fsrc , "0:/test.TXT" , FA_CREATE_NEW);
	}
	if ( res == FR_OK )
		 RX_mode_enable();
	res = f_open( &fsrc , "0:/test.TXT" , FA_WRITE);

  while (1)                    
 {	
//		if(SDWriteBuf_Cnt(&SDWriteBuffer)!=0)
//		{
//				res = f_open( &fsrc , "0:/test.TXT" , FA_WRITE);
//				if ( res == FR_OK )
//				res = f_lseek(&fsrc, f_size(&fsrc));
//				if ( res == FR_OK )
//				{ 		
//					while(SDWriteBuf_Cnt(&SDWriteBuffer)!=0)
//					{		
//              __set_PRIMASK(1);						
//							SDWritetemp=SDWriteBuf_RD(&SDWriteBuffer);
//							res = f_write(&fsrc, &SDWritetemp, sizeof(SDWritetemp), &br);  
//						  __set_PRIMASK(0);
//					}	
//					f_sync(&fsrc);
//				}
//				else  f_close(&fsrc);
//		}
					while(SDWriteBuf_Cnt(&SDWriteBuffer)!=0)
					{		
              __set_PRIMASK(1);
              if(res != FR_OK)
									TIM_Cmd(TIM3,DISABLE);
							SDWritetemp=SDWriteBuf_RD(&SDWriteBuffer);
							res = f_write(&fsrc, &SDWritetemp, sizeof(SDWritetemp), &br);  
						  __set_PRIMASK(0);
					}	
					f_sync(&fsrc);
  }	
}
/*
�ⲿ�жϳ�ʼ����PB11
*/
void EXTI_init(void)
{
	NVIC_InitTypeDef NVIC_InitStructure;
	GPIO_InitTypeDef GPIO_InitStructure;
	EXTI_InitTypeDef EXTI_InitStructure;

	NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2);
	NVIC_InitStructure.NVIC_IRQChannel=EXTI15_10_IRQn;
	NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 1;
	NVIC_InitStructure.NVIC_IRQChannelSubPriority = 1;
	NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
	NVIC_Init(&NVIC_InitStructure);

	RCC_APB2PeriphClockCmd( RCC_APB2Periph_GPIOB | RCC_APB2Periph_AFIO, ENABLE);
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_11;
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IPD;
	GPIO_Init(GPIOB,&GPIO_InitStructure);
	GPIO_ResetBits(GPIOB,GPIO_Pin_11);

	EXTI_ClearITPendingBit(EXTI_Line11);
	GPIO_EXTILineConfig(GPIO_PortSourceGPIOB, GPIO_PinSource11);
	EXTI_InitStructure.EXTI_Line = EXTI_Line11;
	EXTI_InitStructure.EXTI_Mode = EXTI_Mode_Interrupt;
	EXTI_InitStructure.EXTI_Trigger = EXTI_Trigger_Falling;
	EXTI_InitStructure.EXTI_LineCmd = ENABLE;
	EXTI_Init(&EXTI_InitStructure);
}


//void TIM_GPIO_Init(void)
//{
//	 GPIO_InitTypeDef  GPIO_InitStructure;
//		
//	 RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);	 //ʹ��PA�˿�ʱ��
//		
//	 GPIO_InitStructure.GPIO_Pin = GPIO_Pin_3;				 //LED0-->PA.8 �˿�����
//	 GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP; 		 //�������
//	 GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
//	 GPIO_Init(GPIOA, &GPIO_InitStructure);
//	 GPIO_ResetBits(GPIOA,GPIO_Pin_3);						 //PA.8 �����
//}
