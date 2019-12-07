#include "stm32f10x.h"
#include "UART1.h"
#define SPI2_CS_High GPIO_SetBits(GPIOB, GPIO_Pin_12)
#define SPI2_CS_Low GPIO_ResetBits(GPIOB, GPIO_Pin_12)
/*配置SPI2为双向全双工，主机模式，8bit，时钟4分频*/
void SPI2_init(void)
{
	SPI_InitTypeDef SPI2_conf;
	GPIO_InitTypeDef GPIO_conf;

  RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB, ENABLE);//使能GPIOB时钟
  RCC_APB1PeriphClockCmd(RCC_APB1Periph_SPI2, ENABLE);//使能spi2

	GPIO_conf.GPIO_Pin=GPIO_Pin_13; //MISO,MOSI,SCK为复用推挽输出
	GPIO_conf.GPIO_Speed=GPIO_Speed_50MHz;
	GPIO_conf.GPIO_Mode=GPIO_Mode_AF_PP;
	GPIO_Init(GPIOB, &GPIO_conf);

	GPIO_conf.GPIO_Pin=GPIO_Pin_14; //MISO,MOSI,SCK为复用推挽输出
	GPIO_Init(GPIOB, &GPIO_conf);

	GPIO_conf.GPIO_Pin=GPIO_Pin_15; //MISO,MOSI,SCK为复用推挽输出
	GPIO_Init(GPIOB, &GPIO_conf);

	GPIO_conf.GPIO_Pin=GPIO_Pin_12; //NSS为IO推挽输出
	GPIO_conf.GPIO_Mode=GPIO_Mode_Out_PP;
	GPIO_Init(GPIOB, &GPIO_conf);


	///////////////////////设置///////////////////////////////////
	SPI2_conf.SPI_Direction=SPI_Direction_2Lines_FullDuplex;
	SPI2_conf.SPI_Mode=SPI_Mode_Master;
	SPI2_conf.SPI_DataSize=SPI_DataSize_8b;
	SPI2_conf.SPI_CPOL=SPI_CPOL_Low;
	SPI2_conf.SPI_CPHA=SPI_CPHA_1Edge;
	SPI2_conf.SPI_NSS=SPI_NSS_Soft;
	SPI2_conf.SPI_BaudRatePrescaler=SPI_BaudRatePrescaler_4;
	SPI2_conf.SPI_FirstBit=SPI_FirstBit_MSB;
	SPI2_conf.SPI_CRCPolynomial=7;
	SPI_Init(SPI2,&SPI2_conf);

	SPI_Cmd(SPI2, ENABLE);

	SPI2_CS_High;   //片选置高
	////////////////////////////////////////////////////////////////
	printf("SPI初始化\t\t完成\r\n");
}
/*
通过SPI发送，并且接受到一个字节的数据
data：发送数据的存放指针
返回值：读取的数据
*/
u8 SPI_send_and_receive_byte(u8 *data)
{
	while (SPI_I2S_GetFlagStatus(SPI2, SPI_I2S_FLAG_TXE) == RESET);
	SPI_I2S_SendData(SPI2,*data);
	while (SPI_I2S_GetFlagStatus(SPI2, SPI_I2S_FLAG_RXNE) == RESET);
	return SPI_I2S_ReceiveData(SPI2);
}
/*
对DW1000芯片写入数据
addr:寄存器地址
offset_index:偏移量
data:要写入数据的首地址
length：写入数据的长度
*/
void Write_DW1000(u8 addr,u16 offset_index,u8 *data,u16 length)
{
	u8 SPI_send_and_receive_byte(u8 *data) ;
	u16 i;
	u8 tmp;
   	SPI2_CS_Low;
	if(offset_index==0x00)
	{
		tmp=addr|0x80;
		SPI_send_and_receive_byte(&tmp);
	}
	else if(offset_index<=0x007f)
	{
		tmp=addr|0xC0;
		SPI_send_and_receive_byte(&tmp);
		tmp=offset_index;
		SPI_send_and_receive_byte(&tmp);
	}
	else
	{
		tmp=addr|0xC0;
		SPI_send_and_receive_byte(&tmp);
		tmp=offset_index;
		tmp|=0x80;
		SPI_send_and_receive_byte(&tmp);
		tmp=offset_index>>7;
		SPI_send_and_receive_byte(&tmp);
	}
	for(i=0;i<length;i++)
	{
		SPI_send_and_receive_byte(data++);
	}
	SPI2_CS_High;
}
/*
从DW1000芯片读出数据
addr:寄存器地址
offset_index:偏移量
data:存放读出数据的首地址
length：读出数据的长度
*/
void Read_DW1000(u8 addr,u16 offset_index,u8 *data,u16 length)
{
	u8 SPI_send_and_receive_byte(u8 *data);
	u16 i;
	u8 tmp;
	SPI2_CS_Low;
	if(offset_index==0x00)
	{
		SPI_send_and_receive_byte(&addr);
	}
	else if(offset_index<=0x007f)
	{
		tmp=addr|0x40;
		SPI_send_and_receive_byte(&tmp);
		tmp=offset_index;
		SPI_send_and_receive_byte(&tmp);
	}
	else
	{
		tmp=addr|0x40;
		SPI_send_and_receive_byte(&tmp);
		tmp=offset_index;
		tmp|=0x80;
		SPI_send_and_receive_byte(&tmp);
		tmp=offset_index>>7;
		SPI_send_and_receive_byte(&tmp);
	}
	for(i=0;i<length;i++)
	{
		*(data++)=SPI_send_and_receive_byte(&addr);
	}
	SPI2_CS_High;
}
