#ifndef __MS5611_H
#define __MS5611_H

#include "IICx.h"
#include "delay.h"


// addresses of the device CSB =0 
#define MS5611_ADDR          0xEE     // default I2C address

// registers of the device
#define MS561101BA_D1 0x40
#define MS561101BA_D2 0x50
#define MS561101BA_RESET 0x1E

// D1 and D2 result size (bytes)
#define MS561101BA_D1D2_SIZE 3

// OSR (Over Sampling Ratio) constants
#define MS561101BA_OSR_256 0x00  //Conversion time 0.6ms  Resolution 0.065mbar
#define MS561101BA_OSR_512 0x02  //Conversion time 1.2ms  Resolution 0.042mbar
#define MS561101BA_OSR_1024 0x04 //Conversion time 2.3ms  Resolution 0.027mbar
#define MS561101BA_OSR_2048 0x06 //Conversion time 4.6ms  Resolution 0.018mbar
#define MS561101BA_OSR_4096 0x08 //Conversion time 9.1ms  Resolution 0.012mbar

#define MS561101BA_PROM_BASE_ADDR 0xA2 // by adding ints from 0 to 6 we can read all the prom configuration values. 
// C1 will be at 0xA2 and all the subsequent are multiples of 2
#define MS561101BA_PROM_REG_COUNT 6 // number of registers in the PROM
#define MS561101BA_PROM_REG_SIZE 2 // size in bytes of a prom registry.

//Other
#define MSLP                    101325          // Mean Sea Level Pressure = 1013.25 hPA (1hPa = 100Pa = 1mbar)

//  Temperature in 0.01C
//  Pressure    in 0.01mbar = Pa
//  Altitude    in meter  / cm
extern float MS5611_Temperature[ChannelNum],MS5611_Pressure[ChannelNum],MS5611_Altitude[ChannelNum];
extern float ALT_Update_Interval[ChannelNum];
extern uint8_t ALT_Updated[ChannelNum] ; //气压计高度更新完成标志。
extern float avg_Pressure[ChannelNum];
extern uint8_t MS5611BA_flag;

extern u8 MS5611_Complete[ChannelNum];

void MS561101BA_init(void); 
void MS5611BA_Routing(u8 Channel);
void MS561101BA_ResetAlt(u8 Channel);
float MS5611BA_Get_D(u8 Channel);
void MS561101BA_SetAlt(float Current, u8 Channel);

#endif

//------------------End of File----------------------------
