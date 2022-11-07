# prompt-battle-bot
A discord bot to play "Prompt Battle" using Stable Diffusion's DreamStudio

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template/hxAexO?referralCode=jwithing)

## Setup
* DISCORD_TOKEN
* STABLE_DIFFUSION_TOKEN

`docker build . -t bot`

`docker run --env-file .env -it bot`

`docker run --rm --env-file .\.env -it $(docker build -q .)`

Bot permissions:
397821475904
