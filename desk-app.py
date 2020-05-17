import sys

import cv2
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from attendance import Attendance

error_message = None
spin_box = None
scan_button = None
stop_button= None
course_name_lineEdit = None
classtype_lineEdit = None
details_textEdit = None
userName_lineEdit = None
password_lineEdit = None
pending_uploaded_label = None
camera_image = None
camera_timer = None
capture = None
scanner = None
db = None
attendance_so_far = []
class_details = {}
camera_size = QSize(640, 480)

def main():
    app = QApplication(sys.argv)

    global db
    db = Attendance.get_data_base_connection()

    global camera_timer
    camera_timer = QTimer()

    widget = QWidget()
    widget.setWindowTitle("Attendance")
    widget_izq = QWidget()
    widget_der = QWidget()
    widget_der.setMinimumSize(camera_size)

    horizontal_layout = QHBoxLayout()
    vertical_layout_izq = QVBoxLayout()
    vertical_layout_der = QVBoxLayout()

    widget.setLayout(horizontal_layout)
    widget_izq.setLayout(vertical_layout_izq)
    widget_der.setLayout(vertical_layout_der)

    global error_message
    error_message = QErrorMessage()

    global spin_box
    global scan_button
    global stop_button
    global userName_lineEdit
    global password_lineEdit
    global pending_uploaded_label
    spin_box_label = QLabel("Choose a camera index")
    spin_box = QSpinBox()
    scan_button = QPushButton("Scan")
    upload_button = QPushButton("Upload")
    stop_button = QPushButton("Stop")
    stop_button.setEnabled(False)
    userName_label = QLabel("User Name")
    userName_lineEdit = QLineEdit()
    password_label = QLabel("Password")
    password_lineEdit = QLineEdit()
    password_lineEdit.setEchoMode(2)
    pending_uploaded_label = QLabel("Missing " + str(Attendance.pending_attendances_to_upload(db)) + " student(s) to upload")

    global camera_image
    global course_name_lineEdit
    global classtype_lineEdit
    global details_textEdit
    camera_image = QLabel()
    pix_map = QPixmap("Image-Black.png")
    camera_image.setStyleSheet("background-color: black")
    # camera_image.setPixmap(pix_map)
    course_name_label = QLabel("Course Name")
    course_name_lineEdit = QLineEdit()
    classtype_label = QLabel("Class Type")
    classtype_lineEdit = QLineEdit()
    details_Label = QLabel("Details")
    details_textEdit = QTextEdit()

    vertical_layout_izq.addWidget(spin_box_label)
    vertical_layout_izq.addWidget(spin_box)
    vertical_layout_izq.addStretch()
    vertical_layout_izq.addWidget(scan_button)
    vertical_layout_izq.addStretch()
    vertical_layout_izq.addWidget(stop_button)
    vertical_layout_izq.addStretch()
    vertical_layout_izq.addWidget(course_name_label)
    vertical_layout_izq.addWidget(course_name_lineEdit)
    vertical_layout_izq.addStretch()
    vertical_layout_izq.addWidget(classtype_label)
    vertical_layout_izq.addWidget(classtype_lineEdit)
    vertical_layout_izq.addStretch()
    vertical_layout_izq.addWidget(details_Label)
    vertical_layout_izq.addWidget(details_textEdit)
    vertical_layout_izq.addStretch()
    vertical_layout_izq.addWidget(userName_label)
    vertical_layout_izq.addWidget(userName_lineEdit)
    vertical_layout_izq.addStretch()
    vertical_layout_izq.addWidget(password_label)
    vertical_layout_izq.addWidget(password_lineEdit)
    vertical_layout_izq.addStretch()
    vertical_layout_izq.addWidget(upload_button)
    vertical_layout_izq.addWidget(pending_uploaded_label)

    vertical_layout_der.addWidget(camera_image)

    horizontal_layout.addWidget(widget_izq)
    horizontal_layout.addWidget(widget_der)

    scan_button.clicked.connect(start_scan)
    stop_button.clicked.connect(cancel_scan)
    upload_button.clicked.connect(upload)
    camera_timer.timeout.connect(procces_frame)

    widget.show()

    app.exec_()

def showImage(image):
    h, w, c = image.shape
    cv2.cvtColor(image, cv2.COLOR_BGR2RGB, image)
    qimage = QImage(image, w, h, c * w, QImage.Format_RGB888)
    pix_map = QPixmap.fromImage(qimage)
    camera_image.setPixmap(pix_map)

def procces_frame():
    _, image = capture.read()
    if image is None:
        cancel_scan()
        error_message.setWindowTitle("Invalid camera index")
        error_message.showMessage("The camera index you choose is invalid.\nSelect 0 if you dont't have a USB camera connected")
        error_message.show()
        return

    showImage(image)

    qrs = Attendance.get_qrcodes(image, scanner)
    students = Attendance.get_student_from_qrcode(qrs, attendance_so_far)

    Attendance.register_attendance(students, class_details, db)
    attendance_so_far.extend(students)

def start_scan():
    stop_button.setEnabled(True)
    scan_button.setEnabled(False)
    camera_timer.start(50)

    global capture
    capture = cv2.VideoCapture(spin_box.value())

    global class_details
    class_details = {
        'course_name': course_name_lineEdit.text(),
        'class_type': classtype_lineEdit.text(),
        'details': details_textEdit.toPlainText()
    }

def cancel_scan():
    stop_button.setEnabled(False)
    scan_button.setEnabled(True)
    camera_timer.stop()

    global capture
    capture.release()
    capture = None
    global  scanner
    scanner = None
    global attendance_so_far
    attendance_so_far = []
    global class_details
    class_details = {}

    pix_map = QPixmap("Image-Black.png")
    camera_image.setStyleSheet("background-color: black")
    # camera_image.setPixmap(pix_map)

    global pending_uploaded_label
    pending_uploaded_label.setText("Missing " + str(Attendance.pending_attendances_to_upload(db)) + " student(s) to upload")

def upload():
    # user_name = userName_lineEdit.text()
    user_name = 'jpuebla1993@gmail.com'
    # password = password_lineEdit.text()
    password = '12345678'
    Attendance.authenticate(user_name, password)

    Attendance.upload_pending_attendances(db)

    global pending_uploaded_label
    pending_uploaded_label.setText("Missing " + str(Attendance.pending_attendances_to_upload(db)) + " student(s) to upload")

if __name__ == '__main__':
    main()
