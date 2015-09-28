#!/usr/bin/python
from cvinput import cvwindows, Obj
import cv2
import zbar
import beep

import argparse
import datetime
import requests
import json
import sys
import os

def parse_args():
    parser = argparse.ArgumentParser(description='Attendance control system scanner')
    parser.add_argument('-c', "--camera", dest="camera",type=int, default=0, help='Index of the camera to use. Default 0, usually this is the camera on the laptop display')
    parser.add_argument('-t', "--topic", dest="topic",type=str, default='course_name', help='The name of the course. It will be used on the output file.')

    def folder(path):
        if os.path.isdir(path):
            return os.path.abspath(path)
        else:
            raise argparse.ArgumentTypeError("The specified path is not a directory")

    parser.add_argument('-f', '--folder', type=folder, default="./", help='The path of the folder to store the result. Defaults to "./"')
    return parser.parse_args()

def main():
    args = parse_args()


    camera = cvwindows.create("Camera")

    date = str(datetime.date.today())
    asist = { "date": date, "students":[], "course": args.topic}

    capture = cv2.VideoCapture(args.camera)
    _ , image = capture.read()
    if image is None:
        print "Invalid camera index. Use -c option to choose a correct camera on your system."
        sys.exit(1)
    h, w, _ = image.shape
    scanner = QRScanner(w,h)

    while cvwindows.event_loop():
        _ , image = capture.read()
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        camera.show(image)
        result = scanner.get_qrcodes(gray_image)

        if len(result)==0: continue

        for qr in result:
            if not valid_qrcode(qr.data): continue
            student = get_student_info(qr.data)

            scanned = False
            for s in asist["students"]:
                if s["ID"] == student["ID"]: scanned= True

            if not scanned:
                asist["students"].append(student)
                beep.beep()

    file_path = os.path.join(args.folder, "attendance-%s-%s.json"%(date,args.topic))
    archive = open(file_path, "w")
    json.dump(asist, archive, indent=4)

    # requests.post('http://127.0.0.1:5000', data = {'datetime': date, 'teacher' : 'dvd', 'signature' : 'AC', 'list' : j})

# QRCode class contains the data and location of the QRCode in the image
class QRCode(object):
    """QRCode class"""
    def __init__(self, data, location):
        self.data = data
        self.location = list(location)

    def repr(self):
        return str(self.data)

class QRScanner(object):
    """Zbar qrcode scanner wrapper class"""
    def __init__(self, width, height):
        self.scanner = zbar.ImageScanner()
        self.scanner.parse_config('enable')
        self.width = width
        self.height = height

    def get_qrcodes(self, image):
        zbar_img = self.cv2_to_zbar_image(image)
        self.scanner.scan(zbar_img)
        result=[]
        for symbol in zbar_img:
            if str(symbol.type)!=str(zbar.Symbol.QRCODE): continue
            fixed_data = symbol.data.decode("utf8").encode("shift_jis").decode("utf8")
            result.append(QRCode(fixed_data,symbol.location))
        del(zbar_img)
        return result

    def cv2_to_zbar_image(self, cv2_image):
        return zbar.Image(self.width, self.height, 'Y800',cv2_image.tostring())

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

def get_student_info(qrcode_data):
    # sacar la info del qrcode
    qrcode_data = qrcode_data.split("\n") 

    if int(qrcode_data[2][-2]) % 2 == 0:
        gender = "male"
    else:
        gender = "female"

    return {
                "ID": qrcode_data[2][-12:].strip(),
                "Name": qrcode_data[0][2:].strip(),
                "LastName": qrcode_data[1][2:].strip(),
                "FV": qrcode_data[3][-9:].strip(),
                "Gender": gender,
            }

if __name__ == '__main__':
    main() 