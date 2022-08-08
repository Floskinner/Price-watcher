from itertools import product
from json import load
from urllib.error import HTTPError
import telebot
from dotenv import load_dotenv
import os
import validators
import requests
from server import main
from server import watchlist

# Load environemnt variables from .env

load_dotenv()

# Initalizing bot object with API_KEY

bot = telebot.TeleBot(os.getenv("API_KEY"))

# User agent headers

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.81 Safari/537.36"}


# Handle start command

@bot.message_handler(commands=["start"])
def start(message):
    reply = '''
    Welcome to price watcher. I can watch the price drops for you. Send /help to see how to use me.
    '''
    bot.reply_to(message, reply)


# Handle help command

@bot.message_handler(commands=["help"])
def send_hello(message):
    reply_message = f'''Available commands:
/watch <Amazon url here> - To watch the price of the item
/watchlist - To display the items currently being monitored
/dontwatch <watch id> - To remove the item from watchlist
/help - To display available commands'''
    bot.send_message(message.chat.id, reply_message)


# Handle watch command

@bot.message_handler(commands=["watch"])
def watch(message):
    splitted_message = message.text.partition("/watch")
    link = splitted_message[2].strip()

    # If URL not given
    if len(link) == 0:
        bot.reply_to(message, "Please provide the link")

    # If URL not valid
    elif not validators.url(link):
        bot.reply_to(
            message, "Oops.. That does not seem like a valid link. Try again.")

    # If not amazon URL
    if "amazon" in link:
        try:
            # Check if amazon url is valid
            response = requests.get(link, headers=headers)
            if response.status_code == 200:
                # Scrape the website

                for product in watchlist:
                    if product["url"] == link:
                        bot.reply_to(message, "I'm already watching it.")
                        break
                bot.reply_to(message, "Alright.. I have my eyes on it.")
                res = main(link)

                # If price drops
                if type(res) == dict:
                    product = res
                    alert = f"Pricedrop for {product['title']} available at {product['price']}.\nHere {product['url']}"
                    bot.send_message(message.chat.id, alert)
            else:
                response.raise_for_status()
        except ConnectionError:
            bot.reply_to(
                message, "Something is not working.. Try again later.")

        except TimeoutError:
            bot.reply_to(
                message, "Something is not working.. Try again later.")

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                bot.reply_to(message, "Are you sure that link is correct?")
            else:
                bot.reply_to(message, "Oops.. Something went wrong.")
    else:
        bot.reply_to(
            message, "I only work with amazon links for now.")

# Handle watchlist command


@bot.message_handler(commands=["watchlist"])
def handle_watchlist(message):
    if len(watchlist) == 0:
        bot.reply_to(message, "There is nothing in the watchlist.")
    else:
        reply = ""
        for index, product in enumerate(watchlist):
            reply += str(index + 1) + ". " + product["title"] + "\n"
        bot.reply_to(message, reply)

# Handle dontwatch command


@bot.message_handler(commands=["dontwatch"])
def dontwatch(message):
    splitted_message = message.text.partition("/dontwatch")
    index = splitted_message[2]
    if len(index) == 0:
        bot.reply_to(
            message, "Please provide what product to remove from the watchlist.")
    else:
        try:
            index = int(index)
            bot.reply_to(
                message, f"Not watching {watchlist[index - 1]['title']} anymore")
            watchlist.pop(index - 1)
        except ValueError:
            bot.reply_to(message, "That does not seem like a valid number.")
        except IndexError:
            bot.reply_to(message, "There is no product in that index.")


# Bot is active
print("I'm listening.")
bot.infinity_polling()
