import os
import yt_dlp


def download_video_from_url(url: str, output_dir: str, cookies_browser: str = None) -> str:
    """
    Downloads a video from YouTube, TikTok, Instagram, or X (Twitter) using yt-dlp.
    
    Args:
        url: The video URL to download.
        output_dir: Directory to save the downloaded video.
        cookies_browser: Browser name to extract cookies from (e.g. 'chrome', 'firefox', 'edge').
                         Set to None to try without cookies first.
    
    Returns:
        Absolute path to the downloaded .mp4 file.
    
    Raises:
        Exception with a user-friendly message on failure.
    """
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        # Select best pre-merged format or fallback to best single file to avoid ffmpeg
        'format': 'best[ext=mp4]/best[ext=m4v]/best',
        'outtmpl': os.path.join(output_dir, '%(id)s.%(ext)s'),
        'noplaylist': True,
        'quiet': False,
        # Retry settings
        'retries': 3,
        'fragment_retries': 3,
        # Throttle to avoid rate-limiting
        'sleep_interval': 1,
        'max_sleep_interval': 5,
    }

    # If a browser is specified, use its cookies
    if cookies_browser:
        ydl_opts['cookiesfrombrowser'] = (cookies_browser,)

    last_error = None

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            base, _ = os.path.splitext(filename)
            mp4_path = f"{base}.mp4"

            if os.path.exists(mp4_path):
                return mp4_path
            elif os.path.exists(filename):
                return filename
            else:
                raise Exception(f"Download completed but file not found at expected path: {mp4_path}")

    except Exception as e:
        last_error = str(e)

    # Provide a clear, actionable error
    msg = last_error or "Unknown download error"

    if "429" in msg or "Too Many Requests" in msg:
        raise Exception(
            "YouTube is rate-limiting this request (HTTP 429).\n\n"
            "**Fix:** Select your browser in the 'Cookie Source' dropdown and retry. "
            "This lets yt-dlp use your YouTube login cookies to bypass the bot check."
        )
    elif "Sign in to confirm" in msg or "bot" in msg.lower():
        raise Exception(
            "YouTube requires authentication to download this video.\n\n"
            "**Fix:** Select your browser (Chrome, Firefox, or Edge) in the 'Cookie Source' dropdown. "
            "Make sure you are logged into YouTube in that browser, then retry."
        )
    elif "Private video" in msg:
        raise Exception("This video is private and cannot be downloaded.")
    elif "not available" in msg.lower():
        raise Exception("This video is not available in your region or has been removed.")
    else:
        raise Exception(f"Download failed: {msg}")
