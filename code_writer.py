CPP = "__cplusplus"

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
            
    #append raw text
    def append(self, text):
        self.text = self.text + '\t' * self.tabs
        if self.comment:
            self.text += '* '
        self.text += text
        
    #append a line (enforce newline chracter)
    def appendLine(self, text=None):
        if not text:
            self.append('\n')
        else:
            self.append(text + '\n')
    
    #appent a C-style comment line
    def appendComment(self, text=None):
        
        if not text:
            self.appendLine("//")
        else:
            self.appendLine("//" + text)
    
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
            self.append(' ' + value)
        if comment:
            self.append(" //")
            self.append(comment)
            
        self.appendLine()
    
    #write an open-brace and tab in
    def openBrace(self):
        self.appendLine('{')
        self.tabIn()
    
    #tab-out and write the close-brace
    def closeBrace(self):
        self.tabOut()
        self.appendLine('}')
        
    #start a bulk comment
    def startComment(self):
        self.appendLine("/*")
        self.comment = True
        
    def finishComment(self):
        self.comment = False
        self.appendLine("*/")
        
    #start an #ifdef block
    def startIf(self, define, invert=False, comment=None):
        self.defs.append(define)
        if comment:
            self.appendComment(comment)
            
        if invert:
            self.appendLine("#ifndef " + define)
        else:
            self.appendLine('#ifdef ' + define)
        
    def endIf(self):
        self.append("#endif ")
        if len(self.defs) > 0:
            self.appendComment(self.defs.pop())
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