from pyrogram import Client, filters
from bot import db, log, sudo_users, start_time, app
from psycopg2.errors import ProgrammingError, InFailedSqlTransaction
from time import time
from bot.utils.util import time_formatter, static_vars, delete
from bot.utils.copy import Copy, OBJ_LIST
import asyncio


@Client.on_message(filters.command("copy") & filters.user(sudo_users))
async def copy(client, message):
    msg = message.command
    try:
        mode = msg[1]
        from_chat = int(msg[2])
        to_chat = int(msg[3])
        start = msg[4]
        current = msg[4]
        stop = msg[5]
        from_chat_name = (await app.get_chat(from_chat)).title
        to_chat_name = (await app.get_chat(to_chat)).title
        cursor = db.cursor()
        try:
            cursor.execute(f"delete from copy where from_chat = {from_chat} and to_chat = {to_chat}")
            db.commit()
        except (ProgrammingError, InFailedSqlTransaction):
            db.rollback()    
        except Exception as e:            
            log.exception(e)
        
        cursor.execute(f"insert into copy(mode, from_chat, from_chat_name, to_chat, to_chat_name, start, current, stop) values('{mode}', {from_chat}, '{from_chat_name}', {to_chat}, '{to_chat_name}', {start}, {current}, {stop})")    
        db.commit()

        cursor.execute(f"select id from copy where from_chat = {from_chat} and to_chat = {to_chat}")
        db_id = cursor.fetchone()[0]
        obj = Copy(db_id)
        OBJ_LIST.append(obj)
        log.info(f"Starting copy from {from_chat} -> {to_chat}")
        tasks = [obj.start_copy(), status(client, message)]
        await asyncio.gather(*tasks)

    except Exception as e:
        log.exception(e)
        service_msg = await app.send_message(message.chat.id, e)    
        await delete(service_msg, 15)    
    finally:
        cursor.close()    

    
@Client.on_message(filters.command("status") & filters.user(sudo_users))
@static_vars(counter = 0)
async def status(client, message):
    await message.delete()
    def get_status():
        status = ""
        for each in OBJ_LIST:
            status += each.status() + "\n\n"
        status += f"Uptime : {time_formatter(time()-start_time)}"    
        return status
    
    msg = await app.send_message(message.chat.id, get_status() if len(OBJ_LIST)>0 else f"No process, I'm sleeping...\n\nUptime : {time_formatter(time()-start_time)}")    
    status.counter += 1
    try:
        while True:
            await asyncio.sleep(5)
            if len(OBJ_LIST)>0:
                await msg.edit(get_status())  
            else:
                await delete(msg)
                status.counter -= 1
                break

            if status.counter > 1:
                status.counter -= 1
                break
        await delete(msg, 0)
        
    except:
        status.counter -= 1
        await delete(msg, 0)

        
@Client.on_message(filters.regex("cancel") & filters.user(sudo_users))
async def cancel(client, message):
    msg = message.text.split("_")
    await message.delete()
    for each in OBJ_LIST:
        if msg[1] == each.obj_id:
            await each.cancel()
            await status(client, message)        
            return    
    service_msg = await app.send_message(message.chat.id, "Wrong Hash!")    
    await delete(service_msg)
    