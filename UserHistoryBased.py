#!/usr/bin/env python
# coding: utf-8

# In[1]:


import json
import ast

from pyspark.sql import Row
from pyspark.sql import SparkSession 


# In[2]:


spark = SparkSession        .builder        .enableHiveSupport()        .getOrCreate()
#spark


# In[3]:


df_sopr = spark.read.table('prod.mles_sopr')
df_sopr.printSchema()


# In[1]:


rdd_sopr = df_sopr             .select("user_id", "offer_id", 'page_type', 'event_type')             .dropDuplicates()             .rdd


# In[5]:


#rdd_tuple_sopr = rdd_sopr.map(lambda x: (x['user_id'], x['offer_id']))
#rdd_tuple_sopr.take(1)


# In[6]:


#rdd_tuple_sopr_grouped = rdd_tuple_sopr.groupByKey()
#arr = rdd_tuple_sopr_grouped.collect()


# In[ ]:


import datetime
DICT_W_FOR_PAGE_TYPE = {"Card" : 3,
                        "CardJK" : 2,
                        "Listing" : 1,
                        "ListingFavorites" : 5}

DICT_W_FOR_EVENT_TYPE = {"card_show" : 3,
                        "phone_show" : 10}

#разделение на 9 частей по времени
def lambdaForArr(x):
    return (x['user_id'], [x['offer_id'], 
                           DICT_W_FOR_PAGE_TYPE[x['page_type']] * DICT_W_FOR_EVENT_TYPE[x['event_type']]])


# In[ ]:


arr = rdd_sopr.map(lambda x: lambdaForArr(x))           .groupByKey()           .randomSplit([1, 500])[0].collect()


# In[7]:


import numpy as np
from scipy.sparse import csr_matrix

def get_mtrx():
    indptr = [0]
    indices = []
    data = []

    for i in arr:
        if i[1]:
            for j in i[1]:
                indices.append(j[0])
                data.append(j[1])
            indptr.append(len(indices))
    
    return csr_matrix((data, indices, indptr))


# In[8]:


#import numpy as np
#data = np.ones(len(indices))


# In[9]:


#from scipy.sparse import csr_matrix

#mtrx = csr_matrix((data, indices, indptr))


# In[10]:


mtrx = get_mtrx()


# In[11]:


from scipy.sparse import csc_matrix
from scipy.sparse import dia_matrix
import numpy as np
import math

def distEuclid(mtrx):
    test = (mtrx).dot(csr_matrix.transpose(mtrx))
    data = test.diagonal().reshape((1, test.shape[0])).repeat(2 * mtrx.shape[0] + 1, axis=0)
    offsets = np.arange(-mtrx.shape[0], mtrx.shape[0] + 1)
    test_dia = dia_matrix((data, offsets), shape = test.shape)
    
    data = None
    offsets = None
    test = (test_dia + test_dia.transpose() - 2 * test).sqrt()
    
    return test


# In[12]:


def distEuclidForUser(mtrx, user):
    userRow = mtrx.getrow(user)
    
    x2 = np.ones(mtrx.shape[0]) * int(userRow.dot(userRow.transpose())[0,0])
    y2 = mtrx.dot(mtrx.transpose()).diagonal()
    _2xy = 2 * userRow.dot(mtrx.transpose())

    return np.array(np.sqrt(x2 + y2 - _2xy))[0]


# In[11]:


def distEuclidForAnnoun(mtrx, announ):
    announCol = mtrx.getcol(announ)
    
    x2 = np.ones(mtrx.shape[1]) * int((announCol.transpose()).dot(announCol)[0,0])
    y2 = (mtrx.transpose()).dot(mtrx).diagonal()
    _2xy = 2 * (announCol.transpose()).dot(mtrx)
    
    return np.array(np.sqrt(x2 + y2 - _2xy))[0]


# In[26]:


def distCosForUser(mtrx, user):
    userRow = mtrx.getrow(user)

    x = math.sqrt(int(userRow.dot(userRow.transpose())[0,0]))
    y = np.sqrt(mtrx.dot(mtrx.transpose()).diagonal())*x
    xy = userRow.dot(mtrx.transpose())

    return (xy.multiply(1/y)).toarray()[0]


# In[35]:


