import json
import datetime
import logging
import pprint
import queue
import asyncio

logger = logging.getLogger(__name__)

from asyncpraw import models
import aiohttp
import bs4
import yt_dlp

from . import config
from . import filters

async def parse_links(post: models.Submission, after: str, enable_filters):
    try:
        global globapost_filename
        globapost_filename = ''
        post_name = str(post.name)
        post_title = str(post.title)
        post_id = str(post.id)
        post_url = str(post.url)
        post_score = post.score
        logger.debug(f"{post_id} Post name {post_name}")
        logger.debug(f"{post_id} Post title {post_title}")
        logger.debug(f"{post_id} Post url {post_url}")
        logger.debug(f"{post_id} Post score {post_score}")

        if after == post_name:
            return None
        
        #TODO save post_url and check duplicates
        
        # this may require extra api requests
        sub_name = ''
        sub_id = ''
        try:
            r: models.Subreddit = post.subreddit
            await r.load()
            sub_name = r.display_name
            #sub_name = r.name
            sub_id = r.id[3:]
        except:
            logger.exception(f"{post_id} Probably deleted/removed subreddit")
            #return None

        # this may require extra api requests
        user_name = ''
        user_id = ''
        user_subreddit = None
        try:
            u: models.Redditor = post.author
            await u.load()
            user_name = u.name
            user_id = u.id[3:]
            user_subreddit = u.subreddit
            logger.debug(f"{post_id} User subreddit {user_subreddit}")
        except:
            logger.exception(f"{post_id} Probably deleted/removed user")
            #return None
        
        # filter
        if enable_filters:
            if filters.filter(post, post_id, post_title, post_url):
                logger.debug(f"{post_id} Filtered")
                return None

        # Check for non utf8 characters
        post_title_utf8 = post_title.encode('utf8', 'ignore').decode('utf8')
        if len(post_title_utf8) < len(post_title):
            logger.warn(f"{post_id} Warning post has non utf8 characters")

        # download
        direct_url = post_url
        direct_type = ''
        direct_poster = './img/black_pixel.png'

        #pprint.pprint(vars(l))

        # First check for imgut or redgifs image
        if ('imgur' in post_url or 'i.redgifs' in post_url) and (post_url.endswith('.jpg') or post_url.endswith('.jpeg')):
            direct_url = './audio/5-seconds-of-silence.mp3'
            direct_type = ''
            direct_poster = post.preview['images'][0]['source']['url']

        # Then jpg
        elif post_url.endswith('.jpg') or post_url.endswith('.jpeg'):
            direct_url = './audio/5-seconds-of-silence.mp3'
            direct_type = ''
            direct_poster = post_url

        # Then png image
        elif post_url.endswith('.png'):
            direct_url = './audio/5-seconds-of-silence.mp3'
            direct_type = ''
            direct_poster = post_url

        # Post link is png image
        elif 'reddit.com' in post_url and 'gallery' in post_url:
            #logger.debug(json.dumps(post.media_metadata))
            posts = []
            for i, (media_id, media) in enumerate(post.media_metadata.items()):
                if media['e'] == 'Image':
                    # TODO multiple posts
                    direct_url = './audio/5-seconds-of-silence.mp3'
                    direct_type = ''
                    direct_poster = media['s']['u']
                    posts.append({
                        'post_id': post_id,
                        'usesub_id': user_id,
                        'usesub_name': user_name,
                        'subreddit_id': sub_id,
                        'subreddit_name': sub_name,
                        'post_title': post_title_utf8,
                        'post_url': post_url,
                        'post_created_utc': datetime.datetime.fromtimestamp(int(post.created_utc), datetime.UTC).strftime("%Y-%m-%d %H:%M:%S"),
                        'post_score': post_score,
                        'direct_url': direct_url,
                        'direct_type': direct_type,
                        'direct_poster': direct_poster,
                    })
            return posts
        
        # get mp4 preview if gif
        elif 'i.redd.it' in post_url and '.gif' in post_url:
            #TODO sometimes gif is image
            #logger.debug(json.dumps(post.preview))
            direct_url = post.preview['images'][0]['variants']['mp4']['source']['url']
            direct_type = 'video/mp4'
            direct_poster = './img/black_pixel.png'

        elif 'imgur' in post_url and '.gif' in post_url:
            logger.debug(json.dumps(post.preview))
            try:
                direct_url = post.preview['images'][0]['variants']['mp4']['source']['url']
                direct_type = 'video/mp4'
                direct_poster = './img/black_pixel.png'
            except:
                direct_url = post.preview['reddit_video_preview']['fallback_url']

        #TODO does not seem to work : https://v.redd.it/an8oneqxnd7d1/DASHPlaylist.mpd?a=1721392778%2CNDJlYjA2MzcxMjhjMzM2M2JlYzhlYWZiOTdlNzJmZjA3YTgwNTkxNDE1OTU2YWE0NjRhMWEwZWZjZWQ2YmU5ZA%3D%3D&v=1&f=sd localhost:8000:163:19

        elif 'v.redd.it' in post_url and post.media is not None:
            direct_url = post.media['reddit_video']['dash_url']
            direct_type = 'application/dash+xml'
            direct_poster = './img/black_pixel.png'

        else:
            logger.warn(f"{post_id} Unkown type: {post_url}")

        return  [{
            'post_id': post_id,
            'usesub_id': user_id,
            'usesub_name': user_name,
            'subreddit_id': sub_id,
            'subreddit_name': sub_name,
            'post_title': post_title_utf8,
            'post_url': post_url,
            'post_created_utc': datetime.datetime.fromtimestamp(int(post.created_utc), datetime.UTC).strftime("%Y-%m-%d %H:%M:%S"),
            'post_score': post_score,
            'direct_url': direct_url,
            'direct_type': direct_type,
            'direct_poster': direct_poster,
        }]

    except:
        logger.exception(f"Post failed: {post}")
        return None
