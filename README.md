# PythonIRC
A python3 irc client with ANSI graphics

THis is a Python3 IRC client, that can be used in a terminal like Gnome Terminal or even as a DOOR app, from inside a BBS server, like Mystic or Synchronet. It supports ANSI graphics and has many features, like word/command auto completion, logging files, bad words censorship and more.

To run from a Mystic BBS, use the following MPS script:
```
ses cfg;

begin
menucmd('DD','/home/xxx/mys47b/doors/mirc/mirc.py')

end;
```

The project is abandonded, until i find some free time, but the client is usable. The only thing is that it may crash, if you use the /MODE IRC command, which is not 100% implemented and that's why crashing. Feel free to correct the code or add more features to your liking.

As always, respect the license, which is GPL3!
