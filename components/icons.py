"""
icons.py
Helpers that render icons as real graphics (Material Symbols font glyphs,
inline SVGs) instead of raw icon-name text. Use inside unsafe_allow_html markup.
"""


def material_icon(name: str, size: int = 18, filled: bool = False, css_class: str = "") -> str:
    """
    Material Symbols font glyph span. `name` is the icon's codename
    (e.g. "schedule", "autorenew") — rendered as a font glyph, never as text.
    """
    fill = "1" if filled else "0"
    cls = f"material-symbols-outlined {css_class}".strip()
    return (
        f'<span class="{cls}" aria-hidden="true" '
        f'style="font-size:{size}px;vertical-align:middle;'
        f'font-variation-settings:\'FILL\' {fill},\'wght\' 500,\'GRAD\' 0,\'opsz\' 24;">'
        f"{name}</span>"
    )


def trend_arrow(direction: int, size: int = 14) -> str:
    """Inline SVG arrow: up (green), down (red), flat (grey)."""
    if direction > 0:
        stroke, path = "#16a34a", 'M12 19V5M5 12l7-7 7 7'
    elif direction < 0:
        stroke, path = "#dc2626", 'M12 5v14M19 12l-7 7-7-7'
    else:
        stroke, path = "#6b7280", 'M5 12h14'
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="{stroke}" stroke-width="2.5" stroke-linecap="round" '
        f'stroke-linejoin="round" aria-hidden="true" style="vertical-align:middle;">'
        f'<path d="{path}"/></svg>'
    )
