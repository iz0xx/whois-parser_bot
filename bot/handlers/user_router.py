import re
import time
import requests

from aiogram.types import InputFile, FSInputFile
from builders.inline_keyboard_builder import create_button
from bot import bot
from selenium import webdriver
from aiogram.methods.send_photo import SendPhoto
from aiogram import types, Router
from aiogram.filters import Command
from bs4 import BeautifulSoup as BS
from selenium.common import WebDriverException


CACHE_PERIOD_SEC = 3600
user_router = Router()
cache = {}

def check_url(url: str):
    url = re.match(r"([a-zа-я0-9-.]+)?[a-zа-я0-9-]+\.[a-zа-я.]{2,6}",
        url.removeprefix('http://').removeprefix('https://').removeprefix('www.').split('#')[0]
        .split('/')[0].split('@')[-1].split(':')[0]
    )
    return url.group() if url else False

def format_info(info, url):
    for key in info[url]:
        domain_value = info[url][key][key]
        if len(domain_value) == 1:

            domain_text_unparsed = str(domain_value[0]).split('\n')[1].strip().split('<br>')
            if '% ' in domain_text_unparsed[0]:
                domain_text_unparsed = domain_text_unparsed[3:]
                domain_text_unparsed_pt1 = [domain_text_unparsed[0]]
                domain_text_unparsed_pt2 = domain_text_unparsed[1].split('<br/>')[:-1]
            else:
                domain_text_unparsed_pt1 = domain_text_unparsed[0:4]
                domain_text_unparsed_pt2 = domain_text_unparsed[4].split('<br/>')[:-1]

            domain_text_unparsed = domain_text_unparsed_pt1 + domain_text_unparsed_pt2
            for element in domain_text_unparsed:
                if '<a' in element:
                    element_unparsed = element.split(':', 1)
                    if len (element_unparsed) == 1:
                        continue
                    domain_text_unparsed[domain_text_unparsed.index(element)] = ': '.join([f'<b>{element_unparsed[0].strip()}</b>', f'<i>{BS(element_unparsed[1], 'html.parser').text.strip()}</i>'])
                else:
                    element_value = element.split(':', 1)
                    if len(element_value) == 1:
                        continue
                    element_value[0] = f'<b>{element_value[0].strip()}</b>'
                    element_value[1] = f'<i>{element_value[1].strip()}</i>'
                    domain_text_unparsed[domain_text_unparsed.index(element)] = ': '.join(element_value)
            domain_text_unparsed.pop(0)
            domain_text = '\n'.join(domain_text_unparsed)
            info[url][key] = {'title': f'<b>{key}</b>\n', 'domain_info': domain_text}

        if len(domain_value) > 1:
            domain_value = domain_value[1:]
            domain_value = domain_value[1:]
            for value in domain_value:
                if '<a' in str(value):
                    value_text = value.text.strip()
                    element_unparsed = value_text.split(':', 1)
                    domain_value[domain_value.index(value)] = ':'.join([f'<b>{element_unparsed[0]}</b>', f'<i>{BS(element_unparsed[1], 'html.parser').text}</i>'])
                else:
                    value_text = value.text.strip()
                    element_value = value_text.split(':', 1)
                    element_value[0] = f'<b>{element_value[0]}</b>'
                    element_value[1] = f'<i>{element_value[1]}</i>'
                    domain_value[domain_value.index(value)] = ':'.join(element_value)
            domain_text = '\n'.join(domain_value)
            info[url][key] = {'title': f'<b>{key}</b>\n', 'domain_info': domain_text}
    return info[url]

