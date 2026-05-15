@echo off
:: Переключаем кодировку консоли на UTF-8
chcp 65001 > nul

echo Установка необходимых библиотек для Smart Image Renamer...
pip install customtkinter pillow
echo.
echo Установка завершена!
pause