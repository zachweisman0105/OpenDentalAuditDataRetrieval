"""Unit tests for OpenDental response models.

Tests generic data models that accept flexible API response data.
"""

import pytest
from pydantic import SecretStr

from opendental_cli.models.credential import APICredential
from opendental_cli.models.opendental import (
    AllergiesResponse,
    DiseasesResponse,
    MedicationsResponse,
    PatientNotesResponse,
    ProcedureLogsResponse,
    VitalSignsResponse,
)


class TestProcedureLogsResponse:
    """Test ProcedureLogsResponse model."""

    def test_valid_procedure_logs_data(self):
        """Test creating model with valid procedure logs data."""
        response = ProcedureLogsResponse(data=[{"ProcCode": "D0220", "Descript": "X-ray", "ProcFee": "31.00"}])
        assert isinstance(response.data, list)
        assert len(response.data) == 1
        assert response.data[0]["ProcCode"] == "D0220"

    def test_empty_data(self):
        """Test creating model with empty data."""
        response = ProcedureLogsResponse(data=[])
        assert isinstance(response.data, list)
        assert len(response.data) == 0

    def test_default(self):
        """Test creating model without parameters uses default."""
        response = ProcedureLogsResponse()
        assert isinstance(response.data, list)
        assert response.data == []


class TestAllergiesResponse:
    """Test AllergiesResponse model."""

    def test_valid_allergies_data(self):
        """Test creating model with valid allergies data."""
        response = AllergiesResponse(data=[{"AllergyNum": 2961, "defDescription": "Peanuts", "Reaction": "Hives"}])
        assert isinstance(response.data, list)
        assert len(response.data) == 1
        assert response.data[0]["defDescription"] == "Peanuts"

    def test_empty_data(self):
        """Test creating model with empty data."""
        response = AllergiesResponse(data=[])
        assert isinstance(response.data, list)
        assert len(response.data) == 0

    def test_default(self):
        """Test creating model without parameters uses default."""
        response = AllergiesResponse()
        assert isinstance(response.data, list)
        assert response.data == []


class TestMedicationsResponse:
    """Test MedicationsResponse model."""

    def test_valid_medications_data(self):
        """Test creating model with valid medications data."""
        response = MedicationsResponse(data=[{"MedicationPatNum": 6537, "medName": "Antibiotic", "PatNote": "Take daily"}])
        assert isinstance(response.data, list)
        assert len(response.data) == 1
        assert response.data[0]["medName"] == "Antibiotic"

    def test_empty_data(self):
        """Test creating model with empty data."""
        response = MedicationsResponse(data=[])
        assert isinstance(response.data, list)
        assert len(response.data) == 0

    def test_default(self):
        """Test creating model without parameters uses default."""
        response = MedicationsResponse()
        assert isinstance(response.data, list)
        assert response.data == []


class TestDiseasesResponse:
    """Test DiseasesResponse model."""

    def test_valid_diseases_data(self):
        """Test creating model with valid diseases data."""
        response = DiseasesResponse(data=[{"DiseaseNum": 4811, "diseaseDefName": "Anemic", "ProbStatus": "Active"}])
        assert isinstance(response.data, list)
        assert len(response.data) == 1
        assert response.data[0]["diseaseDefName"] == "Anemic"

    def test_empty_data(self):
        """Test creating model with empty data."""
        response = DiseasesResponse(data=[])
        assert isinstance(response.data, list)
        assert len(response.data) == 0

    def test_default(self):
        """Test creating model without parameters uses default."""
        response = DiseasesResponse()
        assert isinstance(response.data, list)
        assert response.data == []


class TestPatientNotesResponse:
    """Test PatientNotesResponse model."""

    def test_valid_patient_notes_data(self):
        """Test creating model with valid patient notes data."""
        response = PatientNotesResponse(data={"PatNum": 39689, "MedicalComp": "Medical History", "Treatment": ""})
        assert isinstance(response.data, dict)
        assert response.data["PatNum"] == 39689
        assert response.data["MedicalComp"] == "Medical History"

    def test_empty_data(self):
        """Test creating model with empty data."""
        response = PatientNotesResponse(data={})
        assert isinstance(response.data, dict)
        assert len(response.data) == 0

    def test_default(self):
        """Test creating model without parameters uses default."""
        response = PatientNotesResponse()
        assert isinstance(response.data, dict)
        assert response.data == {}


class TestVitalSignsResponse:
    """Test VitalSignsResponse model."""

    def test_valid_vital_signs_data(self):
        """Test creating model with valid vital signs data."""
        response = VitalSignsResponse(data=[{"DateTaken": "2025-11-11", "Pulse": 122, "BP": "123/321", "Height": 231.0, "Weight": 98.0}])
        assert isinstance(response.data, list)
        assert len(response.data) == 1
        assert response.data[0]["Pulse"] == 122

    def test_empty_data(self):
        """Test creating model with empty data."""
        response = VitalSignsResponse(data=[])
        assert isinstance(response.data, list)
        assert len(response.data) == 0

    def test_default(self):
        """Test creating model without parameters uses default."""
        response = VitalSignsResponse()
        assert isinstance(response.data, list)
        assert response.data == []

    def test_calculate_bmi(self):
        """Test BMI calculation method."""
        response = VitalSignsResponse()
        bmi = response.calculate_bmi(height=70.0, weight=150.0)
        assert isinstance(bmi, float)
        assert bmi > 0
        # BMI = (150 / 70^2) * 703 ≈ 21.5
        assert 21.4 < bmi < 21.6


class TestCredentialModel:
    """Test APICredential model ODFHIR authentication format."""

    def test_credential_get_auth_header_odfhir_format(self):
        """Test get_auth_header() returns correct ODFHIR format."""
        credential = APICredential(
            base_url="https://api.example.com",
            developer_key=SecretStr("test_dev_key_123"),
            customer_key=SecretStr("test_portal_key_456"),
            environment="production",
        )
        
        headers = credential.get_auth_header()
        
        # Must return single Authorization header
        assert "Authorization" in headers
        assert len(headers) == 1
        
        # Must use ODFHIR format
        assert headers["Authorization"] == "ODFHIR test_dev_key_123/test_portal_key_456"
        assert headers["Authorization"].startswith("ODFHIR ")
        assert "/" in headers["Authorization"]

    def test_credential_get_auth_header_uses_secret_values(self):
        """Test get_auth_header() properly unwraps SecretStr values."""
        credential = APICredential(
            base_url="https://api.example.com",
            developer_key=SecretStr("secret_dev"),
            customer_key=SecretStr("secret_portal"),
            environment="production",
        )
        
        headers = credential.get_auth_header()
        
        # Verify SecretStr values are unwrapped
        assert "secret_dev" in headers["Authorization"]
        assert "secret_portal" in headers["Authorization"]
        assert headers["Authorization"] == "ODFHIR secret_dev/secret_portal"

    def test_credential_get_auth_header_no_custom_headers(self):
        """Test get_auth_header() does NOT return custom DeveloperKey/CustomerKey headers."""
        credential = APICredential(
            base_url="https://api.example.com",
            developer_key=SecretStr("key1"),
            customer_key=SecretStr("key2"),
            environment="production",
        )
        
        headers = credential.get_auth_header()
        
        # Must NOT contain old custom headers
        assert "DeveloperKey" not in headers
        assert "CustomerKey" not in headers
        
        # Must ONLY contain Authorization header
        assert list(headers.keys()) == ["Authorization"]
