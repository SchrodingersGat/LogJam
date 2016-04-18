import re, os
import time
from math import ceil


from code_writer import CodeWriter
from logjam_version import AutogenString

#convert a 'camelCase' string to a 'CAMEL_CASE' string
def camel2define(string):
    r1 = re.compile('(.)([A-Z][a-z]+)')
    r2 = re.compile('([a-z0-9])([A-Z])')
    
    s1 = r1.sub(r'\1_\2',string);
    s2 = r2.sub(r'\1_\2',s1)
    
    return s2.upper()

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
    
#convert a string to a valid c-primitive
#input something like "unsigned8" "unsigned_8" "signed 16" "uint16_t"
def stringToCPrimitive(string):
    s = string #copy
    s = s.strip()
    remove = ["_t","_"," "]
    for r in remove:
        s = s.replace(r,"")
    
    s = s.replace("unsigned","uint")
    s = s.replace("signed","int")
    
    #should now be of the format (u)int<n>
    #search for the num
    res = re.match('u*int(\d*)',s)
    
    if not len(res.groups()) == 1:
        raise ValueError("{s} is not of correct format".format())
        
    return s
    
    
LOGJAM_HEADER_NAME = "logjam_common"
LOGJAM_DEFINE_NAME = "_LOGJAM_COMMON_H_"