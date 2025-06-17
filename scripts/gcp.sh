#!/bin/bash

# Script Manajemen VM GCP
# Fungsi:
# - Membuat VM baru dengan firewall rules
# - Memeriksa status VM dan resource
# - Menghapus VM dan semua resource terkait
# - Setup SSH untuk VSCode Remote

# Nilai default
PROJECT_ID="travel-agency-448103"
ZONE="asia-southeast2-a"
REGION="asia-southeast2"
VM_NAME="agen-travel"
MACHINE_TYPE="e2-standard-16"
IMAGE_FAMILY="ubuntu-2404-lts"
IMAGE_PROJECT="ubuntu-os-cloud"
DISK_SIZE="46GB"
DISK_TYPE="pd-standard"
SSH_USER="esakrissa"
SSH_KEY_PATH="/Users/esakrissa/.ssh/remote-agen-travel.pub"
SSH_CONFIG_PATH="/Users/esakrissa/.ssh/config"

# Warna untuk output
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
NC="\033[0m" # Tanpa warna

# Fungsi untuk menampilkan cara penggunaan
usage() {
  echo -e "${BLUE}Penggunaan:${NC} $0 [create|status|delete|setup-ssh]"
  echo
  echo -e "${BLUE}Perintah:${NC}"
  echo -e "  create\t - Membuat VM instance baru dengan firewall rules"
  echo -e "  status\t - Menampilkan detail VM instance"
  echo -e "  delete\t - Menghapus VM instance dan resource terkait"
  echo -e "  setup-ssh\t - Mengatur SSH untuk VSCode Remote Access"
  exit 1
}

# Fungsi untuk memeriksa keberadaan VM
vm_exists() {
  if gcloud compute instances describe $VM_NAME --zone=$ZONE --project=$PROJECT_ID &>/dev/null; then
    return 0
  else
    return 1
  fi
}

