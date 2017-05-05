import queue
import threading
import datetime
import time

class FuncThread(threading.Thread):
    def __init__(self,func,args):
        threading.Thread.__init__(self)
        self.func = func
        self.args = args
    def run(self):
        if self.args == None:
            self.func()
        elif type(self.args) != tuple:
            self.func(self.args)
        else:
            self.func(*self.args)


class Task(object):
    def __init__(self,function,args,startTime,repeatEvery,runInThread=False):
        self.function = function
        self.args = args
        self.startTime = startTime
        self.repeatEvery = repeatEvery
        self.runInThread = runInThread
    def __cmp__(self,other):
        return self.startTime.timestamp() - other.startTime.timestamp()
    def __lt__(self,other):
        if other.startTime.timestamp() - self.startTime.timestamp()>0:return True
        else: return False
    def accend(self):
        self.startTime += self.repeatEvery


class Synchronizer(object):
    q = queue.PriorityQueue()
    cond = threading.Condition()

    def sign(self,task):
        self.q.put(task)
#        self.cond.notify_all()

    def run(self):
        while True:
            while self.q.queue[0].startTime<=datetime.datetime.now():
                task = self.q.get()
                thread = FuncThread(task.function,task.args)
                if task.runInThread: thread.start()
                else : thread.run()
                task.accend()
                self.q.put(task)
            #print("current",datetime.datetime.now(),"next",self.q.queue[0].startTime)
            #TODO max 2 hours
            if self.q.queue[0].startTime>datetime.datetime.now():
                print("-I- Next task in ",self.q.queue[0].startTime)
                time.sleep(min((self.q.queue[0].startTime-datetime.datetime.now()).seconds+1,2*60*60))
 #               self.cond.wait(self.q.queue[0][0]-datetime.datetime.now())

def test():
    def foo():
        print("XXX",datetime.datetime.now())
    def goo():
        print("YYY",datetime.datetime.now())
    sync = Synchronizer()
    sync.sign(Task(foo,None,datetime.datetime.now(),datetime.timedelta(seconds=5),False))
    sync.sign(Task(goo,None,datetime.datetime.now(),datetime.timedelta(seconds=3),False))
    sync.run()
