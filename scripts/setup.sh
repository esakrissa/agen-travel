#!/bin/bash

# Script untuk setup Docker dan Cloudflare di GCP VM
# Penggunaan: ./setup.sh

# Warna untuk output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Setup folder untuk cloudflared
mkdir -p ~/.cloudflared

# Fungsi untuk memeriksa status command
check_status() {
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ $1${NC}"
  else
    echo -e "${RED}✗ $1${NC}"
    echo -e "${RED}Error: $2${NC}"
    exit 1
  fi
}

# Update package list
echo -e "${BLUE}=== Updating package lists ===${NC}"
sudo apt-get update
check_status "Package lists updated" "Failed to update package lists"

# Install prerequisites
echo -e "${BLUE}=== Installing prerequisites ===${NC}"
sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common gnupg lsb-release
check_status "Prerequisites installed" "Failed to install prerequisites"

# Install Docker
echo -e "${BLUE}=== Installing Docker ===${NC}"
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
check_status "Docker installed" "Failed to install Docker"

# Add current user to docker group
echo -e "${BLUE}=== Adding user to docker group ===${NC}"
sudo usermod -aG docker $USER
check_status "User added to docker group" "Failed to add user to docker group"

# Apply group changes to current session
echo -e "${BLUE}=== Applying Docker group changes ===${NC}"
newgrp docker << EOF
echo -e "${GREEN}✓ Docker group changes applied to current session${NC}"
EOF

# Install Docker Compose (modern version)
echo -e "${BLUE}=== Installing Docker Compose ===${NC}"
# Docker Compose v2 is now included with Docker by default, but let's ensure it's available
# Check if docker compose (v2) is available
if ! docker compose version &> /dev/null; then
    # Install Docker Compose v2 plugin if not available
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.6/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    # Also create symlink for docker compose command
    sudo ln -sf /usr/local/bin/docker-compose /usr/local/bin/docker-compose-v2
fi
check_status "Docker Compose installed" "Failed to install Docker Compose"

# Install Cloudflared
echo -e "${BLUE}=== Installing Cloudflared ===${NC}"
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb
check_status "Cloudflared installed" "Failed to install Cloudflared"

# Setup Cloudflare Tunnel
echo -e "${BLUE}=== Setup Cloudflare Tunnel ===${NC}"

# Cek beberapa kemungkinan lokasi file Cloudflare
CLOUDFLARE_LOCATIONS=(
  "~/.cloudflared"
  "~/tugas-akir/.cloudflared" 
  "~/agen-travel/.cloudflared"
  "~/.config/cloudflared"
  "$(pwd)/.cloudflared"
  "$(pwd)/../.cloudflared"
)

FOUND_CREDENTIALS=false
FOUND_CONFIG=false
CRED_PATH=""
CONFIG_PATH=""

# Cari file kredensial dan konfigurasi di berbagai lokasi
for location in "${CLOUDFLARE_LOCATIONS[@]}"; do
  expanded_location="${location/#\~/$HOME}"
  
  if [ -f "${expanded_location}/98318113-6fe9-4c7d-8f57-5c9f2507b3ff.json" ] && [ "$FOUND_CREDENTIALS" = false ]; then
    FOUND_CREDENTIALS=true
    CRED_PATH="${expanded_location}/98318113-6fe9-4c7d-8f57-5c9f2507b3ff.json"
    echo -e "${GREEN}✓ Cloudflare credentials ditemukan di: ${CRED_PATH}${NC}"
  fi
  
  if [ -f "${expanded_location}/config.yml" ] && [ "$FOUND_CONFIG" = false ]; then
    FOUND_CONFIG=true
    CONFIG_PATH="${expanded_location}/config.yml"
    echo -e "${GREEN}✓ Cloudflare config ditemukan di: ${CONFIG_PATH}${NC}"
  fi
done

# Jika file ditemukan, salin ke ~/.cloudflared/
if [ "$FOUND_CREDENTIALS" = true ]; then
  # Periksa apakah file perlu disalin atau sudah ada di lokasi yang tepat
  if [ "$CRED_PATH" != "$HOME/.cloudflared/98318113-6fe9-4c7d-8f57-5c9f2507b3ff.json" ]; then
    echo -e "${BLUE}=== Menyalin file kredensial ke ~/.cloudflared/ ===${NC}"
    cp -v "$CRED_PATH" ~/.cloudflared/
    check_status "File kredensial disalin" "Gagal menyalin file kredensial"
  else
    echo -e "${GREEN}✓ File kredensial sudah ada di lokasi yang tepat${NC}"
  fi
