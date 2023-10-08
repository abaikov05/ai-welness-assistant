from moderation import ModerationBot
from tools_extrctor import extract_tools
from user_profile import Profile
import asyncio

class Responder():
    def __init__(self, profile_path = '/user_profile'):
        self.moderation = ModerationBot()
        self.user_profile = Profile(profile_path)

    async def handle_user_message(self, user_message) -> str:
        
        flagged, flagged_categories = self.moderation.moderate(user_message=user_message)
        if flagged:
            print(f"Ill content of message. Categories:{flagged_categories}")
            return None

        previous_message = "ADD CHAT HISTORY MODULE"
        tools_extraction_task = asyncio.create_task(
            extract_tools(previous_message=previous_message, user_message=user_message)
        )

        update_profile_task = asyncio.create_task(
            self.user_profile.update_user_profile(previous_message=previous_message, user_message=user_message)
        )

        result = await asyncio.gather(
                             tools_extraction_task,
                             update_profile_task)
        return result
        