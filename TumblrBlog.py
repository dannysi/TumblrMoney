from abc import ABCMeta, abstractmethod


class TumblrBlog:
    def __init__(self,name,client=None):
        self.client = client
        self.name = name

    def queue(self,picture,**kwargs):
        pass
    def getQueueSize(self):
        pass
    def post(self,picture,**kwargs):
        pass
    def getLastPost(self):
        pass
    def getNextPosts(self,numberOfPosts):
        pass


class InstagramPic:
    def __init__(self,path,likes,description,tags):
        self.path = path
        self.likes = likes
        self.description,self.tags = self.extractDescription(description)
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

#TODO make abstract
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





