import requests
import random
import time
import json
import csv
from urllib.parse import parse_qs
import re
import emoji

URL = 'https://weibo.com/ajax/statuses/buildComments?is_reload=1&id=4879260054985126&is_show_bulletin=2&is_mix=0&count=10&uid=2023791210'

query_dict = parse_qs(URL)
id = query_dict.get('id')[0]  # 博文id
uid = query_dict.get('uid')[0]  # 博主用户id

start_url = 'https://weibo.com/ajax/statuses/buildComments?is_reload=1&id=' + id + '&is_show_bulletin=2&is_mix=0&max_id=0&count=20&uid=' + uid  # 首个url
next_url = 'https://weibo.com/ajax/statuses/buildComments?flow=0&is_reload=1&id=' + id + '&is_show_bulletin=2&is_mix=0&max_id={}&count=20&uid=' + uid  # 用于构造后面的url的模板
coc_url = 'https://weibo.com/ajax/statuses/buildComments?is_reload=1&id={}&is_show_bulletin=2&is_mix=1&fetch_level=1&max_id=0&count=20&uid=' + uid
next_coc_url = 'https://weibo.com/ajax/statuses/buildComments?flow=0&is_reload=1&id={0}&is_show_bulletin=2&is_mix=1&fetch_level=1&max_id={1}&count=20&uid=' + uid
continue_url = start_url
continue_coc_url = coc_url

headers = {
    'cookie': 'SINAGLOBAL=5502966083234.466.1661399842232; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9W5EvDUafsba2vedpWYbgZHI5JpX5KMhUgL.FoMN1hB4S0q4eK52dJLoI7.peoSbIPHbIg2t; MEIQIA_TRACK_ID=2EO65fVg4Staci3f6L4uglZu27W; MEIQIA_VISIT_ID=2EO65l3FGi0rKRt1LXpjV7KZsIy; UOR=,,0x3.com; webim_unReadCount={"time":1662973260150,"dm_pub_total":1,"chat_group_client":0,"chat_group_notice":0,"allcountNum":40,"msgbox":0}; ALF=1694589756; SSOLoginState=1663053757; SCF=AmtAQJBFB9MUNgfipdZz_Oxsx_r69f8Dm0QGk0l_t_NCK4Yc0VfcL1UKnR-WRPtSdMmBVPorBZ8G2F8PCwCTzY0.; SUB=_2A25OJF_tDeRhGeFJ41YY9yjFyjyIHXVtUDYlrDV8PUNbmtAKLRiikW9Nfu2WC6Hk_Y1PRoknXbRz2EkvEEtF84v3; XSRF-TOKEN=HUexbCHhM6Y4ZD9Pi-4kJ_1w; _s_tentry=weibo.com; Apache=8093750225032.499.1663055580978; ULV=1663055581066:13:10:5:8093750225032.499.1663055580978:1663032730324; WBPSESS=qBfPw5dzoo2_le6zWLBwqe6j2yiF2XwEo3DrCadXJS9KOM_-J5pqq4mdCanUook3XPKV8J6OHUu1g_Py6GH9OwiKs3GHgaft7ddt-cLCJn0e6Z_8FegygTzbWy-Cx6mWwKGgTSf9u93ZWUWYGeA-1A==',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
}
count = 0

fileHeader = ["id", "评论类型", "评论时间", "昵称", "评论内容"]


