---
name: clips-virales
description: Aplica el estilo de edición de Reels CLIPS VIRALES (firma "Secuencia 01") dentro de Adobe Premiere a través del puente MCP. Define el ritmo objetivo, la estructura por tramos, las capas de diseño y un checklist, todo extraído del análisis cruzado del timeline de referencia + video exportado. Usá esta skill SIEMPRE que el usuario pida editar un Reel en Premiere, armar un montaje con este estilo, revisar si una edición tiene su ritmo, planear la estructura de un video corto, o aplicar/clavar su estilo a material nuevo. También cuando pida analizar una secuencia o video para compararlo con la firma. Requiere el MCP de Premiere conectado (tools capture_frame, analyze_timeline_style, analyze_exported_video, execute_extendscript, get_project_state). NO usar para guiones (usar guiones-virales-master5) ni para stories (usar stories-secuencias).
---

# CLIPS VIRALES — edición de Reels en Premiere

Skill para editar Reels en Premiere con el estilo CLIPS VIRALES, vía el puente MCP. El criterio sale del análisis cruzado del timeline de referencia (cómo construye) + video exportado (cómo se ve). El objetivo es que Claude no solo lea el estilo, sino que lo **aplique** y lo **verifique**.

## Idea central (no perder de vista)

La firma CLIPS VIRALES NO está en la cantidad de cortes duros, sino en **generar sensación de velocidad** con flashes y troceo que el ojo siente pero un detector de escenas no cuenta. El ritmo de construcción es ~el doble del ritmo percibido. Densidad alta, cortes visuales duros moderados.

**Regla madre:** capá densidad con flashes y troceo del mismo plano para acelerar la *sensación* sin saturar de cortes duros. La velocidad se siente, no se cuenta.

---

## Flujo de trabajo (cómo opera Claude con el MCP)

1. **Ver antes de actuar.** Llamar `get_project_state` y/o `analyze_timeline_style` para leer el estado real del timeline antes de proponer o ejecutar nada.
2. **Ejecutar.** Usar `execute_extendscript` para las acciones (cortar, mover, importar, aplicar). Para acciones destructivas (borrar, sobrescribir, exportar), confirmar con el usuario primero.
3. **Verificar.** Después de editar, `capture_frame` para ver el resultado en el monitor y/o `analyze_timeline_style` para chequear que el ritmo quedó dentro de los parámetros. Corregir si hace falta.
4. **Comparar contra la firma.** Si hay export, `analyze_exported_video` y contrastar con los parámetros de abajo.

Regla de oro del sistema: **nunca** sugerir prender el motor a mano (`python server.py`). Si el panel figura desconectado, pedir al usuario que toque Desconectar/Conectar en el panel CEP.

---

## Parámetros de ritmo (objetivo)

| Parámetro | Valor objetivo | Nota |
|---|---|---|
| Duración total | 50–55s | Reel largo, formato narrativo |
| Ritmo percibido (cortes duros) | 1 cada ~1.9s (~28 cpm) | Lo que el espectador "cuenta" |
| Ritmo de construcción (timeline) | 1 cada ~1.3s (~85 cpm) | Densidad real, incluye troceo y flashes |
| Clip más corto | 0.05s | Flashes de ráfaga |
| Clip más largo | ~5.8s | Planos de cierre / respiro |
| Transiciones | 0 — cortes secos | Nada de disolvencias |

Si una edición se va lejos de estos números (ej: ritmo percibido > 2.5s, o aparecen disolvencias), avisar al usuario: se está saliendo de la firma.

---

## Estructura por tramos

1. **Intro cargada (0–6s)** — motion graphics apilados (hasta 6 tracks de gráficos simultáneos) sobre planos cortos de cine. Arranque denso para enganchar.
2. **Desarrollo mixto (6–16s)** — alternar material: cámara cine (`A00...mov`), celular (`IMG_`), dron (`DJI_`). Cortes duros cada 1.5–2.5s, planos respirando.
3. **Ráfaga flash (~16s)** — 10–12 clips de 0.05s seguidos (montaje de Reels/screenshots propios). Total en pantalla ~0.6s. Funciona como parpadeo/acento, no como cortes individuales.
4. **Aceleración por troceo (~29–35s)** — picar UN mismo plano en trozos cada vez más cortos (ej: 0.90 → 0.80 → 0.68 → 0.40s). Sube la energía sin cambiar de imagen. La aceleración se siente por audio + movimiento.
5. **Cierre (>50s)** — planos de cine más largos (3–4s) para bajar y rematar.

---

## Capas de diseño

- **Gráficos (V2 hacia arriba):** concentrar en la intro. Apilar varios tracks los primeros ~6s, despuntar después.
- **Capa de ajuste:** repartir a lo largo de todo el video por tramos (look/color global o efectos).
- **Color mate / fondo de color:** usar puntual en la ráfaga flash como acento.
- **Audio:** 4 tracks de base (música + voz + SFX + ambiente). La sensación de ritmo en las zonas de troceo viene más del audio que de la imagen — cuidar que música y SFX marquen el pulso.

---

## Checklist para el próximo Reel

