import requests
from bs4 import BeautifulSoup


ARAM_WIKI_LINK = 'https://leagueoflegends.fandom.com/wiki/ARAM'
DATA_DRAGON_LINK = 'http://ddragon.leagueoflegends.com/cdn/11.9.1/data/en_GB/champion.json'
UGG_LINK = 'https://stats2.u.gg/lol/1.1/champion_ranking/world/$PATCH/normal_aram/overall/1.4.0.json'

PATCHES = ['11_9', '11_8', '11_7']  # winrates calculated of unweighted avg winrates per patch

WINRATE_COEFFICIENT = 1.12  # winrate must be this higher that free avg to consider it


def main():
    free_champions = get_free_champs()
    champs_dict = get_champs_dict()
    free_champs_avg_winrate = calc_free_avg_winrate(champs_dict, free_champions)
    good_champs = find_good_champions(champs_dict, free_champs_avg_winrate, free_champions)
    print_results(good_champs, free_champs_avg_winrate)


def find_good_champions(champs_dict, free_champs_avg_winrate, free_champions):
    """Find (non-free) champions with winrates better than free roster average"""
    good_champs = []
    for champ in champs_dict.values():
        if not champ['winrate']:
            continue
        if champ['winrate'] > free_champs_avg_winrate * WINRATE_COEFFICIENT and champ['name'] not in free_champions:
            good_champs.append(champ)
    return good_champs


def calc_free_avg_winrate(champs_dict, free_champions):
    """Calculates average winrate of free champions"""
    free_champs_avg_winrate = 0
    for champ in champs_dict.values():
        if champ['name'] not in free_champions:
            continue
        free_champs_avg_winrate += champ['winrate']
    free_champs_avg_winrate /= len(free_champions)

    return free_champs_avg_winrate


def get_champs_dict():
    """Collects champion winrates per patch"""
    champs_dict = {}
    # Get champion info from Data Dragon to find champion IDs
    dd = requests.get(DATA_DRAGON_LINK).json()['data']
    for champ in dd:
        champs_dict[dd[champ]['key']] = {'name': champ}

    for patch in PATCHES:
        # Get winrate information from u.gg
        ugg = requests.get(UGG_LINK.replace('$PATCH', patch)).json()[0]['none']
        for champ in ugg:
            champs_dict[champ[0]][patch] = (champ[2] * 100) / champ[3]

    for champ in champs_dict.values():
        winrate = 0
        patches_active = 0
        for patch in PATCHES:
            if patch not in champ:  # New champions won't have winrate in older patches
                continue
            patches_active += 1
            winrate += champ[patch]
        champ['winrate'] = winrate / patches_active

    return champs_dict


def get_free_champs():
    """Scrapes loeague wiki and finds the ARAM free roster"""
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
