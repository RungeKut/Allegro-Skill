---
id: 10-06
title: К Allegro три пути — пакетный над копией, живой в открытое окно, утилиты; результат правки — новым файлом; единицы — единицы платы, alkit их не переводит
tags: [alkit, пакетный, живой, утилиты, цикл, состав, единицы, порядок]
applies_to: Allegro 17.2-S066, Windows 10, Python 3.13 64-bit
status: проверено
verified: 2026-09-24 — tests/test_board.py, test_edit.py, test_capture.py, test_export.py целиком на демо-паре поставки; test_live.py с открытым Allegro
source: практика; до 2026-10-28 — в SKILL.md, вынесено при сокращении SKILL.md до 4 КБ
---

# Три пути к Allegro и состав alkit

## Три пути

| Путь | Когда | Чем |
|---|---|---|
| **пакетный** | чтение и правка файла платы; Allegro не нужен открытым | `ak.dump`, `ak.place`, `ak.edit`, `ak.run` ([10-01](10-01_пакетный_режим.md)) |
| **живой** | человек держит плату открытой и хочет видеть правку | `ak.Live()` → `.dump()`, `.run(code, edit=True)`, `.send("zoom fit")` ([10-02](10-02_живой_режим_wm_copydata.md)) |
| **утилиты** | отчёты и выходные файлы | `ak.summary`, `ak.drc`, `ak.unconnected`, `ak.unplaced`, `ak.gerber`, `ak.ipc2581`, `ak.step`, `ak.pdf` ([10-04](10-04_утилиты_отчёты_и_экспорт.md)) |

Схема Capture — `ak.read_dsn(path)`, Capture не нужен
([10-03](10-03_схемы_capture_через_tcl.md)).

В живом режиме набор не сохраняет плату и не закрывает Allegro: это
решает человек. В пакетном `overwrite=True` — только по явному решению
человека; иначе `save_to` — новый файл.

## Минимальный рабочий цикл

```python
src = r"D:\проект\плата.brd"                  # оригинал не трогается
b = ak.dump(src)                              # копия, Allegro без окна
print(b)                                      # компоненты, цепи, сегменты
ak.png(b, r"D:\проект\вывод\верх.png", side="top")

s = ak.read_dsn(r"D:\проект\схема.DSN")
ak.compare(s, b)                              # схема -> плата

dst = r"D:\проект\плата_v2.brd"              # результат — НОВЫМ файлом
ak.place(src, {"C11": (10.0, 20.0, 90, "top")}, save_to=dst)
b2 = ak.dump(dst)
ak.check_board(b2, expect_components=len(b.comps), max_drc=len(b.drcs))
ak.png(b2, r"D:\проект\вывод\верх_v2.png", side="top")
```

Единицы — **единицы платы** (`b.units`: millimeters, mils…). Набор их не
переводит; `b.to_mm(v)` — в миллиметры.

## Состав библиотеки

| Модуль | Что в нём |
|---|---|
| `env` | корень Cadence, версия, лицензии, рабочие папки, `utf8_console` |
| `batch` | `run`: SKILL над копией в Allegro без окна, `Result` |
| `board` | `dump`, `edit`, `place`, `Board` |
| `live` | `Live`: открытый Allegro через `WM_COPYDATA`; `allegro_dialogs`, `Live.snapshot`, `Live.press_default` — модальные вопросы |
| `reports` | `report`, `summary`, `drc`, `unconnected`, `unplaced` |
| `export` | `gerber`, `ipc2581`, `step`, `pdf` с проверкой содержимого |
| `capture` | `read_dsn`, `Schematic` |
| `render` | `png` — картинка платы из выгрузки |
| `verify` | `Report`, `check_board`, `compare` |
| `skill/alkit.il` | SKILL-часть: выгрузка, `akPlace`, `akText`, `akJob` |
| `tcl/dsn_dump.tcl` | выгрузка схемы |

Сигнатуры — docstring в `alkit/*.py` и `alkit/skill/alkit.il`.

## Новый проект

Скелет — `templates/new_project/`: скопировать в папку проекта, вписать в
`KIT` (`build.py`) корень набора — папку, из которой прочитан `SKILL.md`,
заменить данные в `params.py`, запустить `build.py`.

## Куда смотреть

Порядок: `INDEX.md` → файл базы → docstring → документация Cadence →
эксперимент на копии (подробно — [00_ПРАВИЛА.md](../00_ПРАВИЛА.md)). При
расхождении базы с документацией верить базе.

| Нужно | Читать |
|---|---|
| Карта базы, поиск по симптому | `knowledge/INDEX.md` |
| Как вести базу | `knowledge/00_ПРАВИЛА.md` |
| Сигнатура функции | docstring в `alkit/*.py`, `alkit/skill/alkit.il` |
| AXL, SKILL, TCL Capture, команды Allegro | `<cdsroot>/doc/algroskill`, `sklangref`, `orctclsample`, `algcmdref` (HTML) |
