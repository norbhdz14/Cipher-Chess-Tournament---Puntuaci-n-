# ♟️ Cipher Chess Tournament

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/T4T629IUEU)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Kivy](https://img.shields.io/badge/Kivy-UI-3776AB?logo=kivy&logoColor=white)](https://kivy.org/)
[![Android](https://img.shields.io/badge/Platform-Android_arm64--v8a-3DDC84?logo=android&logoColor=white)](https://www.android.com/)
[![Build APK](https://github.com/Norbhdz14/cipher-chess-tournament/actions/workflows/build.yml/badge.svg)](https://github.com/Norbhdz14/cipher-chess-tournament/actions)

**Cipher Chess Tournament** es una aplicación móvil nativa para Android diseñada para la gestión integral de torneos de ajedrez bajo el **Sistema Suizo**, emparejamientos dinámicos, desempates automáticos y un **reloj digital de ajedrez integrado** con controles de tiempo estándar (Fischer).

Desarrollada bajo la filosofía de software libre y liviano, está construida en **Python** con el framework gráfico **Kivy**, utilizando un modelo de arquitectura desacoplada donde el motor de lógica pura opera de manera independiente a la interfaz de usuario.

---

## 🚀 Características Principales

* 🏆 **Sistema Suizo Automatizado:**
  * Algoritmo de emparejamiento inteligente (minimiza repetición de rivales y equilibra la asignación de colores blanco/negro).
  * Gestión de descansos (*byes*) automáticos de 1 punto para torneos con número impar de participantes.
* 📊 **Desempates Automáticos:**
  * Cálculo dinámico e instantáneo de puntos, **Buchholz**, **Sonneborn-Berger** y cantidad de victorias/tablas/derrotas.
* ⏱️ **Reloj de Ajedrez Integrado:**
  * Reloj de dos lados con rotación de 180° para el jugador oponente.
  * Sincronizado con `time.monotonic()` (precisión garantizada incluso si el sistema pierde fotogramas).
  * Controles de tiempo estándar: Bullet (1+0, 2+1), Blitz (3+2, 5+0), Rápida (10+0, 15+10, 30+0) y Clásico (90+30).
  * Registro e integración directa de caídas de tiempo (bandera) hacia la mesa vinculada.
  * Mantención de pantalla encendida (`FLAG_KEEP_SCREEN_ON`) durante las partidas.
* 📄 **Historial y Reportes:**
  * Centro de datos con gráficas de barras integradas (*Top 6*).
  * Exportación de resultados e historial a formatos **TXT** y **CSV** (compatible con Excel/UTF-8 BOM) para la tabla de clasificación y las partidas por ronda.
* 🎨 **Interfaz de Usuario (UI) Adaptativa:**
  * Tema oscuro y claro con soporte bilingüe (**Español** e **Inglés**).
  * Arquitectura `@blindado`: protección total contra excepciones en UI para garantizar la estabilidad de la app durante los torneos.

---

## 🛠️ Requisitos e Instalación

### Descargar APK para Android
Puedes descargar el paquete ejecutable `.apk` directamente desde la pestaña de **[Releases](https://github.com/Norbhdz14/cipher-chess-tournament/releases)** o desde los artefactos generados automáticamente en **GitHub Actions**.

​👤 Autor y Créditos

​Desarrollado por Ing. Norberto Hernández
​Cédula profesional: 15061201
​Cipher · Sistemas Computacionales & IoT
​Arandas, Jalisco, México.
​📩 Telegram: t.me/CipherlosAltos
​🌐 Blog: norbhdz.blogspot.com
​🐙 GitHub: @Norbhdz14

​🤝 Apoya el Proyecto
​Cipher Chess Tournament es una herramienta gratuita y de código abierto desarrollada para apoyar a la comunidad ajedrecista e impulsada por el entusiasmo al deporte ciencia. Si esta aplicación te ha sido de utilidad para organizar tus torneos o partidas, considera apoyar el desarrollo continuo: [![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/T4T629IUEU)

​📄 Licencia

​Este proyecto se distribuye bajo la licencia MIT. Consulta el archivo LICENSE para obtener más información.
