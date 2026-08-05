import pytest
from src.backend.macro.nrb_extractors import normalize
from src.backend.macro.validation import validate
from src.backend.macro.exceptions import NRBExtractionError

def test_normalized_label_matching():
    assert normalize(" Housing  &  Utilities—CPI ")=="housing utilities-cpi"

def test_invalid_parser_value_is_rejected():
    values={"cpi_inflation":522,"lending_rate":8,"deposit_rate":4,"credit_growth":7,"remittance_growth":12}
    with pytest.raises(NRBExtractionError): validate(values)

def test_partial_report_is_rejected():
    with pytest.raises(NRBExtractionError): validate({"cpi_inflation":5})
