"""Diagnostic script to test individual API endpoints.

Tests each endpoint independently to identify which are working/failing.
Logs results without exposing PHI.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from opendental_cli.api_client import OpenDentalAPIClient
from opendental_cli.models.credential import APICredential
from pydantic import SecretStr


async def test_endpoints():
    """Test each endpoint individually."""
    
    # Test credentials (replace with actual if available)
    credential = APICredential(
        base_url="https://api.opendental.com/api/v1",
        developer_key=SecretStr("test_dev_key"),
        customer_key=SecretStr("test_portal_key"),
        environment="production",
    )
    
    # Test parameters
    patnum = 39689
    aptnum = 99413
    
    client = OpenDentalAPIClient(credential)
    
    endpoints = [
        ("ProcedureLogs", lambda: client.fetch_procedure_logs(aptnum)),
        ("Allergies", lambda: client.fetch_allergies(patnum)),
        ("Medications", lambda: client.fetch_medications(patnum)),
        ("Problems", lambda: client.fetch_problems(patnum)),
        ("PatientNotes", lambda: client.fetch_patient_notes(patnum)),
        ("VitalSigns", lambda: client.fetch_vital_signs(aptnum)),
    ]
    
    print("=" * 80)
    print("DIAGNOSTIC TEST: Individual Endpoint Testing")
    print("=" * 80)
    print(f"PatNum: {patnum}")
    print(f"AptNum: {aptnum}")
    print(f"Base URL: {credential.base_url}")
    print("=" * 80)
    print()
    
    results = []
    
    for name, fetch_func in endpoints:
        print(f"Testing {name}...", end=" ")
        try:
            response = await fetch_func()
            status = "✅ SUCCESS" if response.success else "❌ FAILED"
            print(f"{status} (HTTP {response.http_status})")
            
            if not response.success:
                print(f"  Error: {response.error_message}")
            
            results.append({
                "endpoint": name,
                "success": response.success,
                "http_status": response.http_status,
                "error": response.error_message if not response.success else None,
            })
        except Exception as e:
            print(f"❌ EXCEPTION: {type(e).__name__}: {str(e)}")
            results.append({
                "endpoint": name,
                "success": False,
                "http_status": 0,
                "error": f"Exception: {str(e)}",
            })
        print()
    
    await client.close()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    print(f"Successful: {len(successful)}/6")
    print(f"Failed: {len(failed)}/6")
    print()
    
    if successful:
        print("✅ Working endpoints:")
        for r in successful:
            print(f"  - {r['endpoint']}")
        print()
    
    if failed:
        print("❌ Failing endpoints:")
        for r in failed:
            print(f"  - {r['endpoint']} (HTTP {r['http_status']}): {r['error']}")
        print()
    
    print("=" * 80)
    
    return results


if __name__ == "__main__":
    print("Note: This script uses test credentials.")
    print("Update credential values if you have real API access.")
    print()
    
    results = asyncio.run(test_endpoints())
    
    # Exit with appropriate code
    failed_count = len([r for r in results if not r["success"]])
    sys.exit(0 if failed_count == 0 else 1)
