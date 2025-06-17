import os
import jwt
import json
import random
import string
import logging
import hashlib
import datetime
import httpx
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class AuthClient:
    """Client untuk komunikasi dengan backend authentication API"""
    
    def __init__(self):
        # Ambil base URL dari environment
        api_url = os.getenv("API_URL", "http://localhost:2025/api/v1/response/")
        # Ubah URL untuk auth endpoint
        self.base_url = api_url.replace("/response/", "/auth/")
        self.timeout = 10.0
        

    
    async def register_user(self, nama: str, email: str, password: str, 
                           telepon: str = None, alamat: str = None, 
                           telegram_id: str = None) -> Dict[str, Any]:
        """
        Registrasi user baru
        
        Args:
            nama (str): Nama lengkap user
            email (str): Email user
            password (str): Password user
            telepon (str, optional): Nomor telepon
            alamat (str, optional): Alamat lengkap
            telegram_id (str, optional): Telegram ID
            
        Returns:
            Dict: Response dari API registrasi
        """
        try:
            payload = {
                "nama": nama,
                "email": email,
                "password": password,
                "telepon": telepon,
                "alamat": alamat,
                "telegram_id": telegram_id
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}register",
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error saat registrasi: {e.response.status_code}")
            if e.response.status_code == 400:
                try:
                    error_detail = e.response.json()
                    return error_detail
                except:
                    pass
            return {
                "success": False,
                "message": "Error saat registrasi user"
            }
        except Exception as e:
            logger.error(f"Error saat registrasi: {e}")
            return {
                "success": False,
                "message": "Error koneksi ke server"
            }
    
    async def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """
        Login user dengan email dan password
        
        Args:
            email (str): Email user
            password (str): Password user
            
        Returns:
            Dict: Response dari API login
        """
        try:
            payload = {
                "email": email,
                "password": password
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}login",
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error saat login: {e.response.status_code}")
            if e.response.status_code == 401:
                return {
                    "success": False,
                    "message": "Email atau password salah"
                }
            return {
                "success": False,
                "message": "Error saat login"
            }
        except Exception as e:
            logger.error(f"Error saat login: {e}")
            return {
                "success": False,
                "message": "Error koneksi ke server"
            }
    
    async def link_telegram_account(self, access_token: str, telegram_id: str) -> Dict[str, Any]:
        """
        Link akun user dengan Telegram ID
        
        Args:
            access_token (str): JWT token user
            telegram_id (str): Telegram ID
            
        Returns:
            Dict: Response dari API link
        """
        try:
            payload = {
                "telegram_id": telegram_id
            }
            
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}telegram/link",
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error saat link telegram: {e.response.status_code}")
            return {
                "success": False,
                "message": "Error saat link telegram account"
            }
        except Exception as e:
            logger.error(f"Error saat link telegram: {e}")
            return {
                "success": False,
                "message": "Error koneksi ke server"
            }

    async def logout_user(self, access_token: str) -> Dict[str, Any]:
        """
        Logout user (hapus session dari Redis)

        Args:
            access_token (str): JWT token user

        Returns:
            Dict: Response dari API logout
        """
        try:
            headers = {
                "Authorization": f"Bearer {access_token}"
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}logout",
                    headers=headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error saat logout: {e.response.status_code}")
            return {
                "success": False,
                "message": "Error saat logout"
            }
        except Exception as e:
            logger.error(f"Error saat logout: {e}")
            return {
                "success": False,
                "message": "Error koneksi ke server"
            }

    async def check_user_session_by_telegram_id(self, telegram_id: str) -> Dict[str, Any]:
        """
        Cek session user di Redis berdasarkan telegram_id

        Args:
            telegram_id (str): Telegram user ID

        Returns:
            Dict: Response dari API dengan informasi session
        """
        try:
            payload = {
                "telegram_id": telegram_id
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}telegram/session-check",
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error saat check session: {e.response.status_code}")
            return {
                "success": False,
                "session_found": False,
                "message": "Error saat mengecek session"
            }
        except Exception as e:
            logger.error(f"Error saat check session: {e}")
            return {
                "success": False,
                "session_found": False,
                "message": "Error koneksi ke server"
            }

    async def refresh_verification_status(self, telegram_id: str) -> Dict[str, Any]:
        """
        Refresh status verifikasi user berdasarkan telegram_id

        Args:
            telegram_id (str): Telegram user ID

        Returns:
            Dict: Response dari API dengan status verifikasi terbaru
        """
        try:
            payload = {
                "telegram_id": telegram_id
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}refresh-verification",
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error saat refresh verification: {e.response.status_code}")
            return {
                "success": False,
                "message": "Error saat refresh status verifikasi"
            }
        except Exception as e:
            logger.error(f"Error saat refresh verification: {e}")
            return {
                "success": False,
                "message": "Error koneksi ke server"
            }

    async def resend_verification_email(self, access_token: str, user_id: int) -> Dict[str, Any]:
        """
        Resend verification email to user
        
        Args:
            access_token (str): JWT token user
            user_id (int): User ID
            
        Returns:
            Dict: Response dari API
        """
        try:
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}resend-verification-email/{user_id}",
                    headers=headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error saat resend verification email: {e.response.status_code}")
            return {
                "success": False,
                "message": "Error saat resend verification email"
            }
        except Exception as e:
            logger.error(f"Error saat resend verification email: {e}")
            return {
                "success": False,
                "message": "Error koneksi ke server"
            }

    async def update_user_profile(self, telegram_id: str, **profile_data) -> Dict[str, Any]:
        """
        Update user profile data
        
        Args:
            telegram_id (str): Telegram ID user
            **profile_data: Data profile yang ingin diupdate (nama, telepon, alamat, dll)
            
        Returns:
            Dict: Response dari API
        """
        try:
            payload = {"telegram_id": telegram_id, **profile_data}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}users/update-profile",
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error saat update profile: {e.response.status_code}")
            if e.response.status_code == 400:
                try:
                    error_detail = e.response.json()
                    return error_detail
                except:
                    pass
            return {
                "success": False,
                "message": "Error saat update profile"
            }
        except Exception as e:
            logger.error(f"Error saat update profile: {e}")
            return {
                "success": False,
                "message": "Error koneksi ke server"
            }

# Global instance
auth_client = AuthClient()
