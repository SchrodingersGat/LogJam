from math import ceil, log
from logjam_common import *

class LogVariable:

    def __init__(self, prefix, xmlTag):
    
        self.prefix = prefix
        #extract information from an xml tag
        attr = xmlTag.attrib
        
        self.name = attr.get('name',None)
        if not self.name:
            raise NameError('Could not find name in {tag}'.format(tag=attr))
        if self.name.lower() in ['data','name','var','type']:
            raise NameError('{name} is an invalid name for a variable'.format(name=self.name))
        self.format=stringToCPrimitive(attr.get('type',None))
        
        self.title = attr.get('title',self.name)
        
        self.scaler = int(attr.get('scaler',1))
        self.units = attr.get('units',None)
        self.comment = attr.get('comment',None)
        
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