def distCosForAnnoun(mtrx, announ):
    announCol = mtrx.getcol(announ)

    x = math.sqrt(int((announCol.transpose()).dot(announCol)[0,0]))
    y = np.sqrt((mtrx.transpose()).dot(mtrx).diagonal())*x
    xy = (announCol.transpose()).dot(mtrx)

    return (xy.multiply(1/y)).toarray()[0]


# In[46]:


def distCos(mtrx):
    test = mtrx.dot(mtrx.transpose())

    x = np.sqrt(test.diagonal())
    x = csr_matrix(1/x)

    return (x.transpose()).dot(x).multiply(test)


# In[14]:


def distPirson(mtrx):
    rowForAvg = (mtrx.sum(axis=1) / mtrx.shape[0]).ravel().tolist()[0]
    #т.к. в rowForAvg значения порядка е-4 => distPirson = distCos
    return distCos(user)


# In[15]:


#distCos()


# In[19]:


OURUSER = 10668 # 10782 3126 13865

#distance = distEuclid()


# In[17]:


'''distForOurUser = []
for i in range(mtrx.shape[0]):
    distForOurUser.append(mtrx.getrow(i).multiply(mtrx.getrow(i)).sum())
'''


# In[13]:


from scipy.sparse import find


# In[19]:


#A.prune()


# In[20]:


def get_u_r(r):
    u_r = find(mtrx.getrow(r))[1]
    return u_r


# In[21]:


#find(mtrx[find((distance.getrow(OURUSER) < ALPHA))[1]])[1]#просмотры от (U(u0)) \in R


# In[22]:


#find((distance.getrow(OURUSER) < ALPHA))[1].size#U(u0)


# In[23]:


#r = 107547678
#find(mtrx.getcol(r))[0]#U(r)


# In[27]:


#U_u0 = distCosForUser(OURUSER)


# In[36]:


#U_u0[:OURUSER].max()


# In[49]:


def recomCosUserBased(mtrx,user, k):
    recom = [(0, 0) for i in range(k)]
    U_u0 = distCosForUser(mtrx, user)
    ALPHACOS = 0.15
    a = find(U_u0 > ALPHACOS)[1]

    for r in find(mtrx[find((U_u0 > ALPHACOS))[1]])[1]:
        t = np.union1d(a, find(mtrx.getcol(r))[0]).size
        if (t != 0):
            b = np.intersect1d(a, find(mtrx.getcol(r))[0]).size/t
            recom.append((r, b))
            recom.sort(key=lambda x: x[1], reverse=True)
            recom = recom[:k]
    return recom


# In[50]:


def recomEuclidUserBased(mtrx,user, k):
    recom = [(0, 0) for i in range(k)]
    ALPHAED = 1.5
    U_u0 = distEuclidForUser(mtrx, user)
    a = find(U_u0 < ALPHAED)[1]

    for r in find(mtrx[find((U_u0 < ALPHAED))[1]])[1]:
        b = np.intersect1d(a, find(mtrx.getcol(r))[0]).size/np.union1d(a, find(mtrx.getcol(r))[0]).size
        recom.append((r, b))
        recom.sort(key = takeSecond)
        recom = recom[:k]
    return recom


# In[14]:


mtrx.getrow(13853)


# In[18]:


find(mtrx.sum(axis = 1) > 10)


# In[20]:


def recomEuclidUserHistoryBased(mtrx,user, k):
    recom = [(0, 0) for i in range(k)]
    ALPHAED = 9.1
    userRow = find(mtrx.getrow(user))[1]

    for r in userRow:
        a = distEuclidForAnnoun(mtrx, r)
        ind = np.setdiff1d(find(a < ALPHAED)[1], userRow)
        data = a[ind]
        add_recom = [(ind[i], data[i]) for i in range(len(data))]
        recom = recom + add_recom
        recom.sort(key=lambda x: x[1])
        recom = recom[:k]
    return recom


# In[26]:


def recomCosUserHistoryBased(mtrx,user, k):
    recom = [(0, 0) for i in range(k)]
    ALPHACOS = 0.7
    userRow = find(mtrx.getrow(user))[1]

    for r in userRow:
        a = distCosForAnnoun(mtrx, r)
        ind = np.setdiff1d(find(a > ALPHACOS)[1], userRow)
        data = a[ind]
        add_recom = [(ind[i], data[i]) for i in range(len(data))]
        recom = recom + add_recom
        recom.sort(key=lambda x: x[1], reverse=True)
        recom = recom[:k]
    return recom

