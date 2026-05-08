import pandas as pd


class BOMProcessor:
    def __init__(self, input_file):
        self.input_file = input_file
        self.bom_data = []

    def read_bom(self):
        import pandas as pd
        # Specify delimiter for semicolon-separated CSV
        self.bom_data = pd.read_csv(self.input_file, delimiter=';')

    def enrich_bom(self, tme_api, boards_qty = 1):
        self.bom_data['Link'] = self.bom_data.get('Link', pd.Series()).astype('string')
        self.bom_data['Symbol'] = self.bom_data.get('Symbol', pd.Series()).astype('string')
        print(self.bom_data.dtypes)
        # return
        required_columns = ['Reference', 'Obudowa', 'Operating Voltage', 'Wartość', 'Tolerance']
        actual_columns = self.bom_data.columns.tolist()
        # print("CSV Columns:", actual_columns)  # Debug print

        # Try to match columns ignoring case and spaces
        col_map = {}
        for req in required_columns:
            for actual in actual_columns:
                if req.lower().replace(" ", "") == actual.lower().replace(" ", ""):
                    col_map[req] = actual
                    break
            else:
                col_map[req] = None
        for index, row in self.bom_data.iterrows():
            #Check if row is empty
            if row.isnull().all():
                print(f"Skipping empty row {index}")
                continue

            ref = row[col_map['Reference']] if col_map['Reference'] else None
            obudowa = row[col_map['Obudowa']] if col_map['Obudowa'] else None
            operating_voltage = row[col_map['Operating Voltage']] if col_map['Operating Voltage'] else None
            wartosc = row[col_map['Wartość']] if col_map['Wartość'] else None
            tolerance = row[col_map['Tolerance']] if col_map['Tolerance'] else None
            qty = row.get('Qty', 1)  # Default to 1 if 'Ilość' column is missing
            # print(f"Processing row {index}: Ref={ref}, Obudowa={obudowa}, Voltage={operating_voltage}, Wartość={wartosc}, Tolerance={tolerance}, Qty={qty}")
            try:
                elements = tme_api.fetch_elements(ref, obudowa, float(operating_voltage), wartosc, tolerance, max_qty=qty*boards_qty)
            except Exception as e:
                print(f"fetch_elements failed for row {index}: {e}")
                elements = None

            if not elements:
                # Try GPT fallback
                row_str = ";".join(str(row.get(col, "")) for col in actual_columns)
                print(f"Trying GPT fallback for row {index}: {row_str}")
                try:
                    elements = tme_api.fetch_gpt(row_str, max_qty=qty*boards_qty)
                    # print(f"GPT query for row {index}: {elements}")
                    # Now use the GPT query as SearchPlain
                except Exception as e:
                    print(f"GPT fallback failed for row {index}: {e}")
                    elements = None

            if elements:
                cheapest_element = min(elements, key=lambda x: x['Cena 1 Sztuka'])
                self.bom_data.at[index, 'Link'] = cheapest_element['Link']
                self.bom_data.at[index, 'Symbol'] = cheapest_element['Symbol']
                self.bom_data.at[index, 'Cena 1 Sztuka'] = cheapest_element['Cena 1 Sztuka']

    def save_enriched_bom(self, output_file):
        # Save with semicolon delimiter to match input format
        self.bom_data.to_csv(output_file, index=False, sep=';', decimal=',')