#!/bin/bash

# Script untuk setup DNS records untuk frontend services
# Penggunaan: ./setup-frontend-dns.sh [create|delete]

# Konfigurasi
DOMAIN="agen-travel.live"
TUNNEL_ID="98318113-6fe9-4c7d-8f57-5c9f2507b3ff"

# Subdomain untuk frontend services
FRONTEND_SUBDOMAINS=(
    "chat"        # WebUI (Next.js) - localhost:3000
    "langgraph"   # LangGraph API - localhost:2024
)

# Warna untuk output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fungsi untuk menampilkan bantuan
show_help() {
    echo -e "${BLUE}Setup DNS Records untuk Frontend Services${NC}"
    echo -e "${BLUE}Penggunaan: $0 [create|delete|help]${NC}"
    echo ""
    echo "Commands:"
    echo "  create  : Membuat DNS CNAME records untuk frontend subdomain"
    echo "  delete  : Menghapus DNS CNAME records untuk frontend subdomain"
    echo "  help    : Menampilkan bantuan ini"
    echo ""
    echo "Frontend subdomain yang akan dikonfigurasi:"
    for subdomain in "${FRONTEND_SUBDOMAINS[@]}"; do
        echo "  - ${subdomain}.${DOMAIN}"
    done
    echo ""
    echo "Setelah setup DNS, akses frontend services via:"
    echo "  - WebUI: https://chat.agen-travel.live"
    echo "  - LangGraph API: https://langgraph.agen-travel.live/docs"
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
    echo -e "${BLUE}Membuat DNS CNAME records untuk frontend subdomain...${NC}"
    
    for subdomain in "${FRONTEND_SUBDOMAINS[@]}"; do
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
    
    echo ""
    echo -e "${GREEN}✓ Selesai membuat DNS records untuk frontend services.${NC}"
    echo ""
    echo -e "${BLUE}Frontend services akan tersedia di:${NC}"
    echo -e "${GREEN}  • WebUI: https://chat.agen-travel.live${NC}"
    echo -e "${GREEN}  • LangGraph API: https://langgraph.agen-travel.live/docs${NC}"
    echo ""
    echo -e "${YELLOW}Catatan: DNS propagation mungkin membutuhkan beberapa menit.${NC}"
}

# Fungsi untuk menghapus DNS records
delete_dns_records() {
    echo -e "${BLUE}Menghapus DNS CNAME records untuk frontend subdomain...${NC}"
    
    for subdomain in "${FRONTEND_SUBDOMAINS[@]}"; do
        echo -e "${YELLOW}Menghapus record untuk ${subdomain}.${DOMAIN}...${NC}"
        
        # Hapus CNAME record
        result=$(cloudflared tunnel route dns --overwrite-dns $TUNNEL_ID "${subdomain}.${DOMAIN}" 2>&1)
        
        if [[ $? -eq 0 ]]; then
            echo -e "${GREEN}✓ Berhasil menghapus record untuk ${subdomain}.${DOMAIN}${NC}"
        else
            echo -e "${RED}✗ Gagal menghapus record untuk ${subdomain}.${DOMAIN}: $result${NC}"
        fi
    done
    
    echo -e "${GREEN}Selesai menghapus DNS records untuk frontend services.${NC}"
}

# Main script logic
case "${1:-}" in
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
    help)
        show_help
        ;;
    *)
        show_help
        exit 1
        ;;
esac
