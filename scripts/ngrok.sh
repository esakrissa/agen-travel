#!/bin/bash

# Script untuk menjalankan, memeriksa status, dan menghentikan ngrok
# Penggunaan: ./ngrok.sh [start|stop|status]

# Periksa lokasi ngrok
if [ -f "$HOME/ngrok" ]; then
    # Jika ngrok adalah file di direktori home
    NGROK_PATH="$HOME/ngrok"
elif [ -f "$HOME/ngrok/ngrok" ]; then
    # Jika ngrok adalah file di subdirektori ngrok
    NGROK_PATH="$HOME/ngrok/ngrok"
elif [ -f "/usr/local/bin/ngrok" ]; then
    # Jika ngrok di-install secara global
    NGROK_PATH="/usr/local/bin/ngrok"
elif command -v ngrok >/dev/null 2>&1; then
    # Jika ngrok ada di PATH
    NGROK_PATH="ngrok"
else
    echo "Error: Tidak dapat menemukan ngrok. Pastikan ngrok sudah diinstal."
    echo "Cek lokasi ngrok dengan perintah: find ~ -name ngrok -type f"
    exit 1
fi

# Fungsi untuk menampilkan bantuan
show_help() {
    echo "Penggunaan: $0 [start|stop|status]"
    echo "  start  : Menjalankan ngrok di background"
    echo "  stop   : Menghentikan proses ngrok"
    echo "  status : Memeriksa status ngrok"
}

# Fungsi untuk menjalankan ngrok
start_ngrok() {
    echo "Menjalankan ngrok di background dengan path: $NGROK_PATH..."
    
    # Periksa apakah ngrok sudah berjalan
    if pgrep -x "ngrok" > /dev/null; then
        echo "ngrok sudah berjalan."
        check_status
        return
    fi
    
    # Jalankan ngrok di background (ganti perintah sesuai kebutuhan, contoh untuk HTTP port 8080)
    $NGROK_PATH http 8080 > /dev/null 2>&1 &
    
    if [ $? -eq 0 ]; then
        echo "ngrok berhasil dijalankan."
        # Tunggu sebentar agar ngrok siap
        sleep 2
        check_status
    else
        echo "Gagal menjalankan ngrok."
    fi
}

# Fungsi untuk menghentikan ngrok
stop_ngrok() {
    echo "Menghentikan proses ngrok..."
    
    # Memeriksa apakah ngrok berjalan
    if ! pgrep -x "ngrok" > /dev/null; then
        echo "ngrok tidak sedang berjalan."
        return
    fi
    
    # Menghentikan proses ngrok
    pkill -f "ngrok"
    
    if [ $? -eq 0 ]; then
        echo "ngrok berhasil dihentikan."
    else
        echo "Gagal menghentikan ngrok."
    fi
}

# Fungsi untuk memeriksa status ngrok
check_status() {
    echo "Memeriksa status ngrok..."
    
    # Memeriksa apakah ngrok berjalan
    if ! pgrep -x "ngrok" > /dev/null; then
        echo "Status: ngrok tidak sedang berjalan."
        return
    fi
    
    echo "Status: ngrok sedang berjalan."
    
    # Dapatkan URL ngrok dari API
    echo "URL ngrok:"
    curl -s http://localhost:4040/api/tunnels | grep -o "https://[a-zA-Z0-9.-]*\.ngrok-free\.app"
}

# Memeriksa argumen
if [ $# -eq 0 ]; then
    show_help
    exit 1
fi

# Menjalankan perintah berdasarkan argumen
case "$1" in
    start)
        start_ngrok
        ;;
    stop)
        stop_ngrok
        ;;
    status)
        check_status
        ;;
    *)
        show_help
        exit 1
        ;;
esac

exit 0 