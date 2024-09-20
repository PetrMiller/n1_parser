import asyncio
import logging
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("log.txt", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

async def scrape_n1():
    async with async_playwright() as p:
        logging.info("Запуск браузера...")
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        url = "https://novosibirsk.n1.ru/kupit/kvartiry/rooms-trehkomnatnye/?price_min=3000000"
        try:
            await page.goto(url, timeout=60000, wait_until='domcontentloaded')
            logging.info(f"Успешно перешли на {url}")
        except PlaywrightTimeoutError as e:
            logging.error(f"Ошибка при загрузке страницы: {e}")
            await browser.close()
            return

        try:
            await page.wait_for_selector('a.link', timeout=10000)
            links = await page.evaluate('''() => {
                return Array.from(document.querySelectorAll('a.link'))
                            .slice(0, 10)
                            .map(a => a.href);
            }''')
            logging.info(f"Найдено {len(links)} ссылок")
        except PlaywrightTimeoutError as e:
            logging.error(f"Ошибка при попытке получить ссылки: {e}")
            await browser.close()
            return

        with open("listings.txt", "w", encoding="utf-8") as file:
            for i, link in enumerate(links):
                try:
                    await page.goto(link, timeout=60000, wait_until='domcontentloaded')
                    logging.info(f"Открыта страница объявления: {link}")

                    try:
                        price = await page.text_content('span.price', timeout=60000)
                        price = price.strip() if price else "Цена не указана"
                    except PlaywrightTimeoutError:
                        logging.error("Ошибка при извлечении цены: Элемент не найден")
                        price = "Ошибка извлечения цены"

                    try:
                        description = await page.text_content('div.text', timeout=60000)
                        description = description.strip() if description else "Описание отсутствует"
                    except PlaywrightTimeoutError:
                        logging.error("Ошибка при извлечении описания: Элемент не найден")
                        description = "Ошибка извлечения описания"

                    try:
                        phone = await page.text_content('a.offer-card-contacts-phones__phone', timeout=60000)
                        phone = phone.strip() if phone else "Телефон не указан"
                    except PlaywrightTimeoutError:
                        logging.error("Ошибка при извлечении телефона: Элемент не найден")
                        phone = "Ошибка извлечения телефона"

                    try:
                        address = await page.text_content('.card-living-content-params__col._last .ui-kit-link__inner', timeout=60000)
                        address = address.strip() if address else "Адрес не указан"
                    except PlaywrightTimeoutError:
                        logging.error("Ошибка при извлечении адреса: Элемент не найден")
                        address = "Ошибка извлечения адреса"

                    file.write(f"Ссылка: {link}\n")
                    file.write(f"Цена: {price}\n")
                    file.write(f"Описание: {description}\n")
                    file.write(f"Телефон: {phone}\n")
                    file.write(f"Адрес: {address}\n")
                    file.write(f"{'='*40}\n")

                    logging.info(f"Записано объявление {i+1}: {link}")
                except Exception as e:
                    logging.error(f"Ошибка при обработке объявления {link}: {e}")

        await browser.close()
        logging.info("Данные сохранены в файл listings.txt")

asyncio.run(scrape_n1())
