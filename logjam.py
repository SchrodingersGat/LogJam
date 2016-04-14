import re,os

from code_writer import CodeWriter

#LOGJAM version
LOGJAM_VERSION = "0.1"

#log entry struct of the format Device_LogEntry_t
def topLevelStruct(prefix):
    return "{prefix}_LogEntry_t".format(prefix=prefix)
    
#bitfield struct of the format Device_LogBitfield_t"
def bitfieldStruct(prefix):
    return "{prefix}_LogBitfield_t".format(prefix=prefix)
    
#data struct for the format Device_LogData_t
def dataStruct(prefix):
    return "{prefix}_LogData_t".format(prefix=prefix)

#header file define string
def headerDefine(prefix):
    return "_LOG_{prefix}_DEFS_H_".format(prefix=prefix.upper())
    
#header file name
def headerFilename(prefix):
    return "log_{prefix}_defs".format(prefix=prefix.lower())
    
def externEntry():
    s  = '//Play nice with C++ compilers!\n'
    s += '#ifdef __cplusplus\n'
    s += 'extern "C" {\n'
    s += '#endif\n'
    
    return s
    
def externExit():
    s  = '#ifdef __cplusplus\n'
    s += '}\n'
    s += '#endif\n'
    s += '//We are done playing nice with C++ compilers\n'
    
    return s
    
