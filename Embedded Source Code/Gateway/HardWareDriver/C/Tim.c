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
Tim.c file
编写者：小马  (Camel)
作者E-mail：375836945@qq.com
编译环境：MDK-Lite  Version: 4.23
初版时间: 2014-01-28
功能：
1.初始化定时器3和定时器4
2.定时器3-->串口打印各种参数
3.定时器4-->姿态解算以及PID输出，属于关键中断，将定时器4的主优先级以及从优先级设为最高很有必要
------------------------------------
*/
#include "tim.h"
#include "config.h"



int LedCounter;//LED闪烁计数值


//控制入口
void TIM4_IRQHandler(void)		//1ms中断一次,用于程序读取6050等
{
    if( TIM_GetITStatus(TIM4 , TIM_IT_Update) != RESET ) 
    {     
//          Controler(); //控制函数
//                  
//          HMC58X3_mgetValues(&Compass_HMC[0]);       
//          LedCounter++;//led闪烁计数值
//          if(Battery.BatteryAD > Battery.BatteryADmin)//当电池电压在设定值之上时，正常模式
//          {
//              if(LedCounter==10){ LedA_off;LedB_off;}   //遥控端使能后，闪灯提示        
//              else if(LedCounter==30){LedCounter=0;LedA_on;LedB_on;}
//          }
//          else //电池电压低时，闪灯提示
//          {
//              if(LedCounter==10){ LedA_off;LedB_off;LedC_off;LedD_off;}   //遥控端使能后，闪灯提示        
//              else if(LedCounter==20){LedCounter=0;LedA_on;LedB_on;LedC_on;LedD_on;}
//          }
//          if(LedCounter>=31)LedCounter=0;

          
          
          TIM_ClearITPendingBit(TIM4 , TIM_FLAG_Update);   //清除中断标志   
    }
}





int Timpackseqnum=1;             



void TIM3_IRQHandler(void)		//打印中断服务程序
{  
  	u16 size= 7;
	  uint8_t temp[4];
    u8 send_buff[20];
    if( TIM_GetITStatus(TIM3 , TIM_IT_Update) != RESET ) 
    { 
			if(Timpackseqnum%2)
			{  Led0_on;
			}
			else		
			{	Led0_off;
			}				

		// if(Timpackseqnum<0x7fffffff)
			{				
				*(int*)temp=Timpackseqnum;
				send_buff[0]= 0xfa;
				send_buff[1]= 0xfb;
				send_buff[2]= 0x04;
				send_buff[3]= temp[3];
				send_buff[4]= temp[2];
				send_buff[5]= temp[1];
				send_buff[6]= temp[0];
				raw_write(send_buff, &size);
			}
	
			Timpackseqnum++;
			TIM_ClearITPendingBit(TIM3 , TIM_FLAG_Update);   //清除中断标志   
    }
}



//定时器4初始化：用来中断处理PID
void TIM4_Init(int clock,int Preiod)
{
    TIM_TimeBaseInitTypeDef TIM_TimeBaseStructure;

    RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM4,ENABLE);  //打开时钟
    
    TIM_DeInit(TIM4);

    TIM_TimeBaseStructure.TIM_Period = Preiod;
    TIM_TimeBaseStructure.TIM_Prescaler = clock-1;//定时1ms
    TIM_TimeBaseStructure.TIM_ClockDivision = TIM_CKD_DIV1; 
    TIM_TimeBaseStructure.TIM_CounterMode = TIM_CounterMode_Up;
    
    TIM_TimeBaseInit(TIM4,&TIM_TimeBaseStructure);
    TIM_ClearFlag(TIM4,TIM_FLAG_Update);

    TIM_ITConfig(TIM4,TIM_IT_Update,ENABLE);
    TIM_Cmd(TIM4,ENABLE);
    printf("定时器4初始化完成...\r\n");
    
}	


//定时器3初始化
void TIM3_Init(int clock,int Preiod)
{
    TIM_TimeBaseInitTypeDef TIM_TimeBaseStructure;

    RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM3,ENABLE);  //打开时钟
    
    TIM_DeInit(TIM3);

    TIM_TimeBaseStructure.TIM_Period = Preiod;
    TIM_TimeBaseStructure.TIM_Prescaler = clock-1;//
    TIM_TimeBaseStructure.TIM_ClockDivision = TIM_CKD_DIV1; 
    TIM_TimeBaseStructure.TIM_CounterMode = TIM_CounterMode_Up;
    
    TIM_TimeBaseInit(TIM3,&TIM_TimeBaseStructure);
    TIM_ClearFlag(TIM3,TIM_FLAG_Update);

    TIM_ITConfig(TIM3,TIM_IT_Update,ENABLE);
    TIM_Cmd(TIM3,DISABLE);
  
   // printf("定时器3初始化完成...\r\n");
}		


void TimerNVIC_Configuration()
{
    NVIC_InitTypeDef NVIC_InitStructure;
    
    /* NVIC_PriorityGroup 2 */
    NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2);
    //TIM3
    NVIC_InitStructure.NVIC_IRQChannel = TIM3_IRQn;
    NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 2;//定时器3作为串口打印定时器，优先级低于姿态解算
    NVIC_InitStructure.NVIC_IRQChannelSubPriority = 0;
    NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
    NVIC_Init(&NVIC_InitStructure);
//    //TIM4
//    NVIC_InitStructure.NVIC_IRQChannel = TIM4_IRQn;
//    NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 1;//定时器4作为姿态解算，优先级高于串口打印
//    NVIC_InitStructure.NVIC_IRQChannelSubPriority = 1;
//    NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
//    NVIC_Init(&NVIC_InitStructure);

} 





