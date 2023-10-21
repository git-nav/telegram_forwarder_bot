import os 
import logging
import psycopg2
from os import getenv
from sys import exit
from dotenv import load_dotenv
from datetime import datetime
from time import time
from pytz import timezone
from pyrogram import Client

start_time = time()

# Setting timezone
def timetz(*args):
    return datetime.now(tz).timetuple()

tz = timezone(getenv("TIMEZONE", 'Asia/Kolkata'))

logging.Formatter.converter = timetz

# Setting logger...
logging.basicConfig(format=("[%(asctime)s - %(name)s - %(levelname)s] %(message)s"),datefmt='%Y-%m-%d %I:%M:%S %p',
                    handlers=[logging.FileHandler("log.txt"), logging.StreamHandler()], level=logging.INFO)

log = logging.getLogger(__name__)

# Getting environmental variables...
if os.path.exists("config.env"):
    load_dotenv("config.env")

token = getenv("BOT_TOKEN", None)
string = getenv("SESSION_STRING", None)
database_url = getenv("DATABASE_URL", None)
remove_string = list(x for x in getenv("REMOVE_STRING", "").split(";"))
sudo_users = ["me"]
temp_sudo = getenv("SUDO_USERS", None)
tg_log = getenv("LOG_CHANNEL", "me")
log.info(token)
log.info(string)
if temp_sudo is not None:
    sudo_users.extend(temp_sudo.split(","))

if (token is None and string is None) or database_url is None:
    log.info("one or more variables is missing...")
    exit(1)

# Initializing database...
try:
    db = psycopg2.connect(database_url)
    cursor = db.cursor()
    cursor.execute("create table if not exists copy(id serial primary key, mode varchar, from_chat bigint, to_chat bigint, start int, current int, stop int)")
    cursor.execute("create table if not exists sync(id serial primary key, from_chat bigint, from_chat_name varchar, to_chat bigint, to_chat_name varchar)")
    db.commit()

except Exception as e:
    log.error(e)
    exit(1)


log.info("Welcome to telegram message forwarder bot...")

class Bot(Client):

    def __init__(self):
        super().__init__(
            name="nav",
            session_string=string,
            bot_token=token,
            in_memory=True,
            plugins=dict(root="bot.plugins")
        )

    async def start(self):
        await super().start()
        cursor.execute("select * from copy")
        res = cursor.fetchall()
        await self.send_message(tg_log, "Bot started..." if len(res)==0 else "Bot started...\nSend <code>/resume</code> to restart the pending tasks...")
            
        
    async def stop(self, *args):
        await super().stop()      
        await self.send_message(tg_log, "Bot Stopped........")        

from flask import Flask
from threading import Thread

web_server = Flask(__name__) 

@web_server.route("/")
def fun():
    return "<h1>Hello World</h1>"

def web():
    web_server.run(host="0.0.0.0", port=5000)

t = Thread(target=web)
t.run()

bot = Bot()
bot.run()
