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
iic.c file
��д�ߣ�С��  (Camel)
����E-mail��375836945@qq.com
���뻷����MDK-Lite  Version: 4.23
����ʱ��: 2014-01-28
���ܣ�
1.��ʼ�����IICЭ��
2.���IICЭ������ţ�Ҳ��STM32Ӳ��IIC�����š�ֻ����û���������
------------------------------------
*/
//STM32ģ��IICЭ�飬STM32��Ӳ��IIC��ЩBUG
//ϸ���п��ٸ�
//����޸�:2014-03-11


#include "IICx.h"
#include "delay.h"
#include "Led.h"
#include "UART1.h"
#include "stdio.h"

/**************************ʵ�ֺ���********************************************
*����ԭ��:		void SDA_IN(u8 Channel)
*��������:		
*******************************************************************************/
void SDA_IN(u8 Channel)
{	
	switch(Channel)
	{
		case 0:
			{GPIOB->CRL&=0X0FFFFFFF;GPIOB->CRL|=0x80000000;}break;
		case 1:
			{GPIOB->CRL&=0XFF0FFFFF;GPIOB->CRL|=0x00800000;}break;
	  case 2:
			{GPIOC->CRH&=0XFFFFF0FF;GPIOC->CRH|=0x00000800;}break;
		case 3:
			{GPIOC->CRL&=0X0FFFFFFF;GPIOC->CRL|=0x80000000;}break;
		case 4:
			{GPIOB->CRH&=0X0FFFFFFF;GPIOB->CRH|=0x80000000;}break;
	}
}

/**************************ʵ�ֺ���********************************************
*����ԭ��:		SDA_OUT(u8 Channel)
*��������:		
*******************************************************************************/
void SDA_OUT(u8 Channel)
{	
	switch(Channel)
	{
		case 0:
			{GPIOB->CRL&=0X0FFFFFFF;GPIOB->CRL|=0x30000000;}break;
		case 1:
			{GPIOB->CRL&=0XFF0FFFFF;GPIOB->CRL|=0x00300000;}break;
		case 2:
			{GPIOC->CRH&=0XFFFFF0FF;GPIOC->CRH|=0x00000300;}break;
		case 3:
			{GPIOC->CRL&=0X0FFFFFFF;GPIOC->CRL|=0x30000000;}break;
		case 4:
			{GPIOB->CRH&=0X0FFFFFFF;GPIOB->CRH|=0x30000000;}break;
	}
}

/**************************ʵ�ֺ���********************************************
*����ԭ��:		IIC_SCL(u8 data,u8 Channel)
*��������:		
*******************************************************************************/
void IIC_SCL(u8 data,u8 Channel)
{	
	switch(Channel)
	{
		case 0:
			PBout(SCL0_PIN) = data;break;
		case 1:
			PBout(6) = data;break;
		case 2:
			PCout(12) = data;break;
		case 3:
			PCout(6) = data;break;
		case 4:
			PBout(14) = data;break;
	}
}

/**************************ʵ�ֺ���********************************************
*����ԭ��:	  IIC_SDA(u8 data,u8 Channel)
*��������:		
*******************************************************************************/
void IIC_SDA(u8 data,u8 Channel)
{	
	switch(Channel)
	{
		case 0:
			PBout(SDA0_PIN) = data;break;
		case 1:
			PBout(5) = data;break;
		case 2:
			PCout(10) = data;break;
		case 3:
			PCout(7) = data;break;
		case 4:
			PBout(15) = data;break;
	}
}

/**************************ʵ�ֺ���********************************************
*����ԭ��:		READ_SDA(u8 Channel)
*��������:		
*******************************************************************************/
u8 READ_SDA(u8 Channel)
{	
	switch(Channel)
	{
		case 0:
			return PBin(SDA0_PIN) ;break;
		case 1:
			return PBin(5);break;
		case 2:
			return PCin(10);break;
		case 3:
			return PCin(7);break;
		case 4:
			return PBin(15);break;
	}
	return 0;
}

