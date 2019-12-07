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
Ledo-->PB0

对应IO=1，灯亮
********************************************/
void LedInit(void)
{
	  GPIO_InitTypeDef  GPIO_InitStructure;
 	
		RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);	 //使能PB端口时钟
			
		GPIO_InitStructure.GPIO_Pin = GPIO_Pin_0;				 //LED0-->PC.13 端口配置
		GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP; 		 //推挽输出
		GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
		GPIO_Init(GPIOA, &GPIO_InitStructure);
    Led0_off;
    printf("状态LED灯初始化完成...\r\n");
}



