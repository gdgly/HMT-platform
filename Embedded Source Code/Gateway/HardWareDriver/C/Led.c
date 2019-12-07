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
��д�ߣ�С��  (Camel)
����E-mail��375836945@qq.com
���뻷����MDK-Lite  Version: 4.23
����ʱ��: 2014-01-28
���ܣ�
1.�ɻ��ĸ�����led IO�ڳ�ʼ��
2.��ʼ��Ĭ�Ϲر�����LED��
------------------------------------
*/

#include "Led.h"
#include "UART1.h"
#include "config.h"

/********************************************
              Led��ʼ������
���ܣ�
1.����Led�ӿ�IO�������
2.�ر�����Led(����Ĭ�Ϸ�ʽ)
������
Led�ӿڣ�
Led1-->PA11
Led2-->PA8
Led3-->PB1
Led4-->PB3
��ӦIO=1������
********************************************/
void LedInit(void)
{
    RCC->APB2ENR|=1<<2;    //ʹ��PORTAʱ��	
		RCC->APB2ENR|=1<<5;    //ʹ��PORTDʱ��	
		//RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOD, ENABLE);	
	
    RCC->APB2ENR|=1<<0;      //ʹ�ܸ���ʱ��	   
  
    GPIOA->CRH&=0XFFFFFFF0;  //PA8�������
    GPIOA->CRH|=0X00000003;
    GPIOA->ODR|=1<<8;        //PA8����
	
		GPIOD->CRL&=0XFFFFF0FF;  //PD2�������
    GPIOD->CRL|=0X00000300;
    GPIOD->ODR|=1<<2;        //PD2����
  
    AFIO->MAPR|=2<<24;      //�ر�JATG,ǧ���ܽ�SWDҲ�رգ�����оƬ���ϣ��ײ�!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    Led0_off;Led1_off;
}
GPIO_TypeDef* BUTTON_PORT[BUTTONn] = {BUTTON0_PORT, BUTTON1_PORT, WAKEUP_BUTTON_PORT}; 

const uint16_t BUTTON_PIN[BUTTONn] = {BUTTON0_PIN, BUTTON1_PIN ,WAKEUP_BUTTON_PIN}; 

const uint32_t BUTTON_CLK[BUTTONn] = {BUTTON0_CLK, BUTTON1_CLK, WAKEUP_BUTTON_CLK}; 

const uint16_t BUTTON_EXTI_LINE[BUTTONn] = {BUTTON0_EXTI_LINE, BUTTON1_EXTI_LINE, WAKEUP_BUTTON_EXTI_LINE}; 

const uint16_t BUTTON_PORT_SOURCE[BUTTONn] = {BUTTON0_PORT_SOURCE, BUTTON1_PORT_SOURCE, WAKEUP_BUTTON_PORT_SOURCE}; 
							 
const uint16_t BUTTON_PIN_SOURCE[BUTTONn] = {BUTTON0_PIN_SOURCE, BUTTON1_PIN_SOURCE ,WAKEUP_BUTTON_PIN_SOURCE}; 
const uint16_t BUTTON_IRQn[BUTTONn] =	{BUTTON0_IRQn, BUTTON1_IRQn ,WAKEUP_BUTTON_IRQn};      
//����
void STM_EVAL_PBInit(Button_TypeDef Button, Button_Mode_TypeDef Button_Mode)  //���ð�������
	{
	GPIO_InitTypeDef GPIO_InitStructure;
	EXTI_InitTypeDef EXTI_InitStructure;
	NVIC_InitTypeDef NVIC_InitStructure;
	
	/* Enable Button GPIO clock */
	RCC_APB2PeriphClockCmd(BUTTON_CLK[Button] | RCC_APB2Periph_AFIO, ENABLE);			//ʹ�ܰ�������GPIOʱ��,ͬʱʹ��AFIOʱ��(��Ҫ�����ⲿ�жϼĴ���)
	
	/* Configure Button pin as input floating */
	GPIO_InitStructure.GPIO_Pin = BUTTON_PIN[Button];			//���ð�������������
	if(Button==Button_WAKEUP)	 //WAKE_UP����,PA0,�ߵ�ƽ��Ч,������������������
		{
	    GPIO_InitStructure.GPIO_Mode =GPIO_Mode_IPD;//��������
		}
	else if(Button==Button_KEY0)  //KEY0����,PA13 JTMS,�ߵ�ƽ��Ч,������������������
		{
		//ʹ��ǰ��ѡ��ֹJTAGʹ�ô�����
	  GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IPU;//�������� 
		}
	else if(Button==Button_KEY1)  //WAKE_UP����PA15 JTDI,�ߵ�ƽ��Ч,������������������
		{
		//ʹ��ǰ��ѡ��ֹJTAGʹ�ô�����
		GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IPU;//�������� 
		}
	
	GPIO_Init(BUTTON_PORT[Button], &GPIO_InitStructure);	//��ʼ����������GPIO�Ĵ���״̬
	
	if (Button_Mode == Mode_EXTI)			//ʹ���ⲿ�жϷ�ʽ
		{
		/* Connect Button EXTI Line to Button GPIO Pin */
		GPIO_EXTILineConfig(BUTTON_PORT_SOURCE[Button], BUTTON_PIN_SOURCE[Button]);  	//ѡ�񰴼����ڵ�GPIO�ܽ������ⲿ�ж���·
		
		/* Configure Button EXTI line */
		EXTI_InitStructure.EXTI_Line = BUTTON_EXTI_LINE[Button];	//���ð������е��ⲿ��·
		EXTI_InitStructure.EXTI_Mode = EXTI_Mode_Interrupt;			//�����ⲿ�ж�ģʽ:EXTI��·Ϊ�ж�����
		
		if(Button != Button_WAKEUP)		//�ж���ʲô����
			{
			EXTI_InitStructure.EXTI_Trigger = EXTI_Trigger_Falling;  //�ⲿ�жϴ�����ѡ��:����������·�½���Ϊ�ж�����
			}
		else
			{
			EXTI_InitStructure.EXTI_Trigger = EXTI_Trigger_Rising;  //�ⲿ�жϴ�����ѡ��:����������·��������Ϊ�ж�����
			}
		EXTI_InitStructure.EXTI_LineCmd = ENABLE;		//ʹ���ⲿ�ж���״̬
		EXTI_Init(&EXTI_InitStructure);		//����EXTI_InitStruct��ָ���Ĳ�����ʼ������EXTI�Ĵ���
		
		/* Enable and set Button EXTI Interrupt to the lowest priority */
		NVIC_InitStructure.NVIC_IRQChannel = BUTTON_IRQn[Button];			//ʹ�ܰ������ڵ��ⲿ�ж�ͨ��
		NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 2;	//��ռ���ȼ�4λ,��16��
		NVIC_InitStructure.NVIC_IRQChannelSubPriority = 1;					//��ռ���ȼ�0λ,�����ȼ�4λ
		NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;								//ʹ���ⲿ�ж�ͨ��
		
		NVIC_Init(&NVIC_InitStructure); 	//����NVIC_InitStruct��ָ���Ĳ�����ʼ������NVIC�Ĵ���
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
	return GPIO_ReadInputDataBit(BUTTON_PORT[Button], BUTTON_PIN[Button]);		//���ذ������˿ڵ�ƽ״̬
	}




