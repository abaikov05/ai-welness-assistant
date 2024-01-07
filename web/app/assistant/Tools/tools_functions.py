from ..helpers import openai_chat_request
import asyncio

# For weather tool
import pyowm
from textwrap import dedent

# For news tool
from newsapi import NewsApiClient

def tools_info() -> str:

    with open('web/app/assistant/Tools/tools_list.txt', 'r', encoding="utf-8") as file:
        tools_list = eval(file.read())

    message = "Here is tools list:\n"
    for tool in tools_list:
        message += f"Name: {tool['name']}; Description: {tool['description']}; Inputs: {tool['inputs']}\n"

    return message

def weather(location):
    if location and location.strip() != '':
        try:
            # Here is my free Open Weather Map API key :)
            owm = pyowm.OWM('7e874d5e11f3c77a5b3bcd4df098e895')
            weather_mgr = owm.weather_manager()
            observation = weather_mgr.weather_at_place(location)

            temperature = observation.weather.temperature("celsius")["temp"]
            humidity = observation.weather.humidity
            wind = observation.weather.wind()
            status = observation.weather.detailed_status
            message = dedent(f"""\
            Weather in: {location}
            Status: {status}
            Temperature: {temperature}°C
            Humidity: {humidity}%
            Wind Speed: {wind["speed"]} m/s""")

            return message
        except Exception as e:
            print(f"Error in weather tool: {e}")

    else:
        raise Exception('No location passed')

def news(key_words, category = None):

    available_categories = ['business', 'entertainment', 'general', 'health', 'science', 'sports', 'technology']

    if category:
        category = str(category).lower()

        if category not in available_categories:
            category = None
            print('Category is not available!')

    try:
        newsapi = NewsApiClient(api_key='6100e0625e454dcdb14f6df98460f28e')
        top_headlines = newsapi.get_top_headlines(
            q = str(key_words),
            category = category,
            language = 'en')
        # For GPT
        result = "Tell user about these found articles. Mention source and link to an article." + str(top_headlines['articles'])
        return result
    except Exception as e:
        print(f"Something went wrong while searching news: {e}")
        return None

def calculator(expression):
    try:
        result = eval(expression)
        return f"Solution for {expression} is {result}."
    
    except (SyntaxError, TypeError, NameError) as e:
        # Handle exceptions based on your needs
        print(f"Error evaluating expression: {e}")
        return None