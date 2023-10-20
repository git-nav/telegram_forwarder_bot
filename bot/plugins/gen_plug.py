from pyrogram import Client, filters
from bot import app, db, cursor, sudo_users
from psycopg2.errors import InFailedSqlTransaction
from bot.utils.util import delete
from sys import exit

@Client.on_message(filters.command("exe") & filters.user(sudo_users))
def execute(client, message):
    message.delete()
    query = message.text[5:]
    try:
        cursor.execute(f"{query}")
        db.commit()
        text = "Returned data\n\n"
        for each in cursor.fetchall():
            text += str(each) + "\n"
        service_msg = app.send_message(message.chat.id, text)
        delete(service_msg, 15)

    except InFailedSqlTransaction as e:
        db.rollback()    
        

@Client.on_message(filters.command("stop") & filters.user(sudo_users))
def stop(client, message):
    message.delete()
    exit(0)
