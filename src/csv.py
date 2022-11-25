#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
File name    : csv.py
Author       : miaoyc
Create time  : 2022/11/25 11:27
Update time  : 2022/11/25 11:29
Description  : csv操作
"""

import os


def write_to_csv(file_path, final_commit_map, extra):
    """
    工具方法：将结果写入csv，从#final_commit_map参数解析业务数据
    :param file_path:文件路径
    :param final_commit_map:提交参数
    :param extra:额外数据列
    :return:
    """
    _make_dir_safe(file_path)
    with open(file_path, 'w') as out:
        title = '%s,%s,%s,%s,%s,%s,%s' % (
            "提交人邮箱", "提交人姓名", "总行数", "增加行数", "删除行数", "提交次数", extra)
        out.write(title + "\n")
        for key, value in final_commit_map.items():
            var = '%s,%s,%s,%s,%s,%s' % (
                value.author_email, value.author_name, value.total, value.additions, value.deletions, value.commit_nums)
            out.write(var + '\n')
        out.close()


def _make_dir_safe(file_path):
    """
    创建文件所对应的文件目录
    :param file_path: 文件路径或者文件夹路径
    :return:
    """
    if file_path.endswith("/"):
        if not os.path.exists(file_path):
            os.makedirs(file_path)
    else:
        folder_path = file_path[0:file_path.rfind('/') + 1]
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
