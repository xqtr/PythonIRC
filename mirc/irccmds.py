CMD = dict()
CMD['exit'] = '/EXIT'
CMD['help'] = '/HELP'
CMD['connect'] = '/CONNECT'
CMD['disconnect'] = '/DISCONNECT'
CMD['toggle_users'] = '/TOGGLENICKS'
CMD['join'] = '/JOIN'
CMD['allchan'] = '/ALLCHAN'
CMD['part'] = '/PART'
CMD['msg'] = '/MSG'
CMD['nick'] = '/NICK'
CMD['names'] = '/NAMES'
CMD['whois'] = '/WHOIS'
CMD['quit'] = '/QUIT'
CMD['away'] = '/AWAY'
CMD['topic'] = '/TOPIC'
CMD['motd'] = '/MOTD'
CMD['invite'] = '/INVITE'
CMD['raw'] = '/RAW'
CMD['say'] = '/SAY'
CMD['me'] = '/ME'

CMD['redrawnicks'] = '/REDRAWNICKS'
CMD['redrawchan'] = '/REDRAWCHAN'
CMD['?'] = '/?'
CMD['CHAN1'] = '/1'
CMD['CHAN2'] = '/2'
CMD['CHAN3'] = '/3'
CMD['CHAN4'] = '/4'
CMD['CHAN5'] = '/5'
CMD['CHAN6'] = '/6'
CMD['CHAN7'] = '/7'
CMD['CHAN8'] = '/8'
CMD['CHAN9'] = '/9'
CMD['CHAN0'] = '/0'
CMD['ver'] = '/VER'
CMD['set'] = '/SET'

HCMD = dict()
HCMD['exit'] = 'Close connection and Exit the program.'
HCMD['ver'] = 'Display version information'
HCMD['help'] = 'Display help for a command. Usage: /help <command>'
HCMD['h'] = HCMD['help']
HCMD['join'] = 'Join a channel. Usage: /join <channel_name>'
HCMD['part'] = 'Leave a channel. Usage: /part <channel_name>'
HCMD['msg'] = ['Send message to a user or channel. Usage:',
               '/msg <user> <message>',
               '/msg <channel_name> <message>']
HCMD['nick'] = 'Change your nick to a new one. Usage: /nick <new_nick>'
HCMD['names'] = 'Ask server for a list of nicks in the channel'
HCMD['whois'] = 'Info about a user. Usage: /whois <username>'
HCMD['quit'] = 'Quit and disconnect from server.'
HCMD['away'] = 'Inform other users that you are away. Usage: /away <reason>'
HCMD['topic'] = 'Change topic of channel. Usage: /topic <new_topic>'
HCMD['motd'] = 'Get the Message of The Day (MOTD) from server.'
HCMD['invite'] = 'Invite a user to a channel. Usage: /invite <user> <channel>'
HCMD['raw'] = 'Send a RAW IRC command to the server. Usage: /raw <command>'
HCMD['say'] = 'A command to put text in current channel, as you.'
HCMD['me'] = '!'
HCMD['allchan'] = 'Send message to all open channels. Usage: /allchan <msg>'

HCMD['set'] = ['---','Set variables for use in the program and/or IRC server.',
               'Usage: /set <cmd> <value>',
               'Commands:',
               'NICK: Set nickname to use in IRC',
               'NAME: Set true name of user to use in IRC',
               'QUITMSG: Set a message to show when quitting server',
               'PARTMSG: Set a message to show when leaving a channel',
               '---']
HCMD['connect'] = 'Connect to IRC server. Usage: /connect <host:port>'
HCMD['disconnect'] = 'Disconnect from IRC server.'

HCMD['redrawnicks'] = '/redrawnicks'
HCMD['redrawchan'] = '/redrawchan'
