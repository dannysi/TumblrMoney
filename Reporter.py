from typing import *

class Reporter(object):
    def __init__(self ,file: str):
        self.file = file
        self.db ,self.total = self._analyze(eval(open(file, 'r',encoding="utf8").read()))  # type: (dict(str,(int,int)),(int,int))

    def _analyze(self ,gdict: dict,includeEmpty: bool = False) -> (Dict[str,Tuple[int,int]],(int,int)):
        db = dict()  # type: dict(str,(int,int))
        total = (0 ,0)
        for dir in gdict:
            fileCount = len(gdict[dir]['files'])
            if not includeEmpty and fileCount == 0 :
                continue
            for tag in gdict[dir]['tags']:
                if tag not in db:
                    db[tag] = (0 ,0)
                db[tag] = (db[tag][0 ] +1 ,db[tag][1 ] +fileCount)
            total = total[0 ] +1 ,total[1 ] +fileCount
        return db ,total


    def reportAll(self) -> None:
        print("Total", "\t", self.total[0], "\t", self.total[1])
        report = list(self.db)
        report.sort(key=lambda x:-self.db[x][0])
        for tag in report:
            print(tag ,"\t" ,self.db[tag][0] ,"\t" ,self.db[tag][1])

    def reportTag(self ,tag: str) -> (int ,int):
        return self.db[tag]
    def reportTotal(self) ->(int, int):
        return self.total
def test():
    reporter = Reporter(r'pics.out')
    reporter.reportAll()

if __name__ == "__main__":
    test()