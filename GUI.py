import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from SkribblClient import SkribblClient
from game import SkribblGame
from PIL import Image
import hitherdither
from recorder import Recorder

class MainWindow(QMainWindow):
    def __init__(self, name="", code="", parent=None):
        super(MainWindow, self).__init__(parent)
        self.client = SkribblClient(name, code)
        self.game = None
        self._set_client_listeners()

        self.initWindow()
        self.thread = ClientThread(self.client)
        self.thread.start()

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

        self.wordwindow = WordWindow(self)

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
            "lobbyChooseWord": self.onLobbyChooseWord,
            "lobbyCurrentWord": self.onLobbyCurrentWord,
            "kicked": self.onKicked,
            "lobbyPlayerConnected": self.onLobbyPlayerConnected,
            "lobbyReveal": self.onLobbyReveal
        }
        [self.client.socket.on(event, method) for event, method in listeners.items()]

    def onChat(self, data):
        self.chatAddMsg("{}: {}".format(self.game.players[data['id']].name, data['message']))

    def onLobbyConnected(self, data):
        self.game = SkribblGame(data)
        self.chatAddMsg("Connected to server", QColor("green"))
        self.client.socket.emit("chat", "my name is walter clements and i love fire trucks and monster trucks")

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
            
            word = words[0] #i cant get wordwindow to work

            self.client.socket.emit("lobbyChooseWord", words.index(word))
            image = SkribblGame.AutoDraw.getGoogleImage(word)
            SkribblGame.AutoDraw.drawImage(self.client, self.paintbox, image, 'random')
            [Recorder.addWord(word) for word in words]

    def onLobbyCurrentWord(self, data):
        self.chatAddMsg("Current word: {} (len: {})".format(data, len(data)), QColor("green"))

        """
        hints = dict()
        if "_" in data:
            for letter_index in range(len(data)):
                if data[letter_index] is not "_":
                    hints[letter_index] = data[letter_index]
        possible_answers = Recorder.matchWords(len(data), hints)
        self.chatAddMsg(str(possible_answers))
        """
        
    def onKicked(self):
        self.chatAddMsg("You were kicked", QColor("red"))

    def onLobbyPlayerConnected(self, data):
        self.game.addPlayer(data)

    def onLobbyReveal(self, data):
        self.chatAddMsg("The word was \"{}\"".format(data['word']), QColor("green"))
        Recorder.addWord(data['word'])

    def sendInput(self):
        self.client.socket.emit("chat", self.input.text())
        self.input.clear()

    def chatAddMsg(self, msg, color=None):
        if color is not None:
            msg = QListWidgetItem(msg)
            msg.setForeground(color)
        self.chat.addItem(msg)
        self.chat.scrollToBottom()

class ClientThread(QThread):
    def __init__(self, client):
        QThread.__init__(self)
        self.client = client

    def __del__(self):
        self.wait()

    def run(self):
        self.client.connect()

class PaintBox(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.path = list()

    def paintEvent(self, event):
        painter = QPainter(self)
        for line in self.path:
            painter.setPen(QPen(QColor(line.r, line.g, line.b), line.size, Qt.SolidLine))
            painter.drawLine(line.x, line.y, line.end_x, line.end_y)

    def addUnparsedCommands(self, commands):
        for command in commands:
            self.path.append(SkribblGame.Canvas.parseDrawCommand(command, self.width(), self.height()))

class WordWindow(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.word = None
        self.initWindow()

    def initWindow(self):
        self.resize(400, 80)
        self.setWindowTitle("Choose word")
        self.main_layout = QHBoxLayout(self)
        self.main_widget = QWidget(self)
        self.button_layout = QHBoxLayout(self.main_widget)
        self.main_layout.addWidget(self.main_widget)
        self.btn_1 = QPushButton()
        self.btn_1.clicked.connect(lambda: self.buttonClicked(self.btn_1.text()))
        self.btn_2 = QPushButton()
        self.btn_2.clicked.connect(lambda: self.buttonClicked(self.btn_2.text()))
        self.btn_3 = QPushButton()
        self.btn_3.clicked.connect(lambda: self.buttonClicked(self.btn_3.text()))
        self.button_layout.addWidget(self.btn_1)
        self.button_layout.addWidget(self.btn_2)
        self.button_layout.addWidget(self.btn_3)

    def getWord(self, word_list):
        self.btn_1.setText(word_list[0])
        self.btn_2.setText(word_list[1])
        self.btn_3.setText(word_list[2])
        self.exec_()
        return self.word

    def buttonClicked(self, text):
        self.word = text
        self.close()
