import os
import subprocess
import logging
import django_rq
from pathlib import Path
from rq import Retry
from django.conf import settings
from .models import Video, VideoStreamVariant

logger = logging.getLogger(__name__)


# provisorisch

# def convert_480p(source):
#     target = source + '_480p'
#     cmd = 'ffmpeg -i "{}" -s hd480 -c:v libx264 -crf 23 -c:a aac -strict -2 "{}"'.format(source, target)
#     subprocess.run(cmd)


def queue_video_processing(video_id):
    """
    Enqueue video processing job in Redis Queue
    Call this from Views/Signals to start background processing
    """
    try:
        queue = django_rq.get_queue('default')
        job = queue.enqueue(
            process_video_to_hls,
            video_id,
            job_timeout=3600,
            retry=Retry(max=3, interval=[60, 300, 900]),
            result_ttl=24 * 3600,
            failure_ttl=7 * 24 * 3600,
            description=f"HLS processing for video {video_id}",
        )
        logger.info("Video %s queued for processing. Job ID: %s",
                    video_id, job.id)
        return job.id
    except Exception as e:
        logger.error("Failed to queue video %s for processing: %s",
                     video_id, str(e))
        raise


def process_video_to_hls(video_id):
    """
    Main background job: Convert video to HLS with multiple resolutions
    Orchestrates the entire video processing pipeline
    """
    video = None
    try:
        video = Video.objects.get(id=video_id)
        logger.info("Starting HLS processing for Video %s: %s",
                    video_id, video.title)

        # Setup video processing
        input_path, output_dir = setup_video_processing(video)

        # Process all HLS resolutions
        process_all_resolutions(video, input_path, output_dir)

        # Finalize with metadata and thumbnail
        finalize_video_processing(video, input_path)

        logger.info("Video %s processing completed successfully", video_id)

    except Video.DoesNotExist:
        error_msg = f"Video with ID {video_id} not found"
        logger.error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Error processing video {video_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        if video:
            video.processing_status = 'failed'
            video.processing_error = str(e)
            video.save()
        raise e


def setup_video_processing(video):
    """
    Setup video for processing: status, directories, paths
    Returns: (input_path, output_dir)
    """
    video.processing_status = 'processing'
    video.processing_progress = 0
    video.save()

    # Setup file paths
    input_path = video.video_file.path
    output_dir = Path(settings.MEDIA_ROOT) / "hls" / str(video.id)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.debug("Video processing setup completed for video %s", video.id)
    return input_path, output_dir


def process_all_resolutions(video, input_path, output_dir):
    """
    Process video into all HLS resolutions (480p, 360p, 720p, 1080p)
    Updates progress from 0% to 80%
    """
    resolutions = [
        {'name': '360p', 'height': 360, 'bitrate': '800k'},
        {'name': '480p', 'height': 480, 'bitrate': '1200k'},
        {'name': '720p', 'height': 720, 'bitrate': '2500k'},
        {'name': '1080p', 'height': 1080, 'bitrate': '5000k'},
    ]

    logger.info("Processing %d resolutions for video %s",
                len(resolutions), video.id)

    for i, res in enumerate(resolutions):
        logger.debug("Processing resolution %s for video %s",
                     res['name'], video.id)
        process_resolution(video, input_path, output_dir, res)

        progress = int((i + 1) / len(resolutions) * 80)
        video.processing_progress = progress
        video.save()
        logger.debug("Video %s progress: %d%%", video.id, progress)

    logger.debug("All resolutions processed for video %s", video.id)


def finalize_video_processing(video, input_path):
    """
    Final steps: extract metadata, generate thumbnail, mark as completed
    Updates progress from 80% to 100%
    """
    # Extract metadata (85% progress)
    logger.debug("Extracting metadata for video %s", video.id)
    video.processing_progress = 85
    video.save()
    extract_video_metadata(video, input_path)

    # Generate thumbnail (95% progress)
    logger.debug("Generating thumbnail for video %s", video.id)
    video.processing_progress = 95
    video.save()
    generate_thumbnail(video, input_path)

    # Complete processing (100%)
    video.processing_status = 'completed'
    video.processing_progress = 100
    video.save()
    logger.debug("Video processing finalized for video %s", video.id)


def process_resolution(video, input_path, output_dir, resolution):
    """
    Convert video to specific resolution with HLS segmentation
    """
    res_name = resolution['name']
    height = resolution['height']
    bitrate = resolution['bitrate']

    # Output directory for this resolution
    res_output_dir = output_dir / res_name
    res_output_dir.mkdir(parents=True, exist_ok=True)

    # Output files
    playlist_path = res_output_dir / "index.m3u8"
    segment_pattern = res_output_dir / "segment_%05d.ts"

    # FFmpeg command for HLS conversion
    ffmpeg_cmd = [
        'ffmpeg',
        '-i', input_path,
        '-vf', f'scale=-2:{height}',
        '-c:v', 'libx264',
        '-b:v', bitrate,
        '-c:a', 'aac',
        '-b:a', '128k',
        '-hls_time', '10',
        '-hls_list_size', '0',
        '-hls_segment_filename', str(segment_pattern),
        '-f', 'hls',
        str(playlist_path),
    ]

    try:
        # Run FFmpeg
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)
        logger.debug(
            "FFmpeg conversion to %s completed successfully", res_name)

        VideoStreamVariant.objects.update_or_create(
            video=video,
            resolution=res_name,
            defaults={'manifest_path': str(playlist_path)},
        )

    except subprocess.CalledProcessError as e:
        logger.error("FFmpeg failed for resolution %s: %s", res_name, e.stderr)
        raise


