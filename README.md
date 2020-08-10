# JLU Health Reporter

为吉林大学本科生每日健康情况申报所作的自动机器人。

以 WTFPL 授权开源。Pray for Hubei.

## 免责声明

本自动程序为个人使用开发，未经充分测试，不保证正常工作。

本自动程序仅适用于 2020 年初 COVID-19 疫情期间吉林大学本科生、研究生健康情况申报，不保证按时更新。

请注意，本自动程序仅会每 24 小时自动重新提交上次提交的内容，**如您的申报内容变化，请立即停止使用本程序！**

__**如运行本程序，您理解并认可，本自动程序的一切操作均视为您本人、或由您授权的操作。**__

## 使用说明

需要 Python 3 ，先 `pip3 install requests` 。

运行之前先登录平台提交一次申报，务必确保信息准确。

把文件开头的 `USERS` 中的示例用户名和密码换为自己的，支持多帐号。

若为**研究生健康申报**使用，请先改变文件开头的 `TRANSACTION` 。

后台模式：

```
./jlu-health-reporter.py & > reporter.log 2>&1
```

Crontab 模式：

```
0 6 * * * /usr/bin/python3 /path/to/jlu-health-reporter.py --once >> reporter.log 2>&1
```

手动模式：

```
./jlu-health-reporter.py --once
```

## 推送功能介绍
详见：[ForeverOpp/JLUAnnounceBot](https://github.com/ForeverOpp/JLUAnnounceBot#%E7%BB%93%E6%9E%84) 下的3。  
> 该类可扩展，故设置了一个`__init__(method)`方法用以选择发送方法，支持SMTP邮件发送，ServerChan微信推送，控制台输出和iOS端的软件Bark推送，关于ServerChan的介绍，请移步[ServerChan](http://sc.ftqq.com)，关于Bark的介绍，请移步[Bark](https://github.com/Finb/Bark/) 。

## 联系

邮箱在源代码里。

欢迎开 issue 、pr ，随缘处理。
