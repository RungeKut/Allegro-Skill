---
id: 20-11
title: Негативные планы: вырез барьера — anti-etch, не etch-фигура; плёнка — negative И со слоем ANTI ETCH, иначе выреза в gerber нет; artwork без проверки gerber не считать готовым
tags: [негативные планы, anti etch, плёнки, gerber, artwork, изоляция]
applies_to: Allegro 17.2-S066
status: проверено
verified: 2026-11-15 — негативные планы на копии, DRC и разбор gerber-файла выреза
source: эксперимент на копии платы с изоляционным барьером
---

# Негативные планы: вырез изоляционного барьера до чистого DRC и до gerber

Задача: на негативном план-слое вырезать полосу (изоляционный барьер),
не создав DRC и не потеряв вырез в gerber. Три ловушки: DRC выреза
против keepout, полярность плёнки, попадание выреза в плёнку.

## Как неправильно

* Резать план **etch-фигурой** (прямоугольник с сетью на etch-слое),
  совпадающей с route keepout: DRC «Shape to Route Keepout» даёт и
  касание (act 0), и перекрытие. Делать фигуру шире keepout — DRC
  «перекрытие», уже — тоже. Фигура и keepout в одной полосе всегда
  нарушают зазор.
* Оставить плёнки позитивными при негативных слоях: artwork падает
  («Layer polarity of layer ETCH/… does not match film polarity of
  Positive») — причём молча в списке ошибок фотоплоттера, файлы
  просто не создаются.
* Пересоздать плёнку негативной **без слоя ANTI ETCH**: artwork
  проходит «с предупреждениями», но «APERTURES USED: NONE» — в
  gerber выреза нет, медь по всей барьерной полосе. Файл .art при
  этом существует и по размеру похож на настоящий.
* Считать artwork успешным без разбора gerber.

## Как правильно

1. Слой негативный: `axlXSectionModify(?negativeArtwork t)` +
   `axlXSectionSet`.
2. Вырез — прямоугольник класса **ANTI ETCH** на подклассе слоя:
   `axlDBCreateRectangle(list(x1:y1 x2:y2) t "anti etch/INT1" "GND")`.
   Anti-etch не участвует в spacing-DRC (0 нарушений против keepout),
   и чуть более широкий вырез (0.2 мм за keepout) только усиливает
   изоляцию.
3. Плёнку пересоздать негативной и **со слоем ANTI ETCH первым в
   списке** (иначе вырез не строится в плёнку):

```skill
s = axlGetParam("artwork:INT1")            ; путь "artwork:ИМЯ", не paramArtwork
layers = s->groupMembers                    ; сохранить атрибуты
axlDeleteObject(s)
axlFilmCreate("INT1" ?negative t ?layers cons("ANTI ETCH/INT1" layers)
  ?shapeBoundingBox s->shapeBoundingBox ?sequence s->sequence
  ?domains s->domains ?ipc2581 s->ipc2581)
```

   Список плёнок — `axlGetParam("artwork")->groupMembers`; атрибут
   полярности — `negative`. Пересоздание через `axlFilmCreate`
   («creates or replaces»).
4. Проверка gerber (обязательна): в .art негативного плана вырез —
   clear-секция: `%LPC*` + контур прямоугольника с координатами
   выреза между `%LPD*`-заливкой всей платы и `M02`. Разбор — grep
   по `%LPC*` и координатам.

## Чем подтверждено

Плата с изоляционной полосой на двух внутренних негативных планах:
etch-фигура — 4 DRC против keepout (и при касании, и при перекрытии);
anti-etch — 0 DRC; позитивная плёнка — artwork ERROR по полярности;
негативная без ANTI ETCH — файлы созданы, выреза в gerber нет
(разбор .art); негативная со слоем ANTI ETCH — в .art clear-прямо-
угольник точно по координатам выреза. DRC до/после — счётчиком.
