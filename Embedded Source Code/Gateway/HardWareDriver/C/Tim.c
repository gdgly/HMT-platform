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
��д�ߣ�С��  (Camel)
����E-mail��375836945@qq.com
���뻷����MDK-Lite  Version: 4.23
����ʱ��: 2014-01-28
���ܣ�
1.��ʼ����ʱ��3�Ͷ�ʱ��4
2.��ʱ��3-->���ڴ�ӡ���ֲ���
3.��ʱ��4-->��̬�����Լ�PID��������ڹؼ��жϣ�����ʱ��4�������ȼ��Լ������ȼ���Ϊ��ߺ��б�Ҫ
------------------------------------
*/
#include "tim.h"
#include "config.h"



int LedCounter;//LED��˸����ֵ


//�������
void TIM4_IRQHandler(void)		//1ms�ж�һ��,���ڳ����ȡ6050��
{
    if( TIM_GetITStatus(TIM4 , TIM_IT_Update) != RESET ) 
    {     
//          Controler(); //���ƺ���
//                  
//          HMC58X3_mgetValues(&Compass_HMC[0]);       
//          LedCounter++;//led��˸����ֵ
//          if(Battery.BatteryAD > Battery.BatteryADmin)//����ص�ѹ���趨ֵ֮��ʱ������ģʽ
//          {
//              if(LedCounter==10){ LedA_off;LedB_off;}   //ң�ض�ʹ�ܺ�������ʾ        
//              else if(LedCounter==30){LedCounter=0;LedA_on;LedB_on;}
//          }
//          else //��ص�ѹ��ʱ��������ʾ
//          {
//              if(LedCounter==10){ LedA_off;LedB_off;LedC_off;LedD_off;}   //ң�ض�ʹ�ܺ�������ʾ        
//              else if(LedCounter==20){LedCounter=0;LedA_on;LedB_on;LedC_on;LedD_on;}
//          }
//          if(LedCounter>=31)LedCounter=0;

          
          
          TIM_ClearITPendingBit(TIM4 , TIM_FLAG_Update);   //����жϱ�־   
    }
}





int Timpackseqnum=1;             



void TIM3_IRQHandler(void)		//��ӡ�жϷ������
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
			TIM_ClearITPendingBit(TIM3 , TIM_FLAG_Update);   //����жϱ�־   
    }
}



//��ʱ��4��ʼ���������жϴ���PID
void TIM4_Init(int clock,int Preiod)
{
    TIM_TimeBaseInitTypeDef TIM_TimeBaseStructure;

    RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM4,ENABLE);  //��ʱ��
    
    TIM_DeInit(TIM4);

    TIM_TimeBaseStructure.TIM_Period = Preiod;
    TIM_TimeBaseStructure.TIM_Prescaler = clock-1;//��ʱ1ms
    TIM_TimeBaseStructure.TIM_ClockDivision = TIM_CKD_DIV1; 
    TIM_TimeBaseStructure.TIM_CounterMode = TIM_CounterMode_Up;
    
    TIM_TimeBaseInit(TIM4,&TIM_TimeBaseStructure);
    TIM_ClearFlag(TIM4,TIM_FLAG_Update);

    TIM_ITConfig(TIM4,TIM_IT_Update,ENABLE);
    TIM_Cmd(TIM4,ENABLE);
    printf("��ʱ��4��ʼ�����...\r\n");
    
}	


//��ʱ��3��ʼ��
void TIM3_Init(int clock,int Preiod)
{
    TIM_TimeBaseInitTypeDef TIM_TimeBaseStructure;

    RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM3,ENABLE);  //��ʱ��
    
    TIM_DeInit(TIM3);

    TIM_TimeBaseStructure.TIM_Period = Preiod;
    TIM_TimeBaseStructure.TIM_Prescaler = clock-1;//
    TIM_TimeBaseStructure.TIM_ClockDivision = TIM_CKD_DIV1; 
    TIM_TimeBaseStructure.TIM_CounterMode = TIM_CounterMode_Up;
    
    TIM_TimeBaseInit(TIM3,&TIM_TimeBaseStructure);
    TIM_ClearFlag(TIM3,TIM_FLAG_Update);

    TIM_ITConfig(TIM3,TIM_IT_Update,ENABLE);
    TIM_Cmd(TIM3,DISABLE);
  
   // printf("��ʱ��3��ʼ�����...\r\n");
}		


void TimerNVIC_Configuration()
{
    NVIC_InitTypeDef NVIC_InitStructure;
    
    /* NVIC_PriorityGroup 2 */
    NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2);
    //TIM3
    NVIC_InitStructure.NVIC_IRQChannel = TIM3_IRQn;
    NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 2;//��ʱ��3��Ϊ���ڴ�ӡ��ʱ�������ȼ�������̬����
    NVIC_InitStructure.NVIC_IRQChannelSubPriority = 0;
    NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
    NVIC_Init(&NVIC_InitStructure);
//    //TIM4
//    NVIC_InitStructure.NVIC_IRQChannel = TIM4_IRQn;
//    NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 1;//��ʱ��4��Ϊ��̬���㣬���ȼ����ڴ��ڴ�ӡ
//    NVIC_InitStructure.NVIC_IRQChannelSubPriority = 1;
//    NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
//    NVIC_Init(&NVIC_InitStructure);

} 





