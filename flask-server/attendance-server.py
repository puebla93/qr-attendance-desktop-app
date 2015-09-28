import sqlite3
from flask import Flask, request, g, redirect, render_template, jsonify, json
from contextlib import closing

# configuration
DATABASE = 'flask_project.db'
DEBUG = True

# initialize application
app = Flask(__name__)
app.config.from_object(__name__)

def connect_db():
	return sqlite3.connect(app.config['DATABASE'])

@app.before_request
def before_request():
    g.db = connect_db()

@app.route('/', methods = ['POST', 'GET'])
def index():
	if request.method == 'POST':

		# ---------------------------------------------------------------
		# | una forma para no permitir subir dos veces el mismo archivo |
		# ---------------------------------------------------------------

		cur = g.db.execute('select * from asist where datetime = ? and teacher = ? and signature = ?', [request.form['datetime'], request.form['teacher'], request.form['signature']])

		for row in cur.fetchall():
			return redirect('/')

		# ---------------------------------------------------------------

		g.db.execute('insert into asist (datetime, teacher, signature, list) values (?, ?, ?, ?)', [request.form['datetime'], request.form['teacher'], request.form['signature'], request.form['list'] ])
		g.db.commit()
		return redirect('/')
		
	elif request.method == 'GET':
		if 'datetime' in request.args and 'teacher' in request.args and 'signature' in request.args: 
			cur = g.db.execute('select list from asist where datetime = ? and teacher = ? and signature = ?', [request.args.get('datetime',''), request.args.get('teacher', ''), request.args.get('signature', '')])
			result = []
			for row in cur.fetchall():
				result.append(row)
			print str(result[0][0])
			try:
				r = json.loads(str(result[0][0]))
			except Exception, e:
				print e
				return 'No es Json'
			return jsonify(r)	
		return 'Hola'

@app.route('/json')
def jsontest():
	return jsonify("'a':5, 'b': 6")

@app.route('/pruebas')
def pruebas():
	return render_template('prueba.html')

if __name__ == '__main__':
    app.run()