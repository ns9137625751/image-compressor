from flask import Flask, request, render_template, send_file, flash, redirect, url_for, jsonify
from PIL import Image
import os
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

UPLOAD_FOLDER = 'static/uploads'
COMPRESSED_FOLDER = 'static/compressed'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['COMPRESSED_FOLDER'] = COMPRESSED_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def compress_image(input_path, output_path, quality):
    with Image.open(input_path) as img:
        # Convert RGBA to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        img.save(output_path, 'JPEG', quality=quality, optimize=True)

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
        # Generate unique filename
        unique_id = str(uuid.uuid4())
        original_filename = secure_filename(file.filename)
        filename = f"{unique_id}_{original_filename}"
        
        # Save original file
        original_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(original_path)
        
        # Get original file size
        original_size = os.path.getsize(original_path)
        
        return jsonify({
            'success': True,
            'original_filename': original_filename,
            'filename': filename,
            'original_size': round(original_size / 1024, 2),
            'original_path': f"uploads/{filename}"
        })
    else:
        return jsonify({'error': 'Invalid file type. Please upload an image file.'})

@app.route('/compress', methods=['POST'])
def compress_file():
    data = request.get_json()
    filename = data.get('filename')
    compression_level = int(data.get('compression', 85))
    
    if not filename:
        return jsonify({'error': 'No filename provided'})
    
    original_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if not os.path.exists(original_path):
        return jsonify({'error': 'Original file not found'})
    
    # Compress image
    compressed_filename = f"compressed_{filename.rsplit('.', 1)[0]}.jpg"
    compressed_path = os.path.join(app.config['COMPRESSED_FOLDER'], compressed_filename)
    
    try:
        compress_image(original_path, compressed_path, compression_level)
        
        # Get file sizes
        original_size = os.path.getsize(original_path)
        compressed_size = os.path.getsize(compressed_path)
        reduction_percent = ((original_size - compressed_size) / original_size) * 100
        
        return jsonify({
            'success': True,
            'compressed_path': f"compressed/{compressed_filename}",
            'compressed_size': round(compressed_size / 1024, 2),
            'reduction_percent': round(reduction_percent, 2),
            'compressed_filename': compressed_filename
        })
    except Exception as e:
        return jsonify({'error': f'Error compressing image: {str(e)}'})

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['COMPRESSED_FOLDER'], filename), as_attachment=True)

@app.route('/result')
def result():
    return render_template('result.html')

@app.route('/sitemap.xml')
def sitemap():
    return send_file('static/sitemap.xml', mimetype='application/xml')

@app.route('/robots.txt')
def robots():
    return send_file('static/robots.txt', mimetype='text/plain')

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(COMPRESSED_FOLDER, exist_ok=True)
    app.run(debug=True)