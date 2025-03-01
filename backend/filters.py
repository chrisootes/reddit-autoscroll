import logging

import asyncpraw.models
import demoji

logger = logging.getLogger(__name__)

def filter(post: asyncpraw.models.Submission, post_id, post_title: str, post_url) -> bool:

    # Check gif
    if 'gif' in post_url:
        return False
    if 'mp4' in post_url:
        return False

    # Delete emojis
    emojis_filtered = demoji.replace(post_title, "")

    # Check if string with delete emojis is shorter
    if len(emojis_filtered) < len(post_title) or \
        ':P' in post_title or \
        ';)' in post_title or \
        ':)' in post_title or \
        '(;' in post_title:

        logger.debug(f"{post_id} Emoji filtered")
        return True

    if 'OC' in post_title or \
        '(oc)' in post_title or \
        '[oc]' in post_title or \
        'my ' in post_title.lower() or \
        '?' in post_title or \
        '!' in post_title or \
        'self' in post_title.lower() or \
        'f)' in post_title.lower() or \
        'f]' in post_title.lower() or \
        'I ' in post_title or \
        ' i ' in post_title.lower() or \
        'mine ' in post_title.lower() or \
        ' me ' in post_title.lower() or \
        'f1' in post_title.lower() or \
        'f2' in post_title.lower() or \
        'f3' in post_title.lower() or \
        'f4' in post_title.lower() or \
        'f5' in post_title.lower() or \
        'f6' in post_title.lower() or \
        'f7' in post_title.lower() or \
        'f8' in post_title.lower() or \
        'f9' in post_title.lower() or \
        'milf' in post_title.lower():

        logger.debug(f"{post_id} Post title filtered")
        return True

    if post.is_self:
        logger.debug(f"{post_id} Self filtered")
        return True
    
    if 'reddit.com/r/' in post_url:
        # TODO browse to x-post
        logger.debug(f"{post_id} X-post filtered")
        return True
    
    # Skip some sites
    if 'pornvideoxxxtube' in post_url or 'pornhub' in post_url:
        logger.debug(f"{post_id} Post is long video: {post_title}, {post_url}")
        return True
    
    return False
    