import re,os
import time

from math import ceil, log

from code_writer import CodeWriter

from logjam_version import LOGJAM_VERSION, AutogenString

from logjam_common import *
    
class LogFile:
    def __init__(self, vars, prefix, version, sourceFile, outputdir=None):
        self.variables = vars
        self.prefix = prefix
        self.version = version
        self.source = sourceFile
        
        hfile = headerFileName(prefix) + '.h'
        cfile = headerFileName(prefix) + '.c'
        
        if outputdir:
            hfile = os.path.join(outputdir, hfile)
            cfile = os.path.join(outputdir, cfile)
        
        self.hFile = CodeWriter(hfile)
        self.cFile = CodeWriter(cfile)
    
    def createHeaderEntry(self):
        self.hFile.startIf(headerDefineName(self.prefix),invert=True)
        self.hFile.define(headerDefineName(self.prefix))
        
    def createHeaderExit(self):
        self.hFile.endIf()
        
    def createHeaderInclude(self):
        self.cFile.include('"{file}.h"'.format(file=headerFileName(self.prefix)))
        
    def constructCodeFile(self):
        
        self.cFile.clear()
        
        self.cFile.append(AutogenString(self.source))
        
        #include the header file
        self.createHeaderInclude()
        
        self.cFile.appendLine()
        
        #add in the global functions
        self.cFile.startComment()
        self.cFile.appendLine("Global functions")
        self.cFile.finishComment()
        
        self.cFile.appendLine()
        
        self.createResetFunction()
        self.createCopyAllToFunction()
        self.createCopyDataToFunction()
        self.createCopyAllFromFunction()
        self.createCopyDataFromFunction()
        self.getSelectionSizeFunction()
        
        self.cFile.appendLine()
        self.cFile.startComment()
        self.cFile.appendLine("Individual variable functions")
        self.cFile.finishComment()
        
        self.cFile.appendLine()
        
        #add in the functions to add variables
        for v in self.variables:
            self.createAdditionFunction(v)
            self.createDecodeFunction(v)
       
        self.titleByIndexFunction()
        self.unitsByIndexFunction()
        self.valueByIndexFunction()
       
    def constructHeaderFile(self):
        
        self.hFile.clear()
        
        self.hFile.append(AutogenString(self.source))
        
        self.createHeaderEntry()
        
        self.hFile.appendLine()
        self.hFile.include('"' + LOGJAM_HEADER_NAME + '.h"', comment='common LogJam routines')
        
        self.hFile.appendLine()
        
        self.hFile.externEntry()

        self.hFile.appendLine()
        #create global enumeration for the variables
        fn = lambda i,val: "{val} is stored in byte {n}, position {m}".format(val=val,n=int(int(i)/8),m=i%8)
        self.hFile.createEnum('Log{pref}_Enum_t'.format(pref=self.prefix),[v.getEnum() for v in self.variables],split=8,commentFunc=fn)
        
        self.hFile.appendLine(comment='{n} bytes are required to store all parameter selction bits for {log} logging'.format(n=bitfieldSize(len(self.variables)),log=self.prefix))
        self.hFile.define('LOG_{pref}_SELECTION_BYTES'.format(pref=self.prefix.upper()),value=bitfieldSize(len(self.variables)))
        self.hFile.appendLine()
        
        self.hFile.appendLine(comment="Struct definition for storing the selection bits of the " + self.prefix + " logging struct")
        self.hFile.appendLine(comment='This is not stored as a native c bitfield to preserve explicit ordering between processors, compilers, etc')
        self.hFile.appendLine('typedef uint8_t[LOG_{pref}_SELECTION_BYTES] {name};'.format(pref=self.prefix.upper(),name=bitfieldStructName(self.prefix)))
        self.hFile.appendLine()
        self.hFile.appendLine(comment="Data struct definition for the " + self.prefix + " logging struct")
        self.createDataStruct()
        
        self.hFile.appendLine()
        
        self.hFile.startComment()
        self.hFile.appendLine("Global Functions:")
        self.hFile.finishComment()
        
        self.hFile.appendLine(comment="Reset the bitfield of the logging structure")
        self.hFile.appendLine(self.resetPrototype() + ";")
        
        self.hFile.appendLine(comment='Copy *all* data from the logging structure')
        self.hFile.appendLine(self.copyAllPrototype() + ';')
        
        self.hFile.appendLine(comment="Copy *selected* data from the logging structure")
        self.hFile.appendLine(self.copySelectedPrototype() + ";")
        
        self.hFile.appendLine(comment='Copy all data back out from a buffer')
        self.hFile.appendLine(self.copyAllFromPrototype() + ';')
        
        self.hFile.appendLine(comment='Copy *selected* data back out from a buffer')
        self.hFile.appendLine(self.copyDataFromPrototype() + ';')
        
        self.hFile.appendLine(comment='Get the total size of the selected variables')
        self.hFile.appendLine(self.getSelectionSizePrototype() + ';')
        
        self.hFile.appendLine()
        
        self.hFile.appendLine(comment="Functions for getting variable information based on the index");
        self.hFile.appendLine(self.titleByIndexPrototype()+';')
        self.hFile.appendLine(self.unitsByIndexPrototype()+';')
        self.hFile.appendLine(self.valueByIndexPrototype() + ';')
        
        self.hFile.appendLine()
        
        self.hFile.startComment()
        self.hFile.appendLine("Variable Functions:")
        self.hFile.appendLine("These functions are applied to individual variables within the logging structure")
        self.hFile.finishComment()
        
        #add in the 'addition' functions
        for var in self.variables:
            self.hFile.appendLine()
            self.hFile.appendLine(comment="Functions for the '{name}' variable".format(name=var.name))
            self.hFile.define('Log{prefix}_{name}Title() {title}'.format(
                prefix=self.prefix,
                name=var.name,
                title=var.getTitleString()),
                comment='Title string for {var} variable'.format(var=var.name))
                
            self.hFile.define('Log{prefix}_{name}Units() {units}'.format(
                prefix=self.prefix,
                name=var.name,
                units=var.getUnitsString()),
                comment='Units string for {var} variable'.format(var=var.name))
            self.hFile.appendLine(self.additionPrototype(var) + '; //Add ' + var.prefix + " to the log struct")
            self.hFile.appendLine(self.decodePrototype(var) + '; //Decode ' + var.prefix + ' into a printable string')
        
        self.hFile.appendLine()
        self.hFile.externExit()
        
        self.createHeaderExit()
    
    def saveFiles(self):
        
        self.constructHeaderFile()
        self.constructCodeFile()
        
        self.hFile.writeToFile()
        self.cFile.writeToFile() 
        
    #create the struct of the variables
    def createDataStruct(self):
    
        self.hFile.appendLine('typedef struct {')
        
        self.hFile.tabIn()
        
        for v in self.variables:
            self.hFile.appendLine(comment='Variable : {name}, {units}'.format(name=v.name,units=v.units if v.units else 'no units specified'))
            
            if v.scaler > 1:
                self.hFile.appendLine(comment='{name} will be scaled by 1.0/{scaler} when decoded to a log file'.format(name=v.name,scaler=v.scaler))
            self.hFile.appendLine(v.dataString())
        
        self.hFile.tabOut()
        
        self.hFile.appendLine('} ' + dataStructName(self.prefix) + ';')
        
    def additionPrototype(self,var):
        return self.createVariableFunction(var,'add',inline=True)
        
    #create the function for adding a variable to the logging structure
    def createAdditionFunction(self, var):
    
        self.cFile.appendLine(comment='Add variable {name} to the {prefix} logging struct'.format(
                        name=var.name,
                        prefix=self.prefix))
                        
        self.cFile.appendLine(self.additionPrototype(var))
        self.cFile.openBrace()
        self.cFile.appendLine(var.setBit('selection'))
        #now actually add the variable in
        self.cFile.appendLine(var.addVariable('data'))
        self.cFile.closeBrace()
        self.cFile.appendLine()
        
    #function for decoding a particular variable into a printable string for writing to a log file
    def decodePrototype(self, var):
        return self.createVariableFunction(var,'decode',blank=True,bits=False,returnType='void',extra=[('*str','char')])
    
    def createDecodeFunction(self, var):
        self.cFile.appendLine(comment='Decode the {name} variable and return a printable string (e.g. for saving to a log file'.format(name=var.name))
        self.cFile.appendLine(comment='Pointer to *str must have enough space allocated!')
        self.cFile.appendLine(self.decodePrototype(var))
        self.cFile.openBrace()
        line = ''
        #perform scaling!
        scale = var.scaler > 1
        
        if not scale:
            pattern = '"%{sign}",{var}'.format(sign='u' if var.format.startswith('u') else 'd',var=var.getPtr('data'))
        else:
            pattern = '"%.{n}f",(float) {var} / {scaling}'.format(
                n = ceil(log(var.scaler) / log(10)),
                var=var.getPtr('data'),
                scaling=var.scaler)
            
        self.cFile.appendLine('sprintf(str,{patt});'.format(patt=pattern))
        self.cFile.closeBrace()
        self.cFile.appendLine()
        pass
        
    #create a function pointing to a particular variable
    def createVariableFunction(self, var, name, blank=False, extra=None,ptr=False, **params):
        name = var.getFunctionName(name)
        
        if not extra:
            extra = []
        
        if not blank:
            extra.append(('{ptr}{name}'.format(ptr='*' if ptr else '',name=var.name),var.format))
        
        return self.createFunctionPrototype(name,extra=extra,**params)
        
    """
    Create a function type of given NAME
    name - name of the function
    data - Include a pointer to the LogData_t struct?
    bits - Include a pointer to the LogBitfield_t struct?
    inline - Make the function inline?
    returnType - Function return type
    extra - Extra parameters to pass to the function - list of tuples
    """
    def createFunctionPrototype(self, name, data=True, bits=True, inline=False, returnType='void', extra=None):
        
        if not extra:
            extra = []
        
        #pass extra parameters to the function as such
        #params = {'*dest': 'void'} (name, type)
        paramstring = ""
        for pair in extra:
            paramstring += ', '
            paramstring += pair[1]
            paramstring += ' '
            paramstring += pair[0]
            
        return '{inline}{returnType} Log{prefix}_{name}({data}{comma}{bits}{params})'.format(
                    inline='inline ' if inline else '',
                    returnType=returnType,
                    prefix=self.prefix.capitalize(),
                    name=name,
                    comma=', ' if data and bits else '',
                    data=dataStructName(self.prefix) + " *data" if data else "",
                    bits=bitfieldStructName(self.prefix) + " *selection" if bits else "",
                    params=paramstring)
                    
    def resetPrototype(self):
        return self.createFunctionPrototype('ResetSelection',data=False)
                    
    #create a function to reset the logging structure
    def createResetFunction(self):
        
        #add the reset function to the c file
        self.cFile.appendLine(comment='Reset the log data struct (e.g. after writing to memory)')
        self.cFile.appendLine(comment='Only the selection bits need to be reset')
        self.cFile.appendLine(self.resetPrototype())
        self.cFile.openBrace()
        
        for i in range(bitfieldSize(len(self.variables))):
            self.cFile.appendLine('selection[{n}] = 0; //Clear byte {x} of {y}'.format(n=i,x=i+1,y=bitfieldSize(len(self.variables))))
        
        self.cFile.closeBrace()
        self.cFile.appendLine()
        
    """
    Functions for copying data out of a struct and into a linear buffer
    """
    def copyAllPrototype(self):
        return self.createFunctionPrototype('CopyAllToBuffer',bits=False,extra=[('*dest','void')])
        
    #create a function to copy ALL parameters across, conserving data format
    def createCopyAllToFunction(self):
        
        self.cFile.appendLine(comment="Copy ALL data in the log struct to the provided address")
        self.cFile.appendLine(comment="Data will be copied even if the associated selection bit is cleared")
        
        self.cFile.appendLine(self.copyAllPrototype())
        self.cFile.openBrace()
        
        self.cFile.appendLine('uint8_t *ptr = (uint8_t*) dest; //Pointer for keeping track of data addressing')
        self.cFile.appendLine()
        
        for var in self.variables:
            self.copyVarToBuffer(var)
            self.cFile.appendLine()
        
        self.cFile.closeBrace()
        self.cFile.appendLine()

    def copySelectedPrototype(self):
        return self.createFunctionPrototype('CopyDataToBuffer',extra=[('*dest','void')], returnType='uint16_t')
        
    #create a function that copies across ONLY the bits that are set
    def createCopyDataToFunction(self):
        self.cFile.appendLine(comment="Copy across data whose selection bit is set in the provided bitfield")
        self.cFile.appendLine(comment="Only data selected will be copied (in sequence)")
        self.cFile.appendLine(comment="Ensure a copy of the selection bits is stored for decoding")
        self.cFile.appendLine(self.copySelectedPrototype())
        self.cFile.openBrace()
        self.cFile.appendLine('uint8_t *ptr = (uint8_t*) dest; //Pointer for keeping track of data addressing')
        self.cFile.appendLine('uint8_t *bf = (uint8_t*) selection; //Pointer for keeping track of the bitfield')
        self.cFile.appendLine('uint16_t count = 0; //Variable for keeping track of how many bytes were copied')
        self.cFile.appendLine()
        self.cFile.appendLine(comment='Copy the selection for keeping track of data')
        
        self.copyBitfieldToBuffer(count=True)
        
        self.cFile.appendLine()
        self.cFile.appendLine(comment='Check each variable in the logging struct to see if it should be added')
        
        for var in self.variables:
            self.cFile.appendLine('if ({test})'.format(test=var.getBit('selection')))
            self.cFile.openBrace()
            
            self.copyVarToBuffer(var, count=True)
            self.cFile.closeBrace()
        
        self.cFile.appendLine()
        self.cFile.appendLine('return count; //Return the number of bytes that were actually copied')
        self.cFile.closeBrace()
        self.cFile.appendLine()
        
    def copyBitfieldToBuffer(self, count=False):
        #bitfield is called 'selection' locally
        #size of the bitfield
        bf_size = bitfieldSize(len(self.variables))
        
        for i in range(bf_size):
            self.cFile.appendLine('*(ptr++) = bf[{i}];'.format(i = i))
                
        if count:
            self.cFile.appendLine('count += {size};'.format(size=bf_size))
            
    def copyBitfieldFromBuffer(self, count=False):
        bf_size = bitfieldSize(len(self.variables))
        
        for i in range(bf_size):
            self.cFile.appendLine('bf[{i}] = *(ptr++);'.format(i=i))
            
        if count:
            self.cFile.appendLine('count += {size};'.format(size=bf_size))
        
    def copyVarToBuffer(self, var, count=False):
    
        #single byte, just copy across
        if var.bytes == 1: 
            self.cFile.appendLine('*(ptr++) = {data};'.format(data=var.getPtr('data')),comment="Copy the '{var}' variable".format(var=var.name))
        else:
            self.cFile.appendLine('Copy{sign}{bits}ToBuffer({data},ptr);'.format(
                            sign='I' if var.isSigned() else 'U',
                            bits=var.bytes*8,
                            data=var.getPtr('data')),
                            comment= "Copy the '{var}' variable ({n} bytes)".format(var=var.name,n=var.bytes))
            self.cFile.appendLine('ptr += {size};'.format(size=var.bytes))
            
            
        if count:
            self.cFile.appendLine('count += {size};'.format(size=var.bytes))
            
    def copyVarFromBuffer(self, var, count=False):
    
        if var.bytes == 1:
            self.cFile.appendLine('{data} = *(ptr++);'.format(data=var.getPtr('data')),comment="Copy the '{var}' variable".format(var=var.name))
        else:
            self.cFile.appendLine('Copy{sign}{bits}FromBuffer({data},ptr);'.format(
                            sign='I' if var.isSigned() else 'U',
                            bits=var.bytes*8,
                            data=var.getPtr('data')),
                            comment="Copy the '{var}' variable ({n} bytes)".format(var=var.name,n=var.bytes))
            self.cFile.appendLine('ptr += {size};'.format(size=var.bytes))
                
        if count:
            self.cFile.appendLine('count += {size};'.format(size=var.bytes))
        
    """
    Functions for copying data back out of a buffer
    """
    def copyAllFromPrototype(self):
        return self.createFunctionPrototype(
                            'CopyAllFromBuffer',
                            bits = False,
                            extra = [('*src','void')])
                            
    def createCopyAllFromFunction(self):
        self.cFile.appendLine(comment="Copy across *all* data from a buffer")
        self.cFile.appendLine(comment="Data will be copied even if it is invalid (selection bit is cleared)")
        self.cFile.appendLine(self.copyAllFromPrototype())
        
        self.cFile.openBrace()
        
        self.cFile.appendLine('uint8_t *ptr = (uint8_t*) src; //Pointer for keeping track of data addressing')
        self.cFile.appendLine()
        
        for var in self.variables:
            self.copyVarFromBuffer(var)
            self.cFile.appendLine()
        
        self.cFile.closeBrace()
        self.cFile.appendLine()
        
    def copyDataFromPrototype(self):
        return self.createFunctionPrototype('CopyDataFromBuffer',
                                            returnType='uint16_t',
                                            extra = [('*src','void')])
                                            
    def createCopyDataFromFunction(self):
        self.cFile.appendLine(comment="Copy across *selected* data from a buffer")
        self.cFile.appendLine(self.copyDataFromPrototype())
        self.cFile.openBrace()
        
        self.cFile.appendLine('uint8_t *ptr = (uint8_t*) src; //Pointer for keeping track of data addressing')
        self.cFile.appendLine('uint8_t *bf = (uint8_t*) selection; //Pointer for keeping track of the bitfield')
        self.cFile.appendLine('uint16_t count = 0; //Variable for keeping track of how many bytes were copied')
        self.cFile.appendLine()
        self.cFile.appendLine(comment='Copy the selection bits')
        
        self.copyBitfieldFromBuffer(count=True)
        
        self.cFile.appendLine()
        self.cFile.appendLine(comment='Only copy across variables that have actually been stored in the buffer')
        
        for var in self.variables:
            self.cFile.appendLine('if ({test})'.format(test=var.getBit('selection')))
            self.cFile.openBrace()
            
            self.copyVarFromBuffer(var,count=True)
            
            self.cFile.closeBrace()
            
        self.cFile.appendLine()
        self.cFile.appendLine('return count; //Return the number of bytes that were actually copied')
        
        self.cFile.closeBrace()
        self.cFile.appendLine()
        
        
    #enumerate through all the varibles in the struct, perform 'function' for each
    def createCaseEnumeration(self, blankFunction=None, returnFunction=None):
        
        for var in self.variables:
            self.cFile.addCase(var.getEnum())
            
            if blankFunction:
                blank = blankFunction(var)
                if not blank.endswith(';'):
                    blank += ';'
                self.cFile.appendLine(blank)
            if returnFunction:
                self.cFile.returnFromCase(returnFunction(var))
            else:
                self.cFile.breakFromCase()

    def titleByIndexPrototype(self):
        return 'char* Log{pref}_GetTitleByIndex(uint8_t index)'.format(pref=self.prefix)
        
    def titleByIndexFunction(self):
        self.cFile.appendLine(comment='Get the title of a variable based on its enumerated value')
        self.cFile.appendLine(self.titleByIndexPrototype())
        self.cFile.openBrace()
        
        self.cFile.startSwitch('index')
        
        #add case labels
        #function to return the index
        fn = lambda var: 'Log{prefix}_{var}Title()'.format(prefix=self.prefix,var=var.name)
        
        self.createCaseEnumeration(returnFunction = fn)
        
        self.cFile.endSwitch()
        
        self.cFile.appendLine(comment='Default return value')
        self.cFile.appendLine('return "";')
        
        self.cFile.closeBrace()
        self.cFile.appendLine()
        
    def unitsByIndexPrototype(self):
        return 'char* Log{pref}_GetUnitsByIndex(uint8_t index)'.format(pref=self.prefix)
        
    def unitsByIndexFunction(self):
        self.cFile.appendLine(comment='Get the units of a variable based on its enumerated value')
        self.cFile.appendLine(self.unitsByIndexPrototype())
        self.cFile.openBrace()
        
        self.cFile.startSwitch('index')
        
        fn = lambda var: 'Log{prefix}_{var}Units()'.format(prefix=self.prefix,var=var.name)
        
        self.createCaseEnumeration(returnFunction = fn)
        
        self.cFile.endSwitch()
        
        self.cFile.appendLine(comment='Default return value')
        self.cFile.appendLine('return "";')
        
        self.cFile.closeBrace()
        self.cFile.appendLine()
         
    def valueByIndexPrototype(self):
        return self.createFunctionPrototype('GetValueByIndex',bits=False,extra=[('index','uint8_t'), ('*str','char')])
        
    def valueByIndexFunction(self):
        self.cFile.appendLine(comment='Get a string-representation of a given variable, based on its enumerated value')
        self.cFile.appendLine(self.valueByIndexPrototype())
        self.cFile.openBrace()
        
        self.cFile.startSwitch('index')
        
        fn = lambda var: 'Log{prefix}_Decode{name}(data,str)'.format(prefix=self.prefix.capitalize(),name=var.name.capitalize())
        
        self.createCaseEnumeration(blankFunction=fn)
        
        self.cFile.endSwitch()
        
        self.cFile.closeBrace()
        self.cFile.appendLine()
        
    #function to determine the size of the selected data
    def getSelectionSizePrototype(self):
        return self.createFunctionPrototype('GetSelectionSize',data=False,returnType='uint16_t')
        
    def getSelectionSizeFunction(self):
        self.cFile.appendLine(comment='Get the total size of the selected variables')
        self.cFile.appendLine(self.getSelectionSizePrototype())
        self.cFile.openBrace()
        
        self.cFile.appendLine('uint16_t size = 0;')
        self.cFile.appendLine()
        
        for var in self.variables:
            self.cFile.appendLine('if ({test})'.format(test=var.getBit('selection')))
            self.cFile.openBrace()
            self.cFile.appendLine('size += {n};'.format(n=var.bytes))
            self.cFile.closeBrace()
            
        self.cFile.appendLine()
        self.cFile.appendLine('return size;')
        
        self.cFile.closeBrace()
        self.cFile.appendLine()
        
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
        
        self.format = self.parseFormat(format)
        self.comment = "//!< " + str(comment) if comment else ""
        self.units = units
        self.scaler = scaler
        
        self.bytes = extractNumBytesFromVarType(self.format)
        
    def parseFormat(self, format):
        format = format.replace("unsigned","uint")
        format = format.replace("signed","int")
        if not format.endswith("_t"):
            format = format + "_t"
            
        return format
        
    #datatype definition string (with comment appended)
    def dataString(self):
        return "{datatype} {name}; {comment}".format(
                datatype = self.format,
                name = self.name,
                comment = self.comment)
                
    #wrap a given function name
    def getFunctionName(self, fnName):
        return "{fn}{name}".format(name=self.name.capitalize(), fn=fnName.capitalize())
        
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
        return 'SetBitByPosition({struct},{pos})'.format(
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
        return '"{name}"'.format(name=self.name)
        
    def getUnitsString(self):
        if not self.units:
            return '""'
        else:
            return '"{units}"'.format(units=self.units)
            
    def isSigned(self):
        return self.format.startswith('i')
