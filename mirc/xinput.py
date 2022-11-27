#!/usr/bin/python3

from pycrt import *
from time import sleep

import os
import sys
import termios
import atexit
from select import select

cs_numbers = " 1234567890"
cs_phone = " 1234567890#+-/"
cs_upper = " QWERTYUIOPASDFGHJKLZXCVBNM"
cs_lower = " qwertyuiopasdfghjklzxcvbnm"
cs_symbols = " ~-=!@#$%^&*()_+[]}{;:'\"\|,<.>/?"
cs_printable = cs_lower+cs_upper+cs_symbols+cs_numbers
cs_email = cs_numbers+cs_lower+cs_upper+"@."
cs_email = cs_email.replace(" ", "")
cs_www = cs_numbers+cs_upper+cs_lower+"/-.:"

KBENTER = chr(10)
KBBACK = chr(8)
KBTAB = chr(9)
KBESC = chr(27)
KBCTRLA = chr(1)
KBCTRLW = chr(23)
KBCTRLN = chr(14)

KBF1 = 'OP'
KBF2 = 'OQ'
KBF3 = 'OR'
KBF4 = 'OS'
KBF5 = '[15'
KBF6 = '[17'
KBF7 = '[18'
KBF8 = '[19'
KBF9 = '[20'
KBF10 = '[21'


KBPAGE_UP = '[V'
KBPAGE_DOWN = '[U'
KBHOME = '[H'
KBEND = '[K'
KBINSERT = '[@'
KBDEL = chr(127)

KBUP = '[A'
KBDOWN = '[B'
KBLEFT = '[D'
KBRIGHT = '[C'

#EXAMPLE!!!!
'''
kb = KBHit()

    print('Hit any key, or ESC to exit')
    a = 0
    while True:
        gotoxy(5,5)
        print(a)
        a+=1
        if a>1000: a=0
        if kb.kbhit():
            c = kb.getch()
            print(c+'..........................................................')
            if ord(c) == 27: # ESC
                break
    kb.set_normal_term()
'''

def stripmci (strn):
  pos = strn.find("|")
  while pos != -1:
    strn = strn[:pos] + strn[pos+3:]
    pos = strn.find("|")
  return strn        
  
def mcilen(text):
  return len(stripmci(text))
  
def lpad(s,w,char):
  d = w + len(s) - mcilen(s)
  return str(s)[:d].ljust(d,char)

class KBHit():

  def __init__(self):
    # Save the terminal settings
    self.fd = sys.stdin.fileno()
    self.new_term = termios.tcgetattr(self.fd)
    self.old_term = termios.tcgetattr(self.fd)

    # New terminal setting unbuffered
    self.new_term[3] = (self.new_term[3] & ~termios.ICANON & ~termios.ECHO)
    termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.new_term)

    # Support normal-terminal reset at exit
    atexit.register(self.set_normal_term)


  def set_normal_term(self):
    ''' Resets to normal terminal.  On Windows this is a no-op.
    '''
    termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.old_term)


  def getch(self):
    ''' Returns a keyboard character after kbhit() has been called.
        Should not be called in the same program as getarrow().
    '''
    return sys.stdin.buffer.raw.read(4).decode(sys.stdin.encoding)
    #return sys.stdin.read(3)


  def getarrow(self):
    ''' Returns an arrow-key code after kbhit() has been called. Codes are
    0 : up
    1 : right
    2 : down
    3 : left
    Should not be called in the same program as getch().
    '''

    
    c = sys.stdin.read(3)[2]
    vals = [65, 67, 66, 68]

    return vals.index(ord(c.decode('utf-8')))


  def kbhit(self):
    dr,dw,de = select([sys.stdin], [], [], 0)
    return dr != []


