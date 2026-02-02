import requests
import click
from typing import Optional, Dict, Any

class APIClient:
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session() #la sessione resta perche definisco la cli 
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict] = None,
        json: Optional[Dict] = None
    ) -> Dict[str, Any]:
       
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.ConnectionError as e:
            raise APIConnectionError(f"Unable to connect to {url}")
            
        except requests.exceptions.Timeout:
            raise APITimeoutError(f"Timeout after {self.timeout} seconds")
            
        except requests.exceptions.HTTPError as e:
            raise APIHTTPError(
                status_code=e.response.status_code,
                reason=e.response.reason,
                detail=self._extract_error_detail(e.response)
            )
    
    def _extract_error_detail(self, response):
        """Estrae i dettagli dell'errore dalla risposta"""
        try:
            error_data = response.json()
            return error_data.get('detail', response.text)
        except:
            return response.text
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        return self._make_request("GET", endpoint, params=params)
    
    def post(self, endpoint: str, params: Optional[Dict] = None, json: Optional[Dict] = None) -> Dict[str, Any]:
        return self._make_request("POST", endpoint, params=params, json=json)  
    
    def delete(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        return self._make_request("DELETE", endpoint, params=params)
    
    def patch(self, endpoint: str, params: Optional[Dict] = None, json: Optional[Dict] = None) -> Dict[str, Any]:
        return self._make_request("PATCH", endpoint, params=params, json=json)

# Eccezioni custom
class APIError(click.ClickException):
    pass

class APIConnectionError(APIError):
    pass

class APITimeoutError(APIError):
    pass

class APIHTTPError(APIError):
    def __init__(self, status_code: int, reason: str, detail: Any):
        self.status_code = status_code
        self.reason = reason
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {reason}")