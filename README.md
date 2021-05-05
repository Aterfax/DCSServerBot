# Documentation
DCSServerBot lets you interact between Discord and DCS.
The bot has to be installed on the same machine that runs DCS or at least in the same network.
The following two main features are supported:

## DCS Server Remote Control
Control DCS servers in your local network via Discord commands.
The following commands are supported:
Command|Parameter|Description
-------|-----------|--------------
.status||(Admin only) Lists all registered DCS servers. They will auto-register on startup.
.mission||Information about the active mission.
.briefing/.brief||Shows the description / briefing of the running mission.
.players||Lists the players currently active on the server.
.list||Lists all missions with IDs available on this server (same as WebGUI).
.add|miz-file|Adds a specific mission to the list of missions. Has to be in DCS_HOME/Missions
.delete|ID|Deletes the mission with this ID from the list of missions.
.load|ID|Load a specific mission by ID.
.restart||Restarts the current mission.
.chat|message|Send a message to the DCS ingame-chat.
.ban|@member or ucid|Bans a specific player either by his Discord ID or his UCID
.unban|@member or ucid|Unbans a specific player either by his Discord ID or his UCID
.bans||Lists the current bans.

## User Statistics
Gather statistics data from users and display them in a user-friendly way in your Discord.
The following commands are supported:
|Command|Parameter|Description|
|-------|-----------|--------------|
|.link|@member or ucid|Sometimes users can't be linked automatically. That is a manual workaround.|
|.statistics/.stats|[@member]|Display your own statistics or that of a specific member.|
|.highscore/.hs||Shows the players with the most playtime or most kills in specific areas (CAP/CAS/SEAD/Anti-Ship)|

## Installation
First of all, download the latest release version and extract it somewhere on your server, where it has write access.
Make sure that this directory can only be seen by yourself and is not exposed to anybody outside via www etc.

### Prerequisites
You need to have python 3.8 or higher installed.
The python modules needed are listed in requirements.txt and can be installed with ```pip3 install -r requirements.txt```

### Discord Token
The bot needs a unique Token per installation. This one can be obtained at http://discord.com/developers.
Create a "New Application", add a Bot, select Bot from the left menu, give it a nice name and icon, press "Copy" below "Click to Reveal Token".
Now your Token is in your clipboard. Paste it in dcsserverbot.ini in your config-directory.
Both "Priviledged Gateway Intents" have to be enabled on that page.
To add the bot to your Discord guild, go to OAuth2, select "bot" in the OAuth2 URL Generator, select the following permissions:
_Send Messages, Manage Messages, Embed Links, Attach Files, Read Message History, Add Reactions_
Press "Copy" on the generated URL, paste it into the browser of your choice, select the guild the bot has to be added to - and you're done!
For easier access to channel IDs, enable "Developer Mode" in "Advanced Settings" in Discord.

### Bot Configuration
The bot configuration is held in config/dcsserverbot.ini. The following parameters can be used to configure the bot:
Parameter|Description
-----------|--------------
OWNER|The Discord ID of the Bot's owner (that's you!). If you don't know your ID, go to your Discord profile, make sure "Developer Mode" is enabled under "Advanced", go to "My Account", press the "..." besides your profile picture and select "Copy ID"
TOKEN|The token to be used to run the bot. Can be obtained at http://discord.com/developers.
COMMAND_PREFIX|The prefix to be used. Default is '.'
HOST|IP the bot listens on for messages from DCS. Default is 127.0.0.1, to only accept internal communication on that machine.
PORT|UDP port, the bot listens on for messages from DCS. Default is 10081. **__Don't expose that port to the outside world!__**
DCS_HOME|The main configuration directory of your DCS server installation (for Hook installation). Keep it empty, if you like to place the Hook by yourself.
GREETING_MESSAGE_MEMBERS|A greeting message, that people will receive in DCS, if they get recognized by the bot as a member of your discord.
GREETING_MESSAGE_UNKNOWN|A greeting message, that people will receive in DCS, if they or not recognized as a member of your discord.

### DCS/Hook Configuration
The DCS World integration is done via a Hook. This is being installed automatically.
You need to configure the Hook upfront in Scripts/net/DCSServerBot/DCSServerBotConfig.lua
Parameter|Description
-----------|--------------
..HOST|Must be the same as HOST in the Bot configuration.
..SEND_PORT|Must be the same as PORT in the Bot configuration (default 10081).
..RECV_PORT|Must be a unique value > 1024 of a port that is not in use on your system. Must be unique for every DCS server instance configured. **__Don't expose that port to the outside world!__**
..CHAT_CHANNEL|The ID of the Discord chat channel to be used for the server. Must be unique for every DCS server instance configured.
..STATUS_CHANNEL|The ID of the Discord status channel to be used for the server. Must be unique for every DCS server instance configured.
..ADMIN_CHANNEL|The ID of the Discord status channel to be used for the server. Must be unique for every DCS server instance configured.

### Discord Configuration
The following roles have to be set up in your Discord guild:
Role|Description
-------|-----------
DCS|People with this role are allowed to chat, check their statistics and gather information about running missions and players.
DCS Admin|People with this role are allowed to restart missions and managing the mission list.

### **ATTENTION**
_One of the main concepts of this bot it to bind people to your discord. Therefor, this solution is not very suitable for public servers._

The bot automatically bans / unbans people from the configured DCS servers, as soon as they leave / join the configured Discord guild.
If you don't like that feature, remove the methods _on_member_join()_ and _on_member_remove()_ from cogs/dcs.py.

## TODO
Things to be added in the future:
* Database versioning / update handling
* Improve mission handling (list local missions, etc.)
* More statistics
* Ability to combine stats from different bots (if multiple servers are being run in different locations)
* Make ban/unban on leave/join configurable

## Credits
Thanks to the developers of the awesome solutions [HypeMan](https://github.com/robscallsign/HypeMan) and [perun](https://github.com/szporwolik/perun), that gave me the main ideas to this solution.
I gave my best to mark parts in the code to show where I copied some ideas or even code from you guys. Hope that is ok.
Both frameworks are much more comprehensive than what I did here, so you better check those out before you look at my simple solution.