class inputxy():
  #position = 0 to Width-1
  #index = 0 - ...
  
  def __init__(self):
    self.text = ''
    self.attr = 15+16
    self.fillattr = 7+16
    self.overwriteattr = 14+4*16
    self.maxwidthattr = 14+5*16
    self.x = 1
    self.y = 1
    
    self.ext = False
    self.ch = chr(0)
    self.disable = False
    
    self.kb = KBHit()
    
    self.preview = False
    self.previewx = 1
    self.previewy = 1
    
    self.suggestions = []
    self.suggest_string = ''
    self.suggest_show = True
    self.suggest_pos = (1,24,8,68,' ','left') #x,y,att,width,fill_char,align
    self.suggest_minimum_text = 3
    self.disable_suggest = False
    
    self.redraw = False
    self.position = 0
    self.index = 0
    self.width = 10
    self.maxwidth = 180
    self.fillchar = chr(176)
    self.changed = False
    self.tab = '  '
    self.insert = True
    self.leftwrapchar = '<'
    self.rightwrapchar = '>'
    self.wrapattr = 14+2*16
    self.delimeters = [' ',',',';','!',':','|']
    self.onmaxwidth = None
    self.onoverwrite = None
    self.onenter = None
    self.onkey = None
    self.ontab = None
    self.oncancel = None
    self.onextotherkey = None
    
  def __del__(self):
    self.kb.set_normal_term()
    self.suggestions.clear()
     
  def writexy(self,xi,yi,at,st):
    gotoxy(xi,yi)
    textcolor(at)
    write(st)
    
  def show(self):
    start = self.index
    end = start + self.width
    
    self.writexy(self.x,self.y,self.fillattr,self.fillchar*self.width)
    if self.insert:
      self.writexy(self.x,self.y,self.attr,self.text[start:end])
    else:
      self.writexy(self.x,self.y,self.overwriteattr,self.text[start:end])
    if self.maxwidth==len(self.text):
      self.writexy(self.x,self.y,self.maxwidthattr,self.text[start:end])
    if self.index>0:
      self.writexy(self.x,self.y,self.wrapattr,self.leftwrapchar)
    if self.index+self.width<len(self.text):
      self.writexy(self.x+self.width-1,self.y,self.wrapattr,self.rightwrapchar)
    
    if self.preview:
      gotoxy(self.previewx,self.previewy)
      textcolor(self.attr)
      write(self.text[start:end])
    
    gotoxy(self.x+self.position,self.y)
    #self.debug()
  
  def tabkey(self):
    if self.maxwidth==len(self.text):
      if self.onmaxwidth:
        self.onmaxwidth
      return
    
    strpos = self.index+self.position
    if strpos == len(self.text):
      self.text += self.tab
      if self.position >= self.width-len(self.tab):
        self.index += len(self.tab)
      else:
        self.position += len(self.tab)
    else:
      if self.insert:
        tmp1 = self.text[:strpos]
        tmp2 = self.text[strpos:]
        self.text = tmp1+self.tab+tmp2
        if self.position >= self.width-len(self.tab):
          self.index += len(self.tab)
        else:
          self.position += len(self.tab)
    if self.onkey:
      self.onkey(self.text,chr(9))
  
  def backkey(self):
    if len(self.text)==0: return
    strpos = self.index+self.position
    if strpos == 0:return
    
    if strpos == len(self.text):
      self.text = self.text[:-1]
      if self.index>0: 
        self.index-=1
      else:
        self.position-=1
    else:
      tmp1 = self.text[:strpos-1]
      tmp2 = self.text[strpos:]
      
      self.text = tmp1+tmp2
      self.position -= 1
      if self.position<0:
        self.position = 0
        self.index -= 1
        if self.index<0: 
          self.index = 0
    if self.onkey:
      self.onkey(self.text,chr(8))
          
  def display_suggestions(self):
    if not self.suggest_show: return
    if self.disable_suggest: return
    
    st = ''
    self.suggest_string = ''
    strpos = self.index+self.position
    while True:
      if strpos<0: break
      if self.text[strpos-1:strpos] in self.delimeters:
        break
      else:
        st = self.text[strpos-1:strpos] + st
      strpos-=1
    #writexy(1,1,12,st)    
    if st and len(st)>=self.suggest_minimum_text:
      st = st.lower()
      for word in self.suggestions:
        if word.find(st)>=0:
          self.suggest_string += word+' '
          if len(self.suggest_string)>self.suggest_pos[3]:
            self.suggest_string = self.suggest_string[:self.suggest_pos[3]-3]+'...'
            break
    if self.suggest_string:
      writexylist(self.suggest_pos,self.suggest_string)
    else:
      writexylist(self.suggest_pos,'')
      self.suggest_string = ''
    gotoxy(self.x+self.position,self.y)
  
  def accept_suggest(self):
    if self.suggest_string:
      self.backword()
      self.text += self.suggest_string.split()[0]
      self.endkey()
    
    
  def backword(self):
    while True:
      strpos = self.index+self.position
      if strpos == 0: return
      self.backkey()
      '''
      if self.position >0:
        self.position-=1
      else:
        self.index-=1
        '''
      strpos = self.index+self.position
      if self.text[strpos-1:strpos] in self.delimeters:
        break
    if self.onkey:
      self.onkey(self.text,chr(23))
    
    
  def delkey(self):
    if len(self.text)==0: return
    strpos = self.index+self.position
    if strpos == len(self.text): return
    
    tmp1 = self.text[:strpos]
    tmp2 = self.text[strpos+1:]
           
    self.text = tmp1+tmp2
    if self.onkey:
      self.onkey(self.text,chr(83))
    
  def leftkey(self):
    self.position -= 1
    if self.position<0:
      self.index -= 1
      self.position = 0
    if self.index<0:
      self.index = 0
    
  def rightkey(self):
    if self.position == self.width-1:
      self.index += 1
      if self.index+self.position>len(self.text):
        self.position = self.width-1
        self.index = len(self.text)-self.width+1
    else:
      self.position +=1
    
  def homekey(self):
    if len(self.text)==0: return
    self.index = 0
    self.position = 0
  
  def clearkey(self):
    self.text = ''
    self.position = 0
    self.index = 0

  def endkey(self):
    a = len(self.text)

    if a==0:
      return
    elif a<=self.width:
      self.position = len(self.text)
      self.index = 0
    elif a>self.width:
      self.position = self.width-1
      self.index = a-self.width+1

  def debug(self):
    self.writexy(1,1,13,'pos:'+str(self.position)+';index:'+str(self.index)+';width:'+str(self.width)+';width:'+str(len(self.text)))
    
  def addchar(self,ch):
    if self.maxwidth==len(self.text):
      if self.onmaxwidth:
        self.onmaxwidth
      return

    strpos = self.index+self.position
    if strpos == len(self.text):
      self.text += ch
      if self.position == self.width-1:
        self.index += 1
      else:
        self.position += 1
    else:
      if self.insert:
        tmp1 = self.text[:strpos]
        tmp2 = self.text[strpos:]
        self.text = tmp1+ch+tmp2
        if self.position==self.width-1:
          self.index+=1
        else:
          self.position+=1
      else:
        tmp1 = self.text[:strpos]
        
        tmp2 = self.text[strpos+1:]
        self.text = tmp1+ch+tmp2
        if self.position==self.width-1:
          self.index+=1
        else:
          self.position+=1
    if self.onkey:
      self.onkey(self.text,ch)
  
  def downkey(self):
    if self.index+self.position == self.width-1: return

    while True:
      strpos = self.index+self.position
      if strpos>=len(self.text): break
      
      if self.position == self.width-1:
        self.index+=1
      else:
        self.position+=1
      if self.text[strpos:strpos+1] in self.delimeters:
        break
  
  def upkey(self):
    while True:
      strpos = self.index+self.position
      if strpos ==0: return
      
      if self.position >0:
        self.position-=1
      else:
        self.index-=1
      strpos = self.index+self.position
      if self.text[strpos-1:strpos] in self.delimeters:
        break
          
  def getstrxy(self,xi,yi,default):
    self.x = xi
    self.y = yi
    self.index = 0
    if default!='':
      self.text = default
      
    if len(self.text)>self.width:
      self.position=self.width-1
      self.index = len(self.text)-self.width+1
    else:
      self.position = len(default)
    self.show()
    while True:
      ch,ext = getkey()
      if ext:
        if ch == chr(71): #home
          self.homekey()
        elif ch == chr(72): #up
          self.upkey()
        elif ch == chr(79): #end
          self.endkey()
        elif ch == chr(75): #left
          self.leftkey()
        elif ch == chr(77): #right
          self.rightkey()
        elif ch == chr(80): #down
          self.downkey()
        elif ch == chr(82): #insert
          self.insert = not self.insert
          if self.insert == False:
            if self.onoverwrite:
              self.onoverwrite(self.text)
        elif ch == chr(83): #del
          self.delkey()
        else:
          if self.onextotherkey:
            self.onextotherkey(ch)
        self.show()
      else:
        if ch == chr(13): # enter
          break
        elif ch == chr(14): # CTRL+N, clear text
          self.clearkey()
        elif ch == chr(23): # CTRL-W, clear previous word
          self.backword()
        elif ch == chr(27): # escape
          self.text = default
          if self.oncancel:
            self.oncancel(self.text)
          break
        elif ch == chr(9): #tab
          self.tabkey()
        elif ch == chr(8): #backspace
          self.backkey()
        else:
          self.addchar(ch)
        self.show()
      #sleep(0.05)
  
  def getstrxy_nonblock(self):
    '''
    self.x = xi
    self.y = yi
    self.index = 0
    if default!='':
      self.text = default
    
    if len(self.text)>self.width:
      self.position=self.width-1
      self.index = len(self.text)-self.width+1
    else:
      self.position = len(self.text)
    '''
    #if self.disable: return
    
    if self.redraw: 
      self.show()
      self.display_suggestions()
      self.redraw = False
    
    if self.kb.kbhit():
      self.ch = self.kb.getch()
      #self.writexy(70,10,14,str(self.ch))
      '''
      if self.ch == chr(27) and len(self.ch)>1:
        self.ext = True
        self.ch = self.kb.getch()
        writexy(70,11,14,str(self.ch))
      '''
    #ch,ext = getkey()
      self.redraw = True
      if len(self.ch)>1:
        self.ch = self.ch[1:]
        #writexy(60,11,14,str(self.ch)+'/'+str(len(self.ch)))
        #writexy(60,12,13,str2hex(self.ch).ljust(12,' '))
        
        if self.ch == KBHOME: #home
          self.homekey()
        elif self.ch == KBUP: #up
          self.upkey()
        elif self.ch == KBEND: #end
          self.endkey()
        elif self.ch == KBLEFT: #left
          self.leftkey()
        elif self.ch == KBRIGHT: #right
          self.rightkey()
        elif self.ch == KBDOWN: #down
          self.downkey()
        elif self.ch == KBINSERT: #insert
          self.insert = not self.insert
          if self.insert == False:
            if self.onoverwrite:
              self.onoverwrite(self.text)
        #elif self.ch == KBDEL: #del
        #  self.delkey()
        else:
          if self.onextotherkey:
            self.onextotherkey(self.ch)
        
        self.ext = False
      else:
        #writexy(1,1,14,str(self.ch))
        #writexy(70,11,14,str(ord(self.ch)).zfill(3))
        if self.ch == KBENTER: # enter
          if self.onenter: self.onenter()
        elif self.ch == KBCTRLN: # CTRL+N, clear text
          self.clearkey()
        elif self.ch == KBDEL: #del
          self.delkey()
        elif self.ch == KBCTRLA: # CTRL+A, Accept first suggestion
          self.accept_suggest()
        elif self.ch == KBCTRLW: # CTRL-W, clear previous word
          self.backword()
        elif self.ch == KBESC: # escape
          self.text = ''
          self.position = 0
          self.index = 0
          if self.oncancel:
            self.oncancel(self.text)
        elif self.ch == KBTAB: #tab
          if self.ontab: self.ontab()
          #self.tabkey()
        elif self.ch == KBBACK: #backspace
          self.backkey()
        else:
          if not self.disable: 
            self.addchar(self.ch)
        self.ch = chr(0)
    sleep(0.01)
              

