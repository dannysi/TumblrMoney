import datetime
import pytumblr
from enum import Enum
#TODO implement unimplemented methods
#TODO test dump/reload mechanics



class PictureSourceType(Enum):
    LINK = 1
    FILE = 2

class TumblrSourceType(Enum):
    DIR = 1
    SET_FILE = 2


class TumblrPhoto:
    def __init__(self, post):
        self.photos = [post["photos"][i]["original_size"]["url"] for i in post["photos"] ]
        self.notes = post["note_count"]
        self.reblog = post["reblogged_root_name"] if "reblogged_root_name" in post else None
        #TODO parse tags
        self.tags = []
        self.date = datetime.datetime.fromtimestamp(post["timestamp"])
        self.id = post["id"]
        self.reblog_key = post["reblog_key"]





class TumblrBlog:
    def __init__(self,name,source,client=None):
        self.client = client
        self.name = name
        self.source = source

    def queue(self,picture,**kwargs):
        queueDict = dict()
        queueDict["state"] = "queue"
        queueDict["tags"] = kwargs["tags"]
        queueDict["format"] = "markdown"
        queueDict["source" if kwargs["picSource"] == PictureSourceType.LINK else "data"] = picture
        queueDict["caption"] = kwargs["caption"]
        response = self.client.create_photo(self.name,**queueDict)
        print(response)

    def getQueueSize(self):
        pass
    def post(self,picture,**kwargs):
        pass
    def getLastPost(self):
        pass
    def getNextPosts(self,numberOfPosts):
        pass


class TumblrSource:
    def __init__(self,sourceType,path):
        if type(sourceType) != TumblrSourceType:
            raise "wrong source type"
        #TODO check if path exists and is set file or dicectory
        self.sourceType = sourceType
        self.path = path

    def getPics(self,amount):
        pass

