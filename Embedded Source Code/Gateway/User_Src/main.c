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
void EXTI_init(void);
void TIM_GPIO_Init(void);
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
	delay_init(SysClock);         //滴答延时初始化 
  UART1_init(SysClock,115200); 	//串口1初始化
  SPI2_init()	;
	
  NVIC_INIT();	                //中断初始化

	LedInit();		                //IO初始化 
	
	STM_EVAL_PBInit(Button_KEY0, Mode_EXTI);			//设置按键外部中断方式
	STM_EVAL_PBInit(Button_KEY1, Mode_EXTI);			//设置按键外部中断方式
	
 	EXTI_init();

  DW1000_init();
  TIM3_Init(SysClock*10,60000);	    //定时器3初始化 500ms
  RX_mode_enable();	 

  while (1)                    
  {
		delay_ms(1000);	
	}
}

/*
外部中断初始化，PA1
*/
void EXTI_init(void)
{
	NVIC_InitTypeDef NVIC_InitStructure;
	GPIO_InitTypeDef GPIO_InitStructure;
	EXTI_InitTypeDef EXTI_InitStructure;

	NVIC_PriorityGroupConfig(NVIC_PriorityGroup_4);
	NVIC_InitStructure.NVIC_IRQChannel=EXTI4_IRQn;
	NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 1;
	NVIC_InitStructure.NVIC_IRQChannelSubPriority = 1;
	NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
	NVIC_Init(&NVIC_InitStructure);

	RCC_APB2PeriphClockCmd( RCC_APB2Periph_GPIOA | RCC_APB2Periph_AFIO, ENABLE);
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_4;
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IPD;
	GPIO_Init(GPIOA,&GPIO_InitStructure);
	GPIO_ResetBits(GPIOA,GPIO_Pin_4);

	EXTI_ClearITPendingBit(EXTI_Line4);
	GPIO_EXTILineConfig(GPIO_PortSourceGPIOA, GPIO_PinSource4);
	EXTI_InitStructure.EXTI_Line = EXTI_Line4;
	EXTI_InitStructure.EXTI_Mode = EXTI_Mode_Interrupt;
	EXTI_InitStructure.EXTI_Trigger = EXTI_Trigger_Falling;
	EXTI_InitStructure.EXTI_LineCmd = ENABLE;
	EXTI_Init(&EXTI_InitStructure);
}

void TIM_GPIO_Init(void)
{
 GPIO_InitTypeDef  GPIO_InitStructure;
 	
 RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);	 //使能PA端口时钟
	
 GPIO_InitStructure.GPIO_Pin = GPIO_Pin_3;				 //PA.3 端口配置
 GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP; 		 //推挽输出
 GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
 GPIO_Init(GPIOA, &GPIO_InitStructure);
 GPIO_ResetBits(GPIOA,GPIO_Pin_3);						 //PA.3 输出高

}
