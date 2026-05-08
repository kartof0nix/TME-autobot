import pytest
from src.get_value import get_value
from src.tme_api import inch_to_mm, mm_to_inch

def test_getvalue():
    EPS = 1e-14

    assert abs(get_value("capacitor 10uF") - 10e-6) < EPS
    assert abs(get_value("10k") - 1e4) < EPS
    assert abs(get_value("resistor 10k 5%") - 1e4) < EPS
    assert abs(get_value("resistor 10k 5% 0.25W") - 1e4) < EPS
    assert abs(get_value("10k 5% 0.25W 0603") - 1e4) < EPS
    assert abs(get_value("100kΩ 5% 0.25W 0603") - 100e3) < EPS
    assert abs(get_value("resistor 10k 5% 0.25W 0603 SMD") - 1e4) < EPS
    assert abs(get_value("resistor 10k 5% 0.25W 0603 SMD 1/4W") - 1e4) < EPS
    assert abs(get_value("resistor 10k 5% 0.25W 0603 SMD 1/4W 5%") - 1e4) < EPS
    assert abs(get_value("resistor 100R 5% 0.25W 0603 SMD 1/4W 5% 10%") - 100) < EPS
    assert abs(get_value("0.2k 5% 0.25W 0603 SMD 1/4W 5% 10%") - 200) < EPS
    assert abs(get_value("100nF 5% 0.25W 0603 SMD 10R 1/4W 5% 10%") - 100e-9) < EPS
    assert abs(get_value("10uF 5% 0.25W 0603 SMD 100R 1/4W 5% 10%") - 10e-6) < EPS
    assert abs(get_value("capacitor 1uF 5% 0.25W 0603 SMD 100R 1/4W 5% 10%") - 1e-6) < EPS
    assert abs(get_value("Resistor: thick film; SMD; 0805; 1kΩ; 0.125W; ±5%; 150V; -55÷125°C") - 1e3) < EPS
    assert abs(get_value("Resistor: thick film; SMD; 0805; 4k7; 0.125W; ±5%; 150V; -55÷125°C") - 4.7e3) < EPS

@pytest.mark.parametrize("inch,mm", [
    ("1005", "0402"),
    ("0201", "0603"),
    ("0402", "1005"),
    ("0603", "1608"),
    ("0805", "2012"),
    ("1008", "2520"),
    ("1206", "3216"),
    ("1210", "3225"),
    ("1411", "3528"),
    ("1812", "4532"),
    ("2010", "5025"),
    ("2012", "5032"),
    ("2312", "6032"),
    ("2512", "6332"),
    ("9999", "9999"),  # unknown mapping returns input
])
def test_inch_to_mm_and_mm_to_inch(inch, mm):
    assert inch_to_mm(inch) == mm
    assert mm_to_inch(mm) == inch