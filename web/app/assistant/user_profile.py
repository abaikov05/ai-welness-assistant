from .helpers import openai_chat_request
from textwrap import dedent
import os
import json

class Profile:
    """
    Represents a user profile and provides methods to generate and update the profile using GPT responses.

    Methods:
        __init__(user_profile: str, gpt_model: str) -> None:
            Initializes the Profile object with the user's profile and the specified GPT model.

        async generate_user_profile(previous_messages: str, user_message: str) -> dict|None:
            Utilizes GPT to generate or update the user profile based on recent chat history and the latest user message.

        async update_user_profile(previous_messages: str, user_message: str) -> list|None:
            Updates the user profile by applying the changes suggested by GPT, and returns the updated profile as a list.
    """
    def __init__(self, user_profile: str, gpt_model: str) -> None:
        """
        Initialize the Profile object with user profile and GPT model.

        Args:
            user_profile (str): JSON string representing the user's profile.
            gpt_model (str): The GPT model to use for profile generation.
        """
        self.user_profile = json.loads(user_profile)
        self.profile = {}
        for i, entry in enumerate(self.user_profile):
            self.profile[i] = entry

        self.gpt_model = gpt_model

    async def generate_user_profile(self, previous_messages: str, user_message: str) -> (dict|None, dict|None):
        """
        Generates the user profile based on chat history and the latest user message.

        Args:
            previous_messages (str): Chat history as a string.
            user_message (str): The latest user message.

        Returns:
            Tupple: dictionary representing profile changes or None if no changes are needed
            and dictionary with token usage information.
        """

        # System message with instruction
        system_message = dedent("""\
        Your task is to update or generate a user profile from recent chat.
        Provide concise entries for user preferences, likes, dislikes, and key aspects of the user's personality.
        Your response should be short but descriptive, focusing on the most useful data for understanding the user.
        - If no changes need to be made to the user profile, your response is empty.
        - Don't duplicate the old profile; your response should only include updates.
        - To change an entire entry, respond with {"number": "Changed text of this element"}
        NEVER RESPOND DIRECTLY TO THE USER!
        Follow this JSON format:
        {"1": "Changed text describing the first element", "2": "Changed text describing the second element"}
        """)

        # Compose the prompt for profile generation
        prompt = "PREVIOUS USER PROFILE:|\n" + json.dumps(self.profile) + "\nCHAT HISTORY:|\n" + previous_messages + f"""\
        Last user message: {user_message}|
        |\nRemember format: {{"number": "Changed text of this element", "number": "Changed text of this element"}}"""

        print("- Profiler prompts:\n", system_message, prompt)
        responce, token_usage = await openai_chat_request(prompt=prompt, system=system_message, temperature=0.8, model=self.gpt_model)
        print("- Generated user prifile changes:", responce, '\n', '_'*100)

        # Process and validate the response
        if responce and responce.strip() != '':
            try:  
                responce = json.loads(responce)
                return responce, token_usage
            except Exception as e:
                print("Error in generated user profile format", e)
                return None, token_usage
        else:
            return None, None
        
    async def update_user_profile(self, previous_messages: str, user_message: str) -> (list|None, dict|None):
        """
        Update the user profile based on chat history and the latest user message.

        Args:
            previous_messages (str): Chat history as a string.
            user_message (str): The latest user message.

        Returns:
            Tupple: list with ne profile entries or None if no changes are made
            and dictionary with token usage information.
        """
        # Generate profile changes
        profile_changes, token_usage = await self.generate_user_profile(previous_messages=previous_messages, user_message=user_message)

        print("Last profile:\n", self.profile)
        # Apply profile changes if any
        if profile_changes is not None:

            for i in profile_changes:
                self.profile[i] = profile_changes[i]
            print("New profile:\n", self.profile)

            # Transform profile dictionary to array and return it with token usage statistics
            profile_array = []
            for i in self.profile:
                profile_array.append(self.profile[i])

            return profile_array, token_usage
        else:
            # Handle the case when no profile changes made
            if token_usage is not None:
                print("GPT tried to update profile but no changes were made!")
                return None, token_usage

            return None, None