else
  echo -e "${YELLOW}⚠ Cloudflare credentials tidak ditemukan.${NC}"
  echo -e "${YELLOW}Gunakan perintah berikut dari komputer lokal Anda:${NC}"
  echo -e "${YELLOW}scp .cloudflared/98318113-6fe9-4c7d-8f57-5c9f2507b3ff.json ${USER}@$(hostname -I | awk '{print $1}' | tr -d ' '):~/.cloudflared/${NC}"
  echo -e "${YELLOW}Atau, jika ada di VM, gunakan perintah berikut:${NC}"
  echo -e "${YELLOW}cp ~/tugas-akir/.cloudflared/98318113-6fe9-4c7d-8f57-5c9f2507b3ff.json ~/.cloudflared/${NC}"
  FOUND_CREDENTIALS=false
fi

if [ "$FOUND_CONFIG" = true ]; then
  # Periksa apakah file perlu disalin atau sudah ada di lokasi yang tepat
  if [ "$CONFIG_PATH" != "$HOME/.cloudflared/config.yml" ]; then
    echo -e "${BLUE}=== Menyalin file konfigurasi ke ~/.cloudflared/ ===${NC}"
    cp -v "$CONFIG_PATH" ~/.cloudflared/
    check_status "File konfigurasi disalin" "Gagal menyalin file konfigurasi"
  else
    echo -e "${GREEN}✓ File konfigurasi sudah ada di lokasi yang tepat${NC}"
  fi
else
  echo -e "${YELLOW}⚠ Cloudflare config tidak ditemukan.${NC}"
  echo -e "${YELLOW}Gunakan perintah berikut dari komputer lokal Anda:${NC}"
  echo -e "${YELLOW}scp .cloudflared/config.yml ${USER}@$(hostname -I | awk '{print $1}' | tr -d ' '):~/.cloudflared/${NC}"
  echo -e "${YELLOW}Atau, jika ada di VM, gunakan perintah berikut:${NC}"
  echo -e "${YELLOW}cp ~/tugas-akir/.cloudflared/config.yml ~/.cloudflared/${NC}"
  FOUND_CONFIG=false
fi

