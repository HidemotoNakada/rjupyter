
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

class JupyterStub(object):
    @classmethod
    def getStub(cls, cmd_dict):
        if "use_qrsh" in cmd_dict.keys() and cmd_dict["use_qrsh"]:
            return ABCIJupyterStub(cmd_dict)
        return DirectJupyterStub(cmd_dict)

    def __init__(self, cmd_dict):
        self.cmd_dict = cmd_dict
        self.jupyter_err = None

    def start(self):
        logger.error("start: not implemented")

    def kill_jupyter(self):
        logger.error("kill_jupyter: not implemented")
    
    def _gen_url_dict(self, o):
        logger.error("_gen_url_dict: not implemented")

    def find_jupyter_url(self):
        pick_next = False
        while True:
            line = self.jupyter_err.readline().decode().strip()
            if len(line) == 0:
                logger.error("failed to get jupyter url")
                return None
            logger.info(line)
            if pick_next:
                tokens = line.split()
                o = urllib.parse.urlparse(tokens[3])
                break                 
            if "The Jupyter Notebook is running at:" in line:
                pick_next = True
        self.redirect_thtread = threading.Thread(target=self._redirect_stderr)
        self.redirect_thtread.start()            
        return self._gen_url_dict(o)

    def _redirect_stderr(self):
        while True:
            one_line = self.jupyter_err.readline().decode().strip()
            logger.info("stderr: %s", one_line)
            if len(one_line) == 0:
                break
#            sys.stderr.write(one_line)
#            sys.stderr.flush()            

class DirectJupyterStub(JupyterStub):
    def __init__(self, cmd_dict):
        super().__init__(cmd_dict)
    def start(self):
        if "cwd" in self.cmd_dict.keys():
            logger.info("change cwd: %s", self.cmd_dict["cwd"])
            os.chdir(self.cmd_dict["cwd"])
        self.proc = subprocess.Popen(
                        [JUPYTER_CMD, "notebook"], 
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )   
        self.from_jupyter = self.proc.stdout
        self.jupyter_err = self.proc.stderr   
        atexit.register(self.kill_jupyter)

    def kill_jupyter(self):
        self.proc.kill()

    def _gen_url_dict(self, o):
        return {"port": o.port, "host": "localhost", "token": o.query}

class ABCIJupyterStub(JupyterStub):
    """
    to invoke jupyter with UGE the following command is required
    qrsh -g $GROUP -l rt_C.small=1 bash -c ". .bashrc; jupyter notebook"
    """
    
    def __init__(self, cmd_dict):
        super().__init__(cmd_dict)
    def _setup_string(self):
        return ". .bashrc; cd {:s}; {:s} notebook".format(self.cmd_dict["cwd"], JUPYTER_CMD)

    def start(self):
        arg_str = self._setup_string()
        logger.info("str: %s", arg_str)
        cmd_array = ["qrsh", 
                    "-g", self.cmd_dict["group_id"],
                    "-l", self.cmd_dict["resource_type"]+"="+str(self.cmd_dict["num_nodes"]),
                    "-l", "h_rt="+self.cmd_dict["duration"],
                    "-l", "USE_SSH="+("1" if self.cmd_dict["use_qrsh_ssh"] else "0"),
                    "bash", "-c", arg_str]
        self.proc = subprocess.Popen(
                        cmd_array,   
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )   
        self.from_jupyter = self.proc.stdout
        self.jupyter_err = self.proc.stderr   
        atexit.register(self.kill_jupyter)

    def kill_jupyter(self):
        self.proc.kill()

    def _gen_url_dict(self, o):
        return {"port": o.port, "host": o.hostname, "token": o.query}


class ProcManager(object):
    def __init__(self):
        self.pids = []
    def add_pid(self, pid):
        self.pids.append(pid)
    def kill_all(self):
        logger.error("killing child process")
        for pid in self.pids:
            logger.error("killing proc %d", pid)
            os.kill(pid, signal.SIGTERM)
pm = ProcManager()

class CmdErrorException(Exception):
    def __init__(self, msg):
        self.msg = msg

def gen_ack(code, val=None):
    return {"code": code, "val": val}

values = {}

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
            if res == None:
                return gen_ack("NG", "failed to start jupyter")
            return gen_ack("OK", res)
        if cmd == "test":
            return gen_ack("OK")
        if cmd == "stop":
            raise CmdErrorException('stopped')

    def start_jupyter(self):
        jupyter = JupyterStub.getStub(values)
        jupyter.start()
        pm.add_pid(jupyter.proc.pid)
        return jupyter.find_jupyter_url()

def main():
    logger.info('startup.')

    try:
        while True:
            cmd = Cmd(sys.stdin.readline())
            res = cmd.proc()
            sys.stdout.write(json.dumps(res))
            sys.stdout.write("\n")
            sys.stdout.flush()
    except json.decoder.JSONDecodeError as e:
        logger.error('failed to parse : %s', e.msg)
    except CmdErrorException as e:
        logger.error('stop requested')
    except Exception as e:
        logger.error('unknown error : %s', e)
    pm.kill_all()

def test():
    jupyter = JupyterStub.getStub(values)
    jupyter.start()
    print(jupyter.find_jupyter_url())

if __name__ == "__main__":
    main()