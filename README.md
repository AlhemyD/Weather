# Dash-apps

Здесь будут выложены работы веб-приложений на основе Dash (python)

# Погодосборник
Приложение, которое определяет погоду по координатам для списка мест. Алгоритм действий:

1. Загрузить файл с координатами и датой (записанными в колонках `lat`, `lon`, `dt`) в форматах `csv` 
2. Подождать
3. Получить таблицу с данными о погоде
4. Получить карту с точками, при наведении на которые будут показаны сведения о погоде
4.5. Применить фильтры при необходимости
5. Скачать готовый файл с таблицей.

## Установка
### Скачать данные

Кликнуть на `Code` -> `Download ZIP` чтобы скачать архив. После чего извлечь данные.

### Установка зависимостей

Запустить консоль `python`. Перейти в папку `Погодосборник`. При необходимости прописать полный путь (`cd D:/.../.../Погодосборник`)
```
cd Погодосборник 
pip install -r requirements.txt
```
## Использование

1. Подготовить файл в формате `csv` с колонками `lat`, `lon`, `dt`, в которых содержатся координаты и дата.
2. Запуск приложения осуществляется также в консоли `python`
```
python weather.py
```
3. После чего нужно открыть страницу (`localhost:8050`): 
```
Dash is running on http://127.0.0.1:8050/

 * Serving Flask app "geocoder" (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: on
```

### Инструкция по использованию фильтров

1. Найдите поле для ввода, в котором написано "Введите запрос фильтра"
2. Введите запрос фильтра
3. Примечание: названия столбцов необходимо писать в фигурных скобках при формировании запроса фильтра
4. Если вам, например, нужно получить данные по датам между 2013 и 2014 годами, то ваш запрос фильтра будет иметь следующий вид: 
	{название столбца с датами} datestartswith 2013/ or {название столбца с датами} datestartswith 2014/
5. Если вы хотите получить данные по определённым лесничествам, то ваш запрос фильтра будет иметь вид: 
	{название столбца с лесничеством} contains название_лесничества
6. Если вы хотите получить данные, у которых, например, температура выше 30 градусов, то ваш запрос фильтра будет иметь следующий вид:
	{название столбца с температурой} > 30
7. Если вы хотите сбросить фильтры, нажмите на кнопку "Reset"
