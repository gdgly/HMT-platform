#ifndef __IIC1_H
#define __IIC1_H
#include "stm32f10x.h"



//IO�ڲ����궨��
#define BITBAND(addr, bitnum) ((addr & 0xF0000000)+0x2000000+((addr &0xFFFFF)<<5)+(bitnum<<2)) 
#define MEM_ADDR(addr)  *((volatile unsigned long  *)(addr)) 
#define BIT_ADDR(addr, bitnum)   MEM_ADDR(BITBAND(addr, bitnum))  

//IO�ڵ�ַӳ��
#define GPIOA_ODR_Addr    (GPIOA_BASE+12) //0x4001080C 
#define GPIOB_ODR_Addr    (GPIOB_BASE+12) //0x40010C0C 
#define GPIOC_ODR_Addr    (GPIOC_BASE+12) //0x4001100C 
#define GPIOD_ODR_Addr    (GPIOD_BASE+12) //0x4001140C 
#define GPIOE_ODR_Addr    (GPIOE_BASE+12) //0x4001180C 
#define GPIOF_ODR_Addr    (GPIOF_BASE+12) //0x40011A0C    
#define GPIOG_ODR_Addr    (GPIOG_BASE+12) //0x40011E0C    

#define GPIOA_IDR_Addr    (GPIOA_BASE+8) //0x40010808 
#define GPIOB_IDR_Addr    (GPIOB_BASE+8) //0x40010C08 
#define GPIOC_IDR_Addr    (GPIOC_BASE+8) //0x40011008 
#define GPIOD_IDR_Addr    (GPIOD_BASE+8) //0x40011408 
#define GPIOE_IDR_Addr    (GPIOE_BASE+8) //0x40011808 
#define GPIOF_IDR_Addr    (GPIOF_BASE+8) //0x40011A08 
#define GPIOG_IDR_Addr    (GPIOG_BASE+8) //0x40011E08 


#define PBout(n)   BIT_ADDR(GPIOB_ODR_Addr,n)  //��� 
#define PBin(n)    BIT_ADDR(GPIOB_IDR_Addr,n)  //���� 
   	   		   
////�����ӿڣ�GPIOģ��IIC
//SCL-->PB6
//SDA-->PB7
#define SDA1_IN()  {GPIOB->CRL&=0X0FFFFFFF;GPIOB->CRL|=0x80000000;}
#define SDA1_OUT() {GPIOB->CRL&=0X0FFFFFFF;GPIOB->CRL|=0x30000000;}


//IO��������	 
#define IIC1_SCL    PBout(6) //SCL
#define IIC1_SDA    PBout(7) //SDA	 
#define READ1_SDA   PBin(7)  //����SDA 

//IIC���в�������
void IIC1_Init(void);          //��ʼ��IIC��IO��				 
void IIC1_Start(void);			   	//����IIC��ʼ�ź�
void IIC1_Stop(void);	  			//����IICֹͣ�ź�
void IIC1_Send_Byte(u8 txd);			//IIC����һ���ֽ�
u8 IIC1_Read_Byte(unsigned char ack);//IIC��ȡһ���ֽ�
u8 IIC1_Wait_Ack(void); 				//IIC�ȴ�ACK�ź�
void IIC1_Ack(void);					//IIC����ACK�ź�
void IIC1_NAck(void);				//IIC������ACK�ź�

void IIC1_Write_One_Byte(u8 daddr,u8 addr,u8 data);
u8 IIC1_Read_One_Byte(u8 daddr,u8 addr);	 
unsigned char I2C1_Readkey(unsigned char I2C_Addr);

unsigned char I2C1_ReadOneByte(unsigned char I2C_Addr,unsigned char addr);
unsigned char IIC1writeByte(unsigned char dev, unsigned char reg, unsigned char data);
u8 IIC1writeBytes(u8 dev, u8 reg, u8 length, u8* data);
u8 IIC1writeBits(u8 dev,u8 reg,u8 bitStart,u8 length,u8 data);
u8 IIC1writeBit(u8 dev,u8 reg,u8 bitNum,u8 data);
u8 IIC1readBytes(u8 dev, u8 reg, u8 length, u8 *data);

#endif

//------------------End of File----------------------------







