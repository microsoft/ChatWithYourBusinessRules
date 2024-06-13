@ECHO OFF 
ECHO Packaging backend for deployment...
ECHO -----------------------------------
ECHO.
IF EXIST "bin" (
   RD /Q /S bin
)

ECHO Creating output folder...
MD "bin\common"

ECHO Copying content...
COPY app.py bin 
COPY bot.py bin
COPY config.py bin
COPY requirements.txt bin
COPY runserver.sh bin
COPY ..\common\callbacks.py bin\common
COPY ..\common\prompts.py bin\common
COPY ..\common\sql_checkpointer.py bin\common
COPY ..\common\utils.py bin\common
COPY ..\common\__init__.py bin\common

ECHO Destroying CRLF in runserver.sh...
powershell -File "recode-file.ps1" -inputFile "bin\runserver.sh" -outputFile "bin\runserver.sh"

ECHO Done!