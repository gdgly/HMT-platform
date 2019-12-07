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
led.c file
编写者：小马  (Camel)
作者E-mail：375836945@qq.com
编译环境：MDK-Lite  Version: 4.23
初版时间: 2014-01-28
功能：
1.飞机四个臂上led IO口初始化
2.初始化默认关闭所有LED灯
------------------------------------
*/

#include "Led.h"
#include "UART1.h"
#include "config.h"

/********************************************
              Led初始化函数
功能：
1.配置Led接口IO输出方向
2.关闭所有Led(开机默认方式)
描述：
Led接口：
Led1-->PA11
Led2-->PA8
Led3-->PB1
Led4-->PB3
对应IO=1，灯亮
********************************************/
void LedInit(void)
{
    RCC->APB2ENR|=1<<2;    //使能PORTA时钟	
		RCC->APB2ENR|=1<<5;    //使能PORTD时钟	
		//RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOD, ENABLE);	
	
    RCC->APB2ENR|=1<<0;      //使能复用时钟	   
  
    GPIOA->CRH&=0XFFFFFFF0;  //PA8推挽输出
    GPIOA->CRH|=0X00000003;
    GPIOA->ODR|=1<<8;        //PA8上拉
	
		GPIOD->CRL&=0XFFFFF0FF;  //PD2推挽输出
    GPIOD->CRL|=0X00000300;
    GPIOD->ODR|=1<<2;        //PD2上拉
  
    AFIO->MAPR|=2<<24;      //关闭JATG,千万不能将SWD也关闭，否则芯片作废，亲测!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    Led0_off;Led1_off;
}
GPIO_TypeDef* BUTTON_PORT[BUTTONn] = {BUTTON0_PORT, BUTTON1_PORT, WAKEUP_BUTTON_PORT}; 

const uint16_t BUTTON_PIN[BUTTONn] = {BUTTON0_PIN, BUTTON1_PIN ,WAKEUP_BUTTON_PIN}; 

const uint32_t BUTTON_CLK[BUTTONn] = {BUTTON0_CLK, BUTTON1_CLK, WAKEUP_BUTTON_CLK}; 

const uint16_t BUTTON_EXTI_LINE[BUTTONn] = {BUTTON0_EXTI_LINE, BUTTON1_EXTI_LINE, WAKEUP_BUTTON_EXTI_LINE}; 

const uint16_t BUTTON_PORT_SOURCE[BUTTONn] = {BUTTON0_PORT_SOURCE, BUTTON1_PORT_SOURCE, WAKEUP_BUTTON_PORT_SOURCE}; 
							 
const uint16_t BUTTON_PIN_SOURCE[BUTTONn] = {BUTTON0_PIN_SOURCE, BUTTON1_PIN_SOURCE ,WAKEUP_BUTTON_PIN_SOURCE}; 
const uint16_t BUTTON_IRQn[BUTTONn] =	{BUTTON0_IRQn, BUTTON1_IRQn ,WAKEUP_BUTTON_IRQn};      
//按键
void STM_EVAL_PBInit(Button_TypeDef Button, Button_Mode_TypeDef Button_Mode)  //设置按键功能
	{
	GPIO_InitTypeDef GPIO_InitStructure;
	EXTI_InitTypeDef EXTI_InitStructure;
	NVIC_InitTypeDef NVIC_InitStructure;
	
	/* Enable Button GPIO clock */
	RCC_APB2PeriphClockCmd(BUTTON_CLK[Button] | RCC_APB2Periph_AFIO, ENABLE);			//使能按键所在GPIO时钟,同时使能AFIO时钟(需要设置外部中断寄存器)
	
	/* Configure Button pin as input floating */
	GPIO_InitStructure.GPIO_Pin = BUTTON_PIN[Button];			//设置按键盘所在引脚
	if(Button==Button_WAKEUP)	 //WAKE_UP按键,PA0,高电平有效,输入引脚需下拉设置
		{
	    GPIO_InitStructure.GPIO_Mode =GPIO_Mode_IPD;//上拉输入
		}
	else if(Button==Button_KEY0)  //KEY0按键,PA13 JTMS,高电平有效,输入引脚需下拉设置
		{
		//使用前请选禁止JTAG使用此引脚
	  GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IPU;//上拉输入 
		}
	else if(Button==Button_KEY1)  //WAKE_UP按键PA15 JTDI,高电平有效,输入引脚需下拉设置
		{
		//使用前请选禁止JTAG使用此引脚
		GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IPU;//上拉输入 
		}
	
	GPIO_Init(BUTTON_PORT[Button], &GPIO_InitStructure);	//初始化按键所在GPIO寄存器状态
	
	if (Button_Mode == Mode_EXTI)			//使用外部中断方式
		{
		/* Connect Button EXTI Line to Button GPIO Pin */
		GPIO_EXTILineConfig(BUTTON_PORT_SOURCE[Button], BUTTON_PIN_SOURCE[Button]);  	//选择按键所在的GPIO管脚用作外部中断线路
		
		/* Configure Button EXTI line */
		EXTI_InitStructure.EXTI_Line = BUTTON_EXTI_LINE[Button];	//设置按键所有的外部线路
		EXTI_InitStructure.EXTI_Mode = EXTI_Mode_Interrupt;			//设外外部中断模式:EXTI线路为中断请求
		
		if(Button != Button_WAKEUP)		//判断是什么按键
			{
			EXTI_InitStructure.EXTI_Trigger = EXTI_Trigger_Falling;  //外部中断触发沿选择:设置输入线路下降沿为中断请求
			}
		else
			{
			EXTI_InitStructure.EXTI_Trigger = EXTI_Trigger_Rising;  //外部中断触发沿选择:设置输入线路上升降沿为中断请求
			}
		EXTI_InitStructure.EXTI_LineCmd = ENABLE;		//使能外部中断新状态
		EXTI_Init(&EXTI_InitStructure);		//根据EXTI_InitStruct中指定的参数初始化外设EXTI寄存器
		
		/* Enable and set Button EXTI Interrupt to the lowest priority */
		NVIC_InitStructure.NVIC_IRQChannel = BUTTON_IRQn[Button];			//使能按键所在的外部中断通道
		NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 2;	//先占优先级4位,共16级
		NVIC_InitStructure.NVIC_IRQChannelSubPriority = 1;					//先占优先级0位,从优先级4位
		NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;								//使能外部中断通道
		
		NVIC_Init(&NVIC_InitStructure); 	//根据NVIC_InitStruct中指定的参数初始化外设NVIC寄存器
		}
	}
/**
  * @brief  Returns the selected Button state.
  * @param  Button: Specifies the Button to be checked.
  *   This parameter can be one of following parameters:    
  *     @arg Button_WAKEUP: Wakeup Push Button
  *     @arg Button_TAMPER: Tamper Push Button  
  *     @arg Button_KEY: Key Push Button 
  *     @arg Button_RIGHT: Joystick Right Push Button 
  *     @arg Button_LEFT: Joystick Left Push Button 
  *     @arg Button_UP: Joystick Up Push Button 
  *     @arg Button_DOWN: Joystick Down Push Button
  *     @arg Button_SEL: Joystick Sel Push Button    
  * @retval The Button GPIO pin value.
  */
uint32_t STM_EVAL_PBGetState(Button_TypeDef Button)
	{
	return GPIO_ReadInputDataBit(BUTTON_PORT[Button], BUTTON_PIN[Button]);		//返回按键所端口电平状态
	}




