import re
import shutil
import sys
from pathlib import Path

import pytest

from deepwick_spec.ansi import line_with, runs, style_of
from deepwick_spec.check_port import check_port
from deepwick_spec.palette import ANSI_KEYS, load_palette
from deepwick_spec.tui import capture, tmux_available
from deepwick_spec.xterm256 import nearest_index

REPO = Path(__file__).resolve().parents[1]
SAMPLES = Path(__file__).resolve().parent / "samples"
PALETTE = load_palette()
C = PALETTE.colors
sys.path.insert(0, str(REPO))
COLORS = REPO / "colors" / "deepwick.vim"

requires_vim = pytest.mark.skipif(not (tmux_available() and shutil.which("vim")), reason="requires tmux and vim")


def hexof(name):
    return C[name].lower()


def hi_lines():
    """group -> {key: value} for each `hi` line; links as {'link': target}."""
    groups = {}
    for line in COLORS.read_text(encoding="utf-8").splitlines():
        if m := re.match(r"hi! link (\w+) (\w+)$", line):
            groups[m.group(1)] = {"link": m.group(2)}
        elif m := re.match(r"hi (\w+) (.*)$", line):
            groups[m.group(1)] = dict(kv.split("=", 1) for kv in m.group(2).split())
    return groups


def resolve(group):
    groups = hi_lines()
    while "link" in groups[group]:
        group = groups[group]["link"]
    return groups[group]


def gui_attrs(spec):
    return set() if spec["gui"] == "NONE" else set(spec["gui"].split(","))


def test_committed_file_matches_generator():
    import generate
    assert COLORS.read_text(encoding="utf-8") == generate.render_colors(PALETTE)


def test_every_hi_line_has_gui_and_cterm():
    for group, spec in hi_lines().items():
        if "link" in spec:
            continue
        for gui, cterm in (("guifg", "ctermfg"), ("guibg", "ctermbg")):
            assert gui in spec and cterm in spec, group
            if spec[gui] != "NONE" and spec[cterm] != "NONE" and not group.startswith("Diff"):
                assert int(spec[cterm]) == nearest_index(spec[gui]), (group, gui)
            if spec[cterm] != "NONE":
                assert int(spec[cterm]) >= 16, (group, cterm)
        assert spec["cterm"] == spec["gui"].replace("undercurl", "underline"), group


def test_terminal_background_is_left_to_the_terminal():
    assert hi_lines()["Normal"]["guibg"].lower() == hexof("background")
    assert hi_lines()["Normal"]["ctermbg"] == "NONE"


def test_header():
    text = COLORS.read_text(encoding="utf-8")
    for needle in ("set background=dark", "hi clear", "if exists('syntax_on')", "syntax reset",
                   "let g:colors_name = 'deepwick'"):
        assert needle in text, needle
    ansi = re.search(r"let g:terminal_ansi_colors = \[(.*)\]", text).group(1)
    assert re.findall(r"'(#[0-9a-fA-F]{6})'", ansi) == [PALETTE.ansi[k] for k in ANSI_KEYS]


ROLE_GROUPS = {
    "comment": ["Comment", "SpecialComment"],
    "keyword": ["Keyword", "Statement", "StorageClass", "Boolean"],
    "controlFlow": ["Conditional", "Repeat", "Exception", "Include"],
    "operator": ["Operator", "Delimiter"],
    "type": ["Type", "Typedef"],
    "interface": ["Structure"],
    "function": ["Function"],
    "macro": ["Macro"],
    "variable": ["Identifier"],
    "constant": ["Constant"],
    "string": ["String", "Character"],
    "escape": ["Special", "SpecialChar"],
    "number": ["Number", "Float"],
    "tag": ["Tag"],
    "preprocessor": ["PreProc", "PreCondit"],
    "preprocessorKeyword": ["Define"],
    "label": ["Label"],
    "heading": ["Title"],
    "invalid": ["Error"],
}


@pytest.mark.parametrize("role", ROLE_GROUPS)
def test_syntax_roles(role):
    style = PALETTE.syntax[role]
    for group in ROLE_GROUPS[role]:
        spec = resolve(group)
        assert spec["guifg"].lower() == hexof(style.color), group
        assert set(style.style) <= gui_attrs(spec), group


