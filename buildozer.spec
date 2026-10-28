[app]
title = Cipher Chess Tournament
package.name = chesstournament
package.domain = org.cipher
source.dir = .
# ttf: imprescindible para que la fuente Noto Sans viaje dentro del APK
source.include_exts = py,png,jpg,ttf,otf,json
version = 1.0.0
requirements = python3,kivy==2.3.0,pyjnius
orientation = portrait
fullscreen = 0
icon.filename = %(source.dir)s/logo.png
presplash.filename = %(source.dir)s/cipher.png
android.permissions = WRITE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
