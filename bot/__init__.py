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
try:
    tz = timezone(getenv("TIMEZONE"))
except Exception:
    tz = timezone('Asia/Kolkata')    

logging.Formatter.converter = timetz

# Setting logger...
logging.basicConfig(format=("[%(asctime)s - %(name)s - %(levelname)s] %(message)s"),datefmt='%Y-%m-%d %I:%M:%S %p',
                    handlers=[logging.FileHandler("log.txt"), logging.StreamHandler()], level=logging.INFO)

log = logging.getLogger(__name__)

# Getting environmental variables...
if os.path.exists("config.env"):
    load_dotenv("config.env", override=False)

token = getenv("BOT_TOKEN", None)
string = getenv("SESSION_STRING", None)
database_url = getenv("DATABASE_URL", None)
remove_string = list(x for x in getenv("REMOVE_STRING", "").split(";"))
sudo_users = ["me"]
temp_sudo = getenv("SUDO_USERS", None)
tg_log = getenv("LOG_CHANNEL", "me")
if temp_sudo is not None:
    sudo_users.extend(temp_sudo.split(","))

if ((token is None) ^ (string is None)) and database_url is None:
    log.info("one or more variables is missing...")
    exit(1)

# Initializing database...
try:
    db = psycopg2.connect(database_url)
    cursor = db.cursor()
    cursor.execute("create table if not exists copy(id serial primary key, mode varchar, from_chat bigint, to_chat bigint, start int, current int, stop int)")
    cursor.execute("create table if not exists sync(id serial primary key, from_chat bigint, from_chat_name varchar, to_chat bigint, to_chat_name varchar, last_id int)")
    db.commit()

except Exception as e:
    log.error(e)
    exit(1)

log.info("Welcome to telegram message forwarder bot...")

# Loading data
sync_data = {}
from_chats = []


async def sync_data_loader(app):
    global sync_data, from_chats
    cursor.execute("select from_chat, to_chat, last_id from sync")
    try:
        for each in cursor.fetchall():
            from_chat, to_chat, start_id = each
            stop_id = None
            async for msg in app.get_chat_history(from_chat, 1):
                stop_id = msg.id
            try:
                sync_data[from_chat].append([to_chat, start_id, stop_id])
            except KeyError:
                sync_data[from_chat] = [[to_chat, start_id, stop_id]]

        from_chats = list(set(sync_data.keys()))
    except Exception as err:
        log.exception(err)
        pass    
    print(sync_data)
    print(from_chats)

log.info("Sync data loaded...")



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
        await self.send_message(tg_log, "Starting bot..." if len(res)==0 else "Bot started...\nSend <a href='/resume'>/resume</a> to restart the pending tasks...")
        await sync_data_loader(self)
            
        
    async def stop(self, *args):
        await self.send_message(tg_log, "Stopping bot...")
        await super().stop()      
                

app = Bot()
