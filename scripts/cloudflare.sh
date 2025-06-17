#!/bin/bash

# Script untuk mengelola DNS records subdomain di Cloudflare
# Penggunaan: ./cloudflare-dns.sh [create|delete|list|status]

# Konfigurasi
DOMAIN="agen-travel.live"
TUNNEL_ID="98318113-6fe9-4c7d-8f57-5c9f2507b3ff"

# Daftar subdomain yang akan dikonfigurasi
SUBDOMAINS=(
    "traefik"
    "redis" 
    "grafana"
    "prometheus"
    "supabase"
)

# Warna untuk output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Path ke konfigurasi dan log
CONFIG_PATH="./.cloudflared/config.yml"
LOG_PATH="./.cloudflared/tunnel.log"
TUNNEL_NAME="agen-travel"

# Fungsi untuk menampilkan bantuan
show_help() {
    echo -e "${BLUE}Penggunaan: $0 [create|delete|list|status|start|stop|restart|logs|help]${NC}"
    echo ""
    echo "DNS Management:"
    echo "  create  : Membuat DNS CNAME records untuk semua subdomain"
    echo "  delete  : Menghapus DNS CNAME records untuk semua subdomain"
    echo "  list    : Menampilkan semua DNS records untuk domain"
    echo "  status  : Memeriksa status DNS records subdomain"
    echo ""
    echo "Tunnel Management:"
    echo "  start   : Menjalankan Cloudflare Tunnel di background"
    echo "  stop    : Menghentikan proses Cloudflare Tunnel"
    echo "  restart : Restart Cloudflare Tunnel (stop + start)"
    echo "  logs    : Menampilkan log tunnel"
    echo ""
    echo "  help    : Menampilkan bantuan ini"
    echo ""
    echo "Subdomain yang akan dikonfigurasi:"
    for subdomain in "${SUBDOMAINS[@]}"; do
        echo "  - ${subdomain}.${DOMAIN}"
    done
}

# Fungsi untuk memeriksa apakah cloudflared terinstall
check_cloudflared() {
    if ! command -v cloudflared &> /dev/null; then
        echo -e "${RED}Error: cloudflared tidak terinstall.${NC}"
        echo "Install dengan: brew install cloudflared"
        exit 1
    fi
}

# Fungsi untuk memeriksa autentikasi Cloudflare
check_auth() {
    echo -e "${BLUE}Memeriksa autentikasi Cloudflare...${NC}"
    
    # Cek apakah sudah login
    if ! cloudflared tunnel list &> /dev/null; then
        echo -e "${RED}Error: Belum login ke Cloudflare.${NC}"
        echo "Login dengan: cloudflared tunnel login"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Autentikasi Cloudflare berhasil${NC}"
}

# Fungsi untuk membuat DNS records
create_dns_records() {
    echo -e "${BLUE}Membuat DNS CNAME records untuk subdomain...${NC}"
    
    for subdomain in "${SUBDOMAINS[@]}"; do
        echo -e "${YELLOW}Membuat record untuk ${subdomain}.${DOMAIN}...${NC}"
        
        # Buat CNAME record yang mengarah ke tunnel
        result=$(cloudflared tunnel route dns $TUNNEL_ID "${subdomain}.${DOMAIN}" 2>&1)
        
        if [[ $? -eq 0 ]]; then
            echo -e "${GREEN}✓ Berhasil membuat record untuk ${subdomain}.${DOMAIN}${NC}"
        else
            # Cek apakah error karena record sudah ada
            if [[ $result == *"already exists"* ]] || [[ $result == *"sudah ada"* ]]; then
                echo -e "${YELLOW}⚠ Record untuk ${subdomain}.${DOMAIN} sudah ada${NC}"
            else
                echo -e "${RED}✗ Gagal membuat record untuk ${subdomain}.${DOMAIN}: $result${NC}"
            fi
        fi
    done
    
    echo -e "${GREEN}Selesai membuat DNS records.${NC}"
}

# Fungsi untuk menghapus DNS records
delete_dns_records() {
    echo -e "${BLUE}Menghapus DNS CNAME records untuk subdomain...${NC}"
    
    for subdomain in "${SUBDOMAINS[@]}"; do
        echo -e "${YELLOW}Menghapus record untuk ${subdomain}.${DOMAIN}...${NC}"
        
        # Hapus CNAME record
        result=$(cloudflared tunnel route dns --overwrite-dns $TUNNEL_ID "${subdomain}.${DOMAIN}" 2>&1)
        
        if [[ $? -eq 0 ]]; then
            echo -e "${GREEN}✓ Berhasil menghapus record untuk ${subdomain}.${DOMAIN}${NC}"
        else
            echo -e "${RED}✗ Gagal menghapus record untuk ${subdomain}.${DOMAIN}: $result${NC}"
        fi
    done
    
    echo -e "${GREEN}Selesai menghapus DNS records.${NC}"
}

# Fungsi untuk menampilkan semua DNS records
list_dns_records() {
    echo -e "${BLUE}Menampilkan semua DNS records untuk ${DOMAIN}...${NC}"
    
    # Gunakan cloudflared untuk menampilkan route
    echo -e "${YELLOW}Routes yang dikonfigurasi untuk tunnel:${NC}"
    cloudflared tunnel route list
    
    echo ""
    echo -e "${YELLOW}Informasi tunnel:${NC}"
    cloudflared tunnel info $TUNNEL_ID
}