class LogFile:
    def __init__(self, vars, prefix, version, outputdir=None):
        self.variables = vars
        self.prefix = prefix
        self.version = version
        
        hfile = headerFilename(prefix) + '.h'
        cfile = headerFilename(prefix) + '.c'
        
        if outputdir:
            hfile = os.path.join(outputdir, hfile)
            cfile = os.path.join(outputdir, cfile)
        
        self.hFile = CodeWriter(hfile)
        self.cFile = CodeWriter(cfile)
    
    def createHeaderEntry(self):
        self.hFile.appendLine("#ifndef {h}".format(h=headerDefine(self.prefix)))
        self.hFile.appendLine("#define {h}".format(h=headerDefine(self.prefix)))
        
    def createHeaderExit(self):
        self.hFile.appendLine("#endif //{h}".format(h=headerDefine(self.prefix)))

    def createHeaderInclude(self):
        self.cFile.appendLine('#include "{file}.h"'.format(file=headerFilename(self.prefix)))
        
    def createAutogenInfo(self):
        self.hFile.startComment()
        self.hFile.appendLine("Logging structure definitions for the {device}".format(device=self.prefix))
        self.hFile.appendLine("This file was created using LogJam v{version}".format(version=LOGJAM_VERSION))
        self.hFile.finishComment()
        self.hFile.appendLine()
        
    def createVersionString(self):
        self.hFile.appendLine('#define {prefix}_GetLogVersion() {{return "{version}";}}\n'.format(
                        prefix=self.prefix,
                        version=self.version))
        
    def constructCodeFile(self):
        
        self.cFile.clear()
        
        #include the header file
        self.createHeaderInclude()
        
        self.cFile.appendLine()
        
        #add in the global functions
        self.cFile.startComment()
        self.cFile.appendLine("Global functions")
        self.cFile.finishComment()
        
        self.createInitFunction()
        self.createResetFunction()
        self.createCopyAllFunction()
        self.createCopySomeFunction()
        
        self.cFile.appendLine()
        self.cFile.startComment()
        self.cFile.appendLine("Individual variable functions")
        self.cFile.finishComment()
        
        #add in the functions to add variables
        for v in self.variables:
            self.cFile.appendLine()
            self.createAdditionFunction(v)
       
    def constructHeaderFile(self):
        
        self.hFile.clear()
        
        self.createHeaderEntry()
        
        self.hFile.appendLine()
        
        self.hFile.appendLine("#include <stdint.h> //Primitive definitions")
        self.hFile.appendLine("#include <string.h> //memcpy function")
        
        self.hFile.appendLine()
        
        self.hFile.appendLine(externEntry())
        
        self.createAutogenInfo()
        self.createVersionString()
        
        self.hFile.appendCommentLine("Bitfield struct definition for the " + self.prefix + " logging struct")
        self.createBitfieldStruct()
        self.hFile.appendLine()
        self.hFile.appendCommentLine("Data struct definition for the " + self.prefix + " logging struct")
        self.createDataStruct()
        self.hFile.appendLine()
        self.hFile.appendCommentLine("Structure for complete definition of the " + self.prefix + " logging protocol")
        self.hFile.appendLine('typedef struct')
        self.hFile.openBrace()
        self.hFile.appendCommentLine("Cumulative size of the logging struct")
        self.hFile.appendLine("uint16_t size;")
        self.hFile.appendLine()
        self.hFile.appendCommentLine("Bitfield defining which variables are selected")
        self.hFile.appendLine(bitfieldStruct(self.prefix) + " selection;")
        self.hFile.appendLine()
        self.hFile.appendCommentLine("Struct defining the actual data to be logged")
        self.hFile.appendLine(dataStruct(self.prefix) + " data;")
        self.hFile.tabOut()
        self.hFile.appendLine()
        
        self.hFile.appendLine("} " + topLevelStruct(self.prefix) + ";")
        
        self.hFile.appendLine()
        
        self.hFile.startComment()
        self.hFile.appendLine("Global Functions:")
        self.hFile.appendLine("These functions are applied to the global struct " + topLevelStruct(self.prefix))
        self.hFile.finishComment()
        
        self.hFile.appendCommentLine("Initialize the logging structure")
        self.hFile.appendLine(self.initPrototype() + ";")
        
        self.hFile.appendCommentLine("Reset the bitfield of the logging structure")
        self.hFile.appendLine(self.resetPrototype() + ";")
        
        self.hFile.appendCommentLine('Copy *all* data from the logging structure')
        self.hFile.appendLine(self.copyAllPrototype() + ';')
        
        self.hFile.appendCommentLine("Copy *some* of the data from the logging structure")
        self.hFile.appendLine(self.copySomePrototype() + ";")
        
        self.hFile.appendLine()
        
        self.hFile.startComment()
        self.hFile.appendLine("Variable Functions:")
        self.hFile.appendLine("These functions are applied to individual variables within the logging structure")
        self.hFile.finishComment()
        
        self.hFile.appendCommentLine('Function prototypes for adding the variables to the data struct')
        
        #add in the 'addition' functions
        for var in self.variables:
            self.hFile.appendLine(var.getFunctionPrototype('add',inline=True) + "; //Add " + var.prefix + " to the log struct")
        
        
        self.hFile.appendLine()
        self.hFile.appendLine(externExit())
        
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
            self.hFile.appendLine(v.dataString())
        
        self.hFile.tabOut()
        
        self.hFile.appendLine('} ' + dataStruct(self.prefix) + ';')
        
    #create a bitfield struct of all variables
    def createBitfieldStruct(self):
    
        self.hFile.appendLine('typedef struct {')
        
        self.hFile.tabIn()
        
        for v in self.variables:
            self.hFile.appendLine(v.bitfieldString())
            
        self.hFile.tabOut()
        
        self.hFile.appendLine('} ' + bitfieldStruct(self.prefix) + ';')
        
    #create the function for adding a variable to the logging structure
    def createAdditionFunction(self, var):
    
        self.cFile.appendCommentLine('Add variable {name} to the {prefix} logging struct'.format(
                        name=var.name,
                        prefix=self.prefix))
                        
        self.cFile.appendLine(var.getFunctionPrototype('add',inline=True))
        self.cFile.openBrace()
        
        #check if the variable is already 'in' the log struct
        #if it isn't, set the bit and increment the size
        self.cFile.appendCommentLine("Check if the '{data}' is already in the logging struct".format(
                            data=var.name))
        self.cFile.appendLine(var.checkNotBit())
        self.cFile.openBrace()
        self.cFile.appendLine(var.setBit())
        self.cFile.appendLine(var.incrementSize())
        self.cFile.closeBrace()
        
        self.cFile.appendLine()
        #now actually add the variable in
        self.cFile.appendLine(var.addVariable())
        
        self.cFile.closeBrace()
        
    def createFunctionPrototype(self, name, inline=False, returnType='void', params={}):
        
        #pass extra parameters to the function as such
        #paramsa = {'dest': 'void*'} (name, type)
        paramstring = ""
        for k in params.keys():
            paramstring += ', '
            paramstring += params[k]
            paramstring += ' '
            paramstring += k
            
        return '{inline}{returnType} {prefix}Log_{name}({struct} *log{params})'.format(
                    inline='inline ' if inline else '',
                    returnType=returnType,
                    prefix=self.prefix.capitalize(),
                    name=name,
                    struct=topLevelStruct(self.prefix),
                    params=paramstring)
                    
    def resetPrototype(self):
        return self.createFunctionPrototype('Reset')
                    
    #create a function to reset the logging structure
    def createResetFunction(self):
        
        #add the reset function to the c file
        self.cFile.appendCommentLine('Reset the log data struct (e.g. after writing to memory)')
        self.cFile.appendCommentLine('Only the selection bits need to be reset')
        self.cFile.appendLine(self.resetPrototype())
        self.cFile.openBrace()
        
        self.cFile.appendLine("memset(&(log->selection),0,sizeof(" + bitfieldStruct(self.prefix) + "));")
        
        self.cFile.closeBrace()
        self.cFile.appendLine()
        
    def initPrototype(self):
        return self.createFunctionPrototype('Initialize')
        
    #create a func to initialize the logging structure
    def createInitFunction(self):
    
        self.cFile.appendCommentLine("Initialize the log data struct to zero")
        self.cFile.appendLine(self.initPrototype())
        self.cFile.openBrace()
        self.cFile.appendLine('memset(&log,0,sizeof({struct}));'.format(struct=topLevelStruct(self.prefix)))
        self.cFile.closeBrace()
        self.cFile.appendLine()
        
    def copyAllPrototype(self):
        return self.createFunctionPrototype('CopyAll',params={'dest' : 'void*'})
        
    #create a function to copy ALL parameters across, conserving data format
    def createCopyAllFunction(self):
        
        self.cFile.appendCommentLine("Copy ALL data in the log struct to the provided address")
        self.cFile.appendCommentLine("Data will be copied even if the associated selection bit is cleared")
        
        self.cFile.appendLine(self.copyAllPrototype())
        self.cFile.openBrace()
        self.cFile.appendLine('memcpy(dest, &(log->data), sizeof({struct}));'.format(struct=dataStruct(self.prefix)))
        self.cFile.closeBrace()
        self.cFile.appendLine()
        
    def copySomePrototype(self):
        return self.createFunctionPrototype('CopySome',params={'dest' : 'void*'}, returnType='uint16_t')
        
    #create a function that copies across ONLY the bits that are set
    def createCopySomeFunction(self):
        self.cFile.appendCommentLine("Copy across data whose selection bit is set")
        self.cFile.appendCommentLine("Only data selected will be copied (in sequence)")
        self.cFile.appendCommentLine("Ensure a copy of the selection bits is stored for decoding")
        self.cFile.appendLine(self.copySomePrototype());
        self.cFile.openBrace()
        self.cFile.appendLine('void* ptr = dest;')
        self.cFile.appendLine('uint16_t count = 0; //Variable for keeping track of how many bytes were copied')
        self.cFile.appendLine()
        self.cFile.appendCommentLine('Check each variable in the logging struct to see if it should be added')
        
        for var in self.variables:
            self.cFile.appendLine(var.checkBit())
            self.cFile.openBrace()
            #copy the data across
            self.cFile.appendLine('memcpy(ptr, {ptr}, {size}); //Copy the data'.format(ptr=var.getPtr(), size=var.getSize()))
            self.cFile.appendLine('ptr += {size}; //Increment the pointer'.format(size=var.getSize()))
            self.cFile.appendLine('count += {size}; //Increase the count'.format(size=var.getSize()))
            self.cFile.closeBrace()
        
        self.cFile.appendLine()
        self.cFile.appendLine('return count; //Return the number of bytes that were actually copied')
        self.cFile.closeBrace()
        self.cFile.appendLine()

