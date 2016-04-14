import sys
import os
import re

def close(*arg):
    print(" ".join(map(str,arg)))
    sys.exit(0)
    
#get an xml file
if len(sys.argv) < 2 or not sys.argv[1].endswith(".xml"):
    close("No xml file supplied")
    
xml_file = sys.argv[1]

#import xml funcs
from xml.etree import ElementTree

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
    s  = '#ifdef __cplusplus\n'
    s += 'extern "C" {\n'
    s += '#endif\n'
    
    return s
    
def externExit():
    s  = '#ifdef __cplusplus\n'
    s += '}\n'
    s += '#endif\n'
    
    return s
    
#class for simplifying generation of code
class CodeWriter:
    def __init__(self, fname):
        self.fname = fname
        
        self.clear()
        
    def tabIn(self):
        self.tabs += 1
        
    def tabOut(self):
        if self.tabs > 0:
            self.tabs -= 1
            
    def append(self, text):
        self.text = self.text + '\t' * self.tabs + text
        
    def appendLine(self, text=None):
        if not text:
            self.append('\n')
        else:
            self.append(text + '\n')
            
    def openBrace(self):
        self.appendLine('{')
        self.tabIn()
    
    def closeBrace(self):
        self.tabOut()
        self.appendLine('}')
        
    def writeToFile(self):
        with open(self.fname,'w') as file:
            file.write(self.text)
            
    def clear(self):
        self.text = ''
        self.tabs = 0
    
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
        self.cFile.appendLine("#include {file}.h".format(file=headerFilename(self.prefix)))
        
    def constructCodeFile(self):
        
        self.cFile.clear()
        
        #include the header file
        self.createHeaderInclude()
        self.cFile.appendLine()
        
        #add in the functions to add variables
        for v in self.variables:
            self.cFile.appendLine()
            self.createAdditionFunction(v)
       
    def constructHeaderFile(self):
        
        self.hFile.clear()
        
        self.createHeaderEntry()
        
        self.hFile.appendLine()
        
        self.hFile.appendLine(externEntry())
        
        self.hFile.appendLine()
        self.hFile.appendLine("//Bitfield struct definition for the " + self.prefix + " logging struct")
        self.createBitfieldStruct()
        self.hFile.appendLine()
        self.hFile.appendLine("//Data struct definition for the " + self.prefix + " logging struct\n")
        self.createDataStruct()
        self.hFile.appendLine()
        self.hFile.appendLine("//Structure for complete definition of the " + self.prefix + " logging protocol\n")
        self.hFile.appendLine('typedef struct')
        self.hFile.openBrace()
        self.hFile.appendLine("//Cumulative size of the logging struct")
        self.hFile.appendLine("uint16_t size;")
        self.hFile.appendLine()
        self.hFile.appendLine("//Bitfield defining which variables are selected")
        self.hFile.appendLine(bitfieldStruct(self.prefix) + " selection;")
        self.hFile.appendLine()
        self.hFile.appendLine("//Struct defining the actual data to be logged")
        self.hFile.appendLine(dataStruct(self.prefix) + " data;")
        self.hFile.tabOut()
        
        self.hFile.appendLine("} " + topLevelStruct(self.prefix) + ";")
        
        self.hFile.appendLine("\n")
        
        self.hFile.appendLine('//Function prototypes for adding the variables to the data struct')
        
        #add in the 'addition' functions
        for var in self.variables:
            self.hFile.appendLine(var.getFunctionPrototype('add') + "; //Add " + var.prefix + " to the log struct")
        
        
        self.hFile.appendLine("\n")
        
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
    
        self.cFile.appendLine('//Add variable {name} to the {prefix} logging struct\n'.format(
                        name=var.name,
                        prefix=self.prefix))
                        
        self.cFile.appendLine(var.getFunctionPrototype('add'))
        self.cFile.openBrace()
        
        #check if the variable is already 'in' the log struct
        #if it isn't, set the bit and increment the size
        self.cFile.appendLine(var.checkNotBit())
        self.cFile.openBrace()
        self.cFile.appendLine(var.setBit())
        self.cFile.appendLine(var.incrementSize())
        self.cFile.closeBrace()
        
        self.cFile.closeBrace()
        

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
        return "Log_{fn}{name}".format(name=self.name.capitalize(), fn=fnName.capitalize())
        
    #get a prototype for a function of a given name
    def getFunctionPrototype(self, fname):
        s  = 'void '
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
        s  = 'log->size += sizeof({data}); //Increment the size counter'.format(data=self.format)
        return s
        
    #set the 'size' field to zero
    def clearSize(self):
        return 'log->size = 0; //Clear the size counter'

        
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
        
    lf = LogHeaderFile(variables, prefix, version)
    
    lf.saveFiles()

close("Complete!")