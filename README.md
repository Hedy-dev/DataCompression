# DataCompression
Сравнение эффективности алгоритмов сжатия (BWT+MTF+ZLE+ARI/HUF) на текстах и бинарных данных
---
## Архивация
В папке с файлом archiver.py и другими, которые он использует, лежит файл с
текстом. Чтобы сжать файл, выполним команду
python archiver.py compress rousseau-confessions-lowercase.txt rousseau.compressed
где rousseau-confessions-lowercase.txt – исходный текст
rousseau.compressed – сжатый файл
compress – функция сжатия
(можно не класть файл в папку с кодом, просто указать путь до него)  
## Распаковка
python archiver.py decompress rousseau.compressed decoded_rousseau.txt
rousseau.compressed – сжатый файл
decoded_rousseau.txt – куда хотим записать результат
decompress – команда разархивирования
## Установка зависимотей
  ```pip install -r requirements.txt```
