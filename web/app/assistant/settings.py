# Here are ajuastable settings

# Enries to load per 1 request
CHAT_MESSAGES_TO_LOAD_PER_REQUEST = 20
EMOTIONAL_JOURNALS_TO_LOAD_PER_REQUEST = 4

# At this time there are only 2 cost-efficient models
AVAILABLE_GPT_MODELS = [
    'gpt-4o',
    'gpt-4o-mini',
]
# 1000 tokens price for every model
GPT_MODELS_PRICING = {
    'gpt-4o':{'input': 0.0025, 'output': 0.01},
    'gpt-4o-mini':{'input': 0.00015, 'output': 0.0006},
}
# Responder constants
MESSAGES_TO_PASS_TO_ASSISTANT = 21
CHAT_HISTORY_MESSAGES_FOR_RESPONDER = 5

# Profiler constants
MIN_MESSAGES_FOR_PROFILE_UPDATE = 1
MAX_MESSAGES_FOR_PROFILE_UPDATE = 10

MIN_MESSAGES_TILL_PROFILE_UPDATE = 1
MAX_MESSAGES_TILL_PROFILE_UPDATE = 21
# Emotional journal constants
MIN_MESSAGES_FOR_JOURNAL_UPDATE = 1
MAX_MESSAGES_FOR_JOURNAL_UPDATE = 10

MIN_MESSAGES_TILL_JOURNAL_UPDATE = 1
MAX_MESSAGES_TILL_JOURNAL_UPDATE = 21
# Tools constants 
MIN_MESSAGES_FOR_INPUT_EXTACTION = 1
MAX_MESSAGES_FOR_INPUT_EXTACTION = 10

# Recommender
RECOMMENDER_TREE_PATH = "web/app/assistant/Recommendations/recomendation_tree.pkl"
RECOMMENDER_RECOMMENDATIONS_PATH = "web/app/assistant/Recommendations/recommendations.txt"
RECOMMENDATION_CATEGORIES = [
    "Sport", "Nutrition","Sleep", 
    "Stress", "Mental Health", "Social", 
    "Self-Care", "Motivation", "Resilience", 
    "Body", "Mindfulness", "Positive Thinking"
]

# Debug options
RECOMMENDER_DEBUG = True
CONSUMERS_DEBUG = True
TOOLS_DEBUG = True
EMOTIONAL_JOURNAL_DEBUG = True
RESPONDER_DEBUG = True
PROFILE_DEBUG = True

class AssistantSettings:
    """
    AssistantSettings class encapsulates configuration settings for the assistant.
    """
    def __init__(self, 
            responder_gpt_model: str,
            profiler_gpt_model: str = None,
            journal_gpt_model: str = None,
            messages_for_profile_update: int = None,
            messages_till_profile_update: int = None,
            messages_for_input_extraction: int = None,
            messages_till_journal_update: int = None,
            messages_for_journal_update: int = None,
            responder_personality: str = None,
            ) -> None:
        
        self.responder_gpt_model = responder_gpt_model
        self.responder_personality = responder_personality
        self.profiler_gpt_model = profiler_gpt_model
        self.journal_gpt_model = journal_gpt_model
        self.messages_till_profile_update = messages_till_profile_update
        self.messages_for_profile_update = messages_for_profile_update
        self.messages_for_input_extraction = messages_for_input_extraction
        self.messages_till_journal_update = messages_till_journal_update
        self.messages_for_journal_update = messages_for_journal_update