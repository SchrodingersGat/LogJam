#include <stdio.h>
#include <string.h>
#include <stdint.h>

#include "log_test_defs.h"

int main(void)
{
    uint8_t uBuf[64];
    char cBuf[64];

    LogTest_Bitfield_t bits;
    LogTest_Data_t data;

    LogTest_ResetSelection(&bits);

    LogTest_AddCurrent(&data,&bits,50);

    //Get the current value
    LogTest_GetValueByIndex(&data,LOG_TEST_CURRENT,cBuf);
    printf("%s=%s\n",LogTest_GetTitleByIndex(LOG_TEST_CURRENT),cBuf);

    return 0;
}

