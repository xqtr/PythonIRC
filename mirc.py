#!/usr/bin/python3
# -*- coding: CP437 -*-
# coding: CP437

import sys,os
import queue
from datetime import datetime
import hashlib
import socket
import string
import threading
import time
import re

version = 'Mystic IRC v0.1'
maindir = sys.path[0]+os.sep
datadir = maindir + 'mirc'+os.sep
sys.path.append(datadir)

from irccmds import *
import xinput
from chanel import *
from pycrt import *

WIDTH, HEIGHT = (80,25)

config_background = 'bg.ans'

config_chatscreen = (1,3,79,21) #x1,y1,x2,y2
config_chatscreen_gfx_lo = (1,1)
config_chatscreen_gfx_hi = config_chatscreen_gfx_lo
config_chatscreen_normal = 7
config_chatscreen_irrelevant = 8
config_chatscreen_attention = 15+4*16
config_chatscreen_notseen = 14+6*16
config_chatscreen_error_mci = '|13'
config_chatscreen_error_att = 13
config_chatscreen_notice_mci = '|02'
config_chatscreen_notice_att = 2
config_chatscreen_hl = 14
config_chatscreen_more_up = (78,2,11+16,7+16,'<','-') #x,y,att_on,att_off,char,off_char
config_chatscreen_more_down = (79,2,11+16,7+16,'>','-') #x,y,att_on,att_off,char,off_char

config_statusbar = (1,24,8,79,' ','left')

config_nicklist = (68,4,79,20)  #x1,y1,x2,y2
config_nicks_normal = 7
config_nicklist_normal = 7
config_nicklist_gfx_lo = (67,3)
config_nicklist_gfx_hi = config_nicklist_gfx_lo 
config_topic_title = (1,2,30,79,' ','center')

config_channel_bar = (5,22)
config_channel_bar_width = 60
config_channel_bar_hasdata = 11
config_channel_bar_active = 7
config_channel_bar_inactive = 8
config_channel_bar_current = 15
config_channel_bar_prefix = '|01['
config_channel_bar_postfix = '|01]|07'
config_channel_name = (3,1,11,73,' ','left')
config_chatscreen_mynick = (3,23,11,10,' ','center')

config_input = (12,23,64,255) #x, y, width, maxsize
config_input_gfx_lo = (1,22)
config_input_gfx_hi = config_input_gfx_lo
config_input_attr = 7+16
config_input_fillattr = 1

config_chatscreen_total_users = (71,config_input_gfx_lo[1],1,5,'-','right')

config_prompt_att = 15
config_prompt_true_att = 16+14
config_prompt_false_att = 7*16
config_prompt_normal_att = 7

config_chatscreen_nick_width = 8
config_chatscreen_nick_char = '³' 
config_chatscreen_nick_color = 8
config_chatscreen_timestamps = True

config_chatscreen_text_width = config_chatscreen[2]-config_chatscreen[0]-config_chatscreen_nick_width -1
config_chatscreen_timestamp_width = 6
config_chatscreen_timestamp_color_mci = '|08'
config_chatscreen_timestamp_color_att = 8
config_chatscreen_text_width -= config_chatscreen_timestamp_width
config_chatscreen_text_height = config_chatscreen[3]-config_chatscreen[1]+1

config_chatscreen_ruler='-' * config_chatscreen_text_width
config_chatscreen_ruler_att=8



config_mci_censor = '|12'
config_mci_reset_text = '|07'

config_command_prefix = '/'
config_alias_prefix = '`'
config_alias_sep = '&'

config_channeloptions_pos = (31,3)
config_channelmode_pos = (25,3)

EXIT_COMMAND = "/EXIT"
channels = None
AREA = 1
AREA_CHAT = 2
AREA_USERS = 3
AREA_INPUT = 1
NICKS_VISIBLE = True


ALIASES = {}
sprites = {}
irc = None
ENCODING = 'latin'

#CMD[''] = ''

def add_replacer(match_obj):
  recur_arith = '\$add\((\d|[1-9]\d+)\s*\+\s*(.*)\)'
  try:
    return str(int(match_obj.group(1)) + int(re.sub(recur_arith, add_replacer, match_obj.group(2))))
  except ValueError:
    return match_obj.group(1)

def eval_adds(string):
  return re.sub(recur_arith, add_replacer, string)


#print(eval_adds("the result is 5 + 4 + 2+3+1 + ."))

def mysticvariables(st):
  res = st
  res = res.replace('|CN',channels.channels[channels.current].name) #channel name
  res = res.replace('|CM',channels.channels[channels.current].mode)  # channel mode
  res = res.replace('|CT',channels.channels[channels.current].topic)  # channel topic
  res = res.replace('|CU',str(len(channels.channels[channels.current].users)))  # channel users
  
  res = res.replace('|UH',irc.nick)
  res = res.replace('|UN',irc.name)
  res = res.replace('|DT',datetime.datetime.now().strftime("%H:%M"))
  res = res.replace('|DA',datetime.datetime.now().strftime("%Y-%m-%d"))
  
  res = res.replace('|PM',irc.partMessage) # part message
  res = res.replace('|QM',irc.quitMessage) # quit message
  return res

def statusbar(text):
  writexylist(config_statusbar,text)
  if irc.connected:
    writexy(70,config_statusbar[1],config_statusbar[2],'| CONNECT ')
  else:
    writexy(70,config_statusbar[1],config_statusbar[2],'| DISCON. ')
  textcolor(7)

def attr2mci(att,change_background=True):
  fg = att % 16
  bg = att // 16
  s = '|'+str(fg).zfill(2)
  if change_background:
    s = s + '|'+str(16+bg).zfill(2)
  return s
  
def getyesno(prompt):
  _,y,w,_ = config_input #= (12,23,64,255)
  x, _, _, w1, _, _ = config_chatscreen_mynick #(3,23,11,10,' ','center')
  writexy(x,y,7,' '*(w+w1))
  writexy(x,y,config_prompt_att,prompt)
  ans = xinput.getyesno(x+len(prompt)+1,y,config_prompt_true_att,config_prompt_false_att,config_prompt_normal_att,False)
  if ans == 'yes':
    return True
  else:
    return False

def onoff2bool(bl):
  if bl.upper() == 'ON':
    return True
  else:
    return False
  
def bool2onoff(bl):
  return 'On' if bl else 'Off'

