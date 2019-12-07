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
HMC5883.c file
��д�ߣ�С��  (Camel)
����E-mail��375836945@qq.com
���뻷����MDK-Lite  Version: 4.23
����ʱ��: 2014-01-28
���ܣ�
1.��ʼ����������HMC5883
2.��Ŀǰ��4.1�����棬���оƬ��Ĭ��û���ӡ���
3.����ͨ����֮����û�ӣ���Ϊԭ��ͼ�ϣ�IIC �������ߺ�ʱ���߻����ˣ������λ����Ȥ�����оƬ��������ϵ�ң��Ҹ��ߴ����ô��������~~
------------------------------------
*/

#include "HMC5883L.h"
#include "config.h"
float Compass_HMC[ChannelNum][3];
float HMC5883_lastx[ChannelNum],HMC5883_lasty[ChannelNum],HMC5883_lastz[ChannelNum];

int16_t  HMC5883_FIFO[ChannelNum][3][11]; //�������˲�
void HMC58X3_getRaw(int16_t *x,int16_t *y,int16_t *z,u8 Channel);

/**************************ʵ�ֺ���********************************************
*����ԭ��:	   unsigned char HMC5883_IS_newdata(void)
*��������:	   ��ȡDRDY ���ţ��ж��Ƿ������һ��ת��
 Low for 250 ��sec when data is placed in the data output registers. 
���������  ��
���������  ������ת���������1  ������� 0
*******************************************************************************/
//unsigned char HMC5883_IS_newdata(void)
//{
// 	if(GPIO_ReadInputDataBit(GPIOB,GPIO_Pin_4)==Bit_SET){
//	  return 1;
//	 }
//	 else return 0;
//}

/**************************ʵ�ֺ���********************************************
*����ԭ��:	   void HMC58X3_FIFO_init(void)
*��������:	   ������ȡ100�����ݣ��Գ�ʼ��FIFO����
���������  ��
���������  ��
*******************************************************************************/
void HMC58X3_FIFO_init(u8 Channel)
{
  int16_t temp[3];
  unsigned char i;
  for(i=0;i<50;i++){
  HMC58X3_getRaw(&temp[0],&temp[1],&temp[2], Channel);
  delay_us(200);  //��ʱ�ٶ�ȡ����
  }
}

/**************************ʵ�ֺ���********************************************
*����ԭ��:	   void  HMC58X3_newValues(int16_t x,int16_t y,int16_t z)
*��������:	   ����һ�����ݵ�FIFO����
���������  �������������Ӧ��ADCֵ
���������  ��
*******************************************************************************/
void  HMC58X3_newValues(int16_t x,int16_t y,int16_t z,u8 Channel)
{
	unsigned char i ;
	int32_t sum=0;

	for(i=1;i<10;i++){
		HMC5883_FIFO[Channel][0][i-1]=HMC5883_FIFO[Channel][0][i];
		HMC5883_FIFO[Channel][1][i-1]=HMC5883_FIFO[Channel][1][i];
		HMC5883_FIFO[Channel][2][i-1]=HMC5883_FIFO[Channel][2][i];
	}

	HMC5883_FIFO[Channel][0][9]=x;
	HMC5883_FIFO[Channel][1][9]=y;
	HMC5883_FIFO[Channel][2][9]=z;

	sum=0;
	for(i=0;i<10;i++){	//ȡ�����ڵ�ֵ���������ȡƽ��
   		sum+=HMC5883_FIFO[Channel][0][i];
	}
	HMC5883_FIFO[Channel][0][10]=sum/10;	//��ƽ��ֵ����

	sum=0;
	for(i=0;i<10;i++){
   		sum+=HMC5883_FIFO[Channel][1][i];
	}
	HMC5883_FIFO[Channel][1][10]=sum/10;

	sum=0;
	for(i=0;i<10;i++){
   		sum+=HMC5883_FIFO[Channel][2][i];
	}
	HMC5883_FIFO[Channel][2][10]=sum/10;
} //HMC58X3_newValues

/**************************ʵ�ֺ���********************************************
*����ԭ��:	   void HMC58X3_writeReg(unsigned char reg, unsigned char val)
*��������:	   дHMC5883L�ļĴ���
���������    reg  �Ĵ�����ַ
			  val   Ҫд���ֵ	
���������  ��
*******************************************************************************/
void HMC58X3_writeReg(unsigned char reg, unsigned char val, u8 Channel) {
  IICwriteByte(HMC58X3_ADDR,reg,val,Channel);
}

/**************************ʵ�ֺ���********************************************
*����ԭ��:	  void HMC58X3_getRaw(int16_t *x,int16_t *y,int16_t *z)
*��������:	   дHMC5883L�ļĴ���
���������    reg  �Ĵ�����ַ
			  val   Ҫд���ֵ	
���������  ��
*******************************************************************************/
void HMC58X3_getRaw(int16_t *x,int16_t *y,int16_t *z,u8 Channel) {
   unsigned char vbuff[6];
   vbuff[0]=vbuff[1]=vbuff[2]=vbuff[3]=vbuff[4]=vbuff[5]=0;
   IICreadBytes(HMC58X3_ADDR,HMC58X3_R_XM,6,vbuff, Channel);
   HMC58X3_newValues(((int16_t)vbuff[0] << 8) | vbuff[1],((int16_t)vbuff[4] << 8) | vbuff[5],((int16_t)vbuff[2] << 8) | vbuff[3], Channel);
   *x = HMC5883_FIFO[Channel][0][10];
   *y = HMC5883_FIFO[Channel][1][10];
   *z = HMC5883_FIFO[Channel][2][10];
}