# Set permissions for Cloudflare files
echo -e "${BLUE}=== Setting permissions for Cloudflare files ===${NC}"
if [ "$(ls -A ~/.cloudflared/ 2>/dev/null)" ]; then
  # Direktori harus executable, file harus readable
  chmod 755 ~/.cloudflared
  chmod 600 ~/.cloudflared/*
  
  # Fix credentials file path in config.yml
  sed -i "s|credentials-file: .*|credentials-file: /etc/cloudflared/98318113-6fe9-4c7d-8f57-5c9f2507b3ff.json|" ~/.cloudflared/config.yml
  
  check_status "Permissions set for Cloudflare files" "Failed to set permissions"
else
  echo -e "${YELLOW}⚠ No files found in ~/.cloudflared/ directory. Skipping permissions step.${NC}"
fi

# Install Cloudflared as a service
echo -e "${BLUE}=== Installing Cloudflared as a service ===${NC}"
if [ -f ~/.cloudflared/98318113-6fe9-4c7d-8f57-5c9f2507b3ff.json ] && [ -f ~/.cloudflared/config.yml ]; then
  # Pastikan izin folder benar
  chmod 755 ~/.cloudflared
  
  # Salin file ke lokasi alternatif yang dikenali cloudflared
  sudo mkdir -p /etc/cloudflared
  sudo cp ~/.cloudflared/config.yml /etc/cloudflared/
  sudo cp ~/.cloudflared/98318113-6fe9-4c7d-8f57-5c9f2507b3ff.json /etc/cloudflared/
  sudo chmod 600 /etc/cloudflared/*
  
  # Install service dengan merujuk ke file konfigurasi
  sudo cloudflared --config /etc/cloudflared/config.yml service install
  check_status "Cloudflared service installed" "Failed to install Cloudflared service"
  
  # Enable and start Cloudflared service
  echo -e "${BLUE}=== Enabling and starting Cloudflared service ===${NC}"
  sudo systemctl daemon-reload
  sudo systemctl enable cloudflared
  sudo systemctl start cloudflared
  
  # Tampilkan status dan log untuk debugging
  echo -e "${BLUE}Cloudflared service status:${NC}"
  sudo systemctl status cloudflared --no-pager
  
  echo -e "${BLUE}Cloudflared logs:${NC}"
  sudo journalctl -u cloudflared --no-pager -n 20
  
  check_status "Cloudflared service enabled and started" "Failed to enable and start Cloudflared service"
else
  echo -e "${YELLOW}⚠ Required Cloudflare files not found in ~/.cloudflared/. Skipping service installation.${NC}"
  echo -e "${YELLOW}Please ensure both credential and config files are in place before installing the service.${NC}"
  echo -e "${YELLOW}After fixing, run: sudo cloudflared service install${NC}"
fi

# Note: Firewall rules are already configured in gcp.sh when creating the VM
# No additional firewall configuration needed here

# Restart Docker service to ensure group changes take effect
echo -e "${BLUE}=== Restarting Docker service ===${NC}"
sudo systemctl restart docker
check_status "Docker service restarted" "Failed to restart Docker service"

# Test Docker without sudo
echo -e "${BLUE}=== Testing Docker without sudo ===${NC}"
if docker --version &> /dev/null; then
    echo -e "${GREEN}✓ Docker commands work without sudo${NC}"
    echo -e "${GREEN}✓ Docker version: $(docker --version)${NC}"
else
    echo -e "${YELLOW}⚠ Docker commands may still require sudo in this session${NC}"
    echo -e "${YELLOW}This is normal - you may need to log out and log back in${NC}"
fi
# Note: Docker networks will be created automatically by docker-compose

# Enable and start Docker service
echo -e "${BLUE}=== Enabling and starting Docker service ===${NC}"
sudo systemctl enable docker
sudo systemctl start docker
check_status "Docker service enabled and started" "Failed to enable and start Docker service"

# Test Docker installation
echo -e "${BLUE}=== Testing Docker Installation ===${NC}"
echo -e "${BLUE}Docker version:${NC}"
docker --version 2>/dev/null || sudo docker --version
echo -e "${BLUE}Docker Compose version:${NC}"
docker compose version 2>/dev/null || docker-compose --version 2>/dev/null || echo "Docker Compose not found"

# Display status of services
echo -e "${BLUE}=== Service Status ===${NC}"
echo -e "${BLUE}Docker:${NC}"
sudo systemctl status docker --no-pager
echo ""
echo -e "${BLUE}Cloudflared:${NC}"
sudo systemctl status cloudflared --no-pager

echo ""
echo -e "${GREEN}===========================${NC}"
echo -e "${GREEN}Installation Complete!${NC}"
echo -e "${GREEN}===========================${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Upload your project files to the VM"
echo "2. Test Docker without sudo: docker --version"
echo "3. Run docker compose up -d to start your services (no sudo needed!)"
echo "4. Check Cloudflared tunnel status with: sudo cloudflared tunnel info"
echo ""
echo -e "${GREEN}Docker Configuration:${NC}"
echo -e "${GREEN}✓ Docker installed and configured${NC}"
echo -e "${GREEN}✓ User added to docker group${NC}"
echo -e "${GREEN}✓ Docker Compose v2 available${NC}"
echo -e "${GREEN}✓ Docker networks will be created automatically by docker-compose${NC}"
echo ""
echo -e "${BLUE}Docker Commands (no sudo required):${NC}"
echo "  - docker --version"
echo "  - docker compose --version"
echo "  - docker compose up -d"
echo "  - docker compose down"
echo "  - docker ps"
echo "  - docker logs <container_name>"
echo ""
echo -e "${YELLOW}NOTE: If Docker commands still require sudo, try:${NC}"
echo -e "${YELLOW}1. Log out and log back in, OR${NC}"
echo -e "${YELLOW}2. Run: newgrp docker${NC}"
echo -e "${YELLOW}3. Or restart the VM: sudo reboot${NC}"