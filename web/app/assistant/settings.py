# Here are ajuastable settings 
CHAT_MESSAGES_TO_LOAD_PER_REQUEST = 20
EMOTIONAL_JOURNALS_TO_LOAD_PER_REQUEST = 4

AVAILABLE_GPT_MODELS = [
    'gpt-3.5-turbo-instruct',
    'gpt-3.5-turbo-1106',
    'gpt-3.5-turbo-16k',
    'gpt-3.5-turbo',

    'gpt-4-1106-preview',
    'gpt-4-32k-0613',
    'gpt-4-32k',
    'gpt-4'
]
# 1000 tokens price for every model
GPT_MODELS_PRICING = {
    'gpt-3.5-turbo-instruct':{'input': 0.0015, 'output': 0.002},
    'gpt-3.5-turbo-1106':{'input': 0.001, 'output': 0.002},
    'gpt-3.5-turbo-16k':{'input': 0.003, 'output': 0.004},
    'gpt-3.5-turbo':{'input': 0.0015, 'output': 0.002},

    'gpt-4-1106-preview':{'input': 0.01, 'output': 0.03},
    'gpt-4-32k-0613':{'input': 0.06, 'output': 0.12},
    'gpt-4-32k':{'input': 0.06, 'output': 0.12},
    'gpt-4':{'input': 0.03, 'output': 0.06}
}

MESSAGES_TO_PASS_TO_ASSISTANT = 21

CHAT_HISTORY_MESSAGES_FOR_RESPONDER = 5

MIN_MESSAGES_FOR_PROFILE_UPDATE = 1
MAX_MESSAGES_FOR_PROFILE_UPDATE = 10

MIN_MESSAGES_TILL_PROFILE_UPDATE = 1
MAX_MESSAGES_TILL_PROFILE_UPDATE = 21

MIN_MESSAGES_FOR_JOURNAL_UPDATE = 1
MAX_MESSAGES_FOR_JOURNAL_UPDATE = 10

MIN_MESSAGES_TILL_JOURNAL_UPDATE = 1
MAX_MESSAGES_TILL_JOURNAL_UPDATE = 21

MIN_MESSAGES_FOR_INPUT_EXTACTION = 1
MAX_MESSAGES_FOR_INPUT_EXTACTION = 10


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