# Fungsi untuk membuat VM dan mengkonfigurasi firewall rules
create_vm() {
  echo -e "${BLUE}Membuat VM instance ${VM_NAME}...${NC}"
  
  # Memeriksa apakah VM sudah ada
  if vm_exists; then
    echo -e "${RED}Error: VM instance ${VM_NAME} sudah ada!${NC}"
    echo -e "${YELLOW}Gunakan './gcp.sh status' untuk memeriksa detail VM yang ada.${NC}"
    exit 1
  fi
  
  # Memeriksa apakah SSH key ada
  if [ ! -f "$SSH_KEY_PATH" ]; then
    echo -e "${RED}Error: SSH public key tidak ditemukan di $SSH_KEY_PATH!${NC}"
    echo -e "${YELLOW}Pastikan SSH key tersedia sebelum membuat VM.${NC}"
    exit 1
  fi

  # Membaca SSH key
  SSH_KEY_CONTENT=$(cat "$SSH_KEY_PATH")
  
  # Membuat VM instance
  echo -e "${YELLOW}Membuat VM instance dengan konfigurasi berikut:${NC}"
  echo -e "  - Nama: ${VM_NAME}"
  echo -e "  - Tipe Mesin: ${MACHINE_TYPE}"
  echo -e "  - Zona: ${ZONE}"
  echo -e "  - Image: ${IMAGE_FAMILY} dari ${IMAGE_PROJECT}"
  echo -e "  - Ukuran Disk: ${DISK_SIZE}"
  echo -e "  - SSH Key: ${SSH_KEY_PATH}"
  
  gcloud compute instances create $VM_NAME \
    --project=$PROJECT_ID \
    --zone=$ZONE \
    --machine-type=$MACHINE_TYPE \
    --image-family=$IMAGE_FAMILY \
    --image-project=$IMAGE_PROJECT \
    --boot-disk-size=$DISK_SIZE \
    --boot-disk-type=$DISK_TYPE \
    --tags=http-server,https-server,allow-supabase,allow-telegram,allow-grafana,allow-prometheus \
    --metadata="ssh-keys=${SSH_USER}:${SSH_KEY_CONTENT}"
  
  VM_CREATE_STATUS=$?
  
  if [ $VM_CREATE_STATUS -ne 0 ]; then
    echo -e "${RED}Error: Gagal membuat VM instance!${NC}"
    exit 1
  fi
  
  echo -e "${GREEN}VM instance ${VM_NAME} berhasil dibuat!${NC}"
  
  # Membuat firewall rules
  echo -e "\n${BLUE}Membuat firewall rules...${NC}"
  
  # HTTP dan HTTPS sudah tercakup oleh aturan GCP default, tapi kita akan memeriksa dan membuat jika diperlukan
  
  # Allow app ports (80, 3000, 8000, 8443)
  echo -e "${YELLOW}Membuat firewall rule untuk port aplikasi (80, 3000, 8000, 8443)...${NC}"
  gcloud compute firewall-rules create allow-app-ports \
    --project=$PROJECT_ID \
    --direction=INGRESS \
    --priority=1000 \
    --network=default \
    --action=ALLOW \
    --rules=tcp:80,tcp:3000,tcp:8000,tcp:8443 \
    --source-ranges=0.0.0.0/0 \
    --target-tags=http-server \
    || echo -e "${YELLOW}Firewall rule allow-app-ports sudah ada atau gagal dibuat.${NC}"
  
  # Allow HTTPS
  echo -e "${YELLOW}Membuat firewall rule untuk HTTPS (443)...${NC}"
  gcloud compute firewall-rules create allow-https \
    --project=$PROJECT_ID \
    --direction=INGRESS \
    --priority=1000 \
    --network=default \
    --action=ALLOW \
    --rules=tcp:443 \
    --source-ranges=0.0.0.0/0 \
    --target-tags=https-server \
    || echo -e "${YELLOW}Firewall rule allow-https sudah ada atau gagal dibuat.${NC}"
  
  # Allow Supabase (54322)
  echo -e "${YELLOW}Membuat firewall rule untuk Supabase (54322)...${NC}"
  gcloud compute firewall-rules create allow-supabase \
    --project=$PROJECT_ID \
    --direction=INGRESS \
    --priority=1000 \
    --network=default \
    --action=ALLOW \
    --rules=tcp:54322 \
    --source-ranges=0.0.0.0/0 \
    --target-tags=allow-supabase \
    || echo -e "${YELLOW}Firewall rule allow-supabase sudah ada atau gagal dibuat.${NC}"
  
  # Allow Telegram (8444)
  echo -e "${YELLOW}Membuat firewall rule untuk Telegram (8444)...${NC}"
  gcloud compute firewall-rules create allow-telegram \
    --project=$PROJECT_ID \
    --direction=INGRESS \
    --priority=1000 \
    --network=default \
    --action=ALLOW \
    --rules=tcp:8444 \
    --source-ranges=0.0.0.0/0 \
    --target-tags=allow-telegram \
    || echo -e "${YELLOW}Firewall rule allow-telegram sudah ada atau gagal dibuat.${NC}"
  
  # Allow Backend (2025)
  echo -e "${YELLOW}Membuat firewall rule untuk Backend (2025)...${NC}"
  gcloud compute firewall-rules create allow-backend \
    --project=$PROJECT_ID \
    --direction=INGRESS \
    --priority=1000 \
    --network=default \
    --action=ALLOW \
    --rules=tcp:2025 \
    --source-ranges=0.0.0.0/0 \
    || echo -e "${YELLOW}Firewall rule allow-backend sudah ada atau gagal dibuat.${NC}"
    
  # Allow Grafana (2027)
  echo -e "${YELLOW}Membuat firewall rule untuk Grafana (2027)...${NC}"
  gcloud compute firewall-rules create allow-grafana \
    --project=$PROJECT_ID \
    --direction=INGRESS \
    --priority=1000 \
    --network=default \
    --action=ALLOW \
    --rules=tcp:2027 \
    --source-ranges=0.0.0.0/0 \
    --target-tags=allow-grafana \
    || echo -e "${YELLOW}Firewall rule allow-grafana sudah ada atau gagal dibuat.${NC}"
    
  # Allow Prometheus (9090) dan exporters (9121, 9100)
  echo -e "${YELLOW}Membuat firewall rule untuk Prometheus (9090, 9121, 9100)...${NC}"
  gcloud compute firewall-rules create allow-prometheus \
    --project=$PROJECT_ID \
    --direction=INGRESS \
    --priority=1000 \
    --network=default \
    --action=ALLOW \
    --rules=tcp:9090,tcp:9121,tcp:9100 \
    --source-ranges=0.0.0.0/0 \
    --target-tags=allow-prometheus \
    || echo -e "${YELLOW}Firewall rule allow-prometheus sudah ada atau gagal dibuat.${NC}"
  
  echo -e "${GREEN}Firewall rules berhasil dibuat!${NC}"
  
  # Setup SSH untuk VSCode
  setup_ssh
  
  # Menampilkan detail VM
  echo -e "\n${BLUE}Detail VM Instance:${NC}"
  show_vm_status
}

