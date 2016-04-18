#ifndef _LOGJAM_COMMON_H_
#define _LOGJAM_COMMON_H_

#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>

//Copy unsigned data types to/from buffer 
void CopyU16ToBuffer(uint16_t data, uint8_t **buf);
void CopyU24ToBuffer(uint32_t data, uint8_t **buf);
void CopyU32ToBuffer(uint32_t data, uint8_t **buf);
void CopyU16FromBuffer(uint16_t *data, uint8_t **buf);
void CopyU24FromBuffer(uint32_t *data, uint8_t **buf);
void CopyU32FromBuffer(uint32_t *data, uint8_t **buf);

//Copy signed types out of buffer
void CopyI16ToBuffer(int16_t data, uint8_t **buf);
void CopyI32ToBuffer(int32_t data, uint8_t **buf);
void CopyI16FromBuffer(int16_t *data, uint8_t **buf);
void CopyI32FromBuffer(int32_t *data, uint8_t **buf);

void SetBitByPosition(void *ptr, uint8_t pos);
void ClearBitByPosition(void *ptr, uint8_t pos);
bool GetBitByPosition(void *ptr, uint8_t pos);

#endif //_LOGJAM_COMMON_H_


