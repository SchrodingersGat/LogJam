
#include "logjam_common.h" //LogJam common function

void CopyU8ToBuffer(uint8_t data, uint8_t **ptr)
{
    *(*ptr)++ = data;
}

//Copy an uint16_t to a pointer, and auto-increment the pointer
void CopyU16ToBuffer(uint16_t data, uint8_t **ptr)
{
    *(*ptr)++ = (uint8_t) (data >> 8);
    *(*ptr)++ = (uint8_t) (data & 0xFF);
}

void CopyU24ToBuffer(uint32_t data, uint8_t **ptr)
{
    *(*ptr)++ = (uint8_t) (data >> 16);
    *(*ptr)++ = (uint8_t) (data >> 8);
    *(*ptr)++ = (uint8_t) (data & 0xFF);
}

void CopyU32ToBuffer(uint32_t data, uint8_t **ptr)
{
    *(*ptr)++ = (uint8_t) (data >> 24);
    *(*ptr)++ = (uint8_t) (data >> 16);
    *(*ptr)++ = (uint8_t) (data >> 8);
    *(*ptr)++ = (uint8_t) (data & 0xFF);
}

void CopyU8FromBuffer(uint8_t *data, uint8_t **ptr)
{
    *data = *(*ptr)++;
}

void CopyU16FromBuffer(uint16_t *data, uint8_t **ptr)
{
    *data  = *(*ptr)++;      //Byte 2
    *data <<= 8;
    *data |= *(*ptr)++;      //Byte 1
}

void CopyU24FromBuffer(uint32_t *data, uint8_t **ptr)
{
    *data  = *(*ptr)++;    //Byte 3
    *data <<= 8;
    *data |= *(*ptr)++;    //Byte 2
    *data <<= 8;
    *data |= *(*ptr)++;    //Byte 1
}

void CopyU32FromBuffer(uint32_t *data, uint8_t **ptr)
{   
    *data  = *(*ptr)++;    //Byte 4
    *data <<= 8;
    *data |= *(*ptr)++;    //Byte 3
    *data <<= 8;
    *data |= *(*ptr)++;    //Byte 2
    *data <<= 8;
    *data |= *(*ptr)++;    //Byte 1
}

void CopyI8ToBuffer(int8_t *data,)

void CopyI16ToBuffer(int16_t data, uint8_t **ptr)
{
    CopyU16ToBuffer((uint16_t) data, ptr);
}

void CopyI32ToBuffer(int32_t data, uint8_t **ptr)
{
    CopyU32ToBuffer((uint32_t) data, ptr);
}

void CopyI16FromBuffer(int16_t *data, uint8_t **ptr)
{
    CopyU16FromBuffer((uint16_t*) data, ptr);
}

void CopyI32FromBuffer(int32_t *data, uint8_t **ptr)
{
    CopyU32FromBuffer((uint32_t*) data, ptr);
}

void SetBitByPosition(void *ptr, uint8_t pos)
{
    uint8_t *bits = (uint8_t*) ptr;
    
    bits[pos/8] |= (1 << (pos % 8));
}

void ClearBitByPosition(void *ptr, uint8_t pos)
{
    uint8_t *bits = (uint8_t*) ptr;
    
    bits[pos/8] &= ~(1 << (pos % 8));    
}

bool GetBitByPosition(void *ptr, uint8_t pos)
{
    uint8_t *bits = (uint8_t*) ptr;
    
    return (bits[pos/8] & (1 << (pos % 8))) > 0;
}
