#ifndef _ReceiveData_H_
#define _ReceiveData_H_
#include "stm32f10x.h"


//RCң��
typedef struct int16_rcget
{
    float ROOL;
    float PITCH;
    int THROTTLE;
    int YAW;
}RC_GETDATA;


extern RC_GETDATA RC_DATA;//���������RC����
   
void ReceiveDataFormNRF(void);
void ReceiveDataFormUART(void);
void Send_PIDToPC(void);
void Send_AtitudeToPC(void);
extern int  Rool_error_init;     //����ɻ���ɳ���ƫ��Rool_error_init�����������޸�;����ƫ��Rool_error_init�����������޸�
extern int  Pitch_error_init;     //����ɻ���ɳ�ǰƫ��Pitch_error_init�����������޸�;����ƫ��Pitch_error_init�����������޸�
void parse_package(u8 pkdata);
void Crazepony_get_uartpack(void);

#endif

