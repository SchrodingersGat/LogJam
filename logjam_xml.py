import sys
import os

import re

from logjam import LogVariable, LogFile

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
        units = a.get('units','dimensionless')
        scaler = float(a.get('scaler',1))
        
        if not name:
            print('Name missing for', a)
            continue
        if not datatype:
            print('Type missing for', a)
            continue
            
        variables.append(LogVariable(prefix,name,datatype,comment,units=units, scaler=scaler))
        
    lf = LogFile(variables, prefix, version, outputdir=outputdir)
    
    lf.saveFiles()

close("Complete!")