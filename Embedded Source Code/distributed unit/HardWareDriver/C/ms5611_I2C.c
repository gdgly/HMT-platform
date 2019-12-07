/* MS5611.c file
��д�ߣ�lisn3188
��ַ��www.chiplab7.com
����E-mail��lisn3188@163.com
���뻷����MDK-Lite  Version: 4.23
����ʱ��: 2012-06-25
���ԣ� ���������ڵ���ʵ���ҵ�[Captain �ɿذ�]����ɲ���

ռ����Դ��
1. I2C �ӿڷ���MS561101BA
2. ��ȡ ��ǰϵͳ��ʱ��  ��ȷ���Ƿ������ת��

���ܣ�
�ṩMS5611 ��ʼ�� ���� ��ȡ�¶� ��ѹ API
------------------------------------
 */
#include "ms5611_I2C.h"
#include <math.h>

#define MS5611Press_OSR  MS561101BA_OSR_4096  //��ѹ��������
#define MS5611Temp_OSR   MS561101BA_OSR_4096  //�¶Ȳ�������

// ��ѹ��״̬��
#define SCTemperature  0x01	  //��ʼ �¶�ת��
#define CTemperatureing  0x02  //����ת���¶�
#define SCPressure  0x03	  //��ʼת�� ��ѹ
#define SCPressureing  0x04	  //����ת����ѹֵ

#define MOVAVG_SIZE  10	   //������� 10������

const float  MS5611_Lowpass = 7.9577e-3f;  //10hz

static uint8_t  Now_doing[ChannelNum] = {SCTemperature, SCTemperature};	//��ǰת��״̬
static uint16_t PROM_C[ChannelNum][MS561101BA_PROM_REG_COUNT]; //�궨ֵ���
static uint32_t Current_delay[ChannelNum];	   //ת����ʱʱ�� us 
static uint32_t Start_Convert_Time[ChannelNum];   //����ת��ʱ�� ʱ�� us 
static int32_t  tempCache[ChannelNum];
uint8_t ALT_Updated[ChannelNum] = {0,0}; //��ѹ�Ƹ߶ȸ�����ɱ�־��
static float Alt_Offset_cm[ChannelNum] = {0,0};
float avg_Pressure[ChannelNum];
float ALT_Update_Interval[ChannelNum] = {0.0,0.0}; //���θ߶Ȳ�����֮���ʱ����
uint8_t MS5611BA_flag = 0;
//units (Celsius degrees*100, mbar*100  ).
//��λ [�¶� 0.01��] [��ѹ ��]  [�߶�0.01��] 
float MS5611_Temperature[ChannelNum],MS5611_Pressure[ChannelNum],MS5611_Altitude[ChannelNum];

u8 MS5611_Complete[ChannelNum] = {1,1,1,1,1};

// ��ʱ��  ��λ us 	  ��ͬ�Ĳ������ȶ�Ӧ��ͬ����ʱֵ
uint32_t MS5611_Delay_us[9] = {
	1500,//MS561101BA_OSR_256 0.9ms  0x00
	1500,//MS561101BA_OSR_256 0.9ms  
	2000,//MS561101BA_OSR_512 1.2ms  0x02
	2000,//MS561101BA_OSR_512 1.2ms
	3000,//MS561101BA_OSR_1024 2.3ms 0x04
	3000,//MS561101BA_OSR_1024 2.3ms
	5000,//MS561101BA_OSR_2048 4.6ms 0x06
	5000,//MS561101BA_OSR_2048 4.6ms
	11000,//MS561101BA_OSR_4096 9.1ms 0x08
};

// FIFO ����					
static float Temp_buffer[ChannelNum][MOVAVG_SIZE],Press_buffer[ChannelNum][MOVAVG_SIZE],Alt_buffer[ChannelNum][MOVAVG_SIZE];
static uint8_t temp_index[ChannelNum]={0, 0},press_index[ChannelNum]={0, 0};  //����ָ��

//���һ���µ�ֵ�� �¶ȶ��� �����˲�
void MS561101BA_NewTemp(float val, u8 Channel) {
  Temp_buffer[Channel][temp_index[Channel]] = val;
  temp_index[Channel] = (temp_index[Channel] + 1) % MOVAVG_SIZE;
}

//���һ���µ�ֵ�� ��ѹ���� �����˲�
void MS561101BA_NewPress(float val, u8 Channel) {

		Press_buffer[Channel][press_index[Channel]] = val;
		press_index[Channel] = (press_index[Channel] + 1) % MOVAVG_SIZE;

}