def lightbarmenu(items,sel=0):
  res = ""
  kbrd = KBHit()
  while True:
    for i in range(len(items)):
      writexypipe(items[i]['x'],items[i]['y'],items[i]['low'],mcilen(items[i]['textlow']),items[i]['textlow'])
    writexypipe(items[sel]['x'],items[sel]['y'],items[sel]['high'],mcilen(items[sel]['texthigh']),items[sel]['texthigh'])
    
    ans = kbrd.getch()
    if len(ans)>1:
      ans = ans[1:]
      if ans == KBUP or ans == KBLEFT:
        sel -= 1
        if sel < 0: sel = len(items) - 1
      elif ans == KBDOWN or ans == KBRIGHT:
        sel += 1
        if sel > len(items) - 1 : sel = 0
    else:
      if ans == KBESC:
        res == "#esc"
        break
      elif ans == KBENTER:
        res = items[sel]['code']
        break
      else:
        for i in range(len(items)):
          if ans in items[i]['key']:
            res = items[i]['code']
            return res
  return res

def simpleinput(x,y,att,fillatt,chars,length,maxc,fc,default):
    """
    Simple function to get an input from user
    att    : fg color
    fillatt: bg color
    chars  : string with valid characters.
    length : length for the input box
    maxc   : maximum size for the string to be entered
    fc     : fill character for the bg
    default: default value
    """
    pos = 0
    res = default
    key = ""
    kbrd = KBHit()
    while key != KBENTER:
        writexy(x,y,fillatt,fc*length)
        writexy(x,y,att,res[pos:length+pos])
        #writexy(x,y,att,res)
        #gotoxy(x+len(res[pos:length+pos]),y)
        key = kbrd.getch()
        if len(key)>1:
            key = key[1:]
        if key in chars:
            res = res + key
            if len(res)>length:
                if len(res)<maxc:
                    pos += 1
        elif key == ' ':
            res = res + " "
            if len(res)>length:
                if len(res)<maxc:
                    pos += 1
        elif key == KBBACK:
            res = res[:-1]
            pos = pos - 1
            if pos < 0:
                pos = 0
        elif key == KBCTRLN:
            res = ""
        elif key == KBENTER:
            break
        elif key == KBESC:
            res = ''
            break
    writexy(x,y,fillatt,fc*length)
    writexy(x,y,fillatt,res[:length])
    return res
    
