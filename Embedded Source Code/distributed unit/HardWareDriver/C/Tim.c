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




volatile int Addpacknum=0;
volatile int Dataseqnum=0;
volatile int Waitpacknum=0;
void TIM3_IRQHandler(void)		//��ӡ�жϷ������
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
  
    printf("��ʱ��3��ʼ�����...\r\n");
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

extern volatile int Motionstatus;

volatile float SDdatatmp;//д��SD����ʱ�����ֽ�
void Data_Record(void)
{    
			MS5611_Complete[0]=0;
			while(!(MS5611_Complete[0]))
			{
				if(!MS5611_Complete[0])
					MS5611BA_Routing(0); //����MS5611 ���� 
			}
			//__set_PRIMASK(1);
			Controler(0);
			//__set_PRIMASK(0);
			if(SDWriteBuf_Cnt(&SDWriteBuffer)<=SDWriteBuffer.Mask-12)
			{
				SDdatatmp = (float)Dataseqnum;          //��ʱ���ݸ�ֵ
				SDWriteBuf_WD(&SDWriteBuffer,SDdatatmp);               //д���ڽ��ջ�������
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
			  printf("����������\r\n");	
			
			
}
void Tim_Sync(int SequenceNum)
{
 	if(Dataseqnum==SequenceNum*10)
	{
		TIM3->CNT = 0x0;//����
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
				SDdatatmp = (float)Dataseqnum;          //��ʱ���ݸ�ֵ
				SDWriteBuf_WD(&SDWriteBuffer,SDdatatmp); 
				for(i=0;i<addpacknum*10;i++)
				{
				   SDWriteBuf_WD(&SDWriteBuffer,SDdatatmp);               //д���ڽ��ջ�������
				}
				SDdatatmp = (float)Motionstatus; 
        SDWriteBuf_WD(&SDWriteBuffer,SDdatatmp); 
			}
			else
			  printf("����������\r\n");	

}
