from .helpers import openai_chat_request
from textwrap import dedent
import json

# Import all tool functions
from .Tools.tools_functions import *

from .settings import TOOLS_DEBUG
# FIXME Names of tools in browser

# rename "found_inputs" to "inputs". "inputs" should contain all inputs and if there is no input than {"input1": None} 
class Tools():
    """
    This class ir core component for managing and executing tools within the AI Wellbeing Assistant.
    It manages the extraction of relevant tools and inputs based on user messages and conversation context,
    as well as the execution of these tools.
    """
    def __init__(self, gpt_model:str, tools_path = "web/app/assistant/Tools/tools_list.txt"):
        """
        Initialize the Tools class with a GPT model and a path to the tools list.

        Args:
        - gpt_model (str): OpenAI GPT model name.
        - tools_path (str): Path to the file containing the list of dictionaries with description of available tools.
        """
        # Read and store the tools list with all tools descriptions from the specified file
        with open(tools_path, 'r', encoding='utf-8') as file:
            # Read the tools list from the specified file
            self.tools_list = eval(file.read())

        # Set the GPT model for the Tools GPT requests
        self.gpt_model = gpt_model

        # Dictionary to track the total tokens used for GPT prompts and responces
        self.total_tokens_used = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }

    async def extract_tools(self, user_message: str, previous_message: str) -> list[str]:
        """
        Extracts relevant tools based on the user's message and previous message context.
        
        This function uses the OpenAI GPT model to analyze the user's message and identify if there
        is an intention to use a tool. The function provides information about available tools to the model.
        The response is processed, and a list of tool names is returned if any relevant tools are identified.

        Args:
        - user_message (str): The current user message.
        - previous_message (str): The previous message in the chat.

        Returns:
        A (list) of relevant tools (str) extracted from the user's message, or None if no tools are detected.
        
        If no tools are found, the function returns None.
        """
        # Construct a system message providing task and context about available tools.
        system_message = dedent(f"""\
        Your task is to identify if the user intends to use a tool from the provided list below.
        - YOU RESPOND WITH A TOOL ONLY IF YOU ARE 100% SURE USER WNATS TO USE IT.
        - If there are no relevant tools to use, your response MUST BE EMPTY.
        - Your response is always only a string of tools delimited by a comma. Follow this format:
        "tool_name, tool_name, ..."
        - NEVER RESPOND DIRECTLY TO THE USER!
        - You can only choose tools from this list:
        """)

        # Append tool information to the system_message.
        for tool in self.tools_list:
            system_message += f"Name: {tool['name']}; Description: {tool['description']}\n"

        # Construct prompt with conversation context.
        prompt = dedent(f"""\
        NEVER RESPOND USER DIRECTLY!
        Previous message: {previous_message}
        User message: {user_message}""")

        # Request a response from the OpenAI GPT model.
        response, token_usage = await openai_chat_request(prompt=prompt, system=system_message, model=self.gpt_model)

        # Gather token usage statistics.
        if token_usage:
            self.total_tokens_used = {key: self.total_tokens_used[key] + token_usage[key] for key in self.total_tokens_used}

        # Debugging information.
        if TOOLS_DEBUG: print(f"{'_'*20}\nTool extraction:\n{prompt}\n{system_message}\n{response}\n{'_'*20}")

        # Process the GPT response if it is not empty. If responce is empty, GPT not found available tools to use.
        if response and response.strip() != '':

            # Remove spaces and split the response into a list of tool names.
            response = response.replace(' ', '')
            response = response.split(',')

            valid_tools = []

            # Validate and filter tool names against the valid tools list.
            for item in response:
                for tool in self.tools_list:
                    if item == tool['name']:
                        valid_tools.append(str(item))

            # Return the list of tool names if found, otherwise, return None.
            if valid_tools:
                return valid_tools
            else:
                if TOOLS_DEBUG: print('GPT tied to extract tools but found no valid tools to use')
                return None
        
        else:
            if TOOLS_DEBUG: print('GPT tied to extract tools but found no tools to use')
            return None
        
    def get_tool(self, tool_name: str) -> dict:
        """
        Little helper function that retrieves all information about a specific tool from the available tools list based on its name.

        Args:
        - tool_name (str): The name of the tool to retrieve.

        Returns:
        dict or None: A dictionary containing information about the tool if found, or None if not found.
        """
        for tool in self.tools_list:
            if tool['name'] == tool_name:
                return tool
            
        if TOOLS_DEBUG: print(f"Tool '{tool_name}' not found!")    
        return None
    
    async def extract_inputs(self, tool_name: str, chat_history: str) -> tuple[dict[str, str | None], list[str | None]] | None:
        """
        Extracts inputs for a specified tool from the conversation and returns a dictionary of inputs and list of missing inputs.
        This function uses the OpenAI GPT model to analyze the conversation and extract inputs for a specified tool function.
        
        Args:
        - tool_name (str): The name of the tool for which inputs are to be extracted.
        - chat_history (str): The conversation history.

        Returns:
        (dict | None, list): A tuple containing a dictionary of extracted inputs (or None) and a list of missing required inputs.

        - If an input has '(optional)' in the description, it can be empty and will be None in inputs dictionary.
        
        - If there are no inputs in user messages or a required input is missing, the function returns a tuple with None
        and a list of missing required inputs.

        - If no response or an error occurs during input extraction, the function returns None for inputs and a list of missing required inputs.
        """
        # Get information about the tool
        tool = self.get_tool(tool_name)

        # Construct a system message providing task.
        system_message = dedent("""\
        Extract inputs for the described function from the conversation and respond with a JSON file containing inputs.
        Follow this format:
        {
            "input_name1": "input1",
            "input_name2": "input2",
            ...
        }
        Ensure all inputs are in the same sequence as described.
        If an input has '(optional)' in the description, it can be empty.
        If there are no inputs in user messages or a required input is missing, your response MUST BE EMPTY.
        If there are no inputs, leave the input field EMPTY.
        Analyze the entire chat for input extraction.""")

        # Construct a prompt providing information about tool to extract inputs for.
        prompt = dedent(f"""\
        Function name: {tool['name']}
        - Function description: {tool['description']}
        - Function inputs: {str(tool['inputs'])}
        - Inputs description: {tool['inputs_description']}
        - Conversation: |
        """) + chat_history + "\nRemember the format!"

        # Request a responce
        response, token_usage = await openai_chat_request(prompt=prompt, system=system_message, model=self.gpt_model)

        # Gather token usage statistics.
        if token_usage:
            self.total_tokens_used = {key: self.total_tokens_used[key] + token_usage[key] for key in self.total_tokens_used}

        # Debug information.
        if TOOLS_DEBUG: print(f"{'_'*20}\nInput extraction:\n{prompt}\n{system_message}\n{response}\n{'_'*20}")

        # Process the response to extract inputs.
        if response and response.strip() != '':
            inputs = {}
            missing_inputs = []
            try:
                # Try to parse the GPT response as JSON.
                response = json.loads(response)

                # Iterate over the expected inputs for the tool.
                for input in tool['inputs']:
                    # Get the value of the valid input from the parsed response.
                    response_input = response.get(input)
                    
                    # If the input is found in the response and is not empty, add it to the inputs dictionary.
                    if response_input and response_input.strip() != '':
                        inputs[input] = response_input

                    # If the input is not found, check if it is a required input.
                    else:
                        for required_input in tool['required_inputs']:
                            # If input is required, add the input to the list of missing inputs.
                            if input == required_input:
                                if TOOLS_DEBUG: print('Required input not found! -', input)
                                missing_inputs.append(input)
                                
                        # Set the input value to None if input is optional.
                        inputs[input] = None

                # Return the extracted inputs and the list of missing required inputs.
                return inputs, missing_inputs
            
            # Handle exceptions that may occur during JSON parsing and return None.
            except Exception as e:
                print('Error in input format from GPT', e)
                # Return None as tool inputs and tool's required inputs as missing
                missing_inputs = tool['required_inputs']
                
                return None, missing_inputs
        else:
            # If GPT did not find any inputs, print a message.
            if TOOLS_DEBUG: print("GPT did not find any inputs!")
            missing_inputs = tool['required_inputs']
            # Return None as tool inputs and tool's required inputs as missing
            return None, missing_inputs
    
    def ask_for_inputs(self, tool_name: str, missing_inputs: list, inputs: None|dict = None ):
        """
        Generates metadata for the input request.

        Args:
        - tool_name (str): The name of the tool for which inputs are requested.
        - missing_inputs (list): List of missing required inputs for the tool.
        - inputs (dict): (Optional) Dictionary containing already found inputs.

        Returns:
        - Tuple containing tool_result (None) and metadata dictionary.
        """
        # Get information about the tool
        tool = self.get_tool(tool_name)

        # If no found inputs are not provided, create an dictionary with inputs as a key and set all values to empty string.
        if inputs == None:
            inputs = {}
            tool_inputs = tool['inputs']
            for input in tool_inputs:
                inputs[input] = None

        # Create metadata dictionary for the input request.
        metadata = {
            "type": "input_request",
            "tool": tool_name,
            "found_inputs": inputs,
            "missing_inputs": missing_inputs,
            "inputs_description": tool['inputs_description']
        }

        # Tool is missing inputs, so result is None
        tool_result = None
        
        # Print information for debugging.
        if TOOLS_DEBUG: print(f"{'_'*20}\nAsking for inputs:\nTool result:\n{tool_result}\nMetadata:\n{metadata}\n{'_'*20}")
        
        return tool_result, metadata
    
    async def run_tools(self, tools_list: list[str], inputs: dict[str, str] = None) -> tuple[str | None, dict[str, str]]:
        """
        Run the specified tools with given inputs.

        Args:
        - tools_list (list): List of tools to be executed.
        - inputs (dict): Dictionary containing inputs for the first tool.

        Returns:
        - Tuple containing output of the tool and metadata dictionary.
        """

        # Get the first tool from the list and remove it from the list.
        tool = self.get_tool(tools_list.pop(0))

        # Check if the tool requires inputs.
        if tool['needs_inputs']:

            # Check if inputs are provided.
            if inputs:
                try:
                    # Try to execute the tool with the provided inputs.
                    tool_result = tool['function_name'](**inputs)
                    metadata = {
                        "type": "tool_result",
                        "tool": tool['name'],
                        "found_inputs": inputs,
                    }
                    return tool_result, metadata
                
                # Handle exceptions during tool execution.
                except Exception as e:

                    # If the tool fails to execute, create a message with description of an error and
                    # metadata with input request to get correct input data from user and rerun the tool.
                    if TOOLS_DEBUG: print("Recived exception running tool:\n", e, '\n', 'Inputs:\n', inputs)
                    tool_result = await self.describe_input_error(tool, inputs, e)
                    metadata = {
                        "type": "input_request",
                        "tool": tool['name'],
                        "found_inputs": inputs,
                        "missing_inputs": [],
                    }
                    return tool_result, metadata
            else:
                # If inputs are not provided, ask for inputs.
                tool_result, metadata = self.ask_for_inputs(tool_name = tool['name'], missing_inputs = tool["inputs"])
                return tool_result, metadata
        else:
            # If the tool does not need inputs, execute the tool without inputs.
            tool_result = tool['function_name']()
            metadata = {
                        "type": "tool_result",
                        "tool": tool['name']
                        }
            return tool_result, metadata

    async def handle_tools(self, extract_inputs: bool, user_message: str, chat_history: list, messages_for_input_extraction: int) -> tuple[str, dict] | tuple[None, None]:
        """
        Handle the extraction and execution of tools based on user message and chat history.

        Args:
        - extract_inputs (bool): Boolean indicating whether to extract inputs for tools.
        - user_message (str): Current user message.
        - chat_history (list): List of previous chat messages.
        - messages_for_input_extraction (int): Number of messages to consider for input extraction.

        Returns:
        - Tuple containing output of the tool and metadata dictionary.
        """

        # Extract tools from the user's message and previous chat message.
        extracted_tools = await self.extract_tools(
            user_message = user_message,
            previous_message = chat_history[-1]
        )
        
        # If tool detected in chat
        if extracted_tools:

            # Check if the first extracted tool needs inputs.
            if self.get_tool(extracted_tools[0])['needs_inputs']:

                # If inputs extraction is on.
                if extract_inputs is True:

                    # Extract inputs for the tool.
                    inputs, missing_inputs = await self.extract_inputs(
                        tool_name = extracted_tools[0],
                        chat_history = '\n'.join(chat_history[:messages_for_input_extraction])+ "\nLast user message: " + user_message
                    )

                    # If there are missing inputs, create message and metadata asking for inputs.
                    if missing_inputs:
                        tool_result, metadata = self.ask_for_inputs(
                            tool_name = extracted_tools[0],
                            missing_inputs = missing_inputs,
                            inputs = inputs
                        )
                        return tool_result, metadata
                    
                    # If inputs are passed, run the tools.
                    if inputs is not None:
                        tool_result, metadata = await self.run_tools(
                            tools_list = extracted_tools,
                            inputs = inputs
                    )
                        return tool_result, metadata
                    
                # If inputs extraction turned off, create message and metadata asking for inputs.
                else:
                    tool = self.get_tool(extracted_tools[0])
                    inputs = None
                    missing_inputs = tool['required_inputs']
                    
                    tool_result, metadata = self.ask_for_inputs(extracted_tools[0], missing_inputs, inputs)
                    return tool_result, metadata
                
            # If the tool does not need inputs, run the tool without inputs.
            else:
                tool_result, metadata = await self.run_tools(extracted_tools, inputs=None)
                return tool_result, metadata
            
        # If no tools are detected, return None, None.
        else:
            if TOOLS_DEBUG: print("No tools detected!")
            return None, None
    
    async def describe_input_error(self, tool: dict, inputs: dict, exeption: str):
        """
        Generate a description for the exception raised during tool execution.

        Args:
        - tool (dict): Dictionary containing all information about the tool.
        - inputs (dict): Dictionary containing inputs for the tool.
        - exception (str): Exception raised during tool execution.

        Returns:
        - Response generated based on the exception for user understanding.
        """

         # Provide instructions for translating the exception.
        system_message = dedent("""Your task is to translate exeption raised calling function.
        Your response should be short and simple to uderstand for unexpierienced user.
        Don't say function(), insted call it tool.
        Ask for correct inputs.""")

        # Create a prompt with details about the exception and inputs.
        prompt = dedent(f"""Exeeption: {exeption}
        Inputs that tool needs: {tool['inputs_description']}
        Inputs passed: {inputs}""")

        # Request a response from GPT
        response, token_usage = await openai_chat_request(prompt=prompt, system=system_message, model=self.gpt_model)

        # Gather token usage statistics.
        if token_usage:
            self.total_tokens_used = {key: self.total_tokens_used[key] + token_usage[key] for key in self.total_tokens_used}

        return response
    
    # def tool_needs_input(self, tool_name:str):
    #     """
    #     Small helper function to check if a given tool requires input based on its name.

    #     Args:
    #     - tool_name (str): Name of the tool to check.

    #     Returns:
    #     - True if the tool requires input, False otherwise.
    #     """
    #     tool = self.get_tool(tool_name)
    #     return tool['needs_inputs']