//���һ���µ�ֵ�� �߶ȶ��� �����˲�
void MS561101BA_NewAlt(float val, u8 Channel) {
  int16_t i;
  static uint32_t alt_lastupdate , temp;
  temp = micros();
  ALT_Update_Interval[Channel] = ((float)(temp - alt_lastupdate))/1000000.0f;
  alt_lastupdate = temp;
  for(i=1;i<MOVAVG_SIZE;i++)
  Alt_buffer[Channel][i-1] = Alt_buffer[Channel][i];
  Alt_buffer[Channel][MOVAVG_SIZE-1] = val;
}

//ȡ��ѹ�Ƶ�D�仯��
float MS5611BA_Get_D(u8 Channel){
	float new=0,old=0;
	int16_t i;
	for(i=0;i<MOVAVG_SIZE/2;i++)
		old += Alt_buffer[Channel][i];
	old /= (MOVAVG_SIZE/2);

	for(i=MOVAVG_SIZE/2;i<MOVAVG_SIZE;i++)
	    new += Alt_buffer[Channel][i];
	new /= (MOVAVG_SIZE/2);

	return new - old;
}

//��ȡ���� ��ƽ��ֵ
float MS561101BA_getAvg(float * buff, int size) {
  float sum = 0.0;
  int i;
  for(i=0; i<size; i++) {
    sum += buff[i];
  }
  return sum / size;
}

/**************************ʵ�ֺ���********************************************
*����ԭ��:		void MS561101BA_readPROM(void)
*��������:	    ��ȡ MS561101B �Ĺ����궨ֵ
��ȡ ��ѹ�Ƶı궨ֵ  ���������¶Ⱥ���ѹ�Ķ���
*******************************************************************************/
void MS561101BA_readPROM(u8 Channel) {
  u8  inth,intl;
  int i;
  for (i=0;i<MS561101BA_PROM_REG_COUNT;i++) {
		IIC_Start(Channel);
    	IIC_Send_Byte(MS5611_ADDR, Channel);
		IIC_Wait_Ack(Channel);
    	IIC_Send_Byte(MS561101BA_PROM_BASE_ADDR + (i * MS561101BA_PROM_REG_SIZE), Channel);
		IIC_Wait_Ack(Channel);	
    	IIC_Stop(Channel);
		delay_us(5);
   		IIC_Start(Channel);
		IIC_Send_Byte(MS5611_ADDR+1, Channel);  //�������ģʽ	
		delay_us(1);
		IIC_Wait_Ack(Channel);
		inth = IIC_Read_Byte(1, Channel);  //��ACK�Ķ�����
		delay_us(1);
		intl = IIC_Read_Byte(0, Channel);	 //���һ���ֽ�NACK
		IIC_Stop(Channel);
    PROM_C[Channel][i] = (((uint16_t)inth << 8) | intl);
  }
}

/**************************ʵ�ֺ���********************************************
*����ԭ��:		void MS561101BA_reset(void)
*��������:	    ���͸�λ��� MS561101B 
*******************************************************************************/
void MS561101BA_reset(u8 Channel) {
	IIC_Start(Channel);
    IIC_Send_Byte(MS5611_ADDR, Channel); //д��ַ
	IIC_Wait_Ack(Channel);
    IIC_Send_Byte(MS561101BA_RESET, Channel);//���͸�λ����
	IIC_Wait_Ack(Channel);	
    IIC_Stop(Channel);
}

/**************************ʵ�ֺ���********************************************
*����ԭ��:		void MS561101BA_startConversion(uint8_t command)
*��������:	    ��������ת����� MS561101B
��ѡ�� ת������Ϊ MS561101BA_D1  ת����ѹ
				  MS561101BA_D2  ת���¶�	 
*******************************************************************************/
void MS561101BA_startConversion(uint8_t command, u8 Channel) {
  // initialize pressure conversion
  IIC_Start(Channel);
  IIC_Send_Byte(MS5611_ADDR, Channel); //д��ַ
  IIC_Wait_Ack(Channel);
  IIC_Send_Byte(command, Channel); //дת������
  IIC_Wait_Ack(Channel);	
  IIC_Stop(Channel);
}

