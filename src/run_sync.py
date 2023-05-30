#!/usr/bin/env python
# coding=utf-8

"""
File name    : run_sync.py
Author       : miaoyc
Create date  : 2021/9/28 13:38
Update date  : 2023/3/13 10:23
Description  :
"""

import time
import datetime
import requests
from urllib import parse

import config as config
import csv
import gitlab

user_unknown = {}
g_email_2_name = {}
g_user_name = {}


class GitlabApiCount:

    def __init__(self):
        self.commit_set = set()     # 所有commit的集合
        self.totalMap = dict()      # 最终的数据集合

    def run(self):
        self.get_projects()

    def get_projects(self):
        """
        获取所有仓库，并生成报告
        :return:
        """
        # 获取服务器上的所有仓库
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
                if time.strptime(r3["last_activity_at"][:19], "%Y-%m-%dT%H:%M:%S") < \
                        time.strptime(config.t_from, "%Y-%m-%d %H:%M:%S"):
                    continue

                if config.PRINT_BRANCH_NAME:
                    if config.FILTER_BRANCH_KEY:
                        for key in config.FILTER_BRANCH_KEY:
                            if key in name_with_namespace:
                                print('"{0}",'.format(name_with_namespace))
                    else:
                        print('"{0}",'.format(name_with_namespace))
                    continue
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
                project_info = gitlab.ProjectInfo()
                project_info.project_id = r3['id']
                project_info.name = r3['name']
                project_info.project_desc = r3['description']
                project_info.project_url = r3['web_url']
                project_info.path = r3['path']
                #
                self.get_branches(r3['id'], project_info)

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
                    exist_detail.commit_nums += detail.commit_nums
                    final_commit_map[detail.author_email] = exist_detail

        csv.write_to_csv("%s/GitStatic_%s/%s_%s.csv" % (config.export_path, config.t_from, 'total', config.t_from),
                         final_commit_map, "extra")

    def get_branches(self, project_id, project_info):
        """
        获取仓库的所有Branch，并汇总commit到一个map梨
        :param project_id:
        :param project_info:
        :return:cd
        """
        # 线上gitlab可用，问题是没有全部显示, 添加默认分页参数，每页 1000条数据
        url = '%s/api/v4/projects/%s/repository/branches?private_token=%s&per_page=1000' % (
            config.git_root_url, project_id, config.git_token)
        r1 = requests.get(url)  # 请求url，传入header，ssl认证为false
        if r1.content == b'Retry later\n':
            print("Exception branch: {0}->{1}".format(project_info.project_url, url))
            return
        r2 = r1.json()  # 显示json字符串
        if not r2:
            return
        # branch的map，key为branch名称，value为按照提交者email汇总的，key为email的子map集合
        branch_map = {}
        # 主动获取master分支的提交
        for r3 in r2:
            branch_name = r3['name']
            if branch_name is None:
                continue
            if config.BRANCH_FILTER and branch_name not in config.branch_filter_list:
                continue
            # 如果仓库已经被Merge了，则不再处理
            if r3['merged']:
                # print("merged")
                continue
            #
            detail_map = None
            while detail_map is None:
                detail_map = self.get_commits(project_id, project_info.name, branch_name)
                if detail_map is not None:
                    # print("Success get_commits: {0}->{1}".format(project_info.name, branch_name))
                    pass
            # 将结果放到map里
            branch_map[branch_name] = detail_map
        final_commit_map = {}
        # 遍历branch map，并按照提交者email进行汇总
        for branch_name, value_map in branch_map.items():
            for author_email, detail in value_map.items():
                exist_detail = final_commit_map.get(detail.author_email)
                if exist_detail is None:
                    final_commit_map[detail.author_email] = detail
                else:
                    exist_detail.total += detail.total
                    exist_detail.additions += detail.additions
                    exist_detail.deletions += detail.deletions
                    exist_detail.commit_nums += detail.commit_nums
                    final_commit_map[detail.author_email] = exist_detail

        if not final_commit_map:
            return

        project_info.commit_map = final_commit_map
        self.totalMap[project_info.project_id] = project_info
        # 汇总完毕后，将结果写入到projectID+日期的csv文件里
        csv.write_to_csv(
            "{0}/GitStatic_{1}/project/{2}_{3}.csv".format(
                config.export_path, config.t_from, project_info.path, project_info.project_id),
            final_commit_map,
            project_info.project_url
        )

    def get_commits(self, project_id, project_name, branch_name):
        """
        获取指定仓库，指定分支的所有commits，然后遍历每一个commit获得单个branch的统计信息
        :param project_id:
        :param project_name:
        :param branch_name:
        :return: dict<email, CommitDetails>
        """
        since_date = config.date_from.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        until_date = config.date_end.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        url = parse.urljoin(
            config.git_root_url,
            "/api/v4/projects/{0}/repository/commits?"
            "page=1&per_page=1000&ref_name={1}&since={2}&until={3}&private_token={4}".format(
                project_id, branch_name, since_date, until_date, config.git_token)
        )
        r1 = requests.get(url)
        if r1.content == b'Retry later\n':
            print("Exception get_commits: {0}->{1}".format(project_name, branch_name))
            return
        r2 = r1.json()
        detail_map = {}

        for r3 in r2:
            if not isinstance(r3, dict):
                print("exception:", project_name, branch_name)
                continue
            commit_id = r3.get("id")
            if not commit_id or commit_id in self.commit_set:
                continue
            else:
                # 在这里进行commit去重判断, 已经统计过的commit不再重复统计
                self.commit_set.add(commit_id)

            # 这里开始获取单次提交详情，detail 为 CommitDetails对象
            detail = None
            while detail is None:
                detail = get_commit_detail(project_id, commit_id)
                if isinstance(detail, int):
                    detail = None if detail < 0 else gitlab.CommitDetails()
                if detail:
                    pass
            # 过滤异常数据，单次提交大于5000行的代码，可能是脚手架之类生成的代码，不做处理
            if detail.total == 0 or detail.total > 5000:
                continue

            # 根据email纬度，统计提交数据
            exist_detail = detail_map.get(detail.author_email)
            if not exist_detail:
                detail.commit_nums = 1
                detail_map[detail.author_email] = detail
            else:
                exist_detail.total += detail.total
                exist_detail.additions += detail.additions
                exist_detail.deletions += detail.deletions
                exist_detail.commit_nums += 1
                detail_map[detail.author_email] = exist_detail
        return detail_map


