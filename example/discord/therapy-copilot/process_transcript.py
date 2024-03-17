import os
from honcho import Honcho

from langchain_core.prompts import load_prompt

from transcript_chain import TranscriptChain
import asyncio

_APP_NAME = "therapy-copilot-hackathon"
_USER_ID = "discord_1234567892"
_LOCATION_ID = 'transcript'

async def main():
    # honcho = Honcho(app_name=app_name, base_url="http://localhost:8000") # uncomment to use local
    honcho = Honcho(app_name=_APP_NAME)  # uses demo server at https://demo.honcho.dev
    honcho.initialize()
    
    # read file transcript.txt
    with open('transcript.txt', 'r') as file:
        transcript = file.read()

    user_id = _USER_ID
    user = honcho.get_or_create_user(user_id)
    
    sessions = list(user.get_sessions_generator(_LOCATION_ID))
    if len(sessions) > 0:
        session = sessions[0]
    else:
        session = user.create_session(_LOCATION_ID)
    try:
        collection = user.get_collection(name="discord")
    except Exception:
        collection = user.create_collection(name="discord")
    
    print(f"Collection {collection.id}")
    response = await TranscriptChain.process(
            transcript=transcript,
            session=session,
            collection=collection,
        )
    print(response)

if __name__ == '__main__':
    # main()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
