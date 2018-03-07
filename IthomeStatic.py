# -*- coding: utf-8 -*-
import re
import sys
import MySQLdb
import urllib2
import urllib
import time
import json
import threading
import threadpool
def ConnectMySql():#在这里改成你的MySql连接信息
    return MySQLdb.connect(host='localhost', user='root', passwd='545269649', port=3306, charset='utf8')
emoji_pattern = re.compile(
    u"(\ud83d[\ude00-\ude4f])|" 
    u"(\ud83c[\udf00-\uffff])|"  
    u"(\ud83d[\u0000-\uddff])|"  
    u"(\ud83d[\ude80-\udeff])|"  
    u"(\ud83c[\udde0-\uddff])" 
    "+", flags=re.UNICODE)
database='ithome'
def remove_emoji(text):
    return emoji_pattern.sub(r'', text)
def GetUrl(url):
 try:
  handler=urllib2.HTTPCookieProcessor()
  opener=urllib2.build_opener(handler)
  request = urllib2.Request(url)
  response_data = opener.open(request)
  result = response_data.read()
  return result
 except:
  return
def PostUrl(url,post_data):
 try:
  handler=urllib2.HTTPCookieProcessor()
  opener=urllib2.build_opener(handler)
  post_data_urlencode = urllib.urlencode(post_data)
  request = urllib2.Request(url = url,data =post_data_urlencode)
  response_data=opener.open(request)
  result = response_data.read()
  return result
 except:
  return
def gethash(url):
    result=GetUrl(url)
    if result is None:
        return
    hash=re.findall("(?<=id=\"hash\" value=\").+?(?=\")",result)
    return hash[0]
def SearchComment(page):
  SearchHotComment(page)
  conn = ConnectMySql()
  cur = conn.cursor()
  conn.select_db(database)
  hash=gethash("https://dyn.ithome.com/comment/"+str(page))
  if hash is None:
      return
  i=1
  url = "https://dyn.ithome.com/ithome/getajaxdata.aspx"
  data = {
    'newsID': str(page),
    'hash':hash,
    'type':'commentpage',
    'page':str(i),
    'order':'false'
    }
  result=PostUrl(url,data)
  if(result is None):
   return
  result=result.decode('utf-8')
  comments=re.findall("(?<=<li class=\"entry\">).+?(?=</li>)",result)
  try:
   while(comments[0]):
    data = {
    'newsID': str(page),
    'hash':hash,
    'type':'commentpage',
    'page':str(i),
    'order':'false'
    }
    result=PostUrl(url,data)
    if(result is None):
     return
    result=result.decode('utf-8')
    comments=re.findall("(?<=<li class=\"entry\">).+?(?=\"></div></div></li>)",result)
    cnt=len(comments)+1
    for values in comments:
     try:
      temp = re.findall("<a title=.*(?=><img class=)", values)
      id=re.findall(u"(?<=<a title=\"软媒通行证数字ID：).+?(?=\")", values)
      commentid=re.findall("(?<=<a id=\"agree).+?(?=\")",values)
      name=re.findall("(?<=</strong><div class=\"nmp\"><span class=\"nick\">"+ temp[0]+">).+?(?=</a></span>)",values)
      if(len(name)==0):
        name=re.findall(u"(?<=<span class=\"nick\"><a title=\"软媒通行证数字ID："+id[0]+"\" target=\"_blank\" href=\"http://quan.ithome.com/user/"+id[0]+"\">).+?(?=</a></span>)",values)
      content=re.findall("(?<=<div class=\"comm\"><p>).+?(?=</p>)",values)
      pri = re.findall("(?<=<a title=).+?(?=<span class=\"posandtime\">)", values)
      device = re.findall("(?<=ithome/download/\">).+?(?=</a></span>)", pri[0])
      position=re.findall(u"(?<=class=\"posandtime\">IT之家).+?(?=网友)",values)
      avator=re.findall("(?<='\" src=\"//).+?(?=\")",values)
      favor=re.findall(u"(?<=>支持\().+?(?=\))",values)
      against = re.findall(u"(?<=>反对\().+?(?=\))", values)
      floor= re.findall(u"(?<=class=\"p_floor\">).+?(?=楼)", values)
      sendtime=re.findall(u"(?<=&nbsp;).+?(?=</span>)", values)
      sql = "insert into comments VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
      if(len(device)>0):
       device=device[0]
      else:
        device="null"
      if(len(floor)>0):
        floor=floor[0]
      else:
        floor=str(cnt-1)
      cnt = cnt - 1
      if(len(position)>0):
        position=position[0]
      else:
        position="null"
      if(len(sendtime)>0):
          sendtime=sendtime[0]
      else:
          sendtime="null"
      sqldata = (id[0],commentid[0],name[0],content[0], device,position,avator[0],int(favor[0], 10), int(against[0], 10),page,floor,sendtime,time.strftime('%Y-%m-%d  %H:%M:%S',time.localtime()))
      cur.execute(sql, sqldata)
      conn.commit()
      major=floor
      temp=re.findall("class=\"gh\".+?(?=></span></div></div>)",values)
      if(len(temp)>0):
          for value in temp:
              try:
                  tem = re.findall("<a title=.*(?=><img class=)", value)
                  id = re.findall(u"(?<=<a title=\"软媒通行证数字ID：).+?(?=\")", value)
                  commentid = re.findall("(?<=<a id=\"agree).+?(?=\")", value)
                  name = re.findall("(?<=</strong><div class=\"nmp\"><span class=\"nick\">" + tem[0] + ">).+?(?=</a></span>)", value)
                  if (len(name) == 0):
                      name = re.findall(u"(?<=<span class=\"nick\"><a title=\"软媒通行证数字ID：" + id[
                          0] + "\" target=\"_blank\" href=\"http://quan.ithome.com/user/" + id[
                                            0] + "\">).+?(?=</a></span>)", value)
                  content = re.findall("(?<=re_comm\"><p>).+?(?=</p>)", value)
                  pri = re.findall("(?<=<a title=).+?(?=<span class=\"posandtime\">)", value)
                  device = re.findall("(?<=ithome/download/\">).+?(?=</a></span>)", pri[0])
                  position = re.findall(u"(?<=class=\"posandtime\">IT之家).+?(?=网友)", value)
                  avator = re.findall("(?<='\" src=\"//).+?(?=\")", value)
                  favor = re.findall(u"(?<=>支持\().+?(?=\))", value)
                  against = re.findall(u"(?<=>反对\().+?(?=\))", value)
                  floor = re.findall(u"(?<=class=\"p_floor\">).+?(?=#)", value)
                  sendtime = re.findall(u"(?<=&nbsp;).+?(?=</span>)", values)
                  sql = "insert into comments VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                  if (len(device) > 0):
                      device = device[0]
                  else:
                      device = "null"
                  if (len(floor) > 0):
                      floor =major+"#"+floor[0]
                  else:
                      floor = "null"
                  if (len(position) > 0):
                      position = position[0]
                  else:
                      position = "null"
                  if (len(sendtime) > 0):
                      sendtime = sendtime[0]
                  else:
                      sendtime = "null"
                  sqldata = (id[0], commentid[0], name[0],content[0], device, position, avator[0],
                             int(favor[0], 10), int(against[0], 10), page, floor, sendtime,
                             time.strftime('%Y-%m-%d  %H:%M:%S', time.localtime()))
                  cur.execute(sql, sqldata)
                  conn.commit()
              except:
               continue
     except:
      continue
    i=i+1
  except:
   return
