from flask import Flask, request, render_template, send_file, jsonify
from PIL import Image
from werkzeug.utils import secure_filename
from io import BytesIO
import os
import uuid

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16 MB


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file selected'})

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'})

    if file and allowed_file(file.filename):
        original_filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())
        filename = f"{unique_id}_{original_filename}"

        # Save in memory buffer
        file_bytes = file.read()
        if len(file_bytes) > MAX_FILE_SIZE:
            return jsonify({'error': 'File too large (max 16 MB)'})

        return jsonify({
            'success': True,
            'filename': filename,
            'original_filename': original_filename,
            'original_size': round(len(file_bytes) / 1024, 2)  # in KB
        })
    else:
        return jsonify({'error': 'Invalid file type. Please upload an image file.'})


@app.route('/compress', methods=['POST'])
def compress_file():
    file = request.files.get('file')
    compression_level = int(request.form.get('compression', 85))

    if not file:
        return jsonify({'error': 'No file uploaded'})

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'})

    try:
        img = Image.open(file)

        # Convert transparent formats to RGB
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')

        buf = BytesIO()
        img.save(buf, "JPEG", quality=compression_level, optimize=True)
        buf.seek(0)

        compressed_size = round(len(buf.getvalue()) / 1024, 2)  # in KB

        return send_file(
            buf,
            mimetype="image/jpeg",
            as_attachment=True,
            download_name=f"compressed_{secure_filename(file.filename)}"
        )

    except Exception as e:
        return jsonify({'error': f'Error compressing image: {str(e)}'})


@app.route('/result')
def result():
    return render_template('result.html')


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
