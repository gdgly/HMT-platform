#ifndef _Battery_H_
#define _Battery_H_
#include "stm32f10x.h"





//��ѹ��Ϣ�ṹ��
typedef struct
{
    
int    BatteryAD;             //��ѹADֵ
float  BatteryVal;            //��ѹʵ��ֵ
float  BatReal;               //��ص�ʵ�ʵ�ѹ�������ñ��
float  ADRef;                 //AD�ο�Դ��ѹ�������ǵ�Ƭ�������ѹ��һ����3.3V���ң�Ҫʵ��
float  ADinput;               //AD���������ѹ--->R15��R17�����ĺ��̵�ѹ
float  Bat_K;                 //�����ѹֵϵ�������ڵ�ѹУ׼
int    BatteryADmin;           //��ѹ����

}Bat_Typedef;



void BatteryCheckInit(void);	
u16 Get_Adc_Average(u8 ch,u8 times);             
int GetBatteryAD(void);     
//ʵ����һ����ѹ��Ϣ�ṹ��
extern Bat_Typedef Battery;

#endif
                
        



