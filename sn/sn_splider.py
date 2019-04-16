# -*- coding: utf-8 -*-
# @author: Tele
# @Time  : 2019/04/15 下午 8:20
import time
import requests
import os
import json
import re
from fake_useragent import UserAgent


class SNSplider:
    flag = True
    regex_cluser_id = re.compile("\"clusterId\":\"(.{8})\"")
    regex_comment = re.compile("reviewList\((.*)\)")

    @staticmethod
    def get_proxy():
        return requests.get("http://127.0.0.1:5010/get/").content.decode()

    @staticmethod
    def get_ua():
        ua = UserAgent()
        return ua.random

    def __init__(self, kw_list):
        self.kw_list = kw_list
        # 评论url 参数顺序:cluser_id,sugGoodsCode,页码
        self.url_temp = "https://review.suning.com/ajax/cluster_review_lists/general-{}-{}-0000000000-total-{}-default-10-----reviewList.htm"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36",
        }
        self.proxies = {
            "http": None
        }
        self.parent_dir = None
        self.file_dir = None

    # ua,proxy
    def check(self):
        self.headers["User-Agent"] = SNSplider.get_ua()
        proxy = "http://" + SNSplider.get_proxy()
        self.proxies["http"] = proxy
        print("ua:", self.headers["User-Agent"])
        print("proxy:", self.proxies["http"])

    # 评论
    def parse_url(self, cluster_id, sugGoodsCode, page):
        url = self.url_temp.format(cluster_id, sugGoodsCode, page)
        response = requests.get(url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            print(url)
            if len(response.content) < 0:
                return
            data = json.loads(SNSplider.regex_comment.findall(response.content.decode())[0])
            if "commodityReviews" in data:
                # 评论
                comment_list = data["commodityReviews"]
                if len(comment_list) > 0:
                    item_list = list()
                    for comment in comment_list:
                        item = dict()
                        try:
                            # 商品名
                            item["referenceName"] = comment["commodityInfo"]["commodityName"]
                        except:
                            item["referenceName"] = None
                        # 评论时间
                        item["creationTime"] = comment["publishTime"]
                        # 内容
                        item["content"] = comment["content"]
                        # label
                        item["label"] = comment["labelNames"]
                        item_list.append(item)

                    # 保存
                    with open(self.file_dir, "a", encoding="utf-8") as file:
                        file.write(json.dumps(item_list, ensure_ascii=False, indent=2))
                        file.write("\n")
                    time.sleep(5)
            else:
                SNSplider.flag = False
        else:
            print("评论页出错")

    # 提取商品信息
    def get_product_info(self):
        url_temp = "https://tuijian.suning.com/recommend-portal/recommendv2/biz.jsonp?parameter={}&sceneIds=2-1&count=10"
        result_list = list()
        for kw in self.kw_list:
            url = url_temp.format(kw)
            response = requests.get(url, headers=self.headers, proxies=self.proxies, verify=False)
            if response.status_code == 200:
                kw_dict = dict()
                id_list = list()
                data = json.loads(response.content.decode())
                skus_list = data["sugGoods"][0]["skus"]
                if len(skus_list) > 0:
                    for skus in skus_list:
                        item = dict()
                        sugGoodsCode = skus["sugGoodsCode"]
                        # 请求cluserId
                        item["sugGoodsCode"] = sugGoodsCode
                        item["cluster_id"] = self.get_cluster_id(sugGoodsCode)
                        id_list.append(item)
                kw_dict["title"] = kw
                kw_dict["id_list"] = id_list
                result_list.append(kw_dict)
            else:
                pass
        return result_list

    # cluserid
    def get_cluster_id(self, sugGoodsCode):
        self.check()
        url = "https://product.suning.com/0000000000/{}.html".format(sugGoodsCode[6::])
        response = requests.get(url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            cluser_id = None
            try:
                cluser_id = SNSplider.regex_cluser_id.findall(response.content.decode())[0]
            except:
                pass
            return cluser_id
        else:
            print("请求cluster id出错")

    def get_comment(self, item_list):
        if len(item_list) > 0:
            for item in item_list:
                id_list = item["id_list"]
                item_title = item["title"]
                if len(id_list) > 0:
                    self.parent_dir = "f:/sn_comment/" + item_title + time.strftime("-%Y-%m-%d-%H-%M-%S",
                                                                                    time.localtime(time.time()))
                    if not os.path.exists(self.parent_dir):
                        os.makedirs(self.parent_dir)
                    for product_code in id_list:
                        # 检查proxy,ua
                        sugGoodsCode = product_code["sugGoodsCode"]
                        cluster_id = product_code["cluster_id"]
                        if not cluster_id:
                            continue
                        page = 1
                        # 检查目录
                        self.file_dir = self.parent_dir + "/" + sugGoodsCode[6::] + "_ratecontent.txt"
                        self.check()
                        while SNSplider.flag:
                            self.parse_url(cluster_id, sugGoodsCode, page)
                            page += 1
                        SNSplider.flag = True
                else:
                    print("---error,empty id list---")
        else:
            print("---error,empty item list---")

    def run(self):
        self.check()
        item_list = self.get_product_info()
        print(item_list)
        self.get_comment(item_list)


def main():
    # , "华为mate20pro", "vivoz3", "oppok1", "荣耀8x", "小米9", "小米mix3", "三星s9", "iphonexr", "iphonexs"
    # "华为p30pro", "华为mate20pro", "vivoz3""oppok1""荣耀8x", "小米9"
    kw_list = ["小米mix3", "三星s9", "iphonexr", "iphonexs"]
    splider = SNSplider(kw_list)
    splider.run()


if __name__ == '__main__':
    main()
