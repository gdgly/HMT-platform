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
*/
/* Control.c file
��д�ߣ�С��  (Camel)
����E-mail��375836945@qq.com
���뻷����MDK-Lite  Version: 4.23
����ʱ��: 2014-01-28
���ܣ�
1.PID������ʼ��
2.���ƺ���

------------------------------------
*/
#include "control.h"
#include "moto.h"
#include "math.h"
#include "sys_fun.h"
#include "mpu6050.h"
#include "imu.h"
#include "extern_variable.h"
#include "led.h"
#include "stmflash.h"
#include "DMP.h"
#include "stdio.h"
#include "BT.h"

//----PID�ṹ��ʵ����----
PID_Typedef pitch_angle_PID;	//�ǶȻ���PID
PID_Typedef pitch_rate_PID;		//�����ʻ���PID

PID_Typedef roll_angle_PID;
PID_Typedef roll_rate_PID;

PID_Typedef yaw_angle_PID;
PID_Typedef yaw_rate_PID;

float gyroxGloble[ChannelNum] = {0,0};
float gyroyGloble[ChannelNum] = {0,0};


S_FLOAT_XYZ DIF_ACC;		//ʵ��ȥ�������ļ��ٶ�
S_FLOAT_XYZ EXP_ANGLE;	//�����Ƕ�	
S_FLOAT_XYZ DIF_ANGLE;	//ʵ�����������ĽǶ�	

//��������Controler()
//���룺��
//���: ��
//�������ɻ����ƺ������壬����ʱ������
//���ߣ���
//��ע��û�����У����鲻��
void Controler(u8 Channel)
{     
    DMP_Routing(Channel);	        //DMP �߳�  ���е����ݶ����������
    HMC58X3_mgetValues(Compass_HMC[Channel],Channel); 
	//DMP_getYawPitchRoll();  //��ȡ ��̬��
    /*******************����λ��������̬��Ϣ�����Ҫ��PC��λ����ʵʱ��̬,�꿪�ؿ���***************/
  
}

