#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2018/12/5 1:19
# @Author  : 码农凯凯
# @File    : multiconn-server.py
# @belief  : stay foolish,stay hungry
# -*- coding: cp936 -*-
import sys
if(sys.version[:1] == "3"):
    import _thread as thread
import time
# import thread
import socket


# def timer(no, interval):
#     cnt = 0
#     while cnt < 10:
#         print('Thread:(%d) Time:%s/n' % (no, time.ctime()))
#         time.sleep(interval)
#         cnt += 1
#     thread.exit_thread()
#
#
# def test():  # Use thread.start_new_thread() to create 2 new threads
#     thread.start_new_thread(timer, (1, 1))
#     thread.start_new_thread(timer, (2, 2))


def child_connection(index, sock, connection):
    try:
        print("begin connecion ", index)
        print("begin connecion %d" % index)
        connection.settimeout(50)
        # 获得一个连接，然后开始循环处理这个连接发送的信息
        while True:
            buf = connection.recv(1024)
            print("Get value %s from connection %d: " % (buf, index))
            if buf == '1':
                print("send welcome")

                connection.send('welcome to server!'.encode())
            elif buf != '0':
                connection.send('please go out!'.encode())
                print("send refuse")

            else:
                print("close")

                break  # 退出连接监听循环
    except socket.timeout:  # 如果建立连接后，该连接在设定的时间内无数据发来，则time out
        print('time out')

    print("closing connection %d" % index)  # 当一个连接监听循环退出后，连接可以关掉
    connection.close()
    # 关闭连接，最后别忘了退出线程
    thread.exit_thread()


'''
建立一个python server，监听指定端口，
如果该端口被远程连接访问，则获取远程连接，然后接收数据，
并且做出相应反馈。
'''
if __name__ == "__main__":

    print("Server is starting")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('127.0.0.1', 8998))  # 配置soket，绑定IP地址和端口号
    sock.listen(5)  # 设置最大允许连接数，各连接和server的通信遵循FIFO原则
    print( "Server is listenting port 8001, with max connection 5")

    index = 0
    while True:  # 循环轮询socket状态，等待访问

        connection, address = sock.accept()
        index += 1
        # 当获取一个新连接时，启动一个新线程来处理这个连接
        thread.start_new_thread(child_connection, (index, sock, connection))
        if index > 10:
            break
    sock.close()

