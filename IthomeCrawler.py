# -*- coding: utf-8 -*-
import re
import os
import MySQLdb
import requests
from bs4 import BeautifulSoup
import time
import json
import threadpool
database='ithome'
def ConnectMySql():#在这里改成你的MySql连接信息
    return MySQLdb.connect(host='', user='', passwd='', port=3306, charset='utf8')
emoji_pattern = re.compile(
    u"(\ud83d[\ude00-\ude4f])|" 
    u"(\ud83c[\udf00-\uffff])|"  
    u"(\ud83d[\u0000-\uddff])|"  
    u"(\ud83d[\ude80-\udeff])|"  
    u"(\ud83c[\udde0-\uddff])" 
    "+", flags=re.UNICODE)
def remove_emoji(text):
    return emoji_pattern.sub(r'', text)
def gethash(url):
    r=requests.get(url)
    result=r.text
    if result is None:
        return
    hash=re.findall("(?<= var ch11 = \').+?(?=\')",result)
    return hash[0]
def gettime():
    return time.strftime('%m-%d/%H:%M:%S', time.localtime())
def SearchComment(page):
  print("{}-{}\n".format(gettime(), page))
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
    if(result is None):
     return
    comments = re.findall("<li class=\"entry\">.+?</li>", result)
    total=[]
    for comment in comments:
     try:
      count+=1
      apptype="null"
      comment=BeautifulSoup(comment,"html.parser")
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
        apptype = " ".join(comment.select_one(".nmp").find_all("span")[1].attrs["class"])
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
      sqldata = (id,commentid,name,remove_emoji(content),device,position,avator,int(favor, 10), int(against, 10),page,floor,sendtime,time.strftime('%Y-%m-%d  %H:%M:%S',time.localtime()),apptype)
      total.append(sqldata)
      major=floor
      reply=comment.select_one(".reply")
      if(reply!=None):
          details=reply.select(".gh")
          for value in details:
              try:
                  apptype = "null"
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
                      apptype=" ".join(value.select_one(".nmp").find_all("span")[1].attrs["class"])
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
                  sqldata = (id, commentid, name,remove_emoji(content), device, position, avator,
                             int(favor, 10), int(against, 10), page, floor, sendtime,
                             time.strftime('%Y-%m-%d  %H:%M:%S', time.localtime()),apptype)
                  total.append(sqldata)
              except Exception as e:
                  with open("error.log", "a") as fd:
                      fd.write("{} 进入第{}层楼中楼失败,文章:{}\n错误日志:{}\n".format(gettime(),major,page,e))
                  continue
     except Exception as e:
         with open("error.log", "a") as fd:
             fd.write("{} 进入第{}条评论失败,文章:{},页码:{}\n错误日志:{}\n".format(gettime(),count, page,i,e))
         continue
    try:
        sql = "replace into comments VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        cur.executemany(sql, total)
        conn.commit()
    except Exception as e:
        with open("error.log", "a") as fd:
            fd.write("{} 插入{}条评论记录失败,文章:{},页码:{}\n错误日志:{}\n".format(gettime(),len(total), page, i,e))
        pass
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
    hash = gethash("https://dyn.Ithome.com/comment/" + str(page))
    while(db):
        url = "https://dyn.Ithome.com/Ithome/getajaxdata.aspx"
        data = {
        'newsID': str(page),
        'hash':hash,
        'pid':str(pid),
        'type':'hotcomment'
        }
        r = requests.post(url, data=data)
        result = r.text
        if(result is None):
         return
        jsondata=json.loads(result)
        db=jsondata['db']
        result=jsondata['html']
        data=BeautifulSoup(result,"html.parser")
        nicks=data.select(".nick")
        try:
            sqldata=[(nick.text,) for nick in nicks]
            sql = "insert into hotcomment VALUES (%s)"
            cur.executemany(sql,sqldata)
            conn.commit()
        except Exception as e:
            with open("error.log","a") as fd:
                fd.write("插入{}条热评记录失败,文章:{}\n错误日志:{}\n".format(len(nicks),page,e))
            pass
        pid=pid+1
    return
def get_range():
    last=int(open("last.txt").read())
    try:
        url = "http://api.ithome.com/json/newslist/news"
        result = requests.get(url).json()
        latest=result["newslist"][0]["newsid"]
    except Exception as e:
        with open("error.log", "a") as fd:
            fd.write("{} 获取最新文章列表错误:{}\n".format(gettime(),e))
        latest=last
    return (last,latest)
if __name__=='__main__':
    if not os.path.exists("last.txt"):
        with open("last.txt","w") as fd:
            fd.write(221111)
    queue=[]
    (last, latest)=get_range()
    with open("record.log", "a") as fd:
        fd.write("{} 正在爬取文章范围:{}-{}\n".format(gettime(), last,latest))
    for i in range(last,latest):
        queue.append(i)
    pool = threadpool.ThreadPool(4)#使用的线程数，推荐默认值
    request = threadpool.makeRequests(SearchComment, queue)
    [pool.putRequest(req) for req in request]
    pool.wait()
    with open("record.log", "a") as fd:
        fd.write("{} 已完成，保存的下次文章的起始号码为:{}\n".format(gettime(),latest))
    with open("last.txt", "w") as fd:
        fd.write(str(latest))