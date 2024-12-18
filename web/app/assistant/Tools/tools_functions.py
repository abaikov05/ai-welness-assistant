from textwrap import dedent

# For weather tool
import pyowm
# For news tool
from newsapi import NewsApiClient
# Calculator
from simpleeval import simple_eval
# Chat summarizer
from ...utils import get_chat_history
from ..helpers import openai_chat_request
from ...models import Chat, Message
# For website scraper.
import requests
import aiohttp
import asyncio
from bs4 import BeautifulSoup

import os
from dotenv import load_dotenv


load_dotenv()
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

def tools_info() -> str:

    with open('web/app/assistant/Tools/tools_list.txt', 'r', encoding="utf-8") as file:
        tools_list = eval(file.read())
        
    message = "Here is tools list:\n"
    for tool in tools_list:
        message += f"Name: {tool['name'].replace('_', ' ')}; Description: {tool['description']}; Inputs: {tool['inputs'].replace('_', ' ')}\n"

    return message

def weather(location) -> str|None:
    if location and location.strip() != '':
        try:
            # Make request to weather API
            owm = pyowm.OWM(WEATHER_API_KEY)
            weather_mgr = owm.weather_manager()
            observation = weather_mgr.weather_at_place(location)
            # Extracte needed info
            temperature = observation.weather.temperature("celsius")["temp"]
            humidity = observation.weather.humidity
            wind = observation.weather.wind()
            status = observation.weather.detailed_status
            # Create message for assistant
            message = dedent(f"""\
            Weather in: {location}
            Status: {status}
            Temperature: {temperature}°C
            Humidity: {humidity}%
            Wind Speed: {wind["speed"]} m/s""")

            return message
        except Exception as e:
            print(f"Error in weather tool: {str(e)}")
            return None

    else:
        raise Exception('No location passed')

def news(key_words, category = None) -> str|None:

    available_categories = ['business', 'entertainment', 'general', 'health', 'science', 'sports', 'technology']

    if category:
        category = str(category).lower()

    if category not in available_categories:
        category = None
        print('Category is not available or empty!')

    try:
        # Get news from news API
        newsapi = NewsApiClient(api_key=NEWS_API_KEY)
        top_headlines = newsapi.get_top_headlines(
            q = str(key_words),
            category = category,
            language = 'en')
        # And create message for assistant with news
        result = "Tell user about these found articles. You MUST mention source and link to the article!" + str(top_headlines['articles'])
        return result
    except Exception as e:
        print(f"Something went wrong while searching news: {e}")
        return None

def calculator(expression) -> str|None:
    try:
        result = simple_eval(expression)
        return f"Solution for {expression} is {result}."
    
    except (SyntaxError, TypeError, NameError) as e:
        # Handle exceptions based on your needs
        print(f"Error evaluating expression: {str(e)}")
        return None

async def chat_summarizer(messages_to_summarize, user) -> tuple[str|None, dict|None]:

    chat = await Chat.objects.aget(user=user)
    messages = await get_chat_history(chat, int(messages_to_summarize))
    
    system = "Summarize this chat"
    prompt = f"Chat history:\n{messages}"
    response, token_usage = await openai_chat_request(prompt=prompt, system=system)
    
    return response, token_usage
   
async def website_checker(website_link: str):
    try:
        response = requests.get(website_link)
        response.raise_for_status()  # Raise an error for failed requests
        
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract relevant info
        title = soup.title.string if soup.title else "No title available"
        paragraphs = [p.get_text(strip=True) for p in soup.find_all('p')]
        content = f"Title: {title}\nContent:\n" +'\n'.join(paragraphs)

        # Create message for assitant.
        message = dedent(f"""\
        User asked to get information about this website.
        You MUST provide this website link to user: {website_link}
        Here is found website:
        """) + content

        return message

    except Exception as e:
        return f"Error fetching or the website: {str(e)}"
def test_tool(exeption = False):
    if exeption:
        raise Exception('Test Exception')
    
    return
