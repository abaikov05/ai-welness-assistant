from helpers import openai_chat_request
import os
from textwrap import dedent

class Profile:

    def __init__(self, path):
        self.path = path
        if os.path.exists(self.path):
            with open(self.path, 'r', encoding="utf-8") as file:
                self.profile = eval(file.read())
        else:
            with open(self.path, 'x') as file:
                file.write('{1: "Change this one!"}')

    async def update_user_profile(self, previous_message: str, user_message: str) -> None:

        profile_changes = eval(await self.generate_user_profile(previous_message=previous_message, user_message=user_message))
        print("Last profile:\n", self.profile)

        for i in profile_changes:
            self.profile[i] = profile_changes[i]

        print("New profile:\n", self.profile)

        with open(self.path, 'w') as file:
            file.write(self.profile)
        return None

    async def generate_user_profile(self, previous_message: str, user_message: str) -> str:

        system_message = dedent("""\
        Your task is to update or generate (if no profile is passed) user profile from recent chat.
        Only write user preferences, what user likes or dislikes and information about user personality.
        Your responce should be short, but descriptive.
        - If there no changes must be made to user profile your responce is empty.
        - If there is something new info about user, add it in user profile and mark it (new).
        - DO NOT DELETE OR REPLACE ANY PART OF USER PROFILE IF IT'S NOT UPDATED.
        NEVER RESPOND USER DIRECTLY!
        Follow this JSON format:
        {number: "Changed text of this element", number: "Changed text of this element"}
        """)

        prompt = dedent(f"""\
        |USER PROFILE:
        {self.profile}|

        |RECENT_CHAT:
        Previous message: {previous_message}
        User message: {user_message}|
        Remember format: {{number: "Changed text of this element", number: "Changed text of this element"}}
    """)
        
        responce = await openai_chat_request(prompt=prompt, system=system_message, temperature=0.8)
        print("Generated user prifile changes:", responce)

        return responce
    
    def delete_profile(self) -> None:

        os.remove(self.path)
        print('Profile removed')

        return None