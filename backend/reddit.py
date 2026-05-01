import asyncpraw
import asyncpraw.models
import asyncpraw.models.listing.mixins

# class SubredditListing(asyncpraw.models.listing.mixins.SubredditListingMixin):
#     def best(self, limit = 20, params: dict[str, str | int]| None = None):
#         return super().best(limit = limit, params= params)

class Reddit(asyncpraw.Reddit):
    """
    Add types to asyncpraw.Reddit for type check 
    """
    user: asyncpraw.models.User
    front: asyncpraw.models.Front
    #subreddit: asyncpraw.models.Subreddit

    def __init__(self):
        pass

    def subreddit(self, display_name: str):
        return super().subreddit(display_name)