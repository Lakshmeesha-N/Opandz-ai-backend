import httpx
import asyncio
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

BASE_URL = "http://localhost:8080"

async def test_endpoint(client, method, url, requires_auth=False, json=None, data=None, files=None):
    try:
        if method == "GET":
            response = await client.get(url)
        elif method == "POST":
            response = await client.post(url, json=json, data=data, files=files)
        elif method == "PUT":
            response = await client.put(url, json=json)
        elif method == "DELETE":
            response = await client.delete(url)
        
        # If it requires auth and we provide no token, it should be 401
        if requires_auth:
            if response.status_code == 401:
                logging.info(f"[PASS] {method} {url} - Returned 401 as expected (No Auth)")
            else:
                logging.error(f"[FAIL] {method} {url} - Expected 401, got {response.status_code}")
        else:
            if response.status_code in (200, 202):
                logging.info(f"[PASS] {method} {url} - Returned {response.status_code}")
            else:
                logging.warning(f"[WARN] {method} {url} - Returned {response.status_code}")
                
    except Exception as e:
        logging.error(f"[ERROR] {method} {url} - Exception: {e}")

async def main():
    async with httpx.AsyncClient() as client:
        # Public endpoints
        await test_endpoint(client, "GET", f"{BASE_URL}/")
        await test_endpoint(client, "GET", f"{BASE_URL}/health")
        
        # Auth protected endpoints (should return 401)
        await test_endpoint(client, "POST", f"{BASE_URL}/auth/me", requires_auth=True)
        
        await test_endpoint(client, "POST", f"{BASE_URL}/agents/setup/", requires_auth=True, json={"file_path": "a", "vault_name": "b", "template_name": "c"})
        # /agents/setup/status/{job_id} is public
        await test_endpoint(client, "GET", f"{BASE_URL}/agents/setup/status/123")
        
        await test_endpoint(client, "POST", f"{BASE_URL}/agents/intake/", requires_auth=True, data={"session_id": "a", "template_id": "b"}, files=[("files", ("test.txt", b"dummy content"))])
        # /agents/intake/status/{job_id} is public
        await test_endpoint(client, "GET", f"{BASE_URL}/agents/intake/status/123")
        
        await test_endpoint(client, "POST", f"{BASE_URL}/agents/document-edit/", requires_auth=True, data={"template_id": "a", "user_message": "b"}, files=[("files", ("test.txt", b"dummy content"))])
        # /agents/document-edit/status/{job_id} is public
        await test_endpoint(client, "GET", f"{BASE_URL}/agents/document-edit/status/123")
        
        await test_endpoint(client, "GET", f"{BASE_URL}/generated-documents/123", requires_auth=True)
        await test_endpoint(client, "PUT", f"{BASE_URL}/generated-documents/123", requires_auth=True, json={"generated_docxjs_code": "a"})
        await test_endpoint(client, "DELETE", f"{BASE_URL}/generated-documents/123", requires_auth=True)
        
        await test_endpoint(client, "GET", f"{BASE_URL}/template-registry/vaults", requires_auth=True)
        await test_endpoint(client, "GET", f"{BASE_URL}/template-registry/vaults/my-vault", requires_auth=True)
        await test_endpoint(client, "GET", f"{BASE_URL}/template-registry/templates/123", requires_auth=True)

if __name__ == "__main__":
    asyncio.run(main())