def writecenter(line,att,text):
  d = len(text) // 2
  writexy((WIDTH // 2) - d,line,att,text)

def loadsprites(filename):
  if not os.path.isfile(filename): return
  sf = open(filename,'r', encoding="cp437")
  res = {}
  while True:
    line = sf.readline()
    l = line.upper()
    if not line: break
    if line.startswith('#'):
      continue
    elif line == '':
      continue
    elif l.startswith('!AUTHOR'):
      res['author']=line.split('=')[1].strip()
    elif l.startswith('!DATE'):
      res['date']=line.split('=')[1].strip()
    elif l.startswith('!LICENSE'):
      res['license']=line.split('=')[1].strip()
    elif l.startswith('!TITLE'):
      res['title']=line.split('=')[1].strip()
    elif l.startswith('!RESOLUTION'):
      res['resolution']=line.split('=')[1].strip()
    elif l.startswith('!MODE'):
      res['mode']=line.split('=')[1].strip()
    elif l.startswith('!COMMENT'):
      res['comment']=line.split('=')[1].strip()
    elif l.startswith('!CONTACT'):
      res['contact']=line.split('=')[1].strip()
    elif line.startswith('@'):
      line = line[1:]
      name,w,h = line.split(';')
      w=int(w)
      h=int(h)
      name = name.replace('"','')
      item = {}
      item['width']=w
      item['height']=h
      item['data'] = []
      for d in range(h):
        l = sf.readline()
        item['data'].append(l)
      res[name]=item
  return res
  
def writesprite(x,y,name):
  for yi in range(sprites[name]['height']):
    gotoxy(x,y+yi)
    write(sprites[name]['data'][yi])

def dispfilebg(filename):
  gotoxy(1,1)
  with open(filename,encoding="CP437") as fp:  
    lines = fp.readlines()
    cnt = 0
    while cnt<=len(lines)-1:
      a=lines[cnt]
      gotoxy(1,cnt+1)
      write(a)
      cnt+=1
      
class IRC:
    # Encapsulates a connection to an IRC server. Handles sending / receiving of
    # messages, message parsing, connection and disconnection, etc.
    nick = "valhala"
    host = "localhost"
    server = "localhost:6667" #"irc.rizon.net:6667"
    user = ""
    name = "beta tester"
    partMessage = "Parting!"
    quitMessage = "Quitting!"
    logfile = maindir+"log.txt"
    version = "0.0000001"
    connected = False
    logEnabled = True
    stopThreadRequest = threading.Event()
    rxQueue = queue.Queue()
    
    def isjoined(self):
        chan = channels.channels[channels.findactive()]
        if chan:
          return True
        else:
          return False
          

    def start_thread(self):
        # Spawn a new thread to handle incoming data. This function expects that
        # the class variable named socket is a handle to a currently open socket.
        self.socketThread = SocketThread(self.stopThreadRequest,
                                         self.rxQueue,
                                         self.server,
                                         self.port,
                                         self.sock)
        self.stopThreadRequest.clear()
        self.socketThread.start()

    def stop_thread(self):
        # Signal the socket thread to terminate by setting a shared event flag.
        self.stopThreadRequest.set()

    def connect(self, server, port):
        # Connect to an IRC server using a given host name and port. Creates a
        # network socket that is used by a separate thread when receiving data.
        try:
          if (not self.connected):
              self.server = server
              self.port = port
              #try:
              self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
              self.sock.connect((server, port))
              self.start_thread()
              ui.add_status_message("Connecting to %s:%s" % (server, str(port)))
              self.connected = True
              time.sleep(3)
              self.login(self.nick, self.user, self.name, self.host, server)
              statusbar('Connected...')
              #except:
              #    self.connected = False
              #    ui.add_status_message('Server not found. Could not connect!')
          else:
              ui.add_status_message("Already connected.")
        except:
            ui.add_status_message('Error while connecting... aborted!')
            self.connected = False
            statusbar('Not connected!')

    def send(self, command):
        # Send data to a connected IRC server.
        if (self.connected):
            self.sock.send(bytes(command + '\n', ENCODING))
            #ui.add_debug_message("-> " + command)
            self.logToFile(command)
    
    def topic(self,channel,topic):
        if (self.connected):
            self.send("TOPIC %s :%s" % (channel, topic))
            self.send("TOPIC %s" % (channel))
        else:
            ui.add_status_message("You are not connected!")

    def invite(self,nick,channel):
        if (self.connected):
            self.send("INVITE %s :%s" % (nick, channel))
            ui.add_status_message("Sent invitation to %s, to join %s" % (nick,channel))
        else:
            ui.add_status_message("You are not connected!")

    def send_message(self, s):
        # Send a message to the currently joined channel.
        if (channels.current!=0):
            ui.add_nick_message(irc.get_nick(), s)
            self.send("PRIVMSG %s :%s" % (channels.channels[channels.current].name, s))
            self.logToFile("PRIVMSG %s :%s" % (channels.channels[channels.current].name, s))
        else:
            ui.add_status_message("not in a channel")

    def send_private_message(self, nick, s):
        # Send a private message to the given nickname.
        if (self.connected):
            self.send("PRIVMSG %s :%s" % (nick, s))
            ui.add_nick_message(irc.get_nick(), "[%s] %s" % (nick, s))
        else:
            ui.add_status_message("You are not connected!")

    def get_status(self):
        return (self.nick, self.server, self.channel, self.topic)

    def disconnect(self):
        # Disconnect from the currently connected IRC server.
        if (self.connected):
            self.send("QUIT :%s" % self.quitMessage)
            self.stop_thread()
            self.connected = False
            statusbar('Disconnected...')
            #self.server = ""
            ui.add_status_message("Disconnected from "+self.server,'Server')
        else:
            ui.add_status_message("You are not connected!")

    def login(self, nick, user, name, host, server):
        # Send a log-in stanza to the currently connected server.
        self.send("USER %s %s %s %s" % (user, host, server, name))
        self.send("NICK %s" % nick)
        ui.add_status_message("Using nickname %s" % nick)
    
    def othercommand(self,command,args):
        self.send(command.upper()+' '+' '.join(args[0:]))
        self.logToFile('other> '+command.upper()+' '+' '.join(args[0:]))
        
    def join(self, channel,args):
        # Join the given channel.
        if channel[:1]!='#':
          ui.add_status_message(channel+': Not a channel name. Add the # char in front of it.')
          return
        if (self.connected):
            if args:
                self.send("JOIN %s %s" % (channel,' '.join(args[0:])))
            else:
                self.send("JOIN %s" % channel)
            cid = channels.findbyname(channel)
            if not cid:
              cid = channels.add(channel)
              channels.channels[cid].filename = datadir+'logs'+os.sep+safefilenamestring(self.server)+'_'+channels.channels[cid].filename
            
            self.send("MODE %s" % (channel))
            
            channels.channels[channels.current].active = False
            channels.setactivebyname(channel)
            channels.current = channels.findactive()
            ui.add_status_message('Saving log to: '+channels.channels[channels.current].filename)
            ui.clearchatscreen()
            ui.redrawchannel()
            ui.redrawchannelbar()
            ui.redraw_nicks()
        else:
            ui.add_status_message("not connected")

    def part(self):
        global channels
        # Leave the current channel.
        if channels.current!=0:
            channels.channels[channels.current].savechat()
            self.send("PART %s" % channels.channels[channels.current].name)
            
            ui.add_status_message("Left channel %s " % channels.channels[channels.current].name)
            
            i = channels.current+1
            while i<channels.count:
              channels.channels[i].cid -= 1
              i+=1
            
            channels.remove(channels.channels[channels.current].name)
            channels.channels[0].active = True
            channels.current = 0
              
            ui.clearchatscreen()
            ui.redrawchannel()
            ui.redraw_nicks()
            ui.redrawchannelbar()

        else:
            ui.add_status_message("not in a channel")
        channels.current = 0

    def add_nick(self, s):
        # Add a nickname to the list of nicknames we think are in the channel.
        # Called when a user joins the current channel, in response to a join.
        chan = channels.channels[channels.findactive()]
        chan.users.append(s)
        chan.users.sort()
        if channels.current!=0:
            writexylist(config_chatscreen_total_users,str(len(channels.channels[channels.current].users)))

    def del_nick(self, s):
        # Remove a nickname the list of nicknames we think are in the channel.
        success = False
        chan = channels.channels[channels.findactive()]
        if s in chan.users:
            chan.users.remove(s)
            success = True
        if not success:
            if '@'+s in chan.users:
              chan.users.remove('@'+s)
              success = True
        if not success:
            if '+'+s in chan.users:
              chan.users.remove('+'+s)
              success = True
        if channels.current!=0:
            writexylist(config_chatscreen_total_users,str(len(channels.channels[channels.current].users)))
              
    def replace_nick(self, old, new):
        self.del_nick(old)
        self.add_nick(new)
        #ui.set_nicklist(self.nicklist)
        ui.add_status_message("%s is now known as %s" % (old, new))
        if channels.current!=0:
            channels.channels[channels.current].addline('Channel',"%s is now known as %s" % (old, new),config_chatscreen_text_width,config_chatscreen_notice_att)
        ui.create_suggestions()

    def request_nicklist(self):
        # Send a request to the IRC server to give us a list of nicknames
        # visible in the current channel.
        if channels.current!=0:
            self.send("NAMES %s" % channels.getnameofactive())
    
    def setchannelmode(self,s):
      if (self.connected):
        if channels.current!=0:
          chan = channels.channels[channels.current]
          self.send("MODE %s %s" % (chan.name,s))
            
            
    def set_nick(self, s):
        # Change our own nickname.
        if (self.connected):
            self.send(":%s!%s@%s NICK %s" % (self.nick, self.user, self.host, s))
            ui.redraw_nicks()
            writexylist(config_chatscreen_mynick,self.nick)
            
    def whois(self,user):
        if (self.connected):
            if user[0] in '@+':
              user = user[1:]
            self.send("WHOIS %s" % (user))
        else:
            ui.add_status_message("You are not connected!")
    
    def motd(self):
        if (self.connected):
            self.send('MOTD')
        else:
            ui.add_status_message("You are not connected!")
            
    def away(self,reason):
        if (self.connected):
            self.send("AWAY :%s" % (reason))
        else:
            ui.add_status_message("You are not connected!")

    def get_nick(self):
        # Return our own nickname.
        return self.nick

    def is_connected(self):
        # Return our IRC server connection state.
        return self.connected
    
    def handle_ctcp(self, cmd, msg):
        ui.add_status_message("got CTCP message: " + cmd)
        if (cmd == "VERSION"):
            self.send("VERSION Mystic-IRC %s" % version)
        if (cmd == "ACTION"):
            #ui.add_emote_message(self.nick, msg)
            ui.add_message(msg,15,True)

    def logToFile(self, s):
        # Write the given string to a log file on disk, appending a newline.
        # The logfile is opened for writing if not already open.
        
        self.file = open(self.logfile, 'a+')
        self.file.write(datetime.datetime.now().strftime("%Y-%m-%d / %H:%M:%S")+'| '+s + "\n")
        self.file.flush()

    def poll(self):
        # Check for incoming messages from the IRC server by polling a shared
        # message-queue populated by the socket handling thread. Strings read
        # from the queue have been buffered from the receiving socket and each
        # string represents a logical message sent by the server.
        rx = ""
        try:
            rx = self.rxQueue.get(True, 0.01)
        except:
            pass
        if rx:
            #ui.add_debug_message("<- " + rx)
            #self.logToFile('poll> '+rx)
            self.handle_message(self.parse_message(rx))

    def parse_message(self, s):
        # Transform incoming message strings received by the IRC server in to
        # component parts common to all messages.
        prefix = ''
        trailing = []
        if (s[0] == ':'):
            prefix, s = s[1:].split(' ', 1)
        if (s.find(' :')) != -1:
            s, trailing = s.split(' :', 1)
            args = s.split()
            args.append(trailing)
        else:
            args = s.split()
        command = args.pop(0)
        self.logToFile('parse2> '+str(prefix)+' | '+str(command)+' | '+str(args))
        return prefix, command, args
    
    def get_privmsg(self,nick,channel,message):
      cid = channels.findbyname(channel)
      if cid and cid!=0:
        message = ui.censor(message)
        channels.channels[cid].addline(nick,message,config_chatscreen_text_width)
        if channels.current!=cid:
          channels.channels[cid].has_data = True
          ui.redrawchannelbar()
        else:
          ui.redrawchannel()
          ui.redraw_nicks()
      else:
        cid = channels.findbyname(nick)
        if not cid:
          cid = ui.add_private_channel(nick)
        message = ui.censor(message)
        channels.channels[cid].addline(nick,message,config_chatscreen_text_width)
        if channels.current == cid:
          ui.redrawchannel()
          ui.redrawtopic()
        else:
          channels.channels[cid].has_data = True
          ui.redrawchannelbar()

    def handle_message(self, msg):
        # Respond to incoming IRC messages by handling them here or passing
        # control to other class methods for further processing.
        prefix, cmd, args = msg
        #self.logToFile('>>'+str(prefix)+' | '+str(cmd)+' | '+str(args))
        if cmd.isnumeric():
            cmdint = int(cmd)
            if cmdint >=400 and cmdint < 500: #errors!
                ui.add_status_message(config_chatscreen_error_mci+' '.join(args[1:]))
            elif cmd == '475':
                if args[0] == irc.nick:
                    chan = channels.channels[channels.findbyname(args[1])]
                    if chan:
                        channels.remove(chan.name)
                        channels.channels[0].active = True
                        channels.current = 0
                          
                        ui.clearchatscreen()
                        ui.redrawchannel()
                        ui.redraw_nicks()
                        ui.redrawchannelbar()
                        ui.create_suggestions()
                        
                      
            elif (cmd == '451'): # request identify
                self.login()
            elif cmd == '253':  #how many clients are connected
                ui.add_status_message(' '.join(args[1:]))
            elif cmd == '254':  #how many clients are connected
                ui.add_status_message(' '.join(args[1:]))
            elif cmd == '255':  #how many clients are connected
                ui.add_status_message(' '.join(args[1:]))
            elif cmd == '321': #start of channel list
                ui.add_status_message('List of available channels in server...')
                ui.add_status_message('|15%-15s %-3s %-50s' % ('Channel','#U','Topic'))
                ui.add_status_message('-'*config_chatscreen_text_width,color=config_chatscreen_irrelevant)
            elif cmd == '322': #list of channel
                ui.add_status_message('|15%-15s |07%-3s |11%-50s' % (args[1],args[2],' '.join(args[3:])))
            elif cmd == '323': #end of channel list
                s = '-'*(config_chatscreen_text_width-6)
                s = '- END ' +s
                ui.add_status_message(s,color=config_chatscreen_irrelevant)
            elif cmd == '301':
                chan = channels.channels[channels.findactive()]
                if chan:
                    chan.addline('Server',('User: %s is marked as away.' % args[1]),config_chatscreen_text_width,config_chatscreen_notice_att)
                    chan.addline('Server',' '.join(args[2:]),config_chatscreen_text_width,config_chatscreen_notice_att)
                    if chan.cid !=0:
                        ui.add_status_message(('User: %s is marked as away.' % args[1]))
                        ui.add_status_message(' '.join(args[2:]))
                    
            elif cmd == '315': #end of who, omit
                ui.add_status_message(config_chatscreen_ruler,color=config_chatscreen_ruler_att)
            elif cmd == '317': # whois, idle time and signon
                ui.add_status_message('Idle: %s, SignOn: %s' % (str(datetime.timedelta(seconds=int(args[2]))),datetime.datetime.utcfromtimestamp(int(args[3])).strftime('%Y-%m-%d %H:%M:%S')))
            elif cmd == '318': #end of whois, omit
                ui.add_status_message(config_chatscreen_ruler,color=config_chatscreen_ruler_att)
            elif cmd == '324':
                if len(args)>2:
                    chan = channels.channels[channels.findbyname(args[1])]
                    if chan:
                        chan.parsemode(' '.join(args[2:]))
                        chan.mode = chan.mode2str()
                        ui.redrawtopic()
            elif cmd == '329':
                chan = channels.channels[channels.findbyname(args[1])]
                if chan:
                    chan.created = int(args[2])
                    ui.add_status_message('Channel '+chan.name+' created at: '+datetime.datetime.utcfromtimestamp(int(chan.created)).strftime('%Y-%m-%d %H:%M:%S'))
            elif cmd == '331': #no topic
                cid = channels.findbyname(args[0])
                if cid:
                  chan = channels.channels[cid]
                  if chan:
                      chan.mode = ''
                      ui.redrawtopic()
            elif cmd == '332': #topic changed
                chan = channels.channels[channels.findactive()]
                if chan:
                    chan.topic = ' '.join(args[2:])
                    ui.redrawtopic()
                    chan.addline('Channel','Topic changed to: '+chan.topic,config_chatscreen_text_width,config_chatscreen_notice_att)
            elif cmd == '333': #who set topic
                chan = channels.channels[channels.findbyname(args[1])]
                if chan.name!='Server':
                    ui.add_status_message('Topic for channel: %s was set by %s at %s' % (args[0],args[1],datetime.datetime.utcfromtimestamp(int(args[3])).strftime('%Y-%m-%d %H:%M:%S')))
            elif cmd == "341": #invitation
                 nick = prefix[:prefix.find('!')]
                 #ui.add_status_message('You have been invited to %s by %s ' % (args[0:],nick),color=config_chatscreen_attention)
                 channels.channels[channels.current].addline('*','You have invited %s to join %s ' % (args[1],args[2]),color=config_chatscreen_irrelevant)
                 ui.redrawchannel()
            elif cmd == "351": #server version
                ui.add_status_message(' '.join(args[1:]))
            elif (cmd == "353"):
                # Receiving a list of users in the channel (aka RPL_NAMEREPLY).
                # Note that the user list may span multiple 353 messages.
                chan = channels.channels[channels.findactive()]
                if chan:
                  chan.users.clear()
                  chan.users = ' '.join(args[3:]).split()
                  chan.users.sort()
                ui.redraw_nicks()
            elif cmd == '365': #end of links
                ui.add_status_message(config_chatscreen_ruler,color=config_chatscreen_ruler_att)
            elif cmd == '368': #end of channel ban list
                ui.add_status_message(config_chatscreen_ruler,color=config_chatscreen_ruler_att)
            elif cmd == '369': #end of whowas, omit
                ui.add_status_message(config_chatscreen_ruler,color=config_chatscreen_ruler_att)
            elif (cmd == "372"): #MOTD
                ui.add_status_message(' '.join(args[1:]))
            elif cmd == '374': #end of info
                ui.add_status_message(config_chatscreen_ruler,color=config_chatscreen_ruler_att)
            elif (cmd == "376"): # Finished receiving the message of the day (MOTD).
                ui.add_status_message(config_chatscreen_ruler,color=config_chatscreen_ruler_att)
            elif (cmd == "375"): # MOTD Starting!!!!
                ui.add_status_message("|14Receiving MOTD... hold up!")
            elif cmd == "391": #time of server
                ui.add_status_message('DateTime is: '+' '.join(args[1:]))
            elif cmd == '394': #end of users
                ui.add_status_message(config_chatscreen_ruler,color=config_chatscreen_ruler_att)
            else:
                ui.add_status_message(' '.join(args[1:]))
        else:
            if (cmd == "PING"):
                # Reply to PING, per RFC 1459 otherwise we'll get disconnected.
                irc.send("PONG %s" % args[0])
            elif (cmd == "PRIVMSG"):
                # Either a channel message or a private message; check and display.
                message = ' '.join(args[1:])
                nick = prefix[:prefix.find('!')]
                if (args[1].startswith(chr(1))):
                    #mytable = message.maketrans(None, chr(1))
                    ctcp = message.replace(chr(1),'')
                    ctcp = message.split()
                    ctcp_cmd = ctcp[0]
                    ctcp_msg = ' '.join(ctcp[1:])
                    self.handle_ctcp(ctcp_cmd, ctcp_msg)
                else:
                    self.get_privmsg(nick,args[0],message)
                #elif (args[0] == irc.channel):
                #    ui.add_nick_message(nick, message)
            elif cmd == 'NOTICE':
                ui.add_status_message(config_chatscreen_notice_mci+' '.join(args[0:]))
            elif cmd == 'ERROR':
                ui.add_status_message(config_chatscreen_error_mci+' '.join(args[0:]))
            elif (cmd == 'JOIN'):
                nick = prefix[:prefix.find('!')]
                if (not self.isjoined()):
                    # We weren't joined, so join message must be us joining.
                    #ui.update_status()
                    channels.setactivebyname(args[0],args[1:])
                    channels.current = channels.findactive()
                    ui.redrawchannel()
                    ui.redrawchannelbar()
                    ui.redraw_nicks()
                    ui.add_status_message('Joined channel %s ' % channels.channels[channels.current].name)
                    ui.add_status_message('Saving log to file: %s ' % channels.channels[channels.current].name)
                    
                elif (nick != self.nick):
                    # A user has joined the channel. Update nick list.
                    irc.add_nick(prefix[:prefix.find('!')])
                    chan = channels.channels[channels.findactive()]
                    ui.add_status_message("User %s joined %s" % (nick,chan.name))
                    ui.redraw_nicks()
                    ui.create_suggestions()
            elif cmd == 'INVITE':
                nick = prefix[:prefix.find('!')]
                channels.channels[channels.current].addline('*','You have been invited to %s by %s ' % (args[1],nick),color=config_chatscreen_attention)
                ui.redrawchannel()
            elif (cmd == "PART" and args[0] == channels.channels[channels.current].name):
                # A user has left the channel. Update nick list.
                nick = prefix[:prefix.find('!')]
                irc.del_nick(nick)
                channels.channels[channels.current].addline('Channel',"%s left the channel" % nick,config_chatscreen_text_width,config_chatscreen_notice_att)
                ui.redrawchannel()
                ui.redraw_nicks()
                ui.create_suggestions()
            elif (cmd == "NICK"):
                old = prefix[:prefix.find('!')]
                new = args[0]
                if (old == self.nick):
                    # server acknowledges we changed our own nick
                    self.nick = new
                    writexylist(config_chatscreen_mynick,self.nick)
                self.replace_nick(old, new)
                #ui.update_status()
            elif cmd == 'TOPIC':
                cid = channels.findbyname(args[0])
                if cid:
                    channels.channels[cid].topic = ' '.join(args[1:])
                    channels.channels[cid].addline('Channel',prefix,config_chatscreen_text_width,config_chatscreen_notice_att)
                    irc.logToFile(prefix+'|'+cmd+'|'+' '.join(args[0:]))
                    ui.redrawtopic()
            elif cmd == 'MODE':
                if len(args)>1:
                    if args[0].startswith('#'): #it's a channel...
                        cid = channels.findbyname(args[0])
                        if cid: #it's a channel
                            channels.channels[cid].parsemode(' '.join(args[1:]))
                            channels.channels[cid].mode = channels.channels[cid].mode2str()
                            ui.redrawtopic()
                    else: #it's a user...
                        pass
                    
                
            else:
                ui.add_status_message(' '.join(args[1:]))

class SocketThread(threading.Thread):
    # A worker thread used to receive data from the connected IRC server. Once
    # started, sits in a loop reading data and assembling line-based messages
    # from the server. This thread terminates after a shared status flag is set
    # by the main thread in response to a disconnect command.
    running = True
    def __init__(self, event, rxQueue, server, port, sock):
        super(SocketThread, self).__init__()
        self.stopThreadRequest = event
        self.rxQueue = rxQueue
        self.server = server
        self.port = port
        self.sock = sock

    def run(self):
        # Continuously read from our (blocking) socket. We want to add complete
        # messages from the IRC server to our queue to be handled downstream, but
        # since the network buffer may contain only part of a message, we'll use
        # a local buffer to store incomplete messages.
        rx = ""
        while(not self.stopThreadRequest.isSet()):
            rx = rx + self.sock.recv(1024).decode(ENCODING)
            if (rx != ""):
                #ui.add_status_message(rx)
                irc.logToFile('rx> '+rx)
                temp = rx.split("\n")
                rx = temp.pop( ) # put left-over data back in our local buffer
                for line in temp:
                    line = line.rstrip()
                    self.rxQueue.put(line)
            else:
                # remote end disconnected, so commit thread suicide!
                self.stopThreadRequest.set()
        return

class UserInterface:
  # Uses the curses terminal handling library to display a chat log,
  # a list of users in the current channel, and a command prompt for
  # entering messages and application commands.
  badwords = []
  hilites = []
  history = []
  history_index = 0
  
  def __init__(self):
    self.inputstring = ''
    self.enable_censor = False
    self.badwords = self.load_list(datadir+"badwords.txt")
    self.hilites = self.load_list(datadir+"hilites.txt")
    self.colors = 16
    self.kb = xinput.inputxy()
    self.kb.x = config_input[0]
    self.kb.y = config_input[1]
    self.kb.attr = config_input_attr
    self.kb.fillattr = config_input_fillattr
    self.kb.maxwidth = config_input[3]
    self.kb.width = config_input[2]
    self.kb.onextotherkey = self.kbd_onotherkey
    self.kb.onenter = self.kbd_onenter
    self.kb.ontab = self.kbd_ontab
    self.history.clear()
    self.history_index = 0
    
    
  def clearchatscreen(self):
    x1,y1,x2,y2 = config_chatscreen
    textcolor(7)
    cleararea(x1,y1,x2,y2,' ')
    
  def add_debug_message(self, s):
    self.add_status_message(s)
    
  def create_suggestions(self):
    tmp = []
    tmp.append(irc.nick.lower())
    for key in CMD.keys():
      tmp.append(CMD[key].lower())
    for i in range(channels.count):
      tmp.append(channels.channels[i].name.lower())
    for user in channels.channels[channels.current].users:
      tmp.append(user.lower())
    return tmp
         
  def redraw_nicks(self):
    global NICKS_VISIBLE, channels
    if channels.channels[channels.current].topic == "Private Chat":
      return
    textcolor(7)    
    if NICKS_VISIBLE and channels.current!=0:
      textcolor(7)
      cleararea(config_nicklist[0],config_nicklist[1],config_nicklist[2],config_nicklist[3],' ')
      if AREA == AREA_USERS:
        x,y = config_nicklist_gfx_hi
        writesprite(x,y,'usershi')
      else:
        x,y = config_nicklist_gfx_lo
        writesprite(x,y,'userslo')
      
      h = config_nicklist[3] - config_nicklist[1] + 1
      w = config_nicklist[2] - config_nicklist[0] + 1
      
      chan = channels.channels[channels.findactive()]
      
      tmp = chan.users
      for i, nick in enumerate(tmp[:h]):
        writexy(config_nicklist[0],config_nicklist[1]+i,config_nicks_normal,nick[:w].ljust(w,' '))
    else:
      self.clearchatscreen
      self.redrawchannel()
   
  def draw_main(self):
    global channels
    cleararea(config_chatscreen[0],config_chatscreen[1],config_chatscreen[2],config_chatscreen[3],' ')
    #writexylist(config_topic_title,' '+channels.channels[channels.current].topic+' ')
    self.redrawtopic()
    #writexylist(config_topic_title,' '+channels.channels[channels.current].name+' ')
    x,y = config_chatscreen_gfx_lo
    writesprite(x,y,'chatlo')
    writecenter(config_channel_name[1],config_channel_name[2],' '+channels.channels[channels.current].name+' ')
    #if NICKS_VISIBLE:
    #  x,y = config_nicklist_gfx_lo
    #  writesprite(x,y,'userslo')
    x,y = config_input_gfx_hi
    writesprite(x,y,'inputhi')
    writexylist(config_chatscreen_mynick,irc.nick)
    
  def redraw_input(self):
    if AREA == AREA_INPUT:
      x,y = config_input_gfx_hi
      writesprite(x,y,'inputhi')
    else:
      x,y = config_input_gfx_lo
      writesprite(x,y,'inputlo')
    writexylist(config_chatscreen_mynick,irc.nick)
    if channels.current!=0:
      writexylist(config_chatscreen_total_users,str(len(channels.channels[channels.current].users)))
  
  def kbd_onotherkey(self,key):
    global AREA, channels, config_chatscreen_text_height
    #writexy(1,1,13,'Other Key!!!>   '+key+' //')
    
    if AREA == AREA_INPUT:   # page up/down changes input History in input mode
      if key == xinput.KBPAGE_UP:   
        if len(self.history)>0:
          self.history_index -=1
          if abs(self.history_index)>len(self.history)-1:
            self.history_index = 0
          self.kb.text = self.history[self.history_index]
      elif key == xinput.KBPAGE_DOWN:
        if len(self.history)>0:
          self.history_index +=1
          if abs(self.history_index)>len(self.history)-1:
            self.history_index = 0
          self.kb.text = self.history[self.history_index]
    elif AREA == AREA_CHAT:
      channel = channels.channels[channels.current]
      if len(channel.chat)<config_chatscreen_text_height:
        pass
      elif key == '[V':   
        if len(channel.chat)<config_chatscreen_text_height:
          return
        channel.chat_top -= config_chatscreen_text_height
        if channel.chat_top < 0: channel.chat_top = 0
        self.redrawchannel()
      elif key == '[U':
        channel.chat_top += config_chatscreen_text_height
        if channel.chat_top > len(channel.chat)-1:
          channel.chat_top = len(channel.chat) - config_chatscreen_text_height
        if channel.chat_top + config_chatscreen_text_height > len(channel.chat)-1:
          channel.chat_top = len(channel.chat) - config_chatscreen_text_height
          
          
        self.redrawchannel()
  def add_nick_message(self, nick, s):
    global config_chatscreen_text_width
    # Add another user's message in the chat window.
    channels.channels[channels.current].addline(nick,s,config_chatscreen_text_width)
    ui.redrawchannel()
      
  def add_status_message(self,text,user='Server',color=config_chatscreen_normal):
    global channels,WIDTH,config_chatscreen_text_width
    seen = False
    if channels.current == 0: seen = True
    if isinstance(text, list):
      for line in text:
        channels.channels[0].addline(user,line,config_chatscreen_text_width,seen=seen,color=color)
    else:
      channels.channels[0].addline(user,text,config_chatscreen_text_width,seen=seen,color=color)
    if channels.current == 0: 
      self.redrawchannel()
    else:
      channels.channels[0].has_data = True
      self.redrawchannelbar()

  def read_kbd_input(self,inputQueue):
    while (True):
      self.kb.getstrxy(config_input[0],config_input[1],'')
      inputQueue.put(self.kb.text)
      self.kb.text = ''
      
  def inputstr(self,title,helptext=''):
    x,y,w,m = config_input
    writexylist(config_chatscreen_mynick,title)
    statusbar(helptext)
    res = xinput.simpleinput(x,y,config_input_attr,config_input_fillattr,xinput.cs_printable,w,m,"#",'')
    #res = xinput.simpleinput(x,y,config_input_attr,config_input_fillattr,xinput.cs_printable,w,m,chr(176),'')
    return res

  def draw_channel_options(self):
    global NICKS_VISIBLE,config_chatscreen_timestamps
    x,y = config_channeloptions_pos
    writesprite(x,y,'optionsbox')
    
    entries = []
    item1 = {}
    item1['x'] = x+1
    item1['y'] = y+2
    item1['low'] = 7
    item1['high'] = 62
    item1['textlow'] = ' Save Log        '
    item1['texthigh'] = ' Save Log        '
    item1['key'] = 'S'
    item1['code'] = 'save'
    entries.append(item1)
    item2 = {}
    item2['x'] = x+1
    item2['y'] = y+3
    item2['low'] = 7
    item2['high'] = 62
    item2['textlow'] = ' Change Topic    '
    item2['texthigh'] = ' Change Topic    '
    item2['key'] = 'T'
    item2['code'] = 'topic'
    entries.append(item2)
    item3 = {}
    item3['x'] = x+1
    item3['y'] = y+4
    item3['low'] = 7
    item3['high'] = 62
    item3['textlow'] = ' Change Mode     '
    item3['texthigh'] = ' Change Mode     '
    item3['key'] = 'M'
    item3['code'] = 'mode'
    entries.append(item3)
    
    item4 = {}
    item4['x'] = x+1
    item4['y'] = y+5
    item4['low'] = 7
    item4['high'] = 62
    item4['textlow'] = ' Toggle User Bar '
    item4['texthigh'] = ' Toggle User Bar '
    item4['key'] = 'U'
    item4['code'] = 'nicks'
    entries.append(item4)
    item5 = {}
    item5['x'] = x+1
    item5['y'] = y+6
    item5['low'] = 7
    item5['high'] = 62
    item5['textlow'] = ' Toggle Timestamp'
    item5['texthigh'] = ' Toggle Timestamp'
    item5['key'] = 'e'
    item5['code'] = 'timestamp'
    entries.append(item5)
    statusbar('Use Arrow keys to select, ENTER to chose and ESC to cancel')
    ans = xinput.lightbarmenu(entries,1)
    if ans == 'topic':
      if channels.current == 0:
        self.add_status_message(config_chatscreen_error_mci+'Topic can be changed, only when connected to a channel.')
      else:
        new = self.inputstr('Topic:','Type new topic, ESC cancels the function')
        if new:
          irc.topic(channels.channels[channels.current].name,new)
    elif ans == 'mode':
      self.draw_channel_mode()
    elif ans == 'nicks':
      NICKS_VISIBLE = not NICKS_VISIBLE
      self.redraw_nicks()
      self.redrawchannelbar()
    elif ans == 'save':
      chan = channels.channels[channels.current]
      chan.savechat()
    elif ans == 'timestamp':
      config_chatscreen_timestamps = not config_chatscreen_timestamps
      self.redrawchannel()
      
      
    self.complete_redraw()
    writexylist(config_chatscreen_mynick,irc.nick)
    statusbar('Press ENTER for options, TAB for next field.')
    
  def draw_users_list(self):
    #x,y = config_channelmode_pos
    #writesprite(x,y,'usersoptions')
    #statusbar('Use Arrow keys to select, ENTER to choose ESC to cancel')
    
    x1,y1,x2,y2 = config_nicklist
    
    ul = xinput.mlist()
    ul.x = x1
    ul.y = y1
    ul.h = y2-y1+1
    ul.w = x2-x1+1
    
    ul.search_show = True
    ul.searchx = x1
    ul.searchy = y2+1
    ul.searchw = ul.w-2
    
    chan = channels.channels[channels.current]
    
    for user in chan.users:
      il = {}
      il['text'] = user
      ul.additem(il)
    
    while True:
      user = ul.show()
      if ul.exitcode == '#esc':
        break
      elif ul.exitcode == '#enter':
        x1,y1,x2,y2 = config_nicklist
        w = sprites['usersoptions']['width']
        h = sprites['usersoptions']['height']
        x = x1-w+2
        if x<1: x = 1
        y = y1+ul.selbar+1
        if y+h> y2: 
          y = y2-h-1
          if y<1: y = 1
        writesprite(x,y,'usersoptions')
        
        userl = xinput.mlist()
        userl.search_show = False
        userl.x = x+1
        userl.y = y+2
        userl.h = h -3
        userl.w = w -2
        userl.scrollbar['enable'] = False
        
        uil = {}
        uil['text'] = 'Who Is...'
        userl.additem(uil)
        uil = {}
        uil['text'] = 'Private Msg.'
        userl.additem(uil)
        
        res = userl.show()
        if userl.exitcode == '#enter':
          if res['text'] == 'Who Is...':
            irc.whois(user['text'])
          elif res['text'] =='Private Msg.':
            msg = self.inputstr('Message:','Type Message, ESC cancels the function')
            if msg:
              irc.send_private_message(user['text'],msg)
              self.redraw_input()
 
        self.complete_redraw()
        
        
        
    
    self.kbd_ontab()
    
  def draw_channel_mode(self):
    if channels.current == 0:
      self.add_status_message('Mode can only be changed when connected to a channel.')
      return
    x,y = config_channelmode_pos
    writesprite(x,y,'channelsmode')
    statusbar('Use Arrow keys to select, ENTER to choose/toggle and ESC to proceed')
    tform = xinput.mform()
    #additem(self, typeof,tx,ty,tw,title,vx,vy,vw,vmax,value,key,code,fields=[]):
    chan = channels.channels[channels.current]
    
    tform.additem(11,x+1,y+2,14,' Topic'      ,x+18,y+2,8,8,bool2onoff(chan.modes['t']),'T','t',['Off','On'])
    tform.additem(11,x+1,y+3,14,' No Outside' ,x+18,y+3,8,8,bool2onoff(chan.modes['n']),'O','n',['Off','On'])
    tform.additem(11,x+1,y+4,14,' Secret'     ,x+18,y+4,8,8,bool2onoff(chan.modes['s']),'S','s',['Off','On'])
    tform.additem(11,x+1,y+5,14,' Invisible'  ,x+18,y+5,8,8,bool2onoff(chan.modes['i']),'I','i',['Off','On'])
    
    tform.additem(11,x+1,y+6,14,' Private'    ,x+18,y+6,8,8,bool2onoff(chan.modes['p']),'P','p',['Off','On'])
    tform.additem(11,x+1,y+7,14,' Moderated'  ,x+18,y+7,8,8,bool2onoff(chan.modes['m']),'M','m',['Off','On'])
    
    tform.additem(10,x+1,y+8,14,' PassKey'    ,x+18,y+8,8,8,chan.modes['key'],'P','key')
    writexy(x+1,y+9,config_chatscreen_irrelevant,' + Empty disables key')
    tform.additem(10,x+1,y+10,14,' Users Limit',x+18,y+10,8,8,str(chan.modes['users']),'U','users')
    writexy(x+1,y+11,config_chatscreen_irrelevant,' + -1 disables user limit')
    
    tform.drawall()
    tform.show()

    if tform.changed:
      if getyesno('Channel Mode changed. Save? '):
        chan.modes['t'] = onoff2bool(tform.results['t'])
        chan.modes['n'] = onoff2bool(tform.results['n'])
        chan.modes['s'] = onoff2bool(tform.results['s'])
        chan.modes['i'] = onoff2bool(tform.results['i'])
        chan.modes['p'] = onoff2bool(tform.results['p'])
        chan.modes['m'] = onoff2bool(tform.results['m'])
        chan.modes['key'] = tform.results['key']
        if tform.results['key']!='':
          chan.modes['k'] = True
        else:
          chan.modes['k'] = False
        
        if int(tform.results['users'])>0:
          chan.modes['l'] = True
          chan.modes['users'] = int(tform.results['users'])
        else:
          chan.modes['l'] = False
        
        enable = '+'
        disable = '-'
        oldmode = chan.mode
        newmode = ''
        for key in 'tnsipmbkl':
          if key in oldmode:
            if chan.modes[key]:
              pass
            else:
              disable += key
              if key == 'l':
                disable += ' '+str(chan.modes['users'])
              elif key == 'k':
                disable += ' '+chan.modes['key']
          else:
            if chan.modes[key]:
              enable += key
              if key == 'l':
                enable += ' '+str(chan.modes['users'])
              elif key == 'k':
                enable += ' '+chan.modes['key']
            else:
              pass
        
        if not chan.modes['k']: chan.modes['key'] = ''
        if not chan.modes['l']: chan.modes['users'] = -1
        
        #chan.mode2str()
        if len(enable)>1:
          newmode += enable
        if len(disable)>1:
          newmode += disable
        irc.setchannelmode(newmode)
        self.add_status_message(newmode)
        
        
    self.complete_redraw()
    writexylist(config_chatscreen_mynick,irc.nick)
    statusbar('Press ENTER for options, TAB for next field.')    
    
  def complete_redraw(self):
    self.clearchatscreen()
    self.redrawchannel()
    self.redrawchannelbar()
    self.redraw_nicks()
    self.redrawtopic()
    
  def kbd_onenter(self):
    global AREA
    if AREA == AREA_INPUT:
      #self.inputstring = self.censor(self.kb.text)
      self.inputstring = self.kb.text
      self.reset_kbd()
    elif AREA == AREA_CHAT:
      self.draw_channel_options()
    #elif AREA == AREA_USERS and NICKS_VISIBLE and channels.current != 0: 
      #self.draw_users_list()
       
  
  def kbd_ontab(self):
    global AREA, NICKS_VISIBLE, channels
    AREA +=1
    
    if AREA > 3: AREA = 1
      
    if AREA == AREA_CHAT:
      self.kb.disable_suggest = True
      self.kb.disable = True
      x,y = config_input_gfx_lo
      writesprite(x,y,'inputlo')
      x,y = config_chatscreen_gfx_hi
      self.redrawchannelbar()
      writesprite(x,y,'chathi')
      writexylist(config_chatscreen_mynick,irc.nick)
      #writexylist(config_topic_title,' '+channels.channels[channels.current].topic+' ')
      self.redrawtopic()
      #writexylist(config_topic_title,' '+channels.channels[channels.current].name+' ')
      writecenter(config_channel_name[1],config_channel_name[2],' '+channels.channels[channels.current].name+' ')
      statusbar('Press ENTER for options, PGUP/PGDN to scroll, TAB for next area.')
    if AREA == AREA_USERS:
      self.kb.disable_suggest = True
      self.kb.disable = True
      if channels.current == 0 or channels.channels[channels.current].topic == 'Private Chat' or NICKS_VISIBLE==False:
        AREA = AREA_INPUT
      else:
        x,y = config_chatscreen_gfx_lo
        writesprite(x,y,'chatlo')
        self.redrawtopic()
        writecenter(config_channel_name[1],config_channel_name[2],' '+channels.channels[channels.current].name+' ')
        if NICKS_VISIBLE and channels.current!=0 and channels.channels[channels.current].topic != 'Private Chat':
          x,y = config_nicklist_gfx_hi
          writesprite(x,y,'usershi')
          # do nick thinkgs here!
          self.draw_users_list()
          statusbar('Use (PG)Up/Down to select, ENTER for OPTIONS, TAB for next area.')
    if AREA == AREA_INPUT:
      self.kb.disable_suggest = False
      self.kb.disable = False
      if NICKS_VISIBLE and channels.current!=0 and channels.channels[channels.current].topic != 'Private Chat':
        x,y = config_nicklist_gfx_lo
        writesprite(x,y,'userslo')
      else:
        x,y = config_chatscreen_gfx_lo
        writesprite(x,y,'chatlo')
        writecenter(config_channel_name[1],config_channel_name[2],' '+channels.channels[channels.current].name+' ')
      self.redraw_input()
      self.redrawchannelbar()
      
    #writexy(1,25,11,str(AREA)+' cur:'+str(channels.current)+' vis:'+str(NICKS_VISIBLE))
    
  def time_stamp(self):
        # Generate a string containing the current time, used to prefix messages.
    return datetime.now().strftime("[%H:%M]")
  
  def redrawchannelbar(self):
    global channels
    x,y = config_channel_bar
    s = config_channel_bar_prefix
    
    for chan in channels.channels:
      channame = chan.name
      colorset = False
      if len(channame)>8:
        channame = chan.name[:8]+'>'
      
      
      if chan.cid == channels.current:
        s = s+attr2mci(config_channel_bar_current)+str(chan.cid)+':'+channame+' '
        colorset = True
      elif chan.has_data and not colorset:
        s = s+attr2mci(config_channel_bar_hasdata)+str(chan.cid)+':'+channame+' '
        colorset = True  
      elif chan.active==True and not colorset:
        s = s+attr2mci(config_channel_bar_active)+str(chan.cid)+':'+channame+' '
        colorset = True
        
      elif chan.active==False and not colorset:
        s = s+attr2mci(config_channel_bar_inactive)+str(chan.cid)+':'+channame+' '
        colorset = True

      if mcilen(s+config_channel_bar_postfix) > config_channel_bar_width: break
    
    s += config_channel_bar_postfix
    gotoxy(x,y)
    writepipe(s)
    
    '''
    for a in range(channels.count):
      writexy(x+(a*3),y,config_channel_bar_inactive,str(a))
    writexy(x,y,config_channel_bar_inactive,'S')
    for a in range(channels.count):
      if channels.channels[a].has_data:
        writexy(x+(a*3),y,config_channel_bar_hasdata,str(a))
      if channels.current!=0:
        writexy(x+(channels.current*3),y,config_channel_bar_active,str(channels.current))
      else:
        writexy(x+(channels.current*3),y,config_channel_bar_active,'S')
    if channels.current!=0:
      writexy(x+(channels.current*3),y,config_channel_bar_current,str(channels.current))
    else:
      writexy(x+(channels.current*3),y,config_channel_bar_current,'S')
      '''
  
  def redrawtopic(self):
    if channels.channels[channels.current].mode:
      s = '[+'+channels.channels[channels.current].mode+'] '+channels.channels[channels.current].topic
    else:
      s = channels.channels[channels.current].topic
    if len(s)>config_topic_title[3]:
      s = s[:config_topic_title[3]-4]+'...'
    writexylist(config_topic_title,s)
  
  def redrawchannel(self):
    global channels,USER
    channels.redraw = False
    self.redrawchannelbar()
   
    channel = channels.channels[channels.current]
    
    x1,y1,x2,y2 = config_chatscreen
    textcolor(7)
    
    height = y2-y1+1
        
    start = channel.chat_top
    left = 0
    a = 0
    while a<height:
      if (a+start)<len(channel.chat):
        color = int(hashlib.md5(channel.chat[a+start]['user'].encode(ENCODING, errors="ignore")).hexdigest(), 16) % 16
        if color == 0: color = 2
        text = channel.chat[a+start]['text']
        if config_chatscreen_timestamps:
          writexy(x1,y1+a,config_chatscreen_timestamp_color_att,channel.chat[a+start]['date'].strftime('%H:%M')+config_chatscreen_nick_char)
          
          writexy(x1+config_chatscreen_timestamp_width,y1+a,color,channel.chat[a+start]['user'][:config_chatscreen_nick_width].rjust(config_chatscreen_nick_width,' '))
          writexy(x1+config_chatscreen_timestamp_width+config_chatscreen_nick_width,y1+a,config_chatscreen_nick_color,config_chatscreen_nick_char)
          
          left = config_chatscreen_nick_width + config_chatscreen_timestamp_width+1
        else:
          writexy(x1,y1+a,color,channel.chat[a+start]['user'][:config_chatscreen_nick_width].rjust(config_chatscreen_nick_width,' '))
          writexy(x1+config_chatscreen_nick_width,y1+a,config_chatscreen_nick_color,config_chatscreen_nick_char)
          left = config_chatscreen_nick_width
          
        text = text.ljust(self.mcipadlen(text,config_chatscreen_text_width+config_chatscreen_timestamp_width),' ')
        
        if channel.chat[a+start]['seen']:
          #writexy(x1+config_chatscreen_nick_width+1,y1+a,config_chatscreen_normal,text)
          writexy(x1+left+1,y1+a,channel.chat[a+start]['color'],text)
        else:
          writexy(x1+left+1,y1+a,config_chatscreen_notseen,text)
        channel.chat[a+start]['seen']=True
      else:
        writexy(x1,y1+a,config_chatscreen_normal,' '.ljust(y2-y1,' '))
      a+=1
    channel.chat_index=len(channel.chat)-1
    
    x,y,a,o,c,h = config_chatscreen_more_up
    if channel.chat_top>0:
      writexy(x,y,a,c)
    else:
      writexy(x,y,o,h)
    x,y,a,o,c,h = config_chatscreen_more_down
    if channel.chat_top+height<len(channel.chat):
      writexy(x,y,a,c)
    else:
      writexy(x,y,o,h)
    
    #writexylist(config_topic_title,channels.channels[channels.current].topic)
    self.redrawtopic()
    #writexylist(config_channel_name,channels.channels[channels.current].name)
    if AREA == AREA_CHAT:
      x,y = config_chatscreen_gfx_hi
      writesprite(x,y,'chathi')
    else:
      x,y = config_chatscreen_gfx_lo
      writesprite(x,y,'chatlo')
      
    writecenter(config_channel_name[1],config_channel_name[2],' '+channels.channels[channels.current].name+' ')
    if channels.current!=0:
      writexylist(config_chatscreen_total_users,str(len(channels.channels[channels.current].users)))
    #writexy(1,25,13,'ind:'+str(channel.chat_index)+' //len:'+str(len(channel.chat))+ ' ::top'+str(channel.chat_top)+'::h:'+str(height))
    #writexylist(config_chatscreen_mynick,irc.nick)
    
  def reset_kbd(self):
    self.kb.text = ''
    self.kb.index = 0
    self.kb.position = 0
    
  def change_to_channel(self,cid,draw_nicks = True):
    global AREA, channels
    if channels.setactive(cid):
      channels.channels[cid].has_data = False
      self.clearchatscreen()
      self.redrawchannel()
      self.redrawchannelbar()
      if draw_nicks:
        self.redraw_nicks()
      
      if AREA == AREA_CHAT:
        x,y = config_chatscreen_gfx_hi
        writesprite(x,y,'chathi')
      else:  
        x,y = config_chatscreen_gfx_lo
        writesprite(x,y,'chatlo')
      #writexylist(config_topic_title,' '+channels.channels[channels.current].topic+' ')
      self.redrawtopic()
      writecenter(config_channel_name[1],config_channel_name[2],' '+channels.channels[channels.current].name+' ')
      self.kb.suggestions.clear()
      self.kb.suggestions.extend(self.create_suggestions())

  def load_aliases(self):
    global ALIASES
    if not os.path.isfile(datadir+'aliases.txt'): return False
    tmp = self.load_list(datadir+'aliases.txt')
    for item in tmp:
      if item and item[0] == '/':
        itemlist = item.split()
        ALIASES[itemlist[0].upper()] = ' '.join(itemlist[1:])
  
  def execute_alias(self,command,args):
    global ALIASES
    function = ALIASES[command]
    function = function.split(';')
    for func in function:
      #strip spaces in front of command... for a weird reason, strip doesn't work... !@#$#$!@#
      a = 0
      while True:
        if func[a] == ' ':
          a += 1
        else:
          func = func[a:]
          break
        
      if len(re.findall('\$\d', func)) > len(args):
        self.add_status_message('Missing paramaters for alias. (%s)' % func,color = config_chatscreen_error_att)
        self.add_status_message('regex> '+str(len(re.findall('$d', func))))
        self.add_status_message('args> '+str(len(args)))
        break
      
      # replace variables
      func = mysticvariables(func)
      
      if args:
        for i,arg in enumerate(args):
          func = func.replace('$'+str(i+1),args[i])
      else:
        self.add_status_message('alias> '+func)
      self.execute_command(func)
   
  
  def execute_command(self,command):
    global EXIT_COMMAND, channels, USER, NICKS_VISIBLE,AREA
    input_str = command
    if not input_str.startswith(config_command_prefix):
      if channels.current == 0:
        channels.channels[channels.current].addline('Server',mysticvariables(input_str),config_chatscreen_text_width,seen=True)
      else:
        #channels.channels[channels.current].addline(irc.nick,input_str,config_chatscreen_text_width,True)
        irc.send_message(mysticvariables(input_str))
      self.redrawchannel()
      self.redraw_nicks()
    else:
      cmdl = input_str.split()
      command = cmdl[0].upper()
      args = cmdl[1:]
    
      if (command == CMD['exit']) or command=='/!':
        irc.disconnect()
        writeln("Exiting Mystic IRC.")
        return False
      elif command == CMD['redrawnicks']:
        ui.redraw_nicks()
      elif command == CMD['redrawchan']:
        ui.redrawchannel()
      elif (command == CMD['join']):
        # Join the given channel.
        if (len(args) < 1):
          ui.add_status_message(HCMD['join'])
        else:
          if len(args)<2:
            irc.join(args[0],'')
          else:
            irc.join(args[0],args[1:])
      elif (command == CMD["names"]):
        # Ask server for a list of nicks in the channel. TODO: Remove this.
        irc.request_nicklist()
      elif command == CMD['quit']:
        irc.disconnect()
      elif command == CMD['whois']:
        if (len(args) < 1):
          ui.add_status_message(HCMD['nick'])
        else:
          irc.whois(args[0])
      elif (command == CMD['nick']):
        if (len(args) < 1):
          ui.add_status_message(HCMD['nick'])
        else:
          irc.set_nick(args[0])
      elif command == CMD['away']:
        if (len(args) < 1):
          self.add_status_message(HCMD['away'])
        else:
          irc.away(' '.join(args[0:]))
      elif command == CMD['motd']:
        irc.motd()
      elif command == CMD['topic']:
        if (len(args) < 1):
          self.add_status_message(HCMD['topic'])
        else:
          if channels.current!=0:
            irc.topic(channels.channels[channels.current].name, ' '.join(args[0:]))
          else:
            self.add_status_message('Cannot change topic in the Server window...')
      elif command == CMD['invite']:
        if (len(args) < 1):
          self.add_status_message(HCMD['invite'])
        elif (len(args) == 1):
          if channels.current!=0:
            irc.invite(args[0],channels.channels[channels.current].name)
        elif  (len(args) == 2):
            irc.invite(args[0],args[1])
      elif command == CMD['say']:
        irc.send_message(' '.join(args[0:]))
      elif command == CMD['msg']:
        if (len(args) < 2):
          self.add_status_message(HCMD['msg'])
        else:
          msg = ' '.join(args[1:])
          irc.send_private_message(args[0], msg)
      elif command == CMD['allchan']:
        for chan in channels.channels:
          if (chan.cid!=0):
            chan.addline(irc.nick,' '.join(args),config_chatscreen_text_width)
            irc.send("PRIVMSG %s :%s" % (chan.name, ' '.join(args)))
        ui.redrawchannel()
      elif command == CMD['part']:
        irc.part()
        self.redraw_input()
      elif command == CMD['disconnect']:
        irc.disconnect()
      elif command == CMD['raw']:
        irc.send(' '.join(args[0:]))
        self.add_status_message('Sent raw command: '+' '.join(args[0:]))
        self.redrawchannel()
      elif command in ALIASES:
        self.execute_alias(command,args)
      elif command == CMD['connect']:
        if not irc.connected: 
          if not irc.name: self.add_status_message('Could not connect. Set the NAME value first.')
          elif not irc.nick: self.add_status_message('Could not connect. Set the NICK value first.')
          else:
            if not args:
              args=[irc.server]
            if (len(args) == 1):
              if (args[0].count(":") == 1):
                server, port = args[0].split(':')
              else:
                server = args[0]
                port = 6667
              if port:
                self.add_status_message(server+' '+str(port))
                irc.connect(server, int(port))
              else:
                self.add_status_message("Port must be specified as an integer")
            else:
              self.add_status_message(HCMD['connect'])
        else:
          self.add_status_message('You are all ready connected!')
      #Setting program variables and options
      elif command == CMD['set']:
        if not args: self.add_status_message(HCMD['set'])
        else:
          if args[0].upper() == 'NICK':
            if len(args)>1:
              irc.nick = args[1]
              self.add_status_message('Nick changed to: '+irc.nick)
              self.create_suggestions()
              writexylist(config_chatscreen_mynick,irc.nick)
            else:
              self.add_status_message(HCMD['set'])
          elif args[0].upper() == 'NAME':
            if len(args)>1:
              irc.name = " ".join(args[1:])
              self.add_status_message('Name changed to: '+irc.name)
            else:
              self.add_status_message(HCMD['set'])
          elif args[0].upper() == 'QUITMSG':
            if len(args)>1:
              irc.quitMessage = " ".join(args[1:])
              self.add_status_message('Quit message changed to: '+irc.quitMessage)
            else:
              self.add_status_message(HCMD['set'])
          elif args[0].upper() == 'PARTMSG':
            if len(args)>1:
              irc.partMessage = " ".join(args[1:])
              self.add_status_message('Quit message changed to: '+irc.partMessage)
            else:
              self.add_status_message(HCMD['set'])
          else:
            self.add_status_message(HCMD['set'])
      elif command == CMD['help']:
        if args and (args[0] in HCMD):
          self.add_status_message(HCMD[args[0]])
        else:
          self.add_status_message(HCMD['help'])
      elif command == CMD['ver']:
        self.add_status_message(version,'MysticIRC')
      elif command == CMD['toggle_users']:
        NICKS_VISIBLE = not NICKS_VISIBLE
        self.redraw_nicks()
      elif command == CMD['CHAN0'] or command == '/S':
        self.change_to_channel(0,False)
      elif command == CMD['CHAN1']:
        self.change_to_channel(1)
      elif command == CMD['CHAN2']:
        self.change_to_channel(2)
      elif command == CMD['CHAN3']:
        self.change_to_channel(3)
      elif command == CMD['CHAN4']:
        self.change_to_channel(4)
      elif command == CMD['CHAN5']:
        self.change_to_channel(5)
      elif command == CMD['CHAN6']:
        self.change_to_channel(6)
      elif command == CMD['CHAN7']:
        self.change_to_channel(7)
      elif command == CMD['CHAN8']:
        self.change_to_channel(8)
      elif command == CMD['CHAN9']:
        self.change_to_channel(9)
      elif command == CMD['?']:
        self.show_help_file()
        self.draw_main()
        self.redrawchannel()
        self.redrawtopic()
        self.redrawchannelbar()
        self.redraw_nicks()
      else:
        irc.othercommand(command[1:],args)
        #statusbar(command+', Unknown command. Try: /help')
        #ui.add_status_message(command+', Unknown command. Try: /help')
    return True
    
  def run(self):
    global EXIT_COMMAND, channels, USER, NICKS_VISIBLE,AREA
    
    #dispfilebg(datadir + config_background)
    self.draw_main()
    self.redrawchannelbar()
    #self.redraw_nicks()
    
    self.kb.x = config_input[0]
    self.kb.y = config_input[1]
    self.kb.text = ''
    self.kb.show()
    #start keyboard input thread
    #inputQueue = queue.Queue()
    #inputThread = threading.Thread(target=self.read_kbd_input, args=(inputQueue,), daemon=True)
    #inputThread.start()
    
    while (True):
      try:
        irc.poll()
        self.kb.getstrxy_nonblock()
        if self.inputstring!='':
          input_str = self.inputstring
          self.reset_kbd()
          self.history.append(input_str)
          self.history_index = 0
          self.inputstring = ''
          
          if not self.execute_command(input_str):
            break
            
        time.sleep(0.01)
      except KeyboardInterrupt:
        break
  
  def mcipadlen(self,text,width=80):
    return width + (len(text)-mcilen(text))

  def show_help_file(self):
    if not os.path.isfile(datadir+'help.ans'):
      self.add_status_message('Help file (help.ans) is missing.',color = config_chatscreen_error_att)
    self.clearchatscreen()
    lines = self.load_list(datadir+'help.ans')
    index = 0
    keyb = self.kb.kb
    x1,y1,x2,y2 = config_chatscreen
    wdt = x2-x1+1
    writexylist(config_topic_title,' Instructions, Usage and Help for Mystic IRC ')
    statusbar('Press ESC when done, to return back...')
    
    while True:
      
      i = 0
      while i<config_chatscreen_text_height:
        if index+i<len(lines):
          actuall = self.mcipadlen(lines[index+i],wdt)
          writexy(x1,y1+i,config_chatscreen_normal,lines[index+i].ljust(actuall,' '))
        else:
          writexy(x1,y1+i,config_chatscreen_normal,' '*config_chatscreen_text_height)
        i+=1
      
      c = keyb.getch()
      if len(c)>1:
        c = c[1:]
        if c == xinput.KBHOME: #home
          index = 0
        elif c == xinput.KBUP: #up
          index -= 1
          if index<0: index = 0
        elif c == xinput.KBDOWN: #down
          index += 1
          if index+config_chatscreen_text_height-1 > len(lines):
            index = len(lines)-config_chatscreen_text_height
            if index<0: index = 0
        elif c == xinput.KBEND: #end
          index = len(lines)-config_chatscreen_text_height
          if index<0: index = 0
        elif c == xinput.KBLEFT or c == xinput.KBPAGE_UP: #left
          index -= config_chatscreen_text_height
          if index<0: index = 0
        elif c == xinput.KBRIGHT or c == xinput.KBPAGE_DOWN: #right
          index += config_chatscreen_text_height
          if index+config_chatscreen_text_height-1 > len(lines):
            index = len(lines)-config_chatscreen_text_height
            if index<0: index = 0
      elif len(c) == 1:
        if c == xinput.KBESC:
          break
        elif c == xinput.KBENTER:
          index += config_chatscreen_text_height
          if index+config_chatscreen_text_height-1 > len(lines):
            index = len(lines)-config_chatscreen_text_height
            if index<0: index = 0
          
        

  def load_list(self, s):
    # A utility function that loads each line from a given file in to a list.
    try:
      with open(s,encoding=ENCODING) as f:
        lines = f.readlines()
        f.close()
    except IOError:
      return []
    return [x.strip() for x in lines]

  def censor(self, s):
    # Replace bad words with an equal length string of asterisks
    for tag in self.badwords:
      s = s.replace(tag, config_mci_censor+"@" * len(tag)+config_mci_reset_text)
    return s
    
  def add_private_channel(self,name):
    global channels,datadir
    cid = channels.add(name)
    channels.changetopic(cid,'Private Chat')
    channels.channels[cid].filename = datadir+'logs'+os.sep+channels.channels[cid].filename
    return cid
    

def initialize():
  global channels,sprites,irc
  if os.path.isfile(maindir + 'history.log'):
    os.remove(maindir + 'history.log')
  channels = ircchanellist()
  channels.chat_height = config_chatscreen[3]-config_chatscreen[1]+1
  channels.add('Server')
  channels.changetopic(0,'Server Messages')
  channels.current = 0
  channels.channels[channels.current].filename = datadir+'logs'+os.sep+channels.channels[channels.current].filename  
  channels.channels[channels.current].active = True
  sprites = loadsprites(datadir+'sprites.ans')
  
  irc = IRC()
  
  
def deinitilize():
  for chan in channels.channels:
    chan.savechat()
  clrscr()

init()
initialize()
clrscr()
ui = UserInterface()
ui.kb.suggestions.extend(ui.create_suggestions())
ui.load_aliases()
statusbar('Welcome to Mystic IRC...')
ui.run()
deinitilize()
