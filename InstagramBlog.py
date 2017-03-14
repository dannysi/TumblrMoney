from abc import ABCMeta, abstractmethod

#TODO implement unimplemented methods
class InstagramPic:
    def __init__(self,path,likes,description,tags):
        self.path = path
        self.likes = likes
        self.description = self.description
        self.tags = self.tags

    @classmethod
    def fromInstagramApi(cls,dic):
        #TODO parse dictionary we get from the instagram api per pic
        path = ""
        likes = ""
        description = ""
        tags = ""
        return cls(path,likes,description,tags)

    def extractDescription(self,desc):
        pass

    def __cmp__(self,other):
        return other.likes - self.likes

class InstagramBlog:

    id = None
    path = None
    tags = []

    def __init__(self,path,tags,id):
        self.id = id
        self.path = path
        self.tags = tags

    def getNextPics(self,NumberOfPics):
        pass

    def getBlogDescription(self):
        pass

    def getBlogTags(self):
        pass

class InstagramPhotoPicker:
    def __init__(self, blog, batch):
        self.blog = blog
        self.batch = batch

    @abstractmethod
    def pick(self):
        raise NotImplementedError()


class InstagramPhotoPickerByAvgMult(InstagramPhotoPicker):
    def __init__(self,blog,batch,avgMultiplyer):
        super(blog,batch)
        self.avgMultiplyer = avgMultiplyer

    def pick(self):
        pics = self.blog.getNextPics(self.batch)
        avg = sum(pic.likes for pic in pics) * self.avgMultiplyrt / len(pics)
        return [x for x in pics if x.likes>=avg]
