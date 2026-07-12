@echo off
chcp 65001 >nul
setlocal EnableExtensions EnableDelayedExpansion

rem ============================================================
rem  time_to_seconds.bat
rem  功能：把「当前时间」换算成秒
rem    1) 今日已过秒数（自 00:00:00 起，0~86399）
rem    2) Unix 时间戳（自 1970-01-01 UTC 起的秒数）
rem  用法：
rem    time_to_seconds.bat              显示两种结果
rem    time_to_seconds.bat midnight     只输出今日已过秒数（便于脚本调用）
rem    time_to_seconds.bat unix         只输出 Unix 时间戳
rem ============================================================

set "MODE=%~1"
if /I "%MODE%"=="" set "MODE=all"

rem ---- 读取当前本地时间（HH:MM:SS.xx）----
set "T=%TIME%"
rem 去掉前导空格（小时 < 10 时）
if "!T:~0,1!"==" " set "T=0!T:~1!"

set "HH=!T:~0,2!"
set "MM=!T:~3,2!"
set "SS=!T:~6,2!"

rem 去掉可能的前导零，避免 set /a 把 08/09 当八进制
set /a H=1%HH% - 100
set /a M=1%MM% - 100
set /a S=1%SS% - 100

set /a SECONDS_SINCE_MIDNIGHT=H*3600 + M*60 + S

if /I "%MODE%"=="midnight" (
    echo !SECONDS_SINCE_MIDNIGHT!
    endlocal & exit /b 0
)

if /I "%MODE%"=="unix" (
    for /f "usebackq delims=" %%U in (`powershell -NoProfile -Command "[int][double]::Parse((Get-Date -UFormat %%s))"`) do set "UNIX_TS=%%U"
    echo !UNIX_TS!
    endlocal & exit /b 0
)

rem ---- 默认：完整显示 ----
echo ========================================
echo  当前日期时间：%DATE%  %TIME%
echo ----------------------------------------
echo  时分秒：!HH!:!MM!:!SS!
echo  今日已过秒数：!SECONDS_SINCE_MIDNIGHT! 秒
echo            （公式：时*3600 + 分*60 + 秒）
echo ----------------------------------------

for /f "usebackq delims=" %%U in (`powershell -NoProfile -Command "[int][double]::Parse((Get-Date -UFormat %%s))"`) do set "UNIX_TS=%%U"
echo  Unix 时间戳：!UNIX_TS! 秒
echo            （自 1970-01-01 00:00:00 UTC 起）
echo ========================================
echo.
echo  静默用法：
echo    time_to_seconds.bat midnight   -^> 只输出今日秒数
echo    time_to_seconds.bat unix       -^> 只输出 Unix 时间戳

endlocal
exit /b 0
