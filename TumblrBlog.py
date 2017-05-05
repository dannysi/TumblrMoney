import datetime
import os
import random
import time
from abc import abstractmethod
from enum import Enum


# TODO implement unimplemented methods
# TODO test dump/reload mechanics
from typing import List

import httplib2
import requests


class PictureSourceType(Enum):
    LINK = 1
    FILE = 2

class PicToPost(object):
    def __init__(self, path: str, tags: List[str], dir: str, dirProps: dict,source = PictureSourceType.FILE ,caption: str = ""):
        self.path = path
        self.tags = tags
        self.caption = caption
        self.dir = dir
        self.dirProps = dirProps
        self.source = source

    def __repr__(self):
        return(str((self.path,self.tags,self.caption)))



class TumblrSourceType(Enum):
    DIR = 1
    SET_FILE = 2


class TumblrPhoto(object):
    def __init__(self, post: dict):
        self.photos = [i["original_size"]["url"] for i in post["photos"]]
        self.notes = post["note_count"]
        self.reblog = post["reblogged_root_name"] if "reblogged_root_name" in post else None
        self.tags = post['tags']
        self.date = datetime.datetime.fromtimestamp(post["timestamp"])
        self.id = post["id"]
        self.reblog_key = post["reblog_key"]
        self.description = post['caption']




class BlogDelegations(object):
    @classmethod
    def defaultCaptionDelegate(dir: str, dirProperties: dict):
        return ""
    @classmethod
    def defaultTagsDelegate(dir: str, dirProperties: dict):
        return list()

    def __init__(self, tagDelegate=defaultTagsDelegate, captionDelegate=defaultCaptionDelegate):
        self.tagDelegate = tagDelegate
        self.captionDelegate = captionDelegate

    def process(self, picToPost: PicToPost):
        picToPost.caption = self.captionDelegate(picToPost.dir, picToPost.dirProps)
        picToPost.tags += self.tagDelegate(picToPost.dir, picToPost.dirProps)


class TumblrSource(object):
    saveCount = 0

    @abstractmethod
    def getPics(self, amount: int, amountPerSubfolder: int = 5):
        pass

    @abstractmethod
    def removeFromDb(self, pic: PicToPost)-> None:
        pass

    @abstractmethod
    def remove(self,pic):
        pass

    @abstractmethod
    def save(self,pic):
        pass

class TumblrLinkSource(TumblrSource):
    def __init__(self,path: str):
        TumblrSource.__init__(self)
        self.sourceDict = eval(open(path, 'r', encoding="utf8").read())
        self.path = path

    def getPics(self, amount: int, amountPerSubfolder: int = 5):
        picked = list()
        c = 0
        for pic in self.sourceDict:
            picked += [PicToPost(pic, self.sourceDict[pic][0], None, None, PictureSourceType.LINK, self.sourceDict[pic][1])]
            c += 1
            if c == amount:
                break
        return picked

    def remove(self, pic):
        self.removeFromDb(pic)

    def save(self,force:bool = True):
        self.saveCount += 1
        if self.saveCount == 30 or force:
            f = open(self.path, 'w', encoding="utf8")
            f.write(str(self.sourceDict))

    def removeFromDb(self, pic: PicToPost) -> None:
        del self.sourceDict[pic.path]

class TumblrDirSource(TumblrSource):
    def __init__(self, path: str, category: str="ALL"):
        TumblrSource.__init__(self)
        # TODO check if path exists and is set file or dicectory
        self.globalDict = eval(open(path, 'r',encoding="utf8").read())
        self.category = category
        self.file = path

    def _initPics(self, listOfPics, dirName: str, dirProperties: dict):
        return [PicToPost(os.path.join(dirProperties['directory'], pic),
                          dirProperties['files'][pic] + dirProperties['tags'], dirName, self.globalDict[dirName],source=PictureSourceType.FILE) for
                pic in listOfPics]

    def save(self, force: bool=False) -> None:
        self.saveCount += 1
        if self.saveCount == 30 or force:
            f = open(self.file, 'w',encoding="utf8")
            f.write(str(self.globalDict))

    def remove(self, pic: PicToPost) -> None:
        try:
            os.remove(pic.path)
            self.removeFromDb(pic)
        except PermissionError as e:
            print("Error! couldn't remove file ",pic.path,e.strerror)
            time.sleep(3)
            print("Retrying")
            try:
                os.remove(pic.path)
                self.removeFromDb(pic)
            except PermissionError as e:
                print("Error! couldn't remove file again", pic.path, e.strerror,"Failing")
                return

    def getPics(self, amount: int, amountPerSubfolder: int = 5)-> List[PicToPost]:
        picked = 0  # type: int
        pics = list()  # type: list[PicToPost]
        while picked < amount:
            dir = random.choice(list(self.globalDict))
            if self.category != "ALL" and self.category not in self.globalDict[dir]['tags']:
                continue
            fileAmount = len(self.globalDict[dir]['files'])
            if fileAmount == 0:
                continue
            elif fileAmount <= amountPerSubfolder:
                pics += self._initPics(list(self.globalDict[dir]['files']), dir, self.globalDict[dir])
                picked += fileAmount
            else:
                pics += self._initPics(random.sample(list(self.globalDict[dir]['files']), amountPerSubfolder), dir,
                                       self.globalDict[dir])
                picked += amountPerSubfolder
        return pics[0:amount]

    def removeFromDb(self, pic: PicToPost)-> None:
        if os.path.basename(pic.path) in self.globalDict[pic.dir]['files']:
            del self.globalDict[pic.dir]['files'][os.path.basename(pic.path)]
            self.save()


