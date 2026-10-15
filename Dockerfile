# Two stages.
#
#   blog   renders blog/*.md into site/blog/
#   nginx  serves the result
#
# Doing it at build time rather than in the browser keeps the pages indexable
# and leaves the runtime image a plain static nginx with no Node, no Python and
# no transpiler. The site ships no third-party JavaScript at all.

FROM python:3.12-alpine AS blog
WORKDIR /build
COPY requirements-blog.txt ./
RUN pip install --no-cache-dir -r requirements-blog.txt
COPY scripts/ scripts/
COPY blog/ blog/
COPY site/ site/
RUN python scripts/build_blog.py

FROM nginx:alpine
# Only site/ crosses over, so the Markdown sources and the toolchain stay out
# of the published image.
COPY --from=blog /build/site/ /usr/share/nginx/html/
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
