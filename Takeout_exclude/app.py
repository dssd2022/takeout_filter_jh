from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from werkzeug.utils import secure_filename
import pandas as pd
import json
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = './static/data'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'json'}

class UploadFileForm(FlaskForm):
    file = FileField('File')
    submit = SubmitField('Upload File')

@app.route('/', methods=['GET', 'POST'])
def intro():
    form = UploadFileForm()
    if form.validate_on_submit():
        file = form.file.data
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            session['filename'] = filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            return redirect(url_for('index'))
    return render_template('intro.html', form=form)

@app.route('/filter', methods=['GET'])
def index():
    if 'filename' not in session:
        return redirect(url_for('intro'))
    filename = session['filename']
    json_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    data_frame = pd.read_json(json_file_path)
    return render_template('filter.html', data=data_frame)

@app.route('/delete', methods=['POST'])
def delete():
    if 'filename' not in session:
        return redirect(url_for('intro'))
    session['rows_to_delete'] = request.form.getlist('row_id')
    return redirect(url_for('delete_confirmation'))

@app.route('/delete/confirm', methods=['POST'])
def delete_confirm():
    if 'filename' not in session or 'rows_to_delete' not in session:
        return redirect(url_for('intro'))
    filename = session['filename']
    rows_to_delete = session.pop('rows_to_delete', None)
    json_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if rows_to_delete:
        with open(json_file_path, 'r') as file:
            data = json.load(file)
        data = [row for idx, row in enumerate(data) if str(idx) not in rows_to_delete]
        timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        new_filename = f"{filename.rsplit('.', 1)[0]}_{timestamp}.json"
        new_file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
        with open(new_file_path, 'w') as new_file:
            json.dump(data, new_file, indent=4)
        return redirect(url_for('download_file', filename=new_filename))
    return redirect(url_for('index'))

@app.route('/delete/cancel', methods=['POST'])
def delete_cancel():
    session.pop('rows_to_delete', None)
    return redirect(url_for('index'))

@app.route('/delete/confirmation', methods=['GET'])
def delete_confirmation():
    return render_template('delete_confirmation.html', num_deleted=len(session.get('rows_to_delete', [])))

@app.route('/downloads/<filename>')
def download_file(filename):
    directory = app.config['UPLOAD_FOLDER']
    return send_from_directory(directory, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
