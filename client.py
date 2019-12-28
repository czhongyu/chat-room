from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from mainwindow import Ui_MainWindow
import socket
import sys
from config import HOST, PORT, BUFSIZE
from protocol import THTTP_Request, THTTP_Response, split_message


class Receiver(QThread):
    # signals
    signal_chat = pyqtSignal(str)
    signal_username = pyqtSignal(str)
    signal_group = pyqtSignal(str)
    signal_member = pyqtSignal(str)

    def __init__(self, socket, parent=None):
        super(Receiver, self).__init__(parent)
        self.working = True
        self.socket = socket

    def __det__(self):
        self.working = False
        self.wait()

    def run(self):
        # receive
        while True:
            try:
                message = self.socket.recv(BUFSIZE).decode()
                # print('send {}'.format(message))
                for response_message in split_message(message):
                    response = THTTP_Response(message=response_message)
                    if response.check() is True:
                        print(str(response))
                        # not chat, show short response message
                        if response.get_status_code() != '205':
                            self.signal_chat.emit(str(response))
                        # OK response
                        if response.get_status_code() == '200':
                            self.signal_username.emit(response.body)
                        elif response.get_status_code() == '201':
                            self.signal_username.emit('')
                        elif response.get_status_code() == '202':
                            self.signal_group.emit(response.body)
                        elif response.get_status_code() == '203':
                            self.signal_group.emit('')
                        elif response.get_status_code() == '204':
                            self.signal_member.emit(response.body.strip(','))
                        elif response.get_status_code() == '205':
                            self.signal_chat.emit(response.body)

            except Exception as e:
                print(e)
                break


class MyWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, socket):
        super(MyWindow, self).__init__()
        self.setupUi(self)

        # socket
        self.socket = socket
        # receive messages
        self.receiver = Receiver(socket)
        self.receiver.signal_chat.connect(self.set_chat)
        self.receiver.signal_username.connect(self.set_username)
        self.receiver.signal_group.connect(self.set_group)
        self.receiver.signal_member.connect(self.set_member)
        self.receiver.start()

        # buttons
        self.sign_in_button.clicked.connect(lambda: self.sign_in())
        self.sign_out_button.clicked.connect(lambda: self.sign_out())
        self.join_button.clicked.connect(lambda: self.join())
        self.leave_button.clicked.connect(lambda: self.leave())
        self.send_button.clicked.connect(lambda: self.send())

    def _send(self, message):
        self.socket.sendall(message.encode())

    def sign_in(self):
        dialog = QInputDialog.getText(self, "Sign in", "Username")
        if dialog[1] is True and dialog[0] != '':
            request = THTTP_Request(method='signin', target=HOST, headers=[], body=dialog[0])
            # print(str(request))
            if request.check() is True:
                self._send(repr(request))

    def sign_out(self):
        request = THTTP_Request(method='signout', target=HOST, headers=[], body='')
        if request.check() is True:
            self._send(repr(request))

    def join(self):
        dialog = QInputDialog.getText(self, "Create / Join", 'Group name')
        if dialog[1] is True and dialog[0] != '':
            request = THTTP_Request(method='join', target=HOST, headers=[], body=dialog[0])
            if request.check() is True:
                self._send(repr(request))

    def leave(self):
        request = THTTP_Request(method='leave', target=HOST, headers=[], body='')
        if request.check() is True:
            self._send(repr(request))

    def send(self):
        text = self.message_input.toPlainText()
        self.message_input.setPlainText('')
        if text != '':
            request = THTTP_Request(method='send', target=HOST, headers=[], body=text)
            if request.check() is True:
                self._send(repr(request))

    def set_username(self, username):
        globals()['username'] = username
        self.username_window.setText(username)

    def set_group(self, group):
        globals()['group'] = group
        self.group_window.setText(group)

    def set_member(self, member):
        self.member_window.setText(member)

    def set_chat(self, message):
        text = self.chat_window.toPlainText()
        self.chat_window.setPlainText(text + message + '\n')

        cursor = self.chat_window.textCursor()
        pos = len(self.chat_window.toPlainText())
        cursor.setPosition(pos - 1)
        self.chat_window.ensureCursorVisible()
        self.chat_window.setTextCursor(cursor)


if __name__ == '__main__':
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    username = ''
    group = ''

    try:
        sock.connect((HOST, PORT))
        app = QApplication(sys.argv)
        myshow = MyWindow(sock)
        myshow.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(e)

    sock.close()
