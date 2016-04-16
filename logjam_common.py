import re, os
import time
from math import ceil

from code_writer import CodeWriter
from logjam_version import AutogenString

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
        
        
#generate the name for a logging bitfield struct
def bitfieldStructName(prefix):
    return "Log{prefix}_Bitfield_t".format(prefix=prefix)
    
#generate the name for a logging data struct
def dataStructName(prefix):
    return "Log{prefix}_Data_t".format(prefix=prefix)

#generate the name for a 
def headerDefineName(prefix):
    return "_LOG_{prefix}_DEFS_H_".format(prefix=prefix.upper())
    
#header file name
def headerFileName(prefix):
    return "log_{prefix}_defs".format(prefix=prefix.lower())
            
def bitfieldSize(nBits):
    return ceil(nBits / 8)
    
#extract num bytes from variable
#t is for e.g. 'uint8_t' 'int16_t'
def extractNumBytesFromVarType(t):
    result = re.match('u*int(\d*)',t)
    
    return int(int(result.groups()[0])/8)
    
LOGJAM_HEADER_NAME = "logjam_common"
LOGJAM_DEFINE_NAME = "_LOGJAM_COMMON_H_"