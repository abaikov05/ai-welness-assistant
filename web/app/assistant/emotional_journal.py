from .helpers import openai_chat_request

from datetime import date
from textwrap import dedent
import json

class EmotionalJournal():
    def __init__(self, journal: str, updates_count: int, journal_date: date, current_date: date, gpt_model: str) -> None:
        """
        Initialize the EmotionalJournal class with necessary attributes.

        Args:
        - journal (str): Serialized JSON string representing the emotional journal.
        - updates_count (int): Number of updates made to the emotional journal.
        - journal_date (class): Date associated with the emotional journal.
        - current_date (class): Current date.

        """
        self.current_date = current_date
        self.journal_date = journal_date

        if journal_date != current_date or not journal:
            self.journal = {}
        else:
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
        Your responce is always JSON file with this format:
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
        responce, token_usage = await openai_chat_request(prompt = prompt, system = system, model = self.gpt_model)

        print("Journal:\n",prompt,'\n', responce)

        # Check if response exists
        if responce is not None:
            # Attempt to parse the response as JSON
            try:
                responce = json.loads(responce)

            # Handle the case where the response has an unexpected format
            except:
                print("Wrong emotional journal format from GPT")
                return None, None, None, token_usage
        
        # Handle the case where GPT did not provide any response
        else:
            # Check if there were token usage despite no response
            if token_usage is not None:
                print("GPT tried to update emotional journal but no changes were made!")
                return None, None, None, token_usage
            
            # Return None for all values as there is response and token usage
            return None, None, None, None
        
        # Increment the count of updates made to the emotional journal
        self.updates_count += 1

        # Update the emotional journal based on the response
        for item in responce.items():
            key, value = item

            # If the emotion is already present in the journal, update the average score
            if self.journal.get(key):
                self.journal[key] = round((self.journal[key] + (float(value) - self.journal[key]) / self.updates_count), 2)
            # If the emotion is new, set the initial avarage score
            else:
                self.journal[key] = float(value) / self.updates_count

        return self.journal, self.updates_count, self.journal_date, token_usage