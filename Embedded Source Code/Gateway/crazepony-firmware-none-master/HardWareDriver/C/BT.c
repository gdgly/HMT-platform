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
BT.c file
��д�ߣ�С��  (Camel)
����E-mail��375836945@qq.com
���뻷����MDK-Lite  Version: 4.23
����ʱ��: 2014-01-28
���ܣ�
1.����͸��ģ��ĵ�Դʹ�ܶ�BT_EN--->PB2
2.��������Դ-->BT_EN=1;
------------------------------------
*/


#include "BT.h"
#include "delay.h"
#include "UART1.h"
#include "stdio.h"
#include "string.h"
#include "sys_fun.h"
#include "control.h"

char Cmdreturn[CmdreturnLength];//ָ��ķ��ؽ������


/********************************************
              ������Դ��ʼ������
********************************************/
void BT_PowerInit(void)
{
    RCC->APB2ENR|=1<<3;      //ʹ��PORTBʱ��	
    GPIOB->CRL&=0XFFFFF0FF;  //PB2�������
    GPIOB->CRL|=0X00000300;
    GPIOB->ODR|=1<<2;        //PB2����
    BT_off();                //Ĭ�Ϲر�
}

/********************************************
              ������д��һ��ָ���
********************************************/
void Uart1SendaBTCmd(const char *p)
{
  char i;
  for(i=0;i<CmdreturnLength;i++) Cmdreturn[i] = 0;//�ͷ�ָ����ջ���
  delay_ms(800);//ÿ����д������֮�䣬Ҫ�м��ٺ��뼶�����ʱ 
  for(i=0;i<strlen(p);i++)
  UART1_Put_Char(*(p+i));  
  delay_ms(800);//д��һ��ָ���ʱ500ms�ٶȽ��ջ���
  i=0;
  while(UartBuf_Cnt(&UartRxbuf) != 0)   //�����ڻ��岻Ϊ��ʱ�������ڻ��帳ֵ��ָ��������
  Cmdreturn[i++] = UartBuf_RD(&UartRxbuf);
}

/********************************************
         �ж�һ��ָ����ǲ��ǵ����趨ֵ
         ����ֵ��0-->ָ�����趨ֵ��ƥ��
                 1-->ָ�����趨ֵƥ��
********************************************/
char CmdJudgement(const char *p)
{
  char i;
  for(i=0;i<strlen(p);i++) if(Cmdreturn[i] != *(p+i)) break;
  if(i != strlen(p)) return 0;
  return 1;
}

const char ATcmdAsk[] = {"AT"};
const char ATcmdAnswer[] = {"OK"};

const char ATcmdNameAsk[] = {"AT+NAME?"};
const char ATcmdNameAnswer[] = {"OK+NAME:Crazepony"};
const char ATcmdNameSet[] = {"AT+NAMECrazepony"};//���������豸��Ϊ��Crazepony����Ȼ�����������޸ĳ� what ever you want...

const char ATcmdCodeAsk[] = {"AT+PIN?"};
const char ATcmdCodeAnswer[] = {"OK+PIN:1234"};
const char ATcmdCodeSet[] = {"AT+PIN1234"};      //�����������Ĭ��Ϊ1234��

const char ATcmdBaudAsk[] = {"AT+BAUD?"};
const char ATcmdBaudAnswer[] = {"OK+BAUD:115200"};
const char ATcmdBaudSet[] = {"AT+BAUD8"};    
      //baud1--->1200
      //baud2--->2400
      //baud3--->4800
      //baud4--->9600
      //baud5--->19200
      //baud6--->38400
      //baud7--->57600
      //baud8--->115200


/********************************************
              д������������
********************************************/
void BT_ATcmdWrite(void)
{
    BT_on();        //������
    delay_ms(1500); //�ȴ������ȶ�
    // if(BTParameter.ReadBuf[2] == false)
    // {
    printf("������ͨ����...\r\n");
    UART1_init(SysClock,9600); 
    Uart1SendaBTCmd(ATcmdAsk);
    if(CmdJudgement(ATcmdAnswer) == true)//���������أ�������дָ��
    {
        Uart1SendaBTCmd(ATcmdBaudAsk);
        if(CmdJudgement(ATcmdBaudAnswer) == false) {Uart1SendaBTCmd(ATcmdBaudSet);   }
        else ;
        Uart1SendaBTCmd(ATcmdNameAsk);
        if(CmdJudgement(ATcmdNameAnswer) == false)  {Uart1SendaBTCmd(ATcmdNameSet); }   
        else ;
        Uart1SendaBTCmd(ATcmdCodeAsk);
        if(CmdJudgement(ATcmdCodeAnswer) == false) {Uart1SendaBTCmd(ATcmdCodeSet);  }
        else ;
    }
    else  {printf("������ͨ��ʧ��\r\n");}
    
    UART1_init(SysClock,115200);
    //   }
    //   else  {printf("����������д��...\r\n");}
    //   
}