def get_commit_detail(project_id, commit_id):
    """
    get single commit info
    :param project_id:
    :param commit_id:
    :return: int or CommitDetails, 返回整型表示未获取到有效提交信息，-1代表接口异常需要重试，1代表已经合并过无需统计，2代表无统计需跳过
    """
    url = parse.urljoin(
        config.git_root_url,
        "/api/v4/projects/{0}/repository/commits/{1}?private_token={2}".format(project_id, commit_id, config.git_token)
    )
    r1 = requests.get(url)
    if r1.content == b'Retry later\n':
        print("Exception get_commit_detail: {0}".format(commit_id))
        return -1

    r2 = r1.json()
    stats = r2['stats']
    if 'Merge branch' in r2['title']:
        return 1
    if stats is None:
        return 2

    author_email, author_name = deduplicate_name(r2['author_email'], r2['author_name'])
    #
    if config.AUTHOR_FILTER and author_email not in config.author_filter_list:
        return 3
    #
    details = gitlab.CommitDetails()
    details.author_email = author_email
    details.author_name = author_name
    details.total = stats['total']
    details.additions = stats['additions']
    details.deletions = stats['deletions']
    return details


def deduplicate_name(email, name):
    """
    针对提交邮箱去重，同一邮箱可能存在多个不同提交用户的提交，返回第一次查询到的提交用户名
    :param email:
    :param name:
    :return:
    """
    if g_email_2_name.get(email):
        return email, g_email_2_name[email]
    else:
        g_email_2_name[email] = name
        return email, name


if __name__ == '__main__':
    gitlab4 = GitlabApiCount()
    gitlab4.run()
