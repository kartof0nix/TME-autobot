# TME BOM Optimizer

This project automates the process of assigning the cheapest TME elements available based on a CSV BOM file. It utilizes the TME API to browse the TME e-shop and filter components based on specific criteria.

## Project Structure

```
tme-bom-optimizer
├── src
│   ├── main.py            # Entry point of the application
│   ├── tme_api.py         # Handles interactions with the TME API
│   ├── bom_processor.py    # Processes the input CSV BOM file
│   └── utils.py           # Utility functions for CSV reading/writing
├── requirements.txt       # Project dependencies
├── README.md              # Project documentation
└── tests
    ├── test_bom_processor.py # Unit tests for BOMProcessor
    └── test_tme_api.py      # Unit tests for TMEApi
```

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   cd tme-bom-optimizer
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Prepare your CSV BOM file with the necessary columns: Obudowa, Operating Voltage, Wartość, and Tolerance.

2. Run the application:
   ```
   python src/main.py <input_bom_file.csv> <output_bom_file.csv>
   ```

   Replace `<input_bom_file.csv>` with the path to your input BOM file and `<output_bom_file.csv>` with the desired path for the output file.

## TME API

The project interacts with the TME API to fetch component details. Ensure you have the necessary API access and credentials if required.

## Testing

To run the tests, use the following command:
```
pytest tests/
```

This will execute all unit tests in the `tests` directory to ensure the functionality of the BOMProcessor and TMEApi classes.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.