
"""Test tambahan buatan kelompok.

Berisi tes regresi untuk bug yang diperbaiki dan lima tes kasus tepi.
"""

import pytest

from crud import ast_nodes as ast
from crud.lexer import tokenize, LexError, TokenType
from crud.parser import parse_sql
from crud.resolver import Resolver
from crud.parser import parse_sql
from crud.analyzer import analyze_statement
from crud.pipeline import analyze_source

def test_subquery_di_update_hanya_dibaca():
    st = parse_sql(
        "UPDATE a SET x = (SELECT y FROM b) WHERE id IN (SELECT id FROM c)"
    ).statements[0]
    assert analyze_statement(st) == {"a": {"U"}, "b": {"R"}, "c": {"R"}}

def resolve(sql):
    """Parse SQL lalu jalankan Resolver."""
    script = parse_sql(sql)
    assert script.errors == [], script.errors

    resolver = Resolver()
    diagnostics = resolver.resolve_script(script)

    return script, diagnostics


def columns(node):
    """Mengambil seluruh ColumnRef dari AST."""
    return [
        n for n in ast.iter_nodes(node)
        if isinstance(n, ast.ColumnRef)
    ]


# ============================================================
# TES REGRESI
# ============================================================

def test_kolom_tanpa_qualifier_satu_tabel_regresi():
    # Regresi T2: kolom tanpa qualifier harus terhubung ke satu tabel.
    script, diags = resolve(
        "SELECT nama FROM pelanggan p"
    )

    kolom_nama = [
        c for c in columns(script)
        if c.name == "nama" and c.qualifier is None
    ]

    assert len(kolom_nama) == 1
    assert kolom_nama[0].resolved == "pelanggan"
    assert diags == []


def test_alias_shadowing_scope_terdalam_diprioritaskan():
    # Regresi Resolver: alias yang sama di subquery harus memakai scope terdalam.
    sql = """
    SELECT x.id
    FROM pelanggan x
    WHERE x.id IN (
        SELECT x.pelanggan_id
        FROM pesanan x
    )
    """

    script, diags = resolve(sql)

    kolom_x = [
        c for c in columns(script)
        if c.qualifier == "x"
    ]

    assert [c.resolved for c in kolom_x] == [
        "pelanggan",
        "pelanggan",
        "pesanan",
    ]
    assert diags == []


def test_scope_delete_tidak_bocor_ke_statement_berikutnya():
    # Regresi Resolver: alias DELETE tidak boleh digunakan oleh statement berikutnya.
    sql = """
    DELETE FROM sesi s WHERE s.kedaluwarsa = 1;
    SELECT s.id FROM pengguna u WHERE u.aktif = 1;
    """

    _, diags = resolve(sql)

    assert len(diags) == 1
    assert diags[0].level == "error"
    assert "alias 's' tidak terdefinisi" in diags[0].message


def test_lexer_mengabaikan_komentar_blok_multibaris():
    # Regresi T3: komentar blok tidak boleh menghasilkan token.
    tokens = tokenize("/* komentar\n   dua baris */ SELECT")

    token_select = next(
        token for token in tokens
        if token.type != TokenType.EOF
    )

    assert token_select.type == TokenType.KEYWORD
    assert token_select.value == "SELECT"
    assert token_select.line == 2


# ============================================================
# LIMA TES KASUS TEPI (EDGE CASES)
# ============================================================

def test_kolom_tanpa_qualifier_ambigu():
    # Berisiko karena dua tabel memiliki kemungkinan sumber kolom yang sama.
    script, diags = resolve(
        "SELECT id FROM pelanggan p JOIN pesanan o ON p.id = o.pelanggan_id"
    )

    kolom_id = [
        c for c in columns(script)
        if c.name == "id" and c.qualifier is None
    ]

    assert len(kolom_id) == 1
    assert kolom_id[0].resolved is None
    assert any(
        d.level == "warning"
        and "ambigu tanpa skema" in d.message
        for d in diags
    )


def test_kolom_tanpa_qualifier_tanpa_tabel():
    # Berisiko karena ekspresi tidak memiliki sumber tabel untuk resolusi kolom.
    script, diags = resolve(
        "INSERT INTO log_akses (id) VALUES (nama)"
    )

    kolom_nama = [
        c for c in columns(script)
        if c.name == "nama"
    ]

    assert len(kolom_nama) == 1
    assert kolom_nama[0].resolved is None
    assert any(
        d.level == "warning"
        and "tidak memiliki tabel sumber" in d.message
        for d in diags
    )


def test_kolom_tanpa_qualifier_satu_subquery():
    # Berisiko karena sumber kolom berasal dari subquery, bukan tabel langsung.
    script, _ = resolve(
        "SELECT nama FROM (SELECT nama FROM pelanggan) p"
    )

    kolom_luar = [
        c for c in columns(script)
        if c.name == "nama"
        and c.resolved == "<subquery p>"
    ]

    assert len(kolom_luar) == 1


def test_lexer_error_jika_komentar_blok_tidak_ditutup():
    # Berisiko karena komentar yang tidak ditutup dapat menelan sisa SQL.
    with pytest.raises(
        LexError,
        match="komentar blok tidak ditutup"
    ):
        tokenize("SELECT /* komentar")


def test_lexer_komentar_blok_kosong():
    # Berisiko karena komentar tanpa isi tetap harus dikenali sebagai komentar.
    tokens = tokenize("/**/ SELECT")

    token_select = next(
        token for token in tokens
        if token.type != TokenType.EOF
    )

    assert token_select.type == TokenType.KEYWORD
    assert token_select.value == "SELECT"

