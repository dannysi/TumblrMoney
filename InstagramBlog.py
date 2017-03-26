from abc import ABCMeta, abstractmethod

#TODO implement unimplemented methods
from queue import PriorityQueue

from InstagramScrapper.Scrapper import InstagramScraper


class InstagramPic(object):
    def __init__(self,id,path,type,creation,likes,description,tags):
        self.id = id
        self.path = path
        self.likes = int(likes)
        self.description = description
        self.tags = tags
        self.creation = creation
        self.type = type

    def __repr__(self):
        return str(self.path)
    @classmethod
    def fromInstagramApi(cls,dic):
        id = dic['id']
        #TODO test for multiple images
        path = dic['images']['standard_resolution']['url']
        likes = dic['likes']['count']
        if 'caption' in dic and dic['caption'] != None and 'text' in dic['caption'] :
            description,tags = cls.extractDescription(dic['caption']['text'])
        else : description , tags = None , None
        #TODO should be datetime
        creation = dic['created_time']
        type = dic['type']
        return cls(id,path,type,creation,likes,description,tags)

    @classmethod
    def extractDescription(cls,desc):
        words = desc.split(" ")
        tags = []
        desc = []
        for word in words:
            if len(word) == 0 : continue
            if word[0] == "#" : tags.append(word)
            else: desc.append(word)
        return " ".join(desc),tags


    def __cmp__(self,other):
        if other.likes < self.likes: return -1
        elif other.likes > self.likes: return 1
        else: return 0

    def __lt__(self,other):
        return other.likes < self.likes


class InstagramBlog(object):

    id = None
    tags = []
    lastDownloaded = None
    picker = None

    def __init__(self, id, tags=None):
        if tags is None:
            tags = []
        self.id = id
        self.tags = tags


    def getNextPics(self,NumberOfPics):
        for batch in InstagramScraper(self.id).getBatchOfPhotos(NumberOfPics):
            ans =  [InstagramPic.fromInstagramApi(item) for item in batch]
            yield ans



    def getBlogDescription(self):
        pass

    def getBlogTags(self):
        pass


class InstagramPhotoPicker(object):
    def __init__(self,blog,batch):
        self.blog = blog
        self.batch = batch

    def pick(self):
        for pics in self.blog.getNextPics(self.batch):
            filtered = [pic for pic in pics if pic.type == 'image']
            yield self._pick(filtered)

    @abstractmethod
    def _pick(self,pics):
        pass



class InstagramPhotoPickerByAvgMult(InstagramPhotoPicker):
    def __init__(self,blog,batch = 50,avgMultiplyer = 1):
        InstagramPhotoPicker.__init__(self,blog,batch)
        self.avgMultiplyer = avgMultiplyer

    def _pick(self,pics):
        avg = sum(pic.likes for pic in pics) * self.avgMultiplyer / len(pics)
        return  [x for x in pics if x.likes>=avg]


class InstagramPhotoPickerByTop(InstagramPhotoPicker):
    def __init__(self,blog,batch = 50,topPics = 1):
        InstagramPhotoPicker.__init__(self, blog, batch)
        self.topPics = topPics

    def _pick(self,pics):
        q = PriorityQueue()
        for pic in pics: q.put(pic)
        for p in q.queue:print(p.likes)
        return [q.get() for i in range(self.topPics)]
