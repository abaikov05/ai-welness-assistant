import asyncio
import openai

async def openai_chat_request(prompt=None, messages=None, system="You are a helpful assistant.", model="gpt-3.5-turbo-16k", max_retries=5, temperature=1, stream=False, max_tokens=1000, timeout=20):
    """
    This function makes a chat request to OpenAI and returns the response.
    In case of an error, or if the request (non-streaming) takes longer than 'timeout' seconds, it retries up to 'max_retries' times with exponential backoff.
    """
    if not messages:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ]
    wait_time = 0.1

    for _ in range(max_retries):
        try:
            if stream:  # No timeout for streaming requests
                chat_completion_resp = await openai.ChatCompletion.acreate(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    stream=stream,
                    max_tokens=max_tokens
                )
                return chat_completion_resp
            else:  # Apply timeout only when stream=False
                chat_completion_resp = await asyncio.wait_for(openai.ChatCompletion.acreate(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    stream=stream,
                    max_tokens=max_tokens
                ), timeout=timeout)

                if 'choices' in chat_completion_resp:
                    response = chat_completion_resp['choices'][0]['message']['content']
                    return response
                else:
                    raise Exception(
                        f"Unexpected response from OpenAI API: {chat_completion_resp}")
        except asyncio.TimeoutError:
            print(f"OpenAI response timed out, retrying in {wait_time} seconds...")
        except Exception as e:
            print(
                f"Error occurred in OpenAI response: {e}, retrying in {wait_time} seconds...")
            
        await asyncio.sleep(wait_time)
        wait_time *= 2

    print("Maximum retries reached.")
    return None


# def num_tokens_from_string(message, model="gpt-3.5-turbo-16k-0613"):
#     """Return the number of tokens used by a message."""
#     try:
#         encoding = tiktoken.encoding_for_model(model)
#     except KeyError:
#         print("Warning: model not found. Using cl100k_base encoding.")
#         encoding = tiktoken.get_encoding("cl100k_base")

#     if model in {
#         "gpt-3.5-turbo-0613",
#         "gpt-3.5-turbo-16k-0613",
#         "gpt-4-0314",
#         "gpt-4-32k-0314",
#         "gpt-4-0613",
#         "gpt-4-32k-0613",
#     }:
#         tokens_per_message = 3
#     elif model == "gpt-3.5-turbo-0301":
#         # every message follows {role/name}\n{content}\n
#         tokens_per_message = 4
#     elif "gpt-3.5-turbo" in model:
#         print("Warning: gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0613.")
#         return num_tokens_from_string(message, model="gpt-3.5-turbo-0613")
#     elif "gpt-4" in model:
#         print(
#             "Warning: gpt-4 may update over time. Returning num tokens assuming gpt-4-0613.")
#         return num_tokens_from_string(message, model="gpt-4-0613")
#     else:
#         raise NotImplementedError(
#             f"""num_tokens_from_string() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens."""
#         )

#     num_tokens = tokens_per_message
#     num_tokens += len(encoding.encode(message))
#     num_tokens += 3  # every reply is primed with assistant

#     return num_tokens
