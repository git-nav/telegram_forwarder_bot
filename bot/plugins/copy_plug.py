from pyrogram import Client, filters
from bot import db, cursor, log, sudo_users, start_time, app
from psycopg2.errors import InFailedSqlTransaction
from time import time, sleep
from bot.utils.util import time_formatter, static_vars, delete
from bot.utils.copy import Copy, OBJ_LIST


@Client.on_message(filters.command("copy") & filters.user(sudo_users))
def copy(client, message):
    msg = message.command
    try:
        mode = msg[1]
        from_chat = msg[2]
        to_chat = msg[3]
        start = msg[4]
        current = msg[4]
        stop = msg[5]

        try:
            cursor.execute(f"delete from copy where from_chat = {from_chat} and to_chat = {to_chat}")
            db.commit()
        except InFailedSqlTransaction:
            db.rollback()

    
        cursor.execute(f"insert into copy(mode, from_chat, to_chat, start, current, stop) values('{mode}', {from_chat}, {to_chat}, {start}, {current}, {stop})")    
        db.commit()

        cursor.execute(f"select id from copy where from_chat = {from_chat} and to_chat = {to_chat}")
        db_id = cursor.fetchone()[0]
        obj = Copy(db_id)
        OBJ_LIST.append(obj)
        service_msg = app.send_message(message.chat.id, "Task added...\nCheck <a href='/status'>/status</a> for details...") 
        delete(service_msg, 5)
        log.info(f"Copy started from {from_chat} -> {to_chat}")
        obj.start_copy()

    except Exception as e:
        log.exception(e)
        service_msg = app.send_message(message.chat.id, e)    
    delete(service_msg, 15)    

@Client.on_message(filters.command("status") & filters.user(sudo_users))
@static_vars(counter = 0)
def status(client, message):
    message.delete()
    def get_status():
        status = ""
        for each in OBJ_LIST:
            status += each.status() + "\n\n"
        status += f"Uptime : {time_formatter(time()-start_time)}"    
        return status
    
    msg = app.send_message(message.chat.id, get_status() if len(OBJ_LIST)>0 else f"No process, I'm sleeping...\n\nUptime : {time_formatter(time()-start_time)}")    
    status.counter += 1
    try:
        while True:
            sleep(5)
            if len(OBJ_LIST)>0:
                msg.edit(get_status())  
            else:
                delete(msg)
                status.counter -= 1
                break

            if status.counter > 1:
                status.counter -= 1
                break
        delete(msg)
        
    except:
        status.counter -= 1

        
@Client.on_message(filters.command("cancel") & filters.user(sudo_users))
def cancel(client, message):
    msg = message.command
    message.delete()
    for each in OBJ_LIST:
        if msg[1] == each.obj_id:
            each.cancel()
        else:
            service_msg = app.send_message(message.chat.id, "Wrong Hash!")    
            delete(service_msg)

    sleep(2)
    status(client, message)        

@Client.on_message(filters.command("resume") & filters.user(sudo_users))
def resume(client, message):
    message.delete()
    cursor.execute("select id from copy")
    copy_list = cursor.fetchall()
    for each in copy_list:
        obj = Copy(each[0])
        OBJ_LIST.append(obj)
        obj.start_copy()
    serv_msg = app.send_message(message.chat.id, "Tasks resumed...\nCheck <a href='/status'>/status</a> for details..." if len(copy_list) > 0 else "No task to resume")    
    delete(serv_msg)

