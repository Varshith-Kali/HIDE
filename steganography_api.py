# steganography_api.py
import requests
import os
import json
from typing import Optional, Dict, Any, Tuple

class SteganographyError(Exception):
    """Base exception for steganography errors"""
    pass

class VersionCompatibilityError(SteganographyError):
    """Exception raised when there's a version incompatibility between client and server"""
    def __init__(self, message: str, version: Optional[int] = None):
        self.version = version
        super().__init__(message)

class NoMessageFoundError(SteganographyError):
    """Exception raised when no hidden message is found in the image"""
    pass

class SteganographyAPI:
    """Client for the Hide-rs Steganography API"""
    
    def __init__(self, base_url: str = "http://localhost:8080/api"):
        self.base_url = base_url
        
    def health_check(self) -> Dict[str, Any]:
        """Check if the API server is running"""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def encode(self, image_path: str, message: str, output_format: str = "png") -> Dict[str, Any]:
        """Encode a message into an image using the API"""
        with open(image_path, 'rb') as img_file:
            files = {'cover_image': (os.path.basename(image_path), img_file, 'image/png')}
            data = {
                'message': message,
                'output_format': output_format
            }
            
            response = requests.post(f"{self.base_url}/encode", files=files, data=data)
            response.raise_for_status()
            return response.json()
    
    def decode(self, image_path: str) -> str:
        """Decode a message from an image using the API"""
        with open(image_path, 'rb') as img_file:
            files = {'stego_image': (os.path.basename(image_path), img_file, 'image/png')}
            
            response = requests.post(f"{self.base_url}/decode", files=files)
            
            # Handle HTTP errors
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                if response.status_code == 400:
                    # Try to parse the error message
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('message', '')
                        
                        # Check for version compatibility error
                        if "Unsupported message format version" in error_msg:
                            import re
                            version_match = re.search(r'version: (\d+)', error_msg)
                            version = int(version_match.group(1)) if version_match else None
                            raise VersionCompatibilityError(
                                f"The image uses an unsupported message format version: {version}",
                                version
                            )
                        # Check for no message found error
                        elif "No message found" in error_msg or "not contain" in error_msg:
                            raise NoMessageFoundError("No hidden message was found in this image")
                    except (ValueError, AttributeError, json.JSONDecodeError):
                        pass
                raise
            
            # Process successful response
            result = response.json()
            
            if result['status'] == 'success':
                return result.get('message', '')
            else:
                # Check for specific error types in API response
                error_msg = result.get('message', '')
                
                if "Unsupported message format version" in error_msg:
                    import re
                    version_match = re.search(r'version: (\d+)', error_msg)
                    version = int(version_match.group(1)) if version_match else None
                    raise VersionCompatibilityError(
                        f"The image uses an unsupported message format version: {version}",
                        version
                    )
                elif "No message found" in error_msg or "not contain" in error_msg or "Failed to decode" in error_msg:
                    raise NoMessageFoundError("No hidden message was found in this image")
                
                # Generic error
                raise SteganographyError(f"API Error: {error_msg}")
    
    def download_image(self, image_id: str, output_path: str) -> None:
        """Download an encoded image by its ID"""
        response = requests.get(f"{self.base_url}/images/{image_id}", stream=True)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
    def check_version_compatibility(self) -> Dict[str, Any]:
        """Check version compatibility with the server"""
        response = requests.get(f"{self.base_url}/version")
        response.raise_for_status()
        return response.json()