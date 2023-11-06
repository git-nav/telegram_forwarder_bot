from pyrogram import Client, filters
from bot import app, db, cursor, sudo_users, log
from psycopg2.errors import InFailedSqlTransaction, ProgrammingError
from bot.utils.util import delete
import sys
import os

@Client.on_message(filters.command("exe") & filters.user(sudo_users))
def execute(client, message):
    message.delete()
    query = message.text[5:]
    text = "Returned data\n\n\n"
    try:
        cursor.execute(f"{query}")
        db.commit()
        for each in cursor.fetchall():
            text += str(each) + "\n"
        
    except InFailedSqlTransaction as e:
        db.rollback()    

    except ProgrammingError:
        text += "Action Performed..."

    except Exception as e:
        log.exception(e)
        text += str(e)

    finally:
        service_msg = app.send_message(message.chat.id, text)
        delete(service_msg, 15)        

@Client.on_message(filters.command("restart") & filters.user(sudo_users))
def restart(client, message):
    message.reply_text("Restarting...")
    app.stop()
    python_path = sys.executable
    os.execl(python_path, "python -m bot")

@Client.on_message(filters.command("help") & filters.user(sudo_users))
def help(client, message):
    message.delete()
    text = """
Sync Commands:    
<a href="/addsync">/addsync</a> "from_chat_id" "to_chat_id": Restart required!!!.
<a href="/showsync">/showsync</a>: Shows the syc data.
<a href="/delsync">/delsync</a> "id": Remove the sync data - Restart required!!!.

Copy Commands:
<a href="/copy">/copy</a> "mode = [all, file]" "from_chat_id" "to_chat_id" "start_message_id" "stop_message_id".
<a href="/status">/status</a>: Show status of all copying process.
<a href="/resume">/resume</a>: Resume stopped copy task after restart.

General Commands:
<a href="/exe">/exe</a> "query": Excute sql query commands.
<a href="/restart">/restart</a>: Restart the bot.
<a href="/help">/help</a>: Show help message.
    """
    service_msg = app.send_message(message.chat.id, text)
    delete(service_msg)