# -*- coding: utf-8 -*-
import re
import sys
import MySQLdb
import urllib2
import urllib
import time
import threading
import threadpool
emoji_pattern = re.compile(
    u"(\ud83d[\ude00-\ude4f])|"  
    u"(\ud83c[\udf00-\uffff])|"  
    u"(\ud83d[\u0000-\uddff])|"  
    u"(\ud83d[\ude80-\udeff])|"  
    u"(\ud83c[\udde0-\uddff])"  
    "+", flags=re.UNICODE)
def remove_emoji(text):
    return emoji_pattern.sub(r'', text)#去除评论中的emoji表情，如果你的数据库使用utfmb4，可以直接return text
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
def SearchComment(page):#Mysql数据库默认用户名跟密码是root，数据库名为ithome，表名为comments，共有13个字段
  conn = MySQLdb.connect(host='localhost', user='root', passwd='root', port=3306, use_unicode=1, charset='utf8')
  cur = conn.cursor()
  conn.select_db('ithome')
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
      name=re.findall("(?<=</strong><strong class=\"nick\">"+ temp[0]+">).*(?=</a></strong>)",values)
      if(len(name)==0):
        name=re.findall(u"(?<=<strong class=\"nick\"><a title=\"软媒通行证数字ID："+id[0]+"\" target=\"_blank\" href=\"http://quan.ithome.com/user/"+id[0]+"\">).+?(?=</a></strong>)",values)
      content=re.findall("(?<=<div class=\"comm\"><p>).+?(?=</p>)",values)
      pri=re.findall("(?<=<a title=).+?(?=<span class=\"posandtime\">)",values)
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
      sqldata = (id[0],commentid[0],name[0],remove_emoji(content[0]), device,position,avator[0],int(favor[0], 10), int(against[0], 10),page,floor,sendtime,time.strftime('%Y-%m-%d',time.localtime()))
      conn.commit()
      major=floor
      temp=re.findall("class=\"gh\".+?(?=></span></div></div>)",values)
      if(len(temp)>0):
          for value in temp:
              try:
                  tem = re.findall("<a title=.*(?=><img class=)", value)
                  id = re.findall(u"(?<=<a title=\"软媒通行证数字ID：).+?(?=\")", value)
                  commentid = re.findall("(?<=<a id=\"agree).+?(?=\")", value)
                  name = re.findall("(?<=</strong><strong class=\"nick\">" + tem[0] + ">).*(?=</a></strong>)", value)
                  if (len(name) == 0):
                      name = re.findall(u"(?<=<strong class=\"nick\"><a title=\"软媒通行证数字ID：" + id[
                          0] + "\" target=\"_blank\" href=\"http://quan.ithome.com/user/" + id[
                                            0] + "\">).+?(?=</a></strong>)", value)
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
                  sqldata = (id[0], commentid[0], name[0],remove_emoji(content[0]), device, position, avator[0],
                             int(favor[0], 10), int(against[0], 10), page, floor, sendtime,
                             time.strftime('%Y-%m-%d  %H:%M:%S', time.localtime()))
                  conn.commit()
              except:
               continue
     except:
      continue
    i=i+1
  except:
   return
class threadsearch(threading.Thread):
    def __init__(self,que):
        threading.Thread.__init__(self)
        self.que = que
    def run(self):
        while True:
            if not self.que.empty():
                SearchComment(self.que.get())
            else:
                break
reload(sys)
sys.setdefaultencoding('utf-8')
queue=[]
#下面填入新闻的id号，从87777到318888左右
for i in range(238831,320000):
    queue.append(i)
pool = threadpool.ThreadPool(16)
requests = threadpool.makeRequests(SearchComment, queue)
[pool.putRequest(req) for req in requests]
pool.wait()
