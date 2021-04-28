import requests
from bs4 import BeautifulSoup


ARAM_WIKI_LINK = 'https://leagueoflegends.fandom.com/wiki/ARAM'
DATA_DRAGON_LINK = 'http://ddragon.leagueoflegends.com/cdn/11.9.1/data/en_GB/champion.json'
UGG_LINK = 'https://stats2.u.gg/lol/1.1/champion_ranking/world/11_8/normal_aram/overall/1.4.0.json'

WINRATE_COEFFICIENT = 1.12


def main():
    free_champions = get_free_champs()
    champs_dict = get_champs_dict()
    free_champs_avg_winrate = calc_free_avg_winrate(champs_dict, free_champions)
    good_champs = find_good_champions(champs_dict, free_champs_avg_winrate)
    print_results(good_champs, free_champs_avg_winrate)


def find_good_champions(champs_dict, free_champs_avg_winrate):
    """Find champions with winrates better than free roster average"""
    good_champs = []
    for champ in champs_dict.values():
        if champ['winrate'] > free_champs_avg_winrate * WINRATE_COEFFICIENT:
            good_champs.append(champ)
    return good_champs


def calc_free_avg_winrate(champs_dict, free_champions):
    free_champs_avg_winrate = 0
    for champ in champs_dict.values():
        if champ['name'] not in free_champions:
            continue
        free_champs_avg_winrate += champ['winrate']
    free_champs_avg_winrate /= len(free_champions)

    return free_champs_avg_winrate


def get_champs_dict():
    champs_dict = {}
    # Get champion info from Data Dragon to find champion IDs
    dd = requests.get(DATA_DRAGON_LINK).json()['data']
    for champ in dd:
        champs_dict[dd[champ]['key']] = {'name': champ}

    # Get winrate information from u.gg
    ugg = requests.get(UGG_LINK).json()[0]['none']
    for champ in ugg:
        champs_dict[champ[0]]['winrate'] = (champ[2] * 100) / champ[3]

    return champs_dict


def get_free_champs():
    # Get ARAM free roster from league wiki
    r = requests.get(ARAM_WIKI_LINK)
    soup = BeautifulSoup(r.text, 'html.parser')
    free_champions_soup = soup.find('dt', string='ARAM free roster').parent.next_sibling.next_sibling.ol

    free_champions = []

    for champion in free_champions_soup.find_all('li'):
        if "data-champion" in champion.span.attrs:
            champ_name = champion.span["data-champion"].replace(' ', '')
            if len(champ_name.split("'")) > 1:
                split_name = champ_name.split("'")  # splits twice but this happens rarely
                champ_name = split_name[0] + split_name[1].lower()  # there is no champion with two ' (yet)
            free_champions.append(champ_name)

    return free_champions


def print_results(good_champs, free_champs_avg_winrate):
    print(f'Average winrate of free ARAM champions is {free_champs_avg_winrate}')
    print(f'There are {len(good_champs)} champions with winrate {WINRATE_COEFFICIENT}x better than free roster average')
    for good_champ in good_champs:
        print(f'\t{good_champ["name"]}: {round(good_champ["winrate"], 3)}')


if __name__ == '__main__':
    main()
