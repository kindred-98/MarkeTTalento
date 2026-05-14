"""Métricas — tarjetas KPI con presentación reforzada (clases dash-kpi)."""
import html
import streamlit as st

from app.views.dashboard.config import COLORS

_KPI_VARIANTS = frozenset({"primary", "success", "danger", "purple", "warning", "neutral"})


def _variant_from_color(color: str | None) -> str:
    if not color:
        return "primary"
    c = color.strip().lower()
    for key in ("primary", "success", "danger", "purple", "warning"):
        if COLORS.get(key, "").strip().lower() == c:
            return key
    return "neutral"


def metric_card(
    col,
    icon,
    label,
    value,
    color=None,
    variant: str | None = None,
    tag: str | None = None,
):
    """Tarjeta KPI. `color` heredado se mapea a variante; `tag` texto corto en la esquina (ej. VENTAS)."""
    v = variant if variant in _KPI_VARIANTS else _variant_from_color(color)
    icon_s = html.escape(str(icon))
    label_s = html.escape(str(label))
    raw_val = str(value)
    value_s = html.escape(raw_val)
    chip_s = html.escape(tag.strip().upper()) if (tag and str(tag).strip()) else "KPI"
    is_currency = raw_val.lstrip().startswith("€")
    value_mod = " dash-kpi__value--currency" if is_currency else ""

    with col:
        st.markdown(
            f"""<article class="dash-kpi dash-kpi--{v}" aria-label="{label_s}">
  <div class="dash-kpi__mesh" aria-hidden="true"></div>
  <div class="dash-kpi__glow" aria-hidden="true"></div>
  <div class="dash-kpi__body">
    <div class="dash-kpi__top">
      <span class="dash-kpi__icon" aria-hidden="true">{icon_s}</span>
      <span class="dash-kpi__chip">{chip_s}</span>
    </div>
    <p class="dash-kpi__label">{label_s}</p>
    <p class="dash-kpi__value{value_mod}">{value_s}</p>
  </div>
  <div class="dash-kpi__bar" aria-hidden="true"></div>
</article>""",
            unsafe_allow_html=True,
        )


def metric_row(metrics):
    cols = st.columns(len(metrics))
    for col, row in zip(cols, metrics):
        if len(row) == 6:
            icon, label, value, color, variant, tag = row
            metric_card(col, icon, label, value, color=color, variant=variant, tag=tag)
        elif len(row) == 5:
            icon, label, value, color, tag = row
            metric_card(col, icon, label, value, color=color, tag=tag)
        else:
            icon, label, value, color = row
            metric_card(col, icon, label, value, color)