def get_data(url, comment_id_list, max_id_list):
    print("visiting url...")
    for trytime in range(3):  # 允许超时次数为3次
        try:
            response = requests.get(url=url, headers=headers, timeout=5)
            data = json.loads(response.text)
            if response.status_code == 200:
                break
        except:
            print('超时')
    print("visiting url over")

    if trytime == 2:  # 连续3次超时就退出递归
        print('连续3次超时')
        return

    if data['ok'] == 0:  # 若没有获取到数据也进行退出
        print("获取到的数据data['ok']=", 0)
        return

    elif data['ok'] == 1:  # 判断若能够获取到数据 则进行所需数据提取，并且构造下次请求的url，调用函数
        max_id = data.get("max_id")
        comments = data.get('data')
        if comments is not None:
            for item in comments:
                ''' 获取内容'''
                comment_id = item['id']
                print("big checking....")
                if comment_id in comment_id_list:
                    print("lose big checking")
                    return
                print("big checking over")
                print("getting data...")
                global count
                global continue_coc_url
                count += 1
                comment_id_list.append(comment_id)
                create_time = item['created_at']
                url_id = item['id']
                continue_coc_url = coc_url.format(str(url_id))
                comment = ''.join(item['text_raw'])
                comment = deleteByStartAndEnd(comment)
                comment = deleteEmoji(comment)
                screen_name = item.get('user')['screen_name']
                # 将内容写入csv文件中
                csv_opreator([count, "一级评论", create_time, screen_name, comment])
                coc_id_list = []
                print("getting data over")
                print("searching coc...")
                coc_max_id_list = []
                get_CoC(continue_coc_url, url_id, coc_id_list, coc_max_id_list)
                print("searching coc over")

            # max_id=0 则意味着已经没有评论了
            if max_id == 0:
                return
            print("max_id != 0")
            print("checking max_id...")
            if max_id in max_id_list:
                print("checking max_id lose")
                return
            print("checking max_id over")
            max_id_list.append(max_id)
            global next_url
            continue_url = next_url.format(str(max_id))
            print("waiting...")
            time.sleep(random.random() * 5)
            print("waiting over")
            get_data(continue_url, comment_id_list, max_id_list)  # 调用函数本身
            return
        else:
            print("empty url | no data")


def get_CoC(url, url_id, coc_id_list, coc_max_id_list):
    try:
        response = requests.get(url=url, headers=headers, timeout=5)
        data = json.loads(response.text)
    except:
        print('超时')
        return

    if data['ok'] == 0:  # 若没有获取到数据也进行退出
        print("获取到的数据data['ok']=", 0)
        return
    data = json.loads(response.text)
    coc_max_id = data.get('max_id')
    comments = data.get('data')
    if comments is not None:
        for item in comments:
            coc_id = item['id']
            print("checking...")
            if coc_id in coc_id_list:
                print("lose checking")
                return
            print("checking over")
            print("getting coc...")
            coc_id_list.append(coc_id)
            global count
            count += 1
            create_time = item['created_at']
            comment = ''.join(item['text_raw'])
            comment = deleteByStartAndEnd(comment)
            comment = deleteEmoji(comment)
            screen_name = item.get('user')['screen_name']
            # 将内容写入csv文件中
            csv_opreator([count, "二级评论", create_time, screen_name, comment])
            print("getting coc over")
        if coc_max_id == 0:
            return
        if coc_max_id in coc_max_id_list:
            return
        coc_max_id_list.append(coc_max_id)
        global next_coc_url
        continue_coc_url = next_coc_url.format(str(url_id), str(coc_max_id))
        print("waiting...")
        time.sleep(random.random() * 5)
        print("waiting over...")
        get_CoC(continue_coc_url, url_id, coc_id_list, coc_max_id_list)


def csv_opreator(a):
    with open("weibocoments.csv", "a", encoding='utf-8-sig', newline="") as f:
        writer = csv.writer(f)
        writer.writerow(a)


def deleteByStartAndEnd(text):
    text = re.sub(r"(回复)?(//)?\s*@\S*?\s*(:| |$)", " ", text)  # 去除正文中的@和回复/转发中的用户名
    text = re.sub(r"\[\S+\]", "", text)  # 去除表情符号
    # text = re.sub(r"#\S+#", "", text)      # 保留话题内容
    URL_REGEX = re.compile(
        r'(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?«»“”‘’]))',
        re.IGNORECASE)
    text = re.sub(URL_REGEX, "", text)  # 去除网址
    text = text.replace("转发微博", "")  # 去除无意义的词语
    text = re.sub(r"\s+", " ", text)  # 合并正文中过多的空格
    return text.strip()


def deleteEmoji(s):
    pattern = r'\[.*?\]'
    s = re.sub(pattern, '', s)
    s = emoji.demojize(s)
    return re.sub(':\S+?:', ' ', s)


if __name__ == "__main__":
    comment_id_list = []
    max_id_list = []
    get_data(continue_url, comment_id_list, max_id_list)
