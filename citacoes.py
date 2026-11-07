#!/usr/bin/env python3
"""Atualiza o gráfico e as métricas do Google Scholar em publications.html.

Uso no diretório raiz do site:
    python citacoes.py                # consulta SerpApi (requer SERPAPI_API_KEY)
    python citacoes.py --preview      # recria só o gráfico com os dados do script antigo
    python citacoes.py --input x.json # usa JSON previamente baixado da SerpApi

O script NÃO altera a lista de artigos, nem os totais manuais de artigos.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
import tempfile
from zoneinfo import ZoneInfo

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import requests

SCHOLAR_ID = "ZF1mcjoAAAAJ"
ROOT = Path(__file__).resolve().parent

# Valores informados no citacoes.py original; NÃO são uma consulta atualizada.
PREVIEW_YEARS = list(range(2019, 2027))
PREVIEW_CITATIONS = [2, 4, 5, 19, 34, 51, 100, 48]

NAVY = "#08243d"
BLUE = "#376c88"
GOLD = "#ba8751"
MUTED = "#71818e"
GRID = "#e6ebec"


def fetch_serpapi(api_key: str) -> dict:
    """Busca o perfil do Google Scholar via SerpApi, não via scraping direto."""
    try:
        response = requests.get(
            "https://serpapi.com/search.json",
            params={
                "engine": "google_scholar_author",
                "author_id": SCHOLAR_ID,
                "hl": "en",
                "api_key": api_key,
            },
            timeout=40,
        )
    except requests.RequestException as exc:
        raise RuntimeError("Falha de conexão com a SerpApi") from exc
    # Não imprima a URL da requisição: contém a chave privada.
    if not response.ok:
        raise RuntimeError(f"SerpApi retornou HTTP {response.status_code}")
    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError("SerpApi retornou um conteúdo que não é JSON") from exc
    if payload.get("error"):
        raise RuntimeError(f"SerpApi: {payload['error']}")
    return payload


def parse_metrics(payload: dict) -> tuple[int, int, list[int], list[int]]:
    """Valida as métricas; não publica dados incompletos."""
    params = payload.get("search_parameters", {})
    profile_id = params.get("author_id")
    if profile_id and profile_id != SCHOLAR_ID:
        raise ValueError("O JSON pertence a outro perfil do Google Scholar")

    cited = payload.get("cited_by", {})
    table = cited.get("table", [])
    graph = cited.get("graph", [])

    def all_time(metric: str) -> int:
        for row in table:
            value = row.get(metric, {}).get("all")
            if value is not None:
                result = int(value)
                if result < 0:
                    raise ValueError(f"Métrica negativa: {metric}")
                return result
        raise ValueError(f"Não foi possível encontrar '{metric}.all' na resposta")

    total = all_time("citations")
    h_index = all_time("h_index")
    if not isinstance(graph, list) or not graph:
        raise ValueError("A SerpApi não retornou o histórico de citações por ano")

    items = {}
    for row in graph:
        year = int(row["year"])
        count = int(row["citations"])
        if not (1980 <= year <= datetime.now().year + 1) or count < 0:
            raise ValueError("O histórico possui um ano ou total inválido")
        items[year] = count
    years = list(range(min(items), max(items) + 1))
    counts = [items.get(y, 0) for y in years]
    if not total or not any(counts):
        raise ValueError("A API retornou métricas vazias ou zeradas")
    return total, h_index, years, counts


def draw_chart(years: list[int], citations: list[int], total: int, output: Path, preview: bool = False) -> None:
    """Gráfico adequado ao cartão claro/azul-marinho do site."""
    fig, ax = plt.subplots(figsize=(9.6, 4.35), dpi=210)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    fig.subplots_adjust(left=.075, right=.975, top=.72, bottom=.20)

    current_year = datetime.now(ZoneInfo("America/Sao_Paulo")).year
    colors = [GOLD if year == current_year else BLUE for year in years]
    bars = ax.bar(range(len(years)), citations, width=.59, color=colors, zorder=3)

    max_val = max(citations) if citations else 1
    ymax = max(5, max_val * 1.23)
    ax.set_ylim(0, ymax)
    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins=4, integer=True))
    ax.yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))
    ax.grid(axis="y", color=GRID, linewidth=.9, zorder=0)
    ax.set_axisbelow(True)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(axis="y", length=0, labelsize=11, colors=MUTED, pad=10)
    ax.tick_params(axis="x", length=0, labelsize=11, colors=NAVY, pad=11)
    ax.set_xticks(range(len(years)))
    ax.set_xticklabels([str(y) for y in years])

    for bar, count in zip(bars, citations):
        if count > 0:
            ax.annotate(
                str(count),
                (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                xytext=(0, 6), textcoords="offset points", ha="center", va="bottom",
                fontsize=10, fontweight="semibold", color=NAVY,
            )

    fig.text(.075, .91, "CITATIONS BY YEAR", color=NAVY,
             fontfamily="DejaVu Sans", fontsize=12, weight="bold")
    fig.text(.975, .91, f"{total:,} citations", ha="right",
             color=NAVY, fontsize=20, weight="semibold")
    fig.text(.075, .82, "Historical values from citacoes.py" if preview else "Source: Google Scholar",
             color=MUTED, fontsize=10)
    output.parent.mkdir(parents=True, exist_ok=True)
    # Formato determinado explicitamente para funcionar também com arquivo temporário.
    fig.savefig(output, format="png", dpi=210, facecolor="white", metadata={"Software": "matplotlib"})
    plt.close(fig)


def change_one(src: str, pattern: str, replacement: str, name: str) -> str:
    edited, count = re.subn(pattern, lambda _: replacement, src, count=1, flags=re.DOTALL)
    if count != 1:
        raise ValueError(f"Não encontrei o elemento '{name}' no publications.html")
    return edited


def update_html(html: str, total: int, h_index: int, date: datetime) -> str:
    """Modifica APENAS os elementos identificados da área de bibliometria.

    O restante do HTML, inclusive a lista de publicações, permanece idêntico.
    """
    opening = '<div class="publication-summary">'
    closing = '<div class="publications-list">'
    if html.count(opening) != 1 or html.count(closing) != 1:
        raise ValueError("Não encontrei a seção bibliométrica única no HTML")
    beginning, rest = html.split(opening, 1)
    section, ending = rest.split(closing, 1)

    # Este arquivo possui marcadores exclusivos para alterações futuras.
    date_en = date.strftime("%-d %B %Y")
    date_short = date.strftime("%b %Y").upper()
    tag = date.strftime("%Y%m%d")
    updates = [
        (r'<div class="eyebrow dark-eyebrow" data-scholar-date>.*?</div>',
         f'<div class="eyebrow dark-eyebrow" data-scholar-date>BIBLIOMETRICS / {date_short}</div>', "data"),
        (r'<p data-scholar-source>.*?</p>',
         f'<p data-scholar-source>Google Scholar: {total:,} citations as of {date_en}. Publication counts are maintained manually.</p>', "fonte"),
        (r'<b data-scholar-hindex>.*?</b>',
         f'<b data-scholar-hindex>{h_index}</b>', "h-index"),
        (r'<img data-scholar-chart [^>]*?/>',
         f'<img data-scholar-chart alt="Annual Google Scholar citations, updated {date_en}" loading="lazy" src="research/output.png?v={tag}"/>', "imagem"),
        (r'<small data-scholar-caption>.*?</small>',
         f'<small data-scholar-caption>Google Scholar · {total:,} citations · {date_en}</small>', "legenda"),
    ]
    for pattern, replacement, name in updates:
        section = change_one(section, pattern, replacement, name)
    return beginning + opening + section + closing + ending


def atomic_text_write(file: Path, text: str) -> None:
    file.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=file.parent, suffix=".html", prefix=".scholar-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(text)
        os.replace(tmp, file)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", action="store_true",
                        help="Gera apenas o gráfico de exemplo, sem consultar API nem alterar HTML")
    parser.add_argument("--input", type=Path, metavar="JSON",
                        help="Utiliza resposta salva da SerpApi, em vez de chamar a API")
    parser.add_argument("--site-root", type=Path, default=ROOT,
                        help="Diretório onde estão publications.html e research/")
    args = parser.parse_args()
    if args.preview and args.input:
        parser.error("Use apenas --preview OU --input")

    root = args.site_root.expanduser().resolve()
    graph_file = root / "research" / "output.png"
    if args.preview:
        draw_chart(PREVIEW_YEARS, PREVIEW_CITATIONS,
                   sum(PREVIEW_CITATIONS), graph_file, preview=True)
        print(f"Prévia criada: {graph_file} (dados históricos; HTML inalterado)")
        return

    if args.input:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
    else:
        api_key = os.environ.get("SERPAPI_API_KEY", "").strip()
        if not api_key:
            parser.error("Defina SERPAPI_API_KEY para obter dados atuais. Use --preview para testar o gráfico.")
        payload = fetch_serpapi(api_key)

    total, h_index, years, counts = parse_metrics(payload)
    page = root / "publications.html"
    before = page.read_text(encoding="utf-8")
    date = datetime.now(ZoneInfo("America/Sao_Paulo"))
    after = update_html(before, total, h_index, date)

    graph_file.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(dir=graph_file.parent, suffix=".png", prefix=".scholar-")
    os.close(fd)
    try:
        draw_chart(years, counts, total, Path(temp_path))
        os.replace(temp_path, graph_file)
        atomic_text_write(page, after)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    print(f"Atualizado: {total} citações, h-index {h_index}, {date:%d/%m/%Y}")
    print(f"Arquivos: {page} e {graph_file}")


if __name__ == "__main__":
    main()