def SearchHotComment(page):
    conn = ConnectMySql()
    cur = conn.cursor()
    conn.select_db(database)
    db=True
    pid=1
    while(db):
        url = "https://dyn.ithome.com/ithome/getajaxdata.aspx"
        data = {
        'newsID': str(page),
        'pid':str(pid),
        'type':'hotcomment'
        }
        result=PostUrl(url,data)
        if(result is None):
         return
        result=result.decode('utf-8')
        jsondata=json.loads(result)
        db=jsondata['db']
        result=jsondata['html']
        comments=re.findall("(?<=<li class=\"entry\").+?(?=</div></div></li>)",result)
        for values in comments:
         try:
          id=re.findall(u"(?<=<a title=\"软媒通行证数字ID：).+?(?=\")", values)[0]
          name = re.findall(u"(?<=<span class=\"nick\"><a title=\"软媒通行证数字ID："+id+"\" target=\"_blank\" href=\"http://quan.ithome.com/user/"+id+"\">).+?(?=</a></span>)", values)
          sql = "insert into hotcomment VALUES (%s)"%('\''+name[0]+'\'')
          cur.execute(sql)
          conn.commit()
         except:
          continue
        pid=pid+1
    return
class threadsearch(threading.Thread):
    def __init__(self,que):
        threading.Thread.__init__(self)
        self.que = que
    def run(self):
        while True:
            if not self.que.empty():
                id=self.que.get()
                SearchComment(id)
            else:
                break
reload(sys)
sys.setdefaultencoding('utf-8')
queue=[]
for i in range(221111,350000):#这里改成你要爬的文章范围，从网页的url上获取
    queue.append(i)
pool = threadpool.ThreadPool(8)#使用的线程数，推荐默认值
requests = threadpool.makeRequests(SearchComment, queue)
[pool.putRequest(req) for req in requests]
pool.wait()
