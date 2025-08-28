# Available resolution options for transcoded video streams
RESOLUTION_CHOICES = [
    ('360p', '360p'),
    ('480p', '480p'),
    ('720p', '720p'),
    ('1080p', '1080p'),
]

# Processing states for video transcoding
PROCESSING_CHOICES = [
    ("pending", "Pending"),
    ("processing", "Processing"),
    ("completed", "Completed"),
    ("failed", "Failed"),
]
