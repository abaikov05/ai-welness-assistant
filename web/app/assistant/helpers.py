import asyncio
import openai


async def openai_chat_request(prompt=None, messages=None, system="You are a helpful assistant.", model="gpt-4o-mini", max_retries=5, temperature=1, max_tokens=1000, timeout=5):
    """
    This function makes a chat request to OpenAI and returns the response and information about used tokens.
    In case of an error, or if the request takes longer than 'timeout' seconds, it retries up to 'max_retries' times with exponential backoff.
    """
    if not messages:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ]
    wait_time = 0.1

    for _ in range(max_retries):
        try:
            chat_completion_resp = await asyncio.wait_for(openai.ChatCompletion.acreate(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            ), timeout=timeout)

            if 'choices' in chat_completion_resp:
                response = chat_completion_resp['choices'][0]['message']['content']
                token_usage = chat_completion_resp['usage']
                return response, token_usage
            else:
                raise Exception(f"Unexpected response from OpenAI API: {chat_completion_resp}")
        except asyncio.TimeoutError:
            print(f"OpenAI response timed out, retrying in {wait_time} seconds...")
        except Exception as e:
            print(f"Error occurred in OpenAI response: {e}, retrying in {wait_time} seconds...")
            
        await asyncio.sleep(wait_time)
        wait_time *= 2

    print("Maximum retries reached.")
    return None, None
