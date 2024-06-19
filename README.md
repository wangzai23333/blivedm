# blivedm

Python获取bilibili直播弹幕的库，使用WebSocket协议，支持web端和B站直播开放平台两种接口

[协议解释](https://open-live.bilibili.com/document/657d8e34-f926-a133-16c0-300c1afc6e6b)

基于本库开发的一个应用：[blivechat](https://github.com/xfgryujk/blivechat)

## 使用说明

1. 需要Python 3.8及以上版本
2. 安装依赖

    ```sh
    pip install -r requirements.txt
    ```

3. 填写SESSDATA值（登录b站后在cookie里）

4. 运行：sample.py

可与[fay带货版](https://github.com/TheRamU/Fay/tree/fay-sales-edition)进行对接
