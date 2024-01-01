from pyrogram.errors import FloodWait
from bot import db, log, app
from time import time
from bot.utils.util import progress_message
import asyncio

OBJ_LIST = []

class Copy:

    def __init__(self, db_id):
        self.db_id = db_id
        self.run = True
        self.cursor = db.cursor()
        self.c_time = time()
        self.obj_id = hex(self.__hash__())
        self.mode, self.from_chat, self.from_chat_name, self.to_chat, self.to_chat_name, self.start, self.current, self.stop = self.get_data(db_id)
        
    def get_data(self, db_id):
        self.cursor.execute(f"select * from copy where id = {db_id}")
        data = self.cursor.fetchone()
        return data[1:]
        
    async def start_copy(self):
        global OBJ_LIST
        while self.run and self.current <= self.stop:
            try:
                if self.mode == "all":
                    while True:
                        try:
                            await app.copy_message(self.to_chat, self.from_chat, self.current)
                            await asyncio.sleep(1.5)

                        except FloodWait as wait:
                            await asyncio.sleep(wait.value + 5)

                        except Exception as error:
                            log.error(error)
                            break

                        else:
                            break

                elif self.mode == "file":
                    while True:
                        try:
                            msg = await app.get_messages(self.from_chat, self.current)
                            if msg.video is not None or msg.document is not None or msg.photo is not None:
                                await app.copy_message(self.to_chat, self.from_chat, self.current)
                                await asyncio.sleep(1.5)

                        except FloodWait as wait:
                            await asyncio.sleep(wait.value + 5)
                            

                        except Exception as error:
                            log.error(error) 
                            break

                        else:
                            break   

                else:
                    log.error("Invalid mode")        


            except Exception as err:
                log.exception(err)              

            finally:
                self.current += 1      
                self.cursor.execute(f"update copy set current={self.current} where id = {self.db_id}")
                db.commit()
        
        if self.current > self.stop:
            await self.cancel()

    def status(self):
        msg = {
            "from": self.from_chat_name,
            "to": self.to_chat_name,
            "id": self.obj_id
        }
        return progress_message((self.current-self.start), (self.stop-self.start), msg, self.c_time)

    async def cancel(self):
        self.run = False
        self.cursor.execute(f"delete from copy where id ={self.db_id}")
        db.commit()
        self.cursor.close()
        OBJ_LIST.remove(self)