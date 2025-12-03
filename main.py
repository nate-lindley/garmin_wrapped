import pandas as pd
import matplotlib.pyplot as plt

def main():
    df = pd.read_csv('data/Activities.csv')
    df_2025 = df[df['Date'].str.contains('2025')].copy()
    df_2025['Distance'] = df_2025['Distance'].str.replace(',', '')
    df_2025['Distance'] = df_2025['Distance'].str.replace('--', '0')
    df_2025['Distance'] = df_2025['Distance'].astype(float)

    # df_2025['Time_td'] = pd.to_timedelta(df_2025['Time'])