import inspect
import os
from datetime import datetime,timedelta
from threading import Thread, Lock

from config.ConfigData import apiConfig
from common.Context import context

class Tools:
    def __init__(self):pass
    def getLine(self,frame):
        projectFilePath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        caller_frame = frame.f_back
        filename = caller_frame.f_code.co_filename.split(projectFilePath)[-1].split('.')[0]
        line_number = caller_frame.f_lineno
        return {'filename': filename, 'line': str(line_number)}
class LoggerConfig(object):
    def __init__(self):
        self.lock = Lock()
    def save(self,filepath,message):
        self.lock.acquire()
        try:
            open(filepath, 'a', encoding='utf-8').write(message + '\n')
        except:pass
        finally:
            self.lock.release()
    def delBackDayFile(self):
        now = (datetime.now()-timedelta(days=apiConfig['logger']['backDays'])).replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        for filedir in os.listdir(apiConfig['logger']['log_dir']):
            fileBig = os.path.join(apiConfig['logger']['log_dir'], filedir)
            for file in os.listdir(fileBig):
                filepath = os.path.join(fileBig, file)
                ctime = os.path.getctime(filepath)
                if now > ctime:
                    try:
                        os.remove(filepath)
                    except:pass
    def log(self,message,level="INFO",func=None):
        if func is None:
            func = tools.getLine(inspect.currentframe())

        fileLevel = 'success'
        if level == 'ERROR':
            fileLevel = 'error'
        log_dir = apiConfig['logger']['log_dir']+'/'+fileLevel
        try:
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
        except:pass

        filename = fileLevel+'.'+datetime.strftime(datetime.now(), '%Y-%m-%d')+'.log'
        filepath = os.path.join(log_dir, filename)

        MessageArr = [
            datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'),
            level.upper().center(6),
            context.get('request_id'),
            context.get('request_method'),
            (func['filename']+':'+func['line']).center(24),
            context.get('request_ip').center(16),
            context.get('request_url'),
            message.strip()
        ]

        message = ' | '.join(MessageArr)
        Thread(target=self.save,args=(filepath,message,)).start()

        if apiConfig['logger']['isBackDay']:
            Thread(target=self.delBackDayFile).start()

        print(message)


    def info(self,message):
        func = tools.getLine(inspect.currentframe())
        self.log(message,"INFO",func)

    def error(self,message):
        func = tools.getLine(inspect.currentframe())
        self.log(message,"ERROR",func)

tools = Tools()
logger = LoggerConfig()