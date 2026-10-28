[app]
​(str) Title of your application
​title = Cipher Chess Tournament
​(str) Package name
​package.name = cipherchesstournament
​(str) Package domain (needed for android/ios packaging)
​package.domain = com.cipher.chess
​(str) Source code where the main.py live
​source.dir = .
​(list) Source files to include (let empty to include all the files)
​source.include_exts = py,png,jpg,ttf,kv,json
​(list) List of inclusions using pattern matching
​source.include_patterns = assets/,core/
​(list) Source files to exclude (let empty to not exclude anything)
​source.exclude_dirs = tests, bin, .buildozer, .git
​(str) Application versioning (method 1)
​version = 1.0.0
​(list) Application requirements
​comma separated e.g. requirements = sqlite3,kivy
​requirements = python3,kivy,pyjnius
​(str) Custom source folders for requirements
​Sets custom source for any requirement with recipes or site-packages
​requirements.source.kivy = ../kivy
​(list) Garden requirements
​#garden_requirements =
​(str) Presplash of the application
​presplash.filename = logo.png
​(str) Icon of the application
​icon.filename = cipher.png
​(str) Supported orientations (landscape, sensorLandscape, portrait or all)
​orientation = portrait
​(bool) Indicate if the application should be fullscreen or not
​fullscreen = 0
​(list) Permissions
​android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE
​(int) Target Android API, should be as high as possible.
​android.api = 33
​(int) Minimum API your APK / AAB will support.
​android.minapi = 21
​(int) Android NDK version
​android.ndk = 25b
​(bool) Use --private data storage (True) or --dir public storage (False)
​android.private_storage = True
​(str) Android NDK directory (if empty, it will be automatically downloaded.)
​android.ndk_path =
​(str) Android SDK directory (if empty, it will be automatically downloaded.)
​android.sdk_path =
​(list) List of Java .jar files to add to the libs so that pyjnius can access
​android.add_jars = foo.jar,bar.jar,libs/eightables.jar
​(list) Android architectures to build for
​android.archs = arm64-v8a, armeabi-v7a
​(bool) Enable AndroidX support. Required for NDK 22+
​android.enable_androidx = True
​[buildozer]
​(int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
​log_level = 2
​(int) Display warning if buildozer is run as root (0 = false, 1 = true)
​warn_on_root = 1
