import openai

class ModerationBot:
    """
    This class takes user message as input and returns:
      - True/False - whether the message has been flagged
      - The categories if True
    """

    def __init__(self, user_id=None):
        self.user_id = user_id

    # A function to check user message for ill-intent

    def moderate(self, user_message):

        # Wait until response is received
        response = openai.Moderation.create(input=user_message)

        # Process moderation response
        flagged = response['results'][0]['flagged']
        flagged_categories = []

        # If message has ill-intent
        if flagged:
        
            # Extract categories that describe message's ill-intent
            categories = response['results'][0]['categories']
            flagged_categories = [category for category,
                                  value in categories.items() if value]
            # make user message as flagged categories for analytics 
            user_message = [f"Message flagged as: {flagged_categories}"]
            
        return flagged, flagged_categories