from pyprnt import prnt
import requests
import pandas as pd
from bs4 import BeautifulSoup

def get_theater_code_from_name(theater_data, theater_name:str):
    """get theater code from theater name
    Args:
        theater_data (pd.DataFrame): dataframe containing theater data
        theater_name (str): theater name, requires exact match ex) 용산아이파크몰
    """
    theater_code = theater_data[theater_data['name'] == theater_name]['code'].values[0]
    
    return theater_code

def get_url_with_query(theater_code:str, date:str):
    """get url with query
    Args:
        theater_code (str): theater code, ex) 0013
        date (str): date, follows format 'YYYYMMDD'
    
    Returns:
        url (str): url with query
    """
    base_url = 'http://www.cgv.co.kr/common/showtimes/iframeTheater.aspx?theatercode={}&date={}'
    return base_url.format(theater_code, date)
    
def get_soup(url:str):
    """get soup from url
    Args:
        url (str): url
    
    Returns:
        soup (BeautifulSoup): BeautifulSoup object
    """
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15"}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')
    return soup

def clean_text(text:str):
    """remove whitespace, newline, tab, etc.
    Args:
        text (str): text

    Returns:
        text (str): cleaned text
    """
    text = text.replace('\n', '')
    text = text.replace('  ', '')
    text = text.replace('\r', '')
    text = text.replace('총', '')
    return text

def crawl_movie_info(soup):
    """crawl movie info from soup
    
    Args:
        soup (BeautifulSoup): BeautifulSoup object
    
    Returns:
        data_dict_list (list): list of dicts containing movie info
    """
    movies = soup.select('body > div > div.sect-showtimes > ul > li')

    data_dict_list = []
    for each_movie in movies:
        title = each_movie.select_one('div.info-movie > a > strong').text.strip()
        data_dict = {}

        # Get movie hall information
        hall_info = each_movie.select('div.type-hall > div.info-hall > ul')
        hall_info_list = []
        for each_hall_info in hall_info:
            each_hall_info_dict = {}
            each_hall_info_dict['hall_type'] = clean_text(each_hall_info.select('li')[0].text)
            each_hall_info_dict['hall_name'] = clean_text(each_hall_info.select('li')[1].text)
            each_hall_info_dict['hall_total_seat'] = clean_text(each_hall_info.select('li')[2].text)

            hall_info_list.append(each_hall_info_dict)

        # Get movie time information
        timetable_info = each_movie.select('div.type-hall > div.info-timetable > ul')
        timetable_info_list = []
        for each_timetable_info in timetable_info:
            each_time_list = []
            for each_time in each_timetable_info.select('li'):
                text = each_time.text.replace('잔여좌석', '')
                try:
                    link = 'https://www.cgv.co.kr' + each_time.find('a')['href']
                except:
                    link = None # 매진의 경우 link가 없음, 예외처리

                each_time_list.append([text[0:5], text[5:], link]) # 시간, 잔여좌석, link
            timetable_info_list.append(each_time_list)

        # Build data_dict
        data_dict['movie_title'] = title
        data_dict['hall_list'] = hall_info_list
        assert len(hall_info_list) == len(timetable_info_list)
        for i in range(len(hall_info_list)):
            data_dict['hall_list'][i]['timetable'] = timetable_info_list[i]

        data_dict_list.append(data_dict)
    
    return data_dict_list

def load_theater_data():
    """load theater data from csv file

    Returns:
        theater_data (pd.DataFrame): dataframe containing theater data
    """

    df = pd.read_csv('theater_data.csv', converters={i: str for i in range(0, 200)}, encoding='utf-8')
    return df

def get_movie_info(theater_name:str, date:str):
    """get movie info from cgv
    Args:
        theater_name (str): theater name, requires exact match ex) 용산아이파크몰
        date (str): date, follows format 'YYYYMMDD'
    
    Returns:
        data_dict_list (list): list of dicts containing movie info
    """

    theater_data = load_theater_data()
    theater_code = get_theater_code_from_name(theater_data, theater_name)
    url = get_url_with_query(theater_code, date)
    soup = get_soup(url)
    data_dict_list = crawl_movie_info(soup)

    return data_dict_list

if __name__ == '__main__':
    theater_name = input('영화관 이름을 입력하세요: ')
    date = input('날짜를 입력하세요(ex: 20220101): ')

    data_dict_list = get_movie_info(theater_name, date)

    prnt(data_dict_list)