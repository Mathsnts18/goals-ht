import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO
import os

class Dados:
    
    def __init__(self, rodada):
        self.round = rodada
        self.url_goals = 'https://www.soccerstats.com/trends.asp?league=england'
        self.url_gameweek = f'https://www.soccerstats.com/results.asp?league=england&pmtype=round{rodada}'
        self.df_goals_ht_home, self.df_goals_ht_away, self.df_goals_ht = self.extract_goals_ht()
        self.df_gameweek = self.extract_gameweek()
        self.raw_data()
        self.processed_df_goals_ht_home, self.processed_df_goals_ht_away, self.processed_df_goals_ht, self.processed_df_gameweek = self.transform_raw_data()
        self.df = self.create_gameweek_ht()
        self.load()



    def extract_goals_ht(self):

        print('Extraindo tabelas HTML...')

        response = requests.get(self.url_goals)

        soup = BeautifulSoup(response.text, 'html.parser')

        # Estatisticas de gols HT do mandante
        h3_goals_ht_home = soup.find("h3", string="Match goals stats at half-time (at home)")
        table_home_ht_goals = h3_goals_ht_home.next_sibling.next_sibling
        table_home_ht_goals_io = StringIO(str(table_home_ht_goals))
        df_goals_ht_home = pd.read_html(table_home_ht_goals_io, header=0, skiprows=[1,22,23])[0]

        # Estatisticas de gols HT do visitante
        h3_goals_ht_away = soup.find("h3", string="Match goals stats at half-time (away)")
        table_away_ht_goals = h3_goals_ht_away.next_sibling.next_sibling
        table_away_ht_goals_io = StringIO(str(table_away_ht_goals))
        df_goals_ht_away = pd.read_html(table_away_ht_goals_io, header=0, skiprows=[1,22,23])[0]

        # Estatisticas de gols HT do campeonato
        h3_goals_ht = soup.find("h3", string="Match goals stats at half-time")
        table_ht_goals = h3_goals_ht.next_sibling.next_sibling
        table_ht_goals_io = StringIO(str(table_ht_goals))
        df_goals_ht = pd.read_html(table_ht_goals_io, header=0, skiprows=[1,22])[0]

        print('Sucesso!')

        return df_goals_ht_home, df_goals_ht_away, df_goals_ht
    
    def extract_gameweek(self):

        print('')
        print('Extraindo tabela de jogos da semana...')

        response = requests.get(self.url_gameweek)

        soup = BeautifulSoup(response.text, 'html.parser')
        
        h2_gameweek = soup.find("h2", string=f"Gameweek {self.round}")
        table_gameweek = h2_gameweek.next_sibling
        table_gameweek_io = StringIO(str(table_gameweek))
        df_gameweek = pd.read_html(table_gameweek_io, skiprows=[0,1])[0]

        print('Sucesso!')

        return df_gameweek
    
    def raw_data(self):
        
        print('')
        print('Salvando tabelas...')

        os.makedirs('./data/raw/csv', exist_ok=True)
        os.makedirs('./data/raw/xlsx', exist_ok=True)

        caminho = './data/raw/'

        self.df_gameweek.to_csv(f'{caminho}csv/rodada{self.round}.csv', index=False)
        
        self.df_goals_ht_home.to_csv(f'{caminho}csv/gols_ht_mandante{self.round - 1}.csv', index=False)

        self.df_goals_ht_away.to_csv(f'{caminho}csv/gols_ht_visitante{self.round - 1}.csv', index=False)

        self.df_goals_ht.to_csv(f'{caminho}csv/gols_ht{self.round - 1}.csv', index=False)
        

        with pd.ExcelWriter(f'{caminho}xlsx/rodada{self.round}.xlsx') as writer:  
            
            self.df_gameweek.to_excel(writer, sheet_name=f'PL_rodada{self.round}', index=False)
            self.df_goals_ht_home.to_excel(writer, sheet_name=f'gols_ht_mandante{self.round - 1}', index=False)
            self.df_goals_ht_away.to_excel(writer, sheet_name=f'gols_ht_visitante{self.round - 1}', index=False)
            self.df_goals_ht.to_excel(writer, sheet_name=f'gols_ht{self.round - 1}', index=False)            

        print('Sucesso!')

    def transform_raw_data(self):
        
        print('')
        print('Transformando os dados...')

        self.processed_df_goals_ht_away = self.df_goals_ht_away.copy()
        self.processed_df_goals_ht_away = self.processed_df_goals_ht_away[['Away matches of...', '0.5+']]
        self.processed_df_goals_ht_away['0.5+'] = self.processed_df_goals_ht_away['0.5+'].str.replace('%', '').astype(float)

        self.processed_df_goals_ht_home = self.df_goals_ht_home.copy()
        self.processed_df_goals_ht_home = self.processed_df_goals_ht_home[['Home matches of...', '0.5+']]
        self.processed_df_goals_ht_home['0.5+'] = self.processed_df_goals_ht_home['0.5+'].str.replace('%', '').astype(float)

        self.processed_df_goals_ht = self.df_goals_ht.copy()
        self.processed_df_goals_ht = self.processed_df_goals_ht[['Matches of...', '0.5+']]
        self.processed_df_goals_ht['0.5+'] = self.processed_df_goals_ht['0.5+'].str.replace('%', '').astype(float)

        self.processed_df_gameweek = self.df_gameweek.copy()
        self.processed_df_gameweek = self.processed_df_gameweek[[0,1,2,3]]
        self.processed_df_gameweek.dropna(inplace= True)
        self.processed_df_gameweek.columns = ['day', 'home', 'hour', 'away']

        print('Sucesso!')

        return self.processed_df_goals_ht_home, self.processed_df_goals_ht_away, self.processed_df_goals_ht, self.processed_df_gameweek

    def create_gameweek_ht(self):

        print('')
        print('Criando nova tabela...')

        df = self.processed_df_gameweek.copy()
        df = df.merge(self.processed_df_goals_ht_home, left_on='home', right_on= 'Home matches of...', how='left').rename(columns={'0.5+': 'home_0.5+%'})
        df = df.merge(self.processed_df_goals_ht_away, left_on='away', right_on= 'Away matches of...', how='left').rename(columns={'0.5+': 'away_0.5+%'})
        df.drop(['Home matches of...', 'Away matches of...'], axis=1, inplace=True)
        df = df.loc[df['hour'] != 'pp.']

        df['avg_0.5+%'] = (df['home_0.5+%'] + df['away_0.5+%'])/2
        df['acima_da_media?'] = df['avg_0.5+%'].apply(lambda x: 1 if x > self.processed_df_goals_ht[self.processed_df_goals_ht['Matches of...'] == 'League average']['0.5+'].values else 0)

        print('Sucesso!')

        return df

    def load(self):

        print('')
        print('Salvando nova tabela...')

        os.makedirs('./data/processed/csv', exist_ok=True)
        os.makedirs('./data/processed/xlsx', exist_ok=True)

        caminho = f'./data/processed/'

        self.df.to_csv(f'{caminho}csv/pl_rodada{self.round}.csv', index=False)
        self.df.to_excel(f'{caminho}xlsx/pl_rodada{self.round}.xlsx', index=False)

        print(f'Tabela .CSV criada em: {caminho}csv/pl_rodada{self.round}.csv')
        print(f'Tabela .XLSX criada em: {caminho}xlsx/pl_rodada{self.round}.xlsx')

rodada33 = Dados(33)