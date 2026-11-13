# -*- coding: utf-8 -*-
"""SES: разбор сессии трассировщика без Allegro.

    python tests\\test_ses.py

Проверяется парсер ses.py на синтетической сессии (формат — из
документации трассировщика и снят с реальной сессии): координаты в
единицах resolution, via на уровне цепи, генерация SKILL.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from alkit import ses  # noqa: E402

SES = r"""(session .\final.ses
 (routes
  (resolution MM 10000)
  (parser (host_cad allegro))
  (structure_out
   (layer TOP (type signal))
   (layer BOTTOM (type signal)))
  (network_out
   (Net 'CLK1'
    (wire (path TOP 2500  100000 200000 100000 400000)
     (connect (terminal via) (terminal smd R1.1)))
    (wire (path BOTTOM 2500  100000 400000 200000 400000)
     (connect (terminal via) (terminal via)))
    (via VIA50 100000 400000)
    (via VIA50 100000 200000 (attr fanout)))
   (Net 'D1'
    (wire (path TOP 2000  500000 500000 600000 500000)
     (connect (terminal smd U1.1) (terminal smd U1.2)))))))"""

ak = None


def _try(fn):
    try:
        fn()
        return False
    except ValueError:
        return True


r_ok = []
r_fail = []


def check(name, cond):
    (r_ok if cond else r_fail).append(name)
    print(("OK  " if cond else "FAIL") + " " + name)


s = ses.Session(SES)
check("unit=10000", s.unit == 10000)
check("wires=3", len(s.wires) == 3)
check("vias=2", len(s.vias) == 2)
w0 = s.wires[0]
check("net name", w0[0] == "CLK1")
check("layer", w0[1] == "TOP")
check("width 0.25", abs(w0[2] - 0.25) < 1e-9)
check("coord mm", abs(w0[3][0][0] - 10.0) < 1e-9
      and abs(w0[3][1][1] - 40.0) < 1e-9)
v1 = s.vias[0]
check("via flat", v1[1] == "VIA50" and abs(v1[2] - 10.0) < 1e-9)

il, nw, nv = s.to_skill()
check("skill wires", nw == 3)
check("skill vias", nv == 2)
check("etch subclass", '"etch/TOP"' in il)
check("net quoted", '"CLK1"' in il)
check("via call", 'axlDBCreateVia("VIA50"' in il)

check("unbalanced paren", _try(lambda: ses.Session("(session (x")))
check("unbalanced paren2", _try(lambda: ses.Session("session x)")))

print("итог: ok=%d fail=%d" % (len(r_ok), len(r_fail)))
sys.exit(1 if r_fail else 0)
