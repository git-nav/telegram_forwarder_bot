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
if os.path.exists("log.txt"):
    with open("log.txt", "w") as log:
        log.truncate(0)
        
logging.basicConfig(format=("[%(asctime)s - %(name)s - %(levelname)s] %(message)s"),datefmt='%Y-%m-%d %I:%M:%S %p',
                    handlers=[logging.FileHandler("log.txt"), logging.StreamHandler()], level=logging.INFO)

log = logging.getLogger(__name__)


# Getting environmental variables...
if os.path.exists("config.env"):
    load_dotenv("config.env", override=False)

token = getenv("BOT_TOKEN", None)
session_string = getenv("SESSION_STRING", None)
database_url = getenv("DATABASE_URL", None)
api_id = getenv("API_ID", None)
api_hash = getenv("API_HASH", None)
owner_id = int(getenv("OWNER_ID", 739663149))
# remove_string = list(x for x in getenv("REMOVE_STRING", "").split(";"))
sudo_users = [owner_id]
temp_sudo = getenv("SUDO_USERS", None)
# tg_log = getenv("LOG_CHANNEL", None)
if temp_sudo is not None and len(temp_sudo) > 0:
    for each in temp_sudo.split(","):
        sudo_users.append(int(each))

if ((token is None) ^ (session_string is None)) and database_url is None and api_id is None and api_hash is None and owner_id is None:
    log.info("one or more variables is missing...")
    exit(1)

# Initializing database...
try:
    db = psycopg2.connect(database_url)
    cursor = db.cursor()
    cursor.execute("create table if not exists copy(id serial primary key, mode varchar(10), from_chat bigint, from_chat_name varchar(255), to_chat bigint,to_chat_name varchar(255), start int, current int, stop int)")
    cursor.execute("create table if not exists sync(id serial primary key, from_chat bigint, from_chat_name varchar(255), to_chat bigint, to_chat_name varchar(255), last_id int)")
    db.commit()

except Exception as e:
    log.error(e)
    exit(1)


# Loading sync data
sync_data = {}
cursor.execute(f"select from_chat, to_chat from sync")
data_values = cursor.fetchall()
cursor.close()
for each in data_values:
    try:
        sync_data[each[0]].append(each[1])
    except KeyError:
        sync_data[each[0]] = [each[1]]
from_chats = list(sync_data.keys())


class Bot(Client):

    def __init__(self, app_id = None, app_hash = None, string = None, token = None):
        super().__init__(
            name="nav",
            api_id=app_id,
            api_hash=app_hash,
            session_string = string,
            bot_token = token,
            in_memory = True,
            plugins = dict(root="bot.plugins")
        )
    
    async def stop(self, *args):
        super().stop()

app = Bot(string=session_string, token=token, app_id=api_id, app_hash=api_hash)
