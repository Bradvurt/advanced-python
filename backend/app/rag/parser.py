from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, MoveTargetOutOfBoundsException
from selenium.webdriver import ActionChains
# from selenium.webdriver.chrome.service import Service as ChromiumService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from bs4 import BeautifulSoup
import json
from time import sleep
import time
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, urlencode

class WebParser:
    """
    Парсер данных о заведениях с Яндекс.Карт.

    Использует Selenium для имитации действий пользователя (поиск, прокрутка,
    открытие карточек) и BeautifulSoup для извлечения данных из HTML.
    Этот подход необходим, так как Яндекс.Карты активно используют JavaScript для
    динамической загрузки контента.
    """

    def __init__(self, headless: bool = True):

        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Инициализация драйвера
        # self.driver = webdriver.Chrome(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
        # self.driver = webdriver.Chrome(options=chrome_options)
        # self.wait = WebDriverWait(self.driver, 10)

    def parse_ymaps(self, city: str = "Москва", category: str = "Ресторан", items: int = 5) -> List[Dict[str, Any]]:
        """
        Основной метод парсинга заведений с Яндекс.Карт.

        Args:
            city: Город для поиска (например, "Москва").
            category: Категория заведений (например, "Ресторан", "Кафе")[citation:3].
            items: Количество заведений для парсинга.

        Returns:
            List[Dict[str, Any]]: Список словарей с данными о заведениях.

        Note:
            Для стабильности работы добавлены паузы (`sleep`). В продакшн-среде
            рекомендуется заменить на явные ожидания (WebDriverWait).
        """
        print(city, category)

        # Настройка и запуск экземпляра браузера для данной сессии парсинга
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-dev-shm-usage')
        # driver = webdriver.Chrome(service=ChromiumService(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()), options=chrome_options)
        driver = webdriver.Chrome(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install(), options=chrome_options)
        driver.get('https://yandex.ru/maps')
        sleep(2)

        # Ввод поискового запроса
        form = driver.find_element(By.CLASS_NAME, "search-form-view__input")
        searchbar = form.find_element(By.TAG_NAME, "input")
        if searchbar:
            if searchbar.get_attribute("type") == "text":
                searchbar.send_keys(city + ' ' + category)

        # Нажатие на кнопку поиска
        driver.find_element_by_class_name(name='small-search-form-view__button').click()
        sleep(2)

        # Элемент для прокрутки списка результатов
        slider = driver.find_element_by_class_name(name='scroll__scrollbar-thumb')

        # Основная вкладка со списком всех организаций
        parent_handle = driver.window_handles[0]

        id = 0
        organizations_href = ""

        venues = []

        print(driver.current_url)

        for i in range(items):
            # Прокрутка списка результатов для подгрузки новых элементов
            ActionChains(driver).click_and_hold(slider).move_by_offset(0, 100).release().perform()

            # Обновление списка ссылок на организации каждые 5 итераций
            if (id == 0) or (id % 5 == 0):
                organizations_href = driver.find_elements_by_class_name(name='link-overlay')
            organization_url = organizations_href[i].get_attribute("href")
            print(organization_url)

            # Открытие карточки организации в новой вкладке
            driver.execute_script(f'window.open("{organization_url}","org_tab");')
            child_handle = [x for x in driver.window_handles if x != parent_handle][0]
            driver.switch_to.window(child_handle)
            sleep(1)

            # Парсинг HTML основной карточки организации
            soup = BeautifulSoup(driver.page_source, "lxml")

            venue = {
                "source": "ymaps",
                "parsed_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            ypage = driver.current_url
            print("YPAGE", ypage)
            current_url_split = ypage.split('/')

            id += 1

            # Извлечение Yandex ID из URL
            venue["yandex_id"] = current_url_split[6]

            # Извлечение различных атрибутов заведения с помощью класса InfoGetter
            venue["name"] = InfoGetter.get_name(soup)
            venue["category"] = InfoGetter.get_catergory(soup)
            venue["address"] = InfoGetter.get_address(soup)
            # venue["website"] = InfoGetter.get_website(soup)
            venue["opening_hours"] = InfoGetter.get_opening_hours(soup)
            venue["ypage"] = driver.current_url
            venue["rating"] = InfoGetter.get_rating(soup)
            # print(venues)

            # Попытка извлечь товары и услуги (меню)
            goods = ""
            try:
                menu = driver.find_element_by_class_name(name='card-feature-view__main-content')
                menu_text = driver.find_element_by_class_name(name='card-feature-view__main-content').text

                if ('товары и услуги' in menu_text.lower()) or ('меню' in menu_text.lower()):
                    # Клик для раскрытия раздела с товарами/услугами
                    menu.click()
                    sleep(2)
                    soup = BeautifulSoup(driver.page_source, "lxml")
                    goods = InfoGetter.get_goods(soup)
            except NoSuchElementException:
                # Раздел с товарами/услугами отсутствует
                pass

            #  Переход на вкладку "Отзывы"
            reviews_url = 'https://yandex.ru/maps/org/' + current_url_split[5] + '/' + current_url_split[6] + \
                            '/reviews'
            driver.get(reviews_url)
            sleep(2)

            venue["reviews"] = InfoGetter.get_reviews(soup, driver)
            # print(venue)
            venues.append(venue)

            """
            # Пример кода для сохранения данных в JSON файл
            print(id, name, address, website, opening_hours, ypage, goods, rating,
                                            reviews)
            
            import os
            print(os.getcwd())
            print(JSONWorker.into_json(id, name, address, website, opening_hours, ypage, goods, rating,
                                            reviews))
            # Записываем данные в OUTPUT.json
            output = JSONWorker.into_json(id, name, address, website, opening_hours, ypage, goods, rating,
                                            reviews)
            JSONWorker("set", output, id+".json")
            print(f'Данные добавлены, id - {id}')
            """

            # Закрытие вкладки с карточкой организации и возврат к списку результатов
            driver.close()
            driver.switch_to.window(parent_handle)
            sleep(1)


        # print('Данные сохранены в OUTPUT.json')
        driver.quit()
        print(venues)
        return venues

class InfoGetter(object):

    @staticmethod
    def get_name(soup_content):
        """Извлекает название организации из HTML."""

        try:
            for data in soup_content.find_all("h1", {"class": "orgpage-header-view__header"}):
                name = data.getText()

            return name
        except Exception:
            return ""
    
    @staticmethod
    def get_catergory(soup_content):
        """Извлекает категорию (рубрику) организации."""

        try:
            for data in soup_content.find_all("a", {"class": "breadcrumbs-view__breadcrumb _outline"}):
                name = data.getText()

            return name
        except Exception:
            return ""

    @staticmethod
    def get_address(soup_content):
        """Извлекает адрес организации."""

        try:
            for data in soup_content.find_all("a", {"class": "business-contacts-view__address-link"}):
                address = data.getText()

            return address
        except Exception:
            return ""

    @staticmethod
    def get_website(soup_content):
        """Извлекает веб-сайт организации."""

        try:
            for data in soup_content.find_all("span", {"class": "business-urls-view__text"}):
                website = data.getText()

            return website
        except Exception:
            return ""

    @staticmethod
    def get_opening_hours(soup_content):
        """Извлекает график работы организации."""

        opening_hours = []
        try:
            for data in soup_content.find_all("meta", {"itemprop": "openingHours"}):
                opening_hours.append(data.get('content'))

            return opening_hours
        except Exception:
            return ""

    @staticmethod
    def get_goods(soup_content):
        """
        Извлекает список товаров и услуг с ценами.
        Обрабатывает два типа представления меню: витрина и список.
        """

        dishes = []
        prices = []

        try:
            # Парсинг меню в формате "витрины" (с фотографиями)
            for dish_s in soup_content.find_all("div", {"class": "related-item-photo-view__title"}):
                dishes.append(dish_s.getText())

            for price_s in soup_content.find_all("span", {"class": "related-product-view__price"}):
                prices.append(price_s.getText())

            # Парсинг меню в формате "списка"
            for dish_l in soup_content.find_all("div", {"class": "related-item-list-view__title"}):
                dishes.append(dish_l.getText())

            for price_l in soup_content.find_all("div", {"class": "related-item-list-view__price"}):
                prices.append(price_l.getText())

        # Если меню представлено только в виде списка
        except NoSuchElementException:
            try:
                for dish_l in soup_content.find_all("div", {"class": "related-item-list-view__title"}):
                    dishes.append(dish_l.getText())

                for price_l in soup_content.find_all("div", {"class": "related-item-list-view__price"}):
                    prices.append(price_l.getText())
            except Exception:
                pass

        except Exception:
            return ""

        # Объединение списков блюд и цен в словарь
        return dict(zip(dishes, prices))

    @staticmethod
    def get_rating(soup_content):
        """Извлекает рейтинг организации."""

        rating = ""
        try:
            for data in soup_content.find_all("span", {"class": "business-summary-rating-badge-view__rating-text"}):
                rating += data.getText()
            return rating
        except Exception:
            return ""

    @staticmethod
    def get_reviews(soup_content, driver):
        """
        Извлекает текст отзывов об организации.
        Выполняет прокрутку страницы отзывов для подгрузки и раскрытия полного текста.
        """

        reviews = []
        slider = driver.find_element_by_class_name(name='scroll__scrollbar-thumb')

        # Определение количества отзывов
        try:
            reviews_count = int(soup_content.find_all("div", {"class": "tabs-select-view__counter"})[-1].text)

        except ValueError:
            reviews_count = 0

        except AttributeError:
            reviews_count = 0

        except Exception:
            return ""

        # Определение необходимого количества итераций прокрутки
        if reviews_count > 150:
            find_range = range(5)
        else:
            find_range = range(3)

        # Прокрутка и раскрытие текста отзывов
        for i in find_range:
            try:
                driver.find_elements_by_class_name(name='business-review-view__expand')[0].click()
                ActionChains(driver).click_and_hold(slider).move_by_offset(0, 25).release().perform()
                

            except MoveTargetOutOfBoundsException:
                ActionChains(driver).click_and_hold(slider).move_by_offset(0, 25).release().perform()
                continue

            except Exception:
                break

        # Парсинг раскрытого текста отзывов
        try:
            soup_content = BeautifulSoup(driver.page_source, "lxml") #business-review-view__body #spoiler-view__text-container
            for data in soup_content.find_all("span", {"class": "spoiler-view__text-container"}):
                reviews.append(data.getText())

            return reviews
        except Exception:
            return ""

class JSONWorker(object):

    def __init__(self, flag, filename, result):
        self.result = result
        _selector = {
            "get": self.get_jsonwork,
            "set": self.set_jsonwork,
        }
        _selector[flag]()

    def get_jsonwork(self):
        with open(filename, 'w+', encoding='utf-8') as f:
            json.dump(self.result, f, ensure_ascii=False, indent=4)

    def set_jsonwork(self):
        with open(filename, 'a+', encoding='utf-8') as f:
            json.dump(self.result, f, ensure_ascii=False, indent=4)

    def into_json(id, name, address, website, opening_hours, ypage, goods, rating, reviews):
        """
        Форматирует данные об организации в структурированный словарь для JSON.
        Приводит график работы к единому формату, заполняя пропущенные дни.
        """

        opening_hours_new = []
        days = ['mo', 'tu', 'we', 'th', 'fr', 'sa', 'su']

        for day in opening_hours:
            opening_hours_new.append(day[:2].lower())
        for i in days:
            if i not in opening_hours_new:
                opening_hours.insert(days.index(i), '   выходной')

        data_grabbed = {
            "ID": id,
            "name": name,
            "address": address,
            "website": website,
            "opening_hours":
                {
                    "mon": opening_hours[0][3:],
                    "tue": opening_hours[1][3:],
                    "wed": opening_hours[2][3:],
                    "thu": opening_hours[3][3:],
                    "fri": opening_hours[4][3:],
                    "sat": opening_hours[5][3:],
                    "sun": opening_hours[6][3:]
                },
            "ypage": ypage,
            "goods": goods,
            "rating": rating,
            "reviews": reviews

        }
        return data_grabbed