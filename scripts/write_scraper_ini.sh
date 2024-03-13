#!/bin/bash

IFS='|' read -ra ADDR <<< "$1"

counter=0
for i in "${ADDR[@]}"; do
    filename="SCRAPER_${counter}.ini"
    echo "[tokens]" > $filename
    echo "session_token = ${ADDR[$counter]}" >> $filename
    echo "gtoken = randomText" >> $filename
    echo "bullet_token = randomText" >> $filename
    echo "" >> $filename
    echo "[data]" >> $filename
    echo "country = US" >> $filename
    echo "language = en-US" >> $filename
    echo "" >> $filename
    echo "[options]" >> $filename
    echo -e "f_token_url = https://nxapi-znca-api.fancy.org.uk/api/znca/f,https://api.imink.app/f" >> $filename
    counter=$((counter+1))
done