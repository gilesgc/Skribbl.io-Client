import socketio

class SkribblClient:
    base_url = 'https://server3.skribbl.io'

    def __init__(self, name="", code="", port=5001):
        self.socket = socketio.Client(logger=True)
        self.socket.on("result", self._party_url_received)
        self.me = self.UserData([9, 24, 16, -1], "", False, code, "English", name)
        self.address = self.base_url + ":" + str(port)
        self.code = code

    def connect(self):
        if self.code != "":
            self.log("Code found. Joining private game...")
            self._wait_for_url()

        self.log("Connecting to game...")
        self.socket.connect(self.address)
        self.socket.emit("userData", self.me.data())
        self.socket.wait()

    def _wait_for_url(self):
        self.socket.connect("https://skribbl.io:4999")
        self.socket.emit("login", self.me.data())
        self.socket.wait()

    def _party_url_received(self, data):
        self.address = data['host']
        self.log("Received url for game {}".format(self.code))
        self.socket.disconnect()

    def log(self, string):
        print("[SkribblClient] {}".format(string))

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
