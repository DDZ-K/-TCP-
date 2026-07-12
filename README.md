# -TCP-

**TCP 文本监视与联动工具集** — 监视本地 `.txt` 内容变化，通过 TCP 发送/应答消息；附带时间换算批处理。

## 仓库文件

| 文件 | 说明 |
|------|------|
| `tcp_txt_watcher.py` | **客户端向**：监视目录中 txt 变化，匹配关键字后向 TCP 服务端发消息 |
| `tcp_txt_server_watcher.py` | **服务端向**：监听 TCP 端口，收到请求后在目录中搜 txt 关键字并回复 |
| `TCP_TXT_Server_GUI_Deploy.zip` | GUI 部署包（图形界面版发布压缩包） |
| `time_to_seconds.bat` | 当前时间换算成秒（今日秒数 / Unix 时间戳） |
| `README.md` | 本说明 |

---

## 1. `tcp_txt_watcher.py`（监视 → 主动发 TCP）

### 作用

轮询监视目录下的 `*.txt`，检测文件变化；若内容包含目标关键字，则向指定 IP:端口发送固定文本。

### 默认配置（文件顶部常量，可自行修改）

```text
WATCH_DIR / LOG_DIR     = E:\Download\AI\Test
TARGET_TEXT             = Result=OK
SEND_TEXT               = PING
TCP_IP / TCP_PORT       = 127.0.0.1:9000
SCAN_INTERVAL_SECONDS   = 2
```

### 运行

```bat
python tcp_txt_watcher.py
```

依赖：Python 3.10+（标准库即可：`socket` / `pathlib` 等）。

---

## 2. `tcp_txt_server_watcher.py`（TCP 服务 → 查文件再应答）

### 作用

在本机监听 TCP；客户端连上并发送请求后，在监视目录中查找 txt：

| 文件中出现 | 默认回复 |
|------------|----------|
| `Result=OK` | `PASS` |
| `Result=NG` | `FAIL` |
| 超时未匹配 | `WAIT_TIMEOUT` |

### 默认配置

```text
SERVER_HOST / PORT              = 0.0.0.0:9000
WATCH_DIR                       = E:\Download\AI\Test
SEARCH_TIMEOUT_SECONDS          = 5
SEARCH_RETRY_INTERVAL_SECONDS   = 1
```

### 运行

```bat
python tcp_txt_server_watcher.py
```

---

## 3. GUI 部署包

`TCP_TXT_Server_GUI_Deploy.zip` 为带界面的发布包，解压后按包内说明运行即可（适合不想直接跑 Python 脚本的场景）。

---

## 4. `time_to_seconds.bat` 使用说明

### 功能

把**当前本地时间**换算成秒：

| 名称 | 含义 | 范围 / 说明 |
|------|------|-------------|
| **今日已过秒数 (midnight)** | 从当天 `00:00:00` 到现在 | `0` ~ `86399` |
| **Unix 时间戳 (unix)** | 自 `1970-01-01 00:00:00 UTC` | 全局时间戳 |

公式（今日秒数）：`秒 = 时×3600 + 分×60 + 秒`

### 用法

```bat
time_to_seconds.bat
time_to_seconds.bat midnight
time_to_seconds.bat unix
```

### 输出示例

```text
========================================
 Date/Time : 2026/07/12  12:34:14
 Clock     : 12:34:14
 Midnight  : 45254 sec
 Unix TS   : 1783859655 sec
========================================
```

### 在其它脚本中调用

```bat
for /f %%S in ('time_to_seconds.bat midnight') do set SEC=%%S
echo 今日已过秒数=%SEC%
```

```powershell
$sec = & .\time_to_seconds.bat midnight
Write-Host $sec
```

### 注意

- 正文使用 ASCII，兼容 Windows `cmd` 编码
- `midnight` 基于本地 `%TIME%`；`unix` 依赖 PowerShell
- 已处理小时前导空格与 `08`/`09` 八进制问题

### 下载

- https://github.com/DDZ-K/-TCP-/blob/main/time_to_seconds.bat
- https://raw.githubusercontent.com/DDZ-K/-TCP-/main/time_to_seconds.bat

---

## 典型联调场景

```text
[设备/软件写出 Result=OK 到 txt]
        |
        v
tcp_txt_watcher 监视到变化 --TCP--> 对端设备/服务
        或
对端 --TCP--> tcp_txt_server_watcher 查 txt --回复 PASS/FAIL
```

请按现场路径修改脚本顶部的 `WATCH_DIR`、`TCP_IP`、`TCP_PORT` 等常量。

## 许可证

个人/项目内部使用。
