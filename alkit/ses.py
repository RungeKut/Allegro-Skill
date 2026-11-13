# -*- coding: utf-8 -*-
"""Сессия трассировщика (SES) → SKILL-код импорта в плату.

Форма specctra_in может висеть вечно (30-11), поэтому надёжный путь —
разобрать SES и создать проводники и переходные напрямую:

    import alkit as ak
    w, v, il = ak.ses.to_skill("final.ses")
    ak.run(плата, il, save_to=новый_файл)

Заливка — приём 20-06: axlDBCreatePath с именем цепи, axlDBCreateVia.
Единицы координат берутся из (resolution MM 10000) — 10000 ед. на мм.
"""
import io
import os

# слой SES → subclass etch
ETCH = "etch/{}"


def tokenize(text):
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c in " \t\r\n":
            i += 1
        elif c in "()":
            yield c
            i += 1
        elif c == "'":
            j = text.find("'", i + 1)
            if j < 0:
                raise ValueError("незакрытая строка в позиции %d" % i)
            yield text[i + 1:j]
            i = j + 1
        else:
            j = i
            while j < n and text[j] not in " \t\r\n()'":
                j += 1
            yield text[i:j]
            i = j


def parse(text):
    """S-выражение SES → вложенные списки."""
    stack = [[]]
    for t in tokenize(text):
        if t == "(":
            new = []
            stack[-1].append(new)
            stack.append(new)
        elif t == ")":
            if len(stack) == 1:
                raise ValueError("лишняя закрывающая скобка")
            stack.pop()
        else:
            stack[-1].append(t)
    if len(stack) != 1:
        raise ValueError("не закрыто %d скобок" % (len(stack) - 1))
    return stack[0]


def walk(node, tag):
    """Все поддеревья, чей первый элемент == tag."""
    out = []
    if isinstance(node, list):
        if node and node[0] == tag:
            out.append(node)
        for ch in node:
            out.extend(walk(ch, tag))
    return out


def _resolution(root):
    for res in walk(root, "resolution"):
        if len(res) >= 3 and str(res[1]).upper() == "MM":
            return int(res[2])
    return 10000


class Session:
    """Разобранная сессия: провода, переходные, полигоны, единицы."""

    def __init__(self, text):
        self.root = parse(text)
        self.unit = _resolution(self.root)
        self.wires = []       # (net, layer, width_mm, [pts_mm])
        self.vias = []        # (net, padstack, x_mm, y_mm)
        self.shapes = 0
        for net in walk(self.root, "network_out"):
            for n in net:
                if not (isinstance(n, list) and n and n[0] in ("Net", "net")):
                    continue
                name = n[1]
                for wire in walk(n, "wire"):
                    for path in walk(wire, "path"):
                        layer, width = path[1], path[2]
                        coords = path[3:]
                        pts = [(int(coords[i]) / self.unit,
                                int(coords[i + 1]) / self.unit)
                               for i in range(0, len(coords) - 1, 2)]
                        self.wires.append((name, layer, int(width) / self.unit,
                                           pts))
                self.shapes += len(walk(wire, "shape"))
                for via in walk(n, "via"):
                    if len(via) >= 4 and isinstance(via[1], str):
                        self.vias.append((name, via[1],
                                          int(via[2]) / self.unit,
                                          int(via[3]) / self.unit))

    @classmethod
    def from_file(cls, path, encoding="cp1251"):
        with io.open(path, encoding=encoding, errors="replace") as f:
            return cls(f.read())

    def to_skill(self, via_pad=None):
        """SKILL-код импорта: пути и переходные; возвращает (код, счётчики).

        via_pad — заменить падстек всех переходных (если сессия ссылается
        на переходную, которой нет в плате-приёмнике).
        """
        lines = ["n_w = 0", "n_v = 0"]
        for name, layer, width, pts in self.wires:
            s = " ".join("%.4f:%.4f" % p for p in pts)
            lines.append("p = axlPathStart(list(%s) %s)" % (s, width))
            lines.append('when(axlDBCreatePath(p "%s" "%s") n_w = n_w + 1)'
                         % (ETCH.format(layer), name))
        for name, pad, x, y in self.vias:
            if via_pad:
                pad = via_pad
            lines.append('when(axlDBCreateVia("%s" %.4f:%.4f "%s") '
                         "n_v = n_v + 1)" % (pad, x, y, name))
        lines.append('fprintf(akPort "wires=%L vias=%L\\n" n_w n_v)')
        return "\n".join(lines) + "\n", len(self.wires), len(self.vias)


def import_session(ses_path, board, save_to, timeout=900, via_pad=None):
    """Залить сессию в плату; возвращает Result alkit и счётчики."""
    from . import batch
    ses = Session.from_file(ses_path)
    il, nw, nv = ses.to_skill(via_pad=via_pad)
    r = batch.run(board, il, save_to=save_to,
                  outputs=["port.txt"], timeout=timeout)
    return r, ses
