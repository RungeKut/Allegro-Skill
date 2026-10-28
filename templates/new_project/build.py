# -*- coding: utf-8 -*-
"""Сценарий проекта: проверить плату, сверить со схемой, расставить,
проверить снова, выгрузить файлы. Данные — в params.py.

Запуск:  python build.py

Скопировав шаблон в папку проекта, впишите в KIT корень набора allegro —
папку, из которой прочитан его SKILL.md.
"""
import os
import sys

KIT = r""


def kit_root():
    """Корень набора allegro: KIT, иначе набор, в котором лежит этот файл."""
    here = os.path.dirname(os.path.abspath(__file__))
    for cand in (KIT, os.path.dirname(os.path.dirname(here))):
        if cand and os.path.isdir(os.path.join(cand, "alkit")):
            return cand
    raise RuntimeError("набор allegro не найден: впишите в KIT (build.py) "
                       "папку, из которой прочитан SKILL.md набора")


sys.path.insert(0, kit_root())
import alkit as ak          # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import params as P          # noqa: E402


def main():
    ak.utf8_console()
    os.makedirs(P.OUT_DIR, exist_ok=True)
    print("Allegro", ak.version())

    # 1. исходная плата: числа и картинка
    b = ak.dump(P.BOARD)
    print(b)
    ak.png(b, os.path.join(P.OUT_DIR, "исх_верх.png"), side="top")
    ak.png(b, os.path.join(P.OUT_DIR, "исх_низ.png"), side="bottom")
    s = ak.summary(P.BOARD)
    print("DRC по отчёту:", s.get("DRC Errors"), " по выгрузке:", len(b.drcs))

    ok = True
    # 2. сверка со схемой
    if P.SCHEMATIC:
        sch = ak.read_dsn(P.SCHEMATIC)
        print(sch)
        ok &= ak.compare(sch, b, ignore=P.SCH_IGNORE)

    # 3. расстановка — в новый файл
    board = P.BOARD
    if P.PLACEMENTS:
        ak.place(P.BOARD, P.PLACEMENTS, save_to=P.BOARD_OUT)
        board = P.BOARD_OUT
        b2 = ak.dump(board)
        r = ak.Report("расстановка")
        for ref, v in P.PLACEMENTS.items():
            v = list(v) + [None] * (4 - len(v))
            sym = b2.sym(ref)
            if v[0] is not None:
                r.close_to("%s X" % ref, sym["xy"][0], v[0], tol=1e-3)
            if v[1] is not None:
                r.close_to("%s Y" % ref, sym["xy"][1], v[1], tol=1e-3)
            if v[2] is not None:
                r.close_to("%s угол" % ref, sym["rot"], float(v[2]),
                           tol=1e-6)
            if v[3] is not None:
                r.equal("%s сторона" % ref,
                        "bottom" if sym["mirror"] else "top", v[3])
        r.equal("компонентов", len(b2.comps), len(b.comps))
        ok &= r.done()
        ak.png(b2, os.path.join(P.OUT_DIR, "нов_верх.png"), side="top")
        ak.png(b2, os.path.join(P.OUT_DIR, "нов_низ.png"), side="bottom")

    # 4. выходные файлы
    if P.EXPORT_GERBER:
        g = ak.gerber(board, os.path.join(P.OUT_DIR, "gerber"))
        print("Gerber:", len(g["paths"]), "файлов")
    if P.EXPORT_IPC2581:
        i = ak.ipc2581(board, os.path.join(P.OUT_DIR, "плата.xml"))
        print("IPC-2581:", i["components"], "компонентов")
    if P.EXPORT_STEP:
        st = ak.step(board, os.path.join(P.OUT_DIR, "плата.stp"))
        print("STEP:", st["bytes"], "байт; контур выброшен:",
              st["outline_dropped"])
        ok &= st["outline_dropped"] == 0
    if P.EXPORT_PDF:
        ak.pdf(board, os.path.join(P.OUT_DIR, "плата.pdf"))

    print("\nИТОГ:", "всё сошлось" if ok else "ЕСТЬ РАСХОЖДЕНИЯ")
    print("Картинки — в", P.OUT_DIR, "— посмотрите на них.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
