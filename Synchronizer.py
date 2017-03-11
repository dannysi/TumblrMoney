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


class Synchronizer:
    q = queue.PriorityQueue()
    cond = threading.Condition()
    def __init__(self):
        pass 
    def sign(self,function,args,startTime,repeatEvery):
        self.q.put((startTime,function,args,repeatEvery))
        self.cond.notify_all()

    def run(self):
        while True:
            while self.q.queue[0][0]<datetime.datetime.now():
                task = self.q.get()
                thread = FuncThread(task[1],task[2])
                thread.start()
                newTask = (task[0]+task[3],task[1],task[2],task[3])
                self.q.put(newTask)
            self.cond.wait(self.q.queue[0][0]-datetime.datetime.now())


