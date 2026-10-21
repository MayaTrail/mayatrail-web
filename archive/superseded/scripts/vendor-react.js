#!/usr/bin/env node
/**
 * Copy the React UMD production builds out of node_modules into site/vendor/.
 *
 * The run page used to pull react, react-dom and @babel/standalone from unpkg
 * and compile JSX in the visitor's browser on every load. Serving our own copies
 * takes a third-party CDN off the critical path, and the *production* builds are
 * a fraction of the development ones the page used to load.
 *
 * site/vendor/ is generated output and git-ignored; the Docker builder stage
 * regenerates it on every deploy.
 */
'use strict';

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'site', 'vendor');

const FILES = [
  ['react', 'umd/react.production.min.js'],
  ['react-dom', 'umd/react-dom.production.min.js'],
];

fs.mkdirSync(OUT, { recursive: true });

for (const [pkg, rel] of FILES) {
  const src = path.join(ROOT, 'node_modules', pkg, rel);
  if (!fs.existsSync(src)) {
    console.error(`error: ${src} not found - run npm install first`);
    process.exit(1);
  }
  const dest = path.join(OUT, path.basename(rel));
  fs.copyFileSync(src, dest);
  const kb = (fs.statSync(dest).size / 1024).toFixed(1);
  console.log(`vendored ${path.basename(rel)} (${kb} KB)`);
}
