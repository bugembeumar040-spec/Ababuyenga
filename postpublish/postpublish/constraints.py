"""Hard limits YouTube enforces on post-publish metadata.

Every number here is a platform constraint, not a style preference. Style
preferences live in rules.py so the two never get confused: breaking a
constraint makes the API reject the write (or silently drop the feature),
breaking a rule just makes the video perform worse.
"""

# videos.update / snippet
TITLE_MAX = 100
DESCRIPTION_MAX = 5000
TAGS_TOTAL_CHARS_MAX = 500  # sum of tag lengths, not the tag count

# Angle brackets are rejected outright in titles and descriptions.
FORBIDDEN_TITLE_CHARS = "<>"

# Hashtags: YouTube shows the first 3 above the title. Past 15 in the
# description it stops honouring *all* of them, which is a silent failure --
# the tags do not partially apply, they switch off.
HASHTAGS_MAX = 15
HASHTAGS_SHOWN_ABOVE_TITLE = 3

# Chapters only render if all three hold at once.
CHAPTER_MIN_COUNT = 3
CHAPTER_FIRST_MUST_BE_ZERO = True
CHAPTER_MIN_LENGTH_SECONDS = 10

# commentThreads.insert
COMMENT_MAX = 10000

# thumbnails.set
THUMBNAIL_MAX_BYTES = 2 * 1024 * 1024
THUMBNAIL_RECOMMENDED_SIZE = (1280, 720)
THUMBNAIL_MIME = ("image/jpeg", "image/png", "image/gif", "image/bmp")

# Above-the-fold description text before YouTube truncates with "...more".
# Not an API limit -- it is where the fold lands on mobile, which is where
# the majority of the audience reads it.
DESCRIPTION_FOLD_CHARS = 150

# Quota cost per call, for budgeting a run (units).
QUOTA = {
    "videos.list": 1,
    "videos.update": 50,
    "thumbnails.set": 50,
    "playlistItems.insert": 50,
    "commentThreads.insert": 50,
    "captions.list": 50,
    "captions.insert": 400,
    "commentThreads.list": 1,
    "playlists.list": 1,
}
DAILY_QUOTA_DEFAULT = 10000
