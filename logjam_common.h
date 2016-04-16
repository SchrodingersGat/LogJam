#ifndef _LOGJAM_COMMON_H_
#define _LOGJAM_COMMON_H_

#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>

void CopyU16ToBuffer(uint16_t data, void *buf);
void CopyU32ToBuffer(uint32_t data, void *buf);
void CopyU16FromBuffer(uint16_t *data, void *buf);
void CopyU32FromBuffer(uint32_t *data, void *buf);

void CopyI16ToBuffer(int16_t data, void *buf);
void CopyI32ToBuffer(int32_t data, void *buf);
void CopyI16FromBuffer(int16_t *data, void *buf);
void CopyI32FromBuffer(int32_t *data, void *buf);

#endif //_LOGJAM_COMMON_H_