/**************************ʵ�ֺ���********************************************
*����ԭ��:		unsigned long MS561101BA_getConversion(void)
*��������:	    ��ȡ MS561101B ��ת�����	 
*******************************************************************************/
unsigned long MS561101BA_getConversion(u8 Channel) {
		unsigned long conversion = 0;
		u8 temp[3];
		IIC_Start(Channel);
    IIC_Send_Byte(MS5611_ADDR, Channel); //д��ַ
		IIC_Wait_Ack(Channel);
    IIC_Send_Byte(0, Channel);// start read sequence
		IIC_Wait_Ack(Channel);	
    IIC_Stop(Channel);
		
		IIC_Start(Channel);
		IIC_Send_Byte(MS5611_ADDR+1, Channel);  //�������ģʽ	
		IIC_Wait_Ack(Channel);
		temp[0] = IIC_Read_Byte(1, Channel);  //��ACK�Ķ�����  bit 23-16
		temp[1] = IIC_Read_Byte(1, Channel);  //��ACK�Ķ�����  bit 8-15
		temp[2] = IIC_Read_Byte(0, Channel);  //��NACK�Ķ����� bit 0-7
		IIC_Stop(Channel);
		conversion = (unsigned long)temp[0] * 65536 + (unsigned long)temp[1] * 256 + (unsigned long)temp[2];
		return conversion;
}

/**************************ʵ�ֺ���********************************************
*����ԭ��:		void MS561101BA_init(void)
*��������:	    ��ʼ�� MS561101B 
*******************************************************************************/
void MS561101BA_init(void) {  
  MS561101BA_reset(0); // ��λ MS561101B 
//  MS561101BA_reset(1);
//  MS561101BA_reset(2); 
//  MS561101BA_reset(3); 	
//	MS561101BA_reset(4); 
	delay_ms(100); // ��ʱ 
   MS561101BA_readPROM(0);
//	MS561101BA_readPROM(1);
//	MS561101BA_readPROM(2);
//	MS561101BA_readPROM(3);
//	MS561101BA_readPROM(4);// ��ȡEEPROM �еı궨ֵ ����	
  
}

/**************************ʵ�ֺ���********************************************
*����ԭ��:		void MS561101BA_GetTemperature(void)
*��������:	    ��ȡ �¶�ת�����	 
*******************************************************************************/
void MS561101BA_GetTemperature(u8 Channel){	
	tempCache[Channel] = MS561101BA_getConversion(Channel);	
}

float Alt_offset_Pa[ChannelNum] = {0.0,0.0}; //�����0��ʱ ��Ӧ����ѹֵ  ���ֵ����ϵ�ʱ����ѹֵ 
uint8_t  Covert_count=0;
/**************************ʵ�ֺ���********************************************
*����ԭ��:		float MS561101BA_get_altitude(void)
*��������:	    ����ǰ����ѹֵת�� �߶ȡ�	 
*******************************************************************************/
float MS561101BA_get_altitude(u8 Channel){

	static float Altitude;
	if(Alt_offset_Pa[Channel]==0){ // �Ƿ��ʼ����0����ѹֵ��
		if(Covert_count++<50);  //�ȴ���ѹ�ȶ� �� ��ȡ����ʱ����ѹֵ
		else Alt_offset_Pa[Channel] = MS5611_Pressure[Channel]; //�� ��ǰ��ѹֵ����� 0 ��ʱ����ѹ
		avg_Pressure[Channel] = MS5611_Pressure[Channel];
		Altitude = 0; //�߶� Ϊ 0
		return Altitude;
	}
	//��������� �ϵ�ʱ��λ�õ� �߶�ֵ ��
	Altitude = 4433000.0 * (1 - pow((MS5611_Pressure[Channel] / Alt_offset_Pa[Channel]), 0.1903));
	Altitude = Altitude + Alt_Offset_cm[Channel] ;  //��ƫ��
	MS561101BA_NewAlt(Altitude, Channel);
	Altitude = MS561101BA_getAvg(Alt_buffer[Channel],MOVAVG_SIZE);
	return (Altitude);
}

/**************************ʵ�ֺ���********************************************
*����ԭ��:		void MS561101BA_ResetAlt(void)
*��������:	    ����ǰ����ѹ��Ϊ0��ʱ����ѹ��	 
*******************************************************************************/
void MS561101BA_ResetAlt(u8 Channel){
	Alt_offset_Pa[Channel] = MS5611_Pressure[Channel]; //�� ��ǰ��ѹֵ����� 0 ��ʱ����ѹ	
	Alt_Offset_cm[Channel] = 0;
}

/**************************ʵ�ֺ���********************************************
*����ԭ��:		void MS561101BA_SetAlt(void)
*��������:	    ����ǰ����ѹ��Ϊ Current ��ʱ����ѹ��	 
*******************************************************************************/
void MS561101BA_SetAlt(float Current, u8 Channel){
	Alt_offset_Pa[Channel] = (avg_Pressure[Channel]); //�� ��ǰ��ѹֵ����� 0 ��ʱ����ѹ	
	Alt_Offset_cm[Channel] = Current*100.0f; //��ת�� CM
	MS561101BA_NewAlt(Current*100.0f, Channel);	 //�µĸ߶�ֵ
	ALT_Updated[Channel] = 1; //�߶ȸ��� ��ɡ�
}

