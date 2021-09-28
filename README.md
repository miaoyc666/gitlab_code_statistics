#Gitlab代码行数统计

## 环境依赖
* python3

## 获取token
1. 登录gitlab, 点击右上角个人信息Preferences； 
2. 左侧选择`Access Tokens`, 输入token名称，选择权限范围（勾选api）和过期时间；
3. 点击`Create personal access token` , 生成的个人账号token。

## 统计代码量
##### Usage
`config.py`文件包含统计脚本需要用到的配置信息  
`run.py`脚本为代码量统计脚本，使用语法：
```
python3 run.py
```

## 致谢
gitlab_code_statistics初版参考了git-status项目。  
感谢git-status项目原作者EightDoor，项目地址 ：https://gitee.com/EightDoor/git-status
