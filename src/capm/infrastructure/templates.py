from datetime import datetime, timedelta
from src.capm.domain.repositories import DatabaseManager
from src.capm.config import settings


def _relative_time(dt: datetime) -> str:
    now = datetime.utcnow()
    diff = now - dt

    if diff < timedelta(minutes=1):
        return "just now"
    elif diff < timedelta(hours=1):
        mins = int(diff.total_seconds() / 60)
        return f"{mins} minute{'s' if mins != 1 else ''} ago"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        days = diff.days
        return f"{days} day{'s' if days != 1 else ''} ago"


def generate_dashboard(db: DatabaseManager) -> str:
    from src.capm.config import settings

    metrics = db.get_all_metrics()
    latest = db.get_latest_calculation()

    beta_buy = settings.beta_buy_threshold
    beta_sell = settings.beta_sell_threshold
    alpha_thresh = settings.alpha_buy_threshold
    sharpe_thresh = settings.sharpe_buy_threshold
    period = settings.data_period

    def highlight_class(value: float, metric: str) -> str:
        if metric == "beta":
            if value < beta_buy:
                return "signal-buy"
            elif value > beta_sell:
                return "signal-sell"
        elif metric == "alpha":
            if value > alpha_thresh:
                return "signal-buy"
            elif value < alpha_thresh:
                return "signal-sell"
        elif metric == "sharpe":
            if value > sharpe_thresh:
                return "signal-buy"
            elif value < 0:
                return "signal-sell"
        return ""

    rows = ""

    for m in metrics:
        beta_class = highlight_class(m.beta, "beta")
        alpha_class = highlight_class(m.alpha, "alpha")
        sharpe_class = highlight_class(m.sharpe, "sharpe")

        volume_str = f"{m.volume:,}" if m.volume else "N/A"
        price_str = f"${m.current_price:.2f}" if m.current_price else "N/A"

        rows += f"""
        <tr>
            <td data-value="{m.ticker}">{m.ticker}</td>
            <td data-value="{m.current_price if m.current_price else ""}">{price_str}</td>
            <td data-value="{m.volume if m.volume else ""}">{volume_str}</td>
            <td data-value="{m.beta}" class="{beta_class}">{m.beta:.3f}</td>
            <td data-value="{m.alpha}" class="{alpha_class}">{m.alpha:.4f}</td>
            <td data-value="{m.sharpe}" class="{sharpe_class}">{m.sharpe:.3f}</td>
            <td data-value="{m.capm}">{m.capm:.4f}</td>
            <td data-value="{m.r_squared}">{m.r_squared:.3f}</td>
        </tr>"""

    status = "READY" if latest else "NO DATA"
    relative_time = _relative_time(latest.calculated_at) if latest else "N/A"

    market_return_pct = f"{(latest.market_return * 100):.2f}%" if latest else "N/A"
    risk_free_pct = f"{(latest.risk_free_rate * 100):.2f}%" if latest else "N/A"
    rf_source = (
        latest.risk_free_source if latest and latest.risk_free_source else "^TNX"
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CAPM Terminal</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ background-color: #0a0a0a; color: #00ff41; font-family: 'Courier New', monospace; min-height: 100vh; padding: 2rem; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        h1 {{ font-size: 1.5rem; border-bottom: 1px solid #008f11; padding-bottom: 0.5rem; margin-bottom: 1.5rem; text-transform: uppercase; letter-spacing: 2px; }}
        .market-bar {{ display: flex; gap: 2rem; margin-bottom: 1.5rem; padding: 1rem; background: #111; border: 1px solid #1a1a1a; font-size: 0.85rem; flex-wrap: wrap; }}
        .market-bar .label {{ color: #666; }}
        .market-bar .value {{ color: #00ff41; }}
        .status {{ color: #888; font-size: 0.85rem; margin-bottom: 2rem; display: flex; align-items: center; gap: 1rem; }}
        .status span {{ color: #00ff41; }}
        .table-wrapper {{ overflow-x: auto; max-height: 70vh; overflow-y: auto; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
        thead {{ position: sticky; top: 0; background-color: #0a0a0a; z-index: 10; }}
        th {{ text-align: left; padding: 0.75rem 1rem; border-bottom: 2px solid #008f11; color: #008f11; text-transform: uppercase; font-size: 0.7rem; letter-spacing: 1px; cursor: pointer; user-select: none; white-space: nowrap; }}
        th:hover {{ color: #00ff41; }}
        th.sorted-asc::after {{ content: ' ▲'; font-size: 0.6em; }}
        th.sorted-desc::after {{ content: ' ▼'; font-size: 0.6em; }}
        td {{ padding: 0.75rem 1rem; border-bottom: 1px solid #1a1a1a; white-space: nowrap; }}
        tr:hover {{ background-color: #111; }}
        .signal-buy {{ color: #00ff41; font-weight: bold; }}
        .signal-sell {{ color: #ff4444; font-weight: bold; }}
        .footer {{ margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #1a1a1a; color: #888; font-size: 0.75rem; display: flex; justify-content: space-between; }}
        .empty {{ text-align: center; padding: 3rem; color: #888; }}
        .legend {{ margin-bottom: 1rem; font-size: 0.75rem; color: #666; }}
        .legend span {{ margin-right: 1.5rem; }}
        .legend .buy {{ color: #00ff41; }}
        .legend .sell {{ color: #ff4444; }}
        .refresh-btn {{ background: #111; border: 1px solid #008f11; color: #00ff41; padding: 0.5rem 1rem; font-family: inherit; font-size: 0.75rem; cursor: pointer; text-transform: uppercase; letter-spacing: 1px; }}
        .refresh-btn:hover {{ background: #1a1a1a; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Financial Metrics Terminal // CAPM</h1>
        <div class="market-bar">
            <div><span class="label">MARKET:</span> <span class="value">{latest.market_ticker if latest else "N/A"}</span></div>
            <div><span class="label">RISK-FREE:</span> <span class="value">{risk_free_pct} ({rf_source})</span></div>
            <div><span class="label">DATA PERIOD:</span> <span class="value">{period}</span></div>
            <div><span class="label">MARKET RETURN:</span> <span class="value">{market_return_pct}</span></div>
            <div><span class="label">LAST UPDATE:</span> <span class="value">{relative_time}</span></div>
        </div>
        <div class="status">
            STATUS: <span>{status}</span>
            <button class="refresh-btn" onclick="window.location.reload()">Refresh</button>
        </div>
        <div class="legend">
            <span class="buy">● GREEN</span>
            <span class="sell">● RED</span>
            <span>(Beta &lt; {beta_buy} | Alpha &gt; {alpha_thresh} | Sharpe &gt; {sharpe_thresh})</span>
        </div>
        <div class="table-wrapper">
            <table id="metrics-table">
                <thead>
                    <tr>
                        <th data-sort="ticker">Ticker</th>
                        <th data-sort="current_price">Price</th>
                        <th data-sort="volume">Volume</th>
                        <th data-sort="beta">Beta</th>
                        <th data-sort="alpha">Alpha</th>
                        <th data-sort="sharpe">Sharpe</th>
                        <th data-sort="capm">CAPM</th>
                        <th data-sort="r_squared">R²</th>
                    </tr>
                </thead>
                <tbody>
                    {rows if rows else '<tr><td colspan="8" class="empty">No metrics calculated. Run POST /sync to calculate.</td></tr>'}
                </tbody>
            </table>
        </div>
        <div class="footer">
            <span>engine v1.0.0</span>
            <span>sqlite backend</span>
            <span>built by matb</span>
        </div>
    </div>
    <script>
        const table = document.getElementById('metrics-table');
        const headers = table.querySelectorAll('th');
        let currentSort = {{ column: null, direction: 'asc' }};
        headers.forEach(header => {{
            header.addEventListener('click', () => {{
                const column = header.dataset.sort;
                const direction = currentSort.column === column && currentSort.direction === 'asc' ? 'desc' : 'asc';
                headers.forEach(h => h.classList.remove('sorted-asc', 'sorted-desc'));
                header.classList.add(direction === 'asc' ? 'sorted-asc' : 'sorted-desc');
                sortTable(column, direction);
                currentSort = {{ column, direction }};
            }});
        }});
        function sortTable(column, direction) {{
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const colIndex = getColumnIndex(column);
            rows.sort((a, b) => {{
                const aCell = a.children[colIndex];
                const bCell = b.children[colIndex];
                const aVal = aCell ? aCell.dataset.value : aCell.textContent;
                const bVal = bCell ? bCell.dataset.value : bCell.textContent;
                const aNum = parseFloat(aVal);
                const bNum = parseFloat(bVal);
                if (!isNaN(aNum) && !isNaN(bNum)) {{
                    return direction === 'asc' ? aNum - bNum : bNum - aNum;
                }}
                return direction === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
            }});
            rows.forEach(row => tbody.appendChild(row));
        }}
        function getColumnIndex(column) {{
            const map = {{ ticker: 0, current_price: 1, volume: 2, beta: 3, alpha: 4, sharpe: 5, capm: 6, r_squared: 7 }};
            return map[column];
        }}
    </script>
</body>
</html>"""
