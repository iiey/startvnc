#!/usr/bin/env python3
"""\033[1mConnect VNC Script\033[0m

This script is used to establish vnc connection with a tigervnc

\033[1mSyntax\033[0m:
    startvnc.py [<s|l>xxx|ip-address] [server|connect|stop]

\033[1mUsage\033[0m:
   \033[1m\033[0m Start server (if not running)
    at labor machine and connect with it
    \033[1mstartvnc.py l193\033[0m

\033[1mExample\033[0m:
    startvnc.py l184 start           # start server at 192.168.200.184 (labor)
    startvnc.py s157 connect         # connect with ip 192.168.101.157
    startvnc.py 192.168.200.193 stop # stop server of given ip

version 1.0
"""
import functools
import os
import re
import shlex
import subprocess
import sys
import time
from typing import Any, Callable, cast, Optional, TypeVar


F = TypeVar('F', bound=Callable[..., Any])


def check_remote(func: F) -> F:
    """decorator to validate attribute remote of class Vnc
    execute decorated function if remote's valid otherwise return stderr
    """
    @functools.wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        isVnc = isinstance(self, Vnc) and hasattr(self, 'remote')
        if isVnc and self.remote:
            return func(self, *args, **kwargs)
        elif not isVnc:
            print("{} is not type Vnc".format(self), file=sys.stderr)
        else:
            print("Could not identify ip from paramter: {}"
                  .format(self.ip), file=sys.stderr)
    return cast(F, wrapper)


class Vnc:
    """Virtual Network Connection class
    which is used to start, connect and stop server
    """
    __SERVER = 'x0tigervncserver'   # vnc program name
    __CLIENT = 'vncviewer'

    def __init__(self, ip_address: str) -> None:
        """constructor of Vnc takes an input string
        instance attributes:
            ip (str): store input ip_address
            remote (str): store converted  form 'procs@ipv4'
        Args:
            ip_address (str): input which is interpretable to ipv4
        """
        self.ip = ip_address
        self.remote = self.get_remote(ip_address)

    @staticmethod
    def get_remote(ip_address: str) -> Optional[str]:
        """function to parse argument
        use regex to check either of of two matches '^(m1)|(m2)$'
        --> match.groups(): (g1, g2, g3, g4)
        match1:       s156
                --> ('s156', 's', '156', None)
        match2:       192.168.101.156
                --> (None, None, None, '192.168.101.156')
        Args:
            ip_address (str): string to identify ipv4
        Returns:
            ipv4 (str): if input valid otherwise None
        """
        m = re.match(r"""^
                     (([ls])(\d{3}))            #m1: match shortname
                     |                          #or
                     ((?:\d{3}\.){3}\d{3})      #m2: match ipv4
                     $""", ip_address, re.X)
        remote = None
        if m:
            remote = 'procs@'
            # print(m.groups())
            if m.group(1):
                # 's' --> 192.168.101 |  'l' --> 192.168.200.
                octet3 = '200.' if m.group(2) == 'l' else '101.'
                octet12 = '192.168.'
                remote += octet12 + octet3 + m.group(3)
            else:
                remote += m.group(4)
        # print(remote)
        return remote

    @check_remote
    def connect_server(self, localport: int = 9900) -> None:
        """function to connect with tigervnc server
        bypass password prompt with a valid password file under: '~/.vnc/labs'
        Args:
            localport (int): do forwarding to this port on local side

        command explaination:
        -L: port forwarding
            e.g. execute ssh -L 1234:google.com:80
            open addresse 'http://localhost:1234' to see result of googles page

        -f: make ssh go in the background
            it will still be alive by executing 'sleep 5'

        vncviewer is then executed and ssh remains open in the background
        as long as vncviewer makes use of the tunnel
        ssh is closed once the tunnel is dropped
        """
        pfile = os.path.expanduser('~/.vnc/labs')
        parg = ("-passwd " + pfile) if os.path.isfile(pfile) else ""
        cmd = ("ssh -fL {port}:localhost:5900 {} sleep 5;"
               "vncviewer {} -DotWhenNoCursor=1 localhost:{port}"
               .format(self.remote, parg, port=localport))
        print(cmd)
        os.system(cmd)

    @check_remote
    def start_server(self, term: bool = False) -> None:
        """function to start server at the given remote machine
        command explaination:
        -t: force psuedo-terminal allocation
            allocate a PTY on server side to have interactive prompt in
            ssh shell terminates connection also sends SIGUP to current command
        """
        cmd = "ssh {} {} 'DISPLAY=:0 {} -rfbauth ~/.vnc/passwd'"\
              .format('-t' if term else '', self.remote, self.__SERVER)
        print(cmd)
        if term:
            # keep running interactive
            subprocess.run(shlex.split(cmd))
        else:
            # start as child process in bg
            subprocess.Popen(shlex.split(cmd),
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.STDOUT)
            # wait a bit after sending cmd via ssh
            time.sleep(1)

    @check_remote
    def stop_server(self) -> None:
        """function to stop tigervnc server"""
        cmd = ['ssh', str(self.remote), 'killall', self.__SERVER]
        if subprocess.run(args=cmd, stdout=subprocess.PIPE).returncode == 0:
            print("Closed {} at {}".format(self.__SERVER, self.remote))

    @check_remote
    def is_server_running(self) -> bool:
        """function to check whether tigervnc server is running at remote"""
        cmd = ['ssh', str(self.remote), 'pgrep', '-f', self.__SERVER]
        if subprocess.run(cmd, stdout=subprocess.PIPE).returncode == 0:
            print("{} already running at {}"
                  .format(self.__SERVER, self.remote))
            return True
        else:
            return False

    def is_client_running(self) -> int:
        """function to check whether vncviewer is running at local machine
        Returns:
            num_proc (int): number of vncviewer processes are running
            if success otherwise asumming zero
        """
        cmd = ['pgrep', '-c', self.__CLIENT]
        res = subprocess.run(cmd, stdout=subprocess.PIPE,
                             universal_newlines=True)
        if res.returncode == 0:
            num_proc = int(res.stdout.strip('\n'))
            return num_proc
        else:
            return 0

    @check_remote
    def start_client(self) -> None:
        """function start vnc client and connect with server at remote
        start server if it's not running then connect with server
        """
        is_started = False
        if not self.is_server_running():
            is_started = True
            self.start_server(False)

        num_proc = self.is_client_running()
        listen = 9900
        if num_proc > 0:
            listen += num_proc
            print("{} instance(s) of {} is running. Use forwarding port: {}"
                  .format(num_proc, self.__CLIENT, listen))
        self.connect_server(listen)

        if is_started:
            self.stop_server()


def main() -> None:
    # open doc in case of insufficient argument(s)
    if len(sys.argv) == 1 or sys.argv[1] == '-h' or sys.argv[1] == '--help':
        print(__doc__)
        if len(sys.argv) == 2 and sys.argv[1] == '--help':
            help(Vnc)
        sys.exit(1)

    vnc_obj = Vnc(sys.argv[1])

    # start connection with remote
    if len(sys.argv) == 2:
        vnc_obj.start_client()

    # call connect method
    if len(sys.argv) == 3:
        cmds = [['start_server', 'True'], ['connect_server'], ['stop_server']]
        func_param = [cmd for cmd in cmds if sys.argv[2] in cmd[0]]
        if func_param:
            func, *param = func_param[0]
            getattr(vnc_obj, func)(*param)


if __name__ == '__main__':
    main()
