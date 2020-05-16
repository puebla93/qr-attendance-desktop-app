import sys

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import sqlite3
import cv2
import zbar
import datetime
import socket
import json
import requests
from requests.auth import HTTPBasicAuth
# from http.client import HTTPSConnection

from attendance import QRCode, QRScanner, valid_qrcode, get_student_info
import beep

error_message = None
# message_box = None
spin_box = None
scan_button = None
stop_button= None
subject_lineEdit = None
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
asist = []

def main():
    app = QApplication(sys.argv)

    global db
    db = sqlite3.connect('attendance.db')
    db.execute('''CREATE TABLE IF NOT EXISTS attendance
             (id integer, date timestamp, subject text, classtype text, name text, uploaded boolean, details text)''')

    global camera_timer
    camera_timer = QTimer()

    widget = QWidget()
    widget.setWindowTitle("Attendance")
    widget_izq = QWidget()
    widget_der = QWidget()

    horizontal_layout = QHBoxLayout()
    vertical_layout_izq = QVBoxLayout()
    vertical_layout_der = QVBoxLayout()

    widget.setLayout(horizontal_layout)
    widget_izq.setLayout(vertical_layout_izq)
    widget_der.setLayout(vertical_layout_der)

    global error_message
    error_message = QErrorMessage()
    error_message.setWindowTitle("Error Message")
    # global message_box
    # message_box = QMessageBox()
    # message_box.setWindowTitle("Error Message")

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
    pending_uploaded_label = QLabel("Missing " + str(pending_uploaded()) + " student(s) to upload")

    global camera_image
    global subject_lineEdit
    global classtype_lineEdit
    global details_textEdit
    camera_image = QLabel()
    pix_map = QPixmap("Image-Black.png")
    camera_image.setPixmap(pix_map)
    subject_label = QLabel("Subject")
    subject_lineEdit = QLineEdit()
    classtype_label = QLabel("Classtype")
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
    vertical_layout_izq.addWidget(subject_label)
    vertical_layout_izq.addWidget(subject_lineEdit)
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

def upload():
    # user_name = userName_lineEdit.text()
    user_name = 'h.quintero@lab.matcom.uh.cu'
    # password = password_lineEdit.text()
    password = '12345678'

    # HOST = 'localhost'
    # PORT = 80

    url_login = '10.6.122.231:3000/users/sign_in'

    c = HTTPSConnection("10.6.122.231:3000")

    a = requests.get(url_login, auth=HTTPBasicAuth(user_name, password))

    print(a)

    # my_socked = socket.socket()
    # # my_socked.connect((HOST, PORT))

    # # db.execute("UPDATE attendance SET uploaded = 'False'")
    # cur = db.execute("SELECT * FROM attendance WHERE uploaded = 'False'")
    # for row in cur.fetchall():
    #     # print(row)
    #     # my_socked.send()
    #     db.execute("UPDATE attendance SET uploaded = 'True' WHERE id = ? AND date = ?",[row[0], row[1]])
    #     pass

    # # db.commit()
    # global pending_uploaded_label
    # pending_uploaded_label.setText("Missing " + str(pending_uploaded()) + " student(s) to upload")
    # my_socked.close()

def procces_frame():
    image = None
    global capture
    if capture is None:
        capture = cv2.VideoCapture(spin_box.value())
        _, image = capture.read()
        if image is None:
            cancel_scan()
            error_message.showMessage("Invalid camera index.")
            error_message.show()
            # message_box.setText("Invalid camera index.")
            # message_box.show()
            return
        h, w, c = image.shape
        global  scanner
        scanner = QRScanner(w, h)
    if image is None:
        _, image = capture.read()

    #Poner en un metodo showImage(image)
    h, w, c = image.shape
    cv2.cvtColor(image, cv2.COLOR_BGR2RGB, image)
    qimage = QImage(image, w, h, c * w, QImage.Format_RGB888)
    pix_map = QPixmap.fromImage(qimage)
    camera_image.setPixmap(pix_map)

    gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    result = scanner.get_qrcodes(gray_image)

    if len(result) == 0:
        return

    for qr in result:
        if not valid_qrcode(qr.data):
            continue
        student = get_student_info(qr.data)

        scanned = False
        #COMPROBAR SI EL ESTUDIANTE YA HA SIDO INSERTADO EN LA BASE DE DATOS
        for s in asist:
            if s == student["ID"]: scanned = True

        if not scanned:
            asist.append(student["ID"])
            date = datetime.datetime.now()
            subject = subject_lineEdit.text()
            classtype = classtype_lineEdit.text()
            details = details_textEdit.toPlainText()
            db.execute('''INSERT INTO attendance VALUES (?, ?, ?, ?, ?, 'False', ?)''', 
                        [student["ID"], date, subject, classtype, student["Name"], details])
            # Save (commit) the changes
            db.commit()
            beep.beep()

def start_scan():
    stop_button.setEnabled(True)
    scan_button.setEnabled(False)
    camera_timer.start(50)

def cancel_scan():
    stop_button.setEnabled(False)
    scan_button.setEnabled(True)
    camera_timer.stop()
    global capture
    capture.release()
    capture = None
    pix_map = QPixmap("Image-Black.png")
    camera_image.setPixmap(pix_map)
    global pending_uploaded_label
    pending_uploaded_label.setText("Missing " + str(pending_uploaded()) + " student(s) to upload")

def pending_uploaded():
    cur = db.execute("SELECT COUNT(*) FROM attendance WHERE uploaded = 'False'")
    count = cur.fetchone()
    return count[0]

if __name__ == '__main__':
    main()