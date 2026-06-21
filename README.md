# Change Commit Date

Herramienta de línea de comandos para planificar y reescribir fechas de commits
Git. Reescribir historial cambia hashes: úsala solo sobre ramas que controles y
después publica con `git push --force-with-lease`.

## Requisitos

- Python 3.9 o superior
- Git

No necesita dependencias de Python externas.

## Uso

Ejecuta la herramienta desde este directorio:

```sh
python change_commit_date.py --help
```

### Planificar un lote dentro de una franja diaria

`schedule` acepta franjas normales y franjas que cruzan medianoche. Por
seguridad, muestra el plan y no modifica el repositorio salvo que se indique
`--apply`.

```sh
# Vista previa de todos los commits incluidos por el rango Git A..B
python change_commit_date.py schedule \
  --path ../mi-repo \
  --range main..feature \
  --window 18:00-03:00

# Aplicar el plan tras revisarlo
python change_commit_date.py schedule \
  --path ../mi-repo \
  --range HEAD~5..HEAD \
  --window 18:00-03:00 \
  --apply
```

También se puede proporcionar un archivo de hashes. Cada línea contiene un
hash; las líneas vacías y los comentarios que empiezan por `#` se ignoran.

```text
# commits-release.txt
abc1234
def5678 # ajuste final
```

```sh
python change_commit_date.py schedule \
  --path ../mi-repo \
  --commits-file commits-release.txt \
  --window 18:00-03:00
```

Los commits se ordenan según la historia Git, no según la posición en el
archivo. La franja se interpreta en la zona horaria original de cada commit.
El primer commit fuera de la franja se ancla de forma natural en la siguiente
apertura: `10:12` con la franja `18:00-03:00` pasa a `18:12`. Los commits que
ya caen dentro de la franja se conservan en su fecha real. Para los demás, se
mantiene el intervalo anterior solo si ello sigue siendo válido en su mismo día;
en caso contrario pasan a la siguiente apertura de su fecha original.

La versión actual exige un árbol de trabajo limpio, commits ancestros de `HEAD`
y una historia lineal en el tramo reescrito. Rechaza merges y el commit raíz.

### Cambiar un único commit

```sh
# Fecha y hora actuales
python change_commit_date.py set --path ../mi-repo --commit abc1234 --now

# Fecha completa ISO 8601 o formato Git clásico
python change_commit_date.py set --path ../mi-repo --commit abc1234 \
  --date '2024-02-16T14:00:00+01:00'

# Hoy a una hora local concreta
python change_commit_date.py set --path ../mi-repo --commit abc1234 --today-at 17:30

# Mantener el día y la zona horaria del commit
python change_commit_date.py set --path ../mi-repo --commit abc1234 --same-day-at 09:00
```

`set` reescribe de inmediato el commit y sus descendientes; confirma el hash
nuevo que Git ha creado al finalizar.

## Desarrollo

Ejecuta la suite de pruebas con:

```sh
python -m unittest discover -s tests -v
```

## Licencia

MPL v2.0. Consulta [LICENSE](LICENSE).
