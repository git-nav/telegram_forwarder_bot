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
    cursor.execute("create table if not exists copy(id serial primary key, mode varchar(10), from_chat bigint, from_chat_name varchar(30), to_chat bigint,to_chat_name varchar(30), start int, current int, stop int)")
    cursor.execute("create table if not exists sync(id serial primary key, from_chat bigint, from_chat_name varchar(10), to_chat bigint, to_chat_name varchar(10), last_id int)")
    db.commit()

except Exception as e:
    log.error(e)
    exit(1)


# Loading sync data
sync_data = {}
cursor.execute(f"select from_chat, to_chat from sync")
data_values = cursor.fetchall()
for each in data_values:
    try:
        sync_data[each[0]].append(each[1])
    except KeyError:
        sync_data[each[0]] = [each[1]]
from_chats = list(sync_data.keys())


#loading missing sync
async def missing_sync_data_loader(app):
    missing_sync = {}
    cursor.execute("select from_chat, from_chat_name, to_chat, to_chat_name, last_id from sync")
    try:
        for sync_data in cursor.fetchall():
            from_chat, from_chat_name, to_chat, to_chat_name, stopped_id = sync_data
            last_id = None
            async for msg in app.get_chat_history(from_chat, 1):
                last_id = msg.id
            if stopped_id < last_id:    
                try:
                    missing_sync[from_chat].append([from_chat_name, to_chat, to_chat_name, stopped_id, last_id])
                except KeyError:
                    missing_sync[from_chat] = [[from_chat_name, to_chat, to_chat_name, stopped_id, last_id]]

        if len(missing_sync) > 0:
            for from_chat in missing_sync.keys():
                for sync_data in missing_sync[from_chat]:
                    from_chat_name, to_chat, to_chat_name, start_id, stop_id = sync_data
                    cursor.execute(f"insert into copy(mode, from_chat, from_chat_name, to_chat, to_chat_name, start, current, stop) values('all', {from_chat}, '{from_chat_name}', {to_chat}, '{to_chat_name}', {start_id}, {start_id}, {stop_id})")
                    db.commit()
                    cursor.execute(f"update sync set last_id = {stop_id} where from_chat = {from_chat} and to_chat = {to_chat}")
                    db.commit()
        
    except Exception as err:
        log.exception(err)
        pass    


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
        await missing_sync_data_loader(self)
        cursor.execute("select * from copy")
        res = cursor.fetchall()
        await self.send_message(tg_log, "Starting bot..." if len(res)==0 else "Bot started...\nSend <a href='/resume'>/resume</a> to restart the pending tasks...")
        
            
        
    async def stop(self, *args):
        await self.send_message(tg_log, "Stopping bot...")
        await super().stop()      
                

app = Bot()