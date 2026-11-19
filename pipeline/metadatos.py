# -*- coding: utf-8 -*-
"""Genera metadata.md (título, descripción, capítulos, etiquetas, fuentes) para cada vídeo."""
import os, json, sys
sys.path.insert(0, os.path.dirname(__file__))
from guiones import VIDEOS

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def fmt(t):
    t = int(t); return f"{t // 60}:{t % 60:02}"

COMUNES = ["gta 6", "gta vi", "grand theft auto 6", "grand theft auto vi", "gta 6 español", "gta 6 guia", "leonida", "vice city", "rockstar games", "ps5", "xbox series x"]

EXTRA = {
 "01-gta6-ya-disponible": dict(
   desc="GTA 6 ya está disponible. Hora de desbloqueo, plataformas, cuánto ocupa (212 GB en PS5), parches previos, precio de las ediciones y lo que todavía NO trae el juego.",
   tags=["gta 6 cuanto ocupa", "gta 6 tamaño", "gta 6 hora de salida", "gta 6 precio", "gta 6 ya disponible", "gta 6 lanzamiento", "gta 6 212 gb"],
   pin="¿Ya lo tienes descargado? ¿PS5 o Xbox? 👇",
   src=[("Rockstar Store – GTA VI", "https://store.rockstargames.com/game/buy-gta-vi"),
        ("Forbes – horas de lanzamiento", "https://www.forbes.com/sites/brianmazique/2026/11/12/gta-6-unlocks-at-midnight-on-november-19-but-millions-of-americans-can-start-playing-the-night-before/"),
        ("Forbes – tamaño y parche", "https://www.forbes.com/sites/erikkain/2026/11/16/gta-6-release-date-time-ps5-xbox-series-x-download-size-day-one-update/"),
        ("Push Square – 212 GB en PS5", "https://www.pushsquare.com/news/2026/11/gta-6-ps5-file-size-confirmed-to-be-212gb-physical-map-available-but-not-in-boxed-copies"),
        ("RockstarINTEL – precarga", "https://rockstarintel.com/gta-6-pre-load-begins-rolling-out-updated-install-size-revealed/")]),
 "02-gta6-99-metacritic-analisis": dict(
   desc="GTA 6 tiene un 99 en Metacritic, empatado con Ocarina of Time. Repasamos qué elogia la crítica (Leonida, Jason y Lucía) y qué critica (30 FPS, ritmo, misiones guiadas).",
   tags=["gta 6 analisis", "gta 6 review", "gta 6 metacritic", "gta 6 nota", "gta 6 merece la pena", "gta 6 opinion"],
   pin="¿Qué nota le das tú tras las primeras horas? 👇",
   src=[("Forbes – nota de Metacritic", "https://www.forbes.com/sites/paultassi/2026/11/18/the-gta-6-metacritic-review-score-is-in-and-ties-an-all-time-record/"),
        ("GamesRadar – récord histórico", "https://www.gamesradar.com/games/grand-theft-auto/gta-6-metacritic-score-makes-it-the-highest-rated-game-of-all-time-matching-the-og-zelda-ocarina-of-time/"),
        ("PC Gamer – resumen de análisis", "https://www.pcgamer.com/games/grand-theft-auto/grand-theft-auto-6-review-roundup-rockstars-magnum-opus-a-great-love-story-and-a-new-bar-for-open-worlds/"),
        ("The National – lo que gusta y lo que no", "https://www.thenationalnews.com/arts-culture/pop-culture/2026/11/18/gta-6-reviews-metacritic/"),
        ("Notebookcheck – comparativa con GTA IV/V", "https://www.notebookcheck.net/GTA-6-reviews-award-99-Metacritic-score-topping-GTA-4-to-become-Rockstar-s-top-rated.1453363.0.html")]),
 "03-gta6-60fps-ps5-pro-xbox": dict(
   desc="¿Se puede jugar GTA 6 a 60 FPS? No, en ninguna consola. Te explico por qué (CPU), qué resolución tiene cada versión y si merece la pena la PS5 Pro.",
   tags=["gta 6 60 fps", "gta 6 ps5 pro", "gta 6 rendimiento", "gta 6 fps", "gta 6 xbox series s", "gta 6 resolucion", "gta 6 30 fps"],
   pin="¿En qué consola juegas y notas los 30 FPS? 👇",
   src=[("Kotaku – sin modo 60 FPS", "https://kotaku.com/gta-6-wont-get-a-60-fps-mode-even-on-ps5-pro-because-its-not-powerful-enough-2000755979"),
        ("Push Square – explicación de Rockstar", "https://www.pushsquare.com/news/2026/11/ps5-pro-is-not-powerful-enough-to-run-gta-6-at-60fps-rockstar-explains-frame-rate-decision"),
        ("VGC – PS5 Pro y 60 FPS", "https://www.videogameschronicle.com/news/rockstar-says-ps5-pro-cant-handle-gta-6-at-60-fps/"),
        ("TechPowerUp – Series S", "https://www.techpowerup.com/355004/gta-6-reportedly-plays-best-on-ps5-pro-xbox-series-s-struggles")]),
 "04-gta6-trucos-como-desbloquear": dict(
   desc="Los trucos vuelven a GTA 6, pero no como en GTA V: hay que terminar la historia y cumplir un desafío por truco. Cómo se activan, el truco de 250.000 $ y el aviso sobre trofeos.",
   tags=["gta 6 trucos", "gta 6 cheats", "trucos gta 6 ps5", "trucos gta 6 xbox", "gta 6 truco dinero", "gta 6 codigos"],
   pin="¿Qué truco quieres que investigue primero? 👇",
   src=[("Dexerto – lista de trucos", "https://www.dexerto.com/wikis/gta-6/cheat-codes/"),
        ("Destructoid – cómo desbloquearlos", "https://www.destructoid.com/all-gta-6-cheat-codes-and-how-to-unlock-them/"),
        ("Tbreak – bloqueados hasta acabar la historia", "https://tbreak.com/gta-6-cheats-locked-until-main-story/"),
        ("Power Up Gaming – inconvenientes", "https://powerupgaming.co.uk/2026/11/18/gta-6-all-cheats-how-to-unlock-them-and-the-drawbacks-of-using-them/"),
        ("Red Bull – 61 trucos", "https://www.redbull.com/int-en/gta-6-cheat-codes")]),
 "05-gta6-dinero-rapido-principio": dict(
   desc="Cómo ganar dinero en GTA 6 desde el capítulo 1 sin trucos: dónde guardarlo, robos, vender coches a Moses, inmersiones con Kenton y los golpes grandes.",
   tags=["gta 6 dinero", "gta 6 dinero rapido", "gta 6 como ganar dinero", "gta 6 money", "gta 6 dinero facil", "gta 6 golpes"],
   pin="¿Cuál es tu método favorito para hacer dinero? 👇",
   src=[("Vice – dinero rápido", "https://www.vice.com/en/article/gta-6-how-to-make-money-fast/"),
        ("GamerBolt – métodos por capítulo", "https://www.gamerbolt.com/gta-6-money-guide/"),
        ("Outputlag – dinero al principio", "https://outputlag.com/guides/gta-6-make-money-fast/"),
        ("Game8 – guía de inicio (banco)", "https://game8.co/games/GTA-6/archives/637017")]),
 "06-gta6-10-consejos-antes-de-empezar": dict(
   desc="10 consejos para tus primeras horas en GTA 6, sin spoilers: ajustes, guardado, dinero, policía, coches con localizador, sigilo, modo enfoque, gimnasio y más.",
   tags=["gta 6 consejos", "gta 6 tips", "gta 6 guia principiantes", "gta 6 primeros pasos", "gta 6 trucos principiantes", "gta 6 errores"],
   pin="¿Cuál sería tu consejo número 11? 👇",
   src=[("GameSpot – lo que me hubiera gustado saber", "https://www.gamespot.com/articles/gta-6-tips-everything-i-wish-i-knew-before-i-started-playing/"),
        ("Game8 – guía de principiantes", "https://game8.co/games/GTA-6/archives/637017"),
        ("TalkEsport – consejos", "https://www.talkesport.com/gta-6/best-gta-6-tips-tricks-beginners/"),
        ("GamerBolt – 20 cosas que saber", "https://www.gamerbolt.com/gta-6-beginners-guide-tips/")]),
 "07-gta6-mapa-leonida-zonas": dict(
   desc="El mapa de GTA 6: Vice City, Leonida Keys, Grassrivers, Port Gellhorn, Ambrosia y Mount Kalaga. Y cuánto mide de verdad Leonida (sin cifras inventadas). Mapa ilustrativo, no oficial.",
   tags=["gta 6 mapa", "gta 6 map", "leonida mapa", "gta 6 vice city", "gta 6 tamaño mapa", "gta 6 zonas"],
   pin="¿Cuál es tu zona favorita de Leonida? 👇",
   src=[("MMO Culture – regiones de Leonida", "https://mmoculture.com/tips-guides/gta-6-map-guide/"),
        ("Allthings.how – tamaño del mapa", "https://allthings.how/gta-6-map-size-how-vice-city-and-leonida-compare-to-los-santos/"),
        ("GTA Boss – localizaciones confirmadas", "https://www.gtaboss.gg/gta-6/guides/gta-6-map")]),
 "08-gta6-cuanto-dura-horas": dict(
   desc="¿Cuánto dura GTA 6? La historia principal está entre 50 y 80 horas según la fuente, unas 90-100 misiones en 5 capítulos, y alrededor de 200 horas para el 100%.",
   tags=["gta 6 cuanto dura", "gta 6 duracion", "gta 6 horas", "gta 6 misiones", "gta 6 how long to beat", "gta 6 platino"],
   pin="¿Cuántas horas llevas ya? 👇",
   src=[("ScreenRant – duración de la historia", "https://screenrant.com/gta-6-main-story-length-completion/"),
        ("Dexerto – time to beat", "https://www.dexerto.com/wikis/gta-6/time-to-beat/"),
        ("Beebom – how long to beat", "https://beebom.com/how-long-to-beat-gta-6/")]),
 "09-gta6-pc-y-gta-online": dict(
   desc="GTA 6 en PC y el nuevo GTA Online: qué es oficial a 19 de noviembre, qué es rumor (GamesBeat: principios de 2027) y cuánto tardaron GTA V y RDR2 en llegar a PC. Ojo con las estafas de 'GTA 6 PC'.",
   tags=["gta 6 pc", "gta 6 pc fecha", "gta 6 online", "gta 6 steam", "gta 6 pc descargar", "gta online 2"],
   pin="¿Esperas a PC o ya lo juegas en consola? 👇",
   src=[("Forbes – sin PC en el lanzamiento", "https://www.forbes.com/sites/brianmazique/2026/11/12/gta-6-unlocks-at-midnight-on-november-19-but-millions-of-americans-can-start-playing-the-night-before/"),
        ("HollywoodLife – cuándo llega a PC", "https://hollywoodlife.com/2026/11/18/when-will-gta-6-come-to-pc/"),
        ("Rockstar Store – plataformas", "https://store.rockstargames.com/game/buy-gta-vi")]),
 "10-gta6-secretos-primer-dia": dict(
   desc="Los primeros easter eggs de GTA 6 encontrados por la comunidad: huevos en la torre de radio más alta, Bigfoot en los pantanos y un cangrejo gigante. Y cómo detectar los 'secretos' falsos.",
   tags=["gta 6 secretos", "gta 6 easter eggs", "gta 6 bigfoot", "gta 6 misterios", "gta 6 curiosidades", "gta 6 huevos de pascua"],
   pin="¿Has encontrado algún secreto? Los mejores salen en el próximo vídeo 👇",
   src=[("Kotaku – directo del lanzamiento", "https://kotaku.com/live-updates-on-gta-6-the-biggest-launch-in-gaming-history-2000758030"),
        ("GameSpot – el easter egg de los huevos", "https://www.gamespot.com/articles/gta-6-has-a-hilarious-riff-on-easter-eggs/")]),
}

