# Mayor Bot

My Discord Bot built on Python.

## 公告

> [!NOTE]
> 目前 Python `3.13.2` 已重新修正為可以執行 music 的功能了，還有很抱歉一直在改 Python 版本 (x</br>
> Python `3.13.2` has now been updated to support the music functionality again. Apologies for frequently changing the Python version (x

> [!WARNING]
> 由於無法及時解決單一機器人管理多個伺服器的問題，現在建議每個伺服器使用一個機器人。</br>
> Unable to promptly address the issue of a single bot managing multiple servers, it is now recommended to use one bot per server.

## 運行版本

Python `3.13.2`

## 使用方法

- 請先確保電腦已安裝 [Python](https://www.python.org) 環境和 [FFmpeg](https://www.ffmpeg.org)
- 安裝必要套件
  ```shell
  pip install -r requirements.txt
  ```

- 配置 config.json
  - `botToken` 你的機器人 Token
  - `CWA_API_KEY` 你的中央氣象署 API_KEY
  - `roles` 身分組頻道設定
    - `adminID` 管理員身分組 ID
  - `guilds` 伺服器頻道設定
    - `welcomeChannelID` 歡迎頻道 ID
    - `leaveChannelID` 離開頻道 ID
    - `dynamicChannelID` 動態語音頻道 ID
  - `valorants` 有關 Valorant 的設定
    - `attackerChannelID` 進攻方語音頻道 ID
    - `defenderChannelID` 守備方語音頻道 ID
    - `maps` 地圖
    - `agents` 角色
  - `teacherSays` 我高中老師的語錄：）

> [!NOTE]
> ID 找不到？</br>
> 請至【Discord 設定】 -> 側邊欄【進階】 -> 打開【開發者模式】</br>
> 接著右鍵點擊語音或文字頻道，就可以看到【複製頻道 ID】

- 若欲使用前綴指令，預設前綴字符為 `=`