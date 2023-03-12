#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
File name    : config.py
Author       : miaoyc
Create date  : 2021/9/28 1:38 下午
Description  : 配置模板
"""

import datetime

# gitlab仓库地址
git_root_url = ""
# 访问Token
git_token = ""
# 统计结果的存储目录
export_path = "./dist"
# 统计的时间区间-开始日期
t_from = ""
# 统计的时间区间-结束日期
t_end = ""
# 统计的时间区间-开始日期，datetime对象
date_from = datetime.datetime.strptime(t_from, '%Y-%m-%d %H:%M:%S')
# 统计的时间区间-结束日期，datetime对象
date_end = datetime.datetime.strptime(t_end, '%Y-%m-%d %H:%M:%S')

# 待统计的仓库列表
valid_project = [
]

# 是否开启author过滤
author_filter = False
# 过滤author列表
author_filter_list = []
