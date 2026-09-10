# Minecraft and Unreal Engine 4 crossplay prototype

## Tested on
Unreal Engine 4.26.2
Minecraft Java 26.2 

## May work on more versions of Minecraft and Unreal Engine


#### Required 

- **VaRest (Plugin for Unreal Engine)**
- **Python 3.12**
- **BotMine (Library for Python)**
- **Java**
- **Minecraft Java Edition**
- **Unreal Engine**
- **Minecraft Java Edition Server**

1. **Setting up directories**
- Create a folder with any name you want
- Inside that folder put the 2 python files **(server.py and bot.py)**
- In the folder create a folder called server
- Inside the server folder place your Minecraft Java server and name it server.jar

2. **Setting up the Minecraft Server**
- Open Command Prompt inside the directory you have server.py inside
- Type ```python server.py```
- Agree to the eula to set up the server
- Inside the server folder you will see **server.properties** open it
- Set ```allow-flight``` to true
- Set ```online-mode``` to false

3. **Inside Unreal Engine**
- Add the BP_Crossplay actor into your content folder
- Drag BP_Crossplay actor to the viewport
