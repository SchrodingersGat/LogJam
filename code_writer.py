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
    def appendCommentLine(self, text=None):
        
        if not text:
            self.appendLine("//")
        else:
            self.appendLine("//" + text)
    
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
        self.appendLine("*/")
        self.comment = False
        
    def writeToFile(self):
        with open(self.fname,'w') as file:
            file.write(self.text)
            
    def clear(self):
        self.text = ''
        self.tabs = 0
        self.comment = False