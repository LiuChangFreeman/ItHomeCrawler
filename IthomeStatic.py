# -*- coding: utf-8 -*-
import re
import os
import MySQLdb
import requests
from bs4 import BeautifulSoup
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
def remove_emoji(text):
    return emoji_pattern.sub(r'', text)
path = "D:/Crawler/ithome/data/"
database='Ithome'
def gethash(url):
    r=requests.get(url)
    result=r.text
    if result is None:
        return
    hash=re.findall("(?<=id=\"hash\" value=\").+?(?=\")",result)
    return hash[0]
def SearchComment(page):
  if not os.path.exists(path+ str(page)):
      os.mkdir(path+ str(page))
  SearchHotComment(page)
  count = 0
  conn = ConnectMySql()
  cur = conn.cursor()
  cur.execute('SET NAMES utf8mb4')
  cur.execute("SET CHARACTER SET utf8mb4")
  cur.execute("SET character_set_connection=utf8mb4")
  conn.select_db(database)
  hash=gethash("https://dyn.Ithome.com/comment/"+str(page))
  if hash is None:
      return
  i=1
  url = "https://dyn.Ithome.com/Ithome/getajaxdata.aspx"
  data = {
    'newsID': str(page),
    'hash':hash,
    'type':'commentpage',
    'page':str(i),
    'order':'false'
    }
  r = requests.post(url,data=data)
  result=r.text
  if(result is None):
   return
  comments=re.findall("<li class=\"entry\">.+?</li>",result)
  try:
   while(len(comments)>0):
    data = {
    'newsID': str(page),
    'hash':hash,
    'type':'commentpage',
    'page':str(i),
    'order':'false'
    }
    r = requests.post(url, data=data)
    result = r.text
    with open(path+ str(page)+"/"+str(page)+"-{}.html".format(str(i)),"w") as file:
        file.write(result.encode("utf-8"))
    if(result is None):
     return
    comments = re.findall("<li class=\"entry\">.+?</li>", result)
    for comment in comments:
     try:
      count+=1
      if count==305:
          pass
      comment=BeautifulSoup(comment)
      id=comment.select_one(".nick").find("a")["title"][10:]
      commentid=comment.select_one(".comm_reply").select_one(".s")["id"].replace("agree","")
      name=comment.select_one(".nick").find("a").text
      content=comment.select_one(".comm").find("p").text
      nmp=comment.select_one(".nmp")
      device="null"
      position="null"
      sendtime="null"
      if len(nmp.find_all("span"))>2:
        device = comment.select_one(".nmp").find_all("span")[1].find("a").text
      pri = comment.select_one(".posandtime")
      if pri!=None:
        pri = pri.text
        position=re.findall(u"(?<=IT之家).+?(?=网友)",pri)
        if len(position)>0:
            position = position[0]
        else:
            position="null"
        sendtime=pri[len(pri)-18:]
      avator=comment.select_one(".headerimage")["src"][2:]
      favor=comment.select_one(".comm_reply").select_one(".s").text
      favor=re.findall(u"(?<=支持\()(.+?)(?=\))",favor)[0]
      against = comment.select_one(".comm_reply").select_one(".a").text
      against = re.findall(u"(?<=反对\()(.+?)(?=\))", against)[0]
      floor= comment.select_one(".p_floor").text.replace(u"楼","")
      sql = "insert into comments VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
      sqldata = (id,commentid,name,remove_emoji(content),device,position,avator,int(favor, 10), int(against, 10),page,floor,sendtime,time.strftime('%Y-%m-%d  %H:%M:%S',time.localtime()))
      cur.execute(sql, sqldata)
      conn.commit()
      major=floor
      reply=comment.select_one(".reply")
      if(reply!=None):
          if(major=="248"):
              pass
          details=reply.select(".gh")
          for value in details:
              try:
                  id = value.select_one(".nick").find("a")["title"][10:]
                  commentid = value.select_one(".comm_reply").select_one(".s")["id"].replace("agree", "")
                  name = value.select_one(".nick").find("a").text
                  content = value.select_one(".re_comm").find("p").text
                  nmp = value.select_one(".nmp")
                  device = "null"
                  position = "null"
                  sendtime = "null"
                  if len(nmp.find_all("span")) > 2:
                      device = value.select_one(".nmp").find_all("span")[1].find("a").text
                  pri = value.select_one(".posandtime")
                  if pri != None:
                      pri = pri.text
                      position = re.findall(u"(?<=IT之家).+?(?=网友)", pri)
                      if len(position) > 0:
                          position = position[0]
                      else:
                          position = "null"
                      sendtime = pri[len(pri) - 18:]
                  avator = value.select_one(".headerimage")["src"][2:]
                  favor = value.select_one(".comm_reply").select_one(".s").text
                  favor = re.findall(u"(?<=支持\()(.+?)(?=\))", favor)[0]
                  against = value.select_one(".comm_reply").select_one(".a").text
                  against = re.findall(u"(?<=反对\()(.+?)(?=\))", against)[0]
                  floor = major+"|"+value.select_one(".p_floor").text.replace(u"楼", "")
                  sql = "insert into comments VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                  sqldata = (id, commentid, name,remove_emoji(content), device, position, avator,
                             int(favor, 10), int(against, 10), page, floor, sendtime,
                             time.strftime('%Y-%m-%d  %H:%M:%S', time.localtime()))
                  cur.execute(sql, sqldata)
                  conn.commit()
              except:
               print(major)
               continue
     except:
      print(count)
      continue
    i=i+1
  except:
   print(page)
   return
def SearchHotComment(page):
    conn = ConnectMySql()
    cur = conn.cursor()
    conn.select_db(database)
    db=True
    pid=1
    while(db):
        url = "https://dyn.Ithome.com/Ithome/getajaxdata.aspx"
        data = {
        'newsID': str(page),
        'pid':str(pid),
        'type':'hotcomment'
        }
        r = requests.post(url, data=data)
        result = r.text
        with open(path+ str(page)+"/"+str(page) + "-{}-hot.html".format(str(pid)), "w") as file:
            file.write(result.encode("utf-8"))
        if(result is None):
         return
        jsondata=json.loads(result)
        db=jsondata['db']
        result=jsondata['html']
        data=BeautifulSoup(result)
        nicks=data.select(".nick")
        for nick in nicks:
            try:
                name=nick.text
                sql = "insert into hotcomment VALUES (%s)"%('\''+name+'\'')
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
if __name__=='__main__':
    queue=[]
    for i in range(221111,353195):#这里改成你要爬的文章范围，从网页的url上获取
        queue.append(i)
    pool = threadpool.ThreadPool(8)#使用的线程数，推荐默认值
    [pool.putRequest(req) for req in request]
    pool.wait()