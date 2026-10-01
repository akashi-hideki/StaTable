import sys
from PySide6.QtWidgets import QApplication
from statable_gui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    from statable_gui.i18n import install_translator
    install_translator(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()