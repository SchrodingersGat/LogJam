from math import ceil, log
from logjam_common import *

class LogVariable:

    #prefix = name of the 'device'
    #name = name of this variable
    #format = primitive datatype
    #comment = comment string
    def __init__(self, prefix, name, format, title, comment=None, units=None, scaler=1.0):
        self.prefix = prefix
        self.name = name
        
        if self.name == 'data':
            raise NameError("Logging variable cannot be called 'data'")
        
        self.format = stringToCPrimitive(format)
        self.comment = "//!< " + str(comment) if comment else ""
        self.units = units
        self.scaler = scaler
        
        self.title = title
        
        self.bytes = extractNumBytesFromVarType(self.format)
        
    #datatype definition string (with comment appended)
    def dataString(self):
        return "{datatype} {name}; {comment}".format(
                datatype = self.format,
                name = self.name,
                comment = self.comment)
                
    #wrap a given function name
    def getFunctionName(self, fnName):
        return "{fn}{name}".format(name=self.name, fn=fnName.capitalize())
        
    #return an enum line
    def getEnum(self):
        return "LOG_{pref}_{name}".format(pref=self.prefix.upper(),name=self.name.upper())
        
    #assume there is always a pointer to *log
    
    #get the pointer to the data type within a given struct
    def getPtr(self, struct='data'):
        return '{struct}->{name}'.format(struct=struct,name=self.name)
    
    #check if a bit is set
    #returns a string of the format 'if (bits->name)'
    def getBit(self,struct='selection'):
        return 'GetBitByPosition({struct},{pos})'.format(
                    struct=struct,
                    pos = self.getEnum())
    #code prototype to set the selection bit
    def setBit(self,struct='selection'):
        return 'SetBitByPosition({struct},{pos});'.format(
                    struct=struct,
                    pos = self.getEnum())
        
    #code prototype to clear the selection bit
    def clearBit(self,struct='selection'):
        return 'ClearBitByPosition({struct},{pos})'.format(
                    struct=struct,
                    pos = self.getEnum())
        
    #add the variable to the struct
    def addVariable(self, struct):
        return "{struct}->{name} = {name}; //Add the '{name}' variable".format(struct=struct,name=self.name)
        
    def getTitleString(self):
        return '"{name}"'.format(name=self.title if self.title else self.name)
        
    def getUnitsString(self):
        if not self.units:
            return '""'
        else:
            return '"{units}"'.format(units=self.units)
            
    def isSigned(self):
        return self.format.startswith('i')