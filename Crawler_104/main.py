import time
import random
import re
import os
from urllib.parse import quote
import argparse
from datetime import datetime
import sys

import requests
import pandas as pd
from bs4 import BeautifulSoup as BS

from setting import JOB_KEY
from setting import SAVE_PATH


def search_company_from_key(comp_key):
    u = f'https://www.104.com.tw/jb/104i/custlist/list?keyword={quote(comp_key)}'
    r = requests.get(u)
    r.encoding = 'utf-8'
    s = BS(r.text, 'lxml')
    all_comp = s.find_all('div', {'class': 'm-box w-resultBox'})

    company_search_list = []
    print('搜尋公司關鍵字：', comp_key)
    for idx, comp in enumerate(all_comp[:15]):
        comp_dic = {}
        comp_name = comp.find('a', {'class': 'a5'}).get('title')
        job_num_tag = comp.find('span', {'class': 'c01'})
        if job_num_tag:
            job_num = int(job_num_tag.text)
        else:
            job_num = 0
        comp_code = re.search(r'.*c=(.*)$', comp.find('a', {'class': 'a5'}).get('href')).group(1)
        comp_dic['company_name'] = comp_name
        comp_dic['company_code'] = comp_code
        comp_dic['job_num'] = job_num
        company_search_list.append(comp_dic)
    return company_search_list


def get_target_company(company_search_list):
    print('======相關公司搜尋如下：' + '=' * 30)
    for idx, company in enumerate(company_search_list):
        comp_name = company.get('company_name')
        job_num = company.get('job_num')
        print(f'  {idx}：{comp_name} [工作機會：{job_num}]')
    while True:
        try:
            correct_index = int(input('\n======請輸入正確公司名稱代碼(最前面數字)' + '=' * 20 + '\n'))
            break
        except ValueError:
            print('Oops...請輸入數字(公司名稱最前面的數字)')
    target_company = company_search_list[correct_index]
    return [target_company]


def get_target_company_from_id(comp_id):
    url = f'https://www.104.com.tw/jb/104i/joblist/list?c={comp_id}'
    res = requests.get(url)
    res.encoding = 'utf-8'
    soup = BS(res.text, 'lxml')
    company_name = soup.find('div', {'class': 'w-condition show'}).find('a').text
    comp_dic = dict()
    comp_dic['company_name'] = company_name
    comp_dic['company_code'] = comp_id
    return [comp_dic]


def check_break(job_post_date, end_date):
    # print(datetime.strptime(job_post_date, '%Y-%m-%d'))
    # print(datetime.strptime(end_date, '%Y-%m-%d'))
    return datetime.strptime(job_post_date, '%Y-%m-%d') < datetime.strptime(end_date, '%Y-%m-%d')


def search_job(target_company, job_key, end_date):
    company_name = target_company.get('company_name')
    print(f'Searching for {company_name}...')
    c_code = target_company.get('company_code')
    url = f'https://www.104.com.tw/jb/104i/joblist/list?order=11%2C0&c={c_code}'
    job_list = []
    break_point = False
    while not break_point:
        res = requests.get(url)
        res.encoding = 'utf-8'
        soup = BS(res.text, 'lxml')

        results = soup.find_all('div', {'class': 'm-box w-resultBox'})
        for result in results:
            job_post_date = result.find('span', {'itemprop': 'datePosted'}).text

            if end_date:
                if check_break(job_post_date, end_date):
                    break_point = True
                    break

            job_title = result.find('a', {'class': 'a4'}).get('title')
            job_url = 'https://www.104.com.tw' + result.find('a', {'class': 'a4'}).get('href')
            job_place = result.find('address').text.strip()
            job_des = result.find('div', {'itemprop': 'description'}).text.strip()
            job_salary = result.find('span', {'itemprop': 'price'}).text

            search_result = re.findall('|'.join(job_key).lower(), (job_title + ' ' + job_des).lower())
            if search_result:
                print(job_title, job_place, list(dict.fromkeys(search_result)))
                job_list.append({'職位名稱': job_title,
                                 '工作地點': job_place,
                                 '薪資': job_salary,
                                 '更新時間': job_post_date,
                                 '關鍵字': list(dict.fromkeys(search_result)),
                                 '網址': job_url})

        next_page_btn = soup.find('div', {'class': 'w-pager'}).find('a', text=re.compile('下一頁'))
        if next_page_btn:
            url = 'https://www.104.com.tw' + next_page_btn.get('href')
            time.sleep(random.randint(5, 8))
        else:
            break_point = True
    return job_list


def get_file_save_path(company):
    filename = company.get('company_name') + '_' + '_'.join(JOB_KEY) + '.xlsx'
    filepath = os.path.join(SAVE_PATH, filename)
    return filepath


def save_file(target_company, target_job_list):
    if not len(target_job_list) == 0:
        df = pd.DataFrame(target_job_list)
        file_save_path = get_file_save_path(target_company)
        df.to_excel(file_save_path, index=False)
        print('File Saved！')
    else:
        print('Not Found')


def get_id_list_from_file():
    print('Loading id_list file')
    id_list = []
    with open('id_list.txt', 'r') as f:
        for line in f:
            id_list.append(line.replace('\n', ''))
    print('Total company：', len(id_list))
    return id_list


def check_input():
    if not JOB_KEY or not SAVE_PATH:
        print('Please set the JOB_KEY and SAVE_PATH variables in setting.py')
        sys.exit(0)


if __name__ == '__main__':
    check_input()

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-k', '--compKey')
    group.add_argument('-i', '--compId')
    group.add_argument('-f', '--compIdFile', action='store_true')
    parser.add_argument('-d', '--date')
    args = parser.parse_args()
    comp_key = args.compKey
    comp_code = args.compId
    compIdFile = args.compIdFile
    end_date = args.date

    if comp_key:
        company_search_list = search_company_from_key(comp_key)
        target_company_list = get_target_company(company_search_list)
    elif comp_code:
        target_company_list = get_target_company_from_id(comp_code)
    elif compIdFile:
        id_list = get_id_list_from_file()
        target_company_list = []
        for id_ in id_list:
            target_company_list += get_target_company_from_id(id_)
            time.sleep(random.randint(2, 4))

    for target_company in target_company_list:
        target_job_list = search_job(target_company, JOB_KEY, end_date)
        save_file(target_company, target_job_list)
