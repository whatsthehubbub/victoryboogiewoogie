# How and what on the front-end

All custom CSS that lies on top of the Bootstrap framework can be found in *custom.less*. The code is separated into the following parts: 
- Chromeframe
- Header
- Masthead
- Calendar
- Sign-in
- Prelaunch
- Summary
- Main
- Content
- Home, latest
- Home, characters
- Summary list
- Itemlist
- Character info
- Characterlist
- Player detail
- Player edit
- Item detail
- Create item
- Entry queue
- Notifications
- Topic list
- Colofon
- Footer

Currently, the *responsive.less* file (and all associated @imports) are not being used. It is left in the folder for possible future use, though.

## Framework in use
- [Bootstrap](http://twitter.github.com/bootstrap/ "Twitter Bootstrap")
- [LESS](http://lesscss.org/ "LESS")

## Software that comes in handy
*bootstrap.less* (which @imports the bootstrap framework and the customised *custom.less*) is automatically concatenated and minified with [CodeKit](http://incident57.com/codekit/ "CodeKit by Incident57")—and outputed as *bootstrap.min.css*.