# Therapy Copilot

The tool injests a client/ therapist session located in transcript.txt, generated a SOAP note and facts about the client and stores them in a Honcho collection. A discord bot can then be launched that has access to the same collection and can provide continued care to the patient 24/7

## Initial Setup

This project uses [Poetry](https://python-poetry.org/) for dependency and virtual environment management. Navigate to this folderand run the following commands:

```
poetry shell
poetry install
```

## Injest the transcript

python3 process_transcript.py

## Run the Bot

By default, the bot will reference the hosted version of Honcho at https://demo.honcho.dev and store data there temorarily for up to 7 days. If you'd like to run Honcho locally, follow the instructions in the README at the root of this repository.  

Copy the `.env.template` file to a `.env` file and fill out the `BOT_TOKEN` and `OPENAI_API_KEY` values. To run the bot, use the following command:
```
python3 bot.py
```

If you have any further questions, feel free to join our [Discord server](https://discord.gg/plasticlabs) and ask in the #honcho channel!
