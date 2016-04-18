from math import ceil, log
from logjam_common import *
import re

class LogElement:
    def __init__(self, prefix, tag):
        self.prefix = prefix
        
        attr = tag.attrib
        
        self.elementType = 'element'
        
        #extract common information
        self.name = attr.get('name',None)
        
        if not self.name:
            raise NameError('Could not find name in {tag}'.format(tag=attr))
        if self.name.lower() in ['data','name','var','type']:
            raise NameError('{name} is an invalid name for a variable'.format(name=self.name))
        
        self.title = attr.get('title',self.name)
        self.comment = attr.get('comment',None)
        
    def getEnumString(self):
        return "LOG_{pref}_{type}_{name}".format(pref=self.prefix.upper(),type=self.elementType.upper(),name=camel2define(self.name))
        
            
    def getTitleString(self):
        return '"{name}"'.format(name=self.title)
    
    #check if a bit is set
    #returns a string of the format 'if (bits->name)'
    def getBit(self,struct='selection'):
        return 'GetBitByPosition({struct},{pos})'.format(
                    struct=struct,
                    pos = self.getEnumString())
    #code prototype to set the selection bit
    def setBit(self,struct='selection'):
        return 'SetBitByPosition({struct},{pos});'.format(
                    struct=struct,
                    pos = self.getEnumString())
        
    #code prototype to clear the selection bit
    def clearBit(self,struct='selection'):
        return 'ClearBitByPosition({struct},{pos})'.format(
                    struct=struct,
                    pos = self.getEnumString())
    
        
class LogVariable(LogElement):

    def __init__(self, prefix, xmlTag):
    
        LogElement.__init__(self, prefix, xmlTag)
        
        self.elementType = 'var'
        
        #extract information from an xml tag
        attr = xmlTag.attrib
        
        self.format=stringToCPrimitive(attr.get('type',None))
        
        self.scaler = int(attr.get('scaler',1))
        self.units = attr.get('units',None)
        
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
        
    #get the pointer to the data type within a given struct
    def getPtr(self, struct='data'):
        return '{struct}->{name}'.format(struct=struct,name=self.name)
        
    #add the variable to the struct
    def addVariable(self, struct):
        return "{struct}->{name} = {name}; //Add the '{name}' variable".format(struct=struct,name=self.name)
        
    def getUnitsString(self):
        if not self.units:
            return '""'
        else:
            return '"{units}"'.format(units=self.units)
            
    def isSigned(self):
        return self.format.startswith('i')
        
class LogEvent(LogElement):
    def __init__(self, prefix, xmlTag):
        LogElement.__init__(self, prefix, xmlTag)
        
        self.elementType = 'evt'
        
        