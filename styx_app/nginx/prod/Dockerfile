FROM nginx:1.24.0
COPY ./styx_app/nginx/prod/nginx.conf /etc/nginx/nginx.conf
COPY ./styx_app/nginx/prod/default.conf /etc/nginx/conf.d/default.conf
# Adjust the COPY command to match the new structure
COPY ./styx_app/frontend/prod/build /usr/share/nginx/html
# If you decide to include fallback.html in your Nginx served pages
COPY ./styx_app/nginx/common/fallback.html /usr/share/nginx/html
