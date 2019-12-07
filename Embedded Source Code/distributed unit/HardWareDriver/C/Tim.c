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




volatile int Addpacknum=0;
volatile int Dataseqnum=0;
volatile int Waitpacknum=0;
void TIM3_IRQHandler(void)		//打印中断服务程序
{
    if( TIM_GetITStatus(TIM3 , TIM_IT_Update) != RESET ) 
    { //GPIO_SetBits(GPIOA,GPIO_Pin_3);
			Dataseqnum++;
			if(Dataseqnum%2)
			{ 
				Led0_on;
				//GPIO_SetBits(GPIOA,GPIO_Pin_3);
			}
			else		
			{
				Led0_off;
				//GPIO_ResetBits(GPIOA,GPIO_Pin_3);
			}
			Initial_System_Timer();    //?????

			if(Waitpacknum>0)
			{
				Waitpacknum--;
				Dataseqnum--;
			}			 
		  else Data_Record();
			while(Addpacknum>0)
			{
				Dataseqnum++;
				Addpack(Addpacknum);
				Addpacknum--;				
			}	
			//GPIO_ResetBits(GPIOA,GPIO_Pin_3);
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
  
    printf("定时器3初始化完成...\r\n");
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

extern volatile int Motionstatus;

volatile float SDdatatmp;//写入SD卡临时数据字节
void Data_Record(void)
{    
			MS5611_Complete[0]=0;
			while(!(MS5611_Complete[0]))
			{
				if(!MS5611_Complete[0])
					MS5611BA_Routing(0); //处理MS5611 事务 
			}
			//__set_PRIMASK(1);
			Controler(0);
			//__set_PRIMASK(0);
			if(SDWriteBuf_Cnt(&SDWriteBuffer)<=SDWriteBuffer.Mask-12)
			{
				SDdatatmp = (float)Dataseqnum;          //临时数据赋值
				SDWriteBuf_WD(&SDWriteBuffer,SDdatatmp);               //写串口接收缓冲数组
				SDdatatmp = MS5611_Pressure[0]; 
				SDWriteBuf_WD(&SDWriteBuffer,SDdatatmp);
				
				SDdatatmp = DMP_DATA[0].dmp_gyrox;          
				SDWriteBuf_WD(&SDWriteBuffer,SDdatatmp);               
				SDdatatmp = DMP_DATA[0].dmp_gyroy;          
				SDWriteBuf_WD(&SDWriteBuffer,SDdatatmp);               
				SDdatatmp = DMP_DATA[0].dmp_gyroz;  		
				SDWriteBuf_WD(&SDWriteBuffer,SDdatatmp); 
				
				SDdatatmp = DMP_DATA[0].dmp_accx;          
				SDWriteBuf_WD(&SDWriteBuffer,SDdatatmp);               
				SDdatatmp = DMP_DATA[0].dmp_accy;          
				SDWriteBuf_WD(&SDWriteBuffer,SDdatatmp);               
				SDdatatmp = DMP_DATA[0].dmp_accz;       			
				SDWriteBuf_WD(&SDWriteBuffer,SDdatatmp); 
				
				SDdatatmp = Compass_HMC[0][0];          
				SDWriteBuf_WD(&SDWriteBuffer,SDdatatmp);               
				SDdatatmp = Compass_HMC[0][1];          
				SDWriteBuf_WD(&SDWriteBuffer,SDdatatmp);               
				SDdatatmp = Compass_HMC[0][2]; 
        SDWriteBuf_WD(&SDWriteBuffer,SDdatatmp); 

        SDdatatmp = (float)Motionstatus; 
        SDWriteBuf_WD(&SDWriteBuffer,SDdatatmp);  
			}
			else
				//TIM_Cmd(TIM3,DISABLE);
			  printf("缓冲区满！\r\n");	
			
			
}
void Tim_Sync(int SequenceNum)
{
 	if(Dataseqnum==SequenceNum*10)
	{
		TIM3->CNT = 0x0;//清零
	}
	else if(Dataseqnum>SequenceNum*10)
	{
		TIM3->CNT = 0x0;
		Waitpacknum=Dataseqnum-SequenceNum*10;
	}
	else if(Dataseqnum<SequenceNum*10)
	{
	 if(Dataseqnum==SequenceNum*10-1 && TIM_GetITStatus(TIM3 , TIM_IT_Update) == RESET)
          TIM3->CNT = 5000-1;//
    else
	 {
		 TIM3->CNT = 0x0;
		 Addpacknum = SequenceNum*10-Dataseqnum;
	 }	 
  }		
}
void Addpack(int addpacknum)
{    
			int i;
	    SDdatatmp = 0.f;
			if(SDWriteBuf_Cnt(&SDWriteBuffer)<=SDWriteBuffer.Mask-12*Addpacknum)
			{
				SDdatatmp = (float)Dataseqnum;          //临时数据赋值
				SDWriteBuf_WD(&SDWriteBuffer,SDdatatmp); 
				for(i=0;i<addpacknum*10;i++)
				{
				   SDWriteBuf_WD(&SDWriteBuffer,SDdatatmp);               //写串口接收缓冲数组
				}
				SDdatatmp = (float)Motionstatus; 
        SDWriteBuf_WD(&SDWriteBuffer,SDdatatmp); 
			}
			else
			  printf("缓冲区满！\r\n");	

}
