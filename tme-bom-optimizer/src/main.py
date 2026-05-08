import time
import pandas as pd
from .tme_api import TMEApi
from .bom_processor import BOMProcessor
from secrets import TME_TOKEN, TME_KEY, OPENAI_KEY
def main():
    # Read the input CSV BOM file
    input_file = 'input_bom.csv'  # Use  actual input file = input_bom.csv, not Elementy_BOM_auto.csv
    output_file = 'output_bom_' + time.strftime("%M%S") + '.csv'  # Output file
    boards = 10

    # Initialize the TME API and BOM Processor
    tme_api = TMEApi(TME_TOKEN, TME_KEY, OPENAI_KEY)
    bom_processor = BOMProcessor(input_file)

    # Process the BOM file
    bom_processor.read_bom()
    bom_processor.enrich_bom(tme_api, boards_qty=boards)
    bom_processor.save_enriched_bom(output_file)

if __name__ == '__main__':
    main()