# Fungsi untuk mengatur SSH untuk VSCode Remote
setup_ssh() {
  if ! vm_exists; then
    echo -e "${RED}Error: VM instance ${VM_NAME} tidak ada!${NC}"
    echo -e "${YELLOW}Buat VM terlebih dahulu dengan './gcp.sh create'.${NC}"
    exit 1
  fi

  echo -e "${BLUE}Mengatur SSH untuk VSCode Remote Access...${NC}"

  # Mendapatkan IP VM
  EXTERNAL_IP=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --project=$PROJECT_ID --format="get(networkInterfaces[0].accessConfigs[0].natIP)")

  if [ -z "$EXTERNAL_IP" ]; then
    echo -e "${RED}Error: Tidak bisa mendapatkan IP eksternal VM.${NC}"
    exit 1
  fi

  # Cek apakah konfigurasi sudah ada di SSH config
  if grep -q "Host $VM_NAME" "$SSH_CONFIG_PATH" 2>/dev/null; then
    echo -e "${YELLOW}Konfigurasi SSH untuk $VM_NAME sudah ada, memperbarui...${NC}"
    # Update IP jika sudah ada
    sed -i '' "/Host $VM_NAME/,/^$/s/HostName .*/HostName $EXTERNAL_IP/" "$SSH_CONFIG_PATH"
  else
    echo -e "${YELLOW}Menambahkan konfigurasi SSH baru untuk $VM_NAME...${NC}"
    # Tambahkan konfigurasi baru
    cat << EOF >> "$SSH_CONFIG_PATH"

# GCP VM $VM_NAME configuration for VSCode Remote SSH
Host $VM_NAME
  HostName $EXTERNAL_IP
  User $SSH_USER
  IdentityFile /Users/esakrissa/.ssh/remote-agen-travel
  StrictHostKeyChecking no
  UserKnownHostsFile /dev/null

EOF
  fi

  # Menyetel izin yang benar pada config
  chmod 600 "$SSH_CONFIG_PATH"

  echo -e "${GREEN}Konfigurasi SSH untuk VSCode Remote berhasil diatur!${NC}"
  echo -e "${YELLOW}Gunakan perintah berikut untuk terhubung:${NC} ssh $VM_NAME"
  echo -e "${YELLOW}atau gunakan VSCode Remote Explorer dengan memilih host ${VM_NAME}${NC}"
}

# Fungsi untuk menampilkan status dan detail VM
show_vm_status() {
  if ! vm_exists; then
    echo -e "${RED}Error: VM instance ${VM_NAME} tidak ada!${NC}"
    exit 1
  fi
  
  echo -e "${BLUE}Memeriksa status VM instance ${VM_NAME} di zona ${ZONE}...${NC}"
  
  # Mendapatkan detail VM
  VM_INFO=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --project=$PROJECT_ID --format=json)
  
  # Mendapatkan status
  STATUS=$(echo $VM_INFO | jq -r '.status')
  echo -e "${GREEN}Status: ${STATUS}${NC}"
  
  # Mendapatkan tipe mesin
  MACHINE_TYPE_FULL=$(echo $VM_INFO | jq -r '.machineType')
  MACHINE_TYPE_SHORT=$(basename $MACHINE_TYPE_FULL)
  echo -e "${GREEN}Tipe Mesin: ${MACHINE_TYPE_SHORT}${NC}"
  
  # Mendapatkan zona
  ZONE_FULL=$(echo $VM_INFO | jq -r '.zone')
  ZONE_SHORT=$(basename $ZONE_FULL)
  echo -e "${GREEN}Zona: ${ZONE_SHORT}${NC}"
  
  # Mendapatkan IP eksternal
  EXTERNAL_IP=$(echo $VM_INFO | jq -r '.networkInterfaces[0].accessConfigs[0].natIP')
  echo -e "${GREEN}IP Eksternal: ${EXTERNAL_IP}${NC}"
  
  # Mendapatkan IP internal
  INTERNAL_IP=$(echo $VM_INFO | jq -r '.networkInterfaces[0].networkIP')
  echo -e "${GREEN}IP Internal: ${INTERNAL_IP}${NC}"
  
  # Mendapatkan sistem operasi
  OS_LICENSE=$(echo $VM_INFO | jq -r '.disks[0].licenses[0]')
  OS_NAME=$(basename $OS_LICENSE)
  echo -e "${GREEN}Sistem Operasi: ${OS_NAME}${NC}"
  
  # Mendapatkan ukuran disk
  DISK_SIZE=$(echo $VM_INFO | jq -r '.disks[0].diskSizeGb')
  echo -e "${GREEN}Ukuran Disk: ${DISK_SIZE} GB${NC}"
  
  # Mendapatkan tag
  TAGS=$(echo $VM_INFO | jq -r '.tags.items[]' 2>/dev/null || echo "Tidak ada")
  echo -e "${GREEN}Tags: ${TAGS}${NC}"
  
  # Menampilkan SSH connection info
  echo -e "${GREEN}SSH Connection: ${SSH_USER}@${EXTERNAL_IP}${NC}"
  
  # Menampilkan firewall rules
  echo -e "\n${BLUE}Firewall Rules:${NC}"
  gcloud compute firewall-rules list \
    --project=$PROJECT_ID \
    --format="table(name, direction, priority, sourceRanges.list(), allowed.list(), targetTags.list())"
}

