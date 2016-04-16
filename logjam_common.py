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
    
LOGJAM_HEADER_NAME = "logjam_common"
LOGJAM_DEFINE_NAME = "_LOGJAM_COMMON_H_"

COPY_BYTES_TOFROM_BUFFER = "LogJam_Copy{n}Bytes{dir}Buffer"
    
#create code that is common to all data logging types
def LogJamHeaderFile(outputdir = None):

    filename = LOGJAM_HEADER_NAME + '.h'
    
    if outputdir:
        filename=os.path.join(outputdir, filename)
    
    h = CodeWriter(filename)
    
    h.append(AutogenString())
    
    h.startIf(LOGJAM_DEFINE_NAME, invert = True)
    h.define(LOGJAM_DEFINE_NAME)
    
    h.appendLine()
    
    h.include('<stdint.h>')
    h.include('<stdbool.h>')
    h.include('<stdio.h>')
    h.include('<string.h>')
    
    h.appendLine()
    
    h.endIf()
    h.appendLine()
    
    #write the file
    h.writeToFile()