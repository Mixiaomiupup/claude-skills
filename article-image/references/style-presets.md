# Style Presets

`--style <name>` expands to a palette + rendering combination. Other dimensions (type, text, mood) remain independently selected or auto-selected.

| --style | palette | rendering |
|---------|---------|-----------|
| `notion` | mono | digital |
| `blueprint` | cool | digital |
| `warm` | warm | hand-drawn |
| `elegant` | elegant | hand-drawn |
| `minimal` | mono | flat-vector |
| `watercolor` | earth | painterly |
| `editorial` | cool | digital |
| `scientific` | cool | digital |
| `sketch-notes` | warm | hand-drawn |
| `chalkboard` | dark | chalk |
| `pixel-art` | vivid | pixel |
| `retro` | retro | digital |
| `flat-doodle` | pastel | flat-vector |
| `fantasy-animation` | pastel | painterly |
| `vintage` | retro | hand-drawn |

## Override Examples

- `--style blueprint --rendering hand-drawn` = cool palette with hand-drawn rendering
- `--style elegant --palette warm` = warm palette with hand-drawn rendering
- `--style retro --rendering hand-drawn` = same as `--style vintage`

Explicit `--palette` / `--rendering` flags always override preset values.
