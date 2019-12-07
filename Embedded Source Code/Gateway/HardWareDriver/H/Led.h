#ifndef _Led_H_
#define _Led_H_
#include "stm32f10x.h"

#define Led0_on    GPIO_ResetBits(GPIOA, GPIO_Pin_8)
#define Led0_off   GPIO_SetBits(GPIOA, GPIO_Pin_8)

#define Led1_on    GPIO_ResetBits(GPIOD, GPIO_Pin_2)
#define Led1_off   GPIO_SetBits(GPIOD, GPIO_Pin_2)


void LedInit(void);   //Led初始化函数外部声明

#define BUTTONn                     3 /*!< Joystick pins are connected to an IO Expander (accessible through I2C1 interface) */

/**
 * @brief KEY0
 */
#define BUTTON0_PORT          GPIOC
#define BUTTON0_CLK           RCC_APB2Periph_GPIOC
#define BUTTON0_PIN           GPIO_Pin_1
#define BUTTON0_EXTI_LINE     EXTI_Line1
#define BUTTON0_PORT_SOURCE   GPIO_PortSourceGPIOC
#define BUTTON0_PIN_SOURCE    GPIO_PinSource1
#define BUTTON0_IRQn          EXTI1_IRQn 

/**
 * @brief KEY1
 */
#define BUTTON1_PORT          GPIOC
#define BUTTON1_CLK           RCC_APB2Periph_GPIOC
#define BUTTON1_PIN           GPIO_Pin_13
#define BUTTON1_EXTI_LINE     EXTI_Line13
#define BUTTON1_PORT_SOURCE   GPIO_PortSourceGPIOC
#define BUTTON1_PIN_SOURCE    GPIO_PinSource13
#define BUTTON1_IRQn          EXTI15_10_IRQn 

/**
 * @brief Wakeup push-button
 */
#define WAKEUP_BUTTON_PORT          GPIOA			 //所在的GPIO端口名
#define WAKEUP_BUTTON_CLK           RCC_APB2Periph_GPIOA   //端口时钟
#define WAKEUP_BUTTON_PIN           GPIO_Pin_0			 //所在的端口号
#define WAKEUP_BUTTON_EXTI_LINE     EXTI_Line0			//对应的外部中断线编号
#define WAKEUP_BUTTON_PORT_SOURCE   GPIO_PortSourceGPIOA   //中断源时钟
#define WAKEUP_BUTTON_PIN_SOURCE    GPIO_PinSource0		  //对应的中断源连接的端口号
#define WAKEUP_BUTTON_IRQn          EXTI0_IRQn 			  //相应的中断事件

void LedInit(void);   //Led初始化函数外部声明

/** 
  * @brief  Uncomment the line corresponding to the STMicroelectronics evaluation
  *   board used in your application.
  *   
  *  Tip: To avoid modifying this file each time you need to switch between these
  *       boards, you can define the board in your toolchain compiler preprocessor.    
  */ 
                     


typedef enum 
	{
	LED1 = 0,
	LED2 = 1
	} Led_TypeDef;
	
typedef enum 
	{  
	Button_KEY0 = 0,
	Button_KEY1 = 1,
	Button_WAKEUP = 2
	} Button_TypeDef;

typedef enum 
	{  
	Mode_GPIO = 0,
	Mode_EXTI = 1
	} Button_Mode_TypeDef;





 
/**
  * @}
  */ 

/** @defgroup STM32_EVAL_Exported_Macros
  * @{
  */ 
/**
  * @}
  */ 

/** @defgroup STM32_EVAL_Exported_Functions
  * @{
  */ 

void STM_EVAL_PBInit(Button_TypeDef Button, Button_Mode_TypeDef Button_Mode);
uint32_t STM_EVAL_PBGetState(Button_TypeDef Button);



#endif

