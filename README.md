# YouTube Downloader
A Flask-based web application for downloading YouTube videos and audio files with customizable quality and volume settings.
## Features

- Download YouTube videos as MP4 or audio as MP3.
- Choose from various quality options (e.g., 320kbps for MP3, 1080p for MP4).
- Adjust audio volume with preset or custom dB values.
- Real-time progress updates with a progress bar.
- Metadata embedding for MP3 files (title, uploader, album, year, and thumbnail).
- Responsive and modern UI with Tailwind CSS.

## Prerequisites

1. Python 3.8+
2. FFmpeg installed on your system (required for audio extraction)

## Installation

Clone the repository:
```bash
git clone https://github.com/J1xsmo/YouTubeDownloader
cd youtube-downloader
```

Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Install FFmpeg:

- On Ubuntu: sudo apt-get install ffmpeg
- On macOS: brew install ffmpeg
- On Windows: Download from FFmpeg website and add to PATH.

## Usage

1. Run the Flask application:
```bash
python main.py
```
2. Open your browser and navigate to http://127.0.0.1:5000 
3. Enter a YouTube URL, select the format (MP3/MP4), quality, and optional volume settings. 
4. Click "Convert & Download" to start the download process. 

## Project Structure
```
youtube-downloader/
├── main.py              
├── requirements.txt   
├── .gitignore          
├── README.md          
├── templates/
│   └── index.html     
├── static/
│   ├── css/
│   │   └── styles.css  
│   └── js/
│       └── script.js   
└── downloads/          # Temporary storage for downloaded files
```
