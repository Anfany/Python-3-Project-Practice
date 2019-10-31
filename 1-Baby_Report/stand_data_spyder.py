# -*- coding：utf-8 -*-
# &Author  AnFany


# 爬虫获取0-5岁宝宝身高、体重、头围、体重指数，身长别体重(0-2岁)，身高别体重(2-5岁)，发育监测的标准数据
# 版本：世界卫生组织版本


# 爬虫获取数据
from urllib import request
from bs4 import BeautifulSoup as bs
import pandas as pd
import numpy as np
import os



GENDER = {'boys': '男童', 'girls': '女童'}  # 性别:男孩，女孩
#  项目：身长/高，体重，头围，体重指数，身长别体重(0-2岁)，身高别体重(2-5岁)
ITEM = {'lhfa': '身长/高', 'wfa': '体重', 'hcfa': '头围', 'bfa': '体重指数', 'wfl': '身长别体重(0-2岁)', 'wfh': '身高别体重(2-5岁)'}
METHOD = {'z_exp': 'Z评分', 'p_exp': '百分位数'}  # 方式：Z评分和百分位数
BASE_URL = 'https://www.who.int/childgrowth/standards'  # 网址
FILE = r'C:\Users\GWT9\Desktop\stand_data\WHO'  # 存数数据的文件夹


class DATA:
    def __init__(self, url=BASE_URL, i_dict=ITEM, g_dict=GENDER, m_dict=METHOD, f_path=FILE):
        """
        获取数据的基本设置
        :param url: 基础的网址
        :param i_dict: 项目字典
        :param g_dict: 性别字典
        :param m_dict: 方式字典
        :param f_path: 存储数据文件的路径
        """
        self.url = url
        self.i_dict = i_dict
        self.g_dict = g_dict
        self.m_dict = m_dict
        self.f_path = f_path

    def spyder_data(self):
        """
        爬虫获取数据存在csv文件中
        :return: csv数据文件
        """
        for g in self.g_dict:
            for m in self.m_dict:
                # 判断文件是否在文件夹中
                if not os.path.exists('%s/%s_%s.xls' % (self.f_path, g, m)):
                    writer = pd.ExcelWriter(r'%s/%s_%s.xls' % (self.f_path, g, m))
                    for i in self.i_dict:
                        # 合成的网址,注意头围的网址稍有不同
                        if i == 'hcfa':
                            all_url = '%s/second_set/%s_%s_%s.txt' % (self.url, i, g, m)
                        else:
                            all_url = '%s/%s_%s_%s.txt' % (self.url, i, g, m)
                        # 打开网址
                        html = request.urlopen(all_url)
                        bs_data = bs(html.read(), "html5lib")
                        data_txt = str(bs_data.body.get_text())
                        # 按行读取txt数据
                        data_list = []
                        for line in data_txt.split('\n'):
                            # 转变为列表形式
                            list_d = line.split(' ')[0].split('\t')
                            if len(list_d) > 1:
                                data_list.append(list_d)
                        # 在第一行添加这份数据的说明
                        doc_str = '0-5岁%s%s发育%s数据表' % (self.g_dict[g], self.i_dict[i], self.m_dict[m])
                        length = len(list(data_list[0]))
                        df_column = [' ' for h in list(range(length))]
                        df_column[0] = doc_str
                        pd_data = pd.DataFrame(np.array(data_list), columns=df_column)
                        # 写入excel中
                        pd_data.to_excel(writer, sheet_name=i, encoding='gb2312', index=False)
                    # 关闭和保存
                    writer.save()
                    writer.close()
        return '数据爬取完毕'

    def read_data(self, g):
        """
        根据性别读取各个指标以及各个方式的数据
        :param g: 性别
        :return: 字典式的数据
        """
        # 获取数据
        self.spyder_data()
        data_dict = {}
        for rm in self.m_dict:
            data_dict[rm] = {}
            for ri in self.i_dict:
                # 读取excel数据
                read_data = pd.read_excel(r'%s/%s_%s.xls' % (self.f_path, g, rm), sheet_name=ri, header=1)
                data_dict[rm][ri] = read_data
        print('数据字典完成')
        return data_dict