/**************************ʵ�ֺ���********************************************
*����ԭ��:		void IIC_Init(void)
*��������:		��ʼ��I2C��Ӧ�Ľӿ����š�
*******************************************************************************/
void IIC_Init(void)
{			
	GPIO_InitTypeDef GPIO_InitStructure;
 	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB, ENABLE);			
  RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOC, ENABLE);			
	
 	//����PB6 PB7 Ϊ��©���  ˢ��Ƶ��Ϊ10Mhz
 	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_7 | GPIO_Pin_9;	
  GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;       
  GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
  //Ӧ�����õ�GPIOB 
  GPIO_Init(GPIOB, &GPIO_InitStructure);
	     
 	//����PB10 PB11 Ϊ��©���  ˢ��Ƶ��Ϊ10Mhz
 	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_5 | GPIO_Pin_6;	
  GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;       
  GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
  //Ӧ�����õ�GPIOB 
  GPIO_Init(GPIOB, &GPIO_InitStructure);
	
	 	//����PB10 PB11 Ϊ��©���  ˢ��Ƶ��Ϊ10Mhz
 	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_10 | GPIO_Pin_12;	
  GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;       
  GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
  //Ӧ�����õ�GPIOB 
  GPIO_Init(GPIOC, &GPIO_InitStructure);
	
		//����PB10 PB11 Ϊ��©���  ˢ��Ƶ��Ϊ10Mhz
 	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_6 | GPIO_Pin_7;	
  GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;       
  GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
  //Ӧ�����õ�GPIOB 
  GPIO_Init(GPIOC, &GPIO_InitStructure);
	
	//����PB10 PB11 Ϊ��©���  ˢ��Ƶ��Ϊ10Mhz
 	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_14 | GPIO_Pin_15;	
  GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;       
  GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
  //Ӧ�����õ�GPIOB 
  GPIO_Init(GPIOB, &GPIO_InitStructure);
	
  printf("IIC���߳�ʼ�����...\r\n");
}

/**************************ʵ�ֺ���********************************************
*����ԭ��:		void IIC_Start(void)
*��������:		����IIC��ʼ�ź�
*******************************************************************************/
void IIC_Start(u8 channel)
{
		SDA_OUT(channel);     //sda����� 
		IIC_SDA(1, channel);	  	  
		IIC_SCL(1, channel);
		delay_us(4);
		IIC_SDA(0, channel);//START:when CLK is high,DATA change form high to low 
		delay_us(4);
		IIC_SCL(0, channel);//ǯסI2C���ߣ�׼�����ͻ�������� 
}

/**************************ʵ�ֺ���********************************************
*����ԭ��:		void IIC_Stop(void)
*��������:	    //����IICֹͣ�ź�
*******************************************************************************/	  
void IIC_Stop(u8 channel)
{
		SDA_OUT(channel);//sda�����
		IIC_SCL(0, channel);
		IIC_SDA(0, channel);//STOP:when CLK is high DATA change form low to high
		delay_us(4);
		IIC_SCL(1, channel); 
		IIC_SDA(1, channel);//����I2C���߽����ź�
		delay_us(4);
}

/**************************ʵ�ֺ���********************************************
*����ԭ��:		u8 IIC_Wait_Ack(void)
*��������:	    �ȴ�Ӧ���źŵ��� 
//����ֵ��1������Ӧ��ʧ��
//        0������Ӧ��ɹ�
*******************************************************************************/
u8 IIC_Wait_Ack(u8 channel)
{
	u8 ucErrTime=0;
	SDA_IN(channel);      //SDA����Ϊ����  
	IIC_SDA(1, channel);delay_us(1);	   
	IIC_SCL(1, channel);delay_us(1);	 
	while(READ_SDA(channel))
	{
		ucErrTime++;
		if(ucErrTime>50)
		{
			IIC_Stop(channel);
			return 1;
		}
		delay_us(1);
	}
	IIC_SCL(0, channel);//ʱ�����0 	 
	return 0;  
} 

/**************************ʵ�ֺ���********************************************
*����ԭ��:		void IIC_Ack(void)
*��������:	    ����ACKӦ��
*******************************************************************************/
void IIC_Ack(u8 channel)
{
	IIC_SCL(0, channel);
	SDA_OUT(channel);
	IIC_SDA(0, channel);
	delay_us(2);
	IIC_SCL(1, channel);
	delay_us(2);
	IIC_SCL(0, channel);
}
	
/**************************ʵ�ֺ���********************************************
*����ԭ��:		void IIC_NAck(void)
*��������:	    ����NACKӦ��
*******************************************************************************/	    
void IIC_NAck(u8 channel)
{
	IIC_SCL(0, channel);
	SDA_OUT(channel);
	IIC_SDA(1, channel);
	delay_us(2);
	IIC_SCL(1, channel);
	delay_us(2);
	IIC_SCL(0, channel);
}					 				     

