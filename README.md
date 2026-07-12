# -TCP-

TCP 相关工具与脚本仓库。

## 仓库文件

| 文件 | 说明 |
|------|------|
| `tcp_txt_server_watcher.py` | TCP 文本服务监视相关 |
| `tcp_txt_watcher.py` | TCP 文本监视相关 |
| `TCP_TXT_Server_GUI_Deploy.zip` | GUI 部署包 |
| `time_to_seconds.bat` | **当前时间换算成秒**（Windows 批处理） |

---

## `time_to_seconds.bat` 使用说明

### 功能

把**当前本地时间**换算成秒，提供两种结果：

| 名称 | 含义 | 范围 / 说明 |
|------|------|-------------|
| **今日已过秒数 (midnight)** | 从当天 `00:00:00` 到现在经过的秒数 | `0` ~ `86399` |
| **Unix 时间戳 (unix)** | 从 `1970-01-01 00:00:00 UTC` 起的秒数 | 全局统一时间戳 |

计算公式（今日秒数）：

```text
秒 = 时 × 3600 + 分 × 60 + 秒
```

### 环境要求

- Windows（`cmd.exe`）
- 系统自带 PowerShell（用于 Unix 时间戳；仅 `midnight` 模式不需要）

### 用法

双击运行，或在命令行中：

```bat
REM 完整显示（推荐）
time_to_seconds.bat

REM 只输出「今日已过秒数」（一行数字，适合被其它脚本调用）
time_to_seconds.bat midnight

REM 只输出 Unix 时间戳（一行数字）
time_to_seconds.bat unix
```

### 输出示例

完整模式大致如下：

```text
========================================
 Date/Time : 2026/07/12 周日  12:34:14.81
----------------------------------------
 Clock     : 12:34:14
 Midnight  : 45254 sec  (H*3600+M*60+S)
----------------------------------------
 Unix TS   : 1783859655 sec  (since 1970-01-01 UTC)
========================================
```

静默模式：

```text
C:\> time_to_seconds.bat midnight
45254

C:\> time_to_seconds.bat unix
1783859655
```

### 在其它脚本中调用

**批处理：**

```bat
for /f %%S in ('time_to_seconds.bat midnight') do set SEC=%%S
echo 今日已过秒数=%SEC%
```

**PowerShell：**

```powershell
$sec = & .	ime_to_seconds.bat midnight
Write-Host "seconds since midnight: $sec"
```

### 注意事项

1. 脚本正文使用 **ASCII**，避免部分 Windows `cmd` 对 UTF-8 中文批处理解析异常。
2. `midnight` 使用本地时钟（`%TIME%`），与时区/夏令时相关的是「本地日界」。
3. `unix` 通过 PowerShell `Get-Date -UFormat %s` 计算，为 **UTC 纪元秒**。
4. 小时/分/秒小于 10 时会自动处理前导空格与前导零，避免 `set /a` 把 `08`/`09` 当成八进制。

### 下载

- 文件页面：https://github.com/DDZ-K/-TCP-/blob/main/time_to_seconds.bat
- 原始文件：https://raw.githubusercontent.com/DDZ-K/-TCP-/main/time_to_seconds.bat

---

## License

按仓库默认约定使用；如无额外声明，仅供个人/项目内部使用。
