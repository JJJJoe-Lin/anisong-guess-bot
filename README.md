# Song Guess Bot

## 指令說明

以下假設指令前綴為 `$`

### 基本指令
* `$summon`：讓機器人加入你所在的語音頻道
* `$disconnect`：讓機器人離開語音頻道
* `$join`：加入遊戲
* `$leave`：離開遊戲
* `$kick <player>`：將指定玩家踢出遊戲（==限 op 使用==）
* `$play`：開始遊戲（==限 op 使用==）
* `$scores`：顯示所有玩家分數
* `$refetch`：重新抓取題庫

### 規則設定（前面請先加`$rule`）

遊戲進行中不得設定

* `show`：顯示當前規則
* `ans_type <name>`：設定要猜的欄位名稱（須與題庫欄位名一致）
* `start_point <name>`：設定歌曲要從何處開始播放
    > 支援的 start_point
    > * `beginning`：從頭
    > * `intro`：前奏
    > * `verse`：主歌
    > * `chorus`：副歌
    > * `random`：隨機
* `length <秒數>`：設定題目播放的時間
* `amount <題數>`：設定題目數量
* `need_season [true|false]`：設定答案是否包含第幾季
* `dup_anime`：設定是否允許重複動畫
* `scoring_mode <mode>`：設定計分方式
    > 支援的計分方式
    > * `first-to-win`：第一個答對者得 1 分
    > * `timing-rush`：第一個答對者得 2 分，接著時間內答對者得 1 分

### 遊戲中指令
* `$next`（`$n`）：切換到下一題（==限 op 使用==）
* `$replay`：重播題目
* `$replay_new`：重設起始點並重播題目（==限 op 使用==）
* `$stop`：停止播放
* `$guess <reply>`（`$g`）：回答
* `$answer`：顯示答案（==限 op 使用==）
    > 在 `first-to-win` 模式下，使用此指令後便不可再回答
* `$qinfo`：顯示此題目詳細資訊（==限 op 使用==）
* `$end`：強制結束此輪遊戲（==限 op 使用==）

### op 管理指令（前面請先加`$op`）
* `add <name>`：讓指定玩家成為 op 之一（==限 op 使用==）
* `kick <name>`：取消指定玩家的 op 身分（==限 op 使用==）
* `list`：列出所有 op

### 分數設定（==限 op 使用==）
* `$add <player> <point>`：增加指定玩家的分數
* `$minus <player> <point>`：扣指定玩家的分數
* `$setpoint <player> <point>`：設定指定玩家的分數
* `$resetpoint`：重設所有玩家分數

### 題目篩選條件設定（前面請先加`$cond`）

> * 篩選條件只有在新的一輪遊戲開始才會套用
> * include 同時最多 10 個

* `show`：顯示目前的篩選條件
    > 篩選時會將每個條件使用 AND 串接
* `reset`：重設篩選條件
* `singer [is | include] <歌手名字>`
* `year [> | >= | == | <= | <] <西元年>`
* `anime [is | include] <動畫名>`
* `type [is | include] <歌曲類型>`
* `tags [is | include] <tag名>`

## 題庫格式
一道題目至少須包含以下資訊
* `name`：歌名（**string**）
* `singer`：歌手（**string**）
* `anime`：動畫名稱（**string**）
* `season`：第幾季（**string**）
* `year`：年份（動畫）（**int**）
* `type`：類型（請見下方說明）（**string**）
* `url`：歌曲網址（Youtube）（**string**）
* `intro`：前奏開始時間（秒）（**int**）
* `verse`：主歌開始時間（秒）（**int**）
* `chorus`：副歌開始時間（秒）（**int**）
* `tags`：其他 tag（**string array**）

## How to build
require python 3.6+
1. `pip3 install -r requriements.txt`
2. 根據 `example_config.ini` 建立 `config.ini`
3. 在 `config.ini` 填入 bot token 與 firebase admin key 的路徑
    > 目前僅支援 firebase
4. 填寫想要的設定
5. `python3 start.py` 啟動 bot