class mform:
  items = []
  cl_normal = 7
  cl_high = 14+3*16
  cl_edit_normal = 7
  cl_edit_high = 15+16
  cl_editing = 14+1*16
  cl_key_norm = 15
  cl_key_high = 11+16
  results = {}
  index = 0
  changed = False
  ch_pass = '$'
  
  '''
  type of input string
  --------------------
  1	Standard input.	All characters allowed.
  2	Upper case input.	Allows all characters, but will convert any lower case letters into upper case.
  3	Proper input.	Allows all characters, but will convert the first letter in each word to an upper case letter.
  4	Phone input.	Allows only numbers and will pre-format them using the USA-style phone numbers. IE: XXX-XXX-XXXX. Note that the length of this input should always be 12, as that is the length of the USA phone number format.
  5	Date input.	Allows only numbers and will pre-format them using the date format (ie XX/XX/XX) that is currently selected by the user. NOTE: The date input will always return the date in the MM/DD/YY format, regardless of what format the user has selected. For example, if the user has selected the DD/MM/YY format, Input will expect the user to enter the date in that format, but will then convert it to MM/DD/YY when it returns the date back to the MPE program.
  6	Password input.	Allows all characters, but will convert any lower case letters into upper case. The character that is typed is NOT echoed to the screen. Instead, it is replaced by the * character so that what they have entered will not be shown on the screen.
  7	Lower case input.	Allows all characters, but will convert any lower case letters into upper case.
  8	User Defined.	User name format from sys config
  9	Standard Input w/o CRLF	Will not append CRLF to input
  10	Numeric Input.
  
  11 : List value picker. You have to set the fields variable. This option will
       display the values from the list and every time the user presses enter
       the value changes.
  
  '''
  
  
  def __init__(self):
    self.kb = KBHit()
    pass
    
  def additem(self, typeof,tx,ty,tw,title,vx,vy,vw,vmax,value,key,code,fields=[]):
    item = {}
    item['titlex']=tx
    item['titley']=ty
    item['title_width']=tw
    item['title']=title
    item['valuex']=vx
    item['valuey']=vy
    item['value_width']=vw
    item['value_max']=vmax
    item['value']=value
    item['key']=key
    if typeof == 11:
      item['value']=value
      item['code']=code
    else:
      item['code']=code
    item['type']=typeof
    item['fields']=fields
    if typeof == 11:
      item['findex']=fields.index(value)
    else:
      item['findex']=0
    self.items.append(item)
    if typeof==11:
      self.results[code] = fields[item['findex']]
    else:
      self.results[code] = value

  def stripmci (self,strn):
    pos = strn.find("|")
    while pos != -1:
      strn = strn[:pos] + strn[pos+3:]
      pos = strn.find("|")
    return strn        
  
  def mcilen(self,text):
    return len(self.stripmci(text))
  
  def lpad(self,s,w,char):
    d = w + len(s) - self.mcilen(s)
    return str(s)[:d].ljust(d,char)
    
  def drawitem_norm(self,item):
    writexy(item['titlex'],item['titley'],self.cl_normal,self.lpad(item['title'],item['title_width'],' '))
    if item['type']==6:
      writexy(item['valuex'],item['valuey'],self.cl_edit_normal,self.lpad('',item['value_width'],self.ch_pass))
    #elif item['type'] == 11:
     # writexy(item['valuex'],item['valuey'],self.cl_edit_normal,self.lpad(self.results[item['value']],item['value_width'],' '))
    else:
      writexy(item['valuex'],item['valuey'],self.cl_edit_normal,self.lpad(self.results[item['code']],item['value_width'],' '))
    i = item['title'].find(item['key'])
    writexy(item['titlex']+i,item['titley'],self.cl_key_norm,item['key'])
    
  def drawitem_high(self,item):
    writexy(item['titlex'],item['titley'],self.cl_high,self.lpad(item['title'],item['title_width'],' '))
    if item['type']==6:
      writexy(item['valuex'],item['valuey'],self.cl_edit_high,self.lpad('',item['value_width'],self.ch_pass))
    else:
      writexy(item['valuex'],item['valuey'],self.cl_edit_high,self.lpad(self.results[item['code']],item['value_width'],' '))
    i = item['title'].find(item['key'])
    writexy(item['titlex']+i,item['titley'],self.cl_key_high,item['key'])
  
  def drawall(self):
    for item in self.items:
      self.drawitem_norm(item)
      
  def getinput(self,index):
    textcolor(self.cl_editing)
    writexy(self.items[index]['valuex'],self.items[index]['valuey'],self.cl_editing,' '*self.items[index]['value_width'])
    if self.items[index]['type']==11:
      self.items[index]['findex']+=1
      if self.items[index]['findex'] > len(self.items[index]['fields'])-1:
        self.items[index]['findex']=0
      r = self.items[index]['fields'][self.items[index]['findex']]
      self.items[index]['value']=r
    else:
      #r = getstr(self.items[index]['type'],self.items[index]['value_width'],self.items[index]['value_max'],self.results[self.items[self.index]['code']])
      #(x,y,att,fillatt,chars,length,maxc,fc,default):
      r = simpleinput(self.items[index]['valuex'],self.items[index]['valuey'],self.cl_editing,1,cs_printable,self.items[index]['value_width'],self.items[index]['value_max'],"░",'')
      
      if not r: r = ''
    if r!=self.results[self.items[self.index]['code']]: self.changed = True
    self.results[self.items[index]['code']] = r
    
              
  def show(self):
    done = False
    while not done:
      self.drawitem_high(self.items[self.index])
      
      key = self.kb.getch()
      
      if len(key)>1:
        key = key[1:]
        self.drawitem_norm(self.items[self.index])
        if key == KBUP or key == KBLEFT: #up or left
          self.index -= 1
          if self.index<0:
            self.index = len(self.items)-1
        elif key == KBDOWN or key == KBRIGHT: #down or right
          self.index += 1
          if self.index == len(self.items):
            self.index = 0
        elif key == KBEND: #end
          self.index = len(self.items)-1
        elif key == KBHOME: #home
          self.index = 0
        self.drawitem_high(self.items[self.index])
      else:
        if key == KBESC: #esc
          done = True
        elif key == KBENTER: #enter
          self.getinput(self.index)
          self.drawitem_high(self.items[self.index])
        else:
          for i in range(len(self.items)):
            if key.upper() == self.items[i]['key']:
              self.drawitem_norm(self.items[self.index])
              self.index = i
              self.drawitem_high(self.items[self.index])
              break
              
