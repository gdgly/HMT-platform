#ifndef _EXTERN_VARIABLE_H_
#define _EXTERN_VARIABLE_H_
#include "NRF24L01.h"
 
 
 
//ϵͳ
extern uint8_t SystemReady_OK;					//ϵͳ��ʼ����ɱ�־
extern uint8_t FLY_ENABLE;						  //���п���
extern uint8_t IIC_ERROR_CNT;					//iic���������,ÿ��tim3�жϼ�1,�����ȡ�ɹ���0
extern uint8_t	I2C2_BUSY;
volatile extern uint32_t	TIM3_IRQCNT;			//TIM3�жϼ�����
volatile extern uint32_t	TIM2_IRQCNT;			//TIM3�жϼ�����
volatile extern uint8_t 	MPU6050_I2CData_Ready;		//mpu6050��ȡ��ɱ�־,=1��ʾ��ȡ���


             
                
//������
typedef struct int16_xyz
{
    int16_t X;
    int16_t Y;
    int16_t Z;
}S_INT16_XYZ;


typedef union 
{
    int16_t D[3];
    S_INT16_XYZ V;
    
}U_INT16_XYZ;




//IMU
typedef struct float_xyz
{
    float X;
    float Y;
    float Z;
    
}S_FLOAT_XYZ;


typedef union 
{
    float D[3];
    S_FLOAT_XYZ V;	
    
}U_FLOAT_XYZ;
   

typedef struct float_angle
{
    float Roll;
    float Pitch;
    float Yaw;
}S_FLOAT_ANGLE;
    
             
extern S_FLOAT_XYZ ACC_F,GYRO_F;	//����ת�����ACC��λΪG,GYRO��λΪ��/��
extern S_FLOAT_XYZ GYRO_I[3];		//�����ǻ���

extern S_FLOAT_XYZ DIF_ACC;		//��ּ��ٶ�
extern S_FLOAT_XYZ EXP_ANGLE;		//�����Ƕ�
extern S_FLOAT_XYZ DIF_ANGLE;		//�����Ƕ���ʵ�ʽǶȲ�
extern S_FLOAT_ANGLE Q_ANGLE;		//��Ԫ��������ĽǶ�
extern S_INT16_XYZ ACC_AVG,GYRO_AVG;		//���������˲����ACCƽ��ֵ�ʹ�����gyroֵ
          
                
#endif
                
        



