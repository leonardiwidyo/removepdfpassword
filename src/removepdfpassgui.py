import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, 
                           QMessageBox, QLineEdit, QPushButton, QListWidget, 
                           QListWidgetItem, QFileIconProvider, QMenu, 
                           QDialog, QAction)
from PyQt5.QtGui import QPixmap
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt5.QtCore import Qt, QSize, QFileInfo, QUrl

import pikepdf
from pikepdf import Pdf

# Set application name for macOS
import platform
if platform.system() == 'Darwin':  # macOS
    from PyQt5.QtWidgets import QApplication
    QApplication.setApplicationName("PDF Password Remover")

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.setWindowTitle("About")
        self.setFixedSize(300, 100)
        
        layout = QVBoxLayout()

        # Add clickable link
        copyright_label = QLabel('RPP v1.03 (c) 2025, Leonardi', self)
        copyright_label.setAlignment(Qt.AlignCenter)
        copyright_label.setOpenExternalLinks(True)
        layout.addWidget(copyright_label)

        # Label for displaying the image
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_label)

        # Load image from URL
        self.loadImageFromUrl("https://storage.ko-fi.com/cdn/brandasset/kofi_button_blue.png")

        # Add clickable link
        link_label = QLabel('<a href="https://ko-fi.com/leonardiw">Buy me a coffee</a>', self)
        link_label.setAlignment(Qt.AlignCenter)
        link_label.setOpenExternalLinks(True)
        layout.addWidget(link_label)

        self.setLayout(layout)

    def loadImageFromUrl(self, url):
        self.network_manager = QNetworkAccessManager(self)
        self.network_manager.finished.connect(self.onImageDownloaded)
        self.network_manager.get(QNetworkRequest(QUrl(url)))

    def onImageDownloaded(self, reply):
        pixmap = QPixmap()
        pixmap.loadFromData(reply.readAll())
        self.image_label.setPixmap(pixmap.scaledToWidth(150))
        
class DragDropLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("border: 2px dashed #aaa; padding: 20px;")
        self.setText("Drag and drop PDF files here")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith('.pdf'):
                    self.parent().parent().add_file_to_list(file_path)
            event.acceptProposedAction()

class PDFPasswordRemover(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Remove PDF Password")
        self.setGeometry(100, 100, 400, 300)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create menu bar
        menubar = self.menuBar()
        help_menu = menubar.addMenu("Help")
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self.show_about_dialog)

        # Drag-and-drop label
        self.drag_drop_label = DragDropLabel(central_widget)
        layout.addWidget(self.drag_drop_label)

        # List widget to display selected files
        self.file_list = QListWidget(central_widget)
        self.file_list.setIconSize(QSize(32, 32))
        layout.addWidget(self.file_list)

        # Enable context menu for the list widget
        self.file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self.show_context_menu)

        # Password input
        self.password_input = QLineEdit(central_widget)
        self.password_input.setPlaceholderText("Enter PDF password")
        layout.addWidget(self.password_input)

        # Remove password button
        self.remove_button = QPushButton("Remove Password", central_widget)
        self.remove_button.clicked.connect(self.remove_password)
        layout.addWidget(self.remove_button)

        # List to store file paths
        self.file_paths = []

        # File icon provider
        self.icon_provider = QFileIconProvider()

    def show_about_dialog(self):
        about_dialog = AboutDialog(self)
        about_dialog.exec_()

    def add_file_to_list(self, file_path):
        if file_path not in self.file_paths:
            self.file_paths.append(file_path)

            # Create a QFileInfo object for the file
            file_info = QFileInfo(file_path)

            # Create a list item with the original file icon and truncated filename
            item = QListWidgetItem()
            item.setIcon(self.icon_provider.icon(file_info))
            item.setText(self.truncate_filename(file_path))
            item.setData(Qt.UserRole, file_path)
            self.file_list.addItem(item)

    def truncate_filename(self, file_path, max_length=30):
        if len(file_path) > max_length:
            return "..." + file_path[-max_length:]
        return file_path

    def show_context_menu(self, position):
        # Create a context menu
        context_menu = QMenu(self)

        # Add "Remove" action
        remove_action = QAction("Remove", self)
        remove_action.triggered.connect(self.remove_selected_file)
        context_menu.addAction(remove_action)

        # Show the context menu
        context_menu.exec_(self.file_list.viewport().mapToGlobal(position))

    def remove_selected_file(self):
        # Get the selected item
        selected_item = self.file_list.currentItem()
        if selected_item:
            # Remove the file path from the list
            file_path = selected_item.data(Qt.UserRole)
            self.file_paths.remove(file_path)

            # Remove the item from the list widget
            self.file_list.takeItem(self.file_list.row(selected_item))

    def remove_password(self):
        if not self.file_paths:
            QMessageBox.warning(self, "Error", "No files selected!")
            return

        password = self.password_input.text()
        if not password:
            QMessageBox.warning(self, "Error", "Please enter a password!")
            return

        for file_path in self.file_paths:
            try:
                with Pdf.open(file_path, password=password, allow_overwriting_input=True) as pdf:
                    pdf.save(file_path)
                print(f"Password removed successfully! File overwritten: {file_path}")
            except pikepdf.PasswordError:
                QMessageBox.critical(self, "Error", f"Incorrect password for file: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred with file {file_path}: {e}")

        # Clear the list after processing
        self.file_paths.clear()
        self.file_list.clear()
        QMessageBox.information(self, "Success", "All files processed!")

    def closeEvent(self, event):
        # Show the AboutDialog when the application is about to close
        self.show_about_dialog()
        event.accept()  # Accept the close event to allow the application to exit

if __name__ == "__main__":
    # Set these before creating QApplication
    if not QApplication.instance():
        app = QApplication(sys.argv)
        app.setApplicationName("PDF Password Remover")
        app.setOrganizationName("Leonardi")
        app.setOrganizationDomain("leonardiw.com")
    else:
        app = QApplication.instance()
    
    window = PDFPasswordRemover()
    window.show()
    sys.exit(app.exec_())