def _tipe_nilai(sql):
    """Daftar (tipe, nilai) token tanpa EOF, supaya assert mudah dibaca."""
    return [(t.type, t.value) for t in tokenize(sql) if t.type != TokenType.EOF]


# ---------- Bug 1: keyword tidak peka huruf besar/kecil (SPEK 2.2) ----------

def test_keyword_tidak_peka_huruf_besar_kecil():
    # Regresi bug 1: select/Select/SELECT sama-sama KEYWORD bernilai SELECT.
    # Kata yang hanya diawali keyword (selection, fromage) tetap IDENT.
    hasil = _tipe_nilai("select Select SELECT selection fromage")

    assert hasil[:3] == [(TokenType.KEYWORD, "SELECT")] * 3
    assert hasil[3] == (TokenType.IDENT, "selection")
    assert hasil[4] == (TokenType.IDENT, "fromage")


# ---------- Bug 2: operator <> adalah satu token (SPEK 2.5) ----------

def test_operator_tidak_sama_dengan_satu_token():
    # Regresi bug 2: <> harus satu token OP (maximal munch), dengan atau tanpa spasi.
    assert _tipe_nilai("a <> b") == [
        (TokenType.IDENT, "a"), (TokenType.OP, "<>"), (TokenType.IDENT, "b"),
    ]
    assert _tipe_nilai("a<>b") == [
        (TokenType.IDENT, "a"), (TokenType.OP, "<>"), (TokenType.IDENT, "b"),
    ]
    # Operator lain yang berawalan < tidak boleh rusak.
    assert [v for _, v in _tipe_nilai("a<b a<=b")] == ["a", "<", "b", "a", "<=", "b"]


# ---------- Bug 3: '' di dalam string = satu kutip (SPEK 2.4) ----------

def test_escape_dua_kutip_di_dalam_string():
    # Regresi bug 3: 'O''Brien' adalah SATU token STRING bernilai O'Brien.
    assert _tipe_nilai("'O''Brien'") == [(TokenType.STRING, "O'Brien")]
    # String kosong tetap satu token STRING.
    assert _tipe_nilai("''") == [(TokenType.STRING, "")]


def test_string_tidak_ditutup_adalah_lex_error():
    # Pelengkap bug 3: perbaikan tidak boleh membuat string tak tertutup lolos.
    with pytest.raises(LexError):
        tokenize("'abc")


# ---------- Bug 4: AND lebih kuat dari OR (SPEK 3.1) ----------

def _where(sql):
    script = parse_sql(sql)
    assert script.errors == [], script.errors
    return script.statements[0].where


def test_and_lebih_kuat_dari_or():
    # Regresi bug 4: a=1 OR b=2 AND c=3  ->  a=1 OR (b=2 AND c=3)
    w = _where("SELECT a FROM t WHERE a = 1 OR b = 2 AND c = 3")
    assert w.op == "OR"
    assert w.left.op == "="
    assert w.right.op == "AND"

    # Urutan dibalik: a=1 AND b=2 OR c=3  ->  (a=1 AND b=2) OR c=3
    w = _where("SELECT a FROM t WHERE a = 1 AND b = 2 OR c = 3")
    assert w.op == "OR"
    assert w.left.op == "AND"
    assert w.right.op == "="


def test_between_and_tidak_terganggu_presedensi():
    # Pelengkap bug 4: AND milik BETWEEN tidak boleh dianggap AND logika.
    w = _where("SELECT a FROM t WHERE x BETWEEN 1 AND 2 OR y = 3")
    assert w.op == "OR"
    assert isinstance(w.left, ast.Between)


# ---------- Bug 5: LEFT OUTER JOIN (SPEK 3, grammar join) ----------

def test_left_outer_join_diterima():
    # Regresi bug 5: OUTER setelah LEFT bersifat opsional.
    script = parse_sql("SELECT a FROM t LEFT OUTER JOIN u ON t.id = u.id")
    assert script.errors == [], script.errors
    assert script.statements[0].joins[0].kind == "LEFT"


def test_outer_join_tanpa_left_tetap_error():
    # Pelengkap bug 5: OUTER hanya sah setelah LEFT.
    script = parse_sql("SELECT a FROM t OUTER JOIN u ON t.id = u.id")
    assert len(script.errors) == 1


# ---------- Bug 6: error recovery panic mode (SPEK 6) ----------

def test_error_recovery_berhenti_di_titik_koma():
    # Regresi bug 6: satu statement rusak = tepat satu error,
    # dan statement valid sesudahnya tetap dianalisis.
    hasil = analyze_source("SELEC x;\nSELECT a FROM t;\nDELETE FROM q;")
    assert len(hasil.parse_errors) == 1
    assert hasil.matrix() == {"t": "R", "q": "D"}


def test_error_recovery_token_error_adalah_titik_koma():
    # Pelengkap bug 6: error terdeteksi tepat di ';', statement berikutnya selamat.
    hasil = analyze_source("SELECT a FROM ;\nDELETE FROM q;")
    assert len(hasil.parse_errors) == 1
    assert hasil.matrix() == {"q": "D"}


# ---------- T1: INSERT ... SELECT (SPEK 3 dan 5) ----------

def test_insert_select_c_dan_r():
    # Regresi T1: tabel tujuan C, tabel sumber SELECT R.
    hasil = analyze_source(
        "INSERT INTO arsip (id) SELECT id FROM pesanan WHERE total > 10;"
    )
    assert hasil.parse_errors == []
    assert hasil.matrix() == {"arsip": "C", "pesanan": "R"}