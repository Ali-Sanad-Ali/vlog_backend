import os
import tempfile
import logging
from datetime import timedelta
from urllib.parse import urljoin
from celery import shared_task
from django.conf import settings
from moviepy.editor import VideoFileClip
from django.core.files import File
from django.core.files.storage import default_storage
from django.core.exceptions import ValidationError
from PIL import Image
import requests
from trend.s3_utils import S3

logger = logging.getLogger('vlogs')


MAX_SIZE = 200 * 1024 * 1024  # 200 MB
MAX_DURATION = 15  # seconds
ALLOWED_EXTENSIONS = ['mp4', 'mov', 'avi']


def validate_video_size(file_path):
    file_size = os.path.getsize(file_path)
    if file_size > MAX_SIZE:
        raise ValidationError('File size exceeds the limit.')


def validate_video_duration(duration):
    if duration > MAX_DURATION:
        raise ValidationError('Video duration exceeds the limit.')


def validate_video_extension(file_key):
    file_extension = os.path.splitext(file_key)[1][1:].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise ValidationError(f"Invalid video extension: {file_extension}. Allowed extensions are: {', '.join(ALLOWED_EXTENSIONS)}")


def generate_thumbnail(file_path, video_id):
    thumbnail_path = file_path.replace('.mp4', f'_{video_id}_thumbnail.jpg')
    logger.info(f"Generating thumbnail for video {video_id} at {thumbnail_path}")
    with VideoFileClip(file_path) as video_clip:
        frame = video_clip.get_frame(1)  # Extract frame at 1 second
        image = Image.fromarray(frame)
        image.save(thumbnail_path, format='JPEG')
    return thumbnail_path


@shared_task
def process_video_validation(video_id):
    from .models import Vlog, VlogProcessingTask
    try:
        video = Vlog.objects.get(id=video_id)
        task = video.processing_task
        logger.info(f"Processing video {video_id}")

        vlog_url = urljoin(settings.MEDIA_URL, video.vlog_key)
        # Download video from URL
        response = requests.get(vlog_url, stream=True)

        if response.status_code != 200:
            raise Exception(f"Failed to download video from {video.video_url}")

        # Save the downloaded video to a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:  # filter out keep-alive new chunks
                    temp_file.write(chunk)
            temp_file.close()
            temp_video_path = temp_file.name

        # Validate file size
        validate_video_size(temp_video_path)
        logger.info(f"Video file size validated.")

        # Validate video extension
        validate_video_extension(video.vlog_key)
        logger.info(f"Video file extention validated.")

        # Calculate duration and validate it
        with VideoFileClip(temp_video_path) as video_clip:
            duration_seconds = video_clip.duration
            validate_video_duration(duration_seconds)
            # Convert seconds to timedelta
            duration_timedelta = timedelta(seconds=duration_seconds)
            video.duration = duration_timedelta
            video.save()
            logger.info(f"Video duration: {duration_seconds} seconds")

        # Process thumbnail in a separate task
        process_thumbnail.delay(video_id, temp_video_path)

        # Update the task status to completed
        task.status = VlogProcessingTask.COMPLETED
        task.error_message = None
        task.save()
        video.processing_status = 'completed'
        video.save()

    except Exception as e:
        task = VlogProcessingTask.objects.get(vlog_id=video_id)
        task.status = VlogProcessingTask.FAILED
        task.error_message = str(e)
        task.save()
        video.processing_status = 'failed'
        video.save()

        # Clean up the invalid video from S3
        S3().delete_file(video.vlog_key)
        logger.error(f"Error processing video {video_id}: {e}", exc_info=True)

@shared_task
def process_thumbnail(video_id, temp_video_path):
    from .models import Vlog
    try:
        video = Vlog.objects.get(id=video_id)
        logger.info(f"Processing thumbnail for video {video_id} using temp video path {temp_video_path}")

        thumbnail_path = generate_thumbnail(temp_video_path, video_id)
        logger.info(f"Thumbnail generated at {thumbnail_path}")

        # Upload thumbnail to S3
        with open(thumbnail_path, 'rb') as thumbnail_file:
            video.thumbnail.save(f'{video_id}_thumbnail.jpg', File(thumbnail_file))
            logger.info(f"Thumbnail uploaded and saved for video {video_id}")
        # Clean up the thumbnail file
        if os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)
            logger.info(f"Thumbnail file removed: {thumbnail_path}")
        else:
            logger.warning(f"Thumbnail file not found during cleanup: {thumbnail_path}")
    
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)
            logger.info(f"Temporary video file removed: {temp_video_path}")
        else:
            logger.warning(f"Temporary video file not found during cleanup: {temp_video_path}")

        # Save the updated video instance
        video.save()
        logger.info(f"Video {video_id} saved successfully")
    except Exception as e:
        logger.error(f"Error generating thumbnail for video {video_id}: {e}", exc_info=True)
