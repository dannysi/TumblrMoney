from abc import abstractmethod
import os
# TODO implement unimplemented methods
from queue import PriorityQueue
from typing import *
import urllib.request
import sys

from InstagramScrapper.Scrapper import InstagramScraper
from TumblrDefs import TOP_DIR, SOURCE_FILE


class InstagramPic(object):
    def __init__(self, id, path, type, creation, likes, description, tags):
        self.id = id
        self.path = path
        self.likes = int(likes)
        self.description = description
        self.tags = tags
        self.creation = creation
        self.type = type

    def __repr__(self):
        return str((self.path, self.id))

    @classmethod
    def fromInstagramApi(cls, dic):
        id = dic['id']
        # TODO test for multiple images
        path = dic['images']['standard_resolution']['url']
        likes = dic['likes']['count']
        if 'caption' in dic and dic['caption'] != None and 'text' in dic['caption']:
            description, tags = cls.extractDescription(dic['caption']['text'])
        else:
            description, tags = "",[]
        # TODO should be datetime
        creation = dic['created_time']
        type = dic['type']
        return cls(id, path, type, creation, likes, description, tags)

    @classmethod
    def extractDescription(cls, desc):
        words = desc.split(" ")
        tags = []
        desc = []
        for word in words:
            if len(word) == 0: continue
            if word[0] == "#":
                tags.append(word[1:])
            else:
                desc.append(word)
        return " ".join(desc), tags

    def __cmp__(self, other):
        if other.likes < self.likes:
            return -1
        elif other.likes > self.likes:
            return 1
        else:
            return 0

    def __lt__(self, other):
        return other.likes < self.likes


class InstagramBlog(object):
    id = None
    tags = []
    lastDownloaded = None
    picker = None  # type: InstagramPhotoPicker
    downloader = None  # type: InstagramDownloader
    link = None

    def __init__(self, id, tags=None):
        if tags is None:
            tags = []
        self.id = id
        self.tags = tags + self.getMoreTags()

    @classmethod
    def fromGlobalDict(cls,name,gDictEntry,topDir,srcFile,limit=1000):
        blog = cls(name,gDictEntry['tags'])
        blog.lastDownloaded= gDictEntry['firstPic']
        blog.downloader = InstagramDownloader(blog,topDir,srcFile,limit)
        if 'pickerAvg' in gDictEntry:
            blog.picker = InstagramPhotoPickerByAvgMult(blog,gDictEntry['batchSize'],gDictEntry['pickerAvg'])
        else :blog.picker = InstagramPhotoPickerByTop(blog,gDictEntry['batchSize'],gDictEntry['PickTop'])
        return blog


    def getNextPics(self, NumberOfPics):
        for batch in InstagramScraper(self.id).getBatchOfPhotos(NumberOfPics):
            ans = [InstagramPic.fromInstagramApi(item) for item in batch]
            yield ans

    def hasNewBatch(self):
        for batch in InstagramScraper(self.id).getBatchOfPhotos(self.picker.batch):
            for entry in batch:
                if self.lastDownloaded in entry['images']['standard_resolution']['url'] or self.lastDownloaded == entry['id']:
                    return False
            return True
        return True

    def getBlogDetails(self):
        ret = InstagramScraper(self.id).fetch_user(self.id)
        return ret

    def getMoreTags(self):
        details = self.getBlogDetails()
        ans = []
        if details['full_name'] != None: ans.append(details['full_name'])
        return ans

    def getBlogDescription(self):
        pass

    def getBlogTags(self):
        pass

    def download(self,update = False):
        x = None
        if update: x = self.lastDownloaded
        if not update and not self.downloader.isNew:
            print("-E- Blog",self.id,"Already exists in database. Please rerun with the update flag")
            return
        for batch in self.picker.pick(x):
            self.downloader.downloadList(batch,update)
            update = False
            if self.downloader.decLimit(len(batch)):
                return



class InstagramPhotoPicker(object):
    def __init__(self, blog: InstagramBlog, batch):
        self.blog = blog
        self.batch = batch

    def findLast(self,pics:List[InstagramPic],last):
        c = 0
        for tup in pics:
            if last in tup.path or last in tup.id:
                return c
            else : c+= 1
        return None
    def pick(self,last = None):
        end = False
        for pics in self.blog.getNextPics(self.batch):
            if last != None:
                lastPos = self.findLast(pics,last)
                if lastPos != None:
                        pics = pics[:lastPos]
                        end = True
            filtered = [pic for pic in pics if pic.type == 'image']
            yield self._pick(filtered)
            if end:break

    @abstractmethod
    def _pick(self, pics):
        pass

    @abstractmethod
    def getProps(self) -> dict:
        pass


