#ifndef _BT_H_
#define _BT_H_
#include "stm32f10x.h"
#include "UART1.h"


#define true  1
#define false !true



#define BT_on()      {GPIO_SetBits(GPIOB, GPIO_Pin_2);printf("������Դ��ʼ�������...\r\n");}
#define BT_off()     {GPIO_ResetBits(GPIOB, GPIO_Pin_2);printf("������Դ��ʼ���ر����...\r\n");}//�궨����������

#define CmdreturnLength 20



// typedef struct
// {
// unsigned char Name[];
// unsigned char Baud[];
// unsigned char PinCode[];
// }BTtype;



void BT_PowerInit(void);   //����͸����Դ��ʼ��
void BT_ATcmdWrite(void);//����д����


#endif

