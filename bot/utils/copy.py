from pyrogram.errors import FloodWait
from bot import db, cursor, log, app
from time import time, sleep
from bot.utils.util import progress_message

OBJ_LIST = []

class Copy:

    def __init__(self, db_id):
        self.db_id = db_id
        self.run = True
        self.c_time = time()
        self.obj_id = hex(self.__hash__())
        self.mode, self.from_chat, self.to_chat, self.start, self.current, self.stop = self.get_data(db_id)
        self.from_chat_name, self.to_chat_name = app.get_chat(self.from_chat).title, app.get_chat(self.to_chat).title

    def get_data(self, db_id):
        cursor.execute(f"select * from copy where id = {db_id}")
        data = cursor.fetchone()
        return data[1], data[2], data[3], data[4], data[5], data[6]

    def start_copy(self):
        global OBJ_LIST
        while self.run and self.current <= self.stop:
            try:
                if self.mode == "all":
                    while True:
                        try:
                            app.copy_message(self.to_chat, self.from_chat, self.current)
                            sleep(1)

                        except FloodWait as wait:
                            sleep(wait.value)

                        except Exception as error:
                            log.error(error)
                            break

                        else:
                            break    

                elif self.mode == "file":
                    while True:
                        try:
                            msg = app.get_messages(self.from_chat, self.current)
                            if msg.video is not None or msg.document is not None or msg.photo is not None:
                                app.copy_message(self.to_chat, self.from_chat, self.current)
                                sleep(1)

                        except FloodWait as wait:
                            sleep(wait.value)
                            

                        except Exception as error:
                            log.error(error) 
                            break

                        else:
                            break   

                else:
                    log.error("Invalid mode")        


            except Exception as err:
                log.error(err)              

            finally:
                self.current += 1      
                cursor.execute(f"update copy set current={self.current} where id = {self.db_id}")
                db.commit()
        
        OBJ_LIST.remove(self)
        cursor.execute(f"delete from copy where id ={self.db_id}")
        db.commit()

    def status(self):
        msg = {
            "from": self.from_chat_name,
            "to": self.to_chat_name,
            "id": self.obj_id
        }
        return progress_message((self.current-self.start), (self.stop-self.start), msg, self.c_time)


    def cancel(self):
        self.run = False
        