import datetime
import random

import pytumblr
from enum import Enum
import os
#TODO implement unimplemented methods
#TODO test dump/reload mechanics



class PicToPost(object):
    def __init__(self, path,tags,caption,dir,dirProps):
        self.path = path #type: str
        self.tags = tags #type: list[str]
        self.caption = caption #type: str
        self.dir = dir #type: str
        self.dirProps = dirProps #type: dict


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
        #TODO parse description
        self.description = ""


def defaultCaptionDelegate(dir: str,dirProperties: dict):
    return ""

def defaultTagsDelegate(dir: str,dirProperties: dict):
    return []

class BlogDelegations(object):
    def __init__(self,tagDelegate=defaultTagsDelegate(),captionDelegate=defaultCaptionDelegate()):
        self.tagDelegate=tagDelegate
        self.captionDelegate=captionDelegate
    def process(self,picToPost):
        picToPost.caption = self.captionDelegate(picToPost.dir,picToPost.dirProps)
        picToPost.tags += self.tagDelegate(picToPost.dir, picToPost.dirProps)


class TumblrBlog:
    def __init__(self,name: str,source: TumblrSource,blogDelegates=TumblrBlog(),client=None,tags = []):
        self.client = client
        self.name = name
        self.source = source
        self.tags = tags
        self.blogDelegates=blogDelegates
#TESTED
    def _queue(self,picture: str,**kwargs):
        queueDict = dict()
        queueDict["state"] = "queue"
        queueDict["tags"] = self.tags
        if 'tags' in kwargs:
            queueDict["tags"] += kwargs["tags"]
        queueDict["format"] = "markdown"
        queueDict["source" if self.source.sourceType == PictureSourceType.LINK else "data"] = picture
        if 'caption' in kwargs:
            queueDict["caption"] = kwargs["caption"]
        response = self.client.create_photo(self.name,**queueDict)
        print(response)
        return(response)


    def getQueueSize(self):
        x = len(self.client.queue(self.name, limit=50, offset=0)['posts'])
        count = x #type: int
        while x == 50:
            x = len(self.client.queue(self.name, limit=50, offset=count)['posts'])
            count += x
        return count

    def fillQueue(self,amount: int):
        pics = self.source.getPics(amount)
        for pic in pics:self.blogDelegates.process(pic)
        #TODO parallelism
        for pic in pics:
            if not os.path.isfile(pic.path):
                continue
            response = self._queue(pic.path,tags = pic.tags,caption = pic.caption)
            if 'meta' in response and 'status' in response['meta'] and response['meta']['status'] == 500:
                print("server error - continue")
                continue
            if 'meta' in response and 'status' in response['meta'] and response['meta']['status'] == 400:
                print("bad request - break")
                break
            if 'meta' in response and 'status' in response['meta'] and response['meta']['status'] == 403:
                print("forbidden")
                break
            self.source.remove(pic)
        self.source.save(True)
    def post(self,picture,**kwargs):
        pass
    def getLastPost(self):
        pass
    def getNextPosts(self,numberOfPosts):
        pass


class TumblrSource:

    saveCount = 0

    def __init__(self,sourceType,path,category = "ALL",captionDelegate = defaultCaptionDelegate,tagsDelegate = defaultTagsDelegate):
        if type(sourceType) != TumblrSourceType:
            raise "wrong source type"
        #TODO check if path exists and is set file or dicectory
        self.sourceType = sourceType
        self.globalDict = eval(open(path, 'r').read())
        self.category = category
        self.file = path


    def _initPics(self,listOfpics,dirName,dirProperties):
        return [PicToPost(os.path.join(dirProperties['directory'],pic),dirProperties['files'][pic]+dirProperties['tags'],dirName,self.globalDict[dirName]) for pic in listOfpics]

    def save(self,force = False ):
        self.saveCount +=1
        if self.saveCount == 30 or force:
            f = open(self.file, 'w')
            f.write(str(self.globalDict))

    def remove(self,pic):
        os.remove(pic.path)
        del self.globalDict[pic.dir]['files'][os.path.basename(pic.path)]
        self.save()

    def getPics(self,amount,amountPerSubfolder = 5):
        picked = 0
        pics = []
        while picked < amount:
            dir = random.choice(list(self.globalDict))
            if self.category != "ALL" and self.category not in self.globalDict[dir]['tags']:
                continue
            fileAmount = len(self.globalDict[dir]['files'])
            if fileAmount == 0:
                continue
            elif fileAmount <= amountPerSubfolder:
                pics += self._initPics(list(self.globalDict[dir]['files']),dir,self.globalDict[dir])
                picked += fileAmount
            else:
                pics += self._initPics(random.sample(list(self.globalDict[dir]['files']),amountPerSubfolder),dir,self.globalDict[dir])
                picked += amountPerSubfolder
        return pics[0:amount]


