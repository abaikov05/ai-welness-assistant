import openai
from openai import OpenAI

from dotenv import load_dotenv
load_dotenv()
client = OpenAI()

class Moderation:
    """
    This class takes user message as input and returns:
      - True/False - whether the message has been flagged
      - The categories if True
    """
    def moderate(self, user_message, model='omni-moderation-latest'):
        '''A function to check user message for ill-intent'''
        # Wait until response is received
        response = client.moderations.create(input=user_message, model=model)

        # Process moderation response
        flagged = response.results[0].flagged
        flagged_categories = []

        # If message has ill-intent
        if flagged:
        
            # Extract categories that describe message's ill-intent
            categories = response.results[0].categories.model_dump()
            flagged_categories = [category for category,
                                  value in categories.items() if value]
            
        return flagged, flagged_categories