UI = {
    "Normal": ("foreground", "background", set()),
    "CursorLine": (None, "surface", set()),
    "CursorLineNr": ("foreground", None, {"bold"}),
    "LineNr": ("muted", None, set()),
    "SignColumn": (None, "background", set()),
    "Folded": ("comment", "surface", set()),
    "WinSeparator": ("overlay", None, set()),
    "StatusLine": ("foreground", "surface", set()),
    "StatusLineNC": ("muted", "surface", set()),
    "TabLine": ("muted", "surface", set()),
    "TabLineSel": ("foreground", "background", {"bold"}),
    "Pmenu": ("foreground", "surface", set()),
    "PmenuSel": ("foreground", "selection", set()),
    "PmenuThumb": (None, "muted", set()),
    "Visual": (None, "selection", set()),
    "Search": (None, "selection", set()),
    "CurSearch": ("gold", "selection", {"bold"}),
    "IncSearch": ("gold", "selection", {"bold"}),
    "MatchParen": ("gold", None, {"bold"}),
    "NonText": ("muted", None, set()),
    "EndOfBuffer": ("background", None, set()),
    "SpecialKey": ("muted", None, set()),
    "Directory": ("blue", None, set()),
    "ErrorMsg": ("red", None, set()),
    "WarningMsg": ("yellow", None, set()),
    "MoreMsg": ("green", None, set()),
    "ModeMsg": ("foreground", None, {"bold"}),
    "Question": ("blue", None, set()),
    "QuickFixLine": (None, "selection", set()),
    "ColorColumn": (None, "surface", set()),
    "DiffAdd": (None, "diffAdded", set()),
    "DiffChange": (None, "diffChanged", set()),
    "DiffDelete": ("red", "diffRemoved", set()),
    "DiffText": (None, "diffText", set()),
    "Added": ("green", None, set()),
    "Changed": ("blue", None, set()),
    "Removed": ("red", None, set()),
    "Todo": ("blue", None, {"bold"}),
}


@pytest.mark.parametrize("group", UI)
def test_ui_groups(group):
    fg, bg, attrs = UI[group]
    spec = resolve(group)
    assert spec["guifg"].lower() == (hexof(fg) if fg else "none"), group
    assert spec["guibg"].lower() == (hexof(bg) if bg else "none"), group
    assert attrs <= gui_attrs(spec), group


def test_vert_split_follows_win_separator():
    assert resolve("VertSplit") == resolve("WinSeparator")


@pytest.mark.parametrize(("group", "color"), [("SpellBad", "red"), ("SpellCap", "yellow"), ("SpellLocal", "cyan"), ("SpellRare", "magenta")])
def test_spell_undercurls(group, color):
    spec = resolve(group)
    assert spec["guisp"].lower() == hexof(color) and "undercurl" in gui_attrs(spec)
    assert spec["cterm"] == "underline" and spec["ctermfg"] == str(nearest_index(C[color]))


@pytest.mark.parametrize(("group", "color"), [("DiffAdd", "green"), ("DiffChange", "blue"), ("DiffDelete", "red")])
def test_cterm_diffs_use_git_colors(group, color):
    spec = resolve(group)
    assert spec["ctermfg"] == str(nearest_index(C[color])) and spec["ctermbg"] == "NONE"


def test_cterm_diff_text_stands_out_from_diff_change():
    spec = resolve("DiffText")
    assert spec["ctermbg"] == str(nearest_index(C["selection"]))
    assert (spec["ctermfg"], spec["ctermbg"]) != (resolve("DiffChange")["ctermfg"], resolve("DiffChange")["ctermbg"])


VIM_ONLY = {
    "pythonDecorator": ("yellow", set()), "pythonDecoratorName": ("yellow", set()),
    "pythonBuiltin": ("yellow", set()), "pythonClassVar": ("blue", set()), "pythonClass": ("teal", set()), "pythonExceptions": ("teal", set()),
    "cInclude": ("foreground", {"bold"}), "cPreCondit": ("foreground", {"bold"}), "cPreProc": ("foreground", {"bold"}),
    "cDefine": ("magenta", set()), "cConstant": ("magenta", set()),
}


@pytest.mark.parametrize("group", VIM_ONLY)
def test_vim_only_groups(group):
    color, attrs = VIM_ONLY[group]
    spec = resolve(group)
    assert spec["guifg"].lower() == hexof(color)
    assert attrs <= gui_attrs(spec)


def vimrc(tmp_path, truecolor=True, scheme=True):
    lines = ["set nocompatible", f"set rtp^={REPO}", "syntax on"]
    if truecolor:
        lines += ["set termguicolors", 'let &t_8f = "\\e[38;2;%lu;%lu;%lum"', 'let &t_8b = "\\e[48;2;%lu;%lu;%lum"']
    else:
        lines += ["set t_Co=256"]
    if scheme:
        lines.append("colorscheme deepwick")
    path = tmp_path / "vimrc"
    path.write_text("\n".join(lines) + "\n")
    return path


def isolated_env(tmp_path):
    dirs = {"HOME": tmp_path / "home"}
    for kind in ("CONFIG", "DATA", "STATE", "CACHE"):
        dirs[f"XDG_{kind}_HOME"] = tmp_path / kind.lower()
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)
    env = {key: str(path) for key, path in dirs.items()}
    env["TERM"] = "tmux-256color"
    return env


def vim(tmp_path, sample, **kwargs):
    rc = vimrc(tmp_path, **kwargs)
    return capture(f"vim -Nu {rc} -i NONE {SAMPLES / sample}", isolated_env(tmp_path), size=(100, 50), wait_for="def" if sample.endswith(".py") else "include")


PY_TOKENS = [("def", "blue"), ("if", "magenta"), ("import", "magenta"), ("3", "sage"), ('"no one to greet"', "orange"),
             ("# Escape sequences and f-strings", "comment"), ("@dataclass", "yellow"), ("print", "yellow"), ("ValueError", "teal")]


