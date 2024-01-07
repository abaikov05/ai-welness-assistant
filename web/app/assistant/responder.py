from .moderation import Moderation
from .tools import Tools
from .user_profile import Profile
from .emotional_journal import EmotionalJournal
from .settings import AssistantSettings, CHAT_HISTORY_MESSAGES_FOR_RESPONDER

from textwrap import dedent
from .helpers import openai_chat_request

import asyncio
import openai

import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_KEY")

class Responder:
    """
    The Responder class manages the response generation process within the AI Wellbeing Assistant.
    The class encapsulates the logic needed to orchestrate the assistant's
    behavior in responding to user, ensuring a thoughtful and context-aware conversation.
    It integrates various components such as moderation, tools, user profiles, emotional journal,
    and assistant settings to handle incoming user messages. The class is responsible for processing user messages,
    applying moderation checks, updating user profiles and emotional journals, and generating appropriate responses.
    """
    def __init__(self, user_profile: str, chat_history: list[str], assistant_settings: AssistantSettings, message_count: int = None, emotional_journal: EmotionalJournal = None) -> None:
        """
        Initialize the Responder class with necessary attributes.

        Args:
        - user_profile (str): User's profile information.
        - chat_history (list): List containing the conversation history.
        - assistant_settings (class): Object containing settings for the assistant.
        - message_count (int): Number of messages in the conversation.
        - emotional_journal (class): Object representing the emotional journal.
        """
        self.settings = assistant_settings
        self.moderation = Moderation()
        self.tools = Tools(gpt_model = self.settings.responder_gpt_model)
        self.user_profile = Profile(user_profile = user_profile, gpt_model = self.settings.profiler_gpt_model)
        self.emotioal_journal = emotional_journal
        self.chat_history = chat_history
        self.message_count = message_count

        # Dictionary to track the total tokens used for GPT prompts and responces for every module.
        self.total_tokens_used = {
            "Tools":{},
            "Profiler":{},
            "Journal":{},
            "Responder": {}
        }

    async def handle_user_message(self, user_message: str, use_tools: bool, extract_inputs: bool) -> (str|None, dict|None, str|None, str|None):
        """
        Process and handle the user's message, applying moderation, updating profile and emotional journal, and generating a response.

        Args:
        - user_message (str): User's latest message.
        - use_tools (bool): Indicates whether to use tools.
        - extract_inputs (bool): Indicates whether to extract inputs for tools.

        Returns:
        - Tuple containing response, metadata, profile update, and journal update.
        """

        # Apply moderation to the user's message.
        flagged, flagged_categories = self.moderation.moderate(user_message = user_message)
        if flagged:
            response =  f"Ill content of message. Categories:{flagged_categories}"
            print(response)

            metadata, profile_update, journal_update = None, None, None

            return response, metadata, profile_update, journal_update
        
        # Initialize task list for concurrent processing.
        task_list = {}

        # If using tools, create a task for handling tools.
        if use_tools:
            tools_task = asyncio.create_task(
                self.tools.handle_tools(
                    user_message = user_message,
                    chat_history = self.chat_history,
                    extract_inputs = extract_inputs,
                    messages_for_input_extraction = self.settings.messages_for_input_extraction
                )
            )
            task_list['tools_task'] = tools_task

        # Check if it's time to update the user profile.
        if self.message_count % self.settings.messages_till_profile_update == 0:
            profile_update_task = asyncio.create_task(
                self.user_profile.update_user_profile(
                    previous_messages = self.chat_history[:self.settings.messages_for_profile_update],
                    user_message = user_message,
                    )
                )
            task_list['profile_update_task'] = profile_update_task
        
         # Check if it's time to update the emotional journal.
        if self.message_count % self.settings.messages_till_journal_update == 0:
            journal_update_task = asyncio.create_task(
                self.emotioal_journal.update_journal(
                    chat_history = self.chat_history[-self.settings.messages_for_journal_update:]
                    )
                )
            task_list['journal_update_task'] = journal_update_task

        # Gather results from tasks concurrently.
        results = await asyncio.gather(*task_list.values())

        # Process tools results if the tools task was created.
        if task_list.get('tools_task'):
            tools_results = results.pop(0)
            
            tools_result, metadata = tools_results

            if self.tools.total_tokens_used:
                self.total_tokens_used['Tools'] = self.tools.total_tokens_used
        else:
            tools_result, metadata = None, None

        # Process profile update results if the profile update task was created.
        if task_list.get('profile_update_task'):
            profile_update, profiler_used_tokens = results.pop(0)

            if profiler_used_tokens:
                self.total_tokens_used['Profiler'] = profiler_used_tokens
        else:
            profile_update = None

        # Process journal update results if the journal update task was created.
        if task_list.get('journal_update_task'):
            journal_result = results.pop(0)
            journal, updates_count, journal_date, journal_used_tokens =  journal_result

            journal_update = journal, updates_count, journal_date
            print("Journal update: \n",journal_update, '\n' , '_'*100)

            if journal_used_tokens:
                self.total_tokens_used['Journal'] = journal_used_tokens
        else:
            journal_update = None
        
        #  Initiate prompt to add tools result.
        prompt = ""
        
        # Check if tools returned metadata
        if metadata is not None:

            # If tool executed successfuly, add result to prompt
            if metadata.get('type') == 'tool_result':
                prompt += tools_result_additon(tools_result)
            
            # If tool missing inputs, return everything and skip generating response.
            elif metadata.get('type') == 'input_request':
                response = None
                return response, metadata, profile_update, journal_update
            else:
                print("Unexpected result of the tool. Metadata:", metadata)
                return

        # Create system message and prompt for the responder.
        system_message = responder_system_message('\n'.join(self.user_profile.user_profile))
        system_message += '\n' + personality_addition(self.settings.responder_personality)

        prompt += responder_prompt(chat_history = '\n'.join(self.chat_history[-CHAT_HISTORY_MESSAGES_FOR_RESPONDER:]),  user_message = user_message)
        print(f"- _Responder_ Sysytem prompt:\n{system_message}\n- Prompt:\n{prompt}\n{'_'*100}")

        # Request a response from the OpenAI GPT model.
        response, responder_used_tokens = await openai_chat_request(
            prompt=prompt,
            system=system_message,
            model=self.settings.responder_gpt_model)
        
        # Gather token usage statistics.
        if responder_used_tokens:
            self.total_tokens_used['Responder'] = responder_used_tokens

        print(f"- !!! Final results:\nResponse:{response}\nMetadata:{metadata}\nProfile:{profile_update}\nJournal:{journal_update}\n{'_'*100}")
        return response, metadata, profile_update, journal_update

    async def handle_user_inputs(self, tool: str, inputs: dict[str, str]) -> (str, dict[str, str]):
        """
        Process and handle user inputs for a specific tool.

        Args:
        - tool (str): Name of the tool.
        - inputs (dict): Dictionary containing user inputs for the tool.

        Returns:
        - Tuple containing response and metadata.
        """
        # Apply moderation to the user's inputs.
        flagged, flagged_categories = self.moderation.moderate(user_message=str(inputs))
        if flagged:
            message = f"Ill content of message. Categories:{flagged_categories}"
            print(message)
            return message, None
        # # Remove CSRF token from inputs.
        # if inputs.get('csrfmiddlewaretoken'):
        #     del inputs['csrfmiddlewaretoken']

        tools_result, metadata = await self.tools.run_tools([tool], inputs)

        prompt = ""
        if metadata is not None:
            if metadata.get('type') == 'tool_result':
                prompt += tools_result_additon(tools_result)
                
            elif metadata.get('type') == 'input_request':
                response = None
                return response, metadata
            
        system_message = responder_system_message('\n'.join(self.user_profile.user_profile))
        prompt += responder_prompt('\n'.join(self.chat_history[-CHAT_HISTORY_MESSAGES_FOR_RESPONDER:]))

        print(f"{'_'*100}\nSystem message:\n{system_message}\nPrompt:\n{prompt}")

        response, responder_used_tokens = await openai_chat_request(
            prompt = prompt,
            system = system_message,
            model = self.settings.responder_gpt_model
        )

        if responder_used_tokens:
            self.total_tokens_used['Responder'] = responder_used_tokens

        return response, metadata
def responder_system_message(user_profile):
    return dedent(f"""\
You are a helpful wellbeing assistant.
You care about user and trying to make users mental and physical health better.
You have a chat history as a context, focus on answering to LAST USER MESSAGE.
You have a user profile to better understand user:|
{user_profile}|""")

def responder_prompt(chat_history: str, user_message: str = None):
    if user_message:
        return f"""\
Previous conversation|
{chat_history}
LAST USER MESSAGE:{user_message}|
Your responce:"""
    else:
        return f"""\
Previous conversation|
{chat_history}|
Your responce:"""

def tools_result_additon(tools_result):
    return f"""\
It seems like user used tool in conversation. Notify him about result of a tool.
Tool result:|
{tools_result}|"""

def personality_addition(personality):
    return f"""\
Here is your personality, please respond accordingly to it:|
{personality}|"""                        