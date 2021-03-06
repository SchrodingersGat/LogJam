CPP = "__cplusplus"

#class for simplifying generation of code
class CodeWriter:
    def __init__(self, fname):
        self.fname = fname
        
        self.clear()
        
    #increment the tab position
    def tabIn(self):
        self.tabs += 1
        
    #decrement the tab position
    def tabOut(self):
        if self.tabs > 0:
            self.tabs -= 1
            
    #append raw text
    def append(self, text, ignoreTabs=False):
        self.text = self.text + '\t' * (0 if ignoreTabs else self.tabs)
        self.text += text
        
    #append a line (enforce newline chracter)
    def appendLine(self, text=None, comment=None, ignoreTabs=False):
        if self.comment:
            self.text += '* '
        if text:
            self.append(text,ignoreTabs)
        if comment:
            if text:
                ignoreTabs=True
                self.append(' ',ignoreTabs) #add a space after the text
            self.append('//' + comment,ignoreTabs)
            
        self.append('\n',ignoreTabs=True)
            
    #create a c-style enum
    def createEnum(self, name, enums, start=0, values=None, split=None, commentFunc=None):
        
        self.appendLine(comment='{name} enumeration'.format(name=name))
        self.appendLine('typedef enum')
        self.openBrace()
        
        for i,enum in enumerate(enums):
            #values should be a dict of enum/value pairs
            if values and enum in values.keys():
                eVal = values[enum]
            elif i == 0:
                eVal = start
            else:
                eVal = None
                
            self.append('{enum}{value},'.format(enum=enum,value=' = {val}'.format(val=eVal) if eVal is not None else ''))
            
            if commentFunc:
                self.appendLine('\t',comment=commentFunc(i,enum), ignoreTabs=True)
            else:
                self.appendLine()
            
            if i > 0 and type(split) is int:
                if (i+1) % split == 0:
                    self.appendLine()
            
        self.tabOut()
        self.appendLine('}} {name};'.format(name=name))
        self.appendLine()
    
    #add a c-style include line
    def include(self, file,comment=None):
        
        self.append("#include ")
        self.append(file)
            
        if comment:
            self.append(" //")
            self.append(comment)
        
        #line-return
        self.appendLine()
        
    #add a c-style define string
    def define(self, name, value=None, comment=None):
        
        self.append('#define ')
        self.append(name)
        if value:
            self.append(' ' + str(value))
        if comment:
            self.append(" //")
            self.append(str(comment))
            
        self.appendLine()
    
    #write an open-brace and tab in
    def openBrace(self):
        self.appendLine('{')
        self.tabIn()
    
    #tab-out and write the close-brace
    def closeBrace(self, newline=True):
        self.tabOut()
        self.append('}}{newline}'.format(newline='\n' if newline else ''))
        
    #start a bulk comment
    def startComment(self):
        self.appendLine("/*")
        self.comment = True
        
    #finish a bulk comment
    def finishComment(self):
        self.comment = False
        self.appendLine("*/")
        
    #start a switch (case) statement
    def startSwitch(self, switch):
        self.switch.append(switch)
        self.appendLine('switch ({sw})'.format(sw=switch))
        self.openBrace()
        
    #end a switch statement, and demark end of switch
    def endSwitch(self):
        self.tabOut()
        self.append('}')
        if len(self.switch) > 0:
            self.appendLine(comment=' ~switch ({sw})'.format(sw=self.switch.pop()))
        self.appendLine()
        
    #add a new case to a switch statement
    def addCase(self, case):
        if case.lower() == 'default':
            self.appendLine('default:')
        else:
            self.appendLine('case {case}:'.format(case=case))
        self.tabIn()
        
    #return from a case, with the specified value
    def returnFromCase(self, value=None):
        self.appendLine('return{val};'.format(val=' '+str(value) if value else ''))
        self.tabOut()
        
    #break from case (no return value)
    def breakFromCase(self):
        self.appendLine('break;')
        self.tabOut()
        
    #start an #if(n)def block
    def startIf(self, define, invert=False, comment=None):
        self.defs.append(define)
        if comment:
            self.appendLine(comment=comment)
            
        if invert:
            self.appendLine("#ifndef " + define)
        else:
            self.appendLine('#ifdef ' + define)
        
    #end an #if(n)def block
    def endIf(self):
        self.append("#endif ")
        if len(self.defs) > 0:
            self.appendLine(comment=self.defs.pop())
        self.appendLine()
        
    def externEntry(self):
        self.startIf(CPP, comment='Play nice with C++ compilers!')
        self.appendLine('extern "C" {')
        self.endIf()
        
    def externExit(self):
        self.startIf(CPP, comment='We are done playing nice with C++ compilers')
        self.appendLine('}')
        self.endIf()
        
    def writeToFile(self):
        with open(self.fname,'w') as file:
            file.write(self.text)
            
    def clear(self):
        self.text = ''
        self.tabs = 0
        self.comment = False
        self.defs = [] #def levels
        self.switch = [] #switch levels