# Three stages.
#
#   jsx   compiles site/scripts/run-experience.jsx and vendors React
#   blog  renders blog/*.md into site/blog/, the IR playbook Markdown embedded
#         in site/playbook.html, and any committed run recording into
#         site/run.html
#   nginx serves the result
#
# Doing all of it at build time rather than in the browser keeps the pages
# indexable, takes unpkg and jsdelivr off the critical path, and leaves the
# runtime image a plain static nginx with no Node, no Python and no transpiler.

FROM node:20-alpine AS jsx
WORKDIR /build
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY scripts/vendor-react.js scripts/
COPY site/scripts/run-experience.jsx site/scripts/
RUN npm run build

FROM python:3.12-alpine AS blog
WORKDIR /build
COPY requirements-blog.txt ./
RUN pip install --no-cache-dir -r requirements-blog.txt
COPY scripts/ scripts/
COPY blog/ blog/
COPY recordings/ recordings/
COPY site/ site/
# the compiled run experience and the vendored React, from the stage above
COPY --from=jsx /build/site/scripts/run-experience.js site/scripts/
COPY --from=jsx /build/site/vendor/ site/vendor/
RUN python scripts/build_blog.py && python scripts/build_playbook.py && python scripts/build_run.py
# The JSX is build input, not a published asset - the compiled .js is what the
# page loads, so drop the source before it can cross into the runtime image.
RUN rm -f site/scripts/run-experience.jsx

FROM nginx:alpine
# Only site/ crosses over, so the Markdown sources, the JSX and both
# toolchains stay out of the published image.
COPY --from=blog /build/site/ /usr/share/nginx/html/
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
