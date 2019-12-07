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
编写者：小马  (Camel)
作者E-mail：375836945@qq.com
编译环境：MDK-Lite  Version: 4.23
初版时间: 2014-01-28
功能：
1.飞机硬件初始化
2.参数初始化
3.定时器开
4.等待中断到来
------------------------------------
*/

#include "config.h"        //包含所有的驱动头文件
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
              飞控主函数入口
功能：                                        
1.初始化各个硬件
2.初始化系统参数
3.开定时器4等待数据中断到来
4.开定时器3串口广播实时姿态以及相关信息
********************************************/
int main(void)
{
  SystemClock_HSE(9);           //系统时钟初始化，时钟源外部晶振HSE

  UART1_init(SysClock,115200); 	//串口1初始化
	Initial_System_Timer();

  NVIC_INIT();	                //中断初始化
  EXTI_init();
	
  LedInit();		                //IO初始化 
  delay_init(SysClock);         //滴答延时初始化 
  IIC_Init();                   //IIC初始化
	SPI2_init();
	
	MPU6050_DMP_Initialize(0);


  HMC5883L_SetUp(0);           //初始化磁力计HMC5883L

	MS561101BA_init();			   	 //初始化气压
	
  DW1000_init();               //UWB初始化
  TIM3_Init(SysClock*10,6000);	    //定时器3初始化 50ms
  SD_Init();                   //SD卡初始化
//	
	
	to_IDLE();
	f_mount(0,&fs);
  //TIM_GPIO_Init(); //test
  //  TIM4_Init(SysClock,1000);	    //定时器4初始化，定时采样传感器数据，更新PID输出，定时器定时基石为1us，PID更新周期为4ms，所以姿态更新频率 为250Hz    
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
外部中断初始化，PB11
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
//	 RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);	 //使能PA端口时钟
//		
//	 GPIO_InitStructure.GPIO_Pin = GPIO_Pin_3;				 //LED0-->PA.8 端口配置
//	 GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP; 		 //推挽输出
//	 GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
//	 GPIO_Init(GPIOA, &GPIO_InitStructure);
//	 GPIO_ResetBits(GPIOA,GPIO_Pin_3);						 //PA.8 输出高
//}
