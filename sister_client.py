import requests
import json
from typing import Dict, List, Any, Optional

class SisterAPIClient:
    def __init__(self, is_sandbox: bool = False):
        if is_sandbox:
            self.base_url = "https://sister-api.kemdiktisaintek.go.id/ws-sandbox.php/1.0"
        else:
            self.base_url = "https://sister-api.kemdiktisaintek.go.id/ws.php/1.0"
        self.token = None
        
        # Menggunakan Session untuk mempertahankan header browser lengkap (Bypass 403 WAF)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": "https://sister-api.kemdiktisaintek.go.id",
            "Referer": "https://sister-api.kemdiktisaintek.go.id/ws.php/1.0",
            "Sec-Ch-Ua": '"Chromium";v="123", "Not:A-Brand";v="8"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        })

    def authorize(self, username: str, password: str, id_pengguna: str) -> Dict[str, Any]:
        """
        Mendapatkan token akses dari endpoint /authorize
        """
        endpoint = f"{self.base_url}/authorize"
        payload = {
            "username": username.strip(),
            "password": password.strip(),
            "id_pengguna": id_pengguna.strip()
        }
        
        try:
            response = self.session.post(
                endpoint, 
                data=json.dumps(payload), 
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("token")
                return {"success": True, "token": self.token, "data": data}
            else:
                return {
                    "success": False, 
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_sdm_list(self) -> List[Dict[str, Any]]:
        """
        Query awal: mengambil daftar SDM / Dosen
        """
        if not self.token:
            raise ValueError("Belum terautentikasi. Silakan lakukan authorize terlebih dahulu.")
        
        endpoint = f"{self.base_url}/referensi/sdm"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = self.session.get(endpoint, headers=headers, timeout=60)
        
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def get_sdm_data(self, category_endpoint: str, id_sdm: Optional[str] = None) -> Any:
        """
        Mengambil data detail berdasarkan endpoint kategori dan id_sdm (jika diperlukan)
        """
        if not self.token:
            raise ValueError("Belum terautentikasi.")
        
        url = f"{self.base_url}{category_endpoint}"
        headers = {"Authorization": f"Bearer {self.token}"}
        params = {}
        if id_sdm:
            params["id_sdm"] = id_sdm.strip()
            
        response = self.session.get(url, headers=headers, params=params, timeout=60)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}", "detail": response.text}