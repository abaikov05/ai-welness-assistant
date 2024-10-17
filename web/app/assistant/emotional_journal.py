from .helpers import openai_chat_request

from datetime import date
from textwrap import dedent
import json

class EmotionalJournal():
    def __init__(self, journal: str, updates_count: int, gpt_model: str) -> None:
        """
        Initialize the EmotionalJournal class with necessary attributes.

        Args:
        - journal (str): Serialized JSON string representing the emotional journal.
        - updates_count (int): Number of updates made to the emotional journal.
        - journal_date (class): Date associated with the emotional journal.
        - current_date (class): Current date.

        """
        # self.journal_date = journal_date

        # Why the fuck I need this if it gets of creates current date journal in consumers?
        
        # self.current_date = current_date
        
        # if journal_date != current_date or not journal:
        #     self.journal = {}
        # else:
        #     self.journal = json.loads(journal)
        self.journal = json.loads(journal)

        if updates_count:
            self.updates_count = updates_count
        else:
            self.updates_count = 0
        self.gpt_model = gpt_model

    async def update_journal(self, chat_history: list) -> tuple[dict, int, date, dict]:
        """
        Update the emotional journal based on the analysis of the provided chat history.

        Args:
        - chat_history: String containing the conversation history.

        Returns:
        - Tuple containing the updated emotional journal, updates count, journal date, and token usage.

        """
        # System message with instruction
        system = dedent("""\
        Your task is to deeply analize conversation and give a mark to common primal emotions that user might feel.
        Mark must always be in range 0-100.
        Your response is always JSON file with this format:
        {
            "emotion_name": "mark",
            "emotion_name": "mark",
            ...
        }""")
        
        # Prase chat history list to string
        chat_history = '\n'.join(chat_history)
        # Create a prompt with chat history
        prompt = f"Conversation:|\n{chat_history}|"

        # Request a response from the OpenAI GPT model.
        response, token_usage = await openai_chat_request(prompt = prompt, system = system, model = self.gpt_model)

        print("_"*20)
        print("--- Journal prompt:\n",prompt, "\n--- Journal update response:\n", response)
        print("_"*20)
        
        # If response exists
        if response is not None:
            # Attempt to parse the response as JSON
            try:
                response = json.loads(response)
                
                # Try to parse values to float and deletes not valid elements from response
                for key, value in list(response.items()):
                    try:
                        value = float(value)
                        if not (0 <= value <= 100):
                            del response[key]
                    except:
                        del response[key]
                        
                # If the response is empty dictionary don't update the journal
                if len(response) == 0:
                    return None, None, token_usage
                
            # Handle the case where the response has an unexpected format
            except:
                print("Wrong emotional journal format from GPT")
                return None, None, token_usage
        
        # Handle the case where GPT did not provide any response
        else:
            # Check if there were token usage despite no response
            if token_usage is not None:
                print("GPT tried to update emotional journal but no changes were made!")
                return None, None, token_usage
            
            # Return None for all values if there was no response and token usage
            return None, None, None
        
        # Increment the count of updates made to the emotional journal
        self.updates_count += 1
        
        # If it is the first update, simply save response as a journal.
        if self.updates_count <= 1:
            self.journal = response
            return self.journal, self.updates_count, token_usage
        else:
            # Update avarage scores of emotions that are not in response
            for key, value in self.journal.items():
                if not response.get(key):
                    self.journal[key] = round((float(value) * (self.updates_count - 1) + 0) / self.updates_count ,2)
                    
            # Than update emotions that are in response
            for key, value in response.items():
                if self.journal.get(key):
                    self.journal[key] = round((float(self.journal[key]) * (self.updates_count - 1) + float(value)) / self.updates_count ,2)
                else:
                    self.journal[key] = round(float(value)/self.updates_count, 2)

        return self.journal, self.updates_count, token_usage