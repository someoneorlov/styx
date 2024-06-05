FROM nginx:1.24.0
COPY ./styx_app/nginx/nginx.conf /etc/nginx/nginx.conf
COPY ./styx_app/nginx/default.conf /etc/nginx/conf.d/default.conf
# COPY --from=frontend_test /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
