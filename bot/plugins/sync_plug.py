from bot import log, db, cursor, sudo_users, start_time, app
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from time import time, sleep
from bot.utils.util import time_formatter, delete

# Loading data
sync_data = {}
from_chats = []

def sync_data_loader():
    global sync_data, from_chats
    cursor.execute("select from_chat, to_chat from sync")
    for each in cursor.fetchall():
        sync_data[int(each[0])] = int(each[1])

    from_chats = list(set(sync_data.keys()))

sync_data_loader()
log.info("Data sync loaded...")

@Client.on_message(filters.chat(from_chats))
def sync(client, message):    
    chat_id = message.chat.id
    cursor.execute(f"select to_chat from sync where from_chat={chat_id}")
    data = cursor.fetchall()
    for each_data in data:
        while True:
            try:
                message.copy(each_data[0])
            except FloodWait as wait:
                sleep(wait.value)
            except Exception as err:
                log.error(err)    
                break
            else:
                break
                


@Client.on_message(filters.command("addsync") & filters.user(sudo_users))
def add_sync(client, message):
    message.delete()
    data = message.command

    try:
        from_chat_id = int(data[1])
        to_chat_id = int(data[2])
        from_chat_name = app.get_chat(from_chat_id).title
        to_chat_name = app.get_chat(to_chat_id).title
        cursor.execute(f"insert into sync(from_chat, from_chat_name, to_chat, to_chat_name) values({from_chat_id},'{from_chat_name}',{to_chat_id},'{to_chat_name}')")
        db.commit()
        service_msg = app.send_message(message.chat.id, f"Sync Added {from_chat_name} -> {to_chat_name}")    
        sync_data_loader()
    except Exception as e:
        log.exception(e)
        service_msg = app.send_message(message.chat.id, e)    
    delete(service_msg, 10)

@Client.on_message(filters.command("showsync") & filters.user(sudo_users))
def show_sync(client, message):
    message.delete()
    status = ""
    count = 1
    cursor.execute("select * from sync")
    for each in cursor.fetchall():
        status += f"{count}. {each[2]} 🔄 {each[4]}\n"
        count += 1
    status += f"Uptime : {time_formatter(time() - start_time)}"    
    service_msg = app.send_message(message.chat.id, status if count > 1 else f"No sync...\n\nUptime : {time_formatter(time()- start_time)}")
    delete(service_msg, 15)

@Client.on_message(filters.command("delsync") & filters.user(sudo_users))
def del_sync(client, message):
    message.delete()
    data = message.command
    cursor.execute(f"select id from sync")
    try:
        del_id = cursor.fetchall()[int(data[1])-1][0]
        cursor.execute(f"delete from sync where id={del_id}")    
        db.commit()
        service_msg = app.send_message(message.chat.id, f"Sync Removed...")
        sync_data_loader()
    except Exception as e:
        log.exception(e)
        service_msg = app.send_message(message.chat.id, e)        
    delete(service_msg, 15)
        