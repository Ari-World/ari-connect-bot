from discord.ext import commands

class GlobalChatMods(commands.Cog):
  def __init__(self, bot:commands.Bot):
    self.bot = bot
    self.openworld_cog = bot.get_cog("OpenWorldServer")
    self.private_lobbies = self.openworld_cog.private_lobbies
    self.server_lobbies = self.openworld_cog.server_lobbies
    self.create_guild_document = self.openworld_cog.create_guild_document
    self.allowed_server_id = 939025934483357766

  @staticmethod
  async def is_allowed_server(ctx):
      instance = ctx.cog
      return ctx.guild and ctx.guild.id == instance.allowed_server_id


  @commands.hybrid_command(name="global_mute", description="Mutes a user from talking in the global world channel")
  @commands.check(is_allowed_server)
  async def gmute(self, ctx, user_id):
      user_id = int(user_id)
      log_channel = self.bot.get_channel(979962928390365284)
      muted_collection = self.bot.db.muted_collection
      muted_doc = await muted_collection.find_one({"user_id": user_id})

      if muted_doc:
          await ctx.send(f"The mentioned UserID `{user_id}` is already blacklisted.")
      else:
          user = await self.bot.fetch_user(user_id)
          if user:
              username_with_discriminator = f"{user.name}#{user.discriminator}"
              await muted_collection.insert_one({"user_id": user_id, "username_with_discriminator": username_with_discriminator})
              await ctx.send(f"The UserID `{user_id}` ({username_with_discriminator}) is successfully blacklisted!")
              await log_channel.send(f"The UserID `{user_id}` ({username_with_discriminator}) is successfully blacklisted!")
          else:
              await ctx.send("Failed to fetch user.")

  @commands.hybrid_command(name="global_unmute", description="Unmutes a user from talking in the global world channel")
  @commands.check(is_allowed_server)
  async def gunmute(self, ctx, user_id):
      user_id = int(user_id)
      log_channel = self.bot.get_channel(979962954164359229)
      muted_collection = self.bot.db.muted_collection
      muted_doc = await muted_collection.find_one({"user_id": user_id})

      if not muted_doc:
          await ctx.send(f"The mentioned UserID `{user_id}` is not in the blacklist.")
      else:
          username_with_discriminator = muted_doc["username_with_discriminator"]
          await muted_collection.delete_one({"user_id": user_id})
          await ctx.send(f"Successfully removed the UserID `{user_id}` ({username_with_discriminator}) from the blacklist")
          await log_channel.send(f"Successfully removed the UserID `{user_id}` ({username_with_discriminator}) from the blacklist")

  @commands.command(name='admin_connect', description='Admin command to connect a server and channel')
  @commands.has_permissions(administrator=True)
  async def admin_connect(self, ctx, server_id: int, channel_id: int, lobby_name: str):
    existing_guild = await self.bot.db.guilds_collection.find_one({"server_id": server_id})
    if existing_guild:
        channels = existing_guild.get("channels", [])
        if any(channel.get("channel_id") == channel_id for channel in channels):
            await ctx.send("This channel is already registered for Open World Chat.")
            return

    server = self.bot.get_guild(server_id)
    if not server:
        await ctx.send(":no_entry: Invalid server ID.")
        return

    server_name = server.name

    if lobby_name not in self.server_lobbies:
        await ctx.send(":no_entry: Lobby name Invalid or Private.")
        return

    success = await self.create_guild_document(server_id, channel_id, server_name, lobby_name)

    if success:
        await ctx.send(f":white_check_mark: Server with ID {server_id} and channel with ID {channel_id} have been successfully registered for Open World Chat.")
        await ctx.send(f":earth_asia: Selected lobby: {lobby_name}")
    else:
        await ctx.send(":no_entry: Failed to create guild document.")
      
async def setup(bot:commands.Bot):
    await bot.add_cog(GlobalChatMods(bot))