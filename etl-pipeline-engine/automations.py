import os
from pathlib import Path

import pandas as pd


def load_csv(path):
    return pd.read_csv(path)


def clean_data(df):
    df = df.copy()
    df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
    df = df.dropna(how='all')
    return df


def summarize_sales(df):
    if 'price' in df.columns and 'quantity' in df.columns:
        df['total'] = df['price'] * df['quantity']
        summary = df.groupby('product').agg({
            'quantity': 'sum',
            'total': 'sum'
        }).reset_index()
        return summary
    return pd.DataFrame()


def export_to_excel(df, output_path):
    df.to_excel(output_path, index=False)


if __name__ == '__main__':
    source_path = Path('input/sales.csv')
    output_path = Path('output/sales_report.xlsx')

    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = load_csv(source_path)
    df = clean_data(df)
    report = summarize_sales(df)
    export_to_excel(report, output_path)
    print(f'Relatório gerado em: {output_path}')
