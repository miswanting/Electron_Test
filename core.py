# coding=utf-8
import re
import bs4
import sys
import glob
import http.cookiejar
import json
import time
import queue
import random
import socket
import urllib
import hashlib
import threading
HOST = '127.0.0.1'
PORT = 9876
isRunning = {}
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
if glob.glob('db.json') == []:
    db = {
        'raw': {},
        'tmp': {},
        'cache': {},
        'config': {},
        'storage': {}
    }
else:
    with open('db.json', 'r')as f:
        data = f.read()
        db = json.loads(data)


def get_GIH():
    m = hashlib.md5()
    m.update(str(time.time()).encode("utf-8"))
    m.update(str(random.random()).encode("utf-8"))
    return m.hexdigest()


def send_str(s, data):
    s.send(data.encode("utf-8"))


def recv_str(s):
    tmp = s.recv(4096).decode("utf-8")
    return tmp


def send_json(s, data):
    send_str(s, json.dumps(data))


def recv_json(s):
    return json.loads(recv_str(s))


def do_cmd(s, cmd):
    print(cmd)
    if cmd[0] == 'get':
        if cmd[1] == 'GIH':
            send_str(s, get_GIH())


def start_client():
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, PORT))
            # s.send(b'Hello, world')
            # send_str('123')
            # send_str(s, 'askme')
            # s.send(b'Hello, world')
            # cmd = recv_str(s)
            while True:
                # send_str(s,'askme')
                cmd = recv_str(s)
                print(cmd)
                if cmd == 'exit':
                    break
                else:
                    cmd = cmd.split(' ')
                    do_cmd(s, cmd)
            # data = s.recv(4096)
            # print('Received', repr(data))
        except IOError as e:
            pass
        time.sleep(0.3)


# 以下任务同时进行：
# 1. 更新列表
# 2. 更新上海信息
# 3. 更新深圳信息
url_stock_code = 'http://quote.eastmoney.com/stocklist.html'
api_sinajs = 'http://hq.sinajs.cn/rn={}&list={}'

cookie = http.cookiejar.CookieJar()
handler = urllib.request.HTTPCookieProcessor(cookie)
opener = urllib.request.build_opener(handler)


def get_current_time():
    return str(int(time.time()))


def get_sinajs(time, code_list):
    args = ','.join(code_list)
    request = urllib.request.Request(api_sinajs.format(time, args))
    response = opener.open(request)
    try:
        raw_respond = response.read().decode('gbk')
        lines = raw_respond.split('\n')
        ans = []
        for line in lines:
            if not line == '':  # 去除因为操作而生成的空行
                raw = line.split('"')[1]
                if raw == '':  # 返回数据为空
                    data = None
                else:
                    data = raw.split(',')
                ans.append(data)
        return data
    except OSError as e:
        print('!', e)
        return 'timeout'


def fetch_stock_code():  # 获取股票代码
    isRunning['fetch_stock_code'] = True
    request = urllib.request.Request(url_stock_code)
    response = opener.open(request)
    db['raw']['stock_code_page'] = response.read().decode('gbk')
    soup = bs4.BeautifulSoup(db['raw']['stock_code_page'], 'lxml')
    pattern = re.compile('">(.*?)\((.*?)\)<')
    db['cache']['sh_code'] = re.findall(pattern, str(soup.find_all('ul')[7]))
    db['cache']['sz_code'] = re.findall(pattern, str(soup.find_all('ul')[8]))
    db['storage']['sh_code'] = db['cache']['sh_code']
    db['storage']['sz_code'] = db['cache']['sz_code']
    with open('db.json', 'w') as f:
        f.write(json.dumps(db))


def fetch_sh_stock():  # 获取上海股票信息
    isRunning['fetch_sh_stock'] = True
    while isRunning['fetch_sh_stock']:
        if not 'sh_code'in db['storage'].keys():
            time.sleep(0.3)
        else:
            fetch_queue = queue.Queue()
            for each in db['storage']['sh_code']:
                fetch_queue.put('sh' + each[1])
            db['tmp']['sh_stock'] = {}
            while not fetch_queue.empty():
                try:
                    code_name = fetch_queue.get()
                    tmp = get_sinajs(get_current_time(), [code_name])
                    if tmp == 'timeout':
                        print(code_name)
                        fetch_queue.put(code_name)
                    db['tmp']['sh_stock'][code_name] = tmp
                except OSError as e:
                    print(e)
            break
    with open('db.json', 'w') as f:
        f.write(json.dumps(db))
    print('[DONE]fetch_sh_stock')


def fetch_sz_stock():  # 获取深圳股票信息
    isRunning['fetch_sz_stock'] = True
    while isRunning['fetch_sz_stock']:
        if not 'sz_code'in db['storage'].keys():
            time.sleep(0.3)
        else:
            fetch_queue = queue.Queue()
            for each in db['storage']['sz_code']:
                fetch_queue.put('sz' + each[1])
            db['tmp']['sz_stock'] = {}
            while not fetch_queue.empty():
                try:
                    code_name = fetch_queue.get()
                    tmp = get_sinajs(get_current_time(), [code_name])
                    if tmp == 'timeout':
                        fetch_queue.put(code_name)
                    db['tmp']['sz_stock'][code_name] = tmp
                except OSError as e:
                    print(e)
            break
    with open('db.json', 'w') as f:
        f.write(json.dumps(db))
    print('[DONE]fetch_sz_stock')

t_stock_code = threading.Thread(target=fetch_stock_code)
t_sh_stock = threading.Thread(target=fetch_sh_stock)
t_sz_stock = threading.Thread(target=fetch_sz_stock)
t_client = threading.Thread(target=start_client)

t_stock_code.start()
t_sh_stock.start()
t_sz_stock.start()
t_client.start()
