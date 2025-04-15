@echo off
echo Building C++ backend with Visual Studio...
call "C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\Tools\VsDevCmd.bat"
cd cpp_backend\build
msbuild simulation_engine.vcxproj /p:Configuration=Release
echo Build completed.
if exist x64\Release\simulation_engine.exe (
    echo Executable found at x64\Release\simulation_engine.exe
) else (
    echo Looking for executable in alternative locations...
    dir /s /b simulation_engine.exe
)
cd ..\.. 