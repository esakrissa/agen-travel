"""
Cache management endpoints dengan session management.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional
from utils.cache import (
    update_cache_key_metrics, redis_cache, invalidate_cache_pattern,
    get_all_user_sessions, cleanup_expired_sessions, invalidate_user_session,
    RedisKeyValidator
)
from utils.auth import get_current_user_with_session
from models.auth import SessionData, ErrorResponse
from utils.handler import log_exception
import logging

router = APIRouter(prefix="/cache", tags=["Cache"])

@router.post("/refresh-metrics")
async def refresh_cache_metrics():
    """
    # 🔄 Refresh Cache Metrics

    **Memperbarui metrik cache secara manual.**

    *Berguna untuk debugging atau monitoring manual sistem cache.*

    ## ✅ Response Success (200)
    ```json
    {
        "status": "success",
        "message": "Cache metrics berhasil direfresh"
    }
    ```

    ## 🎯 Kegunaan
    - Debugging performa cache
    - Monitoring manual
    - Troubleshooting sistem
    """
    try:
        await update_cache_key_metrics()
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Cache metrics berhasil direfresh"
            }
        )
    except Exception as e:
        log_exception(e)
        raise HTTPException(
            status_code=500,
            detail=f"Gagal refresh cache metrics: {str(e)}"
        )

@router.get("/stats")
async def get_cache_stats():
    """
    # 📊 Statistik Cache

    **Mendapatkan informasi lengkap tentang penggunaan cache sistem.**

    *Menampilkan statistik Redis, jumlah keys, dan penggunaan memori.*

    ## ✅ Response Success (200)
    ```json
    {
        "status": "success",
        "data": {
            "redis_info": {
                "used_memory": 1024000,
                "used_memory_human": "1MB",
                "connected_clients": 5,
                "keyspace_hits": 1000,
                "keyspace_misses": 50
            },
            "cache_keys": {
                "total_keys": 150,
                "by_type": {
                    "hotels": 50,
                    "flights": 30,
                    "tours": 20
                }
            }
        }
    }
    ```

    ## 📈 Informasi yang Disediakan
    - **Redis Info**: Penggunaan memori, koneksi client
    - **Cache Keys**: Total keys dan breakdown per kategori
    - **Performance**: Hit/miss ratio
    """
    try:
        client = await redis_cache._get_client()
        
        # Get basic Redis info
        info = await client.info()
        
        # Get all cache keys
        all_keys = await client.keys("agen_travel:*")
        
        # Count keys per cache type dengan format baru
        cache_type_counts = {}
        for key in all_keys:
            key_str = key.decode() if isinstance(key, bytes) else key
            key_info = RedisKeyValidator.get_key_info(key_str)

            if key_info.get("is_valid"):
                category = key_info["category"]
                subcategory = key_info["subcategory"]

                # Count by category
                if category not in cache_type_counts:
                    cache_type_counts[category] = 0
                cache_type_counts[category] += 1
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": {
                    "redis_info": {
                        "used_memory": info.get("used_memory", 0),
                        "used_memory_human": info.get("used_memory_human", "0B"),
                        "connected_clients": info.get("connected_clients", 0),
                        "total_commands_processed": info.get("total_commands_processed", 0),
                        "keyspace_hits": info.get("keyspace_hits", 0),
                        "keyspace_misses": info.get("keyspace_misses", 0),
                    },
                    "cache_keys": {
                        "total_keys": len(all_keys),
                        "by_type": cache_type_counts
                    }
                }
            }
        )
    except Exception as e:
        log_exception(e)
        raise HTTPException(
            status_code=500,
            detail=f"Gagal mendapatkan cache stats: {str(e)}"
        )

@router.delete("/clear/{cache_type}")
async def clear_cache_by_type(cache_type: str):
    """
    # 🧹 Hapus Cache Berdasarkan Tipe

    **Menghapus semua cache untuk kategori tertentu.**

    *Berguna untuk refresh data spesifik tanpa menghapus seluruh cache.*

    ## 🔧 Path Parameters
    - **cache_type**: Jenis cache yang akan dihapus

    ## 📋 Tipe Cache yang Valid
    - `hotels` - Cache data hotel
    - `flights` - Cache data penerbangan
    - `tours` - Cache data paket tur
    - `availability` - Cache ketersediaan
    - `user_bookings` - Cache pemesanan user
    - `database_search` - Cache pencarian database
    - `web_search` - Cache pencarian web

    ## ✅ Response Success (200)
    ```json
    {
        "status": "success",
        "message": "Cache type 'hotels' berhasil dihapus"
    }
    ```

    ## ❌ Response Error (400)
    - Cache type tidak valid
    - Parameter tidak sesuai format
    """
    try:
        # Validasi cache type
        valid_types = [
            "hotels", "flights", "tours", "availability", 
            "user_bookings", "database_search", "web_search"
        ]
        
        if cache_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Cache type tidak valid. Valid types: {', '.join(valid_types)}"
            )
        
        # Hapus cache berdasarkan pattern
        await invalidate_cache_pattern(f"{cache_type}:*")
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": f"Cache type '{cache_type}' berhasil dihapus"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        log_exception(e)
        raise HTTPException(
            status_code=500,
            detail=f"Gagal menghapus cache: {str(e)}"
        )

@router.delete("/clear-all")
async def clear_all_cache():
    """
    # ⚠️ Hapus Semua Cache

    **Menghapus seluruh cache aplikasi.**

    *PERINGATAN: Operasi ini akan menghapus semua cache dan dapat mempengaruhi performa sistem!*

    ## ⚠️ Peringatan Penting
    - **Operasi berbahaya**: Menghapus seluruh cache sistem
    - **Impact performa**: Sistem akan lebih lambat sementara
    - **Gunakan dengan hati-hati**: Hanya untuk maintenance atau troubleshooting

    ## ✅ Response Success (200)
    ```json
    {
        "status": "success",
        "message": "Semua cache berhasil dihapus"
    }
    ```

    ## 🎯 Kegunaan
    - Reset cache saat deployment
    - Troubleshooting masalah cache
    - Maintenance sistem
    - Development testing

    ## 💡 Rekomendasi
    - Lakukan saat traffic rendah
    - Monitor performa setelah operasi
    - Pertimbangkan clear per tipe terlebih dahulu
    """
    try:
        await invalidate_cache_pattern("*")

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Semua cache berhasil dihapus"
            }
        )
    except Exception as e:
        log_exception(e)
        raise HTTPException(
            status_code=500,
            detail=f"Gagal menghapus semua cache: {str(e)}"
        )


@router.get("/sessions/active")
async def get_active_sessions(current_user: SessionData = Depends(get_current_user_with_session)):
    """
    # 👥 Daftar Session Aktif

    **Mendapatkan informasi semua session pengguna yang aktif.**

    *Endpoint ini memerlukan autentikasi dan menampilkan session yang tersimpan di Redis.*

    ## 🔒 Authorization Required
    - **Bearer Token**: JWT token dari login

    ## ✅ Response Success (200)
    ```json
    {
        "status": "success",
        "message": "Ditemukan 3 session aktif",
        "data": {
            "total_sessions": 3,
            "sessions": [
                {
                    "session_key": "agen_travel:session:user:123",
                    "user_id": "123",
                    "email": "wayanbagus@gmail.com",
                    "nama": "Wayan Bagus",
                    "login_time": "2024-01-15T10:30:00Z",
                    "last_activity": "2024-01-15T11:45:00Z",
                    "ttl_seconds": 3600
                }
            ]
        }
    }
    ```

    ## 🎯 Kegunaan
    - Monitoring session aktif
    - Audit login pengguna
    - Troubleshooting session issues
    """
    try:
        session_keys = await get_all_user_sessions()

        active_sessions = []
        for session_key in session_keys:
            session_data = await redis_cache.get(session_key)
            if session_data:
                # Parse user ID dari key
                key_info = RedisKeyValidator.get_key_info(session_key)
                user_id = key_info.get("user_id", "unknown")

                # Get TTL
                client = await redis_cache._get_client()
                ttl = await client.ttl(session_key)

                active_sessions.append({
                    "session_key": session_key,
                    "user_id": user_id,
                    "email": session_data.get("email"),
                    "nama": session_data.get("nama"),
                    "login_time": session_data.get("login_time"),
                    "last_activity": session_data.get("last_activity"),
                    "ttl_seconds": ttl if ttl > 0 else None
                })

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": f"Ditemukan {len(active_sessions)} session aktif",
                "data": {
                    "total_sessions": len(active_sessions),
                    "sessions": active_sessions
                }
            }
        )

    except Exception as e:
        log_exception(e)
        raise HTTPException(
            status_code=500,
            detail=f"Gagal mengambil daftar session aktif: {str(e)}"
        )


@router.post("/sessions/cleanup")
async def cleanup_sessions(current_user: SessionData = Depends(get_current_user_with_session)):
    """
    # 🧹 Bersihkan Session Expired

    **Menghapus session yang sudah kedaluwarsa dari Redis.**

    *Operasi maintenance untuk membersihkan session yang tidak aktif dan menghemat memori.*

    ## 🔒 Authorization Required
    - **Bearer Token**: JWT token dari login

    ## ✅ Response Success (200)
    ```json
    {
        "status": "success",
        "message": "Berhasil membersihkan 5 session expired",
        "details": {
            "sessions_cleaned": 5,
            "total_sessions_before": 15,
            "total_sessions_after": 10
        }
    }
    ```

    ## 🎯 Kegunaan
    - Maintenance rutin sistem
    - Menghemat penggunaan memori Redis
    - Cleanup session yang tidak aktif
    - Optimasi performa

    ## 💡 Rekomendasi
    - Jalankan secara berkala (misalnya daily cron job)
    - Monitor sebelum dan sesudah cleanup
    """
    try:
        cleaned_count = await cleanup_expired_sessions()

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": f"Session cleanup berhasil. {cleaned_count} session expired dibersihkan",
                "data": {
                    "cleaned_sessions": cleaned_count
                }
            }
        )

    except Exception as e:
        log_exception(e)
        raise HTTPException(
            status_code=500,
            detail=f"Gagal melakukan session cleanup: {str(e)}"
        )


@router.delete("/sessions/{user_id}")
async def invalidate_session(
    user_id: int,
    current_user: SessionData = Depends(get_current_user_with_session)
):
    """
    # 🚫 Hapus Session Pengguna

    **Menghapus session spesifik untuk pengguna tertentu.**

    *Berguna untuk logout paksa atau troubleshooting masalah session pengguna.*

    ## 🔒 Authorization Required
    - **Bearer Token**: JWT token dari login

    ## 🔧 Path Parameters
    - **user_id**: ID pengguna yang session-nya akan dihapus

    ## ✅ Response Success (200)
    ```json
    {
        "status": "success",
        "message": "Session untuk user 123 berhasil dihapus"
    }
    ```

    ## ❌ Response Error
    - **404**: Session tidak ditemukan
    - **400**: User ID tidak valid

    ## 🎯 Kegunaan
    - Logout paksa pengguna bermasalah
    - Troubleshooting session issues
    - Security incident response
    - Admin user management

    ## ⚠️ Catatan
    - Pengguna akan ter-logout dari semua device
    - Operasi tidak dapat dibatalkan
    """
    try:
        await invalidate_user_session(user_id)

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": f"Session untuk user {user_id} berhasil di-invalidate",
                "data": {
                    "invalidated_user_id": user_id
                }
            }
        )

    except Exception as e:
        log_exception(e)
        raise HTTPException(
            status_code=500,
            detail=f"Gagal invalidate session untuk user {user_id}: {str(e)}"
        )
