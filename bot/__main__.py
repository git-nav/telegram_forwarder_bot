from bot import app, db, log, cursor
from pyrogram import idle
from .utils.copy import Copy, OBJ_LIST
import asyncio


#loading missing sync
async def missing_sync_loader():
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

async def missing_task():
    await missing_sync_loader()
    cursor.execute("select id from copy")
    copy_list = cursor.fetchall() 

    if len(copy_list) > 0:
        task = []
        for pending_copy in copy_list:
            obj = Copy(pending_copy[0])
            OBJ_LIST.append(obj)
            task.append(obj.start_copy())
        await asyncio.gather(*task)



async def main():
    await app.start()
    await missing_task()
    await idle()

if __name__ == "__main__":
    app.run(main())
