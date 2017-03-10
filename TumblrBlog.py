import pytumblr
#TODO implement unimplemented methods
#TODO test dump/reload mechanics

class TumblrBlog:
    def __init__(self,name,source,client=None):
        self.client = client
        self.name = name

    def queue(self,picture,**kwargs):
        #TODO think of a more pretty design so we can remove this if
        if kwargs["picSource"] == "link":
            response = self.client.create_photo(self.name,
                                           state="queue",
                                           tags=kwargs["tags"],
                                           format="markdown",
                                           source = picture,
                                           caption=kwargs["caption"])
        else: response = self.client.create_photo(self.name,
                                           state="queue",
                                           tags=kwargs["tags"],
                                           format="markdown",
                                           data = picture,
                                           caption=kwargs["caption"])
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
    sourceTypeEnum = ["dir","set-file"]
    def __init__(self,sourceType,path):
        if sourceType not in self.descEnum:
            raise "wrong desc"
        #TODO check if path exists and is set file or dicectory
        self.sourceType = sourceType
        self.path = path

    def getPics(self,amount):
        pass





