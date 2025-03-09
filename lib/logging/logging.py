from micropython import const
import os
import io
import sys
import _thread
import machine
import gc
from fc.modload import loader
from fc import datetime
import time

# secondary threads seem to have a small stack and can't do formats that require deep calls
_primary_thread = _thread.get_ident()

ALWAYS = const(100)
CRITICAL = const(50)
ERROR = const(40)
WARNING = const(30)
INFO = const(20)
DEBUG = const(10)
NOTSET = const(0)
NEVER = const(-1)

_DEFAULT_LEVEL = WARNING

_level_dict = {
    ALWAYS:"ALWAYS",
    CRITICAL: "CRITICAL",
    ERROR: "ERROR",
    WARNING: "WARNING",
    INFO: "INFO",
    DEBUG: "DEBUG",
    NOTSET: "NOTSET",
    NEVER:"NEVER"
}

ld = _level_dict

_logger_level_dict = {
    #'module_name': INFO
}

def getLoggerLevelDict():
    return _logger_level_dict
def getDefaultLevel():
    return _DEFAULT_LEVEL


_loggers = {}
_stream = sys.stderr
#_default_fmt = "%(asctime)s:%(levelname)s:%(name)s:%(message)s"
#_default_fmt = "{secs:8.3f}:{levelname:7}:{name:20}: {message}"
#_default_fmt = "{asctime:18}:{thread}:{levelname:7}:{name:20}: {message}"
#_default_fmt = "{asctime:8}:{levelname:7}:{name:20}: {message}"
_default_fmt = "{asctime:8}:{levelname:7}:{mem:6}:{name:20}: {message}"
#_default_datefmt = "%Y-%m-%d %H:%M:%S"
_default_datefmt = "%H:%M:%S"

    
def getLevelNumber(name):
    if type(name) == int:
        return name
    elif type(name) == str:
        name = name.upper()
        for level,n in _level_dict.items():
            if n.upper() == name:
                return level
    return _DEFAULT_LEVEL

def getLoggerLevel(logger_name):
    if type(logger_name) == int:
        return logger_name
    elif type(logger_name) == str:
        levelno = _DEFAULT_LEVEL
        loggerName = ''
        findName = logger_name.upper()
        for dname,num in _logger_level_dict.items():
            name = dname.upper()
            if name == findName:
                return getLevelNumber(num)
            elif findName.startswith(name) and len(loggerName) < len(findName):
                levelno = num
                loggerName = name
        return getLevelNumber(levelno)
    else:
        return _DEFAULT_LEVEL

class LogRecord:
    def set(self, name, level, message):
        self.name = name
        self.levelno = level
        self.levelname = _level_dict[level]
        self.message = message
        self.ct = time.time()
        self.msecs = time.ticks_ms()  # int((self.ct - int(self.ct)) * 1000)
        self.asctime = None


class Handler:
    def __init__(self, level=NOTSET):
        self.level = level
        self.formatter = None

    def close(self):
        pass

    def setLevel(self, level):
        self.level = level

    def setFormatter(self, formatter):
        self.formatter = formatter

    def format(self, record):
        return self.formatter.format(record)


class StreamHandler(Handler):
    def __init__(self, stream=None):
        super().__init__()
        self.stream = _stream if stream is None else stream
        self.terminator = "\n"

    def close(self):
        if hasattr(self.stream, "flush"):
            self.stream.flush()

    def emit(self, record):
        if record.levelno >= self.level:
            self.stream.write(self.format(record) + self.terminator)


class FileHandler(StreamHandler):
    def __init__(self, filename, mode="a", encoding="UTF-8"):
        super().__init__(stream=open(filename, mode=mode, encoding=encoding))

    def close(self):
        super().close()
        self.stream.close()


class Formatter:
    def __init__(self, fmt=None, datefmt=None):
        self.fmt = _default_fmt if fmt is None else fmt
        self.datefmt = _default_datefmt if datefmt is None else datefmt

    def usesTime(self):
        return "asctime" in self.fmt

    def formatTime(self, datefmt, record):
        # secondary threads run out of stack formating a datetime so use RTC for them
        if _primary_thread == _thread.get_ident():
            now = datetime.now()
            return datetime.format(now,_default_datefmt)
        else:
            rtc = machine.RTC()
            dt = rtc.datetime()
            return f"{dt[4]}:{dt[5]}:{dt[6]}GMT"

    def format(self, record):
        if self.usesTime():
            record.asctime = self.formatTime(self.datefmt, record)
        gc.collect()
        return self.fmt.format(**{
            "name": record.name,
            "message": record.message,
            "secs": record.msecs/1000.0,
            "asctime": record.asctime,
            "levelname": record.levelname,
            "thread": _thread.get_ident(),
            "mem":gc.mem_free()
        })


