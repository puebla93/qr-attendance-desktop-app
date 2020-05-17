#!/usr/bin/python
import argparse
import datetime
import os
import socket
import sqlite3
import sys
from http.client import HTTPSConnection

import cv2
import requests
import zbar
from requests.auth import HTTPBasicAuth

import beep
from cvinput import cvwindows


def parse_args():
    parser = argparse.ArgumentParser(description='Attendance control system scanner')
    parser.add_argument('-c', "--camera", dest="camera",type=int, default=0, help='Index of the camera to use. Default 0, usually this is the camera on the laptop display')
    parser.add_argument('-t', "--topic", dest="topic",type=str, default='course_name', help='The name of the course (e.g Programming, Computer Architecture, etc.)')
    parser.add_argument('-ty', "--type", dest="type",type=str, default='class_type', help='The type of the class (e.g. Conference, Practical Lesson, etc.)')
    parser.add_argument('-d', "--details", dest="details",type=str, help='Class details that you want to specify (e.g First conference, Last practical lesson, etc.)')

    # def folder(path):
    #     if os.path.isdir(path):
    #         return os.path.abspath(path)
    #     else:
    #         raise argparse.ArgumentTypeError("The specified path is not a directory")

    # parser.add_argument('-f', '--folder', type=folder, default="./", help='The path of the folder to store the result. Defaults to "./"')
    return parser.parse_args()

def main():
    args = parse_args()

    camera = cvwindows.create("Camera")

    capture = cv2.VideoCapture(args.camera)
    _ , image = capture.read()
    if image is None:
        print ("Invalid camera index. Use -c option to choose a correct camera on your system.")
        sys.exit(1)

    scanner = QRScanner()

    attendance_so_far = []
    class_details = {
        'course_name': args.topic,
        'class_type': args.type,
        'details': args.details
    }
    db = Attendance.get_data_base()

    while cvwindows.event_loop():
        _ , image = capture.read()
        camera.show(image)

        qrs = Attendance.get_qrcodes(image, scanner)
        students = Attendance.get_student_from_qrcode(qrs, attendance_so_far)

        Attendance.insert_attendances_into_data_base(students, class_details, db)
        attendance_so_far.extend([student['ID'] for student in students])
    
    user_name = 'jpuebla1993@gmail.com'
    password = '12345678'
    Attendance.authenticate(user_name, password)
    Attendance.upload_pending_attendances(db)
    
class QRCode(object):
    """
        QRCode class contains the data and location of the QRCode in the image
    """
    def __init__(self, data, location):
        self.data = data
        self.location = list(location)

    def repr(self):
        return str(self.data)

class QRScanner(object):
    """
        Zbar qrcode scanner wrapper class
    """

    ZBAR_QRCODE = 'QR-Code'

    def __init__(self):
        self.scanner = zbar.Scanner()

    def get_qrcodes(self, zbar_img):
        symbols = self.scanner.scan(zbar_img)
        result=[]
        for symbol in symbols:
            if str(symbol.type) != QRScanner.ZBAR_QRCODE:
                continue
            fixed_data = symbol.data.decode("utf8").encode("shift_jis").decode("utf8")
            result.append(QRCode(fixed_data,symbol.position))
        return result

class Attendance:

    @staticmethod
    def get_data_base():
        db = sqlite3.connect('attendance.db')
        db.execute('''CREATE TABLE IF NOT EXISTS attendance
                (id integer, date timestamp, courseName text, classType text, name text, uploaded boolean, details text)''')

        return db

    @staticmethod
    def valid_qrcode(qrcode_data):

        qrcode_data = qrcode_data.split("\n")
        if len(qrcode_data) != 5 : return False

        #N: Nombre
        test = qrcode_data[0].split(":")
        if test[0] != "N" or len(test[1]) == 0: return False

        #A\: Apellidos
        test = qrcode_data[1].split(":")
        if test[0] != "A" or len(test[1]) == 0: return False

        #CI\: 12345678901
        test = qrcode_data[2].split(":")
        if test[0] != "CI" or len(test[1].strip()) != 11: return False

        #FV\: AA0000000
        test = qrcode_data[3].split(":")
        if test[0] != "FV" or len(test[1].strip()) != 9: return False

        return True

    @staticmethod
    def get_student_info(qrcode_data):
        # get qrcode info
        qrcode_data = qrcode_data.split("\n")

        # get student sex
        # if int(qrcode_data[2][-2]) % 2 == 0:
        #     gender = "male"
        # else:
        #     gender = "female"

        return {
                    "ID": qrcode_data[2][-12:].strip(),
                    "Name": qrcode_data[0][2:].strip() + " " + qrcode_data[1][2:].strip(),
                    # "Name": qrcode_data[0][2:].strip(),
                    # "LastName": qrcode_data[1][2:].strip(),
                    # "FV": qrcode_data[3][-9:].strip(),
                    # "Gender": gender,
                }

    @staticmethod
    def get_qrcodes(image, scanner=None):
        if scanner is None:
            scanner = QRScanner()

        gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        qrs = scanner.get_qrcodes(gray_image)

        return qrs

    @staticmethod
    def get_student_from_qrcode(qrs, attendance_so_far):
        students = []
        for qr in qrs:
            if not Attendance.valid_qrcode(qr.data):
                continue

            student = Attendance.get_student_info(qr.data)
            # check if the student has already been inserted in the database
            if not student["ID"] in attendance_so_far:
                students.append(student)
                beep.beep()

        return students

    @staticmethod
    def insert_attendances_into_data_base(students, class_details, db):
        date = datetime.datetime.now()

        for student in students:
            to_insert = [
                student["ID"], 
                date, 
                class_details['course_name'], 
                class_details['class_type'], 
                student["Name"], 
                class_details['details']
            ]
            db.execute('''INSERT INTO attendance VALUES (?, ?, ?, ?, ?, 'False', ?)''', to_insert)
            # Save (commit) the changes
            db.commit()

    @staticmethod
    def pending_uploaded(db):
        cur = db.execute("SELECT COUNT(*) FROM attendance WHERE uploaded = 'False'")
        count = cur.fetchone()
        return count[0]

    @staticmethod
    def authenticate(user_name, password):
        url_login = '10.6.122.231:3000/users/sign_in'

        # auth = requests.get(url_login, auth=HTTPBasicAuth(user_name, password))
        # print(a)
        # return auth

    @staticmethod
    def upload_pending_attendances(db):
        # HOST = 'localhost'
        # PORT = 80

        c = HTTPSConnection("10.6.122.231:3000")

        # my_socked = socket.socket()
        # # my_socked.connect((HOST, PORT))

        # requests.post('http://127.0.0.1:5000', data = {'datetime': date, 'teacher' : 'dvd', 'signature' : 'AC', 'list' : j})

        # db.execute("UPDATE attendance SET uploaded = 'False'")
        cur = db.execute("SELECT * FROM attendance WHERE uploaded = 'False'")
        for row in cur.fetchall():
            print(row)
        #     # my_socked.send()
            db.execute("UPDATE attendance SET uploaded = 'True' WHERE id = ? AND date = ?",[row[0], row[1]])

        db.commit()
        # my_socked.close()

if __name__ == '__main__':
    main()
