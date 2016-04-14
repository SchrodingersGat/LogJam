import sys
import os
import re

from code_writer import CodeWriter

LOGJAM_VERSION = "0.1"

def say(*arg):
    print(" ".join(map(str,arg)))

def close(*arg):
    say(*arg)
    sys.exit(0)
    
#get an xml file
if len(sys.argv) < 2 or not sys.argv[1].endswith(".xml"):
    close("No xml file supplied")
    
xml_file = sys.argv[1]

#import xml funcs
from xml.etree import ElementTree

outputdir = None

#have we been directed to an output directory?
if len(sys.argv) > 2:
    outputdir = os.path.abspath(sys.argv[2])
    if not os.path.isdir(outputdir):
        say(outputdir,'is not a valid directory')
        outputdir = None
    
else:
    say('No output directory specified.')
    
if not outputdir:
    say('Writing files to',os.getcwd())
else:
    say('Writing files to',outputdir)
#top level funx

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
    
class LogHeaderFile:
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
        
        #init function
        self.createInitFunction()
        #reset function
        self.createResetFunction()
        
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
        self.hFile.appendLine(self.createFunctionPrototype('initialize') + ";")
        
        self.hFile.appendCommentLine("Reset the bitfield of the logging structure")
        self.hFile.appendLine(self.createFunctionPrototype('reset') + ";")
        
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
        
    def createFunctionPrototype(self, name, inline=False):
        return '{inline}void {prefix}Log_{name}({struct} *log)'.format(
                    inline='inline ' if inline else '',
                    prefix=self.prefix.capitalize(),
                    name=name.capitalize(),
                    struct=topLevelStruct(self.prefix))
                    
    #create a function to reset the logging structure
    def createResetFunction(self):
        
        #add the reset function to the c file
        self.cFile.appendCommentLine('Reset the log data struct (e.g. after writing to memory)')
        self.cFile.appendCommentLine('Only the selection bits need to be reset')
        self.cFile.appendLine(self.createFunctionPrototype('reset'))
        self.cFile.openBrace()
        
        self.cFile.appendLine("memset(&(log->selection),0,sizeof(" + bitfieldStruct(self.prefix) + "));")
        
        self.cFile.closeBrace()
        self.cFile.appendLine()
        
    #create a func to initialize the logging structure
    def createInitFunction(self):
    
        self.cFile.appendCommentLine("Initialize the log data struct to zero")
        self.cFile.appendLine(self.createFunctionPrototype('initialize'))
        self.cFile.openBrace()
        self.cFile.appendLine('memset(&log,0,sizeof({struct}));'.format(struct=topLevelStruct(self.prefix)))
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
        
    #increment the 'size' counter by the size of this datatype
    def incrementSize(self):
        s  = 'log->size += sizeof(log->data.{name}); //Increment the size counter'.format(name=self.name)
        return s
        
    #set the 'size' field to zero
    def clearSize(self):
        return 'log->size = 0; //Clear the size counter'
        
    #add the variable to the struct
    def addVariable(self):
        return "log->data.{name} = {name}; //Add the '{name}' variable".format(name=self.name)

        
with open(xml_file, 'rt') as xml:
    tree = ElementTree.parse(xml)
    
    root = tree.getroot()
    
    #check that it's "Logging"
    if not root.tag == "Logging":
        close("Root of xml tree should be 'logging'")
    
    #extract the name of the logging structure
    prefix = root.attrib.get("name",None)
    
    if not prefix:
        close("Logging prefix not set - use attribute 'name'")
        
    #extract the version number
    version = root.attrib.get("version",None)
    
    if not version:
        close("Version number not set")
        
    #is the version number 'valid'?
    
    result = re.match("(\d*).(\d*)", version)
    
    try:
        version_major = int(result.groups()[0])
        version_minor = int(result.groups()[1])
    except:
        close("Version number incorrect format -",version)
    
    variables = []
    
    #extract the children
    for node in root:
        a = node.attrib
        
        name = a.get('name',None)
        datatype = a.get('type',None)
        comment = a.get('comment',None)
        
        if not name:
            print('Name missing for', a)
            continue
        if not datatype:
            print('Type missing for', a)
            continue
            
        variables.append(LogVariable(prefix,name,datatype,comment))
        
    lf = LogHeaderFile(variables, prefix, version, outputdir=outputdir)
    
    lf.saveFiles()

close("Complete!")