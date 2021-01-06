
import logging
import json
import sys
import os, signal
import subprocess
import urllib
import urllib.parse
import threading
import atexit
JUPYTER_CMD = "jupyter"

FORMAT='%(asctime)s SERVER %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger('mainlogger')
logger.setLevel(logging.INFO)

values = {}

class JupyterStub(object):
    def __init__(self):
        pass

    def start(self, cmd_dict):
        if "cwd" in values.keys():
            os.chdir(values["cwd"])
        self.proc = subprocess.Popen(
                        [JUPYTER_CMD, "notebook"], 
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )   
        self.from_jupyter = self.proc.stdout
        self.jupyter_err = self.proc.stderr   
        self.redirect_thtread = threading.Thread(target=self.redirect_stderr)
        atexit.register(self.kill_jupyter)

    def kill_jupyter(self):
        self.proc.kill()

    def find_jupyter_url(self):
        pick_next = False
        while True:
            line = self.jupyter_err.readline().decode().strip()
            logger.info(line)
            if pick_next:
                tokens = line.split()
                o = urllib.parse.urlparse(tokens[3])
                break                 
            if "The Jupyter Notebook is running at:" in line:
                pick_next = True
        self.redirect_thtread.start()            
        return {"port": o.port, "host": "localhost", "token": o.query}

    def redirect_stderr(self):
        while True:
            one_line = self.jupyter_err.readline().decode().strip()
            logger.info("stderr: %s", one_line)
            if len(one_line) == 0:
                break
#            sys.stderr.write(one_line)
#            sys.stderr.flush()            


class ProcManager(object):
    def __init__(self):
        self.pids = []
    def add_pid(self, pid):
        self.pids.append(pid)
    def kill_all(self):
        logger.error("killing child process")
        for pid in self.pids:
            os.kill(pid, signal.SIGTERM)

class CmdErrorException(Exception):
    def __init__(self, msg):
        self.msg = msg

def gen_ack(code, val=None):
    return {"code": code, "val": val}

class Cmd(object):
    def __init__(self, json_string):
        self.obj = json.loads(json_string)
        logger.info("%s", str(self.obj))
        if type(self.obj) != dict:
            raise CmdErrorException(json_string)
        if not "cmd" in self.obj.keys():
            raise CmdErrorException(json_string)

    def proc(self):
        cmd = self.obj["cmd"]
        if cmd == "set":
            values.update(self.obj["vals"])
            return gen_ack("OK")
        if cmd == "exec":
            res = self.start_jupyter()
            return gen_ack("OK", res)
        if cmd == "test":
            return gen_ack("OK")
        if cmd == "stop":
            raise CmdErrorException('stopped')

    def start_jupyter(self):
        jupyter = JupyterStub()
        jupyter.start({})
        return jupyter.find_jupyter_url()

def main():
    logger.info('startup.')

    pm = ProcManager()

    try:
        while True:
            cmd = Cmd(sys.stdin.readline())
            res = cmd.proc()
            sys.stdout.write(json.dumps(res))
            sys.stdout.write("\n")
            sys.stdout.flush()
    except json.decoder.JSONDecodeError as e:
        logger.error('failed to parse : %s', e.msg)
    except Exception as e:
        logger.error('unknown error : %s', e.msg)
    pm.kill_all()

def test():
    jupyter = JupyterStub()
    jupyter.start({})
    print(jupyter.find_jupyter_url())

if __name__ == "__main__":
    main()