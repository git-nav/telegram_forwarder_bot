from pyrogram import Client, filters
from bot import app, db, cursor, sudo_users, log
from psycopg2.errors import InFailedSqlTransaction, ProgrammingError
from bot.utils.util import delete
import sys
import os

@Client.on_message(filters.command("exe") & filters.user(sudo_users))
async def execute(client, message):
    await message.delete()
    query = message.text[5:]
    text = "Returned data\n\n"
    try:
        cursor.execute(f"{query}")
        for each in cursor.fetchall():
            text += str(each) + "\n"
        db.commit()
        
    except InFailedSqlTransaction as e:
        db.rollback()    

    except ProgrammingError:
        text += "Query Executed..."

    except Exception as e:
        log.exception(e)
        text += str(e)

    finally:
        service_msg = await app.send_message(message.chat.id, text)
        await delete(service_msg, 15)        

@Client.on_message(filters.command("restart") & filters.user(sudo_users))
async def restart(client, message):
    await message.reply_text("Restarting...")
    await app.stop()
    python_path = sys.executable
    os.execl(python_path, "python -m bot")

@Client.on_message(filters.command("help") & filters.user(sudo_users))
async def help(client, message):
    await message.delete()
    text = """
Sync Commands:    
<a href="/addsync">/addsync</a> "from_chat_id" "to_chat_id": Restart required!!!.
<a href="/showsync">/showsync</a>: Shows the syc data.
<a href="/delsync">/delsync</a> "id": Remove the sync data - Restart required!!!.

Copy Commands:
<a href="/copy">/copy</a> "mode = [all, file]" "from_chat_id" "to_chat_id" "start_message_id" "stop_message_id".
<a href="/status">/status</a>: Show status of all copying process.

General Commands:
<a href="/resume">/resume</a>: Resume pending copy and sync task.
<a href="/exe">/exe</a> "query": Excute sql query commands.
<a href="/restart">/restart</a>: Restart the bot.
<a href="/help">/help</a>: Show help message.
    """
    service_msg = await app.send_message(message.chat.id, text)
    await delete(service_msg, 15)
    