class LogVariable:

    #prefix = name of the 'device'
    #name = name of this variable
    #format = primitive datatype
    #comment = comment string
    def __init__(self, prefix, name, format, comment=None):
        self.prefix = prefix
        self.name = name
        self.format = self.parseFormat(format)
        self.comment = "//!< " + str(comment) if comment else ""
        
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
                
    #bitfield definition string (with comment appended)
    def bitfieldString(self):
        return "unsigned {name} : 1; {comment}".format(
                name = self.name,
                comment = self.comment)
                
    #wrap a given function name
    def getFunctionName(self, fnName):
        return "{prefix}Log_{fn}{name}".format(prefix=self.prefix.capitalize(),name=self.name.capitalize(), fn=fnName.capitalize())
        
    #get a prototype for a function of a given name
    def getFunctionPrototype(self, fname, inline=False):
        s = 'inline ' if inline else ''
        s += 'void '
        s += self.getFunctionName(fname)
        s += '('
        s += topLevelStruct(self.prefix)
        s += '* log, '
        s += self.format
        s += ' ' + self.name.lower() + ')'
        
        return s
        
    #assume there is always a pointer to *log
    
    #check if a bit is set
    def checkBit(self):
        return 'if (log->selection.{name})'.format(name=self.name)

    #check if a bit is not set
    def checkNotBit(self):
        return 'if (log->selection.{name} == 0)'.format(name=self.name)
    
    #code prototype to set the selection bit
    def setBit(self):
        return 'log->selection.{name} = 1; //Set the {name} bit'.format(name=self.name)
        
    #code prototype to clear the selection bit
    def clearBit(self):
        return 'log->selection.{name} = 0; //Clear the {name} bit'.format(name=self.name)
        
    def getSize(self):
        return 'sizeof(log->data.{name})'.format(name=self.name)
        
    def getPtr(self):
        return '&(log->data.{name})'.format(name=self.name)
        
    #increment the 'size' counter by the size of this datatype
    def incrementSize(self):
        s  = 'log->size += sizeof(log->data.{name}); //Increment the size counter'.format(name=self.name)
        return s
        
    #add the variable to the struct
    def addVariable(self):
        return "log->data.{name} = {name}; //Add the '{name}' variable".format(name=self.name)
