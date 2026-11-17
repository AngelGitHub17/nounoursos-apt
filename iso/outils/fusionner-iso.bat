@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
title NounoursOS - Fusion de l'ISO
rem ===========================================================================
rem  NounoursOS - recolle une ISO telechargee en plusieurs morceaux
rem  (.part0, .part1...) et verifie qu'elle est intacte (SHA-256).
rem  Windows : mets ce fichier dans le meme dossier que les .part,
rem            puis double-clique dessus.
rem ===========================================================================
cd /d "%~dp0"

set "FOUND=0"
for %%F in (*.iso.part0) do (
    set "FOUND=1"
    call :fusionner "%%~nF"
    if errorlevel 1 goto :fin
)

if "%FOUND%"=="0" (
    echo Aucun fichier .iso.part0 trouvé dans ce dossier.
    echo Mets fusionner-iso.bat dans le même dossier que les morceaux téléchargés.
)
goto :fin

:fusionner
set "ISO=%~1"
echo.
echo Fusion de %ISO%...

rem Compter les morceaux et vérifier qu'il n'en manque pas
set /a N=0
:compter
if exist "%ISO%.part!N!" (
    set /a N+=1
    goto :compter
)
set /a SUIVANT=N+1
if exist "%ISO%.part!SUIVANT!" (
    echo [ERREUR] Il manque %ISO%.part!N! : télécharge tous les morceaux puis relance.
    exit /b 1
)

copy /b /y "%ISO%.part0" "%ISO%" >nul || (echo [ERREUR] Impossible de créer %ISO% & exit /b 1)
set /a DERNIER=N-1
for /L %%i in (1,1,!DERNIER!) do (
    copy /b /y "%ISO%"+"%ISO%.part%%i" >nul || (echo [ERREUR] Erreur avec %ISO%.part%%i & exit /b 1)
)
echo    !N! morceaux assemblés.

if not exist "%ISO%.sha256" (
    echo    Pas de fichier %ISO%.sha256 : intégrité non vérifiée.
    exit /b 0
)

echo    Vérification de l'intégrité (peut prendre une minute)...
set "ATTENDU="
for /f "usebackq tokens=1" %%h in ("%ISO%.sha256") do if not defined ATTENDU set "ATTENDU=%%h"
set "OBTENU="
for /f "skip=1 tokens=*" %%h in ('certutil -hashfile "%ISO%" SHA256') do if not defined OBTENU set "OBTENU=%%h"
set "OBTENU=!OBTENU: =!"

if /i "!OBTENU!"=="!ATTENDU!" (
    echo    Intégrité OK.
    echo    %ISO% est prête. Tu peux supprimer les fichiers .part.
    echo    Pour la clé USB : Rufus, mode DD.
    exit /b 0
) else (
    echo [ERREUR] L'ISO est abîmée : retélécharge les morceaux puis relance.
    del "%ISO%" >nul 2>&1
    exit /b 1
)

:fin
echo.
pause
