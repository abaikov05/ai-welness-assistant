import json, io, math

from decimal import Decimal

from channels.generic.websocket import AsyncWebsocketConsumer

from .assistant.responder import Responder
from .assistant.settings import *
from .assistant.emotional_journal import EmotionalJournal
from .assistant.moderation import Moderation
from .assistant.helpers import openai_audio_transcription

from .utils import get_chat_history, Encryption

from .models import Message, Chat, User_profile, User_settings, User_emotional_journal, User_balance, Balance_transaction
from django.utils import timezone
from datetime import date
from time import time


# TODO Welcome messages on last_login or last_message_time

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
        print(self.scope)
        # Check if the user is authenticated
        if not user.is_authenticated:

            await self.close(close_code='1006')
            print("Unauthenticated user tried to connect!", user)
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
        
    async def receive(self, text_data=None, bytes_data=None):
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
        if CONSUMERS_DEBUG: 
            payload_recived = time()
            print("-"*10,"Payload  recived at:", payload_recived)
        
        user = self.scope['user']

        # Check if the user is authenticated
        if not user.is_authenticated:
            await self.close(close_code='1006')
            print("Unauthenticated user sent payload!", text_data, user)
            return
        # Handle media or simple text data payloads.
        image = None
        if bytes_data:
            try:
                user_balance = await User_balance.objects.aget(user=user)
                if user_balance.balance < 0.01:
                    await self.send(text_data=json.dumps({
                            'type':'notification',
                            'type_of_notification': 'error',
                            'header': 'Balance',
                            'message': 'Your balance is too low and may not be sufficient to generate response for your voice message! Please topup your balance.'
                        }))
                    return
                # Split data on separator
                media_metadata, media = bytes_data.split(b'|', 1)
                media_metadata = json.loads(media_metadata)

                if media_metadata['audio_size']:
                    try:  
                        audio = media[:media_metadata['audio_size']]
                        # Create an in-memory file-like object of a voice.
                        audio = io.BytesIO(audio)
                        audio.name = "voice.webm"
                        # Transcribe voice message and calculate cost.
                        text, duration = await openai_audio_transcription(audio, AUDIO_TRANSCRIPTION_MODEL)
                        await calculate_audio_cost(user_balance, duration)
                        
                        if CONSUMERS_DEBUG: print(f"Received audio data, with duration: {duration} and translated as: {text}")     
                    except Exception as e:
                        print(f"Error occurred while handling voice message: {e}")     
                        return

                if media_metadata['image_size'] and media_metadata['image_type']:
                    image_type = media_metadata['image_type'][6:]
                    if image_type.lower() not in ['png','jpg', 'jpeg', 'webp']:
                        await self.send(text_data=json.dumps({
                            'type':'notification',
                            'type_of_notification': 'error',
                            'header': 'Image',
                            'message': 'Unsupported image type! Please upload only: .png, .jpg, .jpeg or .webp'
                        }))
                        return
                    # Create an in-memory file-like object of an image.
                    image = media[- media_metadata['image_size']:]
                    image = io.BytesIO(image)
                    image.name = f"image.{image_type}"         
                # If only image was sent use text from the textbox
                if not media_metadata['audio_size']:
                    text = media_metadata['message']

                text_data_json = {
                    'type': 'message',
                    'use_tools': media_metadata['use_tools'] == 1,
                    'extract_inputs': media_metadata['extract_inputs'] == 1,
                    'message': text
                }
            except Exception as e:
                print(f"Error occurred while handling media payload: {e}")
                return
        else:    
            try:
                # Attempt to parse incoming JSON data
                text_data_json = json.loads(text_data)
                if CONSUMERS_DEBUG:print(f"{'_'*20}\nSocket recived:\n{text_data_json}\n{'_'*20}")
            except:
                print("Socket recived wrong payload format")
                return
        
        encryption = Encryption()
        ###  Handle different payload types
        # Process user profile request
        if text_data_json.get('type') == 'user_profile':

            # Get all information related to user profile from DB
            user_profile = await User_profile.objects.aget(user=user)
            settings = await User_settings.objects.aget(user=user)

            if CONSUMERS_DEBUG:print(f"{'_'*20}\nProfile request sent\nProfile:\n{encryption.decrypt(user_profile.content)}\n{'_'*20}")
            # Send user profile data to the client
            await self.send(text_data=json.dumps({
                'type':'user_profile',
                'profile': encryption.decrypt(user_profile.content),
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
                    'type':'notification',
                    'type_of_notification': 'error',
                    'header': 'Profile',
                    'message': 'Error in profile data! Changes not saved!'
                }))
                return

            if len(profile) >= MAX_PROFILE_LENGTH:
                await self.send(text_data=json.dumps({
                    'type':'notification',
                    'type_of_notification': 'error',
                    'header': 'Profile',
                    'message': 'Profile is too long! Changes not saved!'
                }))
                return
            
            moder = Moderation()
            flagged, category = moder.moderate(profile)
            if flagged:
                if CONSUMERS_DEBUG: print("Flagged: ", flagged)
                await self.send(text_data=json.dumps({
                    'type':'notification',
                    'type_of_notification': 'error',
                    'header': 'Profile',
                    'message': f'Ill content in profile entry! Categories: {", ".join(category)}'
                }))
                return
            
            user_profile = await User_profile.objects.aget(user=user)
            user_profile.content = encryption.encrypt(profile)
            await user_profile.asave()

            await self.send(text_data=json.dumps({
                'type':'notification',
                'type_of_notification': 'success',
                'header': 'Profile',
                'message': 'Profile saved!'
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
            
            if not (MIN_MESSAGES_FOR_PROFILE_UPDATE <= msg_for_update <= MAX_MESSAGES_FOR_PROFILE_UPDATE):
                await self.send(text_data=json.dumps({
                    'type':'notification',
                    'type_of_notification': 'error',
                    'header': 'Profile',
                    'message': "Invalid number of mesages for profile update passed! Changes not saved!"
                }))
                return
            
            if not (MIN_MESSAGES_TILL_PROFILE_UPDATE <= msg_till_update <= MAX_MESSAGES_TILL_PROFILE_UPDATE):
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

            if CONSUMERS_DEBUG:print(f"{'_'*20}\nJournal request sent\nJournals:\n{journals}\n{'_'*20}")
            
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
            
            if journal_gpt_model != None:
                if journal_gpt_model not in AVAILABLE_GPT_MODELS:
                    await self.send(text_data=json.dumps({
                        'type':'notification',
                        'type_of_notification': 'error',
                        'header': 'Emotional journal',
                        'message': "GPT model for journal you have chosen is not available! Changes not saved!"
                    }))
                    return
            
            if not (MIN_MESSAGES_FOR_JOURNAL_UPDATE <= msg_for_update <= MAX_MESSAGES_FOR_JOURNAL_UPDATE):
                await self.send(text_data=json.dumps({
                    'type':'notification',
                    'type_of_notification': 'error',
                    'header': 'Emotional journal',
                    'message': "Invalid number of mesages for journal update passed! Changes not saved!"
                }))
                return
            
            if not (MIN_MESSAGES_TILL_JOURNAL_UPDATE <= msg_till_update <= MAX_MESSAGES_TILL_JOURNAL_UPDATE):
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
            
            moder = Moderation()
            flagged, category = moder.moderate(responder_personality)
            if flagged:
                if CONSUMERS_DEBUG: print("Flagged: ", flagged)
                await self.send(text_data=json.dumps({
                    'type':'notification',
                    'type_of_notification': 'error',
                    'header': 'Responder',
                    'message': f'Ill content in responders personality! Category: {", ".join(category)}'
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
            if CONSUMERS_DEBUG:print(f"{'_'*20}\nInputs recived by socket:{text_data_json}{'_'*20}")

            user_balance = await User_balance.objects.aget(user=user)
            if user_balance.balance < 0.01:
                await self.send(text_data=json.dumps({
                        'type':'notification',
                        'type_of_notification': 'error',
                        'header': 'Balance',
                        'message': 'Your balance is too low and may not be sufficient to generate response! Please topup your balance.'
                    }))
                return
            
            await self.send(text_data=json.dumps({
                'type':'loading_response'
            }))
            
            tool = text_data_json['tool']
            inputs = text_data_json['inputs']

            user_settings = await User_settings.objects.aget(user=user)
            user_profile = await User_profile.objects.aget(user=user)
            
            current_date = timezone.now().date()
            user_emotional_journal, journal_created = await User_emotional_journal.objects.aget_or_create(user=user, date=current_date)
                
            chat = await Chat.objects.aget(user=user)

            chat_history = await get_chat_history(
                chat=chat,
                limit=MESSAGES_TO_PASS_TO_ASSISTANT,
                reverse=True
            )

            assistant_settings = AssistantSettings(
                responder_gpt_model = user_settings.responder_gpt_model,
                responder_personality = user_settings.responder_personality
            )

            emotional_journal = EmotionalJournal(
                journal=user_emotional_journal.journal,
                updates_count=None,
                gpt_model=None
            )
            responder = Responder(
                chat_history = chat_history,
                user_profile = encryption.decrypt(user_profile.content),
                emotional_journal = emotional_journal,
                assistant_settings = assistant_settings,
                user=user
            )

            response, metadata = await responder.handle_user_inputs(tool = tool, inputs = inputs)

            await calculate_cost(user_balance, responder.total_tokens_used, assistant_settings)

            if metadata:
                if metadata.get('type') == "input_request":
                    if CONSUMERS_DEBUG: print(f"{'_'*20}\nInput request\nMetadata:\n{metadata}\n{'_'*20}")

                    if metadata.get('type') == "tool_exeption":
                        await self.send(text_data=json.dumps({
                            'type': 'ai_response',
                            'ai_message': response
                        }))
                        metadata['type'] = "input_request"
                        
                    await self.send(text_data=json.dumps(metadata))

                    return
                else:
                    if CONSUMERS_DEBUG:print(f"{'_'*20}\nResponse with recived inputs:\n{response}\n- Metadata:\n{metadata}\n{'_'*20}")
                    await self.send(text_data=json.dumps({
                        'type':'ai_response',
                        'ai_message': response
                    }))

                    new_bot_message = Message(chat = chat, text = encryption.encrypt(response), is_bot = True)
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
        
        # Check user balance before responding
        user_balance = await User_balance.objects.aget(user=user)
        if user_balance.balance < 0.01:
            await self.send(text_data=json.dumps({
                    'type':'notification',
                    'type_of_notification': 'error',
                    'header': 'Balance',
                    'message': 'Your balance is too low and may not be sufficient to generate response! Please topup your balance.'
                }))
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
        
        if len(user_message) >= MAX_MESSAGE_LEN:
            await self.send(text_data=json.dumps({
                    'type':'notification',
                    'type_of_notification': 'error',
                    'header': 'Message is too long!',
                    'message': 'The assistant will not reply to this message, and it will not be saved in the chat.'
                }))
            return
        
        await self.send(text_data=json.dumps({
                'type':'loading_response'
            }))
        
        chat = await Chat.objects.aget(user=user)

        current_date = timezone.now().date()

        chat_history = await get_chat_history(
            chat = chat,
            limit = MESSAGES_TO_PASS_TO_ASSISTANT,
            reverse=True
        )

        new_message = Message(chat=chat, text=encryption.encrypt(user_message))
        await new_message.asave()

        message_count = await Message.objects.filter(chat=chat).acount()
        if CONSUMERS_DEBUG: print("Message count:", message_count)

        user_profile_object, profile_created = await User_profile.objects.aget_or_create(user=user)
        user_profile = encryption.decrypt(user_profile_object.content)
        if CONSUMERS_DEBUG: print("User profile: ", user_profile)

        user_settings = await User_settings.objects.aget(user=user)
        user_emotional_journal, journal_created = await User_emotional_journal.objects.aget_or_create(user=user, date=current_date)

        emotional_journal = EmotionalJournal(
            journal = user_emotional_journal.journal,
            updates_count = user_emotional_journal.updates_count,
            gpt_model = user_settings.journal_gpt_model
        )


        if CONSUMERS_DEBUG: print(
            f"User settings: ",
            user_settings.responder_gpt_model,
            user_settings.responder_personality,
            user_settings.profiler_gpt_model,
            user_settings.journal_gpt_model,
            user_settings.messages_for_profile_update,
            user_settings.messages_till_profile_update,
            user_settings.messages_for_input_extraction,
            user_settings.messages_till_journal_update,'\n', '_'*20
        )
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
            user=user,
        )
        response = await responder.handle_user_message(
            user_message = user_message,
            use_tools = use_tools,
            extract_inputs = extract_inputs,
            image=image
        )
        text, metadata, profile, journal = response

        if CONSUMERS_DEBUG: print("Responder used tokens: ", responder.total_tokens_used)
        
        await calculate_cost(user_balance, responder.total_tokens_used, assistant_settings)
                    
        if metadata:
            if metadata.get('type') == "input_request" or metadata.get('type') == "tool_exeption":
                if CONSUMERS_DEBUG: print(f"{'_'*20}\nSending input request:\n{json.dumps(metadata, indent=2)}\n{'_'*20}")
                
                if metadata.get('type') == "tool_exeption":
                    await self.send(text_data=json.dumps({
                        'type': 'ai_response',
                        'ai_message': text
                    }))
                    metadata['type'] = "input_request"
                    
                await self.send(text_data=json.dumps(metadata))

                if profile:
                    if len(profile) >= MAX_PROFILE_LENGTH:
                        await self.send(text_data=json.dumps({
                            'type':'notification',
                            'type_of_notification': 'error',
                            'header': 'Profile',
                            'message': 'Assitant tried to update profile, but it was too long! Please, delete or shorten some entries for further updates.'
                        }))
                        return
                    else:   
                        user_profile_object.content = encryption.encrypt(json.dumps(profile))
                        await user_profile_object.asave()

                if journal:
                    journal_text, updates_count = journal

                    user_emotional_journal.journal = json.dumps(journal_text)
                    user_emotional_journal.updates_count = updates_count

                    await user_emotional_journal.asave()
                    
                return
        
        if text:
            await self.send(text_data=json.dumps({
                'type': 'ai_response',
                'ai_message': text
            }))
            new_bot_message = Message(chat=chat, text=encryption.encrypt(text), is_bot=True)
            await new_bot_message.asave()
        else:
            await self.send(text_data=json.dumps({
                'type': 'ai_response',
                'ai_message': "Apologies, the I currently experiencing some technical difficulties. Please try again later. Thank you for your patience!"
            }))
        
        # To measure systems response generaing speed. 
        if CONSUMERS_DEBUG: 
            response_sent = time()
            time_for_response = response_sent-payload_recived
            print("-"*10,"Response sent at:", response_sent, f"\nTook {time_for_response} seconds to generate and send response.")
            
            total_tokens_generated = 0
            for module in responder.total_tokens_used:
                if len(responder.total_tokens_used[module]) != 0:
                    total_tokens_generated += responder.total_tokens_used[module]['completion_tokens']
            
            print(f"Systems tokens per second: {total_tokens_generated/time_for_response}")
            print('Responder, Tools, Recommender model:', assistant_settings.responder_gpt_model)
            print('Profiler model:', assistant_settings.profiler_gpt_model)
            print('Journal model:', assistant_settings.journal_gpt_model)
        
        if profile:
            if len(profile) >= MAX_PROFILE_LENGTH:
                await self.send(text_data=json.dumps({
                    'type':'notification',
                    'type_of_notification': 'error',
                    'header': 'Profile',
                    'message': 'Assitant tried to update profile, but it was too long! Please, delete or shorten some entries for further updates.'
                }))
                return
            else:   
                user_profile_object.content = encryption.encrypt(json.dumps(profile))
                await user_profile_object.asave()

        if journal:
            journal_text, updates_count = journal
            user_emotional_journal.journal = json.dumps(journal_text)
            user_emotional_journal.updates_count = updates_count

            await user_emotional_journal.asave()

        return
        
    async def disconnect(self, close_code):

        if CONSUMERS_DEBUG: print("Socket disconnected with code:", close_code)
        await self.close()

        return
    
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
    if CONSUMERS_DEBUG: print(f"{'_'*20}\nJournals data in consumers:\n", journals, '_'*20)

    return journals

async def calculate_cost(user_balance: User_balance, tokens_used: dict, assistant_settings: AssistantSettings) -> None:
    """
    Calculates cost of used tokens by every asistant module.  Creates and saves transactions for
    modules to database and updates user balance.
    """
    def module_cost(module, gpt_model):
        module_cost = Decimal(tokens_used[module]['prompt_tokens']/1000 * GPT_MODELS_PRICING[gpt_model]['input'])
        module_cost += Decimal(tokens_used[module]['completion_tokens']/1000 * GPT_MODELS_PRICING[gpt_model]['output'])
        return module_cost
    
    modules_and_models = {
        "Tools": assistant_settings.responder_gpt_model,
        "Profiler": assistant_settings.profiler_gpt_model,
        "Journal": assistant_settings.journal_gpt_model,
        "Recommender": assistant_settings.responder_gpt_model,
        "Responder": assistant_settings.responder_gpt_model
    }
    
    total_cost = Decimal(0)
    for module in tokens_used:
        if len(tokens_used[module]) == 0 or tokens_used[module]['total_tokens'] == 0:
            continue
        
        module_costs = module_cost(module, modules_and_models[module])
        total_cost += module_costs
        if CONSUMERS_DEBUG: print(f"{module} cost - {module_costs}")
        
        new_transaction = Balance_transaction(type = module, balance = user_balance, amount = module_costs)
        await new_transaction.asave()
    
    new_user_balance = Decimal(user_balance.balance) - total_cost
    new_user_balance = new_user_balance.quantize(Decimal('0.0001'), rounding='ROUND_FLOOR')
    
    if CONSUMERS_DEBUG: print(f"User balance: {user_balance.balance} - New balance: {new_user_balance}")
    
    user_balance.balance = new_user_balance
    await user_balance.asave()
    
async def calculate_audio_cost(user_balance: User_balance, audio_duration: float) -> None:
    """
    Calculates cost of voice message transcription. Creates and saves transaction to database and 
    updates user balance.
    """
    audio_cost = Decimal(0)
    audio_cost = math.ceil(audio_duration) / 60 * AUDIO_TRANSCRIPTION_MODEL_PRICING
    new_transaction = Balance_transaction(type = 'Audio', balance = user_balance, amount = audio_cost)
    await new_transaction.asave()

    new_user_balance = Decimal(user_balance.balance) - Decimal(audio_cost)
    new_user_balance = new_user_balance.quantize(Decimal('0.0001'), rounding='ROUND_FLOOR')
    
    user_balance.balance = new_user_balance
    await user_balance.asave()