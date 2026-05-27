@echo off
REM Heillon Legal - Browser Extension build script (Windows native).
REM Packages the extension into a .zip ready for distribution.
REM
REM Usage:
REM   build.bat           - outputs dist\heillon-extension-v<version>.zip
REM   build.bat --clean   - removes dist\ first

setlocal enabledelayedexpansion
cd /d "%~dp0"

set ROOT_DIR=%CD%
set DIST_DIR=%ROOT_DIR%\dist
set MANIFEST=%ROOT_DIR%\manifest.json

if "%~1"=="--clean" (
    if exist "%DIST_DIR%" (
        echo Cleaning %DIST_DIR%...
        rmdir /s /q "%DIST_DIR%"
    )
)

if not exist "%DIST_DIR%" mkdir "%DIST_DIR%"

REM Generate icons if missing
if not exist "%ROOT_DIR%\icons\icon-128.png" (
    echo Icons missing - generating with PIL...
    python "%ROOT_DIR%\icons\generate_icons.py"
)

REM Build via Python (always available)
python -c "import os, zipfile; from pathlib import Path; root = Path(os.environ['ROOT_DIR_ESCAPED']); import json; manifest = json.load(open(root/'manifest.json')); version = manifest['version']; output = root/'dist'/f'heillon-extension-v{version}.zip'; includes = ['manifest.json', 'src', 'icons/icon-16.png', 'icons/icon-48.png', 'icons/icon-128.png', 'README.md', 'PRIVACY.md']; excludes = ['__pycache__', '.pyc', 'generate_icons.py']; included = lambda p: not any(x in str(p) for x in excludes); z = zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED, compresslevel=9);
[z.write(root/rel, arcname=rel) for rel in includes if (root/rel).is_file()];
[[z.write(child, arcname=str(child.relative_to(root))) for child in (root/rel).rglob('*') if (root/rel).is_dir() and child.is_file() and included(child)] for rel in includes];
z.close();
print(f'\n{output.name}: {output.stat().st_size:,} bytes')"
set EXITCODE=%ERRORLEVEL%

if %EXITCODE% NEQ 0 (
    echo Build failed.
    exit /b %EXITCODE%
)

echo.
echo Done. Distribute via:
echo   - Chrome Web Store:  upload dist\heillon-extension-v*.zip
echo   - Beta testers:      send zip + install instructions
echo   - Dev mode:          chrome://extensions -^> 'Load unpacked' -^> select this folder

endlocal
