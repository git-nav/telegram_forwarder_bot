import math
from time import time, sleep

def size_formatter(byte):
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB"]
    for unit in units:
        if byte < 1024:
            return f"{round(byte, 2)} {unit}"
        byte /= 1024
    return f"{byte} >PB"

def time_formatter(seconds): 
    minutes, seconds = divmod(round(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)

    time_str = ((str(days) + "d, ") if days else "") + \
            ((str(hours) + "h, ") if hours else "") + \
            ((str(minutes) + "m, ") if minutes else "") + \
            ((str(seconds) + "s, ") if seconds else "")
        
    return time_str[:-2]

def progress_message(current, total, msg, start_time):
    PROGRESS_BAR = "\n\n{a} ➤ {b}\n🚀 : {c}%\n⏱️ : {d}\n<a href='/cancel {e}'>/cancel_{e}</a>"
    now = time()
    diff = now - start_time
    percentage = current / total * 100 
    speed = current / diff
    estimated_seconds = round((total-current)/speed)
    progress = "\n{0}{1}".format(
        "".join(["⬢" for i in range(math.floor(percentage/5))]),
        "".join(["⬡" for i in range(20 - math.floor(percentage/5))])
    )
    return "Current / Total : {}/{}".format(current, total) + progress + PROGRESS_BAR.format(
        a=msg["from"],
        b=msg["to"],
        c=round(percentage),
        d=time_formatter(estimated_seconds),
        e=msg["id"]        
    )

def static_vars(**kwargs):
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate

def delete(message, sleep_time=10):
    sleep(sleep_time)
    message.delete()
