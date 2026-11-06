
"""Test tambahan buatan kelompok.

Berisi tes regresi untuk bug yang diperbaiki dan lima tes kasus tepi.
"""

import pytest

from crud import ast_nodes as ast
from crud.lexer import tokenize, LexError, TokenType
from crud.parser import parse_sql
from crud.resolver import Resolver


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
