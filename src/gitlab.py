#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
File name    : gitlab.py
Author       : miaoyc
Create time  : 2022/11/25 11:48
Update time  : 2022/11/25 11:48
Description  : gitlab object
"""

import json


class GitLabStat(object):
    """
    gitlab code stat struct
    """
    def __init__(self):
        """
        author_email, author_name, total, additions, deletions, commit_nums
        提交人邮箱,提交人姓名,总行数,增加行数,删除行数,提交次数
        """
        self.author_email = ""
        self.author_name = ""
        self.total = ""
        self.additions = ""
        self.deletions = ""
        self.commit_nums = ""


class ProjectInfo(json.JSONEncoder):
    """
    project info struct
    """
    def __init__(self):
        self.project_id = None
        self.project_desc = None
        self.project_url = None
        self.path = None
        self.name = None
        self.commit_map = None


class CommitDetails(json.JSONEncoder):
    """
    commit info struct
    """
    def __init__(self):
        self.author_name = ""
        self.author_email = ""
        self.additions = 0
        self.deletions = 0
        self.total = 0
        self.commit_nums = 0