class Logger:
    def __init__(self, name, level=NOTSET):
        self.name = name
        self.level = level
        self.handlers = []
        self.record = LogRecord()
        if level == NOTSET:
            self.level = getLoggerLevel(name)

    def setLevel(self, level):
        self.level = level

    def isEnabledFor(self, level):
        #print(f"isEnabledFor {level}>={self.getEffectiveLevel()}")
        return level >= self.getEffectiveLevel()

    def getEffectiveLevel(self):
        return self.level or getLogger().level or _DEFAULT_LEVEL

    def log(self, level, msg, *args):
        if self.isEnabledFor(level):
            if args:
                if isinstance(args[0], dict):
                    args = args[0]
                msg = msg % args
            self.record.set(self.name, level, msg)
            handlers = self.handlers
            if not handlers:
                handlers = getLogger().handlers
            for h in handlers:
                #print(f"emit {level}")
                h.emit(self.record)

    def always(self, msg, *args):
        self.log(ALWAYS, msg, *args)
        
    def never(self, msg, *args):
        pass
        
    def debug(self, msg, *args):
        self.log(DEBUG, msg, *args)

    def info(self, msg, *args):
        self.log(INFO, msg, *args)

    def warning(self, msg, *args):
        self.log(WARNING, msg, *args)

    def error(self, msg, *args):
        self.log(ERROR, msg, *args)

    def critical(self, msg, *args):
        self.log(CRITICAL, msg, *args)

    def exception(self, msg, *args, exc_info=True):
        self.log(ERROR, msg, *args)
        tb = None
        if isinstance(exc_info, BaseException):
            tb = exc_info
        elif hasattr(sys, "exc_info"):
            tb = sys.exc_info()[1]
        if tb:
            buf = io.StringIO()
            sys.print_exception(tb, buf)
            self.log(ERROR, buf.getvalue())

    def addHandler(self, handler):
        self.handlers.append(handler)

    def hasHandlers(self):
        return len(self.handlers) > 0


def getLogger(name=None):
    if name is None:
        name = "root"
    if name not in _loggers:
        _loggers[name] = Logger(name)
        if name == "root":
            basicConfig()
    return _loggers[name]


def log(level, msg, *args):
    getLogger().log(level, msg, *args)


def debug(msg, *args):
    getLogger().debug(msg, *args)


def info(msg, *args):
    getLogger().info(msg, *args)


def warning(msg, *args):
    getLogger().warning(msg, *args)


def error(msg, *args):
    getLogger().error(msg, *args)


def critical(msg, *args):
    getLogger().critical(msg, *args)


def exception(msg, *args):
    getLogger().exception(msg, *args)


def shutdown():
    for k, logger in _loggers.items():
        for h in logger.handlers:
            h.close()
        _loggers.pop(logger, None)


def addLevelName(level, name):
    _level_dict[level] = name


def basicConfig(
    filename=None,
    filemode="a",
    format=None,
    datefmt=None,
    level=DEBUG,
    stream=None,
    encoding="UTF-8",
    force=False,
):
    if "root" not in _loggers:
        _loggers["root"] = Logger("root")

    logger = _loggers["root"]

    if force or not logger.handlers:
        for h in logger.handlers:
            h.close()
        logger.handlers = []

        if filename is None:
            handler = StreamHandler(stream)
        else:
            handler = FileHandler(filename, filemode, encoding)

        handler.setLevel(level)
        handler.setFormatter(Formatter(format, datefmt))

        logger.setLevel(level)
        logger.addHandler(handler)


if hasattr(sys, "atexit"):
    sys.atexit(shutdown)



            
def config(filename='data/logging.json'):
    global _logger_level_dict,cnt
    global _DEFAULT_LEVEL

    try:
        with loader('json') as json:
            with open(filename) as file:
                cng = json.load(file)
                levels = cng['levels']
                _logger_level_dict = levels
                if 'default' in levels:
                    level = levels['default']
                    levelno =  getLevelNumber(level)
                    _DEFAULT_LEVEL = levelno          
    except Exception as ex:
        print(f"cannot open logging config {filename}.  {ex}")
        

def file_exists(filename):
    try:
        # Attempt to get the status of the file
        os.stat(filename)
        return True
    except OSError as e:
        return False

if file_exists('data/logging.json'):
    config('data/logging.json')