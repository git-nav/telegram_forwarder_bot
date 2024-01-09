from pyrogram import Client, filters
from bot import app, db, sudo_users, log, owner_id, cursor
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

@Client.on_message(filters.command("addsudo") & filters.user(owner_id))
async def add_sudo(client, message):
    await message.delete()
    try:
        user = message.command[1]     
        if user not in sudo_users:
            with open("config.env", "r+") as f:
                config = ""
                for line in f:
                    if "SUDO_USERS" in line:
                        line = line.replace("\n", "").strip()
                        last_char = line[-1]
                        updated = ""
                        if last_char.isnumeric():
                            updated = line + f",{user}\n"
                        else:
                            updated = line + f"{user}\n"   
                        config += updated
                    else:
                        config += line

                f.seek(0)
                f.write(config)

            await delete(await app.send_message(message.chat.id, f"{user} added as sudo user\n<a href='/restart'>/Restart</a> now"), 5)

        else:
            await delete(await app.send_message(message.chat.id, f"{user} already sudo user"), 5)

    except Exception as e:
        await app.send_message(message.chat.id, str(e))


@Client.on_message(filters.command("showsudo") & filters.user(owner_id))
async def show_sudo(client, message):
    await message.delete()
    try:
        msg = "Sudo Users:\n\n"
        for each in sudo_users:
            msg += f"<code>{each}</code>\n"
        await app.send_message(message.chat.id, msg)    

    except Exception as e:
        await app.send_message(message.chat.id, str(e))


@Client.on_message(filters.command("delsudo") & filters.user(owner_id))
async def del_sudo(client, message):
    await message.delete()
    try:
        user = message.command[1]     
        if user in sudo_users:
            with open("config.env", "r+") as f:
                config = ""
                for line in f:
                    if "SUDO_USERS" in line:
                        updated = line.replace(f"{user},", "")
                        if user in updated:
                            updated = line.replace(user, "")
                        config += updated
                    else:
                        config += line

                f.seek(0)
                f.write(config)

            delete(await app.send_message(message.chat.id, f"{user} removed from sudo user\n<a href='/restart'>/Restart</a> now"), 5)
    
    except Exception as e:
        await app.send_message(message.chat.id, str(e))



@Client.on_message(filters.command("help") & filters.user(sudo_users or owner_id))
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
    
@Client.on_message(filters.command("restart") & filters.user(sudo_users))
async def restart(client, message):
    await delete(await message.reply_text("Restarting..."), 5)
    await app.stop()
    python_path = sys.executable
    os.execl(python_path, "python -m bot")
