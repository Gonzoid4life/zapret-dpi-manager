<div align="center">

# ⚡ Zapret DPI Manager

**Современный и минималистичный графический интерфейс (GUI) для управления [zapret-discord-youtube](https://github.com/Flowseal/zapret-discord-youtube) от Flowseal.**

[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011%20x64-0078D4?style=flat-square&logo=windows)](https://github.com/)
[![UI](https://img.shields.io/badge/UI-Fluent%202%20%2F%20CustomTkinter-blueviolet?style=flat-square)](https://github.com/TomSchimansky/CustomTkinter)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python)](https://python.org)
[![Vibe Coding](https://img.shields.io/badge/Crafted%20with-Vibe%20Coding%20✨-FF6F00?style=flat-square)](https://en.wikipedia.org/wiki/Vibe_coding)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

[🇷🇺 Читать на русском](#-русская-версия) &nbsp;&bull;&nbsp; [🇬🇧 Read in English](#-english-version)

</div>

---

## 🇷🇺 Русская версия

**Zapret DPI Manager** — это удобная легковесная панель управления для сборки `zapret-discord-youtube` (разработчик Flowseal) на базе оригинального пакета `zapret` (bol-van) и драйвера `WinDivert`.

Вместо ручного редактирования bat-файлов, консоли служб Windows и перезапусков через командную строку — единый современный интерфейс в стиле **Windows 11 Fluent 2** с поддержкой тёмной, светлой и системной тем оформления (автоматическая адаптация под Windows), автоподбором стратегий и встроенным редактором списков.

> [!NOTE]
> 💡 **Проект создан методом Vibe Coding:**
> Архитектура, интерфейс и логика приложения созданы в тандеме человека и ИИ (AI-assisted Vibe Coding). Идея — закрыть реальные повседневные потребности пользователей без громоздких фреймворков (Electron/Webview) и лишних скрытых функций, оставив только чистый, быстрый и отзывчивый Python-код.

---

### ✨ Ключевые возможности

* 🎨 **Адаптивный дизайн (Fluent 2):**
  * Полноценная поддержка **тёмной**, **светлой** и **системной** тем оформления (автоматически переключается вместе с темой Windows).
  * Плавные микро-анимации при наведении и выверенная типографика (Segoe UI Variable).

* 🚀 **Управление службой в 1 клик:**
  * Установка, запуск, остановка и перезапуск службы Windows `zapret`.
  * Режим интерактивного запуска (консоль) и фонового сервиса.
  * Автоматический мониторинг статуса службы в реальном времени.

* 🎯 **Умное переключение стратегий обхода:**
  * Автоматическое сканирование всех bat-стратегий из папки Zapret.
  * Понятные человекочитаемые названия стратегий без каши из аргументов командной строки.
  * Бесшовное переключение стратегии "на лету" с автоперезапуском службы.

* ⚡ **Автоподбор стратегий (Автотюн):**
  * Встроенный бенчмарк пинга и доступности ключевых узлов (YouTube, Discord Gateway/Voice, CDN).
  * Наглядный рейтинг стратегий по задержке и стабильности (🥇 Золото, 🥈 Серебро, 🥉 Бронза).
  * Автоматический выбор оптимального варианта для вашего провайдера.

* 🎮 **Умный игровой режим (Low-Latency Bypass):**
  * Защита игрового UDP-трафика от задержек и джиттера.
  * Автоматический пинг-мониторинг для соревновательных игр (CS2, Valorant, Apex, Dota 2).

* 📋 **Встроенный редактор списков правил:**
  * Вкладки для прямого редактирования `list-general-user.txt` (обход), `list-exclude-user.txt` (исключения) и `ipset-exclude-user.txt`.
  * Удобный поиск по доменам, счетчик активных строк.
  * Окно «Быстрое добавление» с автоматической очисткой ссылок до чистого домена.
  * **Высококонтрастный инвертированный курсор (I-Beam)** — указатель мыши больше никогда не теряется на тёмном фоне.
  * Быстрая смена фейк-пакетов (Discord UDP Fake, Game UDP Fake) из выпадающего меню.

* 🛠️ **Диагностика и сетевые инструменты:**
  * Очистка кэша DNS (`ipconfig /flushdns` в один клик).
  * Мгновенный тест доступности любого сайта через активный обход.
  * Выкатная шторка с логами работы программы и службы в реальном времени.
  * Сворачивание в системный трей Windows.

---

### 📦 Использование и установка

#### Вариант 1: Готовый бинарник (Рекомендуется)
1. Скачайте `ZapretManager.exe` из раздела [Releases](https://github.com/).
2. Поместите `ZapretManager.exe` в папку с установленным `zapret-discord-youtube` (рядом с bat-файлами стратегий).
3. Запустите от имени администратора. Программа автоматически подхватит все настройки и списки!

#### Вариант 2: Запуск из исходного кода (Python)
Требуется Python 3.10+ x64:
```bash
# Клонируйте репозиторий
git clone https://github.com/YOUR_USERNAME/zapret-manager.git
cd zapret-manager

# Установите зависимости
pip install customtkinter pystray pillow requests urllib3

# Запустите приложение
python src/main.py
```

#### Сборка в один .exe файл
Для самостоятельной компиляции используется `PyInstaller`:
```bash
pip install pyinstaller
python build_main.py
```
Собранный файл появится в папке `dist/ZapretManager.exe`.

---

### 🙏 Благодарности и сторонние компоненты (Credits)

Этот проект является надстройкой и GUI-оболочкой. Выражаем огромную благодарность авторам ключевых технологий:

* **[Flowseal](https://github.com/Flowseal)** — за превосходную, самую популярную сборку **[zapret-discord-youtube](https://github.com/Flowseal/zapret-discord-youtube)**, подобранные стратегии обхода и постоянную адаптацию под российские реалии.
* **[bol-van](https://github.com/bol-van)** — автору легендарного комплекса **[zapret](https://github.com/bol-van/zapret)**, лежащего в основе всех современных решений DPI-обхода.
* **[basil00 / reqrypt](https://reqrypt.org/windivert.html)** — создателям драйвера перехвата пакетов ядра **WinDivert**.
* **[Tom Schimansky](https://github.com/TomSchimansky)** — за библиотеку **[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)**, позволяющую создавать нативный современный интерфейс на Python.
* **[ValdikSS](https://github.com/ValdikSS)** — за фундаментальные исследования методов противодействия ТСПУ/DPI.

---

<br/>

## 🇬🇧 English Version

**Zapret DPI Manager** is a modern, lightweight desktop graphical user interface (GUI) designed specifically for the popular **[zapret-discord-youtube](https://github.com/Flowseal/zapret-discord-youtube)** distribution by Flowseal, powered by `zapret` (bol-van) and `WinDivert`.

Instead of running raw `.bat` scripts as administrator and managing Windows services manually through the command prompt, Zapret DPI Manager provides a sleek **Windows 11 Fluent 2** control center with full support for Dark, Light, and System-adaptive themes (auto-matches your Windows appearance), automated strategy benchmarking, and an integrated rule editor.

> [!NOTE]
> 💡 **Product of Vibe Coding:**
> This software is the result of human-AI collaborative "vibe coding". Designed to solve real day-to-day user pain points without heavy web-based runtimes (Electron/Webview) or bloated code — delivering an ultra-fast, native, responsive desktop experience.

---

### ✨ Features

* 🎨 **Adaptive Design (Fluent 2):**
  * Full support for **Dark**, **Light**, and **System-adaptive** themes (instantly syncs with Windows personal appearance settings).
  * Smooth micro-animations, refined typography (Segoe UI Variable), and clean layout without visual clutter.

* 🚀 **1-Click Service Control:**
  * Install, start, stop, and restart the `zapret` Windows service.
  * Seamlessly toggle between background Windows Service mode and interactive console mode.
  * Real-time service status detection and watchdog.

* 🎯 **Strategy Switcher:**
  * Automatically scans and lists all available `.bat` strategies in the zapret directory.
  * Human-readable, clean titles for strategies instead of obscure command-line parameters.
  * Instant 1-click strategy switching with graceful service restart.

* ⚡ **Automated Strategy Benchmark (Auto-Tune):**
  * Built-in multi-target latency & packet test (YouTube, Discord Gateway/Voice, CDN endpoints).
  * Strategy leaderboard with performance badges (🥇 Gold, 🥈 Silver, 🥉 Bronze).
  * Automatically applies the optimal strategy for your ISP and region.

* 🎮 **Smart Game Mode (Low-Latency Bypass):**
  * UDP game traffic optimization to eliminate packet loss and jitter.
  * Auto-ping watchdog tailored for competitive games (CS2, Valorant, Dota 2, Apex Legends).

* 📋 **Rule & Domain List Editor:**
  * Clean tabbed editor for `list-general-user.txt`, `list-exclude-user.txt`, and `ipset-exclude-user.txt`.
  * Domain search bar and real-time active entry counter.
  * Quick-Add modal with automatic URL sanitization (extracts base domain from full URLs).
  * **High-visibility inverted text cursor (I-Beam)** — no more invisible black cursor on dark background.
  * Fake UDP package selector (Discord UDP Fake, Game UDP Fake).

* 🛠️ **Diagnostics & Network Utilities:**
  * 1-Click DNS cache flush (`ipconfig /flushdns`).
  * 1-Click website accessibility tester through the active bypass.
  * Live sliding log drawer for real-time output and troubleshooting.
  * System tray integration with quick controls.

---

### 📦 Installation & Usage

#### Option 1: Standalone Binary (Recommended)
1. Download `ZapretManager.exe` from [Releases](https://github.com/).
2. Place `ZapretManager.exe` inside your `zapret-discord-youtube` directory (alongside the `.bat` strategy files).
3. Run as Administrator. The manager will automatically detect strategies and rule lists!

#### Option 2: Run from Source (Python)
Requires Python 3.10+ (64-bit):
```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/zapret-manager.git
cd zapret-manager

# Install dependencies
pip install customtkinter pystray pillow requests urllib3

# Launch the app
python src/main.py
```

#### Building Standalone Executable
Compile using `PyInstaller`:
```bash
pip install pyinstaller
python build_main.py
```
The compiled single-file binary will be placed in `dist/ZapretManager.exe`.

---

### 🙏 Credits & Acknowledgements

Zapret DPI Manager is a management GUI frontend. All core DPI-circumvention credit goes to the respective authors:

* **[Flowseal](https://github.com/Flowseal)** — creator of the renowned **[zapret-discord-youtube](https://github.com/Flowseal/zapret-discord-youtube)** package, customized bypass strategies, and Windows integration.
* **[bol-van](https://github.com/bol-van)** — original author of the legendary **[zapret](https://github.com/bol-van/zapret)** circumvention framework.
* **[basil00 / reqrypt](https://reqrypt.org/windivert.html)** — developers of the **WinDivert** kernel packet interception engine.
* **[Tom Schimansky](https://github.com/TomSchimansky)** — creator of **[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)**.
* **[ValdikSS](https://github.com/ValdikSS)** — pioneering researcher on Russian DPI/TSPU circumvention and GoodbyeDPI.

---

### ⚖️ Disclaimer
This project is developed for educational, testing, and research purposes. Users are solely responsible for compliance with their local regulations.

---

<div align="center">
Made with ❤️, AI & Vibe Coding.
</div>