/**************************ʵ�ֺ���********************************************
*����ԭ��:		void IIC_Send_Byte(u8 txd)
*��������:	    IIC����һ���ֽ�
*******************************************************************************/		  
void IIC_Send_Byte(u8 txd ,u8 channel)
{                        
	u8 t;  
	SDA_OUT(channel); 	    
	IIC_SCL(0, channel);//����ʱ�ӿ�ʼ���ݴ���
	for(t=0;t<8;t++)
	{              
			IIC_SDA((txd&0x80)>>7, channel);
			txd<<=1; 	  
	delay_us(2);   
	IIC_SCL(1, channel);
	delay_us(2); 
	IIC_SCL(0, channel);	
	delay_us(2);
	}	

} 	 
   
/**************************ʵ�ֺ���********************************************
*����ԭ��:		u8 IIC_Read_Byte(unsigned char ack)
*��������:	    //��1���ֽڣ�ack=1ʱ������ACK��ack=0������nACK 
*******************************************************************************/  
u8 IIC_Read_Byte(unsigned char ack ,u8 channel)
{
	unsigned char i,receive=0;
	SDA_IN(channel);//SDA����Ϊ����
		for(i=0;i<8;i++ )
	{
				IIC_SCL(0, channel); 
				delay_us(2);
		IIC_SCL(1, channel);
				receive<<=1;
				if(READ_SDA(channel))receive++;   
		delay_us(2); 
		}					 
		if (ack)
				IIC_Ack(channel); //����ACK 
		else
				IIC_NAck(channel);//����nACK  

	return receive;
}

/**************************ʵ�ֺ���********************************************
*����ԭ��:		unsigned char I2C_ReadOneByte(unsigned char I2C_Addr,unsigned char addr)
*��������:	    ��ȡָ���豸 ָ���Ĵ�����һ��ֵ
����	I2C_Addr  Ŀ���豸��ַ
		addr	   �Ĵ�����ַ
����   ��������ֵ
*******************************************************************************/ 
unsigned char I2C_ReadOneByte(unsigned char I2C_Addr,unsigned char addr ,u8 channel)
{
	unsigned char res=0;
		IIC_Start(channel);	
		
		IIC_Send_Byte(I2C_Addr, channel);	   //����д����
		res++;
		IIC_Wait_Ack(channel);
		IIC_Send_Byte(addr, channel); res++;  //���͵�ַ
		IIC_Wait_Ack(channel);	  
		//IIC_Stop();//����һ��ֹͣ����	
		IIC_Start(channel);
		IIC_Send_Byte(I2C_Addr+1, channel); res++;          //�������ģʽ			   
		IIC_Wait_Ack(channel);
		res=IIC_Read_Byte(0, channel);	   
			IIC_Stop(channel);//����һ��ֹͣ����

	return res;
}


/**************************ʵ�ֺ���********************************************
*����ԭ��:		u8 IICreadBytes(u8 dev, u8 reg, u8 length, u8 *data)
*��������:	    ��ȡָ���豸 ָ���Ĵ����� length��ֵ
����	dev  Ŀ���豸��ַ
		reg	  �Ĵ�����ַ
		length Ҫ�����ֽ���
		*data  ���������ݽ�Ҫ��ŵ�ָ��
����   ���������ֽ�����
*******************************************************************************/ 
u8 IICreadBytes(u8 dev, u8 reg, u8 length, u8 *data ,u8 channel){
    u8 count = 0;
	u8 temp;
	IIC_Start(channel);
	IIC_Send_Byte(dev, channel);	   //����д����
	IIC_Wait_Ack(channel);
	IIC_Send_Byte(reg, channel);   //���͵�ַ
    IIC_Wait_Ack(channel);	  
	IIC_Start(channel);
	IIC_Send_Byte(dev+1, channel);  //�������ģʽ	
	IIC_Wait_Ack(channel);
	
    for(count=0;count<length;count++){
		 
		 if(count!=(length-1))
		 	temp = IIC_Read_Byte(1, channel);  //��ACK�Ķ�����
		 	else  
			temp = IIC_Read_Byte(0, channel);	 //���һ���ֽ�NACK

		data[count] = temp;
	}
    IIC_Stop(channel);//����һ��ֹͣ����
    return count;
}

