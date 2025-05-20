import sqlite3
import os
from datetime import datetime
import uuid

# Подключение к базе данных
conn = sqlite3.connect('realty.db')
cursor = conn.cursor()

# Удаление существующих данных (для чистоты)
cursor.execute('DELETE FROM properties')
conn.commit()

# Список тестовых данных
properties = [
    # Квартиры
    (1, "Уютная 2-комнатная квартира в центре", "Отличное состояние, новая сантехника, рядом школа и магазины", 75000, "ул. Ленина, 15", "Центр", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "flat", "sale", 65.5, 2, 3, 5, 2015, None, 0, 0, None, None, 1, 1, 1, 1, "images/test1.jpg"),
    (1, "1-комнатная квартира с ремонтом", "Свежий ремонт, мебель включена", 45000, "пр. Мира, 10", "Октябрьский", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "flat", "sale", 38.0, 1, 2, 9, 2010, None, 0, 0, None, None, 1, 1, 1, 0, "images/test2.jpg"),
    (1, "3-комнатная квартира на высоком этаже", "Просторная, с балконом, вид на реку", 120000, "ул. Пионерская, 25", "Ленинский", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "flat", "sale", 90.0, 3, 7, 10, 2020, None, 0, 0, None, None, 1, 1, 1, 1, "images/test3.jpg"),
    (1, "Аренда 2-комнатной квартиры", "Меблирована, центр города", 600, "ул. Советская, 5", "Центр", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "flat", "rent", 55.0, 2, 4, 6, 2018, None, 0, 0, None, None, 1, 1, 1, 0, "images/test4.jpg"),
    # Дома
    (1, "Светлый дом с участком", "Новая постройка, все коммуникации", 150000, "д. Новосёлки", "Октябрьский", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "house", "sale", 120.0, None, None, None, 2022, 10.0, 1, 1, "brick", 95, 1, 1, 1, 1, "images/test5.jpg"),
    (1, "Дача у реки", "Идеальна для отдыха, с баней", 80000, "д. Лесное", "Ленинский", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "cottage", "sale", 80.0, None, None, None, 2015, 5.0, 0, 0, "wood", 80, 0, 1, 1, 0, "images/test6.jpg"),
    (1, "Большой дом в пригороде", "Просторный, с гаражом", 200000, "д. Заречье", "Центр", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "house", "sale", 180.0, None, None, None, 2019, 15.0, 1, 1, "block", 100, 1, 1, 1, 1, "images/test7.jpg"),
    # Земельные участки
    (1, "Участок под строительство", "Рядом лес, коммуникации", 30000, "д. Рощино", "Октябрьский", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "land", "sale", None, None, None, None, None, 8.0, 0, 0, None, None, 1, 0, 1, 0, "images/test8.jpg"),
    # Добавим ещё 22 записи для достижения 30
    (1, "Квартира с видом на парк", "Ремонт 2023 года", 85000, "ул. Парковая, 12", "Центр", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "flat", "sale", 70.0, 2, 5, 7, 2023, None, 0, 0, None, None, 1, 1, 1, 1, "images/test9.jpg"),
    (1, "Аренда студии", "Компактная, центр", 400, "ул. Молодёжная, 3", "Ленинский", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "flat", "rent", 30.0, 1, 1, 4, 2016, None, 0, 0, None, None, 1, 1, 1, 0, "images/test10.jpg"),
    (1, "Дом с садом", "Тихое место, участок 12 соток", 180000, "д. Озёрное", "Октябрьский", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "house", "sale", 150.0, None, None, None, 2021, 12.0, 1, 1, "brick", 90, 1, 1, 1, 0, "images/test11.jpg"),
    (1, "Квартира в новостройке", "С отделкой, лифт", 95000, "пр. Независимости, 20", "Центр", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "flat", "sale", 75.0, 3, 3, 10, 2024, None, 0, 0, None, None, 1, 1, 1, 1, "images/test12.jpg"),
    (1, "Аренда 3-комнатной", "Мебель, техника", 800, "ул. Победы, 8", "Ленинский", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "flat", "rent", 85.0, 3, 6, 9, 2017, None, 0, 0, None, None, 1, 1, 1, 0, "images/test13.jpg"),
    (1, "Дача с террасой", "Удобное расположение", 65000, "д. Липки", "Октябрьский", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "cottage", "sale", 60.0, None, None, None, 2014, 4.0, 0, 0, "wood", 75, 0, 1, 1, 0, "images/test14.jpg"),
    (1, "Участок у озера", "Идеален для дачи", 25000, "д. Прудное", "Ленинский", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "land", "sale", None, None, None, None, None, 6.0, 0, 0, None, None, 0, 0, 1, 0, "images/test15.jpg"),
    (1, "Квартира с евроремонтом", "Новостройка, вид на город", 110000, "ул. Центральная, 7", "Центр", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "flat", "sale", 80.0, 2, 4, 8, 2023, None, 0, 0, None, None, 1, 1, 1, 1, "images/test16.jpg"),
    (1, "Аренда 1-комнатной", "Тихий двор", 500, "ул. Школьная, 14", "Октябрьский", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "flat", "rent", 40.0, 1, 3, 5, 2015, None, 0, 0, None, None, 1, 1, 1, 0, "images/test17.jpg"),
    (1, "Большой дом с подвалом", "С гаражом и садом", 220000, "д. Сосновка", "Ленинский", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "house", "sale", 200.0, None, None, None, 2020, 18.0, 1, 1, "block", 100, 1, 1, 1, 1, "images/test18.jpg"),
    (1, "Квартира в центре", "Рядом метро", 90000, "ул. Горького, 9", "Центр", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "flat", "sale", 68.0, 2, 2, 6, 2019, None, 0, 0, None, None, 1, 1, 1, 0, "images/test19.jpg"),
    (1, "Аренда дома", "С мебелью, на длительный срок", 1000, "д. Зеленое", "Октябрьский", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "house", "rent", 130.0, None, None, None, 2018, 10.0, 1, 0, "brick", 90, 1, 1, 1, 0, "images/test20.jpg"),
    (1, "Участок в лесу", "Тихое место", 35000, "д. Боровое", "Ленинский", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "land", "sale", None, None, None, None, None, 9.0, 0, 0, None, None, 0, 0, 1, 0, "images/test21.jpg"),
    (1, "Квартира с балконом", "Свежий ремонт", 70000, "ул. Комсомольская, 11", "Центр", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "flat", "sale", 60.0, 2, 5, 7, 2022, None, 0, 0, None, None, 1, 1, 1, 1, "images/test22.jpg"),
    (1, "Аренда 2-комнатной", "С техникой", 650, "ул. Кирова, 18", "Октябрьский", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "flat", "rent", 58.0, 2, 3, 5, 2016, None, 0, 0, None, None, 1, 1, 1, 0, "images/test23.jpg"),
    (1, "Дом с видом на реку", "Большой участок", 250000, "д. Речное", "Lенинский", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "house", "sale", 220.0, None, None, None, 2021, 20.0, 1, 1, "brick", 95, 1, 1, 1, 1, "images/test24.jpg"),
    (1, "Квартира в спальном районе", "Тихо, с парковкой", 60000, "ул. Заводская, 4", "Октябрьский", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "flat", "sale", 50.0, 1, 2, 4, 2014, None, 0, 0, None, None, 1, 0, 1, 0, "images/test25.jpg"),
    (1, "Аренда дачи", "Для отдыха", 700, "д. Лесная", "Ленинский", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "cottage", "rent", 70.0, None, None, None, 2013, 3.0, 0, 0, "wood", 70, 0, 1, 1, 0, "images/test26.jpg"),
    (1, "Участок под коттедж", "Рядом дорога", 40000, "д. Полевое", "Октябрьский", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "land", "sale", None, None, None, None, None, 7.0, 0, 0, None, None, 1, 0, 1, 0, "images/test27.jpg"),
    (1, "Квартира в новостройке", "Новостройка", 100000, "пр. Строителей, 6", "Центр", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "flat", "sale", 72.0, 2, 4, 8, 2023, None, 0, 0, None, None, 1, 1, 1, 1, "images/test28.jpg"),
    (1, "Аренда 3-комнатной", "Большая кухня", 900, "ул. Фрунзе, 10", "Ленинский", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "flat", "rent", 90.0, 3, 5, 7, 2019, None, 0, 0, None, None, 1, 1, 1, 0, "images/test29.jpg"),
    (1, "Дом с гаражом", "Новая постройка", 230000, "д. Солнечное", "Октябрьский", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "house", "sale", 190.0, None, None, None, 2022, 14.0, 1, 1, "block", 100, 1, 1, 1, 1, "images/test30.jpg"),
]

# Вставка данных
cursor.executemany('''
    INSERT INTO properties (user_id, title, description, price, location, district, date_added, property_type, listing_type,
                           area, rooms, floor, floors, year_built, land_area, has_basement, has_garage, wall_material,
                           readiness, has_electricity, has_gas, has_water, has_sewerage, photo_path)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', properties)

conn.commit()
conn.close()

print("Тестовые данные успешно добавлены в базу!")