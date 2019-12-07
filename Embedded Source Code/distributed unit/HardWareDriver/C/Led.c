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
Ledo-->PB0

��ӦIO=1������
********************************************/
void LedInit(void)
{
	  GPIO_InitTypeDef  GPIO_InitStructure;
 	
		RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);	 //ʹ��PB�˿�ʱ��
			
		GPIO_InitStructure.GPIO_Pin = GPIO_Pin_0;				 //LED0-->PC.13 �˿�����
		GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP; 		 //�������
		GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
		GPIO_Init(GPIOA, &GPIO_InitStructure);
    Led0_off;
    printf("״̬LED�Ƴ�ʼ�����...\r\n");
}



