
def video_upload_to(instance, filename):
    """
    Return the upload path for a video file.

    Files are stored inside the 'videos/' directory, preserving the original filename.
    """

    return f"videos/{filename}"
