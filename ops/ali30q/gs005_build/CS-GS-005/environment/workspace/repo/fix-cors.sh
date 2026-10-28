# Fix CORS configuration
# Replace the incorrect CORS header with proper origin matching

# Find and replace CORS configuration in API server block
sudo sed -i '/# CORS Headers (for API)/,/add_header Access-Control-Allow-Credentials/c\
    # CORS Headers (for API) - Allow both nautilus.social and www.nautilus.social\
    set $cors_origin "";\
    if ($http_origin ~* "^https://(www\\.)?nautilus\\.social$") {\
        set $cors_origin $http_origin;\
    }\
    add_header Access-Control-Allow-Origin $cors_origin always;\
    add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;\
    add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;\
    add_header Access-Control-Allow-Credentials "true" always;' /etc/nginx/sites-available/nautilus-social

# Test and reload
sudo nginx -t && sudo systemctl reload nginx
