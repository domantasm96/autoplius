# General
from datetime import datetime
import random
import time
# Data manipulation
import pandas as pd
import numpy as np
import re
# Requests
import requests
from bs4 import BeautifulSoup
# For decoding and reading base64 image
import base64
import pytesseract
from PIL import Image
from io import BytesIO
# For extracting text from image
import cv2
import pytesseract
import io
# For simulating browser bahaviour for solving captchas
from selenium import webdriver

enable_proxy = False


def decode_vin(encoded_vin):
    im = Image.open(BytesIO(base64.b64decode(encoded_vin))).resize((400, 50))
    return pytesseract.image_to_string(im)

def getProxies():
    pr_list = []
    counter = 0
    for i, row in df_proxy[df_proxy.raw_ip.isin(success_proxy)].iterrows():
        print(row.ip, counter, df_proxy[df_proxy.raw_ip.isin(success_proxy)].shape[0])
        counter += 1
        proxy = {'https': f'https://{row.ip}'}
        try:
            r = requests.get('https://api.ipify.org/', timeout=2, proxies=proxy, headers=headers)
            if row.ip.startswith(r.text):
                r = requests.get('https://autoplius.lt/skelbimai/volvo-xc60-2-4-l-visureigis-2009-dyzelinas-9742229.html', timeout=2, proxies=proxy, headers=headers)
                pr_list.append(row.ip)
        except:
            continue
    return pr_list


USER_AGENT = "Mozilla/5.0 (Windows NT 5.1; rv:9.0.1) Gecko/20100101 Firefox/9.0.1"
headers = requests.utils.default_headers()
headers.update(
    {
        'User-Agent': USER_AGENT,
    }

)

proxy_list = requests.get('https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list.txt')
proxies = re.findall('[0-9]+.[0-9]+.[0-9]+.[0-9]+:[0-9]+.*\n', proxy_list.text)
ip_regex = '[0-9]+.[0-9]+.[0-9]+.[0-9]+:[0-9]+'
df_proxy = pd.DataFrame([{'ip': re.findall(ip_regex, proxy)[0], 'country': proxy.split(' ')[1].split('-')[0], 'anonimity': proxy.split(' ')[1].split('-')[1]} for proxy in proxies])
pool_counter = 0
what_is_my_ip = 'https://api.ipify.org/'

status_proxy = requests.get("https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-status.txt")
success_proxy = [re.sub(':.*', '', proxy) for proxy in status_proxy.text.split('\n') if proxy.endswith('success')]
df_proxy['raw_ip'] = df_proxy.ip.apply(lambda x: re.sub(":.*", '', x))

df_urls = pd.read_csv('output.csv', lineterminator='\n')

if enable_proxy:
    tst_success = getProxies()

def get_latest_links():
    sitemap = requests.get('https://autoplius.lt/xml_sitemap/index.xml', headers=headers, timeout=30)
    soup = BeautifulSoup(sitemap.text, "html.parser")
    ads_sitemap = [tag.text for tag in soup.findAll('loc') if 'ann_list' in tag.text]

    product_urls = []
    last_updated = []
    priority = []
    for sitemap_url in ads_sitemap:
        print(sitemap_url)
        sitemap_r = requests.get(sitemap_url, headers=headers, timeout=30)
        links_soup = BeautifulSoup(sitemap_r.text, "html.parser")

        product_urls.extend([tag.find("xhtml:link", {'hreflang': 'en'})['href'] for tag in links_soup.findAll('url')][0::4])
        last_updated.extend([tag.find('lastmod').text for tag in links_soup.findAll('url')][0::4])
        priority.extend([tag.find('priority').text for tag in links_soup.findAll('url')][0::4])

    return pd.DataFrame({'url': product_urls, 'last_updated': last_updated, 'ad_priority': priority})
    #     sitemaps_links.extend({'url': product_urls, 'last_updated': last_updated, 'ad_priority': priority}])


def solve_captcha():
    driver.get('https://autoplius.lt/')
    driver.get_screenshot_as_file('captcha.png')
    input_elem = driver.find_element_by_xpath("//input[@id='code']")
    img = Image.open("captcha.png")
    area = (900, 510, 1025, 560)
    cropped_img = img.crop(area)
    input_elem.send_keys(read_captcha(cropped_img))
    driver.find_element_by_xpath("//button[@type='submit']").click()


def read_captcha(image):
    #     image = Image.open(io.BytesIO(requests.get('https://en.autoplius.lt/utility/captcha/text').content))
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # Morph open to remove noise and invert image
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
    invert = 255 - opening

    # Perform text extraction
    data = re.sub('[ ]*', '', pytesseract.image_to_string(invert, lang='eng', config='--psm 6')).upper()
    res = re.findall('[a-zA-Z]{4}', data)[0] if len(re.findall('[a-zA-Z]{4}', data)) else 'ABCD'
    return res


def print_exception(column_name, e):
    print(column_name, e)


'''
inspect_exceptions = True: display exceptions message if something triggers except block
inspect_exceptions = False: ignore exceptions message if something triggers except block
'''
inspect_exceptions = False

# Driver for solving captchas
driver = webdriver.Firefox(executable_path='/home/domantas/Documents/selenium_drivers/geckodriver')

df = pd.DataFrame()
error_log = pd.DataFrame()

