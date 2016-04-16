import re, os
import time
from math import ceil

def leftShiftBytes(n):
    return leftShiftBits(n*8)

def leftShiftBits(n):
    if n == 0:
        return ''
    else:
        return ' << {n}'.format(n=int(n))

#return a c-code string to right shift
def rightShiftBytes(n):
    return rightShiftBits(n*8)
    
def rightShiftBits(n):
    if n == 0:
        return ''
    else:
        return ' >> {n}'.format(n=int(n))
        
#bitfield struct of the format Device_LogBitfield_t"
def bitfieldStruct(prefix):
    return "Log{prefix}_Bitfield_t".format(prefix=prefix)
    
#data struct for the format Device_LogData_t
def dataStruct(prefix):
    return "Log{prefix}_Data_t".format(prefix=prefix)

#header file define string
def headerDefine(prefix):
    return "_LOG_{prefix}_DEFS_H_".format(prefix=prefix.upper())
    
#header file name
def headerFilename(prefix):
    return "log_{prefix}_defs".format(prefix=prefix.lower())
            
def bitfieldSize(nBits):
    return ceil(nBits / 8)