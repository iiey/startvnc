# startvnc
script for quick start of remote control using tigervnc

```bash
# safe connection by tunneling vnc over ssh
# 0. setup on server side
~/.vnc
├── config (localhost)
└── passwd (password)

# 1. start server from remote machine:
DISPLAY=:0 x0tigervncserver -rfbauth ~/.vnc/passwd

# 2. run vnc from client side:
ssh -fL 9900:localhost:5900 "user@$host" sleep 5; vncviewer -DotWhenNoCursor=1 localhost:9900
```
