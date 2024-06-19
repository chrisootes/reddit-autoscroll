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

import config
import filter

# l = link
async def parse_links(l: models.Submission, after: str):
    try:
        global global_filename
        global_filename = ''
        l_name = str(l.name)
        l_title = str(l.title)
        l_id = str(l.id)
        l_url = str(l.url)
        l_score = l.score
        logger.debug(f"{l_id} Post name {l_name}")
        logger.debug(f"{l_id} Post title {l_title}")
        logger.debug(f"{l_id} Post url {l_url}")
        logger.debug(f"{l_id} Post score {l_score}")

        if after == l_name:
            return None
        
        #TODO save l_url and check duplicates
        
        # this may require extra api requests
        r_name = ''
        r_id = ''
        try:
            r: models.Subreddit = l.subreddit
            await r.load()
            r_name = r.display_name
            #r_name = r.name
            r_id = r.id[3:]
        except:
            logger.exception(f"{l_id} Probably deleted/removed subreddit")
            #return None

        # this may require extra api requests
        u_name = ''
        u_id = ''
        u_subreddit = None
        try:
            u: models.Redditor = l.author
            await u.load()
            u_name = u.name
            u_id = u.id[3:]
            u_subreddit = u.subreddit
            logger.debug(f"{l_id} User subreddit {u_subreddit}")
        except:
            logger.exception(f"{l_id} Probably deleted/removed user")
            #return None
        
        # filter
        if filter.filter(l, l_id, l_title, l_url):
            logger.debug(f"{l_id} Filtered")
            return None

        # Check for non utf8 characters
        l_title_utf8 = l_title.encode('utf8', 'ignore').decode('utf8')
        if len(l_title_utf8) < len(l_title):
            logger.warn(f"{l_id} Warning post has non utf8 characters")

        # download
        direct_url = l_url
        direct_type = ''
        direct_poster = './img/black_pixel.png'

        #pprint.pprint(vars(l))

        # First check for imgut or redgifs image
        if ('imgur' in l_url or 'i.redgifs' in l_url) and (l_url.endswith('.jpg') or l_url.endswith('.jpeg')):
            direct_url = './5-seconds-of-silence.mp3'
            direct_type = ''
            direct_poster = l.preview['images'][0]['source']['url']

        # Then jpg
        elif l_url.endswith('.jpg') or l_url.endswith('.jpeg'):
            direct_url = './5-seconds-of-silence.mp3'
            direct_type = ''
            direct_poster = l_url

        # Then png image
        elif l_url.endswith('.png'):
            direct_url = './5-seconds-of-silence.mp3'
            direct_type = ''
            direct_poster = l_url

        # Post link is png image
        elif 'reddit.com' in l_url and 'gallery' in l_url:
            #logger.debug(json.dumps(l.media_metadata))
            posts = []
            for i, (media_id, media) in enumerate(l.media_metadata.items()):
                if media['e'] == 'Image':
                    # TODO multiple posts
                    direct_url = './5-seconds-of-silence.mp3'
                    direct_type = ''
                    direct_poster = media['s']['u']
                    posts.append({
                        'link_id': l_id,
                        'user_id': u_id,
                        'user_name': u_name,
                        'subreddit_id': r_id,
                        'subreddit_name': r_name,
                        'post_title': l_title_utf8,
                        'post_url': l_url,
                        'post_created_utc': datetime.datetime.fromtimestamp(int(l.created_utc), datetime.UTC).strftime("%Y-%m-%d %H:%M:%S"),
                        'post_score': l_score,
                        'direct_url': direct_url,
                        'direct_type': direct_type,
                        'direct_poster': direct_poster,
                    })
            return posts

        # get mp4 preview if gif
        elif 'i.redd.it' in l_url and '.gif' in l_url:
            #TODO sometimes gif is image
            #logger.debug(json.dumps(l.preview))
            direct_url = l.preview['images'][0]['variants']['mp4']['source']['url']
            direct_type = 'video/mp4'
            direct_poster = './black_pixel.png'

        elif 'imgur' in l_url and '.gif' in l_url:
            logger.debug(json.dumps(l.preview))
            try:
                direct_url = l.preview['images'][0]['variants']['mp4']['source']['url']
                direct_type = 'video/mp4'
                direct_poster = './black_pixel.png'
            except:
                direct_url = l.preview['reddit_video_preview']['fallback_url']

        elif 'v.redd.it' in l_url and l.media is not None:
            direct_url = l.media['reddit_video']['dash_url']
            direct_type = 'application/dash+xml'
            direct_poster = './black_pixel.png'

        else:
            logger.warn(f"{l_id} Unkown type: {l_url}")

        return  [{
            'link_id': l_id,
            'user_id': u_id,
            'user_name': u_name,
            'subreddit_id': r_id,
            'subreddit_name': r_name,
            'post_title': l_title_utf8,
            'post_url': l_url,
            'post_created_utc': datetime.datetime.fromtimestamp(int(l.created_utc), datetime.UTC).strftime("%Y-%m-%d %H:%M:%S"),
            'post_score': l_score,
            'direct_url': direct_url,
            'direct_type': direct_type,
            'direct_poster': direct_poster,
        }]

    except:
        logger.exception(f"Post failed: {l}")
        return None
