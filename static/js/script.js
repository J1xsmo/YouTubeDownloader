const convertBtn = document.getElementById('convert-btn');
const youtubeUrl = document.getElementById('youtube-url');
const format = document.getElementById('format');
const mp3Quality = document.getElementById('mp3-quality');
const mp4Quality = document.getElementById('mp4-quality');
const mp3Volume = document.getElementById('mp3-volume');
const mp3Bitrate = document.getElementById('mp3-bitrate');
const mp4Resolution = document.getElementById('mp4-resolution');
const volumeSelect = document.getElementById('volume-select');
const customVolume = document.getElementById('custom-volume');
const status = document.getElementById('status');
const statusText = document.getElementById('status-text');
const error = document.getElementById('error');
const progressBar = document.getElementById('progress-bar');

format.addEventListener('change', () => {
    mp3Quality.classList.toggle('hidden', format.value !== 'mp3');
    mp4Quality.classList.toggle('hidden', format.value !== 'mp4');
    mp3Volume.classList.toggle('hidden', format.value !== 'mp3');
});

volumeSelect.addEventListener('change', () => {
    customVolume.classList.toggle('hidden', volumeSelect.value !== 'custom');
});

convertBtn.addEventListener('click', async () => {
    const url = youtubeUrl.value.trim();
    if (!url) {
        error.textContent = 'Please enter a valid YouTube URL';
        error.classList.remove('hidden');
        return;
    }

    let volume = volumeSelect.value;
    if (volume === 'custom') {
        const customValue = customVolume.value.trim();
        if (!customValue || isNaN(customValue)) {
            error.textContent = 'Please enter a valid custom volume in dB';
            error.classList.remove('hidden');
            return;
        }
        volume = customValue;
    }

    status.classList.remove('hidden');
    convertBtn.disabled = true;
    error.classList.add('hidden');
    statusText.textContent = 'Starting...';
    progressBar.style.width = '0%';

    const updateProgress = async () => {
        try {
            const response = await fetch('/progress');
            const data = await response.json();
            if (data.progress) {
                statusText.textContent = data.progress.message;
                progressBar.style.width = `${data.progress.percent || 0}%`;
                if (data.progress.message.includes('Downloading') || data.progress.message === 'Processing file...') {
                    setTimeout(updateProgress, 1000);
                }
            }
        } catch (err) {
            console.error('Progress update failed:', err);
        }
    };

    try {
        updateProgress();
        const quality = format.value === 'mp3' ? mp3Bitrate.value : mp4Resolution.value;
        const response = await fetch('/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, format: format.value, quality, volume })
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || 'Failed to process file');
        }

        const blob = await response.blob();
        if (blob.size === 0) {
            throw new Error('Downloaded file is empty. Please try again or check the URL.');
        }

        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = format.value === 'mp3' ? 'audio.mp3' : 'video.mp4';
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="(.+)"/);
            if (filenameMatch && filenameMatch[1]) {
                filename = filenameMatch[1];
            }
        }

        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(downloadUrl);

        statusText.textContent = 'Download complete!';
        progressBar.style.width = '100%';
    } catch (err) {
        error.textContent = err.message;
        error.classList.remove('hidden');
        statusText.textContent = 'Error occurred.';
        progressBar.style.width = '0%';
    } finally {
        setTimeout(() => {
            status.classList.add('hidden');
            convertBtn.disabled = false;
        }, 2000);
    }
});