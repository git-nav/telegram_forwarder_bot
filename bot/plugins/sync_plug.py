from bot import log, db, cursor, sudo_users, start_time, app, from_chats, sync_data
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from time import time
from bot.utils.util import time_formatter, delete
import asyncio


@Client.on_message(filters.chat(from_chats))
async def sync(client, message):    
    from_chat = message.chat.id
    message_id = message.id
    data_collection = sync_data[from_chat]
    for to_chat in data_collection:
        while True:
            try:
                await message.copy(to_chat)
            except FloodWait as wait:
                asyncio.sleep(wait.value)
            except Exception as err:
                log.exception(err)    
                break
            else:
                break
        
        cursor.execute(f"update sync set last_id={message_id} where from_chat={from_chat} and to_chat={to_chat}")
        db.commit()        
                

@Client.on_message(filters.command("addsync") & filters.user(sudo_users))
async def add_sync(client, message):
    await message.delete()
    data = message.command

    try:
        from_chat_id = int(data[1])
        to_chat_id = int(data[2])
        from_chat_name = (await app.get_chat(from_chat_id)).title
        to_chat_name = (await app.get_chat(to_chat_id)).title
        async for msg in app.get_chat_history(from_chat_id, limit=1):
            last_id = msg.id 
        cursor.execute(f"insert into sync(from_chat, from_chat_name, to_chat, to_chat_name, last_id) values({from_chat_id},'{from_chat_name}',{to_chat_id},'{to_chat_name}', {last_id})")
        db.commit()
        service_msg = await app.send_message(message.chat.id, f"Sync Added {from_chat_name} -> {to_chat_name}\n<a href='/restart'>/restart</a> the bot...")    

    except Exception as e:
        log.exception(e)
        service_msg = await app.send_message(message.chat.id, e)    
    await delete(service_msg, 10)

@Client.on_message(filters.command("showsync") & filters.user(sudo_users))
async def show_sync(client, message):
    await message.delete()
    status = ""
    row_number = 1
    cursor.execute("select * from sync")
    for each in cursor.fetchall():
        status += f"{row_number}. {each[2]} 🔄 {each[4]}\n"
        row_number += 1
    status += f"Uptime : {time_formatter(time() - start_time)}"    
    service_msg = await app.send_message(message.chat.id, status if row_number > 1 else f"No sync...\n\nUptime : {time_formatter(time()- start_time)}")
    await delete(service_msg, 15)

@Client.on_message(filters.command("delsync") & filters.user(sudo_users))
async def del_sync(client, message):
    await message.delete()
    data = message.command
    cursor.execute(f"select id from sync")
    try:
        del_id = cursor.fetchall()[int(data[1])-1][0]
        cursor.execute(f"delete from sync where id={del_id}")    
        db.commit()
        service_msg = await app.send_message(message.chat.id, f"Sync Removed...\n<a href='/restart'>/restart</a> the bot...")

    except Exception as e:
        log.exception(e)
        service_msg = await app.send_message(message.chat.id, e)        
    await delete(service_msg, 15)