async def get_info(url):
        try:
            r = requests.get(f'https://www.reg.ru/whois/?dname={url}')
            soup = BS(r.content, 'html.parser')
            isreg = soup.find('p', class_='b-whois-domain-status__result')
            wrapper = soup.find('div', class_='p-whois__table-wrapper')
            ds_body = soup.find('div', class_='ds-table__body')
            info = {}
            if wrapper and isreg.text != 'свободен':
                info[url] = {}
                title_wrappers = wrapper.find_all('div', class_='ds-table__body')
                titles = []
                for title_wrapper in title_wrappers:
                    title = title_wrapper.find('h3', class_='p-whois__table-header').text.strip()
                    titles.append(title)
                    domain_info_unparsed = title_wrapper.find_all('p', class_='p-whois__text-cell')
                    info[url][title] = {title: domain_info_unparsed}
                info[url] = format_info(info, url)
                for title in titles:
                    domain = '.'.join(url.split('.')[:-1])
                    domain_1st = url.split('.')[-1]
                    domains_1st_list = ['com', 'ru', 'pro', 'is']
                    if domain_1st in domains_1st_list:
                        domains_1st_list.remove(domain_1st)
                    info[url]['sentence'] = f'Если вы хотите приобрести похожий домен, Вы можете попробовать ввести <i>{domain}.{domains_1st_list[0]}</i>, <i>{domain}.{domains_1st_list[1]}</i>, <i>{domain}.{domains_1st_list[2]}</i> и т.д.\nИли, нажав на кнопку ниже, просмотреть все возможные варианты.'
                    add_to_cache(url, info[url][title]['domain_info'], info[url]['sentence'])
                info_string = f"{info[url][titles[0]]['title']}\n{info[url][titles[0]]['domain_info']}\n\n{info[url][titles[1]]['title']}\n{info[url][titles[1]]['domain_info']}"

                return f"<i>{url}</i> - <b>занят!</b>\n\n{info_string}\n\n{info[url]['sentence']}"

            elif isreg.text != 'свободен' and len(ds_body.find_all('p', class_='p-whois__text-cell')) == 1:
                info[url] = {}
                title = ds_body.find('h3', class_='p-whois__table-header').text.strip()
                domain_info_unparsed = ds_body.find_all('p', class_='p-whois__text-cell')
                info[url][title] = {title: domain_info_unparsed}
                info[url] = format_info(info, url)
                domain = '.'.join(url.split('.')[:-1])
                domain_1st = url.split('.')[-1]
                domains_1st_list = ['com', 'ru', 'pro', 'is']
                if domain_1st in domains_1st_list:
                    domains_1st_list.remove(domain_1st)
                info[url]['sentence'] = f'Если вы хотите приобрести похожий домен, Вы можете попробовать ввести <i>{domain}.{domains_1st_list[0]}</i>, <i>{domain}.{domains_1st_list[1]}</i>, <i>{domain}.{domains_1st_list[2]}</i> и т.д.\nИли, нажав на кнопку ниже, просмотреть все возможные варианты.'
                add_to_cache(url, info[url][title]['domain_info'], info[url]['sentence'])
                info_string = f"{info[url][title]['title']}\n{info[url][title]['domain_info']}"
                return f"<i>{url}</i> - <b>занят!</b>\n\n{info_string}\n\n{info[url]['sentence']}"

            elif isreg.text != 'свободен':
                wrapper = soup.find('div', class_='ds-table__body')
                title = wrapper.find('h3', class_='p-whois__table-header').text.strip()
                blocks = wrapper.find_all('div', class_='ds-table__row-body')
                domain_info = ''
                for block in blocks:
                    name = f'<b>{block.find('p', class_='p-whois__title-cell').text.strip()}</b>'
                    value = f'<i>{block.find('p', class_='p-whois__text-cell').text.strip()}</i>'
                    domain_info += f'{name}: {value}\n'
                info[url] = {'title': title, 'domain_info': domain_info.rstrip()}
                domain = '.'.join(url.split('.')[:-1])
                domain_1st = url.split('.')[-1]
                domains_1st_list = ['com', 'ru', 'pro', 'is']
                if domain_1st in domains_1st_list:
                    domains_1st_list.remove(domain_1st)
                info[url]['sentence'] = f'Если вы хотите приобрести похожий домен, Вы можете попробовать ввести <i>{domain}.{domains_1st_list[0]}</i>, <i>{domain}.{domains_1st_list[1]}</i>, <i>{domain}.{domains_1st_list[2]}</i> и т.д.\nИли, нажав на кнопку ниже, просмотреть все возможные варианты.'
                add_to_cache(url, info[url]['domain_info'], info[url]['sentence'])

                return f"<i>{url}</i> - <b>занят!</b>\n\n{info[url]['domain_info']}\n\n{info[url]['sentence']}"

            else:
                domain_1st = url.split('.')[-1]
                domains_1st_list = ['com', 'ru', 'pro', 'is']
                if domain_1st in domains_1st_list:
                    domains_1st_list.remove(domain_1st)

                sentence = 'Вы можете приобрести данный домен по кнопке ниже.'
                add_to_cache(f'{url}', 'свободен', sentence)
                return f'<i>{url}</i>  - <b>свободен!</b>\n\nВы можете приобрести данный домен по кнопке ниже.'
        except Exception:
            return f'Произошла неизвестная ошибка... Попробуйте еще раз.'


