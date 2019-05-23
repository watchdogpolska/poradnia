FROM node:8
WORKDIR /app
VOLUME /app
COPY .contrib/docker/docker-entrypoint.gulp.sh /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["npx", "gulp"]
