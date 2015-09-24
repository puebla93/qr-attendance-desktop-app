#- all the imports ------------------------------------------------------------#
import beep
import cv2
import datetime
import zbar
import argparse
import json
import requests
from cvinput import cvwindows, Obj

#------------------------------------------------------------------------------#

class QRCode(object):
    """QRCode class"""
    def __init__(self, data, location):
        self.data = data
        self.location = list(location)

    def repr(self):
        return str(self.data)

#------------------------------------------------------------------------------# 

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

#------------------------------------------------------------------------------# 

def printDictionary(dictionary):
    archive = open('Asistencia (' + dictionary["Date"] +').json', 'w')
    archive.write("Date:\t" + dictionary["Date"])
    archive.write("\n\nStudents:")
    
    i = 1
    for item in dictionary["Students"]:
        archive.write("\n\t" + str(i) + "- " + str(item.data))
        i = i + 1
    archive.close

#------------------------------------------------------------------------------# 

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

#------------------------------------------------------------------------------# 

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

#------------------------------------------------------------------------------#
def main(arg):
    
    camera = cvwindows.create("Camera")

    date = str(datetime.date.today())
    asist = { "date": date, "students":[] }

    capture = cv2.VideoCapture(1)

    while cvwindows.event_loop():
        _ , image = capture.read()
        h, w, _ = image.shape
        scanner = QRScanner(w,h)

        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        camera.show(image)

        result = scanner.get_qrcodes(gray_image)

        if len(result)==0: continue;

        for qr in result:
            if  not valid_qrcode(qr.data): continue
            student = get_student_info(qr.data)
            scanned = False
            for s in asist["students"]:
                if s["ID"] == student["ID"]: 
                    scanned= True
            if not scanned:
                beep.beep()
                asist["students"].append(student)

    archive = open("Asistencia_("+ date + ").json", "w")
    json.dump(asist, archive)

    j = json.dumps(asist)
    print j
    print type(j)
    requests.post('http://127.0.0.1:5000', data = {'datetime': date, 'teacher' : 'dvd', 'signature' : 'AC', 'list' : j})


if __name__ == '__main__':
    main() 