@requires_vim
def test_renders_truecolor(tmp_path):
    out = vim(tmp_path, "sample.py")
    for token, color in PY_TOKENS:
        assert style_of(out, token)["fg"] == hexof(color), token
    assert style_of(out, "# Escape sequences and f-strings")["italic"]


@requires_vim
def test_renders_256(tmp_path):
    out = vim(tmp_path, "sample.py", truecolor=False)
    for token, color in PY_TOKENS:
        assert style_of(out, token)["fg"] == f"ansi256:{nearest_index(C[color])}", token


@requires_vim
def test_renders_c(tmp_path):
    out = vim(tmp_path, "sample.c")
    include = style_of(out, "#include")
    assert include["fg"] == hexof("foreground") and include["bold"]
    assert style_of(line_with(out, "#define MAX_RETRIES"), "#define MAX_RETRIES")["fg"] == hexof("magenta")


@requires_vim
def test_without_colorscheme_assertions_fail(tmp_path):
    out = vim(tmp_path, "sample.py", scheme=False)
    assert style_of(out, "def")["fg"] != hexof("blue")


def test_port_conventions():
    assert check_port(REPO, PALETTE.allowed_hex()) == []


AIRLINE = REPO / "autoload" / "airline" / "themes" / "deepwick.vim"


def test_airline_matches_generator():
    import generate
    assert AIRLINE.read_text(encoding="utf-8") == generate.render_airline(PALETTE)


def test_airline_has_no_nvim_guard():
    text = AIRLINE.read_text(encoding="utf-8")
    assert "has('nvim')" not in text and "luaeval" not in text


def entry(fg, bg, attr=""):
    return [C[fg], C[bg], nearest_index(C[fg]), nearest_index(C[bg]), attr]


@pytest.mark.skipif(shutil.which("vim") is None, reason="requires vim")
def test_airline_palette(tmp_path):
    import json
    import subprocess
    stub = tmp_path / "rt" / "autoload" / "airline" / "themes.vim"
    stub.parent.mkdir(parents=True)
    out = tmp_path / "palette.json"
    stub.write_text(
        "function! airline#themes#generate_color_map(a, b, c) abort\n"
        "  return {'airline_a': a:a, 'airline_b': a:b, 'airline_c': a:c}\n"
        "endfunction\n"
    )
    script = tmp_path / "dump.vim"
    script.write_text(
        f"set rtp^={tmp_path / 'rt'}\nsource {AIRLINE}\n"
        f"call writefile([json_encode(g:airline#themes#deepwick#palette)], '{out}')\n"
    )
    subprocess.run(["vim", "-Nu", "NONE", "-i", "NONE", "-es", "-S", str(script), "-c", "qa!"],
                   env={"HOME": str(tmp_path), "PATH": "/usr/bin:/bin"}, check=True, timeout=20)
    palette = json.loads(out.read_text())
    for mode, color in (("normal", "blue"), ("insert", "green"), ("visual", "magenta"), ("replace", "red"), ("commandline", "yellow")):
        assert palette[mode]["airline_a"] == entry("background", color, "bold"), mode
        assert palette[mode]["airline_b"] == entry("foreground", "overlay"), mode
        assert palette[mode]["airline_c"] == entry("foreground", "surface"), mode
    assert palette["inactive"]["airline_a"] == entry("muted", "surface")
    for mode in ("normal", "insert", "visual", "replace"):
        assert palette[f"{mode}_modified"]["airline_c"] == entry("yellow", "surface"), mode
    assert palette["accents"]["red"] == [C["red"], "", nearest_index(C["red"]), "", ""]


@requires_vim
@pytest.mark.parametrize("truecolor", [True, False])
def test_python_constants_are_keywords(tmp_path, truecolor):
    rc = vimrc(tmp_path, truecolor=truecolor)
    out = capture(f"vim -Nu {rc} -i NONE {SAMPLES / 'constants.py'}", isolated_env(tmp_path), size=(60, 6), wait_for="value")
    want = hexof("blue") if truecolor else f"ansi256:{nearest_index(C['blue'])}"
    for token in ("None", "True", "False"):
        assert style_of(out, token)["fg"] == want, token


@requires_vim
def test_python_constants_with_older_python_syntax(tmp_path):
    # Vim 9.1 (Ubuntu 24.04) lists True/False/None as pythonBuiltin, linked to Function.
    old = tmp_path / "old" / "syntax"
    old.mkdir(parents=True)
    (old / "python.vim").write_text(
        "syn keyword pythonStatement False None True\n"
        "syn keyword pythonBuiltin False True None\n"
        "syn match pythonAssign '\\<value\\>'\n"
        "hi def link pythonStatement Statement\n"
        "hi def link pythonBuiltin Function\n"
        "let b:current_syntax = 'python'\n"
    )
    rc = vimrc(tmp_path)
    rc.write_text(f"set rtp^={old.parent}\n" + rc.read_text())
    out = capture(f"vim -Nu {rc} -i NONE {SAMPLES / 'constants.py'}", isolated_env(tmp_path), size=(60, 6), wait_for="value")
    for token in ("None", "True", "False"):
        assert style_of(out, token)["fg"] == hexof("blue"), token
