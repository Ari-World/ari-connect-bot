# Ari Connect - Your Ultimate Global Chat Hub

🚀 Say goodbye to server-hopping and hello to seamless connectivity! Our specially designed bot brings gaming communities together like never before.

[Join and show some support](https://discord.gg/HnjyK33cJp)

[Inv the bot](https://discord.com/oauth2/authorize?client_id=895242125208342548)
### Features Include:
- Global Chat Compatibility: Connect with gamers worldwide in one place.
- Anywhere, Anytime Access: Stay connected on-the-go.
- Private Lobbies: Secure spaces for inter-server conversations

## Installation
### Prerequisite
- Python 3.12.*
- pip 24.0

Before running all make sure that you have installed all modules that we'll be using, to do that run this command.
``` cmd
pip install -r requirements. txt
```

After that make sure that you have a `.env `file at the same level of the `main.py`.
How do I know the values for the *.env* file?
- Checkout `plugins > config.py` and check the returned values, you'll be able to see what are needed.
- To know the keys, you'll find in the config `os.getenv(<this is the key>)`
if you have now defined the config, put those keys with corresponding values, e.g.
```.env
DISCORD_API_TOKEN = <put your env file herer>

DISCORD_COMMAND_PREFIX = <desired prefix>

MONGO_DB_URL = <mongodb datbase url>

```
### License
