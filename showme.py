#!/usr/bin/python2
import SimpleHTTPServer
import SocketServer
from BaseHTTPServer import BaseHTTPRequestHandler
from os import curdir, sep
from lxml import html
from bs4 import BeautifulSoup as bs4
import numpy as np
import pandas as pd
import os
import requests
import re
import sys
import time
import creds
import email
import thread

reload(sys)
sys.setdefaultencoding('utf8')
PORT = 8000
url_base = 'http://sfbay.craigslist.org/search/eby/apa'
my_email = 'capodacac@gmail.com'
params = dict(bedroom=1,min_price=900, max_price=1700)

class myHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path=="/":
            self.path = "index.html"
        try:
            sendReply=False
            if self.path.endswith(".html"):
                mimetype='text/html'
                sendReply=True
            if sendReply==True:
                f = open(curdir + sep + self.path)
                self.send_response(200)
                self.send_header('Content-type',mimetype)
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
            return
        except IOError:
            self.send_error(404,'File Not Found: %s',self.path)


def find_prices(results):
    prices =[]
    for r in results:
        price = r.find('span', {'class':'result-price'})
        if price is not None:
            price = float(price.text.strip('$'))
        else:
            price = np.nan
        prices.append(price)
    return prices


def sanitize(strArr):
    s = []
    for st in strArr:
        s.append(st.encode('utf-8'))
    return s

def parse_me(rsp):
    html = bs4(rsp.text,'html.parser')
    apts = html.find_all('li', attrs={'class':'result-row'})
    results =[]

    apt_titles = [ apt.find('a',attrs={'class','hdrlnk'}).text for apt in apts]
    #apt_sizes  = [ re.sub(' +',' ', apt.findAll(attrs ={'class':'housing'})[0].text.replace("\n","").strip()) for apt in apts]
    apt_prices = find_prices(apts)
    apt_times  = [ apt.find('time')['datetime']  for apt in apts]
    apt_links  = [ url_base + apt.find('a',attrs={'class','hdrlnk'})['href'] for apt in apts]
    apt_loc    = [ apt.find('a',attrs={'class','hdrlnk'}).text for apt in apts]

    apt_titles = sanitize(apt_titles)
    #apt_sizes  = sanitize(apt_sizes)
    apt_times  = sanitize(apt_times)
    apt_loc    = sanitize(apt_loc)

    #create a dataframe to hold all info
    data = np.array([apt_titles,apt_prices, apt_times, apt_links, apt_loc])
    col_names = ["Title","Price","Posted On","link","Location"]
    pd.set_option('max_colwidth',2000)
    dataframe = pd.DataFrame(data.T,columns=col_names)
    dataframe.set_index('Title')
    results.append(dataframe)
    results  = pd.concat(results, axis=0)

    return results


def listen():

    link_list = []
    link_list_send = []
    send_list = []
    url_cl_base = "http://sfbay.craigslist.org"
    while True:
        rsp = requests.get(url_base, params=params)
        html = bs4(rsp.text,'html.parser')
        result = parse_me(rsp)
        result.head()
        result.to_html("index.html")
        stylesheet= "style.css"
        with open("./index.html","a") as file:
            file.write("<link rel='stylesheet' type='text/css' href='"+stylesheet+"' >")

        apts = html.find_all('li', attrs={'class':'result-row'})
        for apt in apts:
            title = apt.find_all('a', attrs={'class': 'hdrlnk'})[0]
            name  = ''.join([i for i in title.text])
            link  = title.attrs['href']
            cur_price = apt.find('span', {'class':'result-price'}).text
            cur_price = sanitize(cur_price)
            cur_price = ''.join(cur_price)
            loc       =  apt.find('span',attrs={'class','result-hood'})
            if loc is None:
                loc =""
            else: loc = loc.text

            if link not in link_list and link not in link_list_send:
                #print "found new listing"
                f = open('./home/critter/out.log', 'w')
                print >> f, 'found new listing',url_cl_base,link
                f.close()
                link_list_send.append(link)
                send_list.append(name + '\n -$$ '+ cur_price + ' $$ - \nLOCATION:: '+ loc+"\n" + url_cl_base + link)

        if len(link_list_send)>0:
            g = creds.Creds();
            #print("sending mail")
            f = open('./home/critter/out.log','w')
            print >> f,'sending mail to:: '+ my_email
            f.close()
            msg = "\n\n".join(send_list)
            m   = email.message.Message()
            m.set_payload(msg)
            g.gmailSend(m,my_email)
            link_list += link_list_send
            link_list_send=[]
            send_list=[]
        sleep_time = np.random.randint(150,155)
        time.sleep(sleep_time)


def begin():
    listen()
    httpd = SocketServer.TCPServer(("",PORT),myHandler)
    try:
        print "serving at port", PORT
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.socket.close()

#mac users doThis
#pid = os.fork()
#if pid == 0:
#  begin()

#windows users do this
begin()

