import re,os
import time

from math import ceil, log

from code_writer import CodeWriter

from logjam_version import LOGJAM_VERSION, AutogenString

from logjam_common import *

from logjam_element import LogVariable, LogEvent
    
class LogFile:
    def __init__(self, prefix, version, sourceFile, vars=None, events=None, outputdir=None):
        
        if not vars:
            vars = []
        
        if not events:
            events = []
        
        self.variables = vars
        self.events = events
        
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
        
    def constructCodeFile(self):
        
        self.cFile.clear()
        
        self.cFile.append(AutogenString(self.source))
        
        #include the header file
        self.cFile.include('"{file}.h"'.format(file=headerFileName(self.prefix)))
        
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
        
        if len(self.events) > 0:
            self.cFile.appendLine()
            self.cFile.appendLine(comment='Functions to copy *events* to a buffer')
            
            for e in self.events:
                self.addEventCopyFuncs(e)
                
            self.cFile.appendLine(comment='Decode a {pref} event to a string'.format(pref=self.prefix))
            self.eventsToStringFunction()
            
            self.cFile.appendLine()
            self.cFile.appendLine(comment='Functions for formatting individual events to a string')
            for e in self.events:
                self.eventToStringFunc(e)
       
    def constructHeaderFile(self):
        
        self.hFile.clear()
        
        self.hFile.append(AutogenString(self.source))
        
        self.hFile.startIf(headerDefineName(self.prefix),invert=True)
        self.hFile.define(headerDefineName(self.prefix))
        
        self.hFile.appendLine()
        self.hFile.include('"logjam_common.h"', comment='common LogJam routines')
        
        self.hFile.appendLine()
        
        self.hFile.externEntry()
        
        #version information
        self.hFile.appendLine()
        self.hFile.appendLine(comment='{pre} logging version'.format(pre=self.prefix))
        self.hFile.define('LOG_{pref}_VERSION()'.format(pref=self.prefix),value='"{v}"'.format(v=self.version))
        
        vMaj, vMin = self.version.split('.')
        
        self.hFile.define('LOG_{pref}_VERSION_MAJOR'.format(pref=self.prefix),value=vMaj)
        self.hFile.define('LOG_{pref}_VERSION_MINOR'.format(pref=self.prefix),value=vMin)

        self.hFile.appendLine()
        #create global enumeration for the variables
        fn = lambda i,val: "{val} is stored in byte {n}, position {m}".format(val=val,n=int(int(i)/8),m=i%8)
        self.hFile.createEnum('Log{pref}_VariableEnum_t'.format(pref=self.prefix),[v.getEnumString() for v in self.variables],split=8,commentFunc=fn)
        
        self.hFile.appendLine(comment='{n} bytes are required to store all parameter selction bits for {log} logging'.format(n=bitfieldSize(len(self.variables)),log=self.prefix))
        self.hFile.define('LOG_{pref}_SELECTION_BYTES'.format(pref=self.prefix.upper()),value=bitfieldSize(len(self.variables)))
        self.hFile.appendLine()
        
        self.hFile.appendLine(comment="Number of variables defined for the '{pref}' logging structure".format(pref=self.prefix))
        self.hFile.define('LOG_{pref}_VARIABLE_COUNT'.format(pref=self.prefix.upper()), value=len(self.variables))
        self.hFile.appendLine()
        
        self.hFile.appendLine(comment="Struct definition for storing the selection bits of the " + self.prefix + " logging struct")
        self.hFile.appendLine(comment='This is not stored as a native c bitfield to preserve explicit ordering between processors, compilers, etc')
        self.hFile.appendLine('typedef uint8_t {name}[LOG_{pref}_SELECTION_BYTES];'.format(pref=self.prefix.upper(),name=bitfieldStructName(self.prefix)))
        self.hFile.appendLine()
        self.hFile.appendLine(comment="Data struct definition for the " + self.prefix + " logging struct")
        self.createDataStruct()
        
        #total data size
        d_size = sum([v.bytes for v in self.variables])
        self.hFile.appendLine()
        self.hFile.appendLine(comment='{n} bytes are required to store all the data parameters'.format(n=d_size))
        self.hFile.define('LOG_{pref}_DATA_BYTES'.format(pref=self.prefix.upper()),value=d_size)
        
        self.hFile.appendLine()
        
        #events
        if len(self.events) > 0:
            self.hFile.appendLine(comment='Logging event definitions for the {the}'.format(the=self.prefix))
            self.hFile.appendLine(comment='Enumeration starts at 0x80 as *generic* events are 0x00 -> 0x7F')
            self.hFile.createEnum('Log{pref}_EventEnum_t'.format(pref=self.prefix),[e.getEnumString() for e in self.events],start="0x80")
            
        self.hFile.appendLine()
        
        self.hFile.appendLine(comment='Functions to copy various log events to logging buffer')
        self.hFile.appendLine(comment='Each function returns the number of bytes written to the log') 
        self.hFile.appendLine(comment='Pointer is automatically incremented as required')
        #functions for the events
        for e in self.events:
            self.hFile.appendLine('inline uint8_t {func};'.format(func=e.eventPrototype()))
        
        self.hFile.appendLine();
        self.hFile.appendLine(comment='Function to extract an event from a buffer, and format it as a human-readable string')
        self.hFile.appendLine(self.eventsToStringPrototype() + ';')
        
        self.hFile.appendLine()
        self.hFile.appendLine(comment='Functions for turning individual events into strings')
        for e in self.events:
            self.hFile.appendLine(e.toStringPrototype() + ';',comment='Format the {evt} event into a string'.format(evt=e.getEnumString()))
        
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
            self.hFile.appendLine(self.additionPrototype(var) + '; //Add ' + var.name + " to the log struct")
            self.hFile.appendLine(self.decodePrototype(var) + '; //Decode ' + var.name + ' into a printable string')
        
        self.hFile.appendLine()
        self.hFile.externExit()
        
        self.hFile.endIf()
    
    def saveFiles(self):
        
        self.constructHeaderFile()
        self.constructCodeFile()
        
        self.hFile.writeToFile()
        self.cFile.writeToFile() 
        
    def addEventCopyFuncs(self, e):
        #copy TO buffer
        self.cFile.appendLine('inline uint8_t {func}'.format(func=e.eventPrototype()))
        self.cFile.openBrace()
        
        #copy across the event type
        self.cFile.appendLine('*(*ptr++) = {evt};'.format(evt=e.getEnumString()),comment='Copy the event type to the buffer')
        
        if len(e.variables) > 0:
            self.cFile.appendLine()
            for v in e.variables:
                self.copyVarToBuffer(v,struct='',pointer='ptr')
        
        self.cFile.appendLine()
        self.cFile.appendLine('return {n};'.format(n=e.eventSize()),comment='Number of bytes copied')
        
        self.cFile.closeBrace()
        self.cFile.appendLine()
        
    #create the struct of the variables
    def createDataStruct(self):
    
        self.hFile.appendLine('typedef struct {')
        
        self.hFile.tabIn()
        
        for v in self.variables:
            self.hFile.appendLine(comment="Variable '{name}'{units}{scaler} ({n} bytes)".format(
                    name = v.name,
                    units = ", units='{u}'".format(u=v.units) if v.units else '',
                    scaler = ", scaler=1.0/{scaler}".format(scaler=v.scaler) if v.scaler > 1 else '',
                    n = v.bytes))
            
            self.hFile.appendLine(v.dataString())
        
        self.hFile.tabOut()
        
        self.hFile.appendLine('} ' + dataStructName(self.prefix) + ';')
        
    def additionPrototype(self,var):
        return self.createVariableFunction(var,'add',returnType='bool',extra=[('onlyIfNew','bool')])
        
    #create the function for adding a variable to the logging structure
    def createAdditionFunction(self, var):
    
        self.cFile.appendLine(comment='Add variable {name} to the {prefix} logging struct'.format(
                        name=var.name,
                        prefix=self.prefix))
                        
        self.cFile.appendLine(self.additionPrototype(var))
        self.cFile.openBrace()
        self.cFile.appendLine('if (onlyIfNew == true)',comment='Ignore value if it is the same as the value already stored')
        self.cFile.openBrace()
        self.cFile.appendLine('if (data->{var} == {var})'.format(var=var.name))
        self.cFile.tabIn()
        self.cFile.appendLine('return false;')
        self.cFile.tabOut()
        self.cFile.closeBrace()
        self.cFile.appendLine()
        self.cFile.appendLine(var.setBit('selection'),comment='Set the appropriate bit')
        #now actually add the variable in
        self.cFile.appendLine(var.addVariable('data'))
        self.cFile.appendLine()
        self.cFile.appendLine('return true;')
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
        self.cFile.appendLine('sprintf(str,"{patt}",data->{var});'.format(patt=var.getStringCast(),var=var.name))
        self.cFile.closeBrace()
        self.cFile.appendLine()
        pass
        
    #create a function pointing to a particular variable
    def createVariableFunction(self, var, name, blank=False, extra=None,ptr=False, **params):
        name = var.getFunctionName(name)
        
        if not extra:
            extra = []
        
        if not blank:
            extra = [('{ptr}{name}'.format(ptr='*' if ptr else '',name=var.name),var.format)] + extra
        
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
        
        self.cFile.appendLine('uint8_t *bf = (uint8_t*) selection;')
        for i in range(bitfieldSize(len(self.variables))):
            self.cFile.appendLine('bf[{n}] = 0; //Clear byte {x} of {y}'.format(n=i,x=i+1,y=bitfieldSize(len(self.variables))))
        
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
        
    def copyVarToBuffer(self, var, struct='data->', pointer='&ptr', count=False):
        self.cFile.appendLine('Copy{sign}{bits}ToBuffer({struct}{name}, {ptr});'.format(
                            sign='I' if var.isSigned() else 'U',
                            bits=var.bytes*8,
                            struct=struct,
                            name=var.name,
                            ptr = pointer),
                            comment= "Copy the '{var}' variable ({n} bytes)".format(var=var.name,n=var.bytes))            
            
        if count:
            self.cFile.appendLine('count += {size};'.format(size=var.bytes))
            
    def copyVarFromBuffer(self, var, struct='data->',pointer='&ptr',count=False):
    
        self.cFile.appendLine('Copy{sign}{bits}FromBuffer({struct}{name}, {ptr});'.format(
                            sign='I' if var.isSigned() else 'U',
                            bits=var.bytes*8,
                            struct=struct,
                            name=var.name,
                            ptr = pointer,
                            ),
                            comment="Copy the '{var}' variable ({n} bytes)".format(var=var.name,n=var.bytes))
                
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
    def createCaseEnumeration(self, vars=None, blankFunction=None, returnFunction=None):
        
        if not vars:
            vars = self.variables
        
        for var in vars:
            self.cFile.addCase(var.getEnumString())
            
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
        
        fn = lambda var: 'Log{prefix}_Decode{name}(data,str)'.format(prefix=self.prefix.capitalize(),name=var.name)
        
        self.createCaseEnumeration(blankFunction=fn)
        
        self.cFile.endSwitch()
        
        self.cFile.closeBrace()
        self.cFile.appendLine()
        
    #function to turn an event into a string
    #pass a pointer to where the event data starts
    #pointer will be auto-incremented
    #returns 'true' if an event was extracted, else false
    def eventsToStringPrototype(self):
        return 'bool Log{pref}_EventToString(uint8_t **ptr, char *str)'.format(pref=self.prefix)
        
    def eventsToStringFunction(self):
        self.cFile.startComment()
        self.cFile.appendLine('Extract an event from a buffer, given a pointer to the buffer, and a pointer to where the event will be strung')
        self.cFile.appendLine('Function will auto-increment the pointer as necessary')
        self.cFile.appendLine('Returns true if event was extracted and formatted as string, else returns false')
        self.cFile.finishComment()
        self.cFile.appendLine(self.eventsToStringPrototype())
        self.cFile.openBrace()
        self.cFile.appendLine()
        
        self.cFile.appendLine('#error this needs to be completed')
        self.cFile.startSwitch('TBD')
        
        #function for formatting a given even to a string
        fn = lambda var: 'Log{pref}_EventToString_{name}(ptr,str)'.format(pref=var.prefix,name=var.name)
        
        self.createCaseEnumeration(vars = self.events, blankFunction = fn)
        self.cFile.addCase('default')
        self.cFile.returnFromCase(value='false')
        self.cFile.endSwitch()
        self.cFile.appendLine('return true;',comment='Default return case')
        self.cFile.closeBrace()
        
    #func for formatting an individual func to a string
    def eventToStringFunc(self, evt):
        self.cFile.appendLine(comment='Format a {evt} event into a readable string'.format(evt=evt.name))
        self.cFile.appendLine(comment='Auto-increment the **ptr pointer')
        self.cFile.appendLine(evt.toStringPrototype())
        self.cFile.openBrace()
        
        #define vars for this event
        for v in evt.variables:
            #local var for temp storage of data
            self.cFile.appendLine('{fmt} {name};'.format(fmt=v.format,name=v.name),comment="Temporary storage for '{var}' variable".format(var=v.name))
        
        self.cFile.appendLine()
        
        if len(evt.variables) > 0:
            self.cFile.appendLine(comment='Copy the event variables from the buffer')
        
            for v in evt.variables:
                self.copyVarFromBuffer(v,struct='&',pointer='ptr')

            self.cFile.appendLine()
            
        #compile a list of variables associated with this event
        fmts = " ".join([v.getStringCast() for v in evt.variables])
        vars = ", ".join([v.name for v in evt.variables])
        
        self.cFile.appendLine('sprintf(str,"Event: {evt}{sep}{formats}"{comma}{vars});'.format(
                evt = evt.getEnumString(),
                sep = ' -> ' if len(fmts) > 0 else '',
                formats = fmts,
                comma = ', ' if len(vars) > 0 else '',
                vars = vars))
        
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
        

