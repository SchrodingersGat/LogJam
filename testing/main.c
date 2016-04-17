#include <stdio.h>
#include <string.h>
#include <stdint.h>

#include "log_test_defs.h"

int main(void)
{
    uint8_t uBuf[64];
    char cBuf[64];

    uint16_t tmp;
    uint16_t i;

    LogTest_Bitfield_t bits;
    LogTest_Data_t data;

    LogTest_ResetSelection(&bits);

    LogTest_AddCurrent(&data,&bits,50);
    LogTest_AddMonkeys(&data,&bits,17);
    LogTest_AddUptime(&data,&bits,1234);
    LogTest_AddData4(&data,&bits,1);

    printf("\nData:\n");
    for (i=0;i<LOG_TEST_VARIABLE_COUNT;i++)
    {
        if (GetBitByPosition(&bits, i))
        {
            LogTest_GetValueByIndex(&data,i,cBuf);
            printf("%s = %s\n",LogTest_GetTitleByIndex(i),cBuf);
        }
    }


    //copy across to buffer
    tmp = LogTest_CopyDataToBuffer(&data,&bits,uBuf);

    printf("Copied %u bytes\n",tmp);

    printf("\nTotal Data: %u\n\n",LogTest_GetSelectionSize(&bits));

    printf("Bitfield bytes:\n");
    for (i=0;i<tmp;i++)
    {
        printf("%u -> %u\n",i, uBuf[i]);
    }

    //Now, copy the data back!
    tmp = LogTest_CopyDataFromBuffer(&data,&bits,uBuf);
    printf("\nCopied %u bytes back\n",tmp);

    printf("\nData:\n");
    for (i=0;i<LOG_TEST_VARIABLE_COUNT;i++)
    {
        if (GetBitByPosition(&bits, i))
        {
            LogTest_GetValueByIndex(&data,i,cBuf);
            printf("%s = %s\n",LogTest_GetTitleByIndex(i),cBuf);
        }
    }

    return 0;
}

