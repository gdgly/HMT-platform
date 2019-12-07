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
void EXTI_init(void);
void TIM_GPIO_Init(void);
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
	delay_init(SysClock);         //�δ���ʱ��ʼ�� 
  UART1_init(SysClock,115200); 	//����1��ʼ��
  SPI2_init()	;
	
  NVIC_INIT();	                //�жϳ�ʼ��

	LedInit();		                //IO��ʼ�� 
	
	STM_EVAL_PBInit(Button_KEY0, Mode_EXTI);			//���ð����ⲿ�жϷ�ʽ
	STM_EVAL_PBInit(Button_KEY1, Mode_EXTI);			//���ð����ⲿ�жϷ�ʽ
	
 	EXTI_init();

  DW1000_init();
  TIM3_Init(SysClock*10,60000);	    //��ʱ��3��ʼ�� 500ms
  RX_mode_enable();	 

  while (1)                    
  {
		delay_ms(1000);	
	}
}

/*
�ⲿ�жϳ�ʼ����PA1
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
 	
 RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);	 //ʹ��PA�˿�ʱ��
	
 GPIO_InitStructure.GPIO_Pin = GPIO_Pin_3;				 //PA.3 �˿�����
 GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP; 		 //�������
 GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
 GPIO_Init(GPIOA, &GPIO_InitStructure);
 GPIO_ResetBits(GPIOA,GPIO_Pin_3);						 //PA.3 �����

}
