#!/usr/bin/env python
# coding=utf-8

"""
File name    : run.py
Author       : miaoyc
Create date  : 2021/9/28 1:38 下午
Description  :
"""

import time
import requests
import os
import json
import threading
import datetime
from urllib import parse

import config as config

# 一个线程锁, 用于请求接口
lock = threading.RLock()
# 另一个线程锁，用于计数
lock_num = threading.Lock()
# 插叙commit接口频率显示
rate_limit = {}

user_unknown = {}
user_email_alias_mapping = {}
user_email_name_mapping = {}


def api_rate_limit():
    key = int(time.time())
    dic_plus_one(rate_limit, key)
    if rate_limit[key] >= 10:
        time.sleep(1)
        return


def dic_plus_one(dic, key):
    with lock_num:
        if key not in dic:
            dic[key] = 0
        dic[key] += 1


class GitlabApiCount:
    """
    Worker类
    """
    # 所有commit的集合，用于去重，这里的重复，可能是代码merge造成的
    total_commit_map = {}

    # 最终的数据集合
    totalMap = {}

    def get_projects(self):
        """
        获取所有仓库，并生成报告
        :return:
        """
        threads = []
        # 获取服务器上的所有仓库，每个仓库新建一个线程
        # page_size 根据实际情况调整
        page_size = 5
        for i in range(1, page_size+1):
            url = parse.urljoin(
                config.git_root_url,
                '/api/v4/projects?private_token={0}&per_page=1000&page={1}&order_by=last_activity_at'.format(
                    config.git_token, i)
            )
            r1 = requests.get(url)  # 请求url，传入header，ssl认证为false
            r2 = r1.json()  # 显示json字符串
            for r3 in r2:
                name_with_namespace = r3["name_with_namespace"]
                if name_with_namespace not in config.valid_project:
                    continue
                value = r3['default_branch']
                last_active_time = r3['last_activity_at']
                if value is None:
                    continue
                last_active_time = last_active_time.split('+')[0]
                days = config.date_from - datetime.datetime.strptime(last_active_time, '%Y-%m-%dT%H:%M:%S.%f')
                # 如果project的最后更新时间比起始时间小，则continue
                if days.days > 1:
                    continue
                project_info = ProjectInfo()
                project_info.project_id = r3['id']
                project_info.name = r3['name']
                project_info.project_desc = r3['description']
                project_info.project_url = r3['web_url']
                project_info.path = r3['path']
                # 构件好线程
                t = threading.Thread(
                    target=self.get_branches, args=(r3['id'], project_info))
                threads.append(t)

        # 所有线程逐一开始
        for t in threads:
            t.start()
        # 等待所有线程结束
        for t in threads:
            t.join()
        # 数据聚合
        final_commit_map = {}
        for key, project in self.totalMap.items():
            for author_email, detail in project.commit_map.items():
                exist_detail = final_commit_map.get(detail.author_email)
                if exist_detail is None:
                    final_commit_map[detail.author_email] = detail
                else:
                    exist_detail.total += detail.total
                    exist_detail.additions += detail.additions
                    exist_detail.deletions += detail.deletions
                    final_commit_map[detail.author_email] = exist_detail
        write_to_csv("%s/GitStatic_%s/%s_%s.csv" % (config.export_path, config.t_from, 'total', config.t_from),
                     final_commit_map, "extra")
        return

    def get_branches(self, project_id, project_info):
        """
        获取仓库的所有Branch，并汇总commit到一个map梨
        :param project_id:
        :param project_info:
        :return:
        """
        # 线上gitlab可用，问题是没有全部显示
        url = '%s/api/v4/projects/%s/repository/branches?private_token=%s' % (
            config.git_root_url, project_id, config.git_token)
        r1 = requests.get(url)  # 请求url，传入header，ssl认证为false
        if r1.content == b'Retry later\n':
            # print("Exception branch: {0}->{1}".format(project_info.project_url, url))
            return
        r2 = r1.json()  # 显示json字符串
        if not r2:
            return
        # branch的map，key为branch名称，value为按照提交者email汇总的，key为email的子map集合
        branch_map = {}
        # 主动获取master分支的提交
        detail_map = None
        while detail_map is None:
            detail_map = self.get_commits(project_id, project_info.name, project_info.project_url, "master")
            if detail_map is not None:
                pass
                # print("Success get_commits: {0}->{1}".format(project_info.name, "master"))
        if detail_map:
            branch_map['master'] = detail_map
        for r3 in r2:
            branch_name = r3['name']
            if branch_name is None:
                continue
            # 如果仓库已经被Merge了，则不再处理
            if r3['merged']:
                continue
            #
            api_rate_limit()

            detail_map = None
            while detail_map is None:
                detail_map = self.get_commits(project_id, project_info.name, project_info.project_url, branch_name)
                if detail_map is not None:
                    # print("Success get_commits: {0}->{1}".format(project_info.name, branch_name))
                    pass
            # 将结果放到map里
            branch_map[branch_name] = detail_map
        final_commit_map = {}
        # 遍历branch map，并按照提交者email进行汇总
        for key, value_map in branch_map.items():
            for author_email, detail in value_map.items():
                exist_detail = final_commit_map.get(detail.author_email)
                if exist_detail is None:
                    final_commit_map[detail.author_email] = detail
                else:
                    exist_detail.total += detail.total
                    exist_detail.additions += detail.additions
                    exist_detail.deletions += detail.deletions
                    final_commit_map[detail.author_email] = exist_detail

        if not final_commit_map:
            return

        project_info.commit_map = final_commit_map
        # 加锁
        lock.acquire()
        # 此对象会被各个线程操作
        self.totalMap[project_info.project_id] = project_info
        # 释放锁
        lock.release()
        # 汇总完毕后，将结果写入到projectID+日期的csv文件里
        write_to_csv(
            "%s/GitStatic_%s/project/%s_%d.csv" % (
                config.export_path, config.t_from, project_info.path, project_info.project_id),
            final_commit_map, project_info.project_url)

    def get_commits(self, project_id, project_name, project_url, branch_name):
        """
        获取指定仓库，指定分支的所有commits，然后遍历每一个commit获得单个branch的统计信息
        :param project_id:
        :param project_name:
        :param project_url:
        :param branch_name:
        :return:
        """
        # 多线程同时get commits时，容易因服务端限速引发接口异常，接口会抛出Retry later, 规避此情况，延迟执行
        api_rate_limit()

        # 开始真正的业务
        since_date = config.date_from.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        until_date = config.date_end.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        url = parse.urljoin(
            config.git_root_url,
            "/api/v4/projects/%s/repository/commits?page=1&per_page=1000&ref_name=%s&since=%s&until=%s&private_token=%s" %
            (project_id, branch_name, since_date, until_date, config.git_token)
        )
        r1 = requests.get(url)
        if r1.content == b'Retry later\n':
            # print("Exception get_commits: {0}->{1}".format(project_name, branch_name))
            return
        r2 = r1.json()  # 显示json字符串
        detail_map = {}
        for r3 in r2:
            commit_id = r3['id']
            if commit_id is None:
                continue
            # 在这里进行commit去重判断
            if self.total_commit_map.get(commit_id) is None:
                self.total_commit_map[commit_id] = commit_id
            else:
                continue
            # 这里开始获取单次提交详情
            detail = None
            while detail is None:
                detail = get_commit_detail(project_id, commit_id)
                if isinstance(detail, int):
                    detail = None if detail < 0 else CommitDetails()
                if detail:
                    pass
                    # print("Success get_commit_detail: {0}->{1}".format(project_id, commit_id))
            # 过滤异常数据，单次提交大于5000行的代码，可能是脚手架之类生成的代码，不做处理
            if detail.total == 0 or detail.total > 5000:
                continue
            # 这里和主流程无关，是用来处理commit记录里的提交者，账号不规范的问题
            if detail.author_email in user_unknown:
                print("email %s projectid= %d,branchname,%s,url=%s" % (
                    detail.author_email, project_id, branch_name, project_url))

            # 根据email纬度，统计提交数据
            exist_detail = detail_map.get(detail.author_email)
            if exist_detail is None:
                detail_map[detail.author_email] = detail
            else:
                exist_detail.total += detail.total
                exist_detail.additions += detail.additions
                exist_detail.deletions += detail.deletions
                detail_map[detail.author_email] = exist_detail
        return detail_map