# Fungsi untuk menghapus VM dan resource terkait
delete_vm() {
  echo -e "${RED}PERINGATAN: Ini akan menghapus VM instance ${VM_NAME} dan mungkin menghapus firewall rules terkait.${NC}"
  echo -e "${YELLOW}Apakah Anda yakin ingin melanjutkan? [y/N]${NC}"
  read -r confirm
  
  if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo -e "${BLUE}Operasi dibatalkan.${NC}"
    exit 0
  fi
  
  # Memeriksa apakah VM ada
  if ! vm_exists; then
    echo -e "${RED}Error: VM instance ${VM_NAME} tidak ada!${NC}"
    exit 1
  fi
  
  echo -e "${BLUE}Menghapus VM instance ${VM_NAME}...${NC}"
  gcloud compute instances delete $VM_NAME \
    --project=$PROJECT_ID \
    --zone=$ZONE \
    --quiet
  
  VM_DELETE_STATUS=$?
  
  if [ $VM_DELETE_STATUS -ne 0 ]; then
    echo -e "${RED}Error: Gagal menghapus VM instance!${NC}"
    exit 1
  fi
  
  echo -e "${GREEN}VM instance ${VM_NAME} berhasil dihapus!${NC}"
  
  # Tanyakan apakah ingin menghapus SSH config dari file config
  echo -e "${YELLOW}Apakah Anda ingin menghapus konfigurasi SSH untuk VM ini dari ~/.ssh/config? [y/N]${NC}"
  read -r confirm_ssh
  
  if [[ "$confirm_ssh" == "y" || "$confirm_ssh" == "Y" ]]; then
    if grep -q "Host $VM_NAME" "$SSH_CONFIG_PATH" 2>/dev/null; then
      echo -e "${BLUE}Menghapus konfigurasi SSH untuk ${VM_NAME}...${NC}"
      # Menghapus blok konfigurasi VM dari file config
      sed -i '' "/# GCP VM $VM_NAME configuration for VSCode Remote SSH/,/^$/d" "$SSH_CONFIG_PATH"
      echo -e "${GREEN}Konfigurasi SSH untuk ${VM_NAME} berhasil dihapus.${NC}"
    else
      echo -e "${YELLOW}Tidak ada konfigurasi SSH untuk ${VM_NAME} dalam file.${NC}"
    fi
  fi
  
  echo -e "${YELLOW}Apakah Anda ingin menghapus custom firewall rules juga? [y/N]${NC}"
  read -r confirm_fw
  
  if [[ "$confirm_fw" == "y" || "$confirm_fw" == "Y" ]]; then
    echo -e "${BLUE}Menghapus custom firewall rules...${NC}"
    
    # Daftar custom firewall rules untuk dihapus
    FW_RULES=("allow-app-ports" "allow-https" "allow-supabase" "allow-telegram" "allow-backend" "allow-grafana" "allow-prometheus")
    
    for rule in "${FW_RULES[@]}"; do
      echo -e "${YELLOW}Menghapus firewall rule: $rule${NC}"
      gcloud compute firewall-rules delete $rule --project=$PROJECT_ID --quiet || echo -e "${YELLOW}Firewall rule $rule tidak ada atau gagal dihapus.${NC}"
    done
    
    echo -e "${GREEN}Custom firewall rules berhasil dihapus!${NC}"
  fi
  
  echo -e "${GREEN}Semua resource yang ditentukan telah berhasil dihapus!${NC}"
}

# Script utama
if [ $# -eq 0 ]; then
  usage
fi

case "$1" in
  create)
    create_vm
    ;;
  status)
    show_vm_status
    ;;
  delete)
    delete_vm
    ;;
  setup-ssh)
    setup_ssh
    ;;
  *)
    usage
    ;;
esac 