def add_to_cache(url, domain_info, sentence, screenshot='-'):
    global cache
    cache[url] = {"domain_info": domain_info, 'sentence': sentence, "expires_at": time.time() + CACHE_PERIOD_SEC, 'screenshot': screenshot}

@user_router.message(Command('start'))
async def cmd_start(msg: types.Message) -> None:
    await msg.reply('Привет! Это бот-парсер whois. Отправь ссылку, чтобы узнать всю информацию о домене.')

@user_router.message()
async def usr_message(msg: types.Message) -> None:
    if msg.content_type != 'text':
        await msg.reply("Это не ссылка!")
    else:
        url = check_url(msg.text.lower())
        if url:
            if cache.get(url) and cache[url]["expires_at"] >= time.time() and cache[url]['domain_info'] == 'свободен':
                await msg.reply(f'<i>{url}</i> - <b>свободен!</b>\n\n{cache[url]['sentence']}', reply_markup=create_button('Купить домен', f'https://www.reg.ru/buy/domains/?query={url}'))

            elif cache.get(url) and cache[url]["expires_at"] >= time.time() and cache[url]['screenshot'] != '-':
                photo = FSInputFile(cache[url]['screenshot'])
                await bot.send_photo(msg.chat.id, photo)
                await bot.send_message(msg.chat.id, f"<i>{url}</i> - <b>занят!</b>\n\n{cache[url]['domain_info']}\n\n{cache[url]['sentence']}", reply_markup=create_button('Просмотреть варианты', f'https://www.reg.ru/buy/domains/?query={url}'))

            elif cache.get(url) and cache[url]["expires_at"] >= time.time():
                await msg.reply(f"<i>{url}</i> - <b>занят!</b>\n\n{cache[url]['domain_info']}\n\n{cache[url]['sentence']}", reply_markup=create_button('Просмотреть варианты', f'https://www.reg.ru/buy/domains/?query={url}'))
            else:
                msg = await msg.reply('Ожидайте, идет поиск....')
                info = await get_info(url)
                if 'ошибка' in info:
                    await msg.edit_text(f"{info}")
                elif 'свободен' in info:
                    await msg.edit_text(f"{info}", reply_markup=create_button('Купить домен', f'https://www.reg.ru/buy/domains/?query={url}'))
                else:
                    driver = webdriver.Chrome()
                    try:
                        driver.get(f'https://{url}')
                        driver.save_screenshot(f'{url}.png')
                        add_to_cache(url, cache[url]['domain_info'], cache[url]['sentence'], screenshot=f'{url}.png')
                        photo = FSInputFile(f"{url}.png")

                        await msg.delete()
                        await bot.send_photo(msg.chat.id, photo, caption=f"")
                        await bot.send_message(msg.chat.id, f"<i>{url}</i> - <b>занят!</b>\n\n{cache[url]['domain_info']}\n\n{cache[url]['sentence']}", reply_markup=create_button('Просмотреть варианты', f'https://www.reg.ru/buy/domains/?query={url}'))
                    except WebDriverException:
                        await msg.edit_text(f"{info}", reply_markup=create_button('Просмотреть варианты', f'https://www.reg.ru/buy/domains/?query={url}'))
                    driver.close()
        else:
            await msg.reply("Это не ссылка!")