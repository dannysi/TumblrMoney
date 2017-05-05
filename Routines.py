import os
import random
from copy import deepcopy
from typing import List

from InstagramBlog import InstagramBlog
from TumblrBlog import TumblrBlog
from TumblrDefs import TOP_DIR, SOURCE_FILE


class ReblogRoutine(object):
    blogsFrom = [] #type: List(TumblrBlog)
    blogTo = None #type: TumblrBlog
    history = set()
    def __init__(self,blogsFrom:List[TumblrBlog],blogTo: TumblrBlog,picsPerReblog = None):
        self.blogsFrom = blogsFrom #type: List(TumblrBlog)
        self.blogTo = blogTo #type: TumblrBlog
        self.picsPerReblog = picsPerReblog

    def go(self):
        lastPosts = set() #type: set(TumblrPost)
        if len(self.history) >= 5000:
            self.history.clear()
        for blogFrom in self.blogsFrom:
            lastPosts.add((blogFrom.getLastPost(),blogFrom))
        if self.picsPerReblog != None:
            choice = random.sample(lastPosts,self.picsPerReblog)
        else :
            choice = lastPosts
        for post in choice:
            if post[0].id in self.history:
                print("Post in history",post[0].id)
                continue
            response = self.blogTo.reblog(post[0])
            print(response,post[1].name)
            self.history.add(post[0].id)


class FillQueueRoutine(object):
    def __init__(self,blogs):
        self.blogs = blogs #type: List[TumblrBlog]

    def go(self):
        for blog in self.blogs:
            print("Posting to blog",blog.name)
            qSize = blog.getQueueSize()
            if  qSize > 50:
                continue
            qFill = random.randint(240,290) - qSize
            blog.fillQueue(qFill)


class UpdateBlogRoutine(object):
    def __init__(self,path):
        self.path = path

    def go(self):
        print("-I- Starting random update routine")
        gdict = eval(open(self.path, 'r', encoding="utf8").read())
        dir = random.choice(list(gdict))
        if len(gdict[dir]['files']) < 100:
            blog = InstagramBlog.fromGlobalDict(dir,gdict[dir],TOP_DIR,SOURCE_FILE)
            if blog.hasNewBatch():
                print("-I- Updating dir:",dir)
                blog.download(True)
            else: print("-I- Not enough new pics for:",dir)
        else:print("-I- Dir size",dir,"is too big:",len(gdict[dir]['files']))

class UpdateDictRoutine(object):
    def __init__(self,dictFile):
        self.path = dictFile

    def go(self):
        print("-I- Starting to update dict routine")
        gdict = eval(open(self.path, 'r', encoding="utf8").read())
        for dir in gdict:
            files = deepcopy(gdict[dir]['files'])
            for f in gdict[dir]['files']:
                f2 = os.path.join(gdict[dir]['directory'],f)
                if not os.path.isfile(f2):
                    print(f2,"doesn't exist")
                    del files[f]
            gdict[dir]['files'] = files
        open(self.path, 'w', encoding="utf8").write(str(gdict))

if __name__ == '__main__':
    UpdateDictRoutine("pics.out").go()