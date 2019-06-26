import socketio

class SkribblClient:
    base_url = 'https://skribbl.io'

    def __init__(self, name="", code="", port=5001):
        self.socket = socketio.Client(logger=True)
        self.socket.on("result", self._party_url_received)
        self.me = self.UserData([9, 24, 16, -1], "", False, code, "English", name)
        self.address = self.base_url + ":" + str(port)
        
    def connect(self):
        if self.me.code != "":
            self._wait_for_url()
        self.socket.connect(self.address)
        self.socket.emit("userData", self.me.data())
        self.socket.wait()

    def _wait_for_url(self):
        self.socket.connect(self.base_url)
        self.socket.emit("login", self.me.data())
        self.socket.wait()

    def _party_url_received(self, data):
        self.address = data['host']
        self.log("Received url for game {}".format(self.me.code))
        self.socket.disconnect()

    def log(self, string):
        print("[*] {}".format(string))

    class UserData:
        def __init__(self, avatar, code, createPrivate, join, language, name):
            self.avatar = avatar
            self.code = code
            self.createPrivate = createPrivate
            self.join = join
            self.language = language
            self.name = name

        def data(self):
            return self.__dict__
