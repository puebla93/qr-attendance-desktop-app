import sys

from PyQt5.QtWidgets import *

import sqlite3
import attendance as att
from PyQt5.QtCore import QThread
from threading import Thread

class RenderThread(QThread):

	def __init__(self):
		QThread.__init__(self)
		pass

	def run(self):
		att.main()

def Upload():
	user_name = userName_lineEdit.text()
	password = password_lineEdit.text()

	db = sqlite3.connect('attendance.db')
	cur = db.execute("select * from attendance where uploaded = 'False'")
	for line in cur.fetchall():
		print(line)

	db.close()

app = QApplication(sys.argv)

thread = RenderThread()

w = QWidget()
l = QVBoxLayout()
w.setLayout(l)

scan_button = QPushButton("Scan")
upload_button = QPushButton("Upload")
stop_button = QPushButton("Stop")
userName_label = QLabel("User Name")
userName_lineEdit = QLineEdit()
password_label = QLabel("Password")
password_lineEdit = QLineEdit()
password_lineEdit.setEchoMode(2)

l.addWidget(scan_button)
l.addStretch()
l.addWidget(stop_button)
l.addStretch()
l.addWidget(userName_label)
l.addStretch()
l.addWidget(userName_lineEdit)
l.addStretch()
l.addWidget(password_label)
l.addStretch()
l.addWidget(password_lineEdit)
l.addStretch()
l.addWidget(upload_button)

scan_button.clicked.connect(thread.run)
# stop_button.clicked.connect(thread.quit)
# thread.finished.connect(thread.wait)
upload_button.clicked.connect(Upload)

w.show()

app.exec_()