/**************************ʵ�ֺ���********************************************
*����ԭ��:		u8 IICwriteBytes(u8 dev, u8 reg, u8 length, u8* data)
*��������:	    ������ֽ�д��ָ���豸 ָ���Ĵ���
����	dev  Ŀ���豸��ַ
		reg	  �Ĵ�����ַ
		length Ҫд���ֽ���
		*data  ��Ҫд�����ݵ��׵�ַ
����   �����Ƿ�ɹ�
*******************************************************************************/ 
u8 IICwriteBytes(u8 dev, u8 reg, u8 length, u8* data,u8 channel){
  
 	u8 count = 0;
	IIC_Start(channel);
	IIC_Send_Byte(dev, channel);	   //����д����
	IIC_Wait_Ack(channel);
	IIC_Send_Byte(reg, channel);   //���͵�ַ
    IIC_Wait_Ack(channel);	  
	for(count=0;count<length;count++){
		IIC_Send_Byte(data[count], channel); 
		IIC_Wait_Ack(channel); 
	 }
	IIC_Stop(channel);//����һ��ֹͣ����

    return 1; //status == 0;
}

/**************************ʵ�ֺ���********************************************
*����ԭ��:		u8 IICreadByte(u8 dev, u8 reg, u8 *data)
*��������:	    ��ȡָ���豸 ָ���Ĵ�����һ��ֵ
����	dev  Ŀ���豸��ַ
		reg	   �Ĵ�����ַ
		*data  ���������ݽ�Ҫ��ŵĵ�ַ
����   1
*******************************************************************************/ 
u8 IICreadByte(u8 dev, u8 reg, u8 *data, u8 channel){
	*data=I2C_ReadOneByte(dev, reg, channel);
    return 1;
}

/**************************ʵ�ֺ���********************************************
*����ԭ��:		unsigned char IICwriteByte(unsigned char dev, unsigned char reg, unsigned char data)
*��������:	    д��ָ���豸 ָ���Ĵ���һ���ֽ�
����	dev  Ŀ���豸��ַ
		reg	   �Ĵ�����ַ
		data  ��Ҫд����ֽ�
����   1
*******************************************************************************/ 
unsigned char IICwriteByte(unsigned char dev, unsigned char reg, unsigned char data, u8 channel){
    return IICwriteBytes(dev, reg, 1, &data, channel);
}

/**************************ʵ�ֺ���********************************************
*����ԭ��:		u8 IICwriteBits(u8 dev,u8 reg,u8 bitStart,u8 length,u8 data)
*��������:	    �� �޸� д ָ���豸 ָ���Ĵ���һ���ֽ� �еĶ��λ
����	dev  Ŀ���豸��ַ
		reg	   �Ĵ�����ַ
		bitStart  Ŀ���ֽڵ���ʼλ
		length   λ����
		data    ��Ÿı�Ŀ���ֽ�λ��ֵ
����   �ɹ� Ϊ1 
 		ʧ��Ϊ0
*******************************************************************************/ 
u8 IICwriteBits(u8 dev,u8 reg,u8 bitStart,u8 length,u8 data, u8 channel)
{

    u8 b;
    if (IICreadByte(dev, reg, &b, channel) != 0) {
        u8 mask = (0xFF << (bitStart + 1)) | 0xFF >> ((8 - bitStart) + length - 1);
        data <<= (8 - length);
        data >>= (7 - bitStart);
        b &= mask;
        b |= data;
        return IICwriteByte(dev, reg, b, channel);
    } else {
        return 0;
    }
}

/**************************ʵ�ֺ���********************************************
*����ԭ��:		u8 IICwriteBit(u8 dev, u8 reg, u8 bitNum, u8 data)
*��������:	    �� �޸� д ָ���豸 ָ���Ĵ���һ���ֽ� �е�1��λ
����	dev  Ŀ���豸��ַ
		reg	   �Ĵ�����ַ
		bitNum  Ҫ�޸�Ŀ���ֽڵ�bitNumλ
		data  Ϊ0 ʱ��Ŀ��λ������0 ���򽫱���λ
����   �ɹ� Ϊ1 
 		   ʧ��Ϊ0
*******************************************************************************/ 
u8 IICwriteBit(u8 dev, u8 reg, u8 bitNum, u8 data, u8 channel){
    u8 b;
    
    IICreadByte(dev, reg, &b, channel);
    b = (data != 0) ? (b | (1 << bitNum)) : (b & ~(1 << bitNum));
    
    return IICwriteByte(dev, reg, b, channel);
}

//------------------End of File----------------------------
