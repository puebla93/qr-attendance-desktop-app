import sys

import cv2
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from attendance import Attendance

def main():
    app = QApplication(sys.argv)
    window = MainWindow()

    window.show()
    sys.exit(app.exec())

class MainWindow(QWidget):
    """
    """

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.capture = None
        self.scanner = None
        self.attendance_so_far = []
        self.class_details = {}

        self.db = Attendance.get_data_base_connection()

        self.setWindowTitle("Attendance")

        self.create_global_widgets()
        self.create_global_layouts()
        self.set_layouts_to_global_widgets()
        self.create_widget_components()
        self.add_widgets_to_layouts()
        self.define_signal_handlers()

    def create_global_widgets(self):
        self.widget_izq = QWidget()
        self.widget_der = QWidget()
        camera_size = QSize(640, 480)
        self.widget_der.setMinimumSize(camera_size)

    def create_global_layouts(self):
        self.horizontal_layout = QHBoxLayout()
        self.vertical_layout_izq = QVBoxLayout()
        self.vertical_layout_der = QVBoxLayout()

    def set_layouts_to_global_widgets(self):
        self.setLayout(self.horizontal_layout)
        self.widget_izq.setLayout(self.vertical_layout_izq)
        self.widget_der.setLayout(self.vertical_layout_der)

    def create_widget_components(self):
        self.camera_timer = QTimer()

        self.error_message = QErrorMessage()

        self.spin_box_label = QLabel("Choose a camera index")
        self.spin_box = QSpinBox()
        self.scan_button = QPushButton("Scan")
        self.upload_button = QPushButton("Upload")
        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)
        self.userName_label = QLabel("User Name")
        self.userName_lineEdit = QLineEdit()
        self.password_label = QLabel("Password")
        self.password_lineEdit = QLineEdit()
        self.password_lineEdit.setEchoMode(2)
        self.pending_uploaded_label = QLabel("Missing " + str(Attendance.pending_attendances_to_upload(self.db)) + " student(s) to upload")

        self.camera_image = QLabel()
        camera_size = self.widget_der.minimumSize()
        self.pix_map = QPixmap(camera_size)
        self.pix_map.fill(Qt.black)
        self.camera_image.setPixmap(self.pix_map)
        self.course_name_label = QLabel("Course Name")
        self.course_name_lineEdit = QLineEdit()
        self.classtype_label = QLabel("Class Type")
        self.classtype_lineEdit = QLineEdit()
        self.details_Label = QLabel("Details")
        self.details_textEdit = QTextEdit()

    def add_widgets_to_layouts(self):
        self.vertical_layout_izq.addWidget(self.spin_box_label)
        self.vertical_layout_izq.addWidget(self.spin_box)
        self.vertical_layout_izq.addStretch()
        self.vertical_layout_izq.addWidget(self.scan_button)
        self.vertical_layout_izq.addStretch()
        self.vertical_layout_izq.addWidget(self.stop_button)
        self.vertical_layout_izq.addStretch()
        self.vertical_layout_izq.addWidget(self.course_name_label)
        self.vertical_layout_izq.addWidget(self.course_name_lineEdit)
        self.vertical_layout_izq.addStretch()
        self.vertical_layout_izq.addWidget(self.classtype_label)
        self.vertical_layout_izq.addWidget(self.classtype_lineEdit)
        self.vertical_layout_izq.addStretch()
        self.vertical_layout_izq.addWidget(self.details_Label)
        self.vertical_layout_izq.addWidget(self.details_textEdit)
        self.vertical_layout_izq.addStretch()
        self.vertical_layout_izq.addWidget(self.userName_label)
        self.vertical_layout_izq.addWidget(self.userName_lineEdit)
        self.vertical_layout_izq.addStretch()
        self.vertical_layout_izq.addWidget(self.password_label)
        self.vertical_layout_izq.addWidget(self.password_lineEdit)
        self.vertical_layout_izq.addStretch()
        self.vertical_layout_izq.addWidget(self.upload_button)
        self.vertical_layout_izq.addWidget(self.pending_uploaded_label)

        self.vertical_layout_der.addWidget(self.camera_image)

        self.horizontal_layout.addWidget(self.widget_izq)
        self.horizontal_layout.addWidget(self.widget_der)

    def define_signal_handlers(self):
        self.scan_button.clicked.connect(self.start_scan)
        self.stop_button.clicked.connect(self.cancel_scan)
        self.upload_button.clicked.connect(self.upload)
        self.camera_timer.timeout.connect(self.procces_frame)

    def showImage(self, image):
        h, w, c = image.shape
        cv2.cvtColor(image, cv2.COLOR_BGR2RGB, image)
        qimage = QImage(image, w, h, c * w, QImage.Format_RGB888)
        self.pix_map.convertFromImage(qimage)
        self.camera_image.setPixmap(self.pix_map)

    def procces_frame(self):
        _, image = self.capture.read()
        if image is None:
            self.cancel_scan()
            self.error_message.setWindowTitle("Invalid camera index")
            self.error_message.showMessage("The camera index you choose is invalid.\nSelect 0 if you dont't have a USB camera connected")
            self.error_message.show()
            return

        self.showImage(image)

        qrs = Attendance.get_qrcodes(image, self.scanner)
        students = Attendance.get_student_from_qrcode(qrs, self.attendance_so_far)

        Attendance.register_attendance(students, self.class_details, self.db)
        self.attendance_so_far.extend([student['ID'] for student in students])

    def start_scan(self):
        self.stop_button.setEnabled(True)
        self.scan_button.setEnabled(False)
        self.camera_timer.start(50)

        self.capture = cv2.VideoCapture(self.spin_box.value())

        self.class_details = {
            'course_name': self.course_name_lineEdit.text(),
            'class_type': self.classtype_lineEdit.text(),
            'details': self.details_textEdit.toPlainText()
        }

    def cancel_scan(self):
        self.stop_button.setEnabled(False)
        self.scan_button.setEnabled(True)
        self.camera_timer.stop()

        self.capture.release()
        self.capture = None
        self.scanner = None
        self.attendance_so_far = []
        self.class_details = {}

        self.pix_map.fill(Qt.black)
        self.camera_image.setPixmap(self.pix_map)

        self.pending_uploaded_label.setText("Missing " + str(Attendance.pending_attendances_to_upload(self.db)) + " student(s) to upload")

    def upload(self):
        # user_name = userName_lineEdit.text()
        user_name = 'jpuebla1993@gmail.com'
        # password = password_lineEdit.text()
        password = '12345678'
        Attendance.authenticate(user_name, password)

        Attendance.upload_pending_attendances(db)

        self.pending_uploaded_label.setText("Missing " + str(Attendance.pending_attendances_to_upload(self.db)) + " student(s) to upload")

if __name__ == '__main__':
    main()
