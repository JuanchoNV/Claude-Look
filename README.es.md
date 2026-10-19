# Claude-Look

**Haz que Claude vea videos.** Pega un link de TikTok, un Reel de Instagram o un video de X en
Claude Code y pregúntale de qué trata. Claude-Look saca los cuadros clave y la transcripción,
Claude los mira y al final todo se borra.

[Read in English](README.md)

```
Tú:     https://www.tiktok.com/@alguien/video/123 ¿de qué trata? ¿vale la pena copiar la idea?
Claude: (usa Claude-Look, lee 1 hoja de cuadros + la transcripción)
        Es un reel de 28 s donde... En el 00:13 aparece en pantalla...
```

![Ejemplo de hoja de cuadros](docs/example-sheet.jpg)
*Una hoja: solo los cuadros donde cambia la escena, cada uno con su minuto. Video de ejemplo: [Time Lapse Clouds above Steens Mountain](https://commons.wikimedia.org/wiki/File:Time_Lapse_Clouds_above_Steens_Mountain_(36203941112).webm) (dominio público, Wikimedia Commons).*

## Por qué

- **Ve y escucha.** Cuadros clave (texto en pantalla, productos, escenas) y transcripción con minutos.
- **Gasta poco.** En vez de decenas de imágenes, Claude lee 1 o 2 hojas pequeñas de hasta 6
  cuadros. Las partes estáticas del video se saltan solas.
- **Privado.** La transcripción se hace en tu computador con Whisper. No se envía nada a otros servicios.
- **No deja rastro.** El video y el audio se borran apenas se sacan los cuadros, y las hojas se
  borran cuando Claude termina.
- **Sin cuentas ni claves.** Sin cookies, sin iniciar sesión, sin API keys. Solo contenido público.

## Instalación

**Requisito:** [uv](https://docs.astral.sh/uv/getting-started/installation/). La primera vez
instala Python, ffmpeg y lo demás por su cuenta, en un entorno aislado.

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```powershell
# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Opción A: como plugin (recomendada)

Dentro de Claude Code:

```
/plugin marketplace add JuanchoNV/Claude-Look
/plugin install claude-look@claude-look
```

### Opción B: como habilidad personal

```bash
git clone https://github.com/JuanchoNV/Claude-Look.git
cp -r Claude-Look/skills/claude-look ~/.claude/skills/
```

En Windows (PowerShell):

```powershell
git clone https://github.com/JuanchoNV/Claude-Look.git
Copy-Item -Recurse Claude-Look\skills\claude-look "$env:USERPROFILE\.claude\skills\"
```

Las habilidades personales funcionan en todos tus proyectos. Para compartirla con un equipo,
copia la carpeta en `.claude/skills/` del proyecto.

## Uso

Pega un link y pregunta:

- "¿De qué trata este video? `<link>`"
- "¿Qué producto aparece al final de `<link>`?"
- "Resume los ganchos que usan estos 3 reels: `<link>` `<link>` `<link>`"

La primera vez tarda 1-2 minutos mientras se descargan las dependencias. Después, un video
corto tarda unos 10-20 segundos.

También puedes correr el script tú mismo:

```bash
uv run skills/claude-look/look.py "<url>" [--max-frames 12] [--model base] [--lang es] [--no-audio]
uv run skills/claude-look/look.py clean
```

| Opción | Por defecto | Qué hace |
| --- | --- | --- |
| `--max-frames` | 12 | Máximo de cuadros clave (6 por hoja) |
| `--model` | base | Modelo de Whisper: `tiny`, `base`, `small` (más preciso, más lento) |
| `--lang` | auto | Idioma del audio: `es`, `en`, `pt`... |
| `--no-audio` | no | No transcribe |

## Cómo funciona

1. **Descarga** la versión más liviana (máx. 480p) a una carpeta temporal con
   [yt-dlp](https://github.com/yt-dlp/yt-dlp).
2. **Cuadros:** uno por segundo en miniatura; solo quedan los que cambian respecto al anterior,
   más el último (que suele traer el llamado a la acción).
3. **Hojas:** los cuadros se juntan en hojas JPG de 3x2 con su minuto.
4. **Transcripción:** el audio se transcribe en tu equipo con
   [faster-whisper](https://github.com/SYSTRAN/faster-whisper).
5. **Limpieza:** video y audio se borran al instante; las hojas, cuando Claude ejecuta `clean`.

Lo único que queda en disco: el caché de paquetes de uv y el modelo de Whisper (~150 MB), para
no descargarlos cada vez.

## Sitios

| Sitio | Estado |
| --- | --- |
| TikTok | Funciona sin iniciar sesión |
| Reels públicos de Instagram | Funciona sin iniciar sesión |
| X / Twitter, Facebook, Vimeo y [muchos más](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) | Suelen funcionar |
| YouTube | Suele bloquear sin sesión ("confirm you're not a bot") |

El contenido privado o que pide iniciar sesión no está soportado, a propósito.

## Uso responsable

Úsalo para entender contenido que tienes permitido ver. Respeta los términos de cada plataforma
y los derechos de los creadores: no lo uses para volver a subir ni redistribuir videos ajenos.

## Créditos

Hecho con [yt-dlp](https://github.com/yt-dlp/yt-dlp),
[faster-whisper](https://github.com/SYSTRAN/faster-whisper),
[imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg) y
[Pillow](https://python-pillow.org/).

## Licencia

[MIT](LICENSE)
