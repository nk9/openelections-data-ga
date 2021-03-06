# python 3.5

from urllib.request import urlopen

from bs4 import BeautifulSoup
import psycopg2


def build_list(input_string):
    return_list = []
    for line in input_string:
        for item in line.split(' '):
            if len(item) > 0 and item != '\r':
                return_list.append(item.strip())
    return return_list


def create_connection(database_name):
    conn = psycopg2.connect(
        database=database_name,
        user='jreed',
        host='127.0.0.1',
        port='5432'
    )
    return conn


def extract_data(input_url):
    html = urlopen(input_url)
    bs = BeautifulSoup(html.read(), 'lxml')

    district_info = bs.findAll('h4')
    district_info = district_info[1].get_text()
    district_info = district_info.replace(
        "STATE REPRESENTATIVE -", ""
    )

    district_info = district_info.replace('DISTRICT', '')
    district_info = district_info.replace('DIST.', '')
    district_info = district_info.replace('P1', '')
    district_info = district_info.replace('P2', '')
    district_info = district_info.replace('P3', '')
    district_info = district_info.replace('P4', '')  
    district_number = district_info.replace(' ', '')

    county_vote_info = bs.find('pre')
    county_vote_info = county_vote_info.get_text()

    county_vote_info = county_vote_info.replace('VON EPPS', 'VON_EPPS')

    names = county_vote_info.split('\n')[5:6]
    parties = county_vote_info.split('\n')[6:7]
    totals = county_vote_info.split('\n')[7:8]
    percents = county_vote_info.split('\n')[8:9]
    counties = county_vote_info.split('\n')[10:-1]

    last_names = build_list(names)
    parties = build_list(parties)
    total_votes = build_list(totals)
    percent_votes = build_list(percents)

    county_votes = {}

    for line in counties:
        county_name = line[:14]
        votes = line[22:]
        split_votes = build_list([votes])
        county_votes[county_name.strip()] = split_votes

    for counter, name in enumerate(last_names):
        data = {
            'last_name': name,
            'party': parties[counter],
            'district_number': district_number,
            'total_votes': total_votes[counter],
            'percent_votes': percent_votes[counter],

        }
        for key, value in county_votes.items():
            data['county_name'] = key
            data['county_votes'] = value[counter].replace(' ', '').replace(',', '')

            cur.execute(SQL, data)


SQL = """
INSERT INTO ga_general_state_house_20021105_county_votes
    (last_name, party, total_votes,
        percent_votes, district_number,
        county_name, county_votes)
    VALUES (%(last_name)s, %(party)s, %(total_votes)s,
        %(percent_votes)s, %(district_number)s,
        %(county_name)s, %(county_votes)s);
"""

conn = create_connection('dev')
cur = conn.cursor()

base_url = "http://sos.ga.gov/elections/election_results/2002_1105/"

url = "http://sos.ga.gov/elections/election_results/2002_1105/housemenu.htm"

html = urlopen(url)
bs_links = BeautifulSoup(html.read(), 'lxml')

links = bs_links.findAll('a')
for link in links:
    if 'href' in link.attrs:
        extract_data(base_url + link.attrs['href'])
        conn.commit()

conn.close()