PLAN = {  # recomendación de publicación (hora de España peninsular)
 "01-gta6-ya-disponible": "Hoy 19/11 · 13:00",
 "06-gta6-10-consejos-antes-de-empezar": "Hoy 19/11 · 16:00",
 "04-gta6-trucos-como-desbloquear": "Hoy 19/11 · 19:00",
 "05-gta6-dinero-rapido-principio": "Hoy 19/11 · 22:00",
 "02-gta6-99-metacritic-analisis": "20/11 · 13:00",
 "03-gta6-60fps-ps5-pro-xbox": "20/11 · 17:00",
 "07-gta6-mapa-leonida-zonas": "20/11 · 21:00",
 "08-gta6-cuanto-dura-horas": "21/11 · 13:00",
 "09-gta6-pc-y-gta-online": "21/11 · 17:00",
 "10-gta6-secretos-primer-dia": "21/11 · 21:00",
}

def main():
    rows = []
    for v in VIDEOS:
        d = os.path.join(ROOT, "videos", v["slug"])
        info = json.load(open(os.path.join(d, "_info.json")))
        e = EXTRA[v["slug"]]
        caps = "\n".join(f"{fmt(t)} {n}" for t, n in info["chapters"])
        fuentes = "\n".join(f"· {n}: {u}" for n, u in e["src"])
        tags = COMUNES + e["tags"]
        desc = f"""{e['desc']}

Información verificada a 19 de noviembre de 2026. Si algo cambia, lo actualizo en el comentario fijado.

⏱️ CAPÍTULOS
{caps}

📚 FUENTES
{fuentes}

🔔 Suscríbete a MODO LEONIDA: guías, trucos y secretos de GTA 6 cada día.

Canal de fans no afiliado a Rockstar Games ni a Take-Two Interactive. Grand Theft Auto, GTA y sus logotipos son marcas de sus respectivos propietarios. Gráficos, mapa ilustrativo y música originales del canal. Voz sintética.

#GTA6 #GTAVI #Leonida"""
        md = f"""# {v['title']}

**Archivo:** `video.mp4` · **Duración:** {fmt(info['total'])} · **Miniatura:** `miniatura.jpg` · **Subtítulos:** `subtitulos.srt` (español)
**Publicación recomendada:** {PLAN[v['slug']]}

## Título (copiar)
```
{v['title']}
```

## Descripción (copiar)
```
{desc}
```

## Etiquetas (copiar)
```
{', '.join(tags)}
```

## Comentario fijado
```
{e['pin']}
```

## Ajustes de subida
- Categoría: Videojuegos · Juego: Grand Theft Auto VI
- Idioma del vídeo y de los subtítulos: Español
- "Contenido alterado o sintético": **Sí** (voz generada por IA). Obligatorio declararlo en YouTube.
- Pantalla final: los últimos 12 s están preparados (recuadro de vídeo a la izquierda, botón de suscripción a la derecha).
- Audiencia: no creado para niños (GTA es PEGI 18).
"""
        open(os.path.join(d, "metadata.md"), "w").write(md)
        rows.append((PLAN[v["slug"]], v["slug"], v["title"], fmt(info["total"])))
    return rows

if __name__ == "__main__":
    for r in main(): print(r)
