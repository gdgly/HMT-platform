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
UART1.c file
��д�ߣ�С��  (Camel)
����E-mail��375836945@qq.com
���뻷����MDK-Lite  Version: 4.23
����ʱ��: 2014-01-28
���ܣ�
1.����1��ʼ��
2.��������ӡ�ش������֣���׿4.0���ϰ汾����͸���ӿ��Լ���PC��λ���ӿ�
3.�ṩ��׼�������printf()�ĵײ�������Ҳ����˵printf����ֱ�ӵ���
------------------------------------
*/
#include "UART1.h"
#include "stdio.h"
#include "sys_fun.h"
#include "string.h"
#include "Tim.h"
//uart reicer flag
#define b_uart_head  0x80
#define b_rx_over    0x40

//////////////////////////////////////////////////////////////////
//�������´���,֧��printf����,������Ҫѡ��use MicroLIB	  
#if 1
#pragma import(__use_no_semihosting)             
//��׼����Ҫ��֧�ֺ���                 
struct __FILE 
{ 
	int handle; 
	/* Whatever you require here. If the only file you are using is */ 
	/* standard output using printf() for debugging, no file handling */ 
	/* is required. */ 
}; 
/* FILE is typedef�� d in stdio.h. */ 
FILE __stdout;       
//����_sys_exit()�Ա���ʹ�ð�����ģʽ    
_sys_exit(int x) 
{ 
	x = x; 
} 
//�ض���fputc���� 
int fputc(int ch, FILE *f)
{      
	while((USART1->SR&0X40)==0);//ѭ������,ֱ���������   
	USART1->DR = (u8) ch;      
	return ch;
}
#endif 




/**************************ʵ�ֺ���********************************************
*����ԭ��:		void U1NVIC_Configuration(void)
*��������:		����1�ж�����
�����������
���������û��	
*******************************************************************************/
void UART1NVIC_Configuration(void)
{
        NVIC_InitTypeDef NVIC_InitStructure; 
        /* Enable the USART1 Interrupt */
        NVIC_InitStructure.NVIC_IRQChannel = USART1_IRQn;
        NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 0;
        NVIC_InitStructure.NVIC_IRQChannelSubPriority = 0;
        NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
        NVIC_Init(&NVIC_InitStructure);
}



/**************************ʵ�ֺ���********************************************
*����ԭ��:		void Initial_UART1(u32 baudrate)
*��������:		��ʼ��UART1
���������u32 baudrate   ����RS232���ڵĲ�����
���������û��	
*******************************************************************************/
void UART1_init(u32 pclk2,u32 bound)
{  	 
	float temp;
	u16 mantissa;
	u16 fraction;	   
	temp=(float)(pclk2*1000000)/(bound*16);//�õ�USARTDIV
	mantissa=temp;				 //�õ���������
	fraction=(temp-mantissa)*16; //�õ�С������	 
  mantissa<<=4;
	mantissa+=fraction; 
	RCC->APB2ENR|=1<<2;   //ʹ��PORTA��ʱ��  
	RCC->APB2ENR|=1<<14;  //ʹ�ܴ���ʱ�� 
	GPIOA->CRH&=0XFFFFF00F;//IO״̬����
	GPIOA->CRH|=0X000008B0;//IO״̬����
	RCC->APB2RSTR|=1<<14;   //��λ����1
	RCC->APB2RSTR&=~(1<<14);//ֹͣ��λ	   	   
	//����������
 	USART1->BRR=mantissa; // ����������	 
	USART1->CR1|=0X200C;  //1λֹͣ,��У��λ.
  USART1->CR1|=1<<8;    //PE�ж�ʹ��
	USART1->CR1|=1<<5;    //���ջ������ǿ��ж�ʹ��	    	
 
  UART1NVIC_Configuration();//�ж�����
  
  
  UartTxbuf.Wd_Indx = 0;
  UartTxbuf.Rd_Indx = 0;
  UartTxbuf.Mask = TX_BUFFER_SIZE - 1;
  UartTxbuf.pbuf = &tx_buffer[0];
  
  UartRxbuf.Wd_Indx = 0;
  UartRxbuf.Rd_Indx = 0;
  UartRxbuf.Mask = RX_BUFFER_SIZE - 1;
  UartRxbuf.pbuf = &rx_buffer[0];
  
  
//  printf("ϵͳʱ��Ƶ�ʣ�%dMHz \r\n",pclk2);
//printf("����1��ʼ�������ʣ�%d \r\n",bound);
 
  
}