/**************************ʵ�ֺ���********************************************
*����ԭ��:		void MS561101BA_getPressure(void)
*��������:	    ��ȡ ��ѹת����� ������������	 
*******************************************************************************/
void MS561101BA_getPressure(u8 Channel) {
	int64_t off,sens;
	int64_t TEMP,T2,Aux_64,OFF2,SENS2;  // 64 bits
	int32_t rawPress = MS561101BA_getConversion(Channel);
	int64_t dT  = tempCache[Channel] - (((int32_t)PROM_C[Channel][4]) << 8);
	float temp;
	TEMP = 2000 + (dT * (int64_t)PROM_C[Channel][5])/8388608;
	off  = (((int64_t)PROM_C[Channel][1]) << 16) + ((((int64_t)PROM_C[Channel][3]) * dT) >> 7);
	sens = (((int64_t)PROM_C[Channel][0]) << 15) + (((int64_t)(PROM_C[Channel][2]) * dT) >> 8);
	
	if (TEMP < 2000){   // second order temperature compensation
		T2 = (((int64_t)dT)*dT) >> 31;
		Aux_64 = (TEMP-2000)*(TEMP-2000);
		OFF2 = (5*Aux_64)>>1;
		SENS2 = (5*Aux_64)>>2;
		TEMP = TEMP - T2;
		off = off - OFF2;
		sens = sens - SENS2;
	}

	MS561101BA_NewPress((((((int64_t)rawPress) * sens) >> 21) - off) / 32768, Channel);
  MS5611_Pressure[Channel] = MS561101BA_getAvg(Press_buffer[Channel],MOVAVG_SIZE); //0.01mbar
	
	avg_Pressure[Channel] = avg_Pressure[Channel] + (MS5611_Pressure[Channel] - avg_Pressure[Channel])*0.1f;

	MS561101BA_NewTemp(TEMP, Channel);
	MS5611_Temperature[Channel] = MS561101BA_getAvg(Temp_buffer[Channel],MOVAVG_SIZE); //0.01c
	
	temp = MS561101BA_get_altitude(Channel); // 0.01meter
							  
	MS5611_Altitude[Channel] = MS5611_Altitude[Channel] +	  //��ͨ�˲�   20hz
	 (ALT_Update_Interval[Channel]/(ALT_Update_Interval[Channel] + MS5611_Lowpass))*(temp - MS5611_Altitude[Channel]);
	
}


/**************************ʵ�ֺ���********************************************
*����ԭ��:		void MS5611BA_Routing(void)
*��������:	    MS5611BA �����г��� ����Ҫ���ڵ��� �Ը�����ѹֵ���¶�ֵ 	 
*******************************************************************************/
void MS5611BA_Routing(u8 Channel) {

	switch(Now_doing[Channel]){ //��ѯ״̬ ������������ ����Щʲô��
		case SCTemperature:  //�����¶�ת��
			MS561101BA_startConversion(MS561101BA_D2 + MS5611Temp_OSR, Channel);
			Current_delay[Channel] = MS5611_Delay_us[MS5611Temp_OSR] ;//ת��ʱ��
			Start_Convert_Time[Channel] = micros(); //��ʱ��ʼ
			Now_doing[Channel] = CTemperatureing;//��һ��״̬
			break;
		case CTemperatureing:  //����ת���� 
			if((micros()-Start_Convert_Time[Channel]) > Current_delay[Channel]){ //��ʱʱ�䵽����
			MS561101BA_GetTemperature(Channel); //ȡ�¶�	
			Now_doing[Channel] = SCPressure;	
			}
			break;
		case SCPressure: //������ѹת��
			MS561101BA_startConversion(MS561101BA_D1 + MS5611Press_OSR, Channel);
			Current_delay[Channel] = MS5611_Delay_us[MS5611Press_OSR];//ת��ʱ��
			Start_Convert_Time[Channel] = micros();//��ʱ��ʼ
			Now_doing[Channel] = SCPressureing;//��һ��״̬
			break;
		case SCPressureing:	 //����ת����ѹֵ
			if((micros()-Start_Convert_Time[Channel]) > Current_delay[Channel]){ //��ʱʱ�䵽����
			MS561101BA_getPressure(Channel);  //���� 	
			ALT_Updated[Channel] = 1; //�߶ȸ��� ��ɡ�
			MS5611_Complete[Channel] = 1;
			Now_doing[Channel] = SCTemperature; //��ͷ����	
			
//			if(Channel == (4-1))
//				MS5611BA_flag = 0;
			}
			break;
		default: 
			Now_doing[Channel] = SCTemperature;
		
			break;
	}
}

//------------------End of File----------------------------
