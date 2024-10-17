import json
import asyncio

from decimal import Decimal

from channels.generic.websocket import AsyncWebsocketConsumer
# from asgiref.sync import sync_to_async

from .assistant.responder import Responder
from .assistant.settings import *
from .assistant.emotional_journal import EmotionalJournal
from .assistant.moderation import Moderation

# from django.contrib.auth import authenticate

from .models import Message, Chat, User_profile, User_settings, User_emotional_journal, User_balance, Balance_transaction
# from django.db.models import Count
from django.utils import timezone
from datetime import date


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling chat interactions.

    Attributes:
        None

    Methods:
        connect: Handles the initiation of a connection.
    """
    async def connect(self):
        """
        Handle connection initiation.

        - Retrieves the user from the connection scope.
        - Checks if the user is authenticated.
        - Accepts the connection if authenticated.
        - Retrieves the chat object for the user.
        - Gets the previous chat history from the database.
        - Sends the chat history to the client.
        """
        user = self.scope['user']

        # Check if the user is authenticated
        if not user.is_authenticated:

            await self.close(close_code='1006')
            print("Unauthenticated user tried to connect!")
            return

        # Accept the connection
        await self.accept()

        # Retrieve the chat object for the user
        chat = await Chat.objects.aget(user=user)

        # Get the previous chat history
        chat_history = await get_chat_history(
            chat = chat,
            limit = CHAT_MESSAGES_TO_LOAD_PER_REQUEST,
            for_socket = True,
            reverse=True
        )

        # Send it to the client
        await self.send(text_data=json.dumps({
            'type': 'chat_history',
            'chat': chat_history
        }))
        
    async def receive(self, text_data):
        """
        Handles receiving messages from the WebSocket.

        - Validates user authentication.
        - Parses incoming JSON data.
        - Handeles recived payloads based on its 'type' field.

        Args:
            text_data (str): The received text data.

        Returns:
            None
        """
        user = self.scope['user']

        # Check if the user is authenticated
        if not user.is_authenticated:
            await self.close(close_code='1006')
            print("Unauthenticated user sent payload!")
            return
        
        try:
            # Attempt to parse incoming JSON data
            text_data_json = json.loads(text_data)
            print("_"*20)
            print("Socket recived:" ,text_data_json)
            print("_"*20)
        except:
            print("Socket recived wrong payload format")
            return
        
        ###  Handle different payload types
        # Process user profile request
        if text_data_json.get('type') == 'user_profile':

            # Get all information related to user profile from DB
            user_profile = await User_profile.objects.aget(user=user)
            settings = await User_settings.objects.aget(user=user)

            print(f"- Profile request sent\nProfile:{user_profile.content}\n{'_'*100}")
            # Send user profile data to the client
            await self.send(text_data=json.dumps({
                'type':'user_profile',
                'profile': user_profile.content,
                'gpt_model': settings.profiler_gpt_model,
                'messages_for_profile_update': settings.messages_for_profile_update,
                'messages_till_profile_update': settings.messages_till_profile_update
            }))

            return
        
        # Process user profile change request
        if text_data_json.get('type') == 'user_profile_change':
            
            try:
                profile = json.dumps(text_data_json['profile'])
            except:
                await self.send(text_data=json.dumps({
                    'type':'error_in_data_format'
                }))
                return

            moder = Moderation()
            flagged, category = moder.moderate(profile)
            if flagged:
                print("Flagged: ", flagged)
                await self.send(text_data=json.dumps({
                    'type':'ill_profile_content'
                }))
                return
            
            user_profile = await User_profile.objects.aget(user=user)
            user_profile.content = profile
            await user_profile.asave()

            await self.send(text_data=json.dumps({
                'type':'profile_saved'
            }))

            return
        # Process user profile settings change request
        if text_data_json.get('type') == 'user_profile_settings':
            try:
                profiler_gpt_model = text_data_json['profiler_gpt_model']
                msg_for_update = int(text_data_json['messages_for_profile_update'])
                msg_till_update = int(text_data_json['messages_till_profile_update'])
            except Exception as e:
                await self.send(text_data=json.dumps({
                    'type':'notification',
                    'type_of_notification': 'error',
                    'header': 'Profile',
                    'message': 'Error in passed settings! Changes not saved!'
                }))
                return
            
            print(msg_for_update, msg_till_update)
            if profiler_gpt_model != None:
                if profiler_gpt_model not in AVAILABLE_GPT_MODELS:
                    await self.send(text_data=json.dumps({
                        'type':'notification',
                        'type_of_notification': 'error',
                        'header': 'Profile',
                        'message': "GPT model for profiler you have chosen is not available! Changes not saved!"
                    }))
                    return
            
            if not ((MIN_MESSAGES_FOR_PROFILE_UPDATE <= msg_for_update <= MAX_MESSAGES_FOR_PROFILE_UPDATE) and (msg_for_update % 2 == 1)):
                await self.send(text_data=json.dumps({
                    'type':'notification',
                    'type_of_notification': 'error',
                    'header': 'Profile',
                    'message': "Invalid number of mesages for profile update passed! Changes not saved!"
                }))
                return
            
            if not ((MIN_MESSAGES_TILL_PROFILE_UPDATE <= msg_till_update <= MAX_MESSAGES_TILL_PROFILE_UPDATE) and (msg_till_update % 2 == 1)):
                await self.send(text_data=json.dumps({
                    'type':'notification',
                    'type_of_notification': 'error',
                    'header': 'Profile',
                    'message': "Invalid number of mesages till profile update passed! Changes not saved!"
                }))
                return
            
            user_settings = await User_settings.objects.aget(user=user)
            if profiler_gpt_model != None:
                user_settings.profiler_gpt_model = profiler_gpt_model
            user_settings.messages_for_profile_update = msg_for_update
            user_settings.messages_till_profile_update = msg_till_update
            await user_settings.asave()

            await self.send(text_data=json.dumps({
                'type':'notification',
                'type_of_notification': 'success',
                'header': 'Profile',
                'message': "Profiler settings saved!"
            }))

            return
        
        # Process user emotional journal request
        if text_data_json.get('type') == 'user_journal':

            journals = await get_emotional_journals(
                user = user,
                limit = EMOTIONAL_JOURNALS_TO_LOAD_PER_REQUEST,
                for_socket = True)

            settings = await User_settings.objects.aget(user=user)

            print(f"- Journal request sent\nJournals:{journals}\n{'_'*100}")
            await self.send(text_data=json.dumps({
                'type':'user_journal',
                'journals': journals,
                'gpt_model': settings.journal_gpt_model,
                'messages_for_journal_update': settings.messages_for_journal_update,
                'messages_till_journal_update': settings.messages_till_journal_update
            }))

            return
        
        # Process request to load more user emotional journals
        if text_data_json.get('type') == 'load_more_journals':
    
            try:
                offset = text_data_json['journals_offset']
            except:
                return

            user_journals = await get_emotional_journals(
                user = user,
                limit = EMOTIONAL_JOURNALS_TO_LOAD_PER_REQUEST,
                offset = offset,
                for_socket = True)
            await self.send(text_data=json.dumps({
                'type':'user_journal',
                'subtype': 'load_more_journals',
                'journals': user_journals
            }))

            return

        # Process request to load settings for user emotional journal
        if text_data_json.get('type') == 'user_journal_settings':
            try:
                journal_gpt_model = text_data_json['journal_gpt_model']
                msg_for_update = int(text_data_json['messages_for_journal_update'])
                msg_till_update = int(text_data_json['messages_till_journal_update'])
            except Exception as e:
                await self.send(text_data=json.dumps({
                    'type':'notification',
                    'type_of_notification': 'error',
                    'header': 'Emotional journal',
                    'message': 'Error in passed settings! Changes not saved!'
                }))
                return
            
            print(msg_for_update, msg_till_update)
            if journal_gpt_model != None:
                if journal_gpt_model not in AVAILABLE_GPT_MODELS:
                    await self.send(text_data=json.dumps({
                        'type':'notification',
                        'type_of_notification': 'error',
                        'header': 'Emotional journal',
                        'message': "GPT model for journal you have chosen is not available! Changes not saved!"
                    }))
                    return
            
            if not ((MIN_MESSAGES_FOR_JOURNAL_UPDATE <= msg_for_update <= MAX_MESSAGES_FOR_JOURNAL_UPDATE) and (msg_for_update % 2 == 1)):
                await self.send(text_data=json.dumps({
                    'type':'notification',
                    'type_of_notification': 'error',
                    'header': 'Emotional journal',
                    'message': "Invalid number of mesages for journal update passed! Changes not saved!"
                }))
                return
            
            if not ((MIN_MESSAGES_TILL_JOURNAL_UPDATE <= msg_till_update <= MAX_MESSAGES_TILL_JOURNAL_UPDATE) and (msg_till_update % 2 == 1)):
                await self.send(text_data=json.dumps({
                    'type':'notification',
                    'type_of_notification': 'error',
                    'header': 'Emotional journal',
                    'message': "Invalid number of mesages till journal update passed! Changes not saved!"
                }))
                return
            
            user_settings = await User_settings.objects.aget(user=user)
            if journal_gpt_model != None:
                user_settings.journal_gpt_model = journal_gpt_model
            user_settings.messages_for_journal_update = msg_for_update
            user_settings.messages_till_journal_update = msg_till_update
            await user_settings.asave()

            await self.send(text_data=json.dumps({
                'type':'notification',
                'type_of_notification': 'success',
                'header': 'Emotional journal',
                'message': "Journal settings saved!"
            }))

            return
        
        # Process request for responder settings
        if text_data_json.get('type') == 'user_responder':

            settings = await User_settings.objects.aget(user=user)

            await self.send(text_data=json.dumps({
                'type':'user_responder',
                'gpt_model': settings.responder_gpt_model,
                'responder_personality': settings.responder_personality,
                'messages_for_input_extraction': settings.messages_for_input_extraction
            }))

            return
        
        # Process request for responder settings change
        if text_data_json.get('type') == 'user_responder_settings':
            try:
                responder_gpt_model = text_data_json['responder_gpt_model']
                responder_personality = text_data_json['responder_personality']
                msg_for_input = int(text_data_json['messages_for_input_extraction'])

            except Exception as e:
                await self.send(text_data=json.dumps({
                    'type':'notification',
                    'type_of_notification': 'error',
                    'header': 'Responder',
                    'message': 'Error in passed settings! Changes not saved!'
                }))
                return
            if responder_gpt_model != None:
                if responder_gpt_model not in AVAILABLE_GPT_MODELS:
                    await self.send(text_data=json.dumps({
                        'type':'notification',
                        'type_of_notification': 'error',
                        'header': 'Responder',
                        'message': "GPT model for responder you have chosen is not available! Changes not saved!"
                    }))
                    return
            
            if not (MIN_MESSAGES_FOR_INPUT_EXTACTION <= msg_for_input <= MAX_MESSAGES_FOR_INPUT_EXTACTION):
                await self.send(text_data=json.dumps({
                    'type':'notification',
                    'type_of_notification': 'error',
                    'header': 'Responder',
                    'message': "Invalid number of mesages for input extraction passed! Changes not saved!"
                }))
                return
            
            settings = await User_settings.objects.aget(user=user)
            if responder_gpt_model != None:
                settings.responder_gpt_model = responder_gpt_model
            settings.responder_personality = responder_personality
            settings.messages_for_input_extraction = msg_for_input

            await settings.asave()

            await self.send(text_data=json.dumps({
                'type':'notification',
                'type_of_notification': 'success',
                'header': 'Responder',
                'message': "Responder settings saved!"
            }))

            return
        
        # Process request to load more user emotional journals
        if text_data_json.get('type') == 'user_transactions':

            user_balance = await User_balance.objects.aget(user=user)
            user_transactions = []
            async for transaction in Balance_transaction.objects.order_by('-datetime').filter(balance = user_balance):
                formated_data = {
                    'type': transaction.type,
                    'amount': float(transaction.amount),
                    'datetime': transaction.datetime.strftime("%Y-%m-%d %H:%M:%S")
                }
                user_transactions.append(formated_data)
            
            await self.send(text_data=json.dumps({
                'type':'user_transactions_history',
                'transactions': user_transactions
            }))

            return

        # Handle user inputs for tool that was missing inputs.  
        if text_data_json.get('type') == 'inputs':
            print(f'{"_"*100}\n- Inputs recived by socket', text_data_json)

            tool = text_data_json['tool']
            inputs = text_data_json['inputs']

            user_settings = await User_settings.objects.aget(user=user)
            user_profile = await User_profile.objects.aget(user=user)
            chat = await Chat.objects.aget(user=user)

            chat_history = await get_chat_history(
                chat=chat,
                limit=MESSAGES_TO_PASS_TO_ASSISTANT,
                reverse=True
            )

            settings = AssistantSettings(
                responder_gpt_model = user_settings.responder_gpt_model,
                responder_personality = user_settings.responder_personality
            )

            responder = Responder(
                chat_history = chat_history,
                user_profile = user_profile.content,
                assistant_settings = settings
            )

            response, metadata = await responder.handle_user_inputs(tool = tool, inputs = inputs)

            tokens_used = responder.total_tokens_used
            if tokens_used['Responder']['total_tokens'] != 0:
                total_cost = Decimal(0)

                total_cost += Decimal(tokens_used[module]['prompt_tokens']/1000 * GPT_MODELS_PRICING[assistant_settings.responder_gpt_model]['input'])
                total_cost += Decimal(tokens_used[module]['completion_tokens']/1000 * GPT_MODELS_PRICING[assistant_settings.responder_gpt_model]['output'])

                new_user_balance = Decimal(user_balance.balance) - total_cost
                new_user_balance.quantize(Decimal('0.0001'), rounding='ROUND_FLOOR')
                user_balance.balance = new_user_balance
                await user_balance.asave()

                new_transaction = Balance_transaction(type = module, balance = user_balance, amount = total_cost)
                await new_transaction.asave()

            if metadata:
                if metadata.get('type') == "input_request":
                    print("_"*20)
                    (f"- Input request :\nMetadata:\n{metadata}")
                    print("_"*20)
                    await self.send(text_data=json.dumps(metadata))

                    return
                else:
                    print(f"- Response with recived inputs:\n{response}\n- Metadata:\n{metadata}\n{'_'*100}")
                    await self.send(text_data=json.dumps({
                        'type':'ai_response',
                        'ai_message': response
                    }))

                    new_bot_message = Message(chat = chat, text = response, is_bot = True)
                    await new_bot_message.asave()

                    return
            return
        # Process request to load more chat history
        if text_data_json.get('type') == 'load_more_chat':

            try:
                offset = text_data_json['chat_offset']
            except:
                return

            chat = await Chat.objects.aget(user=user)
            chat_history = await get_chat_history(
                chat = chat,
                limit = CHAT_MESSAGES_TO_LOAD_PER_REQUEST,
                offset = offset,
                for_socket = True,
            )
            await self.send(text_data=json.dumps({
                'type':'more_chat_history',
                'chat': chat_history
            }))

            return
        
        # If payload has no type above, check if payload contains a message
        if not text_data_json.get('message'):
            print("Wrong payload recived!: ", text_data_json)
            return
        
        # Get data from recived message payload
        user_message = text_data_json['message']
        use_tools = text_data_json['use_tools']
        extract_inputs = text_data_json['extract_inputs']

        # Send user message back to show it in chat window
        await self.send(text_data=json.dumps({
            'type':'user_message',
            'user_message': user_message
        }))
        
        chat = await Chat.objects.aget(user=user)

        current_date = timezone.now().date()

        # Should be as async tasks!!
        chat_history = await get_chat_history(
            chat = chat,
            limit = MESSAGES_TO_PASS_TO_ASSISTANT,
            reverse=True
        )

        message_count = await Message.objects.filter(chat=chat).acount()
        print("Message count:", message_count)

        user_profile_object, profile_created = await User_profile.objects.aget_or_create(user=user)
        if profile_created:
            print('New user profile created!')
        user_profile = user_profile_object.content
        print("User profile: ", user_profile)

        user_settings = await User_settings.objects.aget(user=user)

        user_emotional_journal, journal_created = await User_emotional_journal.objects.aget_or_create(user=user, date=current_date)
        if journal_created:
            print('New emotional journal created!')
        user_balance = await User_balance.objects.aget(user=user)

        emotional_journal = EmotionalJournal(
            journal = user_emotional_journal.journal,
            updates_count = user_emotional_journal.updates_count,
            gpt_model = user_settings.journal_gpt_model
        )


        print(
            "User settings: ",
            user_settings.responder_gpt_model,
            user_settings.responder_personality,
            user_settings.profiler_gpt_model,
            user_settings.journal_gpt_model,
            user_settings.messages_for_profile_update,
            user_settings.messages_till_profile_update,
            user_settings.messages_for_input_extraction,
            user_settings.messages_till_journal_update
        )

        new_message = Message(chat=chat, text=user_message)
        await new_message.asave()
        # asyncio.gather()
        
        assistant_settings = AssistantSettings(
            responder_gpt_model = user_settings.responder_gpt_model,
            responder_personality = user_settings.responder_personality,
            profiler_gpt_model = user_settings.profiler_gpt_model,
            journal_gpt_model = user_settings.journal_gpt_model,
            messages_for_profile_update = user_settings.messages_for_profile_update,
            messages_till_profile_update = user_settings.messages_till_profile_update,
            messages_for_input_extraction = user_settings.messages_for_input_extraction,
            messages_till_journal_update = user_settings.messages_till_journal_update,
            messages_for_journal_update = user_settings.messages_for_journal_update
        )

        responder = Responder(
            user_profile = user_profile,
            chat_history = chat_history,
            message_count = message_count,
            emotional_journal=emotional_journal,
            assistant_settings = assistant_settings,
        )

        response = await responder.handle_user_message(
            user_message = user_message,
            use_tools = use_tools,
            extract_inputs = extract_inputs
        )

        text, metadata, profile, journal = response

        print("Responder used tokens: ", responder.total_tokens_used)
        tokens_used = responder.total_tokens_used
        for module in tokens_used:
            if len(tokens_used[module]) != 0 :
                if tokens_used[module]['total_tokens'] != 0:
                    total_cost = Decimal(0)
                    if module == 'Tools':
                        print(f"\nModule: {module, tokens_used[module]}\n")
                        total_cost += Decimal(tokens_used[module]['prompt_tokens']/1000 * GPT_MODELS_PRICING[assistant_settings.responder_gpt_model]['input'])
                        total_cost += Decimal(tokens_used[module]['completion_tokens']/1000 * GPT_MODELS_PRICING[assistant_settings.responder_gpt_model]['output'])
                    elif module == 'Profiler':
                        total_cost += Decimal(tokens_used[module]['prompt_tokens']/1000 * GPT_MODELS_PRICING[assistant_settings.profiler_gpt_model]['input'])
                        total_cost += Decimal(tokens_used[module]['completion_tokens']/1000 * GPT_MODELS_PRICING[assistant_settings.profiler_gpt_model]['output'])
                    elif module == 'Journal':
                        total_cost += Decimal(tokens_used[module]['prompt_tokens']/1000 * GPT_MODELS_PRICING[assistant_settings.journal_gpt_model]['input'])
                        total_cost += Decimal(tokens_used[module]['completion_tokens']/1000 * GPT_MODELS_PRICING[assistant_settings.journal_gpt_model]['output'])
                    elif module == 'Responder':
                        total_cost += Decimal(tokens_used[module]['prompt_tokens']/1000 * GPT_MODELS_PRICING[assistant_settings.responder_gpt_model]['input'])
                        total_cost += Decimal(tokens_used[module]['completion_tokens']/1000 * GPT_MODELS_PRICING[assistant_settings.responder_gpt_model]['output'])
                    else:
                        print('Invalid module in token usage statistics! Module not included in total cost!')

                    new_user_balance = Decimal(user_balance.balance) - total_cost
                    new_user_balance.quantize(Decimal('0.0001'), rounding='ROUND_FLOOR')
                    user_balance.balance = new_user_balance
                    await user_balance.asave()

                    new_transaction = Balance_transaction(type = module, balance = user_balance, amount = total_cost)
                    await new_transaction.asave()

        if metadata:
            if metadata.get('type') == "input_request":
                print('!'*100, '\nSending input request:\n', json.dumps(metadata, indent=2))
                await self.send(text_data=json.dumps(metadata))

                if profile:
                    user_profile_object.content = json.dumps(profile)
                    await user_profile_object.asave()

                if journal:
                    # journal_text, updates_count, date = journal
                    journal_text, updates_count = journal

                    user_emotional_journal.journal = json.dumps(journal_text)
                    user_emotional_journal.updates_count = updates_count

                    await user_emotional_journal.asave()
                    
                return
        
        await self.send(text_data=json.dumps({
            'type': 'ai_response',
            'ai_message': text
        }))

        new_bot_message = Message(chat=chat, text=text, is_bot=True)
        await new_bot_message.asave()

        if profile:
            user_profile_object.content = json.dumps(profile)
            await user_profile_object.asave()
            # profile_update = User_profile(user = user, content = profile)
            # await profile_update.asave()

        if journal:
            # journal_text, updates_count, date = journal
            journal_text, updates_count = journal
            user_emotional_journal.journal = json.dumps(journal_text)
            user_emotional_journal.updates_count = updates_count

            await user_emotional_journal.asave()

        return
        
    async def disconnect(self, close_code):

        print("Socket disconnected with code:", close_code)
        await self.close()

        return
    
async def get_chat_history(chat: Chat, limit: int, offset: int = 0, for_socket: bool = False, reverse:bool = False):
    
    chat_history = []

    if offset > 0:
        offset = offset*limit
        limit = limit + offset
    message_range = slice(offset, limit)

    async for message in Message.objects.order_by('-time').filter(chat=chat)[message_range]:
        if message.is_bot:

            if for_socket:
                chat_history.append({"is_bot": True, "message": message.text})
            else:
                chat_history.append(f"Assistant: {message.text}")
        else:

            if for_socket:
                chat_history.append({"is_bot": False, "message": message.text})
            else:
                chat_history.append(f"User: {message.text}")
    
    if reverse:
        chat_history.reverse()
    print(f"Chat history in consumers:")
    if for_socket:
        print(chat_history)
    else:
        print('\n'.join(chat_history))
    print('_'*100)
    return chat_history

async def get_emotional_journals(user: object, limit: int, offset: int = 0, for_socket: bool = False):
    
    journals = []

    if offset > 0:
        offset = offset*limit
        limit = limit + offset
    range = slice(offset, limit)

    async for journal in User_emotional_journal.objects.order_by('-date').filter(user=user)[range]:
            if for_socket:
                data = {
                    'date': str(journal.date),
                    'journal': journal.journal,
                    'updates_count': journal.updates_count
                }
                journals.append(data)
            else:
                journals.append(journal)


    journals.reverse()
    print(f"Journals data in consumers:", journals)

    return journals
