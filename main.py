from flask import Flask, request, send_file, jsonify, render_template
import yt_dlp
import os
import uuid
from pathlib import Path
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TYER, APIC
import requests
import logging

app = Flask(__name__, template_folder='templates', static_folder='static')

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Global dictionary to store progress status
progress_status = {}

def add_metadata(filename, info, file_format):
    """Adds ID3 metadata and thumbnail to the MP3 file."""
    if file_format != 'mp3':
        return
    try:
        audio = MP3(filename, ID3=ID3)
        if audio.tags is None:
            audio.add_tags()

        audio.tags.add(TIT2(encoding=3, text=info.get('title', 'Unknown Title')))
        audio.tags.add(TPE1(encoding=3, text=info.get('uploader', 'Unknown Uploader')))
        audio.tags.add(TALB(encoding=3, text=info.get('album', 'Unknown Album')))
        upload_date = info.get('upload_date')
        if upload_date and len(upload_date) >= 4:
            audio.tags.add(TYER(encoding=3, text=upload_date[:4]))
        else:
            audio.tags.add(TYER(encoding=3, text='Unknown Year'))

        thumbnail_url = info.get('thumbnail')
        if thumbnail_url:
            try:
                response = requests.get(thumbnail_url, timeout=10)
                if response.status_code == 200:
                    audio.tags.add(APIC(
                        encoding=3,
                        mime='image/jpeg',
                        type=3,
                        desc='Cover',
                        data=response.content
                    ))
                else:
                    logging.warning(f"Failed to download thumbnail: HTTP {response.status_code}")
            except requests.exceptions.RequestException as req_e:
                logging.error(f"Error downloading thumbnail: {req_e}")

        audio.save()
        logging.info(f"Metadata added to {filename}")
    except Exception as e:
        logging.error(f"Error adding metadata to {filename}: {e}")

def progress_hook(d):
    """Updates the global progress_status dictionary based on yt-dlp's download progress."""
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '0%').replace('%', '')
        try:
            percent = float(percent)
        except ValueError:
            percent = 0
        progress_status['progress'] = {
            'message': f"Downloading: {d.get('_percent_str', '0%')} (Speed: {d.get('_speed_str', 'Unknown')}, ETA: {d.get('_eta_str', 'Unknown')})",
            'percent': percent
        }
    elif d['status'] == 'finished':
        progress_status['progress'] = {'message': 'Processing file...', 'percent': 100}
    elif d['status'] == 'error':
        progress_status['progress'] = {'message': f"Error: {d.get('error', 'Unknown error')}", 'percent': 0}
    else:
        progress_status['progress'] = {'message': 'Starting download...', 'percent': 0}

def download_youtube_file(url, output_path, file_format, quality, volume=None):
    """
    Downloads YouTube file (MP3 or MP4) with specified quality and optional volume adjustment.
    Returns the path to the downloaded file and its info, or an error message and None.
    """
    temp_filename_template = os.path.join(output_path, f"{uuid.uuid4()}_%(title)s.%(ext)s").replace('\\', '/')

    ydl_opts = {
        'outtmpl': temp_filename_template,
        'noplaylist': True,
        'progress_hooks': [progress_hook],
        'nocheckcertificate': True,
        'retries': 10,
        'fragment_retries': 10,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        },
        'verbose': True,
    }

    if file_format == 'mp3':
        postprocessor_args = []
        if volume and volume != 'normal':
            try:
                volume_value = float(volume)
                postprocessor_args.append('-filter:a')
                postprocessor_args.append(f'volume={volume_value}dB')
            except ValueError:
                return "Invalid volume value provided", None
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': quality,
            }],
            'postprocessor_args': postprocessor_args if postprocessor_args else None
        })
    else:  # mp4
        ydl_opts.update({
            'format': f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'merge_output_format': 'mp4',
        })

    downloaded_file_path = None
    info = None

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename_base = ydl.prepare_filename(info)
            ext = 'mp3' if file_format == 'mp3' else 'mp4'
            downloaded_file_path = os.path.splitext(filename_base)[0] + f'.{ext}'
            logging.debug(f"Expected file path: {downloaded_file_path}")

            if downloaded_file_path and os.path.exists(downloaded_file_path) and os.path.getsize(downloaded_file_path) > 0:
                if file_format == 'mp3':
                    add_metadata(downloaded_file_path, info, file_format)
                return downloaded_file_path, info
            else:
                error_message = f"Downloaded file is empty or not found: {downloaded_file_path}"
                logging.error(error_message)
                return error_message, None
    except yt_dlp.utils.DownloadError as e:
        error_message = f"Download Error: {e}"
        logging.error(error_message)
        return error_message, None
    except Exception as e:
        error_message = f"An unexpected error occurred during download: {e}"
        logging.error(error_message)
        return error_message, None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    url = data.get('url')
    file_format = data.get('format', 'mp3')
    quality = data.get('quality', '320' if file_format == 'mp3' else '720')
    volume = data.get('volume', 'normal')

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    if file_format == 'mp3' and volume != 'normal':
        try:
            volume = float(volume)
            if volume > 0 or volume < -60:
                return jsonify({'error': 'Volume must be between -60 dB and 0 dB'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid custom volume value'}), 400

    output_path = 'downloads'
    os.makedirs(output_path, exist_ok=True)

    progress_status['progress'] = {'message': 'Starting download...', 'percent': 0}

    filename, info = download_youtube_file(url, output_path, file_format, quality, volume)

    if info and filename and os.path.exists(filename) and os.path.getsize(filename) > 0:
        download_filename = info.get('title', 'file') + f'.{file_format}'
        return send_file(filename, as_attachment=True, download_name=download_filename)
    else:
        if filename and os.path.exists(filename):
            try:
                os.remove(filename)
                logging.info(f"Cleaned up empty or failed file: {filename}")
            except OSError as e:
                logging.error(f"Error cleaning up file {filename}: {e}")
        return jsonify({'error': filename or 'Download failed or file is empty. Please try again.'}), 400

@app.route('/progress')
def get_progress():
    return jsonify(progress_status)

if __name__ == '__main__':
    app.run(debug=True)