def extract_video_metadata(video, input_path):
    """
    Extract video duration and file size using FFprobe
    """
    # Get video duration with ffprobe
    try:
        duration_cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-show_entries', 'format=duration',
            '-of', 'csv=p=0',
            input_path
        ]

        result = subprocess.run(
            duration_cmd, capture_output=True, text=True, check=True)
        duration = float(result.stdout.strip())

        # Get file size
        file_size_bytes = os.path.getsize(input_path)
        file_size_mb = file_size_bytes // (1024 * 1024)

        # Update video model
        video.duration_seconds = int(duration)
        video.file_size_mb = file_size_mb
        video.save()

        logger.info("Metadata extracted for video %s: %ds, %dMB",
                    video.id, int(duration), file_size_mb)
    except subprocess.CalledProcessError as e:
        logger.error("FFprobe failed for video %s: %s", video.id, e.stderr)
        raise
    except Exception as e:
        logger.error("Failed to extract metadata for video %s: %s",
                     video.id, str(e))
        raise


def generate_thumbnail(video, input_path):
    """
    Generate thumbnail from video at 5-second mark
    """
    try:
        thumbnail_dir = Path(settings.MEDIA_ROOT) / "thumbnails"
        thumbnail_dir.mkdir(parents=True, exist_ok=True)

        thumbnail_filename = f"{video.id}_thumb.jpg"
        thumbnail_path = thumbnail_dir / thumbnail_filename

        ffmpeg_cmd = [
            'ffmpeg',
            '-y',
            '-i', input_path,
            '-ss', '00:00:03',
            '-vframes', '1',
            '-q:v', '2',
            str(thumbnail_path),
        ]
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)

        video.thumbnail_url = f"thumbnails/{thumbnail_filename}"

        video.save()
        logger.info("Thumbnail generated for video %s: %s",
                    video.id, thumbnail_filename)

    except subprocess.CalledProcessError as e:
        logger.error(
            "FFmpeg thumbnail generation failed for video %s: %s", video.id, e.stderr)
        # Don't raise - thumbnail failure shouldn't fail the whole job

    except Exception as e:
        logger.error(
            "Failed to generate thumbnail for video %s: %s", video.id, str(e))
        # Don't raise - thumbnail failure shouldn't fail the whole job
