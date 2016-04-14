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
    
class LogHeaderFile:
    def __init__(self, vars, prefix, version):
        self.variables = vars
        self.prefix = prefix
        self.version = version
        
    #function for adding a variable to the struct
    def variableAdditionHeaderString(self, var):
        
        s  = "inline void "
        s += "Log_" + self.prefix + "_Add"
        s += var.name 
        s += "(" 
        s += self.prefixString()
        s += "* log, "
        s += var.format + " data)"
        
        return s
        
    def variableAdditionFunctionString(self, var):
        
        s  = self.variableAdditionHeaderString(var)
        s += "\n"
        s += "\t"
        
        #if the var bit is already set, 
    
    def headerString(self):
        header  = "#ifndef {h}\n".format(h=headerDefine(self.prefix))
        header += "#define {h}\n".format(h=headerDefine(self.prefix))

        return header
        
    def footerString(self):
        footer  = "#endif //{h}\n".format(h=headerDefine(self.prefix))
        
        return footer

    def constructCodeFile(self):
        
        #include the header file
        s = "#include " + headerFilename(self.prefix) + ".h\n"
        
        
        
        #finish with a new-line
        s += "\n"
        
        return s
       
    def constructHeaderFile(self):
    
        log_struct = LogStruct(self.variables, self.prefix, self.version)
    
        s  = self.headerString()
        s += "\n"
        
        #extern C
        s += externEntry()
        s += "\n"
        
        s += "//Bitfield struct definition for the " + self.prefix + " logging struct\n"
        s += log_struct.bitfieldString()
        s += "\n"
        s += "//Data struct definition for the " + self.prefix + " logging struct\n"
        s += log_struct.structString()
        s += "\n"
        s += "//Structure for complete definition of the " + self.prefix + " logging protocol\n"
        s += "typedef struct {\n\n"
        s += "\t//Cumulative size of the logging struct\n"
        s += "\t" + "uint16_t size;\n\n"
        s += "\t//Bitfield defining which variables are selected\n"
        s += "\t" + bitfieldStruct(self.prefix) + " selection;\n"
        s += "\n"
        s += "\t//Struct defining the actual data to be logged\n"
        s += "\t" + dataStruct(self.prefix) + " data;\n"
        s += "\n"
        s += "} "
        s += topLevelStruct(self.prefix) + ";\n"
        s += "\n"
        
        #extern C
        s += externExit()
        s += "\n"
        
        s += self.footerString()
        
        return s
    
    def saveFiles(self, output_dir = None):
        
        filename = headerFilename(self.prefix)
        
        if output_dir:
            filename = os.path.join(output_dir, filename)
            
        with open(filename + ".h",'w') as f:
            f.write(self.constructHeaderFile())
        
        with open(filename + '.c','w') as f:
            f.write(self.constructCodeFile())
            

class LogStruct:
    def __init__(self, vars, prefix, version):
        self.variables = vars
        self.prefix = prefix
        self.version = version
        
    #create the struct of the variables
    def structString(self):
        s  = "typedef struct {\n"
        
        for v in self.variables:
            s += "\t"
            s += v.dataString()
            s += "\n"
            
        s += "} "
        s += dataStruct(self.prefix)
        s += ";\n"
        
        return s
        
    #create a bitfield struct of all variables
    def bitfieldString(self):
        s  = "typedef struct {\n"
        
        for v in self.variables:
            s += "\t"
            s += v.bitfieldString()
            s += "\n"
            
        s += "} "
        s += bitfieldStruct(self.prefix)
        s += ";\n"
        
        return s

class LogVariable:
    def __init__(self, name, format, comment):
        self.prefix = name
        self.format = self.parseFormat(format)
        self.comment = "//!< " + str(comment) if comment else ""
        
    def parseFormat(self, format):
        format = format.replace("unsigned","uint")
        format = format.replace("signed","int")
        if not format.endswith("_t"):
            format = format + "_t"
            
        return format
        
    def dataString(self):
        return "{datatype} {name}; {comment}".format(
                datatype = self.format,
                name = self.prefix,
                comment = self. comment)
                
    def bitfieldString(self):
        return "unsigned {name} : 1; {comment}".format(
                name = self.prefix,
                comment = self.comment)
                
    #wrap a given function name
    def getFunctionName(self, fnName):
        return "Log_{fn}{fn}".format(name=self.prefix, fn=fnName)
        
                
    #function for adding a variable to the log
    def additionHeaderString(self):
        s  = 'inline void '
        s += self.getFunctionName('Add')
        s += '('
        s += topLevelStruct(self.prefix)
        s += "* log, "
        s += self.format
        s += " data)"
        
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
            
        variables.append(LogVariable(name,datatype,comment))
        
    lf = LogHeaderFile(variables, prefix, version)
    
    lf.saveFiles()

close("Complete!")