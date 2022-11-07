from fileinput import filename
import discord
from discord import Intents
from discord.ext import commands
from dotenv import load_dotenv
from PIL import Image
import warnings
import os
import io
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation

load_dotenv()

stability_api = client.StabilityInference(
    key=os.environ['STABLE_DIFFUSION_TOKEN'],
    verbose=True,
)

intents = Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    description="Make art.",
    intents=intents,
)

IMAGE_DIMENSIONS = (512,512)


@bot.command()
async def dream(ctx, *, prompt):
    await ctx.message.delete()
    msg = await ctx.send(f"Generating...")
    
    generated_images = []
    answers = stability_api.generate(
        prompt=prompt, 
        width=IMAGE_DIMENSIONS[0], 
        height=IMAGE_DIMENSIONS[1],
        samples=1
    )
    for resp in answers:
        for artifact in resp.artifacts:
            if artifact.finish_reason == generation.FILTER:
                warnings.warn(
                    "Your request activated the API's safety filters and could not be processed."
                    "Please modify the prompt and try again.")
                await msg.edit(content="You have triggered the filter, please try again")
            if artifact.type == generation.ARTIFACT_IMAGE:
                img = Image.open(io.BytesIO(artifact.binary))
                generated_images.append(img)
    
    if len(generated_images):
        await msg.edit(content=f"Ready. Sending Files...")
        attachments = []
        for img in generated_images:
            arr = io.BytesIO()
            img.save(arr, format='PNG')
            arr.seek(0)
            file = discord.File(arr, filename='SPOILER_art.png')
            attachments.append(file)
        await msg.edit(content=f"Ergebnis für {ctx.message.author.mention}\nPrompt: ||`{prompt}`||", attachments=attachments)
        await msg.add_reaction("⭐")
                
                
@bot.command()
async def react(ctx):
    def check(reaction, user):
        return user == ctx.message.author

    reaction = await bot.wait_for("reaction_add", check=check)
    if reaction[0] == "⭐":
        await ctx.send(f"Dieses Kunstwerk wurde von dir markiert.")
        
@bot.command()        
async def results(ctx):
    channel = ctx.channel
    # TODO für jeden Benutzer die letzte Nachricht raussuchen
    # TODO Befehl "!newround" beachten.
    # TODO Bilder zu einer Kollage zusammenbauen und ausgeben
    async for message in channel.history(limit=200):
        for reaction in message.reactions:
            if reaction.emoji == "⭐":
                users = [user async for user in reaction.users() if user in message.mentions]
                if len(users) > 0:
                    print("SUCCESS!")
                    print(message)
                    await message.channel.send("Das hier nehmen wir :)", reference=message)
                    print(message.attachments)
                    
            
            
    

bot.run(os.environ["DISCORD_TOKEN"])
