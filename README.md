# Gitlab代码行数统计

## Env Dependence
* python3

## Support 
* support gitlab api v4

## Get Token
1. 登录gitlab, 点击右上角个人信息Preferences； 
2. 左侧选择`Access Tokens`, 输入token名称，选择权限范围（勾选api）和过期时间；
3. 点击`Create personal access token` , 生成的个人账号token。

## 统计代码量
##### 文件列表
- `config.py.template` 配置文件模板，包含统计脚本需要用到的配置信息  
- `run_sync.py` 代码量统计脚本（同步调用版本）  
- `csv.py` scv操作方法
- `gitlab.py` gitlab实体信息数据结构

##### 已删文件
- `run.py` 脚本为代码量统计脚本（多线程版本，已删，早期代码tag内可以看到，不想维护两份代码了）

##### Usage
```
python3 run_sync.py
```

##### 运行效果
<img width="765" alt="image" src="https://user-images.githubusercontent.com/2928791/203967770-62d78491-ac9a-4802-8f83-8301d5342079.png">

## 常见问题
1.API返回`Retry later`错误，这是因为giblab接口默认有限速，解决方案为限制客户端的请求频率。    
