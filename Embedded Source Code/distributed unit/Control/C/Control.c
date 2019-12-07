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
编写者：小马  (Camel)
作者E-mail：375836945@qq.com
编译环境：MDK-Lite  Version: 4.23
初版时间: 2014-01-28
功能：
1.PID参数初始化
2.控制函数

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

//----PID结构体实例化----
PID_Typedef pitch_angle_PID;	//角度环的PID
PID_Typedef pitch_rate_PID;		//角速率环的PID

PID_Typedef roll_angle_PID;
PID_Typedef roll_rate_PID;

PID_Typedef yaw_angle_PID;
PID_Typedef yaw_rate_PID;

float gyroxGloble[ChannelNum] = {0,0};
float gyroyGloble[ChannelNum] = {0,0};


S_FLOAT_XYZ DIF_ACC;		//实际去期望相差的加速度
S_FLOAT_XYZ EXP_ANGLE;	//期望角度	
S_FLOAT_XYZ DIF_ANGLE;	//实际与期望相差的角度	

//函数名：Controler()
//输入：无
//输出: 无
//描述：飞机控制函数主体，被定时器调用
//作者：马骏
//备注：没考上研，心情不好
void Controler(u8 Channel)
{     
    DMP_Routing(Channel);	        //DMP 线程  所有的数据都在这里更新
    HMC58X3_mgetValues(Compass_HMC[Channel],Channel); 
	//DMP_getYawPitchRoll();  //读取 姿态角
    /*******************向上位机发送姿态信息，如果要在PC上位机看实时姿态,宏开关控制***************/
  
}

