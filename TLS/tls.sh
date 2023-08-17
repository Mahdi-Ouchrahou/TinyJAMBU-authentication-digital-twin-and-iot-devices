#!/bin/bash

# Step 1: Create a Key Pair for the CA
openssl genrsa -out ca.key 2048

# Step 2: Create a Certificate for the CA
openssl req -new -x509 -days 1826 -key ca.key -out ca.crt

# Step 3: Create a Server Key Pair
openssl genrsa -out server.key 2048

# Step 4: Create a Certificate Request (.csr) for the Server
openssl req -new -out server.csr -key server.key

# Step 5: Verify and Sign the Server Certificate with SAN
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 360 -extfile <(printf "subjectAltName=IP:192.168.0.174")

# Step 6: Organize Your Certificate Files
mkdir -p certs
mv ca.crt certs/
mv server.crt certs/
mv server.key certs/

echo "Certificates generated successfully."
