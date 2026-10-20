#!/usr/bin/env python3
"""Local Maven read-through bridge for build environments with JVM HTTPS restrictions.

All upstream artifact bytes come from public Maven repositories. The bridge is
only exposed on 127.0.0.1 and never accepts uploads or arbitrary URLs.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen
import os
import sys
import threading
import urllib.parse

ROOT = Path(__file__).resolve().parents[3] / '.ymdsh-toolchains' / 'maven-cache'
ROOT.mkdir(parents=True, exist_ok=True)
GOOGLE = ('https://maven.google.com/', 'https://maven.aliyun.com/repository/google/')
CENTRAL = ('https://repo.maven.apache.org/maven2/', 'https://maven.aliyun.com/repository/central/')
JITPACK = ('https://jitpack.io/',)
MOZILLA = ('https://maven.mozilla.org/maven2/',)


def sources(path):
    if path.startswith(('com/android/', 'androidx/', 'com/google/android/material/',
                        'com/google/android/gms/', 'com/google/android/libraries/')):
        return GOOGLE
    if path.startswith('org/mozilla/'):
        return MOZILLA + CENTRAL
    if path.startswith('com/termux/'):
        return JITPACK + CENTRAL
    return CENTRAL + GOOGLE


class Handler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.handle_artifact(True)

    def do_GET(self):
        self.handle_artifact(False)

    def handle_artifact(self, head_only):
        path = urllib.parse.unquote(self.path.split('?', 1)[0]).lstrip('/')
        if not path or '..' in path.split('/') or '\\' in path or ':' in path:
            self.send_error(400)
            return
        # Gradle plugin marker artifacts are POM-only. An implicit .jar HEAD
        # otherwise makes Gradle wait for two slow negative upstream lookups.
        if '.gradle.plugin/' in path and path.endswith('.jar'):
            self.send_error(404)
            return
        target = ROOT / path
        if target.is_file():
            data = target.read_bytes()
        else:
            data = None
            failures = []
            for base in sources(path):
                try:
                    with urlopen(base + urllib.parse.quote(path, safe='/@.+-'), timeout=40) as response:
                        data = response.read()
                    break
                except HTTPError as error:
                    failures.append(str(error.code))
                    continue
                except (URLError, TimeoutError, OSError) as error:
                    failures.append(type(error).__name__)
                    continue
            if data is None:
                print('MISSING', path, ','.join(failures), flush=True)
                self.send_error(404)
                return
            target.parent.mkdir(parents=True, exist_ok=True)
            temp = target.with_name(target.name + '.part-' + str(threading.get_ident()))
            temp.write_bytes(data)
            os.replace(temp, target)
            print('CACHED', path, len(data), flush=True)
        self.send_response(200)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Content-Type', 'application/octet-stream')
        self.end_headers()
        if not head_only:
            self.wfile.write(data)

    def log_message(self, format, *args):
        pass


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 19764
    print(f'Maven bridge listening at 127.0.0.1:{port}', flush=True)
    ThreadingHTTPServer(('127.0.0.1', port), Handler).serve_forever()
