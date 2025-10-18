#!/bin/bash

set -e

show_menu() {
  clear
  echo "=== Expiration Inspector Menu ==="
  echo "1) Validate today's date"
  echo "2) List valid expirations"
  echo "3) Show next valid expiration"
  echo "4) Show expiration summary"
  echo "5) Exit"
  echo
}

while true; do
  show_menu
  read -rp "Select an option: " choice
  case $choice in
    1) python3 core/expiration_inspector.py validate ;;
    2) python3 core/expiration_inspector.py list ;;
    3) python3 core/expiration_inspector.py next ;;
    4) python3 core/expiration_inspector.py summary ;;
    5) echo "Goodbye"; exit 0 ;;
    *) echo "Invalid choice. Try again."; sleep 1 ;;
  esac
done