import logging
import socket

import aiohttp
import fastapi
from fastapi import Response
from fastapi_cache.decorator import cache

from . import config
from . import links

logger = logging.getLogger(__name__)
reddit = None
router = fastapi.APIRouter(
    prefix="/api"
)

@router.get("/multis")
@cache(expire=86400)
async def multis():
    return [m.display_name for m in await reddit.user.multireddits()]

@router.get("/redgifs")
async def redgifs(url: str = ''):
    logger.debug(f"redgifs url: {url}")
    
    if 'watch/' in url:
        video_id = url.split("watch/")[1].split("/")[0].split("#")[0]
    elif 'ifr/' in url:
        video_id = url.split("ifr/")[1].split("/")[0].split("#")[0]
    else:
        return None
    
    connector = aiohttp.TCPConnector(family=socket.AF_INET)
    session = aiohttp.ClientSession(connector=connector)
    
    try:
        # info
        # info_url = "https://api.redgifs.com/info"
        # info_headers = {
        #     'referer': 'https://www.redgifs.com/',
        #     'origin': 'https://www.redgifs.com',
        #     'content-type': 'application/json',
        # }
        # info_response = await session.get(info_url, headers=info_headers)
        # logger.debug(f"info_response.status: {info_response.status}")
        # if info_response.status != 200:
        #     await session.close()
        #     return ""
        # info_data = await info_response.json()
        # info_response.close()
        # logger.debug(f"info_data: {info_data}")

        # auth
        auth_url = "https://api.redgifs.com/v2/auth/temporary"
        auth_headers = {
            'referer': 'https://www.redgifs.com/',
            'origin': 'https://www.redgifs.com',
            'content-type': 'application/json',
        }
        auth_response = await session.get(auth_url, headers=auth_headers)
        logger.debug(f"auth_response.status: {auth_response.status}")
        if auth_response.status != 200:
            await session.close()
            return ""
        auth_data = await auth_response.json()
        auth_response.close()
        logger.debug(f"auth_data.token: {auth_data['token']}")
        
        # api
        api_url = f"https://api.redgifs.com/v2/gifs/{video_id}"
        logger.debug(f"api_url: {api_url}")
        api_headers = {
            'referer': 'https://www.redgifs.com/',
            'origin': 'https://www.redgifs.com',
            'content-type': 'application/json',
            'x-customheader': f'https://www.redgifs.com/watch/{video_id}',
            'authorization': f'Bearer {auth_data['token']}',
        }
        api_response = await session.get(api_url, headers=api_headers)
        logger.debug(f"api_response.status: {api_response.status}")
        if api_response.status != 200:
            await session.close()
            return ""
        api_data = await api_response.json()
        api_response.close()
        logger.debug(f"api_data.gif.urls.hd: {api_data['gif']['urls']['hd']}")

        # gif
        gif_headers = {
            'referer': 'https://www.redgifs.com/',
            'origin': 'https://www.redgifs.com',
            'content-type': 'application/json',
            'x-customheader': f'https://www.redgifs.com/watch/{video_id}',
            'authorization': f'Bearer {auth_data['token']}',
        }
        gif_response = await session.get(api_data['gif']['urls']['hd'], headers=gif_headers)
        logger.debug(f"gif_response.status: {gif_response.status}")
        if gif_response.status != 200:
            await session.close()
            return ""
        gif_data = await gif_response.read()
        gif_response.close()
        await session.close()

        # return
        return Response(content=gif_data, media_type="video/mp4")
    except:
        await session.close()
        logger.exception("execption in /api/redgifs")

@router.get("/")
@cache(expire=86400)
async def root(after: str = '', sort: str = '', t: str = 'all', r: str = '', m: str = '', filters: bool = True):
    """
    after: t3_link id
    sort: best, hot, new, rising, controversial, top
    t: hour, day, week, month, year, all
    r: subreddit
    m: multireddit
    """
    
    params = {}

    # next page
    if after != '':
        params['after'] = after
    
    # valid sort time
    if t not in ['hour', 'day', 'week', 'month', 'year', 'all']:
        return None

    # front
    subreddit = reddit.front
    
    # subreddit
    if r != '':
        subreddit = await reddit.subreddit(r)
    elif m != '':
        # multireddit
        for multireddit in await reddit.user.multireddits():
            if m == multireddit.display_name:
                subreddit = multireddit
        # TODO check if multi is found
    
    generator = []
    if (sort == '' or sort == 'best') and m == '':
        generator = subreddit.best(limit=20, params=params)
    elif sort == 'hot':
        generator = subreddit.hot(limit=20, params=params)
    elif sort == 'new':
        generator = subreddit.new(limit=20, params=params)
    elif sort == 'rising':
        generator = subreddit.rising(limit=20, params=params)
    elif sort == 'controversial':
        generator = subreddit.controversial(limit=20, params=params, time_filter=t)
    elif sort == 'top':
        generator = subreddit.top(limit=20, params=params, time_filter=t)
    else:
        return None

    # multiple
    posts = []
    async for link in generator:
        new_posts = await links.parse_links(link, after, filters)
        if new_posts is not None:
            # concat list of new posts
            posts += new_posts
    
    logger.debug(posts)
    return posts