class TumblrBlog(object):
    def __init__(self, name: str, source: TumblrDirSource, blogDelegates=BlogDelegations(), client=None, tags=None):
        self.client = client
        self.name = name
        self.source = source

        self.tags = tags
        if self.tags is None: self.tags = list()
        self.blogDelegates = blogDelegates

    # TESTED
    def _queue(self, picture: str, **kwargs):
        queueDict = dict()
        queueDict["state"] = "queue"
        queueDict["tags"] = list(self.tags)
        if 'tags' in kwargs:
            queueDict["tags"] += kwargs['tags']
        queueDict["tags"] = [tag.replace("-", " ").replace("_", " ").replace(".", " ") for tag in queueDict["tags"]]
        queueDict["format"] = "markdown"
        queueDict["source" if type(self.source) == TumblrLinkSource else "data"] = picture
        if 'caption' in kwargs:
            queueDict["caption"] = kwargs["caption"]

        response = self.client.create_photo(self.name, **queueDict)
        print(response)
        return (response)

    def getQueueSize(self):
        x = len(self.client.queue(self.name, limit=50, offset=0)['posts'])
        count = x  # type: int
        while x == 50:
            try:
                q = self.client.queue(self.name, limit=50, offset=count)['posts']
            except ConnectionError:
                print("Error! couldn't connect to get Queue size")
                return 500
            x = len(q)
            count += x
        return count

    def fillQueue(self, amount: int):
        pics = self.source.getPics(amount)
        print(len(pics))
        for pic in pics: self.blogDelegates.process(pic)
        # TODO parallelism
        for pic in pics:
            if pic.source == PictureSourceType.FILE and not os.path.isfile(pic.path):
                self.source.removeFromDb(pic)
                continue
            elif pic.source == PictureSourceType.LINK:
                try:
                    httplib2.Http().request(pic.path)
                except:
                    print(pic.path,'doesnt respond...continue')
                    self.source.removeFromDb(pic)
                    continue
            try:
                response = self._queue(pic.path, tags=pic.tags, caption=pic.caption)
            except requests.exceptions.ConnectionError:
                print("Error! Connection refused for blog ", self.name)
                continue
            if 'meta' in response and 'status' in response['meta'] and response['meta']['status'] == 500:
                print("server error - continue")
                continue
            if 'meta' in response and 'status' in response['meta'] and response['meta']['status'] == 400:
                print("bad request - break")
                break
            if 'meta' in response and 'status' in response['meta'] and response['meta']['status'] == 403:
                print("forbidden")
                break
            if 'meta' in response and 'status' in response['meta'] and response['meta']['status'] == 502:
                print("unavailable")
                continue
            self.source.remove(pic)
        self.source.save(True)

    def post(self, picture, **kwargs):
        pass

    def getLastPost(self) -> TumblrPhoto:
        return self.getLastPosts(1)[0]
    def getLastPosts(self,amount: int):
        ans = []
        try:
            if amount < 50:
                ans =  [ TumblrPhoto(post) for post in self.client.posts(self.name, limit=amount, offset=0)['posts']]
            else:
                ans =  [ TumblrPhoto(post) for post in self.client.posts(self.name, limit=50, offset=0)['posts']] + self.getLastPost(amount-50)
        except requests.exceptions.ConnectionError:
            print("Error! couldn't get last posts", amount)
        return ans

    def getNextPosts(self, numberOfPosts):
        pass

    def reblog(self, post: TumblrPhoto):
        return self.client.reblog(self.name, id=post.id,reblog_key=post.reblog_key,tags=post.tags)
