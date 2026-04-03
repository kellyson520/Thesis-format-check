import io
import docx
from fastapi.testclient import TestClient
import sys
import os

# Add src to Python Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from main import app

def test_full_api_loop():
    client = TestClient(app)
    
    # 1. Create a dummy Docx
    doc = docx.Document()
    p = doc.add_paragraph("This is a test paragraph with wrong size.")
    run = p.add_run("Bad Size Run")
    run.font.size = docx.shared.Pt(8)
    
    buffer = io.BytesIO()
    doc.save(buffer)
    content = buffer.getvalue()
    
    # 2. Test /api/check (Zero-Disk IO)
    response = client.post(
        "/api/check",
        files={"file": ("test.docx", content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    )
    assert response.status_code == 200
    data = response.json()
    assert "issues" in data
    print(f"Check success: {data['total']} issues found.")
    
    # 3. Test /api/fix (Zero-Disk IO + FixerPipeline)
    response_fix = client.post(
        "/api/fix",
        files={"file": ("test.docx", content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    )
    assert response_fix.status_code == 200
    assert response_fix.headers["Content-Type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    
    print("Fix success: Received fixed docx.")

if __name__ == "__main__":
    try:
        test_full_api_loop()
        print("Integration Test Passed!")
    except Exception as e:
        print(f"Integration Test Failed: {e}")
        import traceback
        traceback.print_exc()
