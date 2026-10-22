"""Write colors/deepwick.vim from the Deepwick palette.

Run from this directory: PYTHONPATH=../spec python3 generate.py
"""
from pathlib import Path

from deepwick_spec.palette import ANSI_KEYS, Palette, load_palette
from deepwick_spec.xterm256 import nearest_index

COLORS_OUT = Path(__file__).with_name("colors") / "deepwick.vim"

# group: (fg, bg, attrs, sp) as palette color names; None leaves it unset.
GROUPS: dict[str, tuple] = {
    # Editor UI
    "Normal": ("foreground", "background", (), None),
    "Cursor": ("background", "foreground", (), None),
    "CursorLine": (None, "surface", (), None),
    "CursorColumn": (None, "surface", (), None),
    "ColorColumn": (None, "surface", (), None),
    "CursorLineNr": ("foreground", None, ("bold",), None),
    "LineNr": ("muted", None, (), None),
    "SignColumn": (None, "background", (), None),
    "FoldColumn": ("muted", "background", (), None),
    "Folded": ("comment", "surface", (), None),
    "WinSeparator": ("overlay", None, (), None),
    "StatusLine": ("foreground", "surface", (), None),
    "StatusLineNC": ("muted", "surface", (), None),
    "TabLine": ("muted", "surface", (), None),
    "TabLineFill": (None, "background", (), None),
    "TabLineSel": ("foreground", "background", ("bold",), None),
    "Pmenu": ("foreground", "surface", (), None),
    "PmenuSel": ("foreground", "selection", (), None),
    "PmenuSbar": (None, "overlay", (), None),
    "PmenuThumb": (None, "muted", (), None),
    "PmenuKind": ("teal", "surface", (), None),
    "PmenuExtra": ("muted", "surface", (), None),
    "PmenuMatch": ("blue", "surface", ("bold",), None),
    "PmenuMatchSel": ("blue", "selection", ("bold",), None),
    "Visual": (None, "selection", (), None),
    "Search": (None, "selection", (), None),
    "CurSearch": ("gold", "selection", ("bold",), None),
    "IncSearch": ("gold", "selection", ("bold",), None),
    "MatchParen": ("gold", None, ("bold",), None),
    "NonText": ("muted", None, (), None),
    "EndOfBuffer": ("background", None, (), None),
    "SpecialKey": ("muted", None, (), None),
    "Conceal": ("muted", None, (), None),
    "Directory": ("blue", None, (), None),
    "Title": ("blue", None, ("bold",), None),
    "ErrorMsg": ("red", None, (), None),
    "WarningMsg": ("yellow", None, (), None),
    "MoreMsg": ("green", None, (), None),
    "ModeMsg": ("foreground", None, ("bold",), None),
    "Question": ("blue", None, (), None),
    "QuickFixLine": (None, "selection", (), None),
    "SpellBad": (None, None, ("undercurl",), "red"),
    "SpellCap": (None, None, ("undercurl",), "yellow"),
    "SpellLocal": (None, None, ("undercurl",), "cyan"),
    "SpellRare": (None, None, ("undercurl",), "magenta"),
    "DiffAdd": (None, "diffAdded", (), None),
    "DiffChange": (None, "diffChanged", (), None),
    "DiffDelete": ("red", "diffRemoved", (), None),
    "DiffText": (None, "diffText", (), None),
    "Added": ("green", None, (), None),
    "Changed": ("blue", None, (), None),
    "Removed": ("red", None, (), None),
    # Legacy syntax, as in the Neovim port
    "Comment": ("comment", None, ("italic",), None),
    "SpecialComment": ("comment", None, ("italic",), None),
    "Constant": ("cyan", None, (), None),
    "String": ("orange", None, (), None),
    "Character": ("orange", None, (), None),
    "Number": ("sage", None, (), None),
    "Float": ("sage", None, (), None),
    "Boolean": ("blue", None, (), None),
    "Identifier": ("lightBlue", None, (), None),
    "Function": ("yellow", None, (), None),
    "Statement": ("blue", None, (), None),
    "Keyword": ("blue", None, (), None),
    "StorageClass": ("blue", None, (), None),
    "Conditional": ("magenta", None, (), None),
    "Repeat": ("magenta", None, (), None),
    "Exception": ("magenta", None, (), None),
    "Include": ("magenta", None, (), None),
    "Label": ("foreground", None, (), None),
    "Operator": ("foreground", None, (), None),
    "Delimiter": ("foreground", None, (), None),
    "PreProc": ("muted", None, ("bold",), None),
    "PreCondit": ("muted", None, ("bold",), None),
    "Define": ("foreground", None, ("bold",), None),
    "Macro": ("magenta", None, (), None),
    "Type": ("teal", None, (), None),
    "Typedef": ("teal", None, (), None),
    "Structure": ("mint", None, (), None),
    "Special": ("gold", None, (), None),
    "SpecialChar": ("gold", None, (), None),
    "Tag": ("blue", None, (), None),
    "Debug": ("magenta", None, (), None),
    "Underlined": (None, None, ("underline",), None),
    "Ignore": ("muted", None, (), None),
    "Error": ("red", None, (), None),
    "Todo": ("blue", None, ("bold",), None),
    # Vim's own syntax files, aligned with bat and the Neovim port's Tree-sitter colors
    "pythonDecorator": ("yellow", None, (), None),
    "pythonDecoratorName": ("yellow", None, (), None),
    "pythonClassVar": ("blue", None, (), None),
    "pythonClass": ("teal", None, (), None),
    "pythonExceptions": ("teal", None, (), None),
    "cInclude": ("foreground", None, ("bold",), None),
    "cPreCondit": ("foreground", None, ("bold",), None),
    "cPreProc": ("foreground", None, ("bold",), None),
    "cConstant": ("magenta", None, (), None),
}

