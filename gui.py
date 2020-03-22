import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from skribblclient import SkribblClient
from game import SkribblGame
from recorder import Recorder

class MainWindow(QMainWindow):
    def __init__(self, name="", code="", parent=None):
        super(MainWindow, self).__init__(parent)
        self.client = SkribblClient(name, code)
        self.game = None
        self._set_client_listeners()

        self.initWindow()

        self.clientThread = QThread()
        self.clientProcess = ClientProcess(self.client)
        self.clientProcess.moveToThread(self.clientThread)
        self.clientThread.started.connect(self.clientProcess.run)

        self.clientProcess.isChoosingWord.connect(self.onLobbyChooseWord)
        self.clientThread.start()

    def initWindow(self):
        self.resize(1068, 609)
        self.central_widget = QWidget(self)
        self.layout = QHBoxLayout(self.central_widget)
        self.paintbox = PaintBox(self.central_widget)

        palette = QPalette()
        brush = QBrush(QColor(255, 255, 255))
        brush.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.Window, brush)
        self.paintbox.setPalette(palette)
        self.paintbox.setAutoFillBackground(True)
        self.layout.addWidget(self.paintbox)

        self.wordwindow = WordWindow(self, self.choiceHandler)

        self.chatbox = QWidget(self.central_widget)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setHeightForWidth(self.chatbox.sizePolicy().hasHeightForWidth())
        self.chatbox.setSizePolicy(sizePolicy)
        self.chatbox_layout = QVBoxLayout(self.chatbox)
        self.chat = QListWidget(self.chatbox)
        self.chatbox_layout.addWidget(self.chat)
        self.input = QLineEdit(self.chatbox)
        self.input.editingFinished.connect(self.sendInput)
        self.chatbox_layout.addWidget(self.input)
        self.layout.addWidget(self.chatbox)
        self.setCentralWidget(self.central_widget)

    def _set_client_listeners(self):
        listeners = {
            "chat": self.onChat,
            "lobbyConnected": self.onLobbyConnected,
            "drawCommands": self.onDrawCommands,
            "canvasClear": self.onCanvasClear,
            "lobbyCurrentWord": self.onLobbyCurrentWord,
            "kicked": self.onKicked,
            "lobbyPlayerConnected": self.onLobbyPlayerConnected,
            "lobbyReveal": self.onLobbyReveal,
            "lobbyPlayerGuessedWord": self.onLobbyPlayerGuessedWord
        }
        [self.client.socket.on(event, method) for event, method in listeners.items()]

    def onChat(self, data):
        self.chatAddMsg("{}: {}".format(self.game.players[data['id']].name, data['message']))

    def onLobbyConnected(self, data):
        self.game = SkribblGame(data)
        self.chatAddMsg("Connected to server", QColor("green"))

    def onDrawCommands(self, data):
        self.paintbox.addUnparsedCommands(data)
        self.paintbox.update()

    def onCanvasClear(self):
        self.paintbox.path.clear()
        self.paintbox.update()

    def onLobbyChooseWord(self, data):
        if data['id'] == self.game.myID:
            words = data['words']
            self.chatAddMsg("Your turn!\nChoices: {}".format(', '.join(words)), QColor("green"))

            self.wordwindow.chooseWord(words)

            [Recorder.addWord(word) for word in words]

    def choiceHandler(self, choice, index):
        self.client.socket.emit("lobbyChooseWord", index)
        image = SkribblGame.AutoDraw.getGoogleImage(choice + " drawing")
        SkribblGame.AutoDraw.drawImage(self.client, self.paintbox, image, SkribblGame.AutoDraw.DrawMethod.scan)

    def onLobbyCurrentWord(self, data):
        self.chatAddMsg("Current word: {} (len: {})".format(data, len(data)), QColor("green"))

    def onKicked(self):
        self.chatAddMsg("You were kicked", QColor("red"))

    def onLobbyPlayerConnected(self, data):
        self.game.addPlayer(data)

    def onLobbyReveal(self, data):
        self.chatAddMsg("The word was \"{}\"".format(data['word']), QColor("green"))
        Recorder.addWord(data['word'])

    def onLobbyPlayerGuessedWord(self, data):
        if data == self.game.myID:
            self.chatAddMsg("You guessed the word", QColor("green"))
        else:
            self.chatAddMsg(self.game.players[data].name + " has guessed the word", QColor("green"))

    def sendInput(self):
        self.client.socket.emit("chat", self.input.text())
        self.input.clear()

    def chatAddMsg(self, msg, color=None):
        if color is not None:
            msg = QListWidgetItem(msg)
            msg.setForeground(color)
        self.chat.addItem(msg)
        self.chat.scrollToBottom()

    def possibleAnswers(hint):
        letters = dict()
        if "_" in hint:
            for letter_index in range(len(hint)):
                if hint[letter_index] is not "_":
                    letters[letter_index] = hint[letter_index]
        return Recorder.matchWords(len(hint), letters)

#onLobbyChooseWord must run on the GUI thread, so signals and slots have to be used
class ClientProcess(QObject):
    isChoosingWord = pyqtSignal([dict])

    def __init__(self, client):
        super().__init__()
        self.client = client
        self.client.socket.on("lobbyChooseWord", self.onLobbyChooseWord)

    def onLobbyChooseWord(self, data):
        self.isChoosingWord.emit(data)

    def run(self):
        self.client.connect()

class PaintBox(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.path = list()
        self.pen = QPen()
        self.pen.setStyle(Qt.SolidLine)
        self.pen.setCapStyle(Qt.RoundCap)
        self.pen.setJoinStyle(Qt.RoundJoin)

    def paintEvent(self, event):
        painter = QPainter(self)
        for line in self.path:
            self.pen.setColor(QColor(line.r, line.g, line.b))
            self.pen.setWidth(line.size)
            painter.setPen(self.pen)
            painter.drawLine(line.x, line.y, line.end_x, line.end_y)

    def addUnparsedCommands(self, commands):
        for command in commands:
            self.path.append(SkribblGame.Canvas.parseDrawCommand(command, self.width(), self.height()))

class WordWindow(QDialog):
    def __init__(self, parent, choiceHandler):
        super(WordWindow, self).__init__(parent)
        self.word = None
        self.choiceHandler = choiceHandler
        self.initWindow()

    def initWindow(self):
        self.resize(400, 80)
        self.setWindowTitle("Choose word")
        self.main_layout = QHBoxLayout(self)
        self.main_widget = QWidget(self)
        self.button_layout = QHBoxLayout(self.main_widget)
        self.main_layout.addWidget(self.main_widget)
        self.btn_1 = QPushButton()
        self.btn_1.clicked.connect(lambda: self.buttonClicked(self.btn_1.text(), 0))
        self.btn_2 = QPushButton()
        self.btn_2.clicked.connect(lambda: self.buttonClicked(self.btn_2.text(), 1))
        self.btn_3 = QPushButton()
        self.btn_3.clicked.connect(lambda: self.buttonClicked(self.btn_3.text(), 2))
        self.button_layout.addWidget(self.btn_1)
        self.button_layout.addWidget(self.btn_2)
        self.button_layout.addWidget(self.btn_3)

    def chooseWord(self, word_list):
        self.btn_1.setText(word_list[0])
        self.btn_2.setText(word_list[1])
        self.btn_3.setText(word_list[2])
        self.show()

    def buttonClicked(self, choice, index):
        self.hide()
        self.choiceHandler(choice, index)
