import os
from .logger import logger

COMMUNITY_PRESETS = {
    "youtube_boost": {
        "title": "📺 YouTube CDN & Video Boost",
        "desc": "Эндпоинты видеопотоков, превью и мобильных шлюзов",
        "domains": [
            "youtube.com",
            "youtu.be",
            "googlevideo.com",
            "ytimg.com",
            "yt3.ggpht.com",
            "youtubei.googleapis.com",
            "wide-youtube.l.google.com",
            "redirector.googlevideo.com",
            "manifest.googlevideo.com",
            "i.ytimg.com",
            "i9.ytimg.com",
            "s.ytimg.com",
            "play.google.com"
        ]
    },
    "discord_voice": {
        "title": "🎮 Discord Voice & Media RTC",
        "desc": "Все шлюзы, голосовые сервера и медиа-сети Discord",
        "domains": [
            "discord.com",
            "discord.gg",
            "discordapp.com",
            "discordapp.net",
            "gateway.discord.gg",
            "cdn.discordapp.com",
            "status.discord.com",
            "media.discordapp.net",
            "router.discordapp.net",
            "updates.discord.com",
            "latency.discord.media"
        ]
    },
    "trackers": {
        "title": "🧲 Популярные торрент-трекеры",
        "desc": "RuTracker, NNM-Club, Rutor, Кинозал, Megapeer",
        "domains": [
            "rutracker.org",
            "rutracker.cc",
            "rutracker.net",
            "nnmclub.to",
            "rutor.info",
            "rutor.is",
            "kinozal.tv",
            "megapeer.vip",
            "torrentgalaxy.to",
            "1337x.to"
        ]
    },
    "dev_tools": {
        "title": "💻 IT, Репозитории & Документация",
        "desc": "Docker Hub, Hugging Face, Medium, Raw GitHub, Dev.to",
        "domains": [
            "hub.docker.com",
            "registry-1.docker.io",
            "auth.docker.io",
            "production.cloudflare.docker.com",
            "huggingface.co",
            "medium.com",
            "raw.githubusercontent.com",
            "dev.to",
            "gist.github.com"
        ]
    },
    "ai_services": {
        "title": "🤖 Нейросети и AI-платформы",
        "desc": "OpenAI, ChatGPT, Claude (Anthropic), Perplexity",
        "domains": [
            "openai.com",
            "chatgpt.com",
            "oaistatic.com",
            "oaiusercontent.com",
            "claude.ai",
            "anthropic.com",
            "perplexity.ai",
            "api.perplexity.ai"
        ]
    }
}

class PresetListsManager:
    @staticmethod
    def get_presets():
        return COMMUNITY_PRESETS

    @classmethod
    def get_categories(cls):
        return [
            {
                "id": k,
                "name": v["title"],
                "desc": v["desc"],
                "count": len(v["domains"]),
                "domains": v["domains"]
            }
            for k, v in COMMUNITY_PRESETS.items()
        ]

    @classmethod
    def import_presets_to_general_user(cls, preset_keys, base_dir):
        added, total_existing, msg = cls.import_preset_into_list(base_dir, target_list="list-general-user.txt", preset_keys=preset_keys)
        total_selected = sum(len(COMMUNITY_PRESETS[k]["domains"]) for k in preset_keys if k in COMMUNITY_PRESETS)
        skipped = max(0, total_selected - added)
        return added, skipped

    @staticmethod
    def import_preset_into_list(zapret_dir, target_list="list-general-user.txt", preset_keys=None):
        """
        Safely appends non-duplicate domains from selected presets into user's list.
        GUARANTEE: Never deletes or overwrites existing user entries.
        """
        if not preset_keys:
            return 0, 0, "Не выбрано ни одной базы."

        lists_dir = os.path.join(zapret_dir, "lists")
        os.makedirs(lists_dir, exist_ok=True)
        target_path = os.path.join(lists_dir, target_list)

        existing_domains = set()
        existing_lines = []
        if os.path.exists(target_path):
            try:
                with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        existing_lines.append(line)
                        clean = line.strip().lower()
                        if clean and not clean.startswith("#"):
                            existing_domains.add(clean)
            except Exception as e:
                logger.error("LIST", f"Ошибка чтения {target_list}: {e}")
                return 0, 0, f"Ошибка чтения файла: {e}"

        added_domains = []
        for key in preset_keys:
            preset = COMMUNITY_PRESETS.get(key)
            if not preset:
                continue
            for dom in preset["domains"]:
                d_clean = dom.strip().lower()
                if d_clean and d_clean not in existing_domains:
                    existing_domains.add(d_clean)
                    added_domains.append(d_clean)

        if not added_domains:
            return 0, len(existing_domains), "Все домены из выбранных категорий уже есть в вашем списке."

        try:
            with open(target_path, "a", encoding="utf-8") as f:
                # Ensure newline if last line did not have it
                if existing_lines and not existing_lines[-1].endswith("\n"):
                    f.write("\n")
                f.write(f"\n# === ИМПОРТ ИЗ БАЗ СООБЩЕСТВА ({len(added_domains)} шт.) ===\n")
                for d in added_domains:
                    f.write(f"{d}\n")

            logger.success("LIST", f"Успешно импортировано {len(added_domains)} доменов в {target_list}")
            return len(added_domains), len(existing_domains), f"Успешно добавлено новых доменов: {len(added_domains)}"
        except Exception as e:
            logger.error("LIST", f"Ошибка записи в {target_list}: {e}")
            return 0, 0, f"Ошибка записи: {e}"