class InstagramPhotoPickerByAvgMult(InstagramPhotoPicker):
    def __init__(self, blog, batch=50, avgMultiplyer=1):
        InstagramPhotoPicker.__init__(self, blog, batch)
        self.avgMultiplyer = avgMultiplyer

    def _pick(self, pics):
        avg = sum(pic.likes for pic in pics) * self.avgMultiplyer / len(pics)
        return [x for x in pics if x.likes >= avg]

    def getProps(self):
        return {'batchSize': self.batch, 'pickerAvg': self.avgMultiplyer}


class InstagramPhotoPickerByTop(InstagramPhotoPicker):
    def __init__(self, blog, batch=50, topPics=5):
        InstagramPhotoPicker.__init__(self, blog, batch)
        self.topPics = topPics

    def _pick(self, pics):
        q = PriorityQueue()
        for pic in pics: q.put(pic)
        return [q.get() for i in range(self.topPics)]

    def getProps(self):
        return {'batchSize': self.batch, 'PickTop': self.topPics}


class InstagramDownloader(object):
    #TODO add limit
    def __init__(self, blog: InstagramBlog, topDir: str, sourceFile: str,limit :int = sys.maxsize):
        self.topDir = topDir
        self.sourceFile = sourceFile
        self.blog = blog
        self.limit = limit

    def decLimit(self,amount = 1):
        self.limit -= amount
        return (self.limit <= 0)

    def download(self, pic: InstagramPic, update: bool = False):
        globalDict = self._downloadPrep()
        self._download(pic, globalDict[self.blog.id], update)
        f = open(self.sourceFile, 'w')
        f.write(str(globalDict))
        f.close()
        self.limit -= 1

    def _downloadPrep(self) -> dict:
        dir = self._mkdir()
        globalDict = eval(open(self.sourceFile, 'r',encoding="utf8").read())
        if self.blog.id not in globalDict: globalDict[self.blog.id] = {'tags': self.blog.tags, 'files': {},
                                                                       'link': self.blog.link, 'firstPic': None,
                                                                       'directory': dir}
        pickerProps = self.blog.picker.getProps()
        for prop in pickerProps:
            globalDict[self.blog.id][prop] = pickerProps[prop]
        return globalDict

    def _download(self, pic: InstagramPic, dirDict: dict, update: bool):
        basename = os.path.basename(pic.path)
        urllib.request.urlretrieve(pic.path, os.path.join(dirDict['directory'], basename))
        if dirDict['firstPic'] == None or update: dirDict['firstPic'] = pic.id
        dirDict['files'][basename] = pic.tags
        print(pic.path)

    def downloadList(self, pics: List[InstagramPic], update: bool = False):
        globalDict = self._downloadPrep()
        for pic in pics:
            self._download(pic, globalDict[self.blog.id], update)
            if update: update = False
        f = open(self.sourceFile, 'w',encoding="utf8")
        f.write(str(globalDict))
        f.close()

    def _mkdir(self) -> str:
        dir = os.path.join(self.topDir, self.blog.id)
        if not os.path.isdir(dir): os.mkdir(dir)
        return dir

    @property
    def isNew(self):
        return self.blog.id not in eval(open(self.sourceFile, 'r', encoding="utf8").read())


def main():
    todl = [("msashleyvee",["asian",'brunette','cute'],1.5)]
    # ('itslaurenroyce',['israeli','blonde','glamour'])

    # for photo in InstagramPhotoPickerByAvgMult(InstagramBlog('itslaurenroyce',['israeli','blonde','glamour']),20,1).pick():
    #    print(photo)
    for i in todl:
        print(i[0])
        blog = InstagramBlog(i[0], i[1])
        if len(i) == 3:
            picker = InstagramPhotoPickerByAvgMult(blog,avgMultiplyer=i[2])
        else:
            picker = InstagramPhotoPickerByAvgMult(blog)
        downloader = InstagramDownloader(blog, TOP_DIR, SOURCE_FILE,1000)
        blog.picker = picker
        blog.downloader = downloader
        blog.download()


def updateTest():
    gdict =  eval(open("pics.out", 'r',encoding="utf8").read())
    blog = InstagramBlog.fromGlobalDict("daniel_falach",gdict["daniel_falach"],TOP_DIR,SOURCE_FILE)
    blog.download(True)

def PicNumberTest():
    gdict = eval(open("pics.out", 'r', encoding="utf8").read())
    blog = InstagramBlog.fromGlobalDict("anatisan", gdict["anatisan"], TOP_DIR, SOURCE_FILE)
    print(blog.getUpdateAmount())

if __name__ == '__main__':
    main()
