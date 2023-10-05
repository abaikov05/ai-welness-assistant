from helpers import openai_chat_request
from textwrap import dedent

async def extract_tools(previous_message: str, user_message: str) -> list[str] | None:
    """
    Description: ...
    - previous_message: ...
    - user_message: ...
    """
    tools_list = [{'name': 'weather', 'description': 'tells current weather'},
                  {'name': 'news', 'description': 'tells latest news'}]
    
    system_message = dedent(f"""Your task is to decide what tools are necessary to respond to user.
    Your responce is always a string of tools delimeted by comma. Follow this format:
    "{{tool_name}}, {{tool_name}}, ..."
    If there is no necessary tools to use from list of tools, your responce must be empty.
    NEVER RESPOND USER DIRECTLY!
    You can only choose tools from this list:
    """)
    for tool in tools_list:
        system_message += f"Name: {tool['name']}; Description: {tool['description']}\n"
    
    messages = dedent(f"""Previous message: {previous_message}
    User message: {user_message}""")
    
    responce = await openai_chat_request(prompt=messages, system=system_message)
    #For debug 
    print(messages, system_message, responce)

    if responce and responce.strip() != '':
        responce = responce.split()
        valid_tools = []
        for item in responce:
            for tool in tools_list:
                if item == tool['name']:
                    valid_tools.append(item)
        return valid_tools
    
    else:
        print("No tools to use!")
        return None
