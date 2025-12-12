 /*
  ******************************************************************************
  * @file           : delay.h
  * @brief          : delay head file
  * @author			: Ceres_Li
  ******************************************************************************
  * @attention
  * 1. In the use of the file contains the delay.h file
     * 2. In the initialization of delay_init (HCLK frequency) in main.c, such as 72MHz, the parameter is 72
  ******************************************************************************
  */

#ifndef	_DELAY_H_
#define	_DELAY_H_

#include "stm32f1xx_hal.h"	// Transplant STM32F1XX.H
// # include "stm32f4xx_hal.h" // Transplant M4 to release M1

void delay_init(uint8_t Sysclk);	// If SYSTICK is 72MHz, SysClk is 72
void delay_ms(uint16_t _ms);		// millisecond delay
void delay_us(uint32_t _us);		//      

#endif
