import time
import random
import re
import os
from urllib.parse import quote
import argparse

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
    return target_company


def get_target_company_from_id(comp_id):
    url = f'https://www.104.com.tw/jb/104i/joblist/list?c={comp_id}'
    res = requests.get(url)
    res.encoding = 'utf-8'
    soup = BS(res.text, 'lxml')
    company_name = soup.find('div', {'class': 'w-condition show'}).find('a').text
    comp_dic = dict()
    comp_dic['company_name'] = company_name
    comp_dic['company_code'] = comp_id
    return comp_dic


def search_job(target_company, job_key):
    print('Searching...')
    c_code = target_company.get('company_code')
    url = f'https://www.104.com.tw/jb/104i/joblist/list?c={c_code}'
    job_list = []
    while True:
        res = requests.get(url)
        res.encoding = 'utf-8'
        soup = BS(res.text, 'lxml')

        results = soup.find_all('div', {'class': 'm-box w-resultBox'})
        for result in results:
            job_title = result.find('a', {'class': 'a4'}).get('title')
            job_url = 'https://www.104.com.tw' + result.find('a', {'class': 'a4'}).get('href')
            job_place = result.find('address').text.strip()
            job_des = result.find('div', {'itemprop': 'description'}).text.strip()
            job_post_date = result.find('span', {'itemprop': 'datePosted'}).text
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
            break
    return job_list


def get_file_save_path(company):
    filename = company.get('company_name') + '_' + '_'.join(JOB_KEY) + '.xlsx'
    filepath = os.path.join(SAVE_PATH, filename)
    return filepath


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-k', '--compKey')
    group.add_argument('-i', '--compId')
    args = parser.parse_args()
    comp_key = args.compKey
    comp_code = args.compId

    if comp_key:
        company_search_list = search_company_from_key(comp_key)
        target_company = get_target_company(company_search_list)
    else:
        target_company = get_target_company_from_id(comp_code)

    target_job_list = search_job(target_company, JOB_KEY)
    if not len(target_job_list) == 0:
        df = pd.DataFrame(target_job_list)
        file_save_path = get_file_save_path(target_company)
        df.to_excel(file_save_path, index=False)
        print('File Saved！')
    else:
        print('Not Found')

