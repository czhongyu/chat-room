from protocol import THTTP_Request, THTTP_Response, split_message
import socket
import threading
from queue import Queue
from config import HOST, PORT, MAX_THREAD, BUFSIZE, LENGTH_SIZE


class ThreadManger(threading.Thread):
    def __init__(self, work_queue):
        threading.Thread.__init__(self)
        self.work_queue = work_queue
        self.daemon = True

    def run(self):
        while True:
            target, args = self.work_queue.get()
            target(*args)
            self.work_queue.task_done()


class ThreadPoolManger:
    def __init__(self, thread_num):
        self.work_queue = Queue()
        self.thread_num = thread_num
        self.__init_threading_pool(self.thread_num)

    def __init_threading_pool(self, thread_num):
        for _ in range(thread_num):
            thread = ThreadManger(self.work_queue)
            thread.start()

    def add_job(self, func, *args):
        self.work_queue.put((func, args))


class ChatRoom:
    def __init__(self):
        self.connection = {}
        self.group = {}

    def connect(self, connect):
        self.connection[connect] = {'username': '', 'group': ''}

    def sign_in(self, connect, username):
        # connection not exist
        if connect not in self.connection:
            return False, 'Connection not exist.'
        # already sign in
        if self.connection[connect]['username'] != '':
            return False, 'Already signed in.'
        # username collision
        for c in self.connection:
            if self.connection[c]['username'] == username:
                return False, 'Username collision.'
        self.connection[connect]['username'] = username
        return True, 'Sign in as {}.'.format(username)

    def sign_out(self, connect):
        # connection not exist
        if connect not in self.connection:
            return False, 'Connection not exist.'
        # not sign in
        if self.connection[connect]['username'] == '':
            return False, 'Not signed in.'
        # already in a group
        if self.connection[connect]['group'] != '':
            return False, 'Leave group first.'
        self.connection[connect]['username'] = ''
        return True, 'Sign out successful.'

    def join(self, connect, group):
        # connection not exist
        if connect not in self.connection:
            return False, 'Connection not exist.'
        # not sign in
        if self.connection[connect]['username'] == '':
            return False, 'Not signed in.'
        # already in a group
        if self.connection[connect]['group'] != '':
            return False, 'Already in a group.'
        self.connection[connect]['group'] = group
        if group not in self.group:
            self.group[group] = set()
        self.group[group].add(connect)
        return True, 'Join group {}.'.format(group)

    def leave(self, connect):
        # connection not exist
        if connect not in self.connection:
            return False, 'Connection not exist.'
        group = self.connection[connect]['group']
        # not sign in
        if self.connection[connect]['username'] == '':
            return False, 'Not signed in.'
        # not in a group
        if self.connection[connect]['group'] == '':
            return False, 'Not in a group.'
        self.group[group].remove(connect)
        if len(self.group[group]) == 0:
            del self.group[group]
        self.connection[connect]['group'] = ''
        return True, 'Leave group successful.'

    def send(self, connect):
        # connection not exist
        if connect not in self.connection:
            return False, 'Connection not exist.'
        # not sign in
        if self.connection[connect]['username'] == '':
            return False, 'Not signed in.'
        # not in a group
        if self.connection[connect]['group'] == '':
            return False, 'Not in a group.'
        # send message doesn't need to be shown on chat window
        return True, ''

    def member_of(self, connect):
        group = self.connection[connect]['group']
        if group not in self.group:
            return set()
        return self.group[group]

    def username_of(self, connect):
        return self.connection[connect]['username']

    def member_text(self, connect, other=None):
        members = []
        for c in self.member_of(connect):
            if c != other:
                members.append(self.username_of(c))
        return ','.join(members)


def handle_request(connect):
    global chat

    def send(message):
        connect.sendall(message.encode())

    def broadcast(message, other=None):
        for c in chat.member_of(connect):
            if c != other:
                # print('#Send to ' + str(c) + chat.username_of(c))
                c.sendall(message.encode())

    while True:
        try:
            message = connect.recv(BUFSIZE).decode()
            # print("thread {} is running".format(threading.current_thread().name))
            print('{} sent: {}'.format(threading.current_thread().name, message))
            # for request_message in split_message(message):
            #     request = THTTP_Request(message=request_message)
            request = THTTP_Request(message=message[LENGTH_SIZE:])
            if request.check() is False:
                response = THTTP_Response(status_code='400', body='Corrupted request!')
                # print(repr(response))
                send(repr(response))
            elif request.get_method() == 'signin':
                username = request.body
                success, description = chat.sign_in(connect, username)
                if success is True:
                    response = THTTP_Response(status_code='200', body=description)
                else:
                    response = THTTP_Response(status_code='300', body=description)
                # print(str(response))
                send(repr(response))
            elif request.get_method() == 'signout':
                success, description = chat.sign_out(connect)
                if success is True:
                    response = THTTP_Response(status_code='201', body=description)
                else:
                    response = THTTP_Response(status_code='301', body=description)
                send(repr(response))
            elif request.get_method() == 'join':
                group = request.body
                success, description = chat.join(connect, group)
                if success is True:
                    response = THTTP_Response(status_code='202', body=description)
                    member_response = THTTP_Response(status_code='204', body=chat.member_text(connect))
                    # print(str(member_response))
                    broadcast(repr(member_response))
                else:
                    response = THTTP_Response(status_code='302', body=description)
                # print(str(response))
                send(repr(response))
            elif request.get_method() == 'leave':
                member_text = chat.member_text(connect, other=connect)
                members = chat.member_of(connect)
                success, description = chat.leave(connect)
                if success is True:
                    response = THTTP_Response(status_code='203', body=description)
                    # update the members' list in other members
                    member_response = THTTP_Response(status_code='204', body=member_text)
                    for c in members:
                        if c != connect:
                            c.sendall(repr(member_response).encode())
                    empty_member_response = THTTP_Response(status_code='204')
                    send(repr(empty_member_response))
                else:
                    response = THTTP_Response(status_code='303', body=description)
                send(repr(response))
            elif request.get_method() == 'send':
                success, description = chat.send(connect)
                if success is True:
                    text = "{}: {}".format(chat.username_of(connect), request.body)
                    response = THTTP_Response(status_code='205', body=text)
                    broadcast(repr(response))
                else:
                    response = THTTP_Response(status_code='305', body=description)
                    send(repr(response))
            else:
                response = THTTP_Response(status_code='400', body='Corrupted request!')
                send(repr(response))

        except Exception as e:
            print(e)
            print('{} closed'.format(repr(connect)))
            # leave group
            member_text = chat.member_text(connect, other=connect)
            members = chat.member_of(connect)
            success, description = chat.leave(connect)
            if success is True:
                # update the members' list in other members
                member_response = THTTP_Response(status_code='204', body=member_text)
                for c in members:
                    if c != connect:
                        c.sendall(repr(member_response).encode())
            # sign out
            success, _ = chat.sign_out(connect)
            if success is True:
                print('{} signed out'.format(connect))
            else:
                print('{} signed out error'.format(connect))
            # kill loop
            break

    connect.close()

    
if __name__ == "__main__":
    print("Server is starting")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((HOST, PORT))
    sock.listen(MAX_THREAD)
    print("Server is running on ({}, {}), with max connection {}".format(HOST, PORT, MAX_THREAD))

    thread_pool = ThreadPoolManger(MAX_THREAD)
    chat = ChatRoom()
    try:
        while True:
            conn, address = sock.accept()
            chat.connect(conn)
            # handle request
            thread_pool.add_job(handle_request, *(conn, ))
    except Exception as e:
        print(e)
        sock.close()
