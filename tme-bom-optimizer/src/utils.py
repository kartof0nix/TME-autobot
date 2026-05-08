def read_csv(file_path):
    import pandas as pd
    return pd.read_csv(file_path)

def write_csv(dataframe, file_path):
    dataframe.to_csv(file_path, index=False)

def format_currency(value):
    return f"{value:.2f} PLN" if value is not None else None

def extract_columns(dataframe, columns):
    return dataframe[columns] if all(col in dataframe.columns for col in columns) else None