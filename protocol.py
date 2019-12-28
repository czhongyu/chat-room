from config import LENGTH_SIZE

VERSION = 'THTTP/1.1'


def split_message(message):
    p = 0
    messages = []
    while p < len(message):
        length = int(message[p: p + LENGTH_SIZE])
        p += LENGTH_SIZE
        # print('#MESSAGE#' + message[p: p + length])
        messages.append(message[p: p + length])
        p += length
    return messages


# THTTP: trivial hypertext transfer protocol
class _THTTP:
    def __init__(self, start_line, headers=[], body="", message=None):
        self._new_line = "\r\n"

        self._length_size = LENGTH_SIZE
        self.start_line = start_line
        self.headers = headers
        self.empty_line = self._new_line
        self.body = body

        if message is not None:
            self._parse(message)

    def _parse(self, message):
        split = message.split('\r\n')
        self.start_line = split[0].split(' ', 2)
        self.headers = [tuple(header.split(': ', 1)) for header in split[1:-2]]
        self.body = split[-1].strip()

    def __repr__(self):
        # get the str representation of the message
        start_line = ' '.join(self.start_line) + self._new_line
        headers = "" if len(self.headers) == 0 else self._new_line.join([': '.join([t, v]) for (t, v) in self.headers]) + self._new_line
        text = start_line + headers + self.empty_line + self.body
        text = text[: min(len(text), 10 ** self._length_size - 1)]
        length = str(len(text)).zfill(self._length_size)
        return length + text

    def _check_headers(self):
        if len(self.headers) == 0:
            return True
        for t in self.headers:
            if len(t) != 2:
                return False
        return True


class THTTP_Request(_THTTP):
    def __init__(self, method="", target="/", headers=[], body="", message=None):
        super().__init__([method.lower(), target, VERSION], headers=headers, body=body, message=message)
        self._methods = ['signin', 'signout', 'join', 'leave', 'send']
        # GET: get stuff from target url

    def __str__(self):
        return "{} {}: {}".format(self.start_line[0], self.start_line[1], self.body.strip())

    def get_method(self):
        return self.start_line[0]

    def check(self):
        if self.start_line[0] not in self._methods:
            return False
        if self.start_line[2] != VERSION:
            return False
        if self._check_headers() is False:
            return False
        return True


class THTTP_Response(_THTTP):
    def __init__(self, status_code='400', headers=[], body="", message=None):
        self._status = {
            '200': 'Sign in success',
            '201': 'Sign out success',
            '202': 'Join group success',
            '203': 'Leave group success',
            '204': 'Group members',
            '205': 'Send chat success',
            '300': 'Sign in error',
            '301': 'Sign out error',
            '302': 'Join group error',
            '303': 'Leave group error',
            '305': 'Send chat error',
            '400': 'Wrong format request',
        }
        if status_code not in self._status:
            status_code = '400'
        super().__init__([VERSION, status_code, self._status[status_code]], headers=headers, body=body, message=message)

    def __str__(self):
        # display on the chat window, easy to read
        return "{} {}: {}".format(self.start_line[1], self.start_line[2], self.body)

    def get_status_code(self):
        return self.start_line[1]

    def check(self):
        if self.start_line[0] != VERSION:
            return False
        if self.start_line[1] not in self._status:
            return False
        if self.start_line[2] != self._status[self.start_line[1]]:
            return False
        # if self._check_headers() is False:
        #     return False
        return True