def get_commit_detail(project_id, commit_id):
    """
    获取单个commit的信息
    :param project_id: 工程IDException
    :param commit_id: commit的id
    :return: 返回#CommitDetails对象
    """
    # 多线程同时get commits时，容易因服务端限速引发接口异常，接口会抛出Retry later, 规避此情况，延迟执行
    api_rate_limit()

    # 开始真正的业务
    url = parse.urljoin(
        config.git_root_url,
        '/api/v4/projects/%s/repository/commits/%s?private_token=%s' % (project_id, commit_id, config.git_token)
    )
    # print(url)
    r1 = requests.get(url)  # 请求url，传入header，ssl认证为false
    if r1.content == b'Retry later\n':
        print("Exception get_commit_detail: {0}".format(commit_id))
        return -1

    r2 = r1.json()  # 显示json字符串
    author_name = r2['author_name']
    author_email = r2['author_email']

    stats = r2['stats']
    if 'Merge branch' in r2['title']:
        return 1
    if stats is None:
        return 2
    temp_mail = user_email_alias_mapping.get(author_email)
    if temp_mail is not None:
        author_email = temp_mail
    temp_name = user_email_name_mapping.get(author_email)
    if temp_name is not None:
        author_name = temp_name
    additions = stats['additions']
    deletions = stats['deletions']
    total = stats['total']
    details = CommitDetails()
    details.additions = additions
    details.deletions = deletions
    details.total = total
    details.author_email = author_email

    details.author_name = author_name
    return details


def make_dir_safe(file_path):
    """
    工具方法：写文件时，如果关联的目录不存在，则进行创建
    :param file_path:文件路径或者文件夹路径
    :return:
    """
    if file_path.endswith("/"):
        if not os.path.exists(file_path):
            os.makedirs(file_path)
    else:
        folder_path = file_path[0:file_path.rfind('/') + 1]
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)


def write_to_csv(file_path, final_commit_map, extra):
    """
    工具方法：将结果写入csv，从#final_commit_map参数解析业务数据
    :param file_path:文件路径
    :param final_commit_map:提交参数
    :param extra:额外数据列
    :return:
    """
    make_dir_safe(file_path)
    print(file_path)
    with open(file_path, 'w') as out:
        title = '%s,%s,%s,%s,%s,%s' % (
            "提交人邮箱", "提交人姓名", "总行数", "增加行数", "删除行数", extra)
        out.write(title + "\n")
        for key, value in final_commit_map.items():
            var = '%s,%s,%s,%s,%s' % (
                value.author_email, value.author_name, value.total, value.additions, value.deletions)
            out.write(var + '\n')
        out.close()


class CommitDetails(json.JSONEncoder):
    """
    提交信息的结构体
    """
    author_name = None
    author_email = None
    additions = 0
    deletions = 0
    total = 0


class ProjectInfo(json.JSONEncoder):
    """
    工程信息的结构体
    """
    project_id = None
    project_desc = None
    project_url = None
    path = None
    name = None
    commit_map = None


if __name__ == '__main__':
    gitlab4 = GitlabApiCount()
    gitlab4.get_projects()
