#!/bin/bash

# Script untuk menghidupkan dan mematikan VM instance GCP
# Penggunaan: ./vm_control.sh [start|stop]

# Konfigurasi VM
VM_NAME="agen-travel"
ZONE="asia-southeast2-a"

# Fungsi untuk menampilkan bantuan
show_help() {
    echo "Penggunaan: $0 [start|stop|status]"
    echo "  start  : Menghidupkan VM instance"
    echo "  stop   : Mematikan VM instance"
    echo "  status : Memeriksa status VM instance"
}

# Fungsi untuk menghidupkan VM
start_vm() {
    echo "Menghidupkan VM instance $VM_NAME di zona $ZONE..."
    gcloud compute instances start $VM_NAME --zone=$ZONE
    
    if [ $? -eq 0 ]; then
        echo "VM berhasil dihidupkan."
        # Mendapatkan IP eksternal VM
        IP=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
        echo "IP Eksternal: $IP"
    else
        echo "Gagal menghidupkan VM."
    fi
}

# Fungsi untuk mematikan VM
stop_vm() {
    echo "Mematikan VM instance $VM_NAME di zona $ZONE..."
    gcloud compute instances stop $VM_NAME --zone=$ZONE
    
    if [ $? -eq 0 ]; then
        echo "VM berhasil dimatikan."
    else
        echo "Gagal mematikan VM."
    fi
}

# Fungsi untuk memeriksa status VM
check_status() {
    echo "Memeriksa status VM instance $VM_NAME di zona $ZONE..."
    STATUS=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --format='get(status)')
    
    echo "Status VM: $STATUS"
    
    if [ "$STATUS" == "RUNNING" ]; then
        # Mendapatkan IP eksternal VM
        IP=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
        echo "IP Eksternal: $IP"
    fi
}

# Memeriksa argumen
if [ $# -eq 0 ]; then
    show_help
    exit 1
fi

# Menjalankan perintah berdasarkan argumen
case "$1" in
    start)
        start_vm
        ;;
    stop)
        stop_vm
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