
import logging
import json
import sys
import os, signal

FORMAT='%(asctime)s SERVER %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger('mainlogger')
logger.setLevel(logging.INFO)

values = {}

class ProcManager(object):
    def __init__(self):
        self.pids = []
    def add_pid(self, pid):
        self.pids.append(pid)
    def kill_all(self):
        logger.error("killing child process")
        for pid in self.pids:
            os.kill(pid, signal.SIGTERM)

class CmdErroException(Exception):
    pass

class Cmd(object):
    def __init__(self, json_string):
        self.obj = json.loads(json_string)
        if type(self.obj) != dict:
            raise CmdErrorException(json_string)
        if not self.obj.has_key("cmd")
            raise CmdErrorException(json_string)

    def exec(self):
        cmd = self.obj["cmd"]
        if cmd == "set":
            values.update(self.obj["vals"])
            return "OK"
        if cmd == "exec":
            return "OK"

def main():
    logger.info('startup.')

    pm = ProcManager()
    try:
        while True:
            cmd = Cmd(sys.stdin.readline())
            res = cmd.exec()
            sys.stdout.write(res)
            sys.stdout.write("\n")
            sys.stdout.flush()
    except json.decoder.JSONDecodeError as e:
        logger.error('failed to parse : %s', e.msg)
    except Exception as e:
        logger.error('unknown error : %s', e.msg)
    pm.kill_all()



if __name__ == "__main__":
    main()