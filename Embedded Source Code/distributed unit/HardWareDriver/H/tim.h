#ifndef _tim_H_
#define _tim_H_
#include "stm32f10x.h"



void TIM4_Init(int clock,int Preiod);//���ڼ��ϵͳ
void TIM3_Init(int clock,int Preiod);//��ʱ��3�ĳ�ʼ��
void TimerNVIC_Configuration(void);//��ʱ���ж�����������
void Data_Record(void);
void Tim_Sync(int timpackseqnum);
void Addpack(int addpacknum);
#endif

