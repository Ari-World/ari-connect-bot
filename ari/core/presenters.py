import discord


def build_guild_welcome_embed(guild: discord.Guild, bot_user_name: str, guild_count: int) -> discord.Embed:
    """The message posted to a newly-joined guild's first text channel."""
    return discord.Embed(
        title=guild.name,
        description=(
            f"💖 **Thank you for inviting {bot_user_name}!!**\n\n"
            "__**A brief intro**__\n"
            "Hey Everyone! My main purpose is creating an Inter Guild / Server Connectivity "
            "to bring the world closer together!\n"
            "Hope you'll find my application useful! Thankyouuu~\n\n"
            "Type `a!about` to know more about me and my usage!\n\n"
            "**__Servers Connected__**\n"
            f"{guild_count}\n\n"
        ),
    )


def build_guild_join_admin_notice_embed(guild: discord.Guild) -> discord.Embed:
    """Posted to the admin log channel whenever the bot joins a new guild."""
    return discord.Embed(
        description=(
            f"Bot has been added to a new server {guild.name}\n\n"
            f"Added by {guild.owner.global_name} ({guild.owner.id})"
        )
    )
