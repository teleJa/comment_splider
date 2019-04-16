# -*- coding: utf-8 -*-
# @author: Tele
# @Time  : 2019/04/14 下午 3:48
import time
import requests
import os
import json
from fake_useragent import UserAgent
from lxml import etree


class JDSplier:

    flag = True

    @staticmethod
    def get_proxy():
        return requests.get("http://127.0.0.1:5010/get/").content.decode()

    @staticmethod
    def get_ua():
        ua = UserAgent()
        return ua.random

    def __init__(self, kw_list):
        self.kw_list = kw_list
        # 评论url
        self.url_temp = "https://sclub.jd.com/comment/productPageComments.action?&productId={}&score=0&sortType=5&page={}&pageSize=10&isShadowSku=0&rid=0&fold=1"
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
        self.headers["User-Agent"] = JDSplier.get_ua()
        proxy = "http://" + JDSplier.get_proxy()
        self.proxies["http"] = proxy
        print("ua:", self.headers["User-Agent"])
        print("proxy:", self.proxies["http"])


    # 评论
    def parse_url(self, product_id, page):
        url = self.url_temp.format(product_id, page)
        response = requests.get(url, headers=self.headers, proxies=self.proxies)
        if response.status_code == 200:
            print(url)
            if len(response.content) < 0:
                return
            data = json.loads(response.content.decode("gbk"))
            # 评论
            comment_list = data["comments"]
            if len(comment_list) > 0:
                item_list = list()
                for comment in comment_list:
                    item = dict()
                    # 商品名
                    item["referenceName"] = comment["referenceName"]
                    # 评论时间
                    item["creationTime"] = comment["creationTime"]
                    # 内容
                    item["content"] = comment["content"]
                    item_list.append(item)

                # 保存
                with open(self.file_dir, "a", encoding="utf-8") as file:
                    file.write(json.dumps(item_list, ensure_ascii=False, indent=2))
                    file.write("\n")
                time.sleep(5)
            else:
                JDSplier.flag = False


        else:
            pass

    # 提取id
    def get_product_info(self):

        url_temp = "https://search.jd.com/Search?keyword={}&enc=utf-8"
        result_list = list()
        for kw in self.kw_list:
            url = url_temp.format(kw)
            response = requests.get(url, headers=self.headers, proxies=self.proxies)
            if response.status_code == 200:
                item_dict = dict()
                id_list = list()
                html_element = etree.HTML(response.content)
                # 获得该关键词下第一页的商品id,前10个
                id_list = html_element.xpath("//div[@id='J_goodsList']/ul/li[position()<11]/@data-sku")
                item_dict["title"] = kw
                item_dict["id_list"] = id_list
                result_list.append(item_dict)
            else:
                pass
        return result_list

    def get_comment(self, item_list):
        if len(item_list) > 0:
            for item in item_list:
                id_list = item["id_list"]
                item_title = item["title"]
                if len(id_list) > 0:
                    # 检查目录
                    self.parent_dir = item_title + time.strftime("-%Y-%m-%d-%H-%M-%S", time.localtime(time.time()))
                    if not os.path.exists(self.parent_dir):
                        os.makedirs(self.parent_dir)
                    for product_id in id_list:
                        page = 0
                        self.file_dir = self.parent_dir + "/" + str(product_id) + "_ratecontent.txt"
                        while JDSplier.flag:
                            self.check()
                            self.parse_url(product_id, page)
                            page += 1
                        JDSplier.flag = True
                else:
                    print("---error,empty id list---")
        else:
            print("---error,empty item list---")



    def run(self):
        self.check()
        item_list = self.get_product_info()
        print(item_list)
        self.get_comment(item_list)

        # 评论
        # number = 0
        # while JDSplier.flag:
        #     url = self.url_temp.format(number)
        #     self.check()
        #     self.parse_url(url)
        #     number += 1


def main():
    kw_list = ["华为p30", "华为p30pro"]
    splider = JDSplier(kw_list)
    splider.run()


if __name__ == '__main__':
    main()