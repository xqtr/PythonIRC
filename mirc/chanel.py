import datetime
import textwrap as tw
# -*- coding: CP437 -*-
# coding: CP437

def safefilenamestring(filename):
  x = "".join(c for c in filename if c.isalnum()).rstrip()
  x = x.replace('.','_')
  x = x.replace(' ','_')
  return x
  

class ircchanel():
  def __init__(self,name):
    self.name = name
    self.cid = 0
    self.timestamp = True
    self.created = 0 #time created, unix timestamp
    self.max_chat_lines = 500
    self.active = False
    self.users = []
    self.chat = []
    self.topic = ''
    self.chat_index = 0
    self.chat_top = 0
    self.chat_height = 0
    self.has_data = False
    self.save_every = 100
    self.save_index = 0
    self.save_buffer = []
    self.mode = ''
    self.modes = {}
    self.modes['t'] = False
    self.modes['n'] = False
    self.modes['s'] = False
    self.modes['i'] = False
    self.modes['p'] = False
    self.modes['m'] = False
    self.modes['b'] = False
    self.modes['k'] = False
    self.modes['l'] = False
    self.modes['key'] = ''
    self.modes['users'] = -1
    
    self.filename = safefilenamestring(name)+'.txt'
    
  def mini_mcilen(self,txt):
    i = 0
    res = 0
    while i<len(txt):
      if txt[i] == '|':
        i+=2
      else:
        i+=1
        res+=1
    return res
    
  def wraptext(self,txt, width=80,delimeters=',.!;) '):
    res = []
    if not txt: return res
    if len(txt)<=width:
      res.append(txt)
      return res      
    
    lastdel = 0
    i = 0
    text = txt
    mcil = self.mini_mcilen(text)
    while i<len(text) and mcil>width:
      if text[i] in delimeters:
        lastdel = i
      if i == width:
        res.append(text[:lastdel])
        text = text[lastdel:]
        mcil = self.mini_mcilen(text)
        i = 0
        lastdel = 0
      if text[i] == '|':
        i += 2
      else:
        i += 1
    if len(text)>0:
      res.append(text)
    return res
      
    
  def mode2str(self):
    s = ''
    for key in self.modes.keys():
      if self.modes[key]:
        if key == 'k':
          s +='k '+ self.modes['key']+' '
        elif key == 'l':
          s +='l '+ str(self.modes['users'])+' '
        else:
          if key in 'tnsipmb':
            s += key
        
    return s.rstrip()
  
  
  def parsemode(self,st):
    if st[0] not in ('+','-'): return False
    i = 0
    action = False
    while i<len(st):
      if st[i] in ('+','-'):
        if st[i] == '+': 
          action = True
        else:
          action = False
      if st[i] in 'tnsipmb':
        self.modes[st[i]] = action
      elif st[i] == 'k':
        self.modes['k'] = action
        self.modes['key'] = st.split(' ')[1]
        break
      elif st[i] == 'l':
        self.modes['l'] = action
        try:
          self.modes['users'] = int(st.split(' ')[1])
        except:
          self.modes['users'] = -1
        break
      i+=1
      
  def addline(self,user,text,cwidth=80,color=7,seen=False):
    #lines = tw.wrap(text,width=cwidth)
    lines = self.wraptext(text,width=cwidth)
    for index,line in enumerate(lines):
      item = dict()
      item['text']=line
      item['seen']=seen
      item['color']=color
      item['date']=datetime.datetime.now()#.strftime("%H:%M")
      if index==0:
        item['user']=user
      else:
        item['user']='│'
      if index==len(lines)-1 and index!=0:
        item['user']='└'
      self.chat.append(item)
      if item['user'].upper() != 'CHANNEL':
        self.save_buffer.append(item)
        self.save_index += 1
      if self.save_index > self.save_every:
        self.savechat()
      
    self.chat_top = len(self.chat) - self.chat_height
    if self.chat_top < 0: self.chat_top = 0
    
    
  def savechat(self):
    with open(self.filename,'a+') as f:
      for line in self.save_buffer:
        f.write(line['date'].strftime("%Y-%m-%d / %H:%M:%S")+' | '+line['user'].ljust(13,' ')+' : '+line['text']+'\n')
    self.save_index = 0
    self.save_buffer.clear()
    if len(self.chat)>self.max_chat_lines:
      while len(self.chat)<=self.max_chat_lines:
        del self.chat[0]
    
class ircchanellist():
  
  def __init__(self):
    self.channels = list()
    self.count = 0
    self.current = 0
    self.redraw = False
    self.chat_height = 0
    
  def add(self,name):
    self.channel = ircchanel(name)
    self.count +=1
    self.channel.cid = self.count-1
    self.channel.chat_height = self.chat_height
    self.channels.append(self.channel)
    return self.channel.cid
  
  def remove(self,name):
    chan = self.channels[self.findbyname(name)]
    self.channels.remove(chan)
    self.count-=1
    
  def ischannelexist_by_name(self,name):
    found = False
    for c in self.channels:
      if c.name == name:
        found = True
        break
    return found
    
  def ischannelexist_by_id(self,cid):
    found = False
    for c in self.channels:
      if c.cid == cid:
        found = True
        break
    return found
    
  def findbyname(self,name):
    res = 0
    for c in self.channels:
      if c.name == name:
        res = c.cid
        break
    return res
    
  def getnameofactive(self):
    cid = self.findactive()
    if cid:
      return self.channels[cid].name
    else:
      return ''
      
  def setactivebyname(self,name):
    found = False
    for c in self.channels:
      if c.name == name:
        c.active = True
        self.current = c.cid
        found = True
      else:
        c.active = False
    if not found:
      self.current = 0
        
  def findactive(self):
    res = 0
    for c in self.channels:
      if c.active:
        res = c.cid
        break
    return res
        
  def changetopic(self,cid,topic):
    self.channels[cid].topic = topic
    
  def setactive(self,cid):
    res = False
    if self.ischannelexist_by_id(cid):
      self.channels[self.current].active = False
      self.channels[cid].active = True
      self.current = cid
      self.has_data = False
      res = True
    return res
    
  