LINKS = {
    "VertSplit": "WinSeparator", "lCursor": "Cursor", "CursorIM": "Cursor", "WildMenu": "PmenuSel",
    "VisualNOS": "Visual", "StatusLineTerm": "StatusLine",
    "StatusLineTermNC": "StatusLineNC", "pythonBuiltin": "Function", "cDefine": "Macro",
}

# 256-color diffs: the diff backgrounds all land on near-identical grays, so cterm shows the git colors as text.
CTERM_DIFF_FG = {"DiffAdd": "green", "DiffChange": "blue", "DiffDelete": "red", "DiffText": "blue"}

HEADER = """\
" Deepwick for Vim (https://github.com/deepwick/vim).
" Generated by generate.py from the Deepwick palette; edit that, not this file.

set background=dark
hi clear
if exists('syntax_on')
  syntax reset
endif
let g:colors_name = 'deepwick'
"""


def _hi(palette: Palette, group: str, fg, bg, attrs, sp) -> str:
    c = palette.colors

    def cterm(name):
        return "NONE" if name is None else str(nearest_index(c[name]))

    gui = ",".join(attrs) or "NONE"
    ctermfg, ctermbg = cterm(fg), "NONE" if bg == "background" else cterm(bg)
    if group in CTERM_DIFF_FG:
        ctermfg, ctermbg = cterm(CTERM_DIFF_FG[group]), "NONE"
    if sp and fg is None:
        ctermfg = cterm(sp)
    fields = [
        f"guifg={c[fg] if fg else 'NONE'}", f"guibg={c[bg] if bg else 'NONE'}", f"gui={gui}",
        f"ctermfg={ctermfg}", f"ctermbg={ctermbg}", f"cterm={gui.replace('undercurl', 'underline')}",
    ]
    if sp:
        fields.append(f"guisp={c[sp]}")
    return f"hi {group} " + " ".join(fields)


def render_colors(palette: Palette) -> str:
    lines = [HEADER]
    lines += [_hi(palette, group, *spec) for group, spec in GROUPS.items()]
    lines.append("")
    lines += [f"hi! link {group} {target}" for group, target in LINKS.items()]
    lines.append("")
    ansi = ", ".join(f"'{palette.ansi[key]}'" for key in ANSI_KEYS)
    lines.append(f"let g:terminal_ansi_colors = [{ansi}]")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    palette = load_palette()
    COLORS_OUT.parent.mkdir(exist_ok=True)
    COLORS_OUT.write_text(render_colors(palette), encoding="utf-8")
    print(f"wrote {COLORS_OUT.relative_to(Path(__file__).parent)}")
