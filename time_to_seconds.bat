@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem time_to_seconds.bat
rem Convert current local time to seconds.
rem   1) seconds since local midnight (0-86399)
rem   2) Unix epoch seconds (UTC)
rem Usage:
rem   time_to_seconds.bat
rem   time_to_seconds.bat midnight
rem   time_to_seconds.bat unix

set "MODE=%~1"
if /I "%MODE%"=="" set "MODE=all"

set "T=%TIME%"
if "!T:~0,1!"==" " set "T=0!T:~1!"

set "HH=!T:~0,2!"
set "MM=!T:~3,2!"
set "SS=!T:~6,2!"

rem strip leading zeros for set /a (avoid octal 08/09)
set /a H=1!HH! - 100
set /a M=1!MM! - 100
set /a S=1!SS! - 100
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

echo ========================================
echo  Date/Time : %DATE%  %TIME%
echo ----------------------------------------
echo  Clock     : !HH!:!MM!:!SS!
echo  Midnight  : !SECONDS_SINCE_MIDNIGHT! sec  (H*3600+M*60+S)
echo ----------------------------------------
for /f "usebackq delims=" %%U in (`powershell -NoProfile -Command "[int][double]::Parse((Get-Date -UFormat %%s))"`) do set "UNIX_TS=%%U"
echo  Unix TS   : !UNIX_TS! sec  (since 1970-01-01 UTC)
echo ========================================
echo.
echo  Quiet modes:
echo    time_to_seconds.bat midnight
echo    time_to_seconds.bat unix

endlocal
exit /b 0
