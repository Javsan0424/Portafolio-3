# Witch Hunt

Dominó de efectos para 2 jugadores hecho con Python y pygame. Se juega en un mismo dispositivo (local) o entre dos computadoras por red (en línea, con websockets).

## Requisitos

- Python 3.10 o superior
- Dependencias: `pip install -r requirements.txt` (pygame y websockets 12 o mayor)

## Ejecutar

```
python main.py
```

Las rutas a `Assets/` y `data.json` se resuelven con `Resources.ResourcePath`, así que funciona desde cualquier carpeta.

## Cómo se juega

- Cada ficha tiene dos mitades con un efecto: Fuego (F), Veneno (V), Impacto (I) o Drenar (D).
- Cada jugador empieza con 7 fichas. El mazo tiene 32 fichas (las 16 combinaciones arriba/abajo, dos veces cada una).
- En tu turno haces una sola acción: poner una ficha o generar una del mazo. El turno 1 es del Jugador 1 y los impares también. El Jugador 2 juega los turnos pares.
- Encadenar: una mitad que toca el mismo efecto sube la cadena (x2, x3...) y pega más fuerte.
- Cortar: solo la mitad de abajo puede cortar, tocando el efecto contrario (Fuego con Veneno, Impacto con Drenar).
- Gana quien deje la vida del rival en 0. Si el mazo se acaba, el botón pasa a ser "Pasar turno"; si los dos jugadores pasan seguidos, gana quien tenga más vida.

Controles: clic izquierdo elige y coloca, `R` o clic derecho rota, clic sobre la ficha elegida la suelta, `Esc` pausa. La pantalla "Cómo jugar" del menú explica todo con más detalle.

## Multijugador

1. Un jugador entra a Multijugador, elige "Crear partida" y comparte la IP que aparece (puerto 8765).
2. El otro jugador escribe esa IP y elige "Unirse".
3. Para probar en una sola computadora abre dos instancias y usa `127.0.0.1`.

El anfitrión es el Jugador 1 y tiene el mazo real. Si hace falta, abre el puerto 8765 en el firewall.

## Estructura

| Archivo | Responsabilidad |
|---|---|
| `main.py` | Punto de entrada |
| `App.py` | Ventana, bucle principal y unión de las piezas |
| `States.py`, `GameStates.py` | Pantallas (patrón State) |
| `Match.py` | Lógica de una partida (turnos, mazo, vida, fin de juego) |
| `Board.py` | Tablero y reglas de encadenar y cortar |
| `Effects.py` | Un efecto por clase (patrón Strategy) |
| `Commands.py` | Jugadas como objetos (patrón Command) |
| `Events.py` | Bus de eventos (patrón Observer) |
| `Session.py`, `Network.py` | Partida en línea: protocolo y websockets con envío por lotes estilo Nagle |
| `Hud.py`, `UI.py` | Números flotantes, avisos, efectos activos y dibujo compartido |
| `Telemetry.py` | Guarda un registro por partida |
| `Audio.py` | Suscripciones listas para música y sonidos |
| `Deck.py`, `CreateCard.py`, `Player.py`, `SkyBox.py`, `Resources.py` | Mazo, fichas, jugador, fondo y rutas |
| `data.json` | Imágenes, configuración del mazo y créditos |

## Telemetría

Al terminar cada partida se agrega una fila a `Telemetry/partidas.csv` (carpeta junto al juego): fecha, modalidad, duración, turnos, jugadas inválidas, fichas generadas, ganador y motivo.

## Empaquetar con PyInstaller

```
pip install pyinstaller
```

Windows:

```
pyinstaller --noconfirm --onefile --windowed --name WitchHunt --add-data "Assets;Assets" --add-data "data.json;." main.py
```

Linux y macOS (el separador es `:`):

```
pyinstaller --noconfirm --onefile --windowed --name WitchHunt --add-data "Assets:Assets" --add-data "data.json:." main.py
```

El ejecutable queda en `dist/`. `Resources.ResourcePath` lee los archivos desde la carpeta temporal de PyInstaller (`sys._MEIPASS`), y la carpeta `Telemetry` se crea junto al `.exe`.

## Créditos

Los assets propios, de terceros y generados con IA se listan en la sección `Credits` de `data.json` y se muestran en la pantalla Créditos del juego.
