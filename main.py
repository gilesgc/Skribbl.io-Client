from PyQt5.QtWidgets import QApplication
import sys
import gui

def main():
    app = QApplication(sys.argv)
    window = gui.MainWindow(name="bot", code="")
    window.show()
    app.exec_()
    window.client.socket.disconnect()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(e)
        input("\nPress enter to exit")
