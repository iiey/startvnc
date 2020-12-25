#!/usr/bin/env python3
"""\033[1mConnect VNC Script\033[0m

This script is used to establish vnc connection with a tigervnc

\033[1mSyntax\033[0m:
    startvnc.py [server] <s|l>xxx
    startvnc.py [server] ip-addresse

\033[1mUsage\033[0m:
    \033[1m1.\033[0m Start server at remote
        startvnc.py server l193                # run server at labor ip193
        startvnc.py server 192.168.200.184     # run servert at given ip

    \033[1m2.\033[0m Start connection with remote
    Note: no prompt needed if password available under ~/.vnc/labs
        startvnc.py s156                # connect with ip156 in production
        startvnc.py 192.168.200.184     # connect with an ip addresse
"""
import re
import sys
import os
import subprocess


SERVER='x0tigervncserver'


def get_remote(arg):
    """ function to parse argument into ipv4
    regex to check either of of two matches '^(m1)|(m2)$'
    --> match.groups(): (g1, g2, g3, g4)
    match1:       s156
            --> ('s156', 's', '156', None)
    match2:       192.168.101.156
            --> (None, None, None, '192.168.101.156')
    """
    m = re.match(r"""^
                 (([ls])(\d{3}))        #m1: match shortname
                 |                      #or
                 ((?:\d{3}\.){3}\d{3})  #m2: match ipv4
                 $""", arg, re.X)
    ipv4 = None
    if m:
        ipv4 = 'procs@'
        # print(m.groups())
        if m.group(1):
            # 's' --> 192.168.101 |  'l' --> 192.168.200.
            octet3 = '200.' if m.group(2) == 'l' else '101.'
            octet12 = '192.168.'
            ipv4 += octet12 + octet3 + m.group(3)
        else:
            ipv4 += m.group(4)
    # print(ipv4)
    return ipv4


def connect_vnc(remote):
    """ function to connect with tigervnc server
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
    pfile = os.path.expanduser("~/.vnc/labs")
    parg = ("-passwd " + pfile) if os.path.isfile(pfile) else ""
    cmd = ("ssh -fL 9900:localhost:5900 {} sleep 5;"
           "vncviewer {} -DotWhenNoCursor=1 localhost:9900"
           .format(remote, parg))
    print(cmd)
    os.system(cmd)


def start_server(remote):
    """ function to start server at the given remote machine
    command explaination:
    -t: force psuedo-terminal allocation
        allocate a PTY on server side to have interactive prompt in ssh shell
        terminates connection also sends SIGUP to current command
    """
    cmd = "ssh {} 'DISPLAY=:0 {} -rfbauth ~/.vnc/passwd'"\
          .format(remote, SERVER)
    print(cmd)
    os.system(cmd)


def stop_server(remote):
    """function to stop tigervnc server at remote if running"""
    cmd  = ['ssh', remote, 'killall', SERVER]
    if subprocess.run(cmd, stdout=subprocess.PIPE).returncode == 0:
        print("Closed {} at {}".format(SERVER, remote))


def main():
    # check input arguments and open doc
    if len(sys.argv) == 1 or sys.argv[1] == '-h' or sys.argv[1] == '--help':
        print(__doc__)
        sys.exit(1)

    # start connection with remote
    if len(sys.argv) == 2:
        remote = get_remote(sys.argv[1])
        if remote:
            connect_vnc(remote)

    # start server at remote
    if len(sys.argv) == 3 and sys.argv[1] == 'server':
        remote = get_remote(sys.argv[2])
        if remote:
            start_server(remote)

    # stop server at remote
    if len(sys.argv) == 3 and sys.argv[1] == 'stop':
        remote = get_remote(sys.argv[2])
        if remote:
            stop_server(remote)


if __name__ == '__main__':
    main()
