import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
from threading import Thread
from multiprocessing import cpu_count
from tqdm import tqdm
import json

# Основная ссылка на Google Play
HOST = 'https://play.google.com'


def get_full_html(url, params=None):
    """
    Получает html страницу после загрузки всех элементов

    Параметры
    ---------
    url : str
        Ссылка на страницу
    params : None

    Возвращает
    ----------
    str
        html код исходной страницы
    """
    # указываем дополнительные опции
    options = Options()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--incognito')
    # безголовая версия браузера
    options.add_argument('--headless')
    driver = webdriver.Firefox(executable_path='driver/geckodriver', options=options)
    # получаем текущую страницу
    driver.get(url)
    # обработка бесконечной прокрутки
    while True:
        # получаем текущую высоту страницы
        cur_height = driver.execute_script("return document.body.scrollHeight")
        # прокрутка вниз страницы
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        # ждем загрузку остальных элементов
        time.sleep(1)
        # высота страницы после загрузки элементов
        height_after_load = driver.execute_script("return document.body.scrollHeight")
        # Если всевозможные элементы уже загрузились, то выходим из цикла
        if cur_height == height_after_load:
            break
    html = driver.page_source
    driver.quit()
    return html


def get_primary_info(html):
    """
    Получает предварительную информацию о приложениях

    Параметры
    ---------
    html : str
        Полная html страница с результатом поиска

    Возвращает
    ----------
    dict[int: dict[str: str]]
        Словарь первичной информации о приложениях
    """
    soup = BeautifulSoup(html, 'html.parser')
    # находим все карточки с приложениями
    items = soup.find_all('div', class_='vU6FJ p63iDd')
    apps = {}

    for i, item in enumerate(items, 1):
        # рейтинг может быть неопределен
        average_rating = item.find('div', class_='pf5lIe')
        if average_rating is not None:
            average_rating = average_rating.find_next('div').get('aria-label').split()[1]
        apps[i] = {
            'name': item.find('div', class_='WsMG1c nnK0zc').get_text(strip=True),
            'author': item.find('div',  class_='KoLSrc').get_text(strip=True),
            'average_rating': average_rating,
            'link': HOST + item.find('div', class_='b8cIId ReQCgd Q9MA7b').find_next('a').get('href'),
        }
    return apps


def get_full_info(apps, id, keyword):
    """
    Получает полную информацию о приложении и дополняет к первичной

    Параметры
    ---------
    apps : dict[int: dict[str: str]]
        Словарь первичной информации о приложениях
    id : int
        Id приложения, для которого необходимо дополнить информацию
    keyword : str
        Ключевое слово, по которому производился поиск

    Возвращает
    ----------
    None
    """
    # получаем ссылку на страницу приолжения
    link = apps[id]['link']
    # указываем дополнительные опции
    options = Options()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--incognito')
    # безголовая версия браузера
    options.add_argument('--headless')
    driver = webdriver.Firefox(executable_path='driver/geckodriver', options=options)
    # получаем текущую страницу
    driver.get(link)
    # получаем html код страницы
    html = driver.page_source
    # больле драйвер не нужен
    driver.quit()
    soup = BeautifulSoup(html, 'html.parser')
    # выделяем карточку с приложением
    app = soup.find('main', class_='LXrl4c')
    # получаем описание
    apps[id]['description'] = app.find('div', class_='DWPxHb').find_next('div').get_text()
    # смотрим, есть ли ключевое слово в описании или названии приложения
    if apps[id]['description'].lower().find(keyword) == -1 \
            and apps[id]['name'].lower().find(keyword) == -1:
        apps.pop(id)
        return
    # получаем категорию приложения
    apps[id]['category'] = app.find('a', class_='hrTbp R8zArc').get_text()
    # получаем количество оценок приложения
    apps[id]['number_of_ratings'] = app.find('span', class_='AYi5wd TBRnV').find_next('span').get_text()
    # получаем дату последнего обновления приложения
    apps[id]['last_update'] = app.find('span', class_='htlgb').get_text()


def parse(url, keyword):
    """
    Парсит все приложения по указанному url
    и проверяет наличие ключевого слова

    Параметры
    ---------
    url : str
        Ссылка на Google Play с запросом
    keyword : str
        Ключевое слово, по которому производился поиск

    Возвращает
    ----------
    dict[int: dict[str: str]]
        Словарь с полной информацией о приложениях
    """
    # получаем полную страницу html со всеми приложениями
    html = get_full_html(url)
    # получаем первичную информацию о приложениях
    apps = get_primary_info(html)
    # создаем список потоков
    threads = [Thread(target=get_full_info, args=(apps, id, keyword)) for id in apps.keys()]
    # определяем количесво итераций
    iteration_count = cpu_count()-1
    # количество обрабатываемых потоков
    count_per_iteration = len(threads) / float(iteration_count)
    for iter_num in tqdm(range(0, iteration_count),
                         desc=f'Processing pages with {int(count_per_iteration)} threads'):
        # определяем индексы
        start = int(count_per_iteration * iter_num)
        end = int(count_per_iteration * (iter_num + 1))
        # запускаем потоки
        for t in threads[start:end]:
            t.daemon = True
            t.start()
            t.join()
    return apps


if __name__ == '__main__':
    keyword = input('Еnter the keyword: (for example, "сбербанк")\n').lower()
    url = HOST + f'/store/search?q={keyword}&c=apps'
    apps = parse(url, keyword)
    # сохраняем результат в формате json в папке data
    with open(f'data/{keyword}.json', 'w') as file:
        json.dump(apps, file)

