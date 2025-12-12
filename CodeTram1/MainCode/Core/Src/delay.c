 /*
  ******************************************************************************
  * @file           : delay.c
  * @brief          : delay c file
  * @author			: Ceres_Li
  ******************************************************************************
  * @attention
     * 1. In the use of the file contains the delay.h file
     * 2. In the initialization of delay_init (HCLK frequency) in main.c, such as 72MHz, the parameter is 72
  ******************************************************************************
  */
#include "delay.h"

static uint32_t fac_us=0;

void delay_init(uint8_t SYSCLK)
{
	HAL_SYSTICK_CLKSourceConfig(SYSTICK_CLKSOURCE_HCLK);	// Systick Clock Source Set to HCLK
	fac_us=SYSCLK;						// If FAC_US is 72, HCLK is 72MHz, and HCLK has been 72 cycles of 1US.
}

// Delay _US microseconds
void delay_us(uint32_t _us)
{
	uint32_t ticks;
	uint32_t told,tnow,tcnt=0;
	uint32_t reload=SysTick->LOAD;
	ticks=_us*fac_us;	// Delay _US minus cycle
	told=SysTick->VAL;
	// Judging whether the number of cycles is greater than ticks, jump out of the cycle greater than it.
	while(1)
	{
		tnow=SysTick->VAL;
		if(tnow!=told)
		{
			if(tnow<told)	tcnt+=told-tnow;
			else			tcnt+=reload-tnow+told;
			told=tnow;
			if(tcnt>=ticks)break;
		}
	}
}

// Delay _ms microsecond
void delay_ms(uint16_t _ms)
{
	uint32_t i;
	for(i=0;i<_ms;i++)	delay_us(1000);	// Delay _MS 1000US
}
