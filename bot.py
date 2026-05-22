import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread

# ==========================================
# 1. FLASK WEB SERVER (For Render Keep-Alive)
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "Bot is online and running!"

def run_server():
    # Render requires binding to a dynamic port
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_server)
    t.start()

# ==========================================
# 2. DISCORD BOT SETUP
# ==========================================
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.default())

    async def setup_hook(self):
        # Syncs the slash commands to Discord
        await self.tree.sync()
        print("Slash commands synced!")

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')

bot = MyBot()

# ==========================================
# 3. UI COMPONENTS (Buttons & Dropdowns)
# ==========================================

class AudienceMemberSelect(discord.ui.View):
    def __init__(self, post_content: str):
        super().__init__(timeout=120)
        self.post_content = post_content

    @discord.ui.select(
        cls=discord.ui.UserSelect, 
        placeholder="Select members for the private thread...", 
        min_values=1, 
        max_values=10
    )
    async def select_audience(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        try:
            # Create the private thread attached to the channel where the command was run
            thread = await interaction.channel.create_thread(
                name=f"Private Post by {interaction.user.display_name}",
                type=discord.ChannelType.private_thread,
                reason="User created a private audience post"
            )
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to create private threads in this channel!", ephemeral=True)
            return

        # Add the selected users to the thread
        for member in select.values:
            await thread.add_user(member)

        # Post the message inside the thread
        embed = discord.Embed(description=self.post_content, color=discord.Color.purple())
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        await thread.send(embed=embed)

        # Confirm success to the user who ran the command
        await interaction.response.edit_message(content=f"Private thread created successfully! Check {thread.mention}", view=None)


class PostTypeView(discord.ui.View):
    def __init__(self, post_content: str):
        super().__init__(timeout=60)
        self.post_content = post_content

    @discord.ui.button(label="Publicize", style=discord.ButtonStyle.green, emoji="🌍")
    async def publicize_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Post directly to the channel
        embed = discord.Embed(description=self.post_content, color=discord.Color.blue())
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        
        await interaction.channel.send(embed=embed)
        await interaction.response.edit_message(content="Your post is now public in this channel!", view=None)

    @discord.ui.button(label="Select Audience", style=discord.ButtonStyle.primary, emoji="👥")
    async def private_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Swap out the buttons for the User Select dropdown
        view = AudienceMemberSelect(self.post_content)
        await interaction.response.edit_message(content="Who do you want to invite to see this post?", view=view)


# ==========================================
# 4. THE SLASH COMMAND
# ==========================================
@bot.tree.command(name="post", description="Create a post and choose who can see it")
async def create_post(interaction: discord.Interaction, message: str):
    view = PostTypeView(message)
    # The initial response MUST be ephemeral so others don't see the configuration process
    await interaction.response.send_message("How would you like to share this post?", view=view, ephemeral=True)


# ==========================================
# 5. STARTUP
# ==========================================
if __name__ == "__main__":
    # Start the Flask web server
    keep_alive()
    
    # Start the Discord bot using the token stored in Render's Environment Variables
    # DO NOT put your actual token string in this file if you are pushing to GitHub!
   # token = os.environ.get("DISCORD_TOKEN")
   # Start the Discord bot using the token stored in Render's Environment Variables
   token = os.environ.get("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("ERROR: No Discord token found in environment variables.")