from bot import log, db, cursor, sudo_users, start_time, app, from_chats
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from time import time, sleep
from bot.utils.util import time_formatter, delete

sync_data = None

@Client.on_message(filters.chat(from_chats))
def sync(client, message):
    global sync_data
    if sync_data is None:
        from bot import sync_datas
        sync_data = sync_datas
    from_chat = message.chat.id
    message_id = message.id
    data_collection = sync_data[from_chat]
    for data in data_collection:
        to_chat = data[0]
        while True:
            try:
                message.copy(to_chat)
            except FloodWait as wait:
                sleep(wait.value)
            except Exception as err:
                log.exception(err)    
                break
            else:
                break
        
        cursor.execute(f"update sync set last_id={message_id} where from_chat={from_chat} and to_chat={to_chat}")
        db.commit()        
                

@Client.on_message(filters.command("addsync") & filters.user(sudo_users))
def add_sync(client, message):
    message.delete()
    data = message.command

    try:
        from_chat_id = int(data[1])
        to_chat_id = int(data[2])
        from_chat_name = app.get_chat(from_chat_id).title
        to_chat_name = app.get_chat(to_chat_id).title
        last_id = app.get_chat_history(from_chat_id, limit=1).__next__()
        cursor.execute(f"insert into sync(from_chat, from_chat_name, to_chat, to_chat_name, last_id) values({from_chat_id},'{from_chat_name}',{to_chat_id},'{to_chat_name}', {last_id.id})")
        db.commit()
        service_msg = app.send_message(message.chat.id, f"Sync Added {from_chat_name} -> {to_chat_name}\n<a href='/restart'>/restart</a> the bot...")    

    except Exception as e:
        log.exception(e)
        service_msg = app.send_message(message.chat.id, e)    
    delete(service_msg, 10)

@Client.on_message(filters.command("showsync") & filters.user(sudo_users))
def show_sync(client, message):
    message.delete()
    status = ""
    row_number = 1
    cursor.execute("select * from sync")
    for each in cursor.fetchall():
        status += f"{row_number}. {each[2]} 🔄 {each[4]}\n"
        row_number += 1
    status += f"Uptime : {time_formatter(time() - start_time)}"    
    service_msg = app.send_message(message.chat.id, status if row_number > 1 else f"No sync...\n\nUptime : {time_formatter(time()- start_time)}")
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
        service_msg = app.send_message(message.chat.id, f"Sync Removed...\n<a href='/restart'>/restart</a> the bot...")

    except Exception as e:
        log.exception(e)
        service_msg = app.send_message(message.chat.id, e)        
    delete(service_msg, 15)
