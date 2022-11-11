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
import random
from utils import create_collage, combine_images, get_image_from_grid, pil_image2discord_image, add_text
import re
from datetime import datetime, timedelta

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

IMAGE_DIMENSIONS = (640,448)

number_reactions = {
    "1️⃣": (0,0),
    "2️⃣": (0,1),
    "3️⃣": (1,0),
    "4️⃣": (1,1),
}

@bot.command()
async def dream(ctx, *, prompt):
    print(f"{ctx.message.author}: dream")
    await ctx.message.delete()
    msg = await ctx.send(f"{ctx.message.author.mention}\nErschaffe Kunst ...")
    
    generated_images = []
    
    # samplers:
    # SAMPLER_K_DPM_2_ANCESTRAL, SAMPLER_K_EULER_ANCESTRAL 
    answers = stability_api.generate(
        prompt=prompt, 
        width=IMAGE_DIMENSIONS[0], 
        height=IMAGE_DIMENSIONS[1],
        sampler=generation.SAMPLER_K_EULER_ANCESTRAL,
        guidance_preset=generation.GUIDANCE_PRESET_FAST_GREEN,
        cfg_scale=35,
        samples=4,
    )
    for resp in answers:
        for artifact in resp.artifacts:
            if artifact.finish_reason == generation.FILTER:
                warnings.warn(
                    "Your request activated the API's safety filters and could not be processed."
                    "Please modify the prompt and try again.")
                await msg.edit(content=f"{ctx.message.author.mention}\nDeine Eingabe verstößt gegen die Sicherheitsfilter der KI. Versuche es noch einmal.")
            if artifact.type == generation.ARTIFACT_IMAGE:
                img = Image.open(io.BytesIO(artifact.binary))
                generated_images.append(img)
    
    if len(generated_images):
        await msg.edit(content=f"{ctx.message.author.mention}\nFertig. Sende Dateien...")
        attachments = []
        
        grid = combine_images(generated_images)

        arr = io.BytesIO()
        grid.save(arr, format='JPEG', quality=75)
        arr.seek(0)
        file = discord.File(arr, filename="art.jpg")
        attachments.append(file)
        
        await msg.edit(content=f"{ctx.message.author.mention}\nDeine Eingabe: ```{prompt}```", attachments=attachments)
        
        for r in number_reactions.keys():
            await msg.add_reaction(r)
        await msg.add_reaction("👁️")
                
                        
@bot.command()        
async def results(ctx):
    print(f"{ctx.message.author}: results")
    await ctx.message.delete()

    msg = await ctx.send("Suche nach Einsendungen...")
    
    images = []
    
    theme = "???"
    start_date = datetime.now() - timedelta(hours=1)
    
    async for message in ctx.channel.history(limit=200, oldest_first=False):
        if "Neue Runde" in message.content:
            match = re.search("\*\*(.*)\*\*", message.content)
            if match is not None:
                theme = match.group(1)
                start_date = message.created_at
                
    print(f"Start date: {start_date}")
            
    for channel in ctx.guild.channels:
        if not channel.name.startswith("battle_"):
            continue
            
        print(f"Searching in {channel.name}")
        
        entry_found = False
        
        async for message in channel.history(limit=200, oldest_first=False, after=start_date):
        
            if not len(message.attachments) or not len(message.mentions):
                continue
                
            if entry_found:
                break
                
            for reaction in message.reactions:
                # mentioned user has reacted to this messages with a number emoji
                if reaction.emoji in number_reactions.keys() and len([user async for user in reaction.users() if user == message.mentions[0]]):
                    
                    row, col = number_reactions[reaction.emoji]
                    file = await message.attachments[0].to_file()
                    image = get_image_from_grid(Image.open(file.fp), col, row, IMAGE_DIMENSIONS[0], IMAGE_DIMENSIONS[1])
                    
                    prompt = "???"
                    match = re.search("```(.*)```", message.content)
                    if match is not None:
                        prompt = match.group(1)
                    
                    images.append(
                        (image, prompt)
                    )
                    entry_found = True
                    break
    if len(images) > 0:
        images = random.sample(images, len(images))
        collage = create_collage(images, theme)
        await msg.edit(content="Die Ergebnisse sind da. Jetzt darf abgestimmt werden!", attachments=[pil_image2discord_image(collage, "results.jpg")])
    else:
        await msg.edit(content="Keine Einsendungen gefunden. Bilder müssen mit einer Nummer markiert werden!")
 
 
@bot.command()        
async def start(ctx, *, theme=""):
    print(f"{ctx.message.author}: start")
    await ctx.message.delete()
    if not theme:
        themes = []
        with open("themes.txt", "r") as themes_file:
            themes = [line.rstrip() for line in themes_file]
        theme = random.choice(themes)
    await ctx.send(f"Neue Runde wurde gestartet. \n\nDas Thema lautet: \n🏆 **{theme}** 🏆\n\n➟ Erstelle Kunstwerke mit `!dream`\n➟ Beende die Runde mit `!results`")
   

   
@bot.command()        
async def h(ctx):
    await ctx.send(
        "**!start [THEMA]** - Starte eine neue Runde. Wenn mein Thema angegeben wird, wird ein zufälliges gewählt.\n\n"
        "**!dream [Stichworte]** - Erstelle vier Kunstwerke zu Stichworten deiner Wahl. "
        "Wähle eins einem Nummer-Emoji aus, um es einzureichen. Das eingereichte Bild kann du mit 👁️ anzeigen lassen.\n\n"
        "**!results** - Zeige eine Zusammenfassung der Ergebnisse an. Es wird für jeden Benutzer nur das zuletzt mit einer Nummer markierte Bild genommen."
    )
    

@bot.command()
async def clear(ctx, amount=0):
    if not amount:
        await ctx.send("Wie viele Nachrichten sollen gelöscht werden?")
    else:
        await ctx.channel.purge(limit=amount)


@bot.event
async def on_ready():
    print("Bot is ready")
            
            
@bot.event
async def on_reaction_add(reaction, user):
    
    if user.bot:
        return
    
    if reaction.emoji in number_reactions.keys():
    
        if user not in reaction.message.mentions:
            await reaction.remove()
            return

        for r in reaction.message.reactions:
            if r.emoji == reaction.emoji:
                continue
            if user in [u async for u in r.users()]:
                print("remove", r.emoji)
                await r.remove(user)
            
    if reaction.emoji == "👁️":
        await reaction.remove(user)
        nums = []
        for r in reaction.message.reactions:
            if r.emoji not in number_reactions.keys():
                continue
            if user in [u async for u in r.users()]:
                nums.append(r.emoji)
                
        print(nums)

        if len(nums):
            row, col = number_reactions[nums[0]]
            file = await reaction.message.attachments[0].to_file()
            image = get_image_from_grid(Image.open(file.fp), col, row, IMAGE_DIMENSIONS[0], IMAGE_DIMENSIONS[1])
            await reaction.message.channel.send(content="", file=pil_image2discord_image(image, "image.jpg"), reference=reaction.message)


bot.run(os.environ["DISCORD_TOKEN"])
