##############################
#               
# TEST ENVIRIONMENT
#
##############################
# Comment in/out when ready

FROM nginx
COPY ./nginx/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80

##############################
#               
# PRODUCTION ENVIRIONMENT
#
##############################
# Comment in/out when ready

# FROM node:18 AS build
# WORKDIR /app
# COPY ./client/package.json ./client/package-lock.json ./
# RUN npm install
# COPY ./client ./
# RUN npm run build

# FROM nginx
# COPY --from=build /app/dist /usr/share/nginx/html
# COPY ./nginx/nginx.conf /etc/nginx/conf.d/default.conf
# EXPOSE 80