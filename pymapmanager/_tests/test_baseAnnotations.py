import pytest

from pymapmanager.annotations import baseAnnotations

#init_test_cases = [
#	()
#]

def test_init_file():
	ba = baseAnnotations()
	assert ba
	