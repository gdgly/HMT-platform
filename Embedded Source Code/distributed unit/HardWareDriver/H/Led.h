#ifndef _Led_H_
#define _Led_H_
#include "stm32f10x.h"

#define Led0_on    GPIO_ResetBits(GPIOA, GPIO_Pin_0)
#define Led0_off   GPIO_SetBits(GPIOA, GPIO_Pin_0)

void LedInit(void);   //Led��ʼ�������ⲿ����



#endif

