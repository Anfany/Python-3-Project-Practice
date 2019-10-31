# -*- coding：utf-8 -*-
# &Author  AnFany


# 0-5岁宝宝身高、体重、头围、体重指数、身长别体重、身高别体重发育曲线监测

import stand_data_spyder as s_d  # 获取数据
import matplotlib.pyplot as plt
from scipy import interpolate
from matplotlib.ticker import MultipleLocator
import numpy as np
import datetime
from pylab import mpl, tick_params, minorticks_on  # 作图显示中文
mpl.rcParams['font.sans-serif'] = ['STZhongsong']  # 设置中文字体为新宋体
mpl.rcParams['axes.unicode_minus'] = False

# 存储每个人信息的文件夹
FilePath = r'C:\Users\GWT9\Desktop\baby_data'


class Baby:
    def __init__(self, baby_name, birth_date, gender, observe_date, observe_length, observe_weight, observe_head,
                 stand='WHO', path_name=FilePath):
        """
        宝宝的基本信息
        :param baby_name: 宝宝昵称，非空字符串
        :param birth_date: 宝宝出生日期，字符串的出生日期'2019/6/08'
        :param gender: 宝宝性别，girl：女孩，boy：男孩
        :param observe_date: 监测的日期，列表形式['2019/06/08', '2019/09/08'], 日期需要从小到大。
        :param observe_length: 监测的身高序列，列表形式，需要对应上面的监测日期，单位cm,[58.6, 69.3]
        :param observe_weight: 监测的体重序列，列表形式，需要对应上面的监测日期，单位kg,[5.81, 6.94]
        :param observe_head: 监测的头围序列，列表形式，需要对应上面的监测日期，单位cm,[36.5, 42.6]
        :param stand: 应用的标准，'WHO':世界卫生组织版本
        """
        self.b_n = baby_name
        self.b_d_str = birth_date
        self.b_d = datetime.datetime.strptime(self.b_d_str, '%Y/%m/%d')
        self.g = gender
        self.o_d = self.trans_date_normal(observe_date)
        self.o_l = observe_length
        self.o_w = observe_weight
        self.o_hc = observe_head
        self.s = stand
        # who版需要展示的曲线的条数
        self.who_plot_curve = ['P3', 'P10', 'P25', 'P50', 'P75', 'P90', 'P97']

        # 男女不同的颜色
        self.color, self.grid_color, self.line_color = self.get_color()

        self.path_name = path_name

        self.j_t = self.judge_tap()

    def trans_date_normal(self, o_d):
        normal_date_list = []
        for d in o_d:
            date_d = datetime.datetime.strptime(d, '%Y/%m/%d')
            year = str(date_d.year)
            month = str(date_d.month)
            day = str(date_d.day)
            normal_date_list.append('%s/%s/%s' % (year, (month if len(month) == 2 else '0' + month),
                                                   (day if len(day) == 2 else '0' + day)))
        return normal_date_list


    def get_color(self):
        """
        男童，女童定义不同的颜色
        :return:
        """
        if self.g == 'boys':
            return '#2E5C9B', '#5A7EAF', '#FF0000'
        else:
            return '#B53E91', '#B53E91', '#FF0000'

    def get_observe_days(self, o_d):
        """
        获取监测日期距离出生日期的天数
        :return: 天数列表
        """
        days_observe = []
        for d in o_d:
            # 转换字符串为日期
            d_d = datetime.datetime.strptime(d, '%Y/%m/%d')
            days_observe.append((d_d - self.b_d).days + 1)
        return days_observe

    def generate_id(self):
        """
        根据宝宝的昵称和生日生成唯一的可回溯的字符串
        :return: 加密字符串
        """
        # 出生日期加密
        d_d = datetime.datetime.strptime('1971/1/1', '%Y/%m/%d')
        n_n = datetime.datetime.strptime(self.b_d_str, '%Y/%m/%d')
        days = str((n_n - d_d).days + 1)
        alpha_str = ''
        start_sign = 0
        while start_sign < len(days):
            c = days[start_sign]
            if c == '0':
                alpha_str += '0'
                start_sign += 1
            else:
                if start_sign < len(days) - 1:
                    c += days[start_sign + 1]

                    if 1 <= int(c) <= 52:
                        if 1 <= int(c) <= 26:
                            alpha_str += chr(64 + int(c))
                        else:
                            alpha_str += chr(70 + int(c))
                        start_sign += 2
                    else:
                        alpha_str += chr(64 + int(c[:-1]))
                        start_sign += 1
                else:
                    alpha_str += chr(64 + int(c))
                    start_sign += 1
        # 判断汉字的位置
        index_list = ''
        for index, value in enumerate(self.b_n):
            if value >= u'\u4e00' and value <= u'\u9fa5':
                index_list += str(index)
        index_list += str(len(index_list))
        st = self.b_n.encode('unicode_escape')
        st = st.decode("utf-8")
        st = st.replace("\\u", "")
        # 获取转换的数字
        sub_list = [int(i) for i in list(days)]
        tap = max(sub_list) - min(sub_list)
        trans_name = ''
        for kk in st:
            if kk.isdigit():
                # 如果是数字
                number = (int(kk) + tap) % 9
                trans_name += str(number)
            else:
                number = ord(kk)
                if not kk.isupper():
                    number -= 32
                    if number + tap < 91:
                        trans_name += chr((number + tap) % 91)
                    else:
                        trans_name += chr((number + tap) % 90 + 65)
                else:
                    number += 32
                    if number + tap < 123:
                        trans_name += chr((number + tap) % 123)
                    else:
                        trans_name += chr((number + tap) % 122 + 97)

        return trans_name + '-' + index_list + '-' + alpha_str

    def judge_tap(self):
        """
        判断监测日期是否横跨0-2，2-5两个阶段
        :return: '0':0-2, '1':2-5, '2':0-2,2-5
        """
        days_list = self.get_observe_days(self.o_d)

        min_d, max_d = min(days_list), max(days_list)

        if max_d <= 730:
            return '0'

        if min_d >= 731:
            return '1'

        return '2'


    def computer_p(self, number, num_data, key_data):
        """
        根据百分位的系列计算数值所在的百分位数
        :param number: 数值
        :param num_data: 百分位系列
        :param key_data: 标准数据
        :return: 百分位数
        """

        if number < num_data[0]:
            return '<%s' % key_data[0][1:]
        if number > num_data[-1]:
            return '>%s' % key_data[-1][1:]
        else:
            if number in num_data:
                return '%s' % key_data[num_data.index(number)][1:]
            n_data = sorted(num_data + [number])
            c_index = n_data.index(number)
            # 说明在c_index-1 和c_index之间
            min_n = num_data[c_index - 1]
            min_p = float(key_data[c_index - 1][1:])
            max_n = num_data[c_index]
            max_p = float(key_data[c_index][1:])
            # 根据线性插值计算
            x = ((max_n - number) * min_p + (number - min_n) * max_p) / (max_n - min_n)
            return '%.1f' % x

    def cubic_spline_interpolation(self, x_data, y_data):
        """
        生成三次样条插值
        :param x_data: X轴系列
        :param y_data: Y轴系列
        :return: 样条插值的系列
        """
        if len(x_data) == 1:
            return x_data, y_data
        c_d_data = []
        c_n_data = []
        for i in range(len(x_data[:-1])):
            # 日期序列
            c_d_data.append(x_data[i])
            c_d_data.append(abs(x_data[i + 1] - x_data[i]) / 4 + min(x_data[i + 1], x_data[i]))
            c_d_data.append((x_data[i] + x_data[i + 1]) / 2)
            c_d_data.append(abs(x_data[i + 1] - x_data[i]) / 4 * 3 + min(x_data[i + 1], x_data[i]))
            # 监测值序列
            c_n_data.append(y_data[i])
            c_n_data.append((y_data[i + 1] - y_data[i + 1]) / 4 + y_data[i] + 0.34 * (y_data[i + 1] - y_data[i]))
            c_n_data.append((y_data[i + 1] - y_data[i]) / 2 + y_data[i] + 0.14 * (y_data[i + 1] - y_data[i]))
            c_n_data.append((y_data[i + 1] - y_data[i]) / 4 * 3 + y_data[i] + 0.1 * (y_data[i + 1] - y_data[i]))
        c_n_data.append(y_data[-1])
        c_d_data.append(x_data[-1])
        x_data = c_d_data.copy()
        y_data = c_n_data.copy()
        # 三次样条插值插值
        t = interpolate.splrep(x_data, y_data, k=3)
        day_data = np.linspace(min(x_data), max(x_data), num=1000)
        interp_data = interpolate.splev(day_data, t)
        return day_data, interp_data

    def get_date_sub(self, str_date1, str_date2):
        """
        计算2个字符串形式的日期之间差的年数，月数，天数
        :param str_date1: 日期1
        :param str_date2: 日期2
        :return: 差的年月天数
        """
        date1_day = datetime.datetime.strptime(str_date1, "%Y/%m/%d").day
        date2_day = datetime.datetime.strptime(str_date2, "%Y/%m/%d").day + 1

        date1_month = datetime.datetime.strptime(str_date1, "%Y/%m/%d").month
        date2_month = datetime.datetime.strptime(str_date2, "%Y/%m/%d").month

        date1_year = datetime.datetime.strptime(str_date1, "%Y/%m/%d").year
        date2_year = datetime.datetime.strptime(str_date2, "%Y/%m/%d").year

        if date2_day >= date1_day:
            day = date2_day - date1_day
        else:
            day = 30 + date2_day - date1_day
            date2_month -= 1

        if date2_month >= date1_month:
            month = date2_month - date1_month
        else:
            month = 12 + date2_month - date1_month
            date2_year -= 1

        year = date2_year - date1_year

        return ('$%s$岁' % year if year else '') + ('$%s$月' % month if month else '') + ('$%s$天' % day if day else '')

    def plot_p_data_lhfa(self, len_h_data, date_str_data, p_data, fig_name, start_y, end_y, min_num, max_num,
                         fig_size, count_y, y_tap, data_loc, table_w, max_table):
        """
        绘制身高\身长数据的函数
        :param len_h_data: 监测值列表
        :param date_str_data: 监测日期列表
        :param p_data: 总的数据
        :param fig_name: 图片名称
        :param start_y: 绘制开始的岁
        :param end_y: 绘制结束的岁
        :param min_num: 需要绘制的天数的最小值
        :param max_num: 需要绘制的天数的最大值
        :param fig_size: 图片尺寸
        :param count_y: y轴的标签的个数
        :param y_tap: y轴的绘制区间
        :param data_loc: 绘制监测数据的图的位置
        :param table_w: 表格的各个列的宽度
        :param max_table: 表格最大行数
        :return: 绘制的图
        """
        # 首先更改列名
        p_data = p_data.rename(columns={'P01': 'P0.1', 'P999': 'P99.9'})
        # 新建图片
        fig = plt.figure(figsize=fig_size)
        # 绘制
        for value in self.who_plot_curve:
            if value in ['P3', 'P50', 'P97']:  # 比较特殊的三条曲线
                lw = 2.2
                sign = 1
            else:
                lw = 0.9
                sign = 0
            # 曲线粗度
            plt.plot(p_data['Day'].values, p_data[value].values, lw=lw, c=self.color)
            # 为曲线添加说明
            if sign:
                plt.text(max_num, p_data[p_data['Day'] == max_num][value].values[-1] - 0.5,
                         '$\mathbf{%s\\%%}$' % value[1:],
                         color=self.color, size='small', ha='left')
            else:
                plt.text(max_num, p_data[p_data['Day'] == max_num][value].values[-1] - 0.5,
                         '$%s\\%%$' % value[1:],
                         color=self.color, size='small', ha='left')
        # 设置坐标区间
        plt.ylim(y_tap)
        plt.xlim((min_num, max_num))
        minorticks_on()
        tick_params(axis='y', which='major', width=1, length=4, colors=self.color)
        tick_params(axis='x', which='major', width=1, length=2, colors=self.color)
        tick_params(which='minor', length=0)
        # 设置题目
        font = {'color': self.color, 'weight': 'bold', 'size': 14}
        plt.title(('出生' if not start_y else '$%d$' % start_y)
                  + '至$%d$岁%s（%s）发育百分位数标准曲线($WHO$版)\n' %
                  (end_y, s_d.GENDER[self.g], '身高' if start_y else '身长'),
                  fontdict=font, loc='center')
        if len(len_h_data):
            font = {'color': self.color, 'size': 10}
            plt.title('宝宝昵称:%s|记录:%s-%s条' % (self.b_n, len(self.o_d), len(len_h_data)), fontdict=font, loc='left')
            plt.title('注:图中百分数表示%s超过同龄%s童数的比例' %
                      (('身高' if start_y else '身长'), ('女' if self.g == 'girls' else '男')),
                      fontdict={'color': self.color, 'size': 10}, loc='right')
        # 设置x轴标签
        plt.xticks(np.linspace(start=min_num, stop=max_num, num=12 * (end_y - start_y) + 1),
                   ['出生' if i == 0 else '' if (i % 12) % 3 != 0 else int(i) if i % 12 != 0
                   else '$\mathbf{%d}$岁' % (i // 12)
                    for i in np.linspace(start=start_y * 12, stop=end_y * 12, num=12 * (end_y - start_y) + 1)],
                   color=self.color)

        # 设置y轴标签
        plt.yticks(np.linspace(y_tap[0], y_tap[1], count_y),
                   ['$%.1f$' % ii for ii in np.linspace(y_tap[0], y_tap[1], count_y)], color=self.color)
        plt.ylabel('%s(厘米)' % ('身高' if start_y else '身长'), fontdict=font)
        # 模拟绘制X轴的主刻度网格线
        for index, value in enumerate(np.linspace(start=min_num, stop=max_num, num=12 * (end_y - start_y) + 1)):
            if index != 0 and index != 24 and index % 3 == 0:
                plt.plot([value] * len(list(range(y_tap[0], y_tap[1] + 1))),
                         list(range(y_tap[0], y_tap[1] + 1)),
                         linewidth=1, c=self.color)
        ax = plt.gca()  # 获取边框
        ax.spines['top'].set_color(self.color)
        ax.spines['right'].set_color(self.color)
        ax.spines['left'].set_color(self.color)
        ax.spines['bottom'].set_color(self.color)
        ax.spines['bottom'].set_linewidth(1.2)
        ax.spines['left'].set_linewidth(1.2)
        ax.spines['top'].set_linewidth(1.2)
        ax.spines['right'].set_linewidth(1.2)
        ax.yaxis.set_minor_locator(MultipleLocator(1))
        ax.xaxis.grid(True, which='major', linewidth=0.7, color=self.grid_color)  # 使用主刻度绘制x坐标轴的网格
        ax.yaxis.grid(True, which='minor', linewidth=0.7, color=self.grid_color)  # 使用次刻度绘制y坐标轴的网格
        ax.yaxis.grid(True, which='major', linewidth=1.2, color=self.color)  # 使用主刻度绘制y坐标轴的网格
        ax.set_axisbelow(True)
        ax.xaxis.tick_top()

        day_data_list = self.get_observe_days(date_str_data)

        # 身长或者身高的数值以及百分位数
        length_height = []

        # 开始添加监测的散点图
        if day_data_list and len_h_data:
            if len(len_h_data) >= 2:
                # 首先获取三次样条函数的值
                cube_d_data, cube_n_data = self.cubic_spline_interpolation(day_data_list, len_h_data)
                # 绘制发育曲线
                plt.plot(cube_d_data, cube_n_data, '-', lw=3, c='tab:red')

            # 绘制三次，形成比较好看的散点线图
            marker_style = dict(color=self.line_color, marker='o',  markersize=10,
                                markerfacecoloralt=self.line_color, lw=0)
            plt.plot(day_data_list, len_h_data, fillstyle='full', **marker_style)
            marker_style = dict(color='w', marker='o', markersize=7,
                                markerfacecoloralt=self.line_color, lw=0)
            plt.plot(day_data_list, len_h_data, fillstyle='full', **marker_style)
            marker_style = dict(color=self.line_color,  marker='o', markersize=4,
                                markerfacecoloralt=self.line_color, lw=0)
            plt.plot(day_data_list, len_h_data, fillstyle='full', **marker_style)

            # 百分位数
            percent_list = []

            for d_d, d_n, n_n in zip(day_data_list, len_h_data, range(len(day_data_list))):
                # 首先获取标准的数据列表
                day_data = p_data[p_data['Day'] == d_d]
                # 标准百分位列表
                stand_list = list(p_data.keys())[4:]
                s_number_list = [day_data[j].values[0] for j in stand_list]
                # 计算百分位数
                p_percent = self.computer_p(d_n, s_number_list, stand_list)
                percent_list.append(p_percent)
                bbox_props = dict(boxstyle="round4", fc="k", ec="3", alpha=0.6)

                if n_n < len(day_data_list) / 2 or d_d < (min_num + max_num) / 2:
                    # 百分位数
                    plt.text(d_d+4, d_n-1, '$\mathbf{%s\\%%}$' % p_percent, size=10,
                             color='r', bbox=bbox_props, style='italic', ha='left', va='top', wrap=True)
                    # 序号
                    if d_d == min_num:
                        plt.text(d_d+3, d_n+1, '$\mathbf{%d}$' % (n_n + 1), size=7, color='k', ha='left',
                                 va='bottom', bbox=dict(boxstyle="circle", fc=self.color, ec="3", alpha=0.6))
                    else:
                        plt.text(d_d, d_n+1, '$\mathbf{%d}$' % (n_n + 1), size=7, color='k', ha='center',
                                 va='bottom', bbox=dict(boxstyle="circle", fc=self.color, ec="3", alpha=0.6))
                else:
                    # 百分位数
                    plt.text(d_d-4, d_n+1, '$\mathbf{%s\\%%}$' % p_percent, size=10,
                             color='r', bbox=bbox_props, style='italic', ha='right', va='bottom', wrap=True)
                    # 序号
                    if d_d == max_num:
                        plt.text(d_d-3, d_n-1, '$\mathbf{%d}$' % (n_n + 1), size=7, color='k', ha='right',
                                 va='top', bbox=dict(boxstyle="circle", fc=self.color, ec="3", alpha=0.6))
                    else:
                        plt.text(d_d, d_n-1, '$\mathbf{%d}$' % (n_n + 1), size=7, color='k', ha='center',
                                 va='top', bbox=dict(boxstyle="circle", fc=self.color, ec="3", alpha=0.6))
            # 监测的日期天数
            observe_day_list = self.get_observe_days(self.o_d)
            # 添加数据列表
            # 首先固定位置新的图片
            ax2 = fig.add_axes(list(data_loc))  # 图中图
            # 背景透明
            ax2.patch.set_alpha(0.1)
            # 去掉坐标轴
            ax2.set_axis_off()
            # 添加表格列名
            colLabels = ['序号', '日期', '年龄', '%s(百分位)' % ('身高' if start_y else '身长'), '参考说明']
            # 添加表格内容
            cellText = []
            if day_data_list[0] != 1:
                if start_y == 0:  # 0-2生日没有监测数值
                    len_h_data.insert(0, '')
                    date_list = [self.b_d_str] + date_str_data
                    percent_list.insert(0, '<0')
                else:  # 2-5，
                    if observe_day_list[0] != 1:  # 生日没有监测数值
                        len_h_data.insert(0, '')
                        date_list = [self.b_d_str] + date_str_data
                        percent_list.insert(0, '<0')
                    else:  # 生日有监测数值
                        len_h_data.insert(0, self.o_l[0])
                        date_list = [self.b_d_str] + date_str_data
                        # 首先获取标准的数据列表
                        day_data = p_data[p_data['Day'] == 0]
                        # 标准百分位列表
                        stand_list = list(p_data.keys())[4:]
                        s_number_list = [day_data[j].values[0] for j in stand_list]
                        # 计算百分位数
                        p_percent = self.computer_p(self.o_l[0], s_number_list, stand_list)
                        percent_list.insert(0, p_percent)
            else:  # 生日有监测数值
                date_list = date_str_data
            # 不管生日是否有监测数值，都要添加生日
            length_o = len(date_list)

            for i in range(length_o):
                p_number = percent_list[i]  # 获取百分位数
                doc = ''  # 参考信息
                if p_number[0] in ['<', '>']:
                    f_doc = p_number[0]
                    p_number = float(percent_list[i][1:])
                else:
                    f_doc = ''
                    p_number = float(percent_list[i])
                # 根据生日是否有监测数值，判断是否给与序号
                if i == 0:
                    if p_number:  # 生日有监测数值
                        if 0 < p_number < 3:
                            doc = '宫内发育迟缓'
                        elif p_number > 97:
                            doc = '宫内生长过速'
                        else:
                            doc = '正常新生儿'
                    if start_y == 0:  # 02有序号
                        rowText = [' 1' if doc else '  ', '$%s$' % self.b_d_str, '出生',
                                   '$%s(%s%s\\%%)$' % (len_h_data[i], f_doc, p_number) if len_h_data[i] else '', doc]
                    else:  # 2-5没序号
                        rowText = [' ' if doc else '  ', '$%s$' % self.b_d_str, '出生',
                                   '$%s(%s%s\\%%)$' % (len_h_data[i], f_doc, p_number) if len_h_data[i] else '', doc]
                    length_height.append('$%s(%s%s\\%%)$' % (len_h_data[i], f_doc, p_number) if len_h_data[i] else '')
                else:
                    if p_number < 3:
                        doc = '发育迟缓'
                    elif p_number > 97:
                        doc = '生长过速'
                    else:
                        if 3 <= p_number < 20:
                            doc = '正常：矮'
                        elif 20 <= p_number < 40:
                            doc = '正常：偏矮'
                        elif 40 <= p_number <= 60:
                            doc = '正常：标准'
                        elif 60 < p_number <= 80:
                            doc = '正常：偏高'
                        elif 80 < p_number:
                            doc = '正常：高'
                    if start_y == 0:
                        if day_data_list[0] != 1:
                            rowText = [' %s' % i, '$%s$' % date_list[i],
                                       self.get_date_sub(self.b_d_str, date_list[i]),
                                       '$%s(%s%s\\%%)$' % (len_h_data[i], f_doc, p_number), doc]
                        else:
                            rowText = [' %s' % (i + 1), '$%s$' % date_list[i],
                                       self.get_date_sub(self.b_d_str, date_list[i]),
                                       '$%s(%s%s\\%%)$' % (len_h_data[i], f_doc, p_number), doc]
                    else:
                        rowText = [' %s' % i, '$%s$' % date_list[i], self.get_date_sub(self.b_d_str, date_list[i]),
                                   '$%s(%s%s\\%%)$' % (len_h_data[i], f_doc, p_number), doc]

                    length_height.append('$%s(%s%s\\%%)$' % (len_h_data[i], f_doc, p_number))
                cellText.append(rowText)
            if length_o >= max_table:
                table = ax2.table(cellText=cellText, colLabels=colLabels, loc='upper center', cellLoc='left',
                                  colWidths=list(table_w))
            else:
                table = ax2.table(cellText=cellText, colLabels=colLabels, loc='lower center', cellLoc='left',
                                  colWidths=list(table_w))
            table.auto_set_font_size(False)
            table.set_fontsize(8)
            table_props = table.properties()
            table_cells = table_props['child_artists']
            for cell in table_cells:
                cell._text.set_color(self.color)
                cell.set_edgecolor(self.color)
        fig = plt.gcf()
        fig.savefig(r'%s/%s.png' % (self.path_name, fig_name), dpi=100, bbox_inches='tight')
        return length_height

    def plot_p_data_wfa(self, weight_data, data_str_data, p_data, fig_name, start_y, end_y, min_num, max_num,
                        fig_size, count_y, y_tap, data_loc, table_w):
        """
        绘制体重数据的函数
        :param weight_data: 监测值列表
        :param data_str_data: 监测日期列表
        :param p_data: 总的数据
        :param fig_name: 图片名称
        :param start_y: 绘制开始的岁
        :param end_y: 绘制结束的岁
        :param min_num: 需要绘制的天数的最小值
        :param max_num: 需要绘制的天数的最大值
        :param fig_size: 图片尺寸
        :param count_y: y轴的标签的个数
        :param y_tap: y轴的绘制区间
        :param data_loc: 绘制监测数据的图的位置
        :param table_w: 表格的各个列的宽度
        :return: 绘制的图
        """
        # 首先更改列名
        p_data = p_data.rename(columns={'P01': 'P0.1', 'P999': 'P99.9'})
        # 新建图片
        fig = plt.figure(figsize=fig_size)
        # 绘制
        for value in self.who_plot_curve:
            if value in ['P3', 'P50', 'P97']:  # 比较特殊的三条曲线
                lw = 2.2
                sign = 1
            else:
                lw = 0.9
                sign = 0
            # 曲线粗度
            plt.plot(p_data['Age'].values, p_data[value].values, lw=lw, c=self.color)
            # 为曲线添加说明
            if sign:
                plt.text(max_num, p_data[p_data['Age'] == max_num][value].values[-1] - 0.5,
                         '$\mathbf{%s\\%%}$' % value[1:],
                         color=self.color, size='small', ha='left')
            else:
                plt.text(max_num, p_data[p_data['Age'] == max_num][value].values[-1] - 0.5,
                         '$%s\\%%$' % value[1:],
                         color=self.color, size='small', ha='left')
        # 设置坐标区间
        plt.ylim(y_tap)
        plt.xlim((min_num, max_num))
        minorticks_on()
        tick_params(axis='y', which='major', width=1, length=4, colors=self.color)
        tick_params(axis='x', which='major', width=1, length=2, colors=self.color)
        tick_params(which='minor', length=0)
        # 设置题目
        font = {'color': self.color, 'weight': 'bold', 'size': 14}
        plt.title(('出生' if not start_y else '$%d$' % start_y)
                  + '至$%d$岁%s（体重）发育百分位数标准曲线($WHO$版)\n' % (end_y, s_d.GENDER[self.g]),
                  fontdict=font, loc='center')
        if len(weight_data):
            font = {'color': self.color, 'size': 10}
            plt.title('宝宝昵称:%s|记录:%s条' % (self.b_n, len(weight_data)), fontdict=font, loc='left')
            plt.title('注:图中百分数表示体重超过同龄%s童数的比例' % ('女' if self.g == 'girls' else '男'),
                      fontdict={'color': self.color, 'size': 10}, loc='right')
        # 设置x轴标签
        plt.xticks(np.linspace(start=min_num, stop=max_num, num=12 * (end_y - start_y) + 1),
                   ['出生' if i == 0 else '' if (i % 12) % 3 != 0 else int(i) if i % 12 != 0
                   else '$\mathbf{%d}$岁' % (i // 12)
                    for i in np.linspace(start=start_y * 12, stop=end_y * 12, num=12 * (end_y - start_y) + 1)],
                   color=self.color)

        # 设置y轴标签
        plt.yticks(np.linspace(y_tap[0], y_tap[1], count_y), np.linspace(y_tap[0], y_tap[1], count_y), color=self.color)
        plt.ylabel('体重(千克)', fontdict=font)
        # 模拟绘制X轴的主刻度网格线
        for index, value in enumerate(np.linspace(start=min_num, stop=max_num, num=12 * (end_y - start_y) + 1)):
            if index != 0 and index != 24 and index % 3 == 0:
                plt.plot([value] * len(list(range(y_tap[0], y_tap[1] + 1))), list(range(y_tap[0], y_tap[1] + 1)),
                         linewidth=1, c=self.color)
        ax = plt.gca()  # 获取边框
        ax.spines['top'].set_color(self.color)
        ax.spines['right'].set_color(self.color)
        ax.spines['left'].set_color(self.color)
        ax.spines['bottom'].set_color(self.color)
        ax.spines['bottom'].set_linewidth(1.2)
        ax.spines['left'].set_linewidth(1.2)
        ax.spines['top'].set_linewidth(1.2)
        ax.spines['right'].set_linewidth(1.2)
        ax.yaxis.set_minor_locator(MultipleLocator(1))
        ax.xaxis.grid(True, which='major', linewidth=0.7, color=self.grid_color)  # 使用主刻度绘制x坐标轴的网格
        ax.yaxis.grid(True, which='minor', linewidth=0.7, color=self.grid_color)  # 使用次刻度绘制y坐标轴的网格
        ax.yaxis.grid(True, which='major', linewidth=1.2, color=self.color)  # 使用主刻度绘制y坐标轴的网格
        ax.set_axisbelow(True)
        #ax.xaxis.tick_top()

        day_data_list = self.get_observe_days(data_str_data)

        weight_list = []

        # 开始添加监测的散点图
        if day_data_list and weight_data:
            if len(weight_data) >= 2:
                # 首先获取三次样条函数的值
                cube_d_data, cube_n_data = self.cubic_spline_interpolation(day_data_list, weight_data)
                # 绘制发育曲线
                plt.plot(cube_d_data, cube_n_data, '-', lw=3, c='tab:red')

            # 绘制三次，形成比较好看的散点线图
            marker_style = dict(color=self.line_color, marker='o',  markersize=10,
                                markerfacecoloralt=self.line_color, lw=0)
            plt.plot(day_data_list, weight_data, fillstyle='full', **marker_style)
            marker_style = dict(color='w', marker='o', markersize=7,
                                markerfacecoloralt=self.line_color, lw=0)
            plt.plot(day_data_list, weight_data, fillstyle='full', **marker_style)
            marker_style = dict(color=self.line_color,  marker='o', markersize=4,
                                markerfacecoloralt=self.line_color, lw=0)
            plt.plot(day_data_list, weight_data, fillstyle='full', **marker_style)

            # 百分位数
            percent_list = []

            for d_d, d_n, n_n in zip(day_data_list, weight_data, range(len(day_data_list))):
                # 首先获取标准的数据列表
                day_data = p_data[p_data['Age'] == d_d]
                # 标准百分位列表
                stand_list = list(p_data.keys())[4:]
                s_number_list = [day_data[j].values[0] for j in stand_list]
                # 计算百分位数
                p_percent = self.computer_p(d_n, s_number_list, stand_list)
                percent_list.append(p_percent)
                bbox_props = dict(boxstyle="round4", fc="k", ec="3", alpha=0.6)

                if n_n < len(day_data_list) / 2 or d_d < (min_num + max_num) / 2:
                    # 百分位数
                    plt.text(d_d+4, d_n-.5, '$\mathbf{%s\\%%}$' % p_percent, size=10,
                             color='r', bbox=bbox_props, style='italic', ha='left', va='top', wrap=True)
                    # 序号
                    if d_d == min_num:
                        plt.text(d_d+3, d_n+.5, '$\mathbf{%d}$' % (n_n + 1), size=7, color='k', ha='left',
                                 va='bottom', bbox=dict(boxstyle="circle", fc=self.color, ec="3", alpha=0.6))
                    else:
                        plt.text(d_d, d_n+.5, '$\mathbf{%d}$' % (n_n + 1), size=7, color='k', ha='center',
                                 va='bottom', bbox=dict(boxstyle="circle", fc=self.color, ec="3", alpha=0.6))
                else:
                    # 百分位数
                    plt.text(d_d-4, d_n+.5, '$\mathbf{%s\\%%}$' % p_percent, size=10,
                             color='r', bbox=bbox_props, style='italic', ha='right', va='bottom', wrap=True)
                    # 序号
                    if d_d == max_num:
                        plt.text(d_d-3, d_n-.5, '$\mathbf{%d}$' % (n_n + 1), size=7, color='k', ha='right',
                                 va='top', bbox=dict(boxstyle="circle", fc=self.color, ec="3", alpha=0.6))
                    else:
                        plt.text(d_d, d_n-.5, '$\mathbf{%d}$' % (n_n + 1), size=7, color='k', ha='center',
                                 va='top', bbox=dict(boxstyle="circle", fc=self.color, ec="3", alpha=0.6))
            # 添加数据列表
            # 首先固定位置新的图片
            ax2 = fig.add_axes(list(data_loc))  # 图中图
            # 背景透明
            ax2.patch.set_alpha(0.3)
            # 去掉坐标轴
            ax2.set_axis_off()
            # 添加表格列名
            colLabels = ['序号', '日期', '年龄', '体重(百分位)', '参考说明']
            # 添加表格内容
            cellText = []
            if day_data_list[0] != 1:
                weight_data.insert(0, '')
                date_list = [self.b_d_str] + data_str_data
                percent_list.insert(0, '<0')
            else:
                date_list = data_str_data
            length_o = len(date_list)

            for i in range(length_o):
                p_number = percent_list[i]
                doc = ''
                if p_number[0] in ['<', '>']:
                    f_doc = p_number[0]
                    p_number = float(percent_list[i][1:])
                else:
                    f_doc = ''
                    p_number = float(percent_list[i])
                if i == 0:
                    if start_y == 0:
                        if p_number:
                            if 0 < p_number < 3:
                                doc = '宫内发育迟缓'
                            elif p_number > 97:
                                doc = '宫内生长过速'
                            else:
                                doc = '正常新生儿'
                        rowText = [' 1' if doc else '  ', '$%s$' % self.b_d_str, '出生',
                                   '$%s(%s\\%%)$' % (weight_data[i], p_number) if weight_data[i] else '', doc]
                        weight_list.append('$%s(%s%s\\%%)$' % (weight_data[i], f_doc, p_number)
                                           if weight_data[i] else '', )
                    else:
                        rowText = ['  ', '$%s$' % self.b_d_str, '出生', '', '']
                        weight_list.append('')
                else:
                    if p_number < 3:
                        doc = '发育迟缓'
                    elif p_number > 97:
                        doc = '生长过速'
                    else:
                        if 3 <= p_number < 20:
                            doc = '正常：轻'
                        elif 20 <= p_number < 40:
                            doc = '正常：偏轻'
                        elif 40 <= p_number <= 60:
                            doc = '正常：标准'
                        elif 60 < p_number <= 80:
                            doc = '正常：偏重'
                        elif 80 < p_number:
                            doc = '正常：重'
                    if day_data_list[0] != 1:
                        rowText = [' %s' % i, '$%s$' % date_list[i], self.get_date_sub(self.b_d_str, date_list[i]),
                                   '$%s(%s%s\\%%)$' % (weight_data[i], f_doc, p_number), doc]
                        weight_list.append('$%s(%s%s\\%%)$' % (weight_data[i], f_doc, p_number))
                    else:
                        rowText = [' %s' % (i + 1), '$%s$' % date_list[i],
                                   self.get_date_sub(self.b_d_str, date_list[i]),
                                   '$%s(%s%s\\%%)$' % (weight_data[i], f_doc, p_number), doc]
                        weight_list.append('$%s(%s%s\\%%)$' % (weight_data[i], f_doc, p_number))
                cellText.append(rowText)

            table = ax2.table(cellText=cellText, colLabels=colLabels, loc='upper center', cellLoc='left',
                              colWidths=list(table_w))

            table.auto_set_font_size(False)
            table.set_fontsize(8)
            table_props = table.properties()
            table_cells = table_props['child_artists']
            for cell in table_cells:
                cell._text.set_color(self.color)
                cell.set_edgecolor(self.color)
        fig = plt.gcf()
        fig.savefig(r'%s/%s.png' % (self.path_name, fig_name), dpi=100, bbox_inches='tight')
        return weight_list

    def plot_p_data_hcfa(self, head_c_data, date_str_data, p_data, fig_name, start_y, end_y, min_num, max_num,
                         fig_size, count_y, y_tap, data_loc, table_w, max_table):
        """
        绘制头围数据的函数
        :param head_c_data: 监测值列表
        :param date_str_data: 监测日期列表
        :param p_data: 总的数据
        :param fig_name: 图片名称
        :param start_y: 绘制开始的岁
        :param end_y: 绘制结束的岁
        :param min_num: 需要绘制的天数的最小值
        :param max_num: 需要绘制的天数的最大值
        :param fig_size: 图片尺寸
        :param count_y: y轴的标签的个数
        :param y_tap: y轴的绘制区间
        :param data_loc: 绘制监测数据的图的位置
        :param table_w: 表格的各个列的宽度
        :param max_table: 表格最大行数
        :return: 绘制的图
        """
        # 首先更改列名
        p_data = p_data.rename(columns={'P01': 'P0.1', 'P999': 'P99.9'})
        # 新建图片
        fig = plt.figure(figsize=fig_size)
        # 绘制
        for value in self.who_plot_curve:
            if value in ['P3', 'P50', 'P97']:  # 比较特殊的三条曲线
                lw = 2.2
                sign = 1
            else:
                lw = 0.9
                sign = 0
            # 曲线粗度
            plt.plot(p_data['Age'].values, p_data[value].values, lw=lw, c=self.color)
            # 为曲线添加说明
            if sign:
                plt.text(max_num, p_data[p_data['Age'] == max_num][value].values[-1] - 0.5,
                         '$\mathbf{%s\\%%}$' % value[1:],
                         color=self.color, size='small', ha='left')
            else:
                plt.text(max_num, p_data[p_data['Age'] == max_num][value].values[-1] - 0.5,
                         '$%s\\%%$' % value[1:],
                         color=self.color, size='small', ha='left')
        # 设置坐标区间
        plt.ylim(y_tap)
        plt.xlim((min_num, max_num))
        minorticks_on()
        tick_params(axis='y', which='major', width=1, length=4, colors=self.color)
        tick_params(axis='x', which='major', width=1, length=2, colors=self.color)
        tick_params(which='minor', length=0)
        # 设置题目
        font = {'color': self.color, 'weight': 'bold', 'size': 14}
        plt.title(('出生' if not start_y else '$%d$' % start_y)
                  + '至$%d$岁%s（头围）发育百分位数标准曲线(WHO版)\n' % (end_y, s_d.GENDER[self.g]),
                  fontdict=font, loc='center')
        if len(head_c_data):
            font = {'color': self.color, 'size': 10}
            plt.title('宝宝昵称:%s|记录:%s条' % (self.b_n, len(head_c_data)), fontdict=font, loc='left')
            plt.title('注:图中百分数表示头围超过同龄%s童数的比例' % ('女' if self.g == 'girls' else '男'),
                      fontdict={'color': self.color, 'size': 10}, loc='right')
        # 设置x轴标签
        plt.xticks(np.linspace(start=min_num, stop=max_num, num=12 * (end_y - start_y) + 1),
                   ['出生' if i == 0 else '' if (i % 12) % 3 != 0 else int(i) if i % 12 != 0
                   else '$\mathbf{%d}$岁' % (i // 12)
                    for i in np.linspace(start=start_y * 12, stop=end_y * 12, num=12 * (end_y - start_y) + 1)],
                   color=self.color)

        # 设置y轴标签
        plt.yticks(np.linspace(y_tap[0], y_tap[1], count_y), np.linspace(y_tap[0], y_tap[1], count_y), color=self.color)
        plt.ylabel('头围(厘米)', fontdict=font)
        # 模拟绘制X轴的主刻度网格线
        for index, value in enumerate(np.linspace(start=min_num, stop=max_num, num=12 * (end_y - start_y) + 1)):
            if index != 0 and index != 24 and index % 3 == 0:
                plt.plot([value] * len(list(range(y_tap[0], y_tap[1] + 1))), list(range(y_tap[0], y_tap[1] + 1)),
                         linewidth=1, c=self.color)
        ax = plt.gca()  # 获取边框
        ax.spines['top'].set_color(self.color)
        ax.spines['right'].set_color(self.color)
        ax.spines['left'].set_color(self.color)
        ax.spines['bottom'].set_color(self.color)
        ax.spines['bottom'].set_linewidth(1.2)
        ax.spines['left'].set_linewidth(1.2)
        ax.spines['top'].set_linewidth(1.2)
        ax.spines['right'].set_linewidth(1.2)
        ax.yaxis.set_minor_locator(MultipleLocator(1))
        ax.xaxis.grid(True, which='major', linewidth=0.7, color=self.grid_color)  # 使用主刻度绘制x坐标轴的网格
        ax.yaxis.grid(True, which='minor', linewidth=0.7, color=self.grid_color)  # 使用次刻度绘制y坐标轴的网格
        ax.yaxis.grid(True, which='major', linewidth=1.2, color=self.color)  # 使用主刻度绘制y坐标轴的网格
        ax.set_axisbelow(True)
        ax.xaxis.tick_top()

        day_data_list = self.get_observe_days(date_str_data)

        # 开始添加监测的散点图
        if day_data_list and head_c_data:
            if len(head_c_data) >= 2:
                # 首先获取三次样条函数的值
                cube_d_data, cube_n_data = self.cubic_spline_interpolation(day_data_list, head_c_data)
                # 绘制发育曲线
                plt.plot(cube_d_data, cube_n_data, '-', lw=3, c='tab:red')

            # 绘制三次，形成比较好看的散点线图
            marker_style = dict(color=self.line_color, marker='o',  markersize=10,
                                markerfacecoloralt=self.line_color, lw=0)
            plt.plot(day_data_list, head_c_data, fillstyle='full', **marker_style)
            marker_style = dict(color='w', marker='o', markersize=7,
                                markerfacecoloralt=self.line_color, lw=0)
            plt.plot(day_data_list, head_c_data, fillstyle='full', **marker_style)
            marker_style = dict(color=self.line_color,  marker='o', markersize=4,
                                markerfacecoloralt=self.line_color, lw=0)
            plt.plot(day_data_list, head_c_data, fillstyle='full', **marker_style)

            # 百分位数
            percent_list = []

            for d_d, d_n, n_n in zip(day_data_list, head_c_data, range(len(day_data_list))):
                # 首先获取标准的数据列表
                day_data = p_data[p_data['Age'] == d_d]
                # 标准百分位列表
                stand_list = list(p_data.keys())[4:]
                s_number_list = [day_data[j].values[0] for j in stand_list]
                # 计算百分位数
                p_percent = self.computer_p(d_n, s_number_list, stand_list)
                percent_list.append(p_percent)
                bbox_props = dict(boxstyle="round4", fc="k", ec="3", alpha=0.6)

                if n_n < len(day_data_list) / 2 or d_d < (min_num + max_num) / 2:
                    # 百分位数
                    plt.text(d_d+4, d_n-.5, '$\mathbf{%s\\%%}$' % p_percent, size=10,
                             color='r', bbox=bbox_props, style='italic', ha='left', va='top', wrap=True)
                    # 序号
                    if d_d == min_num:
                        plt.text(d_d+3, d_n+.5, '$\mathbf{%d}$' % (n_n + 1), size=7, color='k', ha='left',
                                 va='bottom', bbox=dict(boxstyle="circle", fc=self.color, ec="3", alpha=0.6))
                    else:
                        plt.text(d_d, d_n+.5, '$\mathbf{%d}$' % (n_n + 1), size=7, color='k', ha='center',
                                 va='bottom', bbox=dict(boxstyle="circle", fc=self.color, ec="3", alpha=0.6))
                else:
                    # 百分位数
                    plt.text(d_d-4, d_n+.5, '$\mathbf{%s\\%%}$' % p_percent, size=10,
                             color='r', bbox=bbox_props, style='italic', ha='right', va='bottom', wrap=True)
                    # 序号
                    if d_d == max_num:
                        plt.text(d_d-3, d_n-.5, '$\mathbf{%d}$' % (n_n + 1), size=7, color='k', ha='right',
                                 va='top', bbox=dict(boxstyle="circle", fc=self.color, ec="3", alpha=0.6))
                    else:
                        plt.text(d_d, d_n-.5, '$\mathbf{%d}$' % (n_n + 1), size=7, color='k', ha='center',
                                 va='top', bbox=dict(boxstyle="circle", fc=self.color, ec="3", alpha=0.6))
            # 添加数据列表
            # 首先固定位置新的图片
            ax2 = fig.add_axes(list(data_loc))  # 图中图
            # 背景透明
            ax2.patch.set_alpha(0.3)
            # 去掉坐标轴
            ax2.set_axis_off()
            # 添加表格列名
            colLabels = ['序号', '日期', '年龄', '头围(百分位)', '参考说明']
            # 添加表格内容
            cellText = []
            if day_data_list[0] != 1:
                head_c_data.insert(0, '')
                date_list = [self.b_d_str] + date_str_data
                percent_list.insert(0, '<0')
            else:
                date_list = date_str_data
            length_o = len(date_list)

            for i in range(length_o):
                p_number = percent_list[i]
                doc = ''
                f_doc = ''
                if p_number[0] in ['<', '>']:
                    f_doc = p_number[0]
                    p_number = float(percent_list[i][1:])
                else:
                    p_number = float(percent_list[i])
                if i == 0:
                    if start_y == 0:
                        if p_number:
                            if 0 < p_number < 3:
                                doc = '宫内发育迟缓'
                            elif p_number > 97:
                                doc = '宫内生长过速'
                            else:
                                doc = '正常新生儿'
                        rowText = [' 1' if doc else '  ', '$%s$' % self.b_d_str, '出生',
                                   '$%s(%s%s\\%%)$' % (head_c_data[i], f_doc, p_number)
                                   if head_c_data[i] else '', doc]
                    else:
                        rowText = ['  ', '$%s$' % self.b_d_str, '出生', '', '']
                else:
                    if p_number < 3:
                        doc = '发育迟缓'
                    elif p_number > 97:
                        doc = '生长过速'
                    else:
                        if 3 <= p_number < 20:
                            doc = '正常：短'
                        elif 20 <= p_number < 40:
                            doc = '正常：偏短'
                        elif 40 <= p_number <= 60:
                            doc = '正常：标准'
                        elif 60 < p_number <= 80:
                            doc = '正常：偏长'
                        elif 80 < p_number:
                            doc = '正常：长'
                    if day_data_list[0] != 1:
                        rowText = [' %s' % i, '$%s$' % date_list[i], self.get_date_sub(self.b_d_str, date_list[i]),
                                   '$%s(%s%s\\%%)$' % (head_c_data[i], f_doc, p_number), doc]
                    else:
                        rowText = [' %s' % (i + 1), '$%s$' % date_list[i],
                                   self.get_date_sub(self.b_d_str, date_list[i]),
                                   '$%s(%s%s\\%%)$' % (head_c_data[i], f_doc, p_number), doc]
                cellText.append(rowText)

            if length_o >= max_table:
                table = ax2.table(cellText=cellText, colLabels=colLabels, loc='upper center', cellLoc='left',
                                  colWidths=list(table_w))
            else:
                table = ax2.table(cellText=cellText, colLabels=colLabels, loc='lower center', cellLoc='left',
                                  colWidths=list(table_w))

            table.auto_set_font_size(False)
            table.set_fontsize(8)
            table_props = table.properties()
            table_cells = table_props['child_artists']
            for cell in table_cells:
                cell._text.set_color(self.color)
                cell.set_edgecolor(self.color)
        fig = plt.gcf()
        fig.savefig(r'%s/%s.png' % (self.path_name, fig_name), dpi=100, bbox_inches='tight')


    def plot_p_data_bfa(self, bfa_data, date_str_data, p_data, l_h_doc, w_doc, fig_name, start_y,
                        end_y, min_num, max_num, fig_size, count_y, y_tap, data_loc, table_w, max_table):
        """
        绘制体重指数数据的函数
        :param bfa_data: 监测值列表
        :param date_str_data: 监测日期列表
        :param p_data: 总的数据
        :param l_h_doc: 身长身高数据
        :param w_doc: 体重数据
        :param fig_name: 图片名称
        :param start_y: 绘制开始的岁
        :param end_y: 绘制结束的岁
        :param min_num: 需要绘制的天数的最小值
        :param max_num: 需要绘制的天数的最大值
        :param fig_size: 图片尺寸
        :param count_y: y轴的标签的个数
        :param y_tap: y轴的绘制区间
        :param data_loc: 绘制监测数据的图的位置
        :param table_w: 表格的各个列的宽度
        :param max_table: 表格最大行数
        :return: 绘制的图
        """
        # 首先更改列名
        p_data = p_data.rename(columns={'P01': 'P0.1', 'P999': 'P99.9'})
        # 新建图片
        fig = plt.figure(figsize=fig_size)
        # 绘制
        for value in self.who_plot_curve:
            if value in ['P3', 'P50', 'P97']:  # 比较特殊的三条曲线
                lw = 2.2
                sign = 1
            else:
                lw = 0.9
                sign = 0
            # 曲线粗度
            plt.plot(p_data['Age'].values, p_data[value].values, lw=lw, c=self.color)
            # 为曲线添加说明
            if sign:
                plt.text(max_num, p_data[p_data['Age'] == max_num][value].values[-1] - 0.5,
                         '$\mathbf{%s\\%%}$' % value[1:],
                         color=self.color, size='small', ha='left')
            else:
                plt.text(max_num, p_data[p_data['Age'] == max_num][value].values[-1] - 0.5,
                         '$%s\\%%$' % value[1:],
                         color=self.color, size='small', ha='left')
        # 设置坐标区间
        plt.ylim(y_tap)
        plt.xlim((min_num, max_num))
        minorticks_on()
        tick_params(axis='y', which='major', width=1, length=4, colors=self.color)
        tick_params(axis='x', which='major', width=1, length=2, colors=self.color)
        tick_params(which='minor', length=0)
        # 设置题目
        font = {'color': self.color, 'weight': 'bold', 'size': 14}
        plt.title(('出生' if not start_y else '$%d$' % start_y)
                  + '至$%d$岁%s（体重指数）发育百分位数曲线(WHO版)\n' % (end_y, s_d.GENDER[self.g]),
                  fontdict=font, loc='center')
        if len(bfa_data):
            font = {'color': self.color, 'size': 10}
            plt.title('宝宝昵称:%s|记录:%s条' % (self.b_n, len(bfa_data)), fontdict=font, loc='left')
            plt.title('注:图中百分数表示头围超过同龄儿童数的比例', fontdict={'color': self.color, 'size': 8}, loc='right')
        # 设置x轴标签
        plt.xticks(np.linspace(start=min_num, stop=max_num, num=12 * (end_y - start_y) + 1),
                   ['出生' if i == 0 else '' if (i % 12) % 3 != 0 else int(i) if i % 12 != 0
                   else '$\mathbf{%d}$岁' % (i // 12)
                    for i in np.linspace(start=start_y * 12, stop=end_y * 12, num=12 * (end_y - start_y) + 1)],
                   color=self.color)

        # 设置y轴标签
        plt.yticks(np.linspace(y_tap[0], y_tap[1], count_y),
                   np.linspace(y_tap[0], y_tap[1], count_y), color=self.color)
        plt.ylabel('体重指数', fontdict=font)
        # 模拟绘制X轴的主刻度网格线
        for index, value in enumerate(np.linspace(start=min_num, stop=max_num, num=12 * (end_y - start_y) + 1)):
            if index != 0 and index != 24 and index % 3 == 0:
                plt.plot([value] * len(list(range(y_tap[0], y_tap[1] + 1))), list(range(y_tap[0], y_tap[1] + 1)),
                         linewidth=1, c=self.color)
        ax = plt.gca()  # 获取边框
        ax.spines['top'].set_color(self.color)
        ax.spines['right'].set_color(self.color)
        ax.spines['left'].set_color(self.color)
        ax.spines['bottom'].set_color(self.color)
        ax.spines['bottom'].set_linewidth(1.2)
        ax.spines['left'].set_linewidth(1.2)
        ax.spines['top'].set_linewidth(1.2)
        ax.spines['right'].set_linewidth(1.2)
        ax.yaxis.set_minor_locator(MultipleLocator(1))
        ax.xaxis.grid(True, which='major', linewidth=0.7, color=self.grid_color)  # 使用主刻度绘制x坐标轴的网格
        ax.yaxis.grid(True, which='minor', linewidth=0.7, color=self.grid_color)  # 使用次刻度绘制y坐标轴的网格
        ax.yaxis.grid(True, which='major', linewidth=1.2, color=self.color)  # 使用主刻度绘制y坐标轴的网格
        ax.set_axisbelow(True)
        ax.xaxis.tick_top()

        day_data_list = self.get_observe_days(date_str_data)

        # 开始添加监测的散点图
        if day_data_list and bfa_data:
            if len(bfa_data) >= 2:
                # 首先获取三次样条函数的值
                cube_d_data, cube_n_data = self.cubic_spline_interpolation(day_data_list, bfa_data)
                # 绘制发育曲线
                plt.plot(cube_d_data, cube_n_data, '-', lw=3, c='tab:red')

            # 绘制三次，形成比较好看的散点线图
            marker_style = dict(color=self.line_color, marker='o',  markersize=10,
                                markerfacecoloralt=self.line_color, lw=0)
            plt.plot(day_data_list, bfa_data, fillstyle='full', **marker_style)
            marker_style = dict(color='w', marker='o', markersize=7,
                                markerfacecoloralt=self.line_color, lw=0)
            plt.plot(day_data_list, bfa_data, fillstyle='full', **marker_style)
            marker_style = dict(color=self.line_color,  marker='o', markersize=4,
                                markerfacecoloralt=self.line_color, lw=0)
            plt.plot(day_data_list, bfa_data, fillstyle='full', **marker_style)

            # 百分位数
            percent_list = []

            for d_d, d_n, n_n in zip(day_data_list, bfa_data, range(len(day_data_list))):
                # 首先获取标准的数据列表
                day_data = p_data[p_data['Age'] == d_d]
                # 标准百分位列表
                stand_list = list(p_data.keys())[4:]
                s_number_list = [day_data[j].values[0] for j in stand_list]
                # 计算百分位数
                p_percent = self.computer_p(d_n, s_number_list, stand_list)
                percent_list.append(p_percent)
                bbox_props = dict(boxstyle="round4", fc="k", ec="3", alpha=0.6)

                if n_n < len(day_data_list) / 2 or d_d < (min_num + max_num) / 2:
                    # 百分位数
                    plt.text(d_d+4, d_n-.5, '$\mathbf{%s\\%%}$' % p_percent, size=10,
                             color='r', bbox=bbox_props, style='italic', ha='left', va='top', wrap=True)
                    # 序号
                    if d_d == min_num:
                        plt.text(d_d+3, d_n+.5, '$\mathbf{%d}$' % (n_n + 1), size=7, color='k', ha='left',
                                 va='bottom', bbox=dict(boxstyle="circle", fc=self.color, ec="3", alpha=0.6))
                    else:
                        plt.text(d_d, d_n+.5, '$\mathbf{%d}$' % (n_n + 1), size=7, color='k', ha='center',
                                 va='bottom', bbox=dict(boxstyle="circle", fc=self.color, ec="3", alpha=0.6))
                else:
                    # 百分位数
                    plt.text(d_d-4, d_n+.5, '$\mathbf{%s\\%%}$' % p_percent, size=10,
                             color='r', bbox=bbox_props, style='italic', ha='right', va='bottom', wrap=True)
                    # 序号
                    if d_d == max_num:
                        plt.text(d_d-3, d_n-.5, '$\mathbf{%d}$' % (n_n + 1), size=7, color='k', ha='right',
                                 va='top', bbox=dict(boxstyle="circle", fc=self.color, ec="3", alpha=0.6))
                    else:
                        plt.text(d_d, d_n-.5, '$\mathbf{%d}$' % (n_n + 1), size=7, color='k', ha='center',
                                 va='top', bbox=dict(boxstyle="circle", fc=self.color, ec="3", alpha=0.6))
            # 添加数据列表
            # 首先固定位置新的图片
            ax2 = fig.add_axes(list(data_loc))  # 图中图
            # 背景透明
            ax2.patch.set_alpha(0.3)
            # 去掉坐标轴
            ax2.set_axis_off()
            # 添加表格列名
            if max(day_data_list) <= 730:
                ldoc = '身长(百分位)'
            elif min(day_data_list) >= 731:
                ldoc = '身高(百分位)'
            else:
                ldoc = '身长\高(百分位)'
            colLabels = ['序号', '日期', '年龄', ldoc, '体重(百分位)', '体重指数(百分位)', '参考信息']

            # 添加表格内容
            cellText = []
            if day_data_list[0] != 1:
                bfa_data.insert(0, '')
                date_list = [self.b_d_str] + date_str_data
                percent_list.insert(0, '<0')
            else:
                date_list = date_str_data
            length_o = len(date_list)

            for i in range(length_o):
                p_number = percent_list[i]
                doc = ''
                f_doc = ''
                if p_number[0] in ['<', '>']:
                    f_doc = p_number[0]
                    p_number = float(percent_list[i][1:])
                else:
                    p_number = float(percent_list[i])
                if i == 0:
                    if start_y == 0:
                        if p_number:
                            if 0 < p_number < 5:
                                doc = '体重不足'
                            elif p_number >= 95:
                                doc = '肥胖'
                            elif 85 < p_number < 95:
                                doc = '超重'
                            else:
                                doc = '正常'
                        rowText = [' 1' if doc else '  ', '$%s$' % self.b_d_str, '出生', l_h_doc[i], w_doc[i],
                                   '$%s(%s%s\\%%)$' % (bfa_data[i], f_doc, p_number) if bfa_data[i] else '', doc]
                    else:
                        rowText = ['  ', '$%s$' % self.b_d_str, '出生', '', '', '', '']
                else:
                    if p_number < 5:
                        doc = '体重不足'
                    elif p_number >= 95:
                        doc = '肥胖'
                    elif 85 < p_number < 95:
                        doc = '超重'
                    else:
                        doc = '正常'
                    if day_data_list[0] != 1:
                        rowText = [' %s' % i, '$%s$' % date_list[i], self.get_date_sub(self.b_d_str, date_list[i]),
                                   l_h_doc[i], w_doc[i],
                                   '$%s(%s%s\\%%)$' % (bfa_data[i], f_doc, p_number), doc]
                    else:
                        rowText = [' %s' % (i + 1), '$%s$' % date_list[i],
                                   self.get_date_sub(self.b_d_str, date_list[i]),
                                   l_h_doc[i], w_doc[i],
                                   '$%s(%s%s\\%%)$' % (bfa_data[i], f_doc, p_number), doc]
                cellText.append(rowText)

            if length_o >= max_table:
                table = ax2.table(cellText=cellText, colLabels=colLabels, loc='upper center', cellLoc='left',
                                  colWidths=list(table_w))
            else:
                table = ax2.table(cellText=cellText, colLabels=colLabels, loc='lower center', cellLoc='left',
                                  colWidths=list(table_w))

            table.auto_set_font_size(False)
            table.set_fontsize(8)
            table_props = table.properties()
            table_cells = table_props['child_artists']
            for cell in table_cells:
                cell._text.set_color(self.color)
                cell.set_edgecolor(self.color)
        fig = plt.gcf()
        fig.savefig(r'%s/%s.png' % (self.path_name, fig_name), dpi=100, bbox_inches='tight')

    def plot_p_data_wfl(self, weight_data_02, length_data_02, date_str_data_02, p_data, length_doc,
                        weight_doc, fig_name, start_y, end_y, min_num, max_num, fig_size,
                        count_y, y_tap, data_loc, table_w):
        """
        绘制身长别体重数据
        :param weight_data_02: 监测值列表：体重
        :param length_data_02: 监测值列表：身长
        :param date_str_data_02: 监测值列表：日期
        :param p_data: 总的数据
        :param length_doc: 身长信息
        :param weight_doc: 体重信息
        :param fig_name: 图片名称
        :param start_y: 绘制开始的岁
        :param end_y: 绘制结束的岁
        :param min_num: 需要绘制的身长的最小值
        :param max_num: 需要绘制的身长的最大值
        :param fig_size: 图片尺寸
        :param count_y: y轴的标签的个数
        :param y_tap: y轴的绘制区间
        :param data_loc: 绘制监测数据的图的位置
        :param table_w: 表格的各个列的宽度
        :return: 绘制的图
        """
        # 首先更改列名
        p_data = p_data.rename(columns={'P01': 'P0.1', 'P999': 'P99.9'})
        # 新建图片
        fig = plt.figure(figsize=fig_size)
        # 绘制
        for value in self.who_plot_curve:
            if value in ['P3', 'P50', 'P97']:  # 比较特殊的三条曲线
                lw = 2.2
                sign = 1
            else:
                lw = 0.9
                sign = 0
            # 曲线粗度
            plt.plot(p_data['Length'].values, p_data[value].values, lw=lw, c=self.color)
            # 为曲线添加说明
            if sign:
                plt.text(max_num, p_data[p_data['Length'] == max_num][value].values[-1] - 0.5,
                         '$\mathbf{%s\\%%}$' % value[1:],
                         color=self.color, size='small', ha='left')
            else:
                plt.text(max_num, p_data[p_data['Length'] == max_num][value].values[-1] - 0.5,
                         '$%s\\%%$' % value[1:],
                         color=self.color, size='small', ha='left')
        # 设置坐标区间
        plt.ylim(y_tap)
        plt.xlim((min_num, max_num))
        minorticks_on()
        tick_params(axis='y', which='major', width=1, length=4, colors=self.color)
        tick_params(axis='x', which='major', width=1, length=2, colors=self.color)
        tick_params(which='minor', length=0)
        # 设置题目
        font = {'color': self.color, 'weight': 'bold', 'size': 14}
        plt.title(('出生' if not start_y else '$%d$' % start_y)
                  + '至$%d$岁%s（身长别体重）发育百分位数曲线(WHO版)\n' % (end_y, s_d.GENDER[self.g]),
                  fontdict=font, loc='center')
        if len(weight_data_02):
            font = {'color': self.color, 'size': 10}
            plt.title('宝宝昵称:%s|记录:%s-%s条' % (self.b_n, len(self.o_d), len(weight_data_02)),
                      fontdict=font, loc='left')
            plt.title('注:图中百分数表示体重超过同身长%s童数的比例' % ('女' if self.g == 'girls' else '男'),
                      fontdict={'color': self.color, 'size': 8}, loc='right')

        # 设置x轴标签
        plt.xticks(np.linspace(start=min_num, stop=max_num, num=(max_num - min_num) // 5 + 1),
                   ['$%d$' % i for i in np.linspace(start=min_num, stop=max_num,
                                                    num=(max_num - min_num) // 5 + 1)],
                   color=self.color)

        # 设置y轴标签
        plt.yticks(np.linspace(y_tap[0], y_tap[1], count_y),
                   np.linspace(y_tap[0], y_tap[1], count_y), color=self.color)
        plt.ylabel('体重(千克)', fontdict=font)
        plt.xlabel('身长(厘米)', fontdict=font)

        ax = plt.gca()  # 获取边框
        ax.spines['top'].set_color(self.color)
        ax.spines['right'].set_color(self.color)
        ax.spines['left'].set_color(self.color)
        ax.spines['bottom'].set_color(self.color)
        ax.spines['bottom'].set_linewidth(1.2)
        ax.spines['left'].set_linewidth(1.2)
        ax.spines['top'].set_linewidth(1.2)
        ax.spines['right'].set_linewidth(1.2)
        ax.yaxis.set_minor_locator(MultipleLocator(0.5))
        ax.xaxis.set_minor_locator(MultipleLocator(1))
        ax.xaxis.grid(True, which='major', linewidth=1.2, color=self.grid_color)  # 使用主刻度绘制x坐标轴的网格
        ax.yaxis.grid(True, which='minor', linewidth=0.7, color=self.grid_color)  # 使用次刻度绘制y坐标轴的网格
        ax.xaxis.grid(True, which='minor', linewidth=0.7, color=self.grid_color)  # 使用次刻度绘制x坐标轴的网格
        ax.yaxis.grid(True, which='major', linewidth=1.2, color=self.color)  # 使用主刻度绘制y坐标轴的网格
        ax.set_axisbelow(True)

        day_data_list = self.get_observe_days(date_str_data_02)

        # 开始添加监测的散点图
        if length_data_02 and weight_data_02:
            if len(weight_data_02) >= 2:
                # 首先获取三次样条函数的值
                cube_d_data, cube_n_data = self.cubic_spline_interpolation(length_data_02, weight_data_02)
                # 绘制发育曲线
                plt.plot(cube_d_data, cube_n_data, '-', lw=3, c='tab:red')

            # 绘制三次，形成比较好看的散点线图
            marker_style = dict(color=self.line_color, marker='o',  markersize=10,
                                markerfacecoloralt=self.line_color, lw=0)
            plt.plot(length_data_02, weight_data_02, fillstyle='full', **marker_style)
            marker_style = dict(color='w', marker='o', markersize=7,
                                markerfacecoloralt=self.line_color, lw=0)
            plt.plot(length_data_02, weight_data_02, fillstyle='full', **marker_style)
            marker_style = dict(color=self.line_color,  marker='o', markersize=4,
                                markerfacecoloralt=self.line_color, lw=0)
            plt.plot(length_data_02, weight_data_02, fillstyle='full', **marker_style)

            # 百分位数
            percent_list = []

            for d_d, d_n, n_n in zip(length_data_02, weight_data_02, range(len(length_data_02))):
                # 首先获取标准的数据列表
                day_data = p_data[p_data['Length'] == d_d]
                # 标准百分位列表
                stand_list = list(p_data.keys())[4:]
                s_number_list = [day_data[j].values[0] for j in stand_list]
                # 计算百分位数
                p_percent = self.computer_p(d_n, s_number_list, stand_list)
                percent_list.append(p_percent)
                bbox_props = dict(boxstyle="round4", fc="k", ec="3", alpha=0.6)

                if n_n < len(length_data_02) / 2 or d_d < (min_num + max_num) / 2:
                    # 百分位数
                    plt.text(d_d+.4, d_n-.5, '$\mathbf{%s\\%%}$' % p_percent, size=10,
                             color='r', bbox=bbox_props, style='italic', ha='left', va='top', wrap=True)
                    # 序号
                    if d_d == min_num:
                        plt.text(d_d+.3, d_n+.5, '$\mathbf{%d}$' % (n_n + 1), size=7, color='k', ha='left',
                                 va='bottom', bbox=dict(boxstyle="circle", fc=self.color, ec="3", alpha=0.6))
                    else:
                        plt.text(d_d, d_n+.5, '$\mathbf{%d}$' % (n_n + 1), size=7, color='k', ha='center',
                                 va='bottom', bbox=dict(boxstyle="circle", fc=self.color, ec="3", alpha=0.6))
                else:
                    # 百分位数
                    plt.text(d_d-.4, d_n+.5, '$\mathbf{%s\\%%}$' % p_percent, size=10,
                             color='r', bbox=bbox_props, style='italic', ha='right', va='bottom', wrap=True)
                    # 序号
                    if d_d == max_num:
                        plt.text(d_d-.3, d_n-.5, '$\mathbf{%d}$' % (n_n + 1), size=7, color='k', ha='right',
                                 va='top', bbox=dict(boxstyle="circle", fc=self.color, ec="3", alpha=0.6))
                    else:
                        plt.text(d_d, d_n-.5, '$\mathbf{%d}$' % (n_n + 1), size=7, color='k', ha='center',
                                 va='top', bbox=dict(boxstyle="circle", fc=self.color, ec="3", alpha=0.6))
            # 添加数据列表
            # 首先固定位置新的图片
            ax2 = fig.add_axes(list(data_loc))  # 图中图
            # 背景透明
            ax2.patch.set_alpha(0.3)
            # 去掉坐标轴
            ax2.set_axis_off()
            # 添加表格列名
            colLabels = ['序号', '日期', '年龄', '身长(百分位)', '体重(百分位)', '身长别体重百分位', '参考说明']
            # 添加表格内容
            cellText = []
            if day_data_list[0] != 1:
                weight_data_02.insert(0, '')
                date_list = [self.b_d_str] + date_str_data_02
                percent_list.insert(0, '<0')
            else:
                date_list = date_str_data_02
            length_o = len(date_list)

            for i in range(length_o):
                p_number = percent_list[i]
                doc = ''
                f_doc = ''
                if p_number[0] in ['<', '>']:
                    f_doc = p_number[0]
                    p_number = float(percent_list[i][1:])
                else:
                    p_number = float(percent_list[i])
                if i == 0:
                    if start_y == 0:
                        if p_number:
                            if 0 < p_number < 5:
                                doc = '体重不足'
                            elif p_number >= 95:
                                doc = '肥胖'
                            elif 85 < p_number < 95:
                                doc = '超重'
                            else:
                                doc = '正常'
                        rowText = [' 1' if doc else '  ', '$%s$' % self.b_d_str, '出生',
                                   length_doc[i], weight_doc[i],
                                   '$%s%s\\%%$' % (f_doc, p_number)
                                   if weight_data_02[i] else '', doc]
                    else:
                        rowText = ['  ', '$%s$' % self.b_d_str, '出生', '', '', '', '']
                else:
                    if p_number < 5:
                        doc = '体重不足'
                    elif p_number >= 95:
                        doc = '肥胖'
                    elif 85 < p_number < 95:
                        doc = '超重'
                    else:
                        doc = '正常'
                    if day_data_list[0] != 1:
                        rowText = [' %s' % i, '$%s$' % date_list[i],
                                   self.get_date_sub(self.b_d_str, date_list[i]),
                                   length_doc[i], weight_doc[i],
                                   '$%s%s\\%%$' % (f_doc, p_number), doc]
                    else:
                        rowText = [' %s' % (i + 1), '$%s$' % date_list[i],
                                   self.get_date_sub(self.b_d_str, date_list[i]),
                                   length_doc[i], weight_doc[i],
                                   '$%s%s\\%%$' % (f_doc, p_number), doc]
                cellText.append(rowText)

            table = ax2.table(cellText=cellText, colLabels=colLabels, loc='upper center', cellLoc='left',
                              colWidths=list(table_w))
            table.auto_set_font_size(False)
            table.set_fontsize(8)
            table_props = table.properties()
            table_cells = table_props['child_artists']
            for cell in table_cells:
                cell._text.set_color(self.color)
                cell.set_edgecolor(self.color)
        fig = plt.gcf()
        fig.savefig(r'%s/%s.png' % (self.path_name, fig_name), dpi=100, bbox_inches='tight')


    def plot_p_data_wfh(self, weight_data_25, height_data_25, date_str_data, p_data, length_doc,
                        weight_doc, fig_name, start_y, end_y, min_num, max_num,
                        fig_size, count_y, y_tap, data_loc, table_w):
        """
        绘制身长别体重数据
        :param weight_data_25: 监测值列表：体重
        :param height_data_25: 监测值列表：身长
        :param date_str_data: 监测值列表：日期
        :param p_data: 总的数据
        :param length_doc: 身高信息
        :param weight_doc: 体重信息
        :param fig_name: 图片名称
        :param start_y: 绘制开始的岁
        :param end_y: 绘制结束的岁
        :param min_num: 需要绘制的身长的最小值
        :param max_num: 需要绘制的身长的最大值
        :param fig_size: 图片尺寸
        :param count_y: y轴的标签的个数
        :param y_tap: y轴的绘制区间
        :param data_loc: 绘制监测数据的图的位置
        :param table_w: 表格的各个列的宽度
        :return: 绘制的图
        """
        # 首先更改列名
        p_data = p_data.rename(columns={'P01': 'P0.1', 'P999': 'P99.9'})
        # 新建图片
        fig = plt.figure(figsize=fig_size)
        # 绘制
        for value in self.who_plot_curve:
            if value in ['P3', 'P50', 'P97']:  # 比较特殊的三条曲线
                lw = 2.2
                sign = 1
            else:
                lw = 0.9
                sign = 0
            # 曲线粗度
            plt.plot(p_data['Height'].values, p_data[value].values, lw=lw, c=self.color)
            # 为曲线添加说明
            if sign:
                plt.text(max_num, p_data[p_data['Height'] == max_num][value].values[-1] - 0.5,
                         '$\mathbf{%s\\%%}$' % value[1:],
                         color=self.color, size='small', ha='left')
            else:
                plt.text(max_num, p_data[p_data['Height'] == max_num][value].values[-1] - 0.5,
                         '$%s\\%%$' % value[1:],
                         color=self.color, size='small', ha='left')
        # 设置坐标区间
        plt.ylim(y_tap)
        plt.xlim((min_num, max_num))
        minorticks_on()
        tick_params(axis='y', which='major', width=1, length=4, colors=self.color)
        tick_params(axis='x', which='major', width=1, length=2, colors=self.color)
        tick_params(which='minor', length=0)
        # 设置题目
        font = {'color': self.color, 'weight': 'bold', 'size': 14}
        plt.title(('出生' if not start_y else '$%d$' % start_y)
                  + '至$%d$岁%s（身高别体重）发育百分位数曲线(WHO版)\n' % (end_y, s_d.GENDER[self.g]),
                  fontdict=font, loc='center')
        if len(weight_data_25):
            font = {'color': self.color, 'size': 10}
            plt.title('宝宝昵称:%s|记录:%s-%s条' % (self.b_n, len(self.o_d), len(weight_data_25)),
                      fontdict=font, loc='left')
            plt.title('注:图中百分数表示体重超过同身高%s童数的比例' % ('女' if self.g == 'girls' else '男'),
                      fontdict={'color': self.color, 'size': 8}, loc='right')

        # 设置x轴标签
        plt.xticks(np.linspace(start=min_num, stop=max_num, num=(max_num - min_num) // 5 + 1),
                   ['$%d$' % i for i in np.linspace(start=min_num, stop=max_num,
                                                    num=(max_num - min_num) // 5 + 1)],
                   color=self.color)

        # 设置y轴标签
        plt.yticks(np.linspace(y_tap[0], y_tap[1], count_y),
                   np.linspace(y_tap[0], y_tap[1], count_y), color=self.color)
        plt.ylabel('体重(千克)', fontdict=font)
        plt.xlabel('身高(厘米)', fontdict=font)
        # 模拟绘制X轴的主刻度网格线
        ax = plt.gca()  # 获取边框
        ax.spines['top'].set_color(self.color)
        ax.spines['right'].set_color(self.color)
        ax.spines['left'].set_color(self.color)
        ax.spines['bottom'].set_color(self.color)
        ax.spines['bottom'].set_linewidth(1.2)
        ax.spines['left'].set_linewidth(1.2)
        ax.spines['top'].set_linewidth(1.2)
        ax.spines['right'].set_linewidth(1.2)
        ax.yaxis.set_minor_locator(MultipleLocator(0.5))
        ax.xaxis.set_minor_locator(MultipleLocator(1))
        ax.xaxis.grid(True, which='major', linewidth=1.2, color=self.grid_color)  # 使用主刻度绘制x坐标轴的网格
        ax.yaxis.grid(True, which='minor', linewidth=0.7, color=self.grid_color)  # 使用次刻度绘制y坐标轴的网格
        ax.xaxis.grid(True, which='minor', linewidth=0.7, color=self.grid_color)  # 使用次刻度绘制x坐标轴的网格
        ax.yaxis.grid(True, which='major', linewidth=1.2, color=self.color)  # 使用主刻度绘制y坐标轴的网格
        ax.set_axisbelow(True)

        day_data_list = self.get_observe_days(date_str_data)

        # 开始添加监测的散点图
        if height_data_25 and weight_data_25:
            if len(weight_data_25) >= 2:
                # 首先获取三次样条函数的值
                cube_d_data, cube_n_data = self.cubic_spline_interpolation(height_data_25, weight_data_25)
                # 绘制发育曲线
                plt.plot(cube_d_data, cube_n_data, '-', lw=3, c='tab:red')

            # 绘制三次，形成比较好看的散点线图
            marker_style = dict(color=self.line_color, marker='o',  markersize=10,
                                markerfacecoloralt=self.line_color, lw=0)
            plt.plot(height_data_25, weight_data_25, fillstyle='full', **marker_style)
            marker_style = dict(color='w', marker='o', markersize=7,
                                markerfacecoloralt=self.line_color, lw=0)
            plt.plot(height_data_25, weight_data_25, fillstyle='full', **marker_style)
            marker_style = dict(color=self.line_color,  marker='o', markersize=4,
                                markerfacecoloralt=self.line_color, lw=0)
            plt.plot(height_data_25, weight_data_25, fillstyle='full', **marker_style)

            # 百分位数
            percent_list = []

            for d_d, d_n, n_n in zip(height_data_25, weight_data_25, range(len(height_data_25))):
                # 首先获取标准的数据列表
                day_data = p_data[p_data['Height'] == d_d]
                # 标准百分位列表
                stand_list = list(p_data.keys())[4:]
                s_number_list = [day_data[j].values[0] for j in stand_list]
                # 计算百分位数
                p_percent = self.computer_p(d_n, s_number_list, stand_list)
                percent_list.append(p_percent)
                bbox_props = dict(boxstyle="round4", fc="k", ec="3", alpha=0.6)

                if n_n < len(height_data_25) / 2 or d_d < (min_num + max_num) / 2:
                    # 百分位数
                    plt.text(d_d+.4, d_n-.5, '$\mathbf{%s\\%%}$' % p_percent, size=10,
                             color='r', bbox=bbox_props, style='italic', ha='left', va='top', wrap=True)
                    # 序号
                    if d_d == min_num:
                        plt.text(d_d+.3, d_n+.5, '$\mathbf{%d}$' % (n_n + 1), size=7, color='k', ha='left',
                                 va='bottom', bbox=dict(boxstyle="circle", fc=self.color, ec="3", alpha=0.6))
                    else:
                        plt.text(d_d, d_n+.5, '$\mathbf{%d}$' % (n_n + 1), size=7, color='k', ha='center',
                                 va='bottom', bbox=dict(boxstyle="circle", fc=self.color, ec="3", alpha=0.6))
                else:
                    # 百分位数
                    plt.text(d_d-.4, d_n+.5, '$\mathbf{%s\\%%}$' % p_percent, size=10,
                             color='r', bbox=bbox_props, style='italic', ha='right', va='bottom', wrap=True)
                    # 序号
                    if d_d == max_num:
                        plt.text(d_d-.3, d_n-.5, '$\mathbf{%d}$' % (n_n + 1), size=7, color='k', ha='right',
                                 va='top', bbox=dict(boxstyle="circle", fc=self.color, ec="3", alpha=0.6))
                    else:
                        plt.text(d_d, d_n-.5, '$\mathbf{%d}$' % (n_n + 1), size=7, color='k', ha='center',
                                 va='top', bbox=dict(boxstyle="circle", fc=self.color, ec="3", alpha=0.6))
            # 添加数据列表
            # 首先固定位置新的图片
            ax2 = fig.add_axes(list(data_loc))  # 图中图
            # 背景透明
            ax2.patch.set_alpha(0.3)
            # 去掉坐标轴
            ax2.set_axis_off()
            # 添加表格列名
            colLabels = ['序号', '日期', '年龄', '身高(百分位)', '体重(百分位)', '身高别体重百分位', '说明']
            # 添加表格内容
            cellText = []
            if day_data_list[0] != 1:
                weight_data_25.insert(0, '')
                date_list = [self.b_d_str] + date_str_data
                percent_list.insert(0, '<0')
            else:
                date_list = date_str_data
            length_o = len(date_list)

            for i in range(length_o):
                p_number = percent_list[i]
                doc = ''
                f_doc = ''
                if p_number[0] in ['<', '>']:
                    f_doc = p_number[0]
                    p_number = float(percent_list[i][1:])
                else:
                    p_number = float(percent_list[i])
                if i == 0:
                    if start_y == 0:
                        if p_number:
                            if 0 < p_number < 5:
                                doc = '体重不足'
                            elif p_number >= 95:
                                doc = '肥胖'
                            elif 85 < p_number < 95:
                                doc = '超重'
                            else:
                                doc = '正常'
                        rowText = [' 1' if doc else '  ', '$%s$' % self.b_d_str, '出生',
                                   length_doc[i], weight_doc[i],
                                   '$%s%s\\%%$' % (f_doc, p_number) if weight_data_25[i] else '', doc]
                    else:
                        rowText = ['  ', '$%s$' % self.b_d_str, '出生', '', '', '', '']
                else:
                    if p_number < 5:
                        doc = '体重不足'
                    elif p_number >= 95:
                        doc = '肥胖'
                    elif 85 < p_number < 95:
                        doc = '超重'
                    else:
                        doc = '正常'
                    if day_data_list[0] != 1:
                        rowText = [' %s' % i, '$%s$' % date_list[i],
                                   self.get_date_sub(self.b_d_str, date_list[i]),
                                   length_doc[i], weight_doc[i],
                                   '$%s%s\\%%$' % (f_doc, p_number), doc]
                    else:
                        rowText = [' %s' % (i + 1), '$%s$' % date_list[i],
                                   self.get_date_sub(self.b_d_str, date_list[i]),
                                   length_doc[i], weight_doc[i],
                                   '$%s%s\\%%$' % (f_doc, p_number), doc]
                cellText.append(rowText)

            table = ax2.table(cellText=cellText, colLabels=colLabels, loc='upper center', cellLoc='left',
                              colWidths=list(table_w))
            table.auto_set_font_size(False)
            table.set_fontsize(8)
            table_props = table.properties()
            table_cells = table_props['child_artists']
            for cell in table_cells:
                cell._text.set_color(self.color)
                cell.set_edgecolor(self.color)
        fig = plt.gcf()
        fig.savefig(r'%s/%s.png' % (self.path_name, fig_name), dpi=100, bbox_inches='tight')


