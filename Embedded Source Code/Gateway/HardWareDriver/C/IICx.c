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
编写者：小马  (Camel)
作者E-mail：375836945@qq.com
编译环境：MDK-Lite  Version: 4.23
初版时间: 2014-01-28
功能：
1.初始化软件IIC协议
2.软件IIC协议的引脚，也是STM32硬件IIC的引脚。只是我没有这个功能
------------------------------------
*/
//STM32模拟IIC协议，STM32的硬件IIC有些BUG
//细节有空再改
//最后修改:2014-03-11


#include "IICx.h"
#include "delay.h"
#include "Led.h"
#include "UART1.h"
#include "stdio.h"

/**************************实现函数********************************************
*函数原型:		void SDA_IN(u8 Channel)
*功　　能:		
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

/**************************实现函数********************************************
*函数原型:		SDA_OUT(u8 Channel)
*功　　能:		
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

/**************************实现函数********************************************
*函数原型:		IIC_SCL(u8 data,u8 Channel)
*功　　能:		
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

/**************************实现函数********************************************
*函数原型:	  IIC_SDA(u8 data,u8 Channel)
*功　　能:		
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

/**************************实现函数********************************************
*函数原型:		READ_SDA(u8 Channel)
*功　　能:		
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

/**************************实现函数********************************************
*函数原型:		void IIC_Init(void)
*功　　能:		初始化I2C对应的接口引脚。
*******************************************************************************/
void IIC_Init(void)
{			
	GPIO_InitTypeDef GPIO_InitStructure;
 	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB, ENABLE);			
  RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOC, ENABLE);			
	
 	//配置PB6 PB7 为开漏输出  刷新频率为10Mhz
 	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_7 | GPIO_Pin_9;	
  GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;       
  GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
  //应用配置到GPIOB 
  GPIO_Init(GPIOB, &GPIO_InitStructure);
	     
 	//配置PB10 PB11 为开漏输出  刷新频率为10Mhz
 	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_5 | GPIO_Pin_6;	
  GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;       
  GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
  //应用配置到GPIOB 
  GPIO_Init(GPIOB, &GPIO_InitStructure);
	
	 	//配置PB10 PB11 为开漏输出  刷新频率为10Mhz
 	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_10 | GPIO_Pin_12;	
  GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;       
  GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
  //应用配置到GPIOB 
  GPIO_Init(GPIOC, &GPIO_InitStructure);
	
		//配置PB10 PB11 为开漏输出  刷新频率为10Mhz
 	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_6 | GPIO_Pin_7;	
  GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;       
  GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
  //应用配置到GPIOB 
  GPIO_Init(GPIOC, &GPIO_InitStructure);
	
	//配置PB10 PB11 为开漏输出  刷新频率为10Mhz
 	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_14 | GPIO_Pin_15;	
  GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;       
  GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
  //应用配置到GPIOB 
  GPIO_Init(GPIOB, &GPIO_InitStructure);
	
  printf("IIC总线初始化完成...\r\n");
}

/**************************实现函数********************************************
*函数原型:		void IIC_Start(void)
*功　　能:		产生IIC起始信号
*******************************************************************************/
void IIC_Start(u8 channel)
{
		SDA_OUT(channel);     //sda线输出 
		IIC_SDA(1, channel);	  	  
		IIC_SCL(1, channel);
		delay_us(4);
		IIC_SDA(0, channel);//START:when CLK is high,DATA change form high to low 
		delay_us(4);
		IIC_SCL(0, channel);//钳住I2C总线，准备发送或接收数据 
}

/**************************实现函数********************************************
*函数原型:		void IIC_Stop(void)
*功　　能:	    //产生IIC停止信号
*******************************************************************************/	  
void IIC_Stop(u8 channel)
{
		SDA_OUT(channel);//sda线输出
		IIC_SCL(0, channel);
		IIC_SDA(0, channel);//STOP:when CLK is high DATA change form low to high
		delay_us(4);
		IIC_SCL(1, channel); 
		IIC_SDA(1, channel);//发送I2C总线结束信号
		delay_us(4);
}

/**************************实现函数********************************************
*函数原型:		u8 IIC_Wait_Ack(void)
*功　　能:	    等待应答信号到来 
//返回值：1，接收应答失败
//        0，接收应答成功
*******************************************************************************/
u8 IIC_Wait_Ack(u8 channel)
{
	u8 ucErrTime=0;
	SDA_IN(channel);      //SDA设置为输入  
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
	IIC_SCL(0, channel);//时钟输出0 	 
	return 0;  
} 