def getyesno(x,y,trueat,falseat,offat,default):
    """
    Function to get a Yes/No answer
    trueat  : color in byte value for the No button
    falseat : color in byte value for the Yes button
    default : True/False to begin with 
    """
    key = ""
    val = {0:'No ',1:'Yes'}
    res = default
    kbrd = KBHit()
    while key != KBENTER:
      writexy(x,y,offat,val[True]+val[False])
      if res == True:
        writexy(x,y,trueat,val[res])
      else:
        writexy(x+3,y,falseat,val[res])
      gotoxy(1,25)
      key = kbrd.getch()
      if len(key)>1:
        key = key[1:]
        if key == KBLEFT or key == KBRIGHT:
          res = not res
      else:
        if key == ' ': res = not res
    return val[res].lower().strip(" ")              

class mlist:
  x=1
  y=1
  w=10
  h=5
  done = False
  sort = False
  reverse = False
  sort_field = 'text'
  total = 0
  items = None
  top = 0
  selbar = 0
  cl_normal = 7
  cl_high   = 14 + 3*16
  cl_key_norm = 15 + 16
  cl_key_high = 11 + 3*16
  exitkeys = KBTAB
  exitcode = ''
  itemcode = ''
  scrollbar = {"enable":True,"hichar":'▓',"lochar":'│',"hiatt":7,"loatt":8}
  otherkeys = None
  search_show = True
  search = ''
  searchx = x
  searchy = y+1
  searchw = w
  search_at= 8
  search_fmt = ': %s'
  
  onbaron = None
  onbaroff = None
  
  def __init__(self):
    self.exitkeys=''    
    self.items = []
    self.kb = KBHit()
    
  def additem(self,itm):
    self.items.append(itm)
    self.total = len(self.items)
    if self.sort:
      self.items = sorted(self.items, key = lambda i: (i[self.sort_field]),reverse=self.reverse)
  
  def updatebar(self):
    if self.scrollbar["enable"] == False: return
    for i in range(self.h):
      writexy(self.x+self.w-1,self.y+i,self.scrollbar["loatt"],self.scrollbar["lochar"])
    if len(self.items) < 2:
      fz = 0
    else:
      fz = ((self.top+self.selbar)*self.h) // (len(self.items)-1)
    if fz>self.h-1: fz = self.h-1
    writexy(self.x+self.w-1,self.y+fz,self.scrollbar["hiatt"],self.scrollbar["hichar"])
    
  def draw(self):
    if len(self.items)==0: return
    yy=0
    while yy<self.h:
      if self.top+yy<len(self.items):
        writexy(self.x,self.y+yy,self.cl_normal,lpad(self.items[self.top+yy]['text'],self.w,' '))
      else:
        writexy(self.x,self.y+yy,self.cl_normal,' '*self.w)
      yy+=1
        
  def bar_on(self):
    if len(self.items)==0: return
    writexy(self.x,self.y+self.selbar,self.cl_high,lpad(self.items[self.top+self.selbar]['text'],self.w,' '))
    if self.onbaron:
      self.onbaron(self.items[self.top+self.selbar])
  
  def bar_off(self):
    if len(self.items)==0: return
    writexy(self.x,self.y+self.selbar,self.cl_normal,lpad(self.items[self.top+self.selbar]['text'],self.w,' '))
    if self.onbaroff:
      self.onbaroff(self.items[self.top+self.selbar])
  
  def sortlist(self):
    self.items = sorted(self.items, key = lambda i: (i['order'],i[self.sort_field]),reverse=self.reverse)
  
  def clear(self):
    del self.items[:]
    self.total=0  
    self.top=0
    self.selbar=0
    
  def dosearch(self):
    if len(self.items)<=0: return
    i = 1
    while i+self.top+self.selbar<len(self.items):
      if self.search.upper() in self.items[i+self.top+self.selbar]['text'].upper():
        self.top = i+self.top+self.selbar
        self.selbar = 0
        self.draw()
        self.bar_on()
        break
      i+=1 
  
  def show(self):
    self.done = False    
    res = None 
    
    self.draw()
    self.bar_on()
    
    while not self.done:
      self.updatebar()
      if self.search_show:
        writexy(self.searchx,self.searchy,self.search_at,lpad(self.search_fmt % self.search,self.searchw,' '))
      key = self.kb.getch()
      if len(key)>1:
        key = key[1:]
        if key == KBHOME:
          self.top = 0
          self.selbar = 0
          self.draw()
          self.bar_on()
        elif key == KBLEFT: 
          self.exitcode = '#left'
          if len(self.items)>0:
            res = self.items[self.top+self.selbar]
          else:
            res = None
          self.done = True
        elif key == KBRIGHT: 
          self.exitcode = '#right'
          if len(self.items)>0:
            res = self.items[self.top+self.selbar]
          else:
            res = None
          self.done = True
        elif key == KBEND:
          self.top = ((len(self.items)) // self.h)*self.h
          self.selbar = len(self.items)-self.top-1
          if self.top == len(self.items):
            self.top = len(self.items)-self.h
            self.selbar = self.h-1
          self.draw()
          self.bar_on()
        elif key == KBDOWN:
          if self.selbar + self.top < len(self.items)-1:
            if self.selbar == self.h-1:
              self.top += self.h
              self.selbar = 0
              self.draw()
              self.bar_on()
            else:
              self.bar_off()
              self.selbar += 1
              self.bar_on()
        elif key == KBUP:
          if self.top+self.selbar>0:
            if self.selbar == 0:
              self.top -= self.h 
              self.selbar = self.h-1
              self.draw()
              self.bar_on()
            else:
              self.bar_off()
              self.selbar -= 1
              self.bar_on()
        elif key == KBPAGE_DOWN:
          if self.selbar + self.top + self.h < len(self.items):
            self.top += self.h
          else:
            self.top = ((len(self.items)) // self.h)*self.h
            self.selbar = len(self.items)-self.top-1
            if self.top == len(self.items):
              self.top = len(self.items)-self.h
              self.selbar = self.h-1
          self.draw()
          self.bar_on()
        elif key == KBPAGE_UP:
          if self.selbar + self.top - self.h > 0:
            self.top -= self.h
          else:
            self.top = 0
            self.selbar = 0
          self.draw()
          self.bar_on()
        elif key in self.exitkeys:
          self.exitcode = key
          if len(self.items)>0:
            res = self.items[self.top+self.selbar]
          else:
            res = None
          self.done = True
        else:
          if self.otherkeys:
            self.otherkeys(True,key)
            if len(self.items)>0:
              res = self.items[self.top+self.selbar]
            else:
              res = None
      else:
        if key == KBESC or key == KBTAB: 
          self.exitcode = '#esc'
          self.done = True
        elif key == KBCTRLN and self.search_show: #search next
          if len(self.search)>0:
            self.dosearch()
        elif key == KBBACK:
          if len(self.search)>0:
            self.search = self.search[:-1]
        elif key == KBENTER:
          self.exitcode = '#enter'
          if len(self.items)>0:
            res = self.items[self.top+self.selbar]
          else:
            res = None
          self.done = True
        elif key in self.exitkeys:
          self.exitcode = key
          if len(self.items)>0:
            res = self.items[self.top+self.selbar]
          else:
            res = None
          self.done = True
        elif ord(key)>32 and ord(key)<126 and self.search_show:
          self.search += key
          self.dosearch()
        else:
          if self.otherkeys:
            self.otherkeys(False,key)
            if len(self.items)>0:
              res = self.items[self.top+self.selbar]
            else:
              res = None
    return res

def preview(txt,key):
  gotoxy(1,1)
  textcolor(14)
  write(txt.ljust(78,' '))
  
  
  

#init()
#gi = inputxy()
#gi.maxwidth = 255
#gi.width = 79
#gi.onkey = preview
#gi.preview = False
#getstring = gi.getstrxy(20,10,'hello')

#getstring = gi.getstrxy(1,24,'hello there mother fucker')
#write('\r'+gi.text)
