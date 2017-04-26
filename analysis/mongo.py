from pymongo import MongoClient
import jieba
import jieba.analyse
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from collections import defaultdict
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.svm import LinearSVC



class CommentAnalysis(object):
    def __init__(self):
        self.comments = defaultdict(int)
        self.pushes = defaultdict(int)
        self.hates = defaultdict(int)
        self.init_from_mongo()

    def init_from_mongo(self):
        client = MongoClient('mongodb://localhost:27017/') 
        db = client.ptt
        posts = db.gossiping_38k 
        #print (posts.count())
        #print (posts.find_one())#dict       
        for post in posts.find():
            #print (post['author'])
            for comment in post['comments']:
                user = comment['user']
                self.comments[user] += 1
                if comment['score'] > 0:
                    self.pushes[user] += 1
                elif comment['score'] < 0:
                    self.hates[user] += 1
        client.close()

    def drawCommenter(self):
        sorted_cnts = [t[0] for t in sorted(self.comments.items(), key=lambda x: -x[1])][:100]
        print (sorted_cnts)
        y     = [self.comments[u] for u in sorted_cnts]
        y_pushes= [self.pushes[u] for u in sorted_cnts]
        y_hates =  [self.hates[u] for u in sorted_cnts]
        x = range(len(y))

        f, ax = plt.subplots(figsize=(10, 6))
        sns.set(style='whitegrid')
        sns.set_color_codes('pastel')
        sns.plt.plot(x, y       , label='Total comments', color='blue')
        sns.plt.plot(x, y_pushes, label='Total pushes'  , color='green')
        sns.plt.plot(x, y_hates , label='Total hates'   , color='red')

        ax.legend(ncol=2, loc='upper right', frameon=True)
        ax.set(ylabel='counts',
               xlabel='Rank',
               title ='Total comments')
        sns.despine(left=True, bottom=True)
        plt.show(f)

class WordAnalysis(object):
    def __init__(self):
        self.words = []
        self.scores = [] 
        self.c_words = []
        self.c_scores = [] 
        self.init_from_mongo()

        self.dvec   = DictVectorizer()
        self.c_dvec = DictVectorizer()
        self.svc   = LinearSVC()
        self.c_svc = LinearSVC()
        self.linearSVC_prediction()
        
        # top features for posts
        self.display_top_features(self.svc.coef_[0], self.dvec.get_feature_names(), 30)
        # top positive features for post
        self.display_top_features(self.svc.coef_[0], self.dvec.get_feature_names(), 30, select=lambda x: x)
        # top features for comments
        self.display_top_features(self.c_svc.coef_[0], self.c_dvec.get_feature_names(), 30)
        # top positive features for comments
        self.display_top_features(self.c_svc.coef_[0], self.c_dvec.get_feature_names(), 30, select=lambda x: x)



    def init_from_mongo(self):
        client = MongoClient('mongodb://localhost:27017/') 
        db = client.ptt
        posts = db.gossiping_38k 
        jieba.set_dictionary('extra_dict/dict.txt.big')
        jieba.analyse.set_stop_words("extra_dict/stop_words_cht.txt")   
        for post in posts.find():
            #For content
            d = defaultdict(int)
            content = post['content']
            if post['score'] != 0:
                for l in content.split('\n'):
                    if l:
                        for w in jieba.cut(l):
                            d[w] += 1
            if len(d) > 0:
                self.words.append(d)
                self.scores.append(1 if post['score'] > 0 else 0)
            #For comments
            for comment in post['comments']:
                l = comment['content'].strip()
                if l and comment['score'] != 0:
                    d = defaultdict(int)
                    for w in jieba.cut(l):
                        d[w] += 1
                    if len(d) > 0:
                        self.c_words.append(d)
                        self.c_scores.append(1 if comment['score'] > 0 else 0)

        client.close()   

    def linearSVC_prediction(self):
        tfidf = TfidfTransformer()
        X = tfidf.fit_transform(self.dvec.fit_transform(self.words))

        c_tfidf = TfidfTransformer()
        c_X = c_tfidf.fit_transform(self.c_dvec.fit_transform(self.c_words))

        self.svc = LinearSVC()
        self.svc.fit(X, self.scores)

        self.c_svc = LinearSVC()
        self.c_svc.fit(c_X, self.c_scores)

    def display_top_features(self,weights, names, top_n, select=abs):
        top_features = sorted(zip(weights, names), key=lambda x: select(x[0]), reverse=True)[:top_n]
        top_weights = [x[0] for x in top_features]
        top_names   = [x[1] for x in top_features]

        fig, ax = plt.subplots(figsize=(10,8))
        ind = np.arange(top_n)
        bars = ax.bar(ind, top_weights, color='blue', edgecolor='black')
        for bar, w in zip(bars, top_weights):
            if w < 0:
                bar.set_facecolor('red')

        width = 0.30
        ax.set_xticks(ind + width)
        ax.set_xticklabels(top_names, rotation=45, fontsize=12, fontdict={'fontname': 'Droid Sans Fallback', 'fontsize':12})

        plt.show(fig)


if __name__ == '__main__':
    #PA = CommentAnalysis()
    #PA.drawCommenter()
    WA = WordAnalysis()