/**************************ʵ�ֺ���********************************************
*����ԭ��:		void UART1_Put_Char(unsigned char DataToSend)
*��������:		RS232����һ���ֽ�
���������
		unsigned char DataToSend   Ҫ���͵��ֽ�����
���������û��	
*******************************************************************************/
void UART1_Put_Char(unsigned char DataToSend)
{
  
  UartBuf_WD(&UartTxbuf,DataToSend);//�����������ݷ��ڻ��λ���������
  USART_ITConfig(USART1, USART_IT_TXE, ENABLE);  //���������жϿ�ʼžžž���ͻ����е�����
}


uint8_t Uart1_Put_Char(unsigned char DataToSend)
{
  UartBuf_WD(&UartTxbuf,DataToSend);//�����������ݷ��ڻ��λ���������
  USART_ITConfig(USART1, USART_IT_TXE, ENABLE);  //���������жϿ�ʼžžž���ͻ����е�����
	return DataToSend;
}

//���� ����ṹ��ʵ������������
UartBuf UartTxbuf;//���η��ͽṹ��
UartBuf UartRxbuf;//���ν��սṹ��

unsigned char rx_buffer[RX_BUFFER_SIZE];
unsigned char tx_buffer[TX_BUFFER_SIZE];

//��ȡ���������е�һ���ֽ�
uint8_t UartBuf_RD(UartBuf *Ringbuf)
{
  uint8_t temp;
  temp = Ringbuf->pbuf[Ringbuf->Rd_Indx & Ringbuf->Mask];//���ݳ����������Ҫ�����Ǿ������ݻ��εĹؼ�
  Ringbuf->Rd_Indx++;//��ȡ���һ�Σ���ָ���1��Ϊ��һ�� ��ȡ�� ׼��
  return temp;
}
//��һ���ֽ�д��һ�����νṹ����
void UartBuf_WD(UartBuf *Ringbuf,uint8_t DataIn)
{
  
  Ringbuf->pbuf[Ringbuf->Wd_Indx & Ringbuf->Mask] = DataIn;//���ݳ����������Ҫ�����Ǿ������ݻ��εĹؼ�
  Ringbuf->Wd_Indx++;//д��һ�Σ�дָ���1��Ϊ��һ��д����׼��

}
//�����������Ŀ����ֽڳ��ȣ���дָ��д��һȦ��׷���˶�ָ��
//��ô֤������д���ˣ���ʱӦ�����ӻ��������ȣ�����������Χ���ݴ���ʱ��
uint16_t UartBuf_Cnt(UartBuf *Ringbuf)
{
  return (Ringbuf->Wd_Indx - Ringbuf->Rd_Indx) & Ringbuf->Mask;//���ݳ����������Ҫ�����Ǿ������ݻ��εĹؼ�
}




volatile uint8_t Udatatmp;//���ڽ�����ʱ�����ֽ�
//------------------------------------------------------
void USART1_IRQHandler(void)
{
  if(USART_GetITStatus(USART1, USART_IT_TXE) != RESET)
  {   
    USART_SendData(USART1, UartBuf_RD(&UartTxbuf)); //�������ݻ��淢��
    if(UartBuf_Cnt(&UartTxbuf)==0)  USART_ITConfig(USART1, USART_IT_TXE, DISABLE);//���绺����ˣ��͹رմ��ڷ����ж�
  }
  
  else if(USART_GetITStatus(USART1, USART_IT_RXNE) != RESET)
  {
    //���ֻ��λ������鴮�ڽ��շ�ʽ�������ڽ���������ݣ��ܷ��㡣�����ݵ�Ҫ����:
    //���ͷ�����Ҫ�������ݰ�ͷ���Ա������������޵�ַ������
    Udatatmp = USART_ReceiveData(USART1);          //��ʱ���ݸ�ֵ
    UartBuf_WD(&UartRxbuf,Udatatmp);               //д���ڽ��ջ�������
	
    if(UartBuf_Cnt(&UartRxbuf)==0) USART_SendData(USART1, 'E');//���ڽ������鳤�ȵ���0ʱ�����ͽ�������ձ�־
    if(UartBuf_Cnt(&UartRxbuf)==UartRxbuf.Mask) USART_SendData(USART1, 'F');//���ڽ������鳤�ȵ�������ʱ�����ͽ��ջ�������־
   

		//�ɼ����ݿ�ʼ���������ж�

    USART_ClearITPendingBit(USART1, USART_IT_RXNE);//��������жϱ�־
  }
  
}