/**************************实现函数********************************************
*函数原型:		void IIC_Ack(void)
*功　　能:	    产生ACK应答
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
	
/**************************实现函数********************************************
*函数原型:		void IIC_NAck(void)
*功　　能:	    产生NACK应答
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

/**************************实现函数********************************************
*函数原型:		void IIC_Send_Byte(u8 txd)
*功　　能:	    IIC发送一个字节
*******************************************************************************/		  
void IIC_Send_Byte(u8 txd ,u8 channel)
{                        
	u8 t;  
	SDA_OUT(channel); 	    
	IIC_SCL(0, channel);//拉低时钟开始数据传输
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
   
/**************************实现函数********************************************
*函数原型:		u8 IIC_Read_Byte(unsigned char ack)
*功　　能:	    //读1个字节，ack=1时，发送ACK，ack=0，发送nACK 
*******************************************************************************/  
u8 IIC_Read_Byte(unsigned char ack ,u8 channel)
{
	unsigned char i,receive=0;
	SDA_IN(channel);//SDA设置为输入
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
				IIC_Ack(channel); //发送ACK 
		else
				IIC_NAck(channel);//发送nACK  

	return receive;
}

/**************************实现函数********************************************
*函数原型:		unsigned char I2C_ReadOneByte(unsigned char I2C_Addr,unsigned char addr)
*功　　能:	    读取指定设备 指定寄存器的一个值
输入	I2C_Addr  目标设备地址
		addr	   寄存器地址
返回   读出来的值
*******************************************************************************/ 
unsigned char I2C_ReadOneByte(unsigned char I2C_Addr,unsigned char addr ,u8 channel)
{
	unsigned char res=0;
		IIC_Start(channel);	
		
		IIC_Send_Byte(I2C_Addr, channel);	   //发送写命令
		res++;
		IIC_Wait_Ack(channel);
		IIC_Send_Byte(addr, channel); res++;  //发送地址
		IIC_Wait_Ack(channel);	  
		//IIC_Stop();//产生一个停止条件	
		IIC_Start(channel);
		IIC_Send_Byte(I2C_Addr+1, channel); res++;          //进入接收模式			   
		IIC_Wait_Ack(channel);
		res=IIC_Read_Byte(0, channel);	   
			IIC_Stop(channel);//产生一个停止条件

	return res;
}


/**************************实现函数********************************************
*函数原型:		u8 IICreadBytes(u8 dev, u8 reg, u8 length, u8 *data)
*功　　能:	    读取指定设备 指定寄存器的 length个值
输入	dev  目标设备地址
		reg	  寄存器地址
		length 要读的字节数
		*data  读出的数据将要存放的指针
返回   读出来的字节数量
*******************************************************************************/ 
u8 IICreadBytes(u8 dev, u8 reg, u8 length, u8 *data ,u8 channel){
    u8 count = 0;
	u8 temp;
	IIC_Start(channel);
	IIC_Send_Byte(dev, channel);	   //发送写命令
	IIC_Wait_Ack(channel);
	IIC_Send_Byte(reg, channel);   //发送地址
    IIC_Wait_Ack(channel);	  
	IIC_Start(channel);
	IIC_Send_Byte(dev+1, channel);  //进入接收模式	
	IIC_Wait_Ack(channel);
	
    for(count=0;count<length;count++){
		 
		 if(count!=(length-1))
		 	temp = IIC_Read_Byte(1, channel);  //带ACK的读数据
		 	else  
			temp = IIC_Read_Byte(0, channel);	 //最后一个字节NACK

		data[count] = temp;
	}
    IIC_Stop(channel);//产生一个停止条件
    return count;
}

/**************************实现函数********************************************
*函数原型:		u8 IICwriteBytes(u8 dev, u8 reg, u8 length, u8* data)
*功　　能:	    将多个字节写入指定设备 指定寄存器
输入	dev  目标设备地址
		reg	  寄存器地址
		length 要写的字节数
		*data  将要写的数据的首地址
返回   返回是否成功
*******************************************************************************/ 
u8 IICwriteBytes(u8 dev, u8 reg, u8 length, u8* data,u8 channel){
  
 	u8 count = 0;
	IIC_Start(channel);
	IIC_Send_Byte(dev, channel);	   //发送写命令
	IIC_Wait_Ack(channel);
	IIC_Send_Byte(reg, channel);   //发送地址
    IIC_Wait_Ack(channel);	  
	for(count=0;count<length;count++){
		IIC_Send_Byte(data[count], channel); 
		IIC_Wait_Ack(channel); 
	 }
	IIC_Stop(channel);//产生一个停止条件

    return 1; //status == 0;
}

/**************************实现函数********************************************
*函数原型:		u8 IICreadByte(u8 dev, u8 reg, u8 *data)
*功　　能:	    读取指定设备 指定寄存器的一个值
输入	dev  目标设备地址
		reg	   寄存器地址
		*data  读出的数据将要存放的地址
返回   1
*******************************************************************************/ 
u8 IICreadByte(u8 dev, u8 reg, u8 *data, u8 channel){
	*data=I2C_ReadOneByte(dev, reg, channel);
    return 1;
}

/**************************实现函数********************************************
*函数原型:		unsigned char IICwriteByte(unsigned char dev, unsigned char reg, unsigned char data)
*功　　能:	    写入指定设备 指定寄存器一个字节
输入	dev  目标设备地址
		reg	   寄存器地址
		data  将要写入的字节
返回   1
*******************************************************************************/ 
unsigned char IICwriteByte(unsigned char dev, unsigned char reg, unsigned char data, u8 channel){
    return IICwriteBytes(dev, reg, 1, &data, channel);
}

/**************************实现函数********************************************
*函数原型:		u8 IICwriteBits(u8 dev,u8 reg,u8 bitStart,u8 length,u8 data)
*功　　能:	    读 修改 写 指定设备 指定寄存器一个字节 中的多个位
输入	dev  目标设备地址
		reg	   寄存器地址
		bitStart  目标字节的起始位
		length   位长度
		data    存放改变目标字节位的值
返回   成功 为1 
 		失败为0
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

/**************************实现函数********************************************
*函数原型:		u8 IICwriteBit(u8 dev, u8 reg, u8 bitNum, u8 data)
*功　　能:	    读 修改 写 指定设备 指定寄存器一个字节 中的1个位
输入	dev  目标设备地址
		reg	   寄存器地址
		bitNum  要修改目标字节的bitNum位
		data  为0 时，目标位将被清0 否则将被置位
返回   成功 为1 
 		   失败为0
*******************************************************************************/ 
u8 IICwriteBit(u8 dev, u8 reg, u8 bitNum, u8 data, u8 channel){
    u8 b;
    
    IICreadByte(dev, reg, &b, channel);
    b = (data != 0) ? (b | (1 << bitNum)) : (b & ~(1 << bitNum));
    
    return IICwriteByte(dev, reg, b, channel);
}

//------------------End of File----------------------------
