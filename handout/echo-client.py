#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2018/12/5 0:51
# @Author  : 码农凯凯
# @File    : echo-client.py
# @belief  : stay foolish,stay hungry
import socket

HOST = '127.0.0.1'  # 服务器的主机名或者 IP 地址
PORT = 65432        # 服务器使用的端口

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(b'Hello, world')
    data = s.recv(1024)

print('Received', repr(data))