counter = 0
for i, row in df_urls[(df_urls.scrape_date.isnull()) | (df_urls.breadcrumbs == '[]')].iterrows():
    try:
        if enable_proxy:
            try:
                proxy = {'https': f'https://{random.choice(tst_success)}'}
                r = requests.get(row.url, proxies=proxy, headers=headers, timeout=2)
            except:
                try:
                    r = requests.get(row.url, headers=headers, timeout=2)
                except:
                    continue
        else:
            r = requests.get(row.url, headers=headers, timeout=10)
        if r.status_code == 429:
            solve_captcha()
            print('BLOCKED', counter)
        #             break
        prod_soup = BeautifulSoup(r.text, "html.parser")
        if counter % 50 == 0:
            print(f"{counter}/{df_urls.shape[0]} | {df_urls[(~df_urls.scrape_date.isnull()) & (df_urls.breadcrumbs != '[]')].shape[0]} / {df_urls.shape[0]} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ||| {row.url}")
        try:
            df_urls.loc[i, 'title'] = prod_soup.find(attrs={'class': 'page-title'}).text.replace('\n', '')
        except Exception as e:
            print_exception('title', e) if inspect_exceptions else ''
            df_urls.loc[i, 'title'] = ''

        try:
            df_urls.loc[i, 'price'] = re.sub('(\n)|([ ]+)', '', prod_soup.find(attrs={'class': 'price'}).text)
        except Exception as e:
            print_exception('price', e) if inspect_exceptions else ''
            df_urls.loc[i, 'price'] = 'Price is negotiable'

        try:
            df_urls.loc[i, 'phone'] = re.sub('(\n)|([ ]+)', '',
                                             prod_soup.find(attrs={'class': 'seller-phone-number'}).text)
        except Exception as e:
            print_exception('phone', e) if inspect_exceptions else ''
            df_urls.loc[i, 'phone'] = ''

        try:
            df_urls.loc[i, 'description'] = prod_soup.findAll('div', {'class': 'announcement-description'})[0].text
        except Exception as e:
            print_exception('description', e) if inspect_exceptions else ''
            df_urls.loc[i, 'description'] = ''

        try:
            df_urls.loc[i, 'contact_name'] = prod_soup.find('div', {'class': 'seller-contact-name'}).text
        except Exception as e:
            print_exception('contact_name', e) if inspect_exceptions else ''
            df_urls.loc[i, 'contact_name'] = ''

        try:
            df_urls.loc[i, 'contact_location'] = re.sub('(\n)|([ ]{2,})', '', prod_soup.find('div', {
                'class': 'seller-contact-location'}).text)
        except Exception as e:
            print_exception('contact_location', e) if inspect_exceptions else ''
            df_urls.loc[i, 'contact_location'] = ''

        try:
            df_urls.loc[i, 'article_id'] = re.sub('(\n)|([ ]+)', '',
                                                  prod_soup.find('li', {'class': 'announcement-id'}).text)
        except Exception as e:
            print_exception('article_id', e) if inspect_exceptions else ''
            df_urls.loc[i, 'article_id'] = ''

        try:
            df_urls.loc[i, 'image'] = str(
                [re.sub('ann_[0-9]', 'ann_3', re.findall("https://autoplius-img.dgn.lt/.*.jpg", tag['style'])[0]) for
                 tag in prod_soup.findAll('div', {'class': 'thumbnail'})])
        except Exception as e:
            print_exception('image', e) if inspect_exceptions else ''
            df_urls.loc[i, 'image'] = ''

        try:
            df_urls.loc[i, 'breadcrumbs'] = str(
                [re.sub('(\n)|([ ]+)', '', tag.text) for tag in prod_soup.findAll('li', {'class': 'crumb'})])
        except Exception as e:
            print_exception('breadcrumbs', e) if inspect_exceptions else ''
            df_urls.loc[i, 'breadcrumbs'] = ''

        df_urls.loc[i, 'scrape_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        try:
            params_label = [re.sub('(\n)|([ ]{2,})', '', tag.text) for tag in
                            prod_soup.findAll(attrs={'class': 'parameter-label'})]
            params_value = [re.sub('(\n)|([ ]{2,})', '', tag.text) for tag in
                            prod_soup.findAll(attrs={'class': 'parameter-value'})]
            params = list(zip(params_label, params_value))
            for p in params:
                df_urls.loc[i, p[0]] = p[1]

            # Extract VIN number if exists
            if len(re.findall('data:image/png;base64, .*"', r.text)):
                encoded_vin = re.sub('data:image/png;base64, ', '',
                                     re.findall('data:image/png;base64, .*"', r.text)[0][:-1])
                df_urls.loc[i, 'VIN number'] = decode_vin(encoded_vin)

        except Exception as e:
            error_log = error_log.append([{'params': e, 'url': row.url}])

        try:
            for section in prod_soup.findAll('div', {'class': 'section'}):
                if len(section.findAll('div', {'class': 'feature-row'})):
                    feature_header = re.sub('(\n)|([ ]{2,})', '', section.find('div', {'class': 'heading'}).text)
                    df_urls.loc[i, feature_header] = [section]

        except Exception as e:
            error_log = error_log.append([{'features': e, 'url': row.url}])
        try:
            df_urls.loc[i, 'memorized'] = \
            re.findall('[0-9]+', prod_soup.findAll('span', {'class': 'bookmark-ico'})[0].parent.text)[0]
        except Exception as e:
            print_exception('memorized', e) if inspect_exceptions else ''
            df_urls.loc[i, 'memorized'] = ''
        try:
            df_urls.loc[i, 'update_timestamp'] = \
            [tag.text for tag in prod_soup.findAll('span', {'class': 'bar-item'}) if 'Updated' in tag.text][0]
        except Exception as e:
            print_exception('update_timestamp', e) if inspect_exceptions else ''
            df_urls.loc[i, 'update_timestamp'] = ''

        counter += 1
        if counter % 1000 == 0:
            df_urls.to_csv('output.csv', index=False)
    except Exception as e:
        print(f'Failed: {row.url}', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        print(e)

driver.close()
df_urls.to_csv('output.csv', index=False)