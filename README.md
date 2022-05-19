#Gitlab代码行数统计

## 环境依赖
* python3

## 获取token
1. 登录gitlab, 点击右上角个人信息Preferences； 
2. 左侧选择`Access Tokens`, 输入token名称，选择权限范围（勾选api）和过期时间；
3. 点击`Create personal access token` , 生成的个人账号token。

## 统计代码量
##### 文件列表
`config.py`文件包含统计脚本需要用到的配置信息  
`run.py`脚本为代码量统计脚本（多线程版本，已删，早期代码tag内可以看到，不想维护两份代码了）  
`run_sync.py`脚本为代码量统计脚本（同步调用版本）  
##### Usage
```
python3 run.py
```

##### 运行效果
![image](https://user-images.githubusercontent.com/2928791/135256781-564176b5-4892-486b-a2a4-a4be16d43335.png)

## 常见问题
1.API返回`Retry later`错误，这是因为giblab接口默认有限速，解决方案为限制客户端的请求频率。    


## 致谢
gitlab_code_statistics初版参考了git-status项目。  
感谢git-status项目原作者EightDoor，项目地址 ：https://gitee.com/EightDoor/git-status
