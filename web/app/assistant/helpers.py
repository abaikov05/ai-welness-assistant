import asyncio, base64
from io import BytesIO
from openai import AsyncOpenAI
from PIL import Image

from dotenv import load_dotenv
load_dotenv()

client = AsyncOpenAI()



def encode_image(image: BytesIO, max_image=512):
    """
    Scales down images and encodes them to send in OpenAI request.
    """
    with Image.open(image) as img:
        width, height = img.size
        max_dim = max(width, height)
        if max_dim > max_image:
            scale_factor = max_image / max_dim
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            img = img.resize((new_width, new_height))
        
        buffered = BytesIO()
        img.save(buffered, format=image.name.split('.')[-1].upper())
        
        encoded_image = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return encoded_image
    

async def openai_chat_request(prompt=None, messages=None, system="You are a helpful assistant.", model="gpt-4o-mini", max_retries=5, temperature=1, max_tokens=1000, timeout=10, image: BytesIO = None):
    """
    This function makes a chat request to OpenAI and returns the response and information about used tokens.
    In case of an error, or if the request takes longer than 'timeout' seconds, it retries up to 'max_retries' times with exponential backoff.
    """
    if not messages and not image:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ]
    wait_time = 0.1
    
    if image:
        image_type = image.name.split('.')[-1].upper()
        encoded_image = encode_image(image)
        messages = [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/{image_type};base64,{encoded_image}"},
                    },
                ],
            }
        ]
        # print(messages)
    
    for _ in range(max_retries):
        try:
            chat_completion_resp = await asyncio.wait_for(client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            ), timeout=timeout)

            response = chat_completion_resp.choices[0].message.content
            usage = chat_completion_resp.usage.model_dump()
            
            return response, usage
        except asyncio.TimeoutError:
            print(f"OpenAI response timed out, retrying in {wait_time} seconds...")
        except Exception as e:
            print(f"Error occurred in OpenAI response: {e}, retrying in {wait_time} seconds...")
            
        await asyncio.sleep(wait_time)
        wait_time *= 2

    print("Maximum retries reached.")
    return None, None

async def openai_audio_transcription(audio_file, model='whisper-1', max_retries=3, timeout=5):
    wait_time = 0.1
    for _ in range(max_retries):
        try:
            transcription = await asyncio.wait_for(client.audio.transcriptions.create(
                file=audio_file,
                model=model,
                language='en',
                response_format='verbose_json'
            ),timeout=timeout)
            
            text = transcription.text
            duration = transcription.duration
            return text, duration
        
        except asyncio.TimeoutError:
            print(f"OpenAI audio transcription response timed out, retrying in {wait_time} seconds...")
        except Exception as e:
                print(f"Error occurred in OpenAI audio transcription response: {e}, retrying in {wait_time} seconds...")
            
        await asyncio.sleep(wait_time)
        wait_time *= 2

    print("Maximum retries reached.")
    return None, None

