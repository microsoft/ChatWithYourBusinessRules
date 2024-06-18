# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
from concurrent.futures import ThreadPoolExecutor

from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import ChannelAccount, Activity, ActivityTypes

from common.callbacks import BotServiceCallbackHandler
from common.scenario_prompts import WELCOME_MESSAGE
from common.agents import send_request_to_agent_async

# Bot Class
class MyBot(ActivityHandler):
            
    # Function to show welcome message to new users
    async def on_members_added_activity(self, members_added: ChannelAccount, turn_context: TurnContext):
        for member_added in members_added:
            if member_added.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(WELCOME_MESSAGE)
    
    
    # See https://aka.ms/about-bot-activity-message to learn more about the message and other activity types.
    async def on_message_activity(self, turn_context: TurnContext):
             
        
        input_text_metadata = dict()
        
        # Check if local_timestamp exists and is not None before formatting it
        input_text_metadata["local_timestamp"] = turn_context.activity.local_timestamp.strftime("%I:%M:%S %p, %A, %B %d of %Y") if turn_context.activity.local_timestamp else "Not Available"
    
        # Check if local_timezone exists and is not None before assigning it
        input_text_metadata["local_timezone"] = turn_context.activity.local_timezone if turn_context.activity.local_timezone else "Not Available"
    
        # Check if locale exists and is not None before assigning it
        input_text_metadata["locale"] = turn_context.activity.locale if turn_context.activity.locale else "Not Available"

        # Setting the query to send to OpenAI
        input_text = turn_context.activity.text + "\n\n metadata:\n" + str(input_text_metadata)    
                    
        # Set Callback Handler
        cb_handler = BotServiceCallbackHandler(turn_context)

        # Extract info from TurnContext - You can change this to whatever , this is just one option 
        session_id = turn_context.activity.conversation.id
        user_id = turn_context.activity.from_property.id + "-" + turn_context.activity.channel_id

        await turn_context.send_activity(Activity(type=ActivityTypes.typing))
        answer = await send_request_to_agent_async(input_text, user_id, session_id, cb_handler)
        await turn_context.send_activity(answer)



