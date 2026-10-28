[app]
title = Cipher Chess Tournament
package.name = cipherchesstournament
package.domain = mx.cipher
source.dir = .
source.include_exts = py,png,jpg,ttf,kv,json
version = 1.0.0
​requirements = python3,kivy
​orientation = portrait
fullscreen = 0
icon.filename = %(source.dir)s/logo.png
​android.archs = arm64-v8a
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25b
android.accept_sdk_license = True
​[buildozer]
log_level = 2
warn_on_root = 0
