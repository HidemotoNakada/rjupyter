import logging
import json
import sys, os
import subprocess
import socketserver
import threading
import tempfile
import time
from pathlib import Path

FORMAT='%(asctime)s CLIENT %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger('mainlogger')
logger.setLevel(logging.INFO)

DEFAULT_SERVER="sss"
#DEFAULT_SERVER="localhost"
SSH_COMMAND="ssh"
SSH_OPTIONS={"controlmaster":"auto", "controlpath":None}
RJUPYTER_SERVER="rjupyter/src/rjupyter_server"
#RJUPYTER_SERVER="rjupyter_server"
RCWD="."

def gen_ssh_options(sock_file):
    SSH_OPTIONS["controlpath"] = sock_file
    options = []
    for k, v in SSH_OPTIONS.items():
        options.append("-o")
        options.append("%s=%s"%(k,v))
    logger.info(str(options))
    return options

def gen_sock_file():
    ssh_dir = str(Path.home())+"/.ssh/"
    f = tempfile.NamedTemporaryFile(prefix=ssh_dir)
    f.close()
    #os.remove(f.name)
    return f.name

class ServerStub(object):
    def __init__(self, server):
        self.server = server
        self.sock_file = gen_sock_file()
        opts = gen_ssh_options(self.sock_file)
        self.proc = subprocess.Popen(
                        [SSH_COMMAND, *opts, server, RJUPYTER_SERVER], 
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
        self.to_server = self.proc.stdin
        self.from_server = self.proc.stdout
        self.server_err = self.proc.stderr
        self.redirect_thtread = threading.Thread(target=self.redirect_stderr)
        self.redirect_thtread.start()

    def test(self):
        test_cmd_dict = {"cmd":"test"}
        self.send(test_cmd_dict)
        ack = self.recv()
        assert(ack["code"] == "OK")
    def set(self, dict):
        cmd_dict = {"cmd":"set", "vals":dict}
        self.send(cmd_dict)
        ack = self.recv()
        assert(ack["code"] == "OK")
    def exec(self):
        cmd_dict = {"cmd":"exec"}
        self.send(cmd_dict)
        ack = self.recv()
        assert(ack["code"] == "OK")
        logger.info("port:%s", ack["val"]["port"])
        self.target_port = ack["val"]["port"]
        self.target_host = ack["val"]["host"]
        self.token = ack["val"]["token"]

    def add_forward(self, local_port):
        subprocess.run(
            [SSH_COMMAND, "-O", "forward", "-L", 
            "%d:%s:%s"%(local_port, self.target_host, self.target_port),
            "-S", self.sock_file,
            self.server
            ]
        )
    def stop(self):
        cmd_dict = {"cmd":"stop"}
        self.send(cmd_dict)

    def send(self, cmd_dict):
        cmd_str = json.dumps(cmd_dict).encode()
        self.to_server.write(cmd_str)
        self.to_server.write(b'\n')
        self.to_server.flush()
        logger.info("sending: %s", cmd_str)

    def recv(self):
        ack_str = self.from_server.readline().decode().strip()
        logger.info("recv: %s", ack_str)
        return json.loads(ack_str)

    def redirect_stderr(self):
        while True:
            one_line = self.server_err.readline()
            if len(one_line) == 0:
                break
            sys.stderr.write(one_line.decode())
            sys.stderr.flush()        

def find_vacant_port(port_base, trial_count):
    """find vacant port for forwarding, 
    starts with port_base and test at most trial_count ports.
    if it cannot find, it raise OSError"""
    for i in range(trial_count):
        try:
            ss = socketserver.TCPServer(('127.0.0.1', port_base + i), None)
            # found one
            ss.server_close()
            return port_base + i
        except OSError:
            pass
    raise OSError("cannot find vacant port")

def open_browser(port, tokenstring):
    subprocess.run(
        [
            "open",
            "http://localhost:%d/?%s"%(port,tokenstring)
        ]
    )

def main():
    server = ServerStub(DEFAULT_SERVER)
    server.test()
    server.set({
        "cwd": RCWD
    })
    server.exec()
    local_port = find_vacant_port(9000, 100)
    logger.info("found local port %s", local_port)
    time.sleep(10)
    server.stop()
    server.add_forward(local_port)
#    open_browser(local_port, server.token)

if __name__ == "__main__":
    main()
