from __future__ import annotations

from escada.app import _lances_padrao_dois_lances
from escada.defaults import escada_metallo


def test_lances_padrao_dois_lances_comecam_balanceados():
    lance1, lance2 = _lances_padrao_dois_lances()

    assert [vao.tipo for vao in lance1.vaos] == ["patamar", "escada", "patamar"]
    assert [vao.tipo for vao in lance2.vaos] == ["patamar", "escada", "patamar"]
    assert lance1.vaos[0].L == lance1.vaos[2].L
    assert lance2.vaos[0].L == lance2.vaos[2].L
    assert lance1.comprimento_total == lance2.comprimento_total
    assert lance1.comprimento_total == 3.85


def test_defaults_com_tres_lances_amarram_b1_e_b3_aos_patamares_do_lance_2():
    escada = escada_metallo()
    lance1, lance2, lance3 = escada.lances

    assert lance1.b == lance2.vaos[0].L
    assert lance3.b == lance2.vaos[2].L