/**************************ʵ�ֺ���********************************************
*����ԭ��:	  void HMC58X3_getValues(int16_t *x,int16_t *y,int16_t *z)
*��������:	   ��ȡ �����Ƶĵ�ǰADCֵ
���������    �������Ӧ�����ָ��	
���������  ��
*******************************************************************************/
void HMC58X3_getlastValues(int16_t *x,int16_t *y,int16_t *z,u8 Channel) {
  *x = HMC5883_FIFO[Channel][0][10];
  *y = HMC5883_FIFO[Channel][1][10]; 
  *z = HMC5883_FIFO[Channel][2][10]; 
}

/**************************ʵ�ֺ���********************************************
*����ԭ��:	  void HMC58X3_mgetValues(float *arry)
*��������:	   ��ȡ У����� ������ADCֵ
���������    �������ָ��	
���������  ��
*******************************************************************************/
void HMC58X3_mgetValues(float *arry,u8 Channel) {
  int16_t xr,yr,zr;
  HMC58X3_getRaw(&xr, &yr, &zr, Channel);
  arry[0]= HMC5883_lastx[Channel]=(float)(xr);
  arry[1]= HMC5883_lasty[Channel]=(float)(yr);
  arry[2]= HMC5883_lastz[Channel]=(float)(zr);
}

/**************************ʵ�ֺ���********************************************
*����ԭ��:	  void HMC58X3_setGain(unsigned char gain)
*��������:	   ���� 5883L������
���������     Ŀ������ 0-7
���������  ��
*******************************************************************************/
void HMC58X3_setGain(unsigned char gain,u8 Channel) { 
  // 0-7, 1 default
  if (gain > 7) return;
  HMC58X3_writeReg(HMC58X3_R_CONFB, gain << 5, Channel);
}

/**************************ʵ�ֺ���********************************************
*����ԭ��:	   void HMC58X3_setMode(unsigned char mode)
*��������:	   ���� 5883L�Ĺ���ģʽ
���������     ģʽ
���������     ��
*******************************************************************************/
void HMC58X3_setMode(unsigned char mode,u8 Channel) {
  if (mode > 2) {
    return;
  }
  HMC58X3_writeReg(HMC58X3_R_MODE, mode, Channel);
  delay_us(100);
}

/**************************ʵ�ֺ���********************************************
*����ԭ��:	   void HMC58X3_init(u8 setmode)
*��������:	   ���� 5883L�Ĺ���ģʽ
���������     ģʽ
���������     ��
*******************************************************************************/
void HMC58X3_init(u8 setmode,u8 Channel) {

  if (setmode) {
    HMC58X3_setMode(0, Channel);
  }
  HMC58X3_writeReg(HMC58X3_R_CONFA, 0x70, Channel); // 8 samples averaged, 75Hz frequency, no artificial bias.
  HMC58X3_writeReg(HMC58X3_R_CONFB, 0xA0, Channel);
  HMC58X3_writeReg(HMC58X3_R_MODE,  0x00, Channel);

}

/**************************ʵ�ֺ���********************************************
*����ԭ��:	  void HMC58X3_setDOR(unsigned char DOR)
*��������:	   ���� 5883L�� �����������
���������     ����ֵ
0 -> 0.75Hz  |   1 -> 1.5Hz
2 -> 3Hz     |   3 -> 7.5Hz
4 -> 15Hz    |   5 -> 30Hz
6 -> 75Hz  
���������  ��
*******************************************************************************/
void HMC58X3_setDOR(unsigned char DOR,u8 Channel) {
  if (DOR>6) return;
  HMC58X3_writeReg(HMC58X3_R_CONFA,DOR<<2, Channel);
}

/**************************ʵ�ֺ���********************************************
*����ԭ��:	  void HMC58X3_getID(char id[3])
*��������:	  ��ȡоƬ��ID
���������    ID��ŵ�����
���������  ��
*******************************************************************************/
void HMC58X3_getID(char id[3],u8 Channel) 
{
      id[0]=I2C_ReadOneByte(HMC58X3_ADDR,HMC58X3_R_IDA, Channel);  
      id[1]=I2C_ReadOneByte(HMC58X3_ADDR,HMC58X3_R_IDB, Channel);
      id[2]=I2C_ReadOneByte(HMC58X3_ADDR,HMC58X3_R_IDC, Channel);
}   // getID().

/**************************ʵ�ֺ���********************************************
*����ԭ��:	  void HMC5883_Check()
*��������:	  ���HMC5883�Ƿ�������
���������    
���������    
*******************************************************************************/
void HMC5883_Check(u8 Channel) 
{
  char ID_temp[3];
  HMC58X3_getID(&ID_temp[0], Channel); //��ID��ʱ���鸳ֵ
  
  if((ID_temp[0]==0x48)&&(ID_temp[1]==0x34)&&(ID_temp[2]==0x33))//HMC�Ĺ̶�ID��Ϊ�����ֽڣ�16���Ʊ�ʾ�ֱ�Ϊ48,34,33
  printf("�Ѽ�⵽��������HMC5883L...\r\n");
  else printf("δ��⵽��������HMC5883L...\r\n");
  
  
}   


/**************************ʵ�ֺ���********************************************
*����ԭ��:	  void HMC5883L_SetUp(void)
*��������:	  ��ʼ�� HMC5883L ʹ֮�������״̬
���������     	
���������    ��
*******************************************************************************/
void HMC5883L_SetUp(u8 Channel)
{ 
  HMC5883_Check(Channel); //���HMC5883�Ƿ����
  HMC58X3_init(0, Channel); // Don't set mode yet, we'll do that later on.
  HMC58X3_setMode(0, Channel);
  HMC58X3_setDOR(6, Channel);  //75hz ������
  HMC58X3_FIFO_init(Channel);
}


//------------------End of File----------------------------
