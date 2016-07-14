from PySide.QtGui import QApplication
import sys
import mainwin

if __name__ == '__main__':
    app = QApplication(sys.argv)
    sciVisWindow = mainwin.SciVisView()
    sys.exit(app.exec_())
