from pathlib import Path

import cv2 as cv
import qtawesome as qta

from grayscale_image_processing_widget.custom_components.mimetypes import check_file_type
from grayscale_image_processing_widget.custom_components.my_colors import tab10_qcolor
from grayscale_image_processing_widget.defs import QtGui, QtCore, QtWidgets
from grayscale_image_processing_widget.defs import get_project_root
from grayscale_image_processing_widget.dock import ImgProcessDock
from grayscale_image_processing_widget.image_widget import ImageWidget

QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)


class ProcessWidget(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.img_path = None
        self.original_img = None

        self.setWindowTitle("Grayscale Image Processing")
        self.resize(1000, 500)
        self.setAcceptDrops(True)
        self.setWindowIcon(
            QtGui.QIcon(qta.icon("fa5s.images", color=tab10_qcolor["blue"]))
        )

        main_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(main_widget)
        main_layout = QtWidgets.QVBoxLayout(main_widget)

        self.main_widget = main_widget

        self.dock = ImgProcessDock()
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.dock)

        self.img_widget = ImageWidget()
        main_layout.addWidget(self.img_widget)

        self.connect_ui()

        # load settings from previous session
        self.settings_file = get_project_root() / "image_processing.ini"
        if self.settings_file.is_file():
            settings = QtCore.QSettings(
                str(self.settings_file), QtCore.QSettings.IniFormat
            )
            self.gui_restore(settings)

        self.img_widget.setFocus()

    def connect_ui(self):
        self.dock.connect_ui(self.update_img)
        self.dock.peek_groupbox.peek_button.pressed.connect(self.peek_original_img)
        self.dock.peek_groupbox.peek_button.released.connect(self.update_img)
        self.dock.save_groupbox.save_button.clicked.connect(self.save_button_clicked)
        self.dock.save_groupbox.save_as_button.clicked.connect(
            self.save_as_button_clicked
        )

    def update_img(self):
        if self.img_path:
            processed_img = self.process_img(self.original_img)
            self.img_widget.setImage(processed_img)

    def process_img(self, img):
        process_widget = self.dock.process_groupbox.stacked_layout.currentWidget()
        oriented_image = self.dock.orient_groupbox.orient_img(img)
        processed_img = process_widget.process_img(oriented_image)
        return processed_img

    def peek_original_img(self):
        oriented_image = self.dock.orient_groupbox.orient_img(self.original_img)
        self.img_widget.setImage(oriented_image)

    def read_img(self, path):
        self.img_path = path
        self.original_img = cv.imread(str(self.img_path), cv.IMREAD_GRAYSCALE)
        self.update_img()
        self.dock.process_groupbox.adjust_range(self.original_img.shape)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            path = Path(e.mimeData().urls()[0].toLocalFile())
            if check_file_type(path, "image"):
                e.acceptProposedAction()
                e.setDropAction(QtCore.Qt.LinkAction)
        else:
            super().dragEnterEvent(e)

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls():
            path = Path(e.mimeData().urls()[0].toLocalFile())
            if check_file_type(path, "image"):
                e.setDropAction(QtCore.Qt.LinkAction)
                e.accept()
        else:
            super().dragMoveEvent(e)

    def dropEvent(self, e):
        if e.mimeData().hasUrls():
            e.setDropAction(QtCore.Qt.LinkAction)
            path = Path(e.mimeData().urls()[0].toLocalFile())
            if check_file_type(path, "image"):
                e.accept()
                self.read_img(path)
        else:
            super().dropEvent(e)

    def gui_save(self, settings):
        self.dock.gui_save(settings)
        settings.setValue("Window/geometry", self.saveGeometry())
        settings.setValue("Window/state", self.saveState())

    def gui_restore(self, settings):
        geometry = settings.value("Window/geometry")
        if geometry:
            self.restoreGeometry(geometry)
        state = settings.value("Window/state")
        if state:
            self.restoreState(state)
        self.dock.gui_restore(settings)

    def closeEvent(self, event):
        """save before closing"""
        settings = QtCore.QSettings(str(self.settings_file), QtCore.QSettings.IniFormat)
        self.gui_save(settings)
        event.accept()

    def error_dialog(self, error):
        QtWidgets.QMessageBox.critical(self, "Error", error)

    def save_as_button_clicked(self):
        if self.img_path:
            save_url, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, "Save As", str(self.img_path)
            )
            if save_url:
                cv.imwrite(save_url, self.process_img(self.original_img))
                self.ask_load_saved(Path(save_url))

    def save_button_clicked(self):
        if self.img_path:
            reply = QtWidgets.QMessageBox.warning(
                self,
                "Confirm Save",
                f"{self.img_path.name} already exists.\n" f"Do you want to replace it?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            )
            if reply == QtWidgets.QMessageBox.Yes:
                cv.imwrite(str(self.img_path), self.process_img(self.original_img))
                self.ask_load_saved(Path(self.img_path))

    def ask_load_saved(self, save_path):
        if self.img_path:
            reply = QtWidgets.QMessageBox.warning(
                self,
                "Load Saved",
                f"Do you want to load the saved file?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            )
            if reply == QtWidgets.QMessageBox.Yes:
                self.read_img(save_path)


def main():
    app = QtWidgets.QApplication([])
    win = ProcessWidget()
    win.show()

    app.exec()


if __name__ == "__main__":
    main()