# Fungsi untuk memeriksa status DNS records
check_status() {
    echo -e "${BLUE}Memeriksa status DNS records subdomain...${NC}"

    for subdomain in "${SUBDOMAINS[@]}"; do
        fqdn="${subdomain}.${DOMAIN}"
        echo -e "${YELLOW}Memeriksa ${fqdn}...${NC}"

        # Cek DNS resolution
        if nslookup "$fqdn" &> /dev/null; then
            echo -e "${GREEN}✓ DNS record untuk ${fqdn} ditemukan${NC}"

            # Test HTTP connection
            if curl -s --max-time 5 "http://${fqdn}" &> /dev/null; then
                echo -e "${GREEN}✓ HTTP connection ke ${fqdn} berhasil${NC}"
            else
                echo -e "${YELLOW}⚠ HTTP connection ke ${fqdn} gagal (mungkin service belum ready)${NC}"
            fi
        else
            echo -e "${RED}✗ DNS record untuk ${fqdn} tidak ditemukan${NC}"
        fi
        echo ""
    done
}

# ===== TUNNEL MANAGEMENT FUNCTIONS =====

# Fungsi untuk menjalankan tunnel
start_tunnel() {
    echo -e "${BLUE}Menjalankan Cloudflare Tunnel di background...${NC}"

    # Periksa apakah tunnel sudah berjalan
    if pgrep -f "cloudflared tunnel" > /dev/null; then
        echo -e "${YELLOW}Cloudflare Tunnel sudah berjalan.${NC}"
        check_tunnel_status
        return
    fi

    # Periksa apakah file konfigurasi ada
    if [ ! -f "$CONFIG_PATH" ]; then
        echo -e "${RED}Error: File konfigurasi tidak ditemukan di $CONFIG_PATH${NC}"
        exit 1
    fi

    # Jalankan tunnel di background
    nohup cloudflared tunnel --config "$CONFIG_PATH" run > "$LOG_PATH" 2>&1 &

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Cloudflare Tunnel berhasil dijalankan.${NC}"
        echo -e "${BLUE}Log tersimpan di: $LOG_PATH${NC}"
        # Tunggu sebentar agar tunnel siap
        sleep 3
        check_tunnel_status
    else
        echo -e "${RED}✗ Gagal menjalankan Cloudflare Tunnel.${NC}"
    fi
}

# Fungsi untuk menghentikan tunnel
stop_tunnel() {
    echo -e "${BLUE}Menghentikan proses Cloudflare Tunnel...${NC}"

    # Memeriksa apakah tunnel berjalan
    if ! pgrep -f "cloudflared tunnel" > /dev/null; then
        echo -e "${YELLOW}Cloudflare Tunnel tidak sedang berjalan.${NC}"
        return
    fi

    # Menghentikan proses tunnel
    pkill -f "cloudflared tunnel"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Cloudflare Tunnel berhasil dihentikan.${NC}"
    else
        echo -e "${RED}✗ Gagal menghentikan Cloudflare Tunnel.${NC}"
    fi
}

# Fungsi untuk restart tunnel
restart_tunnel() {
    echo -e "${BLUE}Restart Cloudflare Tunnel...${NC}"
    stop_tunnel
    sleep 2
    start_tunnel
}

# Fungsi untuk memeriksa status tunnel
check_tunnel_status() {
    echo -e "${BLUE}Memeriksa status Cloudflare Tunnel...${NC}"

    # Memeriksa apakah tunnel berjalan
    if ! pgrep -f "cloudflared tunnel" > /dev/null; then
        echo -e "${RED}Status: Cloudflare Tunnel tidak sedang berjalan.${NC}"
        return
    fi

    echo -e "${GREEN}Status: Cloudflare Tunnel sedang berjalan.${NC}"
    echo -e "${BLUE}Domain: https://agen-travel.live${NC}"

    # Tampilkan informasi tunnel
    echo -e "${YELLOW}Informasi tunnel:${NC}"
    cloudflared tunnel info $TUNNEL_NAME 2>/dev/null || echo -e "${RED}Tidak dapat mengambil informasi tunnel.${NC}"
}

# Fungsi untuk menampilkan log
show_logs() {
    echo -e "${BLUE}Menampilkan log Cloudflare Tunnel...${NC}"

    if [ ! -f "$LOG_PATH" ]; then
        echo -e "${RED}File log tidak ditemukan di: $LOG_PATH${NC}"
        return
    fi

    echo -e "${BLUE}Log file: $LOG_PATH${NC}"
    echo -e "${YELLOW}----------------------------------------${NC}"
    tail -f "$LOG_PATH"
}

# Main script logic
case "${1:-}" in
    # DNS Management Commands
    create)
        check_cloudflared
        check_auth
        create_dns_records
        ;;
    delete)
        check_cloudflared
        check_auth
        delete_dns_records
        ;;
    list)
        check_cloudflared
        check_auth
        list_dns_records
        ;;
    status)
        check_status
        ;;

    # Tunnel Management Commands
    start)
        check_cloudflared
        start_tunnel
        ;;
    stop)
        check_cloudflared
        stop_tunnel
        ;;
    restart)
        check_cloudflared
        restart_tunnel
        ;;
    logs)
        show_logs
        ;;

    # Help
    help)
        show_help
        ;;
    *)
        show_help
        exit 1
        ;;
esac
