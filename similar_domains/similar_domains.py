import socket
from queue import Queue
from threading import Thread
import homoglyphs as hg


def get_ips(queue):
    """
    Функция, которая выводит на экран все ip адреса для всех доменов,
    которые хранятся в очереди

    Параметры
    ---------
    queue : Queue[str]
        Очередь, в которой хранятся все домены

    Возращает
    ---------
    None
    """
    for site in iter(queue.get, None):
        try:
            result = ': '
            for info in socket.getaddrinfo(site, 80):
                result += str(info[-1][0]) + ' '
        except IOError:
            pass
        else:
            result = site + ' ' + result
            print(result)


def char_to_digit(word, curr_index=0, all_combs=None):
    """
    Функция, которая рекурсивно заменяет некоторые буквы на похожие на них цифры

    Параметры
    ---------
    word : str
        Слово, в котором будет проводиться замена
    curr_index : int
        Индекс на текущей глубине рекурсии
    all_combs : list[str], optional
        Список всевозможных комбинации всевозможных замен
        (Изменяется при базе рекурсии)

    Возвращает
    ----------
    list[str]
        Список всевозможных комбинации всевозможных замен
    """
    if all_combs is None:
        all_combs = []
    # база рекурсии
    if curr_index == len(word):
        all_combs.append(word)
        return
    # расматриваемая буква
    curr_char = word[curr_index]
    # словарь всевозможных замен
    replace_dict = {'a': '4', 'g': '9', 'i': '1', 'l': '1', 'o': '0', 's': '5', 't': '7', 'z': '2',
                    'а': '4', 'б': '6', 'в': '8', 'з': '3', 'о': '0', 'т': '7'}
    if curr_char in replace_dict.keys():
        # разделения на два случая: заменяем текущую букву и не заменяем
        new_word = word[:curr_index] + replace_dict[curr_char] + word[curr_index + 1:]
        char_to_digit(new_word, curr_index+1, all_combs)
        char_to_digit(word, curr_index+1, all_combs)
    else:
        char_to_digit(word, curr_index+1, all_combs)
    return all_combs


def subdomain_select(domain):
    """
    Выделяет все поддомены из исходного домена

    Параметры
    ---------
    domain : str
        Исходный домен

    Возвращает
    ----------
    list[str]
        Список всех поддоменов
    """
    subdomains = []
    for i in range(1, len(domain)):
        if domain[i-1] == '-' or domain[i] == '-':
            continue
        else:
            subdomains.append(domain[:i] + '.' + domain[i:])
    return subdomains


def delete_one_char(word):
    """
    Формирует список слов из изходного слова с удаленным символом

    Параметры
    ---------
    word : str
        Исходное слово

    Возвращает
    ----------
    list[str]
        Список слов, в которых отсутствует одна буква из исходного слова
    """
    return [word[:i] + word[i+1:] for i in range(len(word))]


def apply_strategies(keyword):
    """
    Применяет стратегии к ключевому слову

    Параметры
    ---------
    keyword : str
        Ключевое слово

    Возвращает
    ----------
    list[str]
        Список ключевых слов после применения всех стратегий
    """
    domains_list = []

    # формируем алфавит
    alphabet = ''.join([chr(i) for i in range(48, 58)])
    alphabet += ''.join([chr(i) for i in range(97, 123)])
    alphabet += ''.join([chr(i) for i in range(1072, 1104)])

    # СТРАТЕГИИ
    # ----------------------------------------
    # 1) добавление одного символа в конец строки
    for char in alphabet:
        domains_list.append(keyword + char)

    # 2) подстановка символа, схожего по написанию
    homoglyphs = hg.Homoglyphs(alphabet=alphabet)
    domains_list.extend(homoglyphs.get_combinations(keyword))
    domains_list.extend(char_to_digit(keyword))

    # 3) выделение поддомена
    domains_list.extend(subdomain_select(keyword))

    # 4) удаление одного символа
    domains_list.extend(delete_one_char(keyword))

    return domains_list


if __name__ == '__main__':
    keywords = input('Enter the keywords: (for example: group-ib google facebook youtube live)\n').split()
    domain_zones = ['com', 'ru', 'net', 'org', 'info', 'cn', 'es', 'top', 'au', 'pl', 'it',
                    'uk', 'tk', 'ml', 'ga', 'cf', 'us', 'xyz', 'top', 'site', 'win', 'bid']
    # ключевые слова после применения стратегий
    extended_keywords = []
    # всевозможные ключевые слова с доменными зонами
    sites_with_zones = []

    # применяем стратегии к каждому ключевому слову
    for keyword in keywords:
        extended_keywords.extend(apply_strategies(keyword))

    # добавляем к каждому ключевому слову все доменные зоны
    for keyword in extended_keywords:
        for domain_zone in domain_zones:
            sites_with_zones.append(keyword + '.' + domain_zone)

    # формируем потоки
    queue = Queue()
    threads = [Thread(target=get_ips, args=(queue,)) for _ in range(50)]
    for t in threads:
        t.daemon = True
        t.start()

    # помещаем проверяемый сайт в очередь
    for site in sites_with_zones:
        queue.put(site)
    # добавляем сигнализацию конца
    for _ in threads:
        queue.put(None)
    # ждем завершения
    for t in threads:
        t.join()