from PySide.QtGui import QApplication
import sys
import graphics

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainwin = graphics.WGSView()
    sys.exit(app.exec_())