- [ ] Intro de motion graphics apilada en los primeros 6s
- [ ] Cortes secos, cero transiciones
- [ ] Mezclar 3 fuentes de imagen (cine + celu + dron/otro)
- [ ] Meter al menos 1 ráfaga flash (10+ clips de 0.05s) como acento
- [ ] 1 zona de aceleración por troceo del mismo plano (trozos decrecientes)
- [ ] Cerrar con planos largos (3–4s) para rematar
- [ ] Ritmo percibido objetivo: corte duro cada ~1.9s
- [ ] 4 tracks de audio marcando el pulso

---

## Cómo usar esto al editar

- **Si el usuario pide armar un Reel desde material crudo:** primero `get_project_items` para ver qué hay, mapear el material a las 3 fuentes (cine/celu/dron), proponer una estructura por tramos según el esquema, y recién ahí ejecutar. Confirmar el plan antes de tocar el timeline si es un cambio grande.
- **Si pide revisar una edición existente:** `analyze_timeline_style`, contrastar contra los parámetros, y devolver qué está dentro de la firma y qué se fue. Señalar lo que falta del checklist.
- **Si pide "que tenga mi feel":** traducir eso a los parámetros concretos de arriba, no a una vibra vaga.

Esta nota es la base. A medida que el usuario edite más Reels y los analicemos, se actualiza con nuevos patrones (otros formatos, otras duraciones, variantes por cliente).

---

# Sistema de subtítulos (receta de estilo)

Subtítulos hechos como captions nativos → "Actualizar a gráfico" para apilar/estilizar. Un solo sistema parejo en todo el video. Al generar o evaluar subtítulos, Claude aplica este sistema, no una vibra.

## Base tipográfica (común a TODO)
- **Fuente:** Alte Haas Grotesk (no varía nunca — la unidad sale de acá).
- **Tracking:** −33.
- Tamaños en **% del alto** de pantalla (1080×1920 vertical) para que escalen. Los px son referencia a 1920 de alto.

## Regla madre
Todo subtítulo tiene **dos niveles**: **setup** (chico, minúscula, conector/arranque) + **impacto** (grande, MAYÚSCULA, palabra clave). Nunca todo al mismo peso.

Color = **semántico**, no decorativo:
- **Rojo** → palabra clímax / clave / lo "prohibido".
- **Blanco** → neutro sobre fondo oscuro o saturado.
- **Negro** → sobre fondo claro (pregunta / duda).

Palabrotas → censura con asterisco (P\*TA), nunca entera.

## Tipo 1 — Hook apilado (build palabra por palabra)
Ej: hizo / lo / que / **NADIE**
- Posición: IZQUIERDA, apilado vertical.
- Animación: una palabra por capa, entran en cascada y **acumulan** (no reemplazan). ~150–300 ms entre palabras.
- En Premiere: una capa de texto por track (V1, V2, V3…), cada una arranca un poco después. 4 palabras → 4 tracks.
- Setup: blanco, minúscula, ≈4–4.5% del alto (~80–86 px).
- Impacto: última palabra ROJO, MAYÚSCULA, ≈6–6.5% (~115–125 px).
- Interlineado ajustado (leading ~100–105%).
- Función: apertura de máxima tensión.

## Tipo 2 — Remate centrado (dos niveles)
Ej: hijo de / **P\*TA**
- Posición: CENTRADO (o sobre el sujeto).
- Animación: golpe único sincronizado a la línea hablada. No acumula.
- Setup: conector arriba, blanco, minúscula, ≈3.5–4% (~70–80 px).
- Impacto: palabra fuerte abajo, blanco, MAYÚSCULA, ≈7–8% (~135–155 px).
- Blanco con borde/sombra sutil para despegar del fondo.
- Función: remate de impacto puntual, humor crudo o golpe seco.

## Tipo 3 — Interludio sobre fondo de color
Ej: ¿POR QUÉ? · pero… · hacerme **VIRAL.**
- Posición: CENTRADO, grande, centro de pantalla.
- Fondo: plano de color pleno (rosa/rojo). Tono suave = pregunta/duda → saturado = clímax.
- Texto se **invierte** según fondo: fondo claro (rosa) → texto NEGRO; fondo saturado (rojo) → texto BLANCO.
- Uno o dos niveles. Impacto ≈8–10% (~155–190 px), el más grande del sistema.
- Función: marca beats narrativos, corta el ritmo, "respiro conceptual".

## Tabla rápida
| | Posición | Niveles | Color | Animación | Función |
|---|---|---|---|---|---|
| Tipo 1 | Izquierda, apilado | Blanco + rojo | Blanco/Rojo | Cascada que acumula | Hook / tensión |
| Tipo 2 | Centrado | Conector + palabra | Blanco | Golpe único | Remate puntual |
| Tipo 3 | Centrado, grande | 1 o 2 | Negro o blanco s/ fondo | Corte / aparición | Interludio / beat |

Constante en los tres: Alte Haas Grotesk · tracking −33 · dos niveles · color semántico · MAYÚSCULA en impacto.

## Nota sobre captura visual
La captura automática de frames (exportFramePNG) no funciona en Premiere 2026 vía scripting. Cuando haga falta análisis visual de subtítulos, Claude le pide al usuario que suba capturas manuales (Cmd+Shift+4 sobre el Program Monitor) en vez de intentar sacarlas solo. El análisis estructural (list_subtitle_graphics) sí funciona y da la ubicación temporal de cada gráfico.
