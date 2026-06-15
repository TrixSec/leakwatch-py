import json
import time

def format_bytes(b):
    if b >= 1024 * 1024:
        return f"{b / (1024 * 1024):.1f} MB"
    elif b >= 1024:
        return f"{b / 1024:.1f} KB"
    else:
        return f"{b} B"

def format_runtime(seconds):
    if seconds >= 3600:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        return f"{h}h {m}m"
    elif seconds >= 60:
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m}m {s}s"
    else:
        return f"{seconds:.1f}s"

class ConsoleReporter:
    def __init__(self, data):
        self.data = data

    def report(self, path=None):
        out = []
        
        # 1. Potential Leaks
        leaks = self.data.get('leaks', [])
        if leaks:
            out.append("Potential Leak Detected")
            out.append("")
            for leak in leaks:
                out.append("Object:")
                out.append(f"{leak['type']}")
                out.append("")
                out.append("Instances:")
                out.append(f"{leak['start_count']:,} -> {leak['end_count']:,}")
                out.append("")
                out.append("Growth:")
                out.append(f"{leak['growth_percent']:.0f}%")
                out.append("")
                if leak.get('created_at'):
                    out.append(f"{leak['type']}")
                    out.append("")
                    out.append("Created At:")
                    out.append("")
                    for src in leak['created_at']:
                        out.append(f"{src}")
                    out.append("")
        
        # 2. Top Growing Objects
        out.append("Top Growing Objects")
        out.append("")
        summary = self.data.get('growth_summary', [])
        for idx, item in enumerate(summary[:5], 1):
            out.append(f"{idx}. {item['type']}")
        out.append("")
        
        # 3. Leak Score/Probability
        out.append("Leak Probability")
        out.append("")
        sorted_prob = sorted(summary, key=lambda x: x['leak_score'], reverse=True)
        for item in sorted_prob[:5]:
            out.append(f"{item['type']}")
            out.append(f"{item['leak_score']}%")
            out.append("")
            
        report_str = "\n".join(out)
        if path:
            with open(path, 'w') as f:
                f.write(report_str)
            print(f"Console report written to {path}")
        else:
            print(report_str)

class JSONReporter:
    def __init__(self, data):
        self.data = data

    def report(self, path=None):
        output_path = path or "leakwatch_report.json"
        with open(output_path, 'w') as f:
            json.dump(self.data, f, indent=2)
        print(f"JSON report written to {output_path}")

class MarkdownReporter:
    def __init__(self, data):
        self.data = data

    def report(self, path=None):
        output_path = path or "leakwatch_report.md"
        
        out = []
        out.append("# LeakWatch Memory Growth Report")
        out.append("")
        out.append(f"- **Runtime:** {format_runtime(self.data['runtime_seconds'])}")
        out.append(f"- **Timestamp:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.data['end_time']))}")
        out.append(f"- **Potential Leaks Found:** {len(self.data.get('leaks', []))}")
        out.append("")
        
        leaks = self.data.get('leaks', [])
        if leaks:
            out.append("## Potential Leaks")
            out.append("")
            for leak in leaks:
                out.append(f"### {leak['type']}")
                out.append(f"- **Leak Score:** {leak['leak_score']}%")
                out.append(f"- **Growth:** {leak['start_count']:,} &rarr; {leak['end_count']:,} (+{leak['growth_percent']:.1f}%)")
                if leak.get('created_at'):
                    out.append("- **Suspected Creation Sources:**")
                    for src in leak['created_at']:
                        out.append(f"  - `{src}`")
                out.append("")
                
        out.append("## All Monitored Object Types")
        out.append("")
        out.append("| Object Type | Start Count | End Count | Growth % | Size Growth | Leak Score |")
        out.append("|:---|:---|:---|:---|:---|:---|")
        for item in self.data.get('growth_summary', []):
            out.append(f"| `{item['type']}` | {item['start_count']:,} | {item['end_count']:,} | +{item['growth_percent']:.1f}% | +{format_bytes(item['growth_bytes'])} | {item['leak_score']}% |")
            
        with open(output_path, 'w') as f:
            f.write("\n".join(out))
        print(f"Markdown report written to {output_path}")

class HTMLReporter:
    def __init__(self, data):
        self.data = data

    def report(self, path=None):
        output_path = path or "leakwatch_report.html"
        
        # Build leak cards
        leak_cards_html = ""
        leaks = self.data.get('leaks', [])
        if leaks:
            for leak in leaks:
                sources_html = ""
                if leak.get('created_at'):
                    sources_html = "<h4>Created At:</h4><ul>" + "".join(f"<li><code>{src}</code></li>" for src in leak['created_at']) + "</ul>"
                else:
                    sources_html = "<p class='no-source'>No allocation stack trace found. Ensure tracemalloc is running.</p>"
                
                # Determine health badge color based on score
                score = leak['leak_score']
                score_class = "critical" if score >= 80 else "warning"
                
                leak_cards_html += f"""
                <div class="card leak-card animated">
                    <div class="card-header">
                        <span class="leak-type">{leak['type']}</span>
                        <span class="badge {score_class}">{score}% Leak Score</span>
                    </div>
                    <div class="card-body">
                        <div class="stats-row">
                            <div class="stat-box">
                                <span class="stat-label">Instance Count</span>
                                <span class="stat-value">{leak['start_count']:,} &rarr; {leak['end_count']:,}</span>
                            </div>
                            <div class="stat-box">
                                <span class="stat-label">Instance Growth</span>
                                <span class="stat-value text-red">+{leak['growth_percent']:.1f}%</span>
                            </div>
                        </div>
                        <div class="source-section">
                            {sources_html}
                        </div>
                    </div>
                </div>
                """
        else:
            leak_cards_html = "<div class='no-leaks-msg'>🎉 Excellent! No memory leaks detected (Leak Score &ge; 50%).</div>"

        # Build growth table rows
        table_rows_html = ""
        for item in self.data.get('growth_summary', []):
            score = item['leak_score']
            badge_class = "critical" if score >= 80 else ("warning" if score >= 50 else "info")
            table_rows_html += f"""
            <tr>
                <td><strong>{item['type']}</strong></td>
                <td>{item['start_count']:,}</td>
                <td>{item['end_count']:,}</td>
                <td class="text-red">+{item['growth_percent']:.1f}%</td>
                <td>+{format_bytes(item['growth_bytes'])}</td>
                <td><span class="badge {badge_class}">{score}%</span></td>
            </tr>
            """

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LeakWatch Memory Report</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #0b0f19;
            --card-bg: #111827;
            --border-color: rgba(255, 255, 255, 0.06);
            --text-primary: #f3f4f6;
            --text-secondary: #9ca3af;
            --primary-accent: #6366f1;
            --accent-red: #ef4444;
            --accent-orange: #f97316;
            --accent-green: #10b981;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: 'Plus Jakarta Sans', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            line-height: 1.5;
            padding: 2rem 1rem;
        }}

        .container {{
            max-width: 1100px;
            margin: 0 auto;
        }}

        header {{
            margin-bottom: 2.5rem;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            flex-wrap: wrap;
            gap: 1rem;
        }}

        h1 {{
            font-size: 2.25rem;
            font-weight: 700;
            background: linear-gradient(135deg, #a78bfa 0%, #6366f1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }}

        .meta-info {{
            display: flex;
            gap: 1.5rem;
            color: var(--text-secondary);
            font-size: 0.95rem;
        }}

        .meta-item strong {{
            color: var(--text-primary);
        }}

        .section-title {{
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1.25rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .grid {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 2rem;
            margin-bottom: 3rem;
        }}

        @media (min-width: 768px) {{
            .grid {{
                grid-template-columns: 1fr 1fr;
            }}
        }}

        .card {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 24px rgba(99, 102, 241, 0.1);
        }}

        .leak-card {{
            border-left: 4px solid var(--accent-red);
        }}

        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }}

        .leak-type {{
            font-size: 1.25rem;
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
            word-break: break-all;
        }}

        .badge {{
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.8rem;
            font-weight: 600;
        }}

        .badge.critical {{
            background-color: rgba(239, 68, 68, 0.15);
            color: #f87171;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }}

        .badge.warning {{
            background-color: rgba(249, 115, 22, 0.15);
            color: #fb923c;
            border: 1px solid rgba(249, 115, 22, 0.3);
        }}

        .badge.info {{
            background-color: rgba(99, 102, 241, 0.15);
            color: #818cf8;
            border: 1px solid rgba(99, 102, 241, 0.3);
        }}

        .stats-row {{
            display: flex;
            gap: 1.5rem;
            margin-bottom: 1.25rem;
            background: rgba(255, 255, 255, 0.02);
            padding: 0.75rem;
            border-radius: 8px;
        }}

        .stat-box {{
            flex: 1;
        }}

        .stat-label {{
            font-size: 0.8rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .stat-value {{
            display: block;
            font-size: 1.1rem;
            font-weight: 600;
        }}

        .text-red {{
            color: var(--accent-red);
        }}

        .source-section h4 {{
            font-size: 0.9rem;
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
            font-weight: 500;
        }}

        .source-section ul {{
            list-style: none;
        }}

        .source-section li {{
            background: rgba(0, 0, 0, 0.2);
            padding: 0.4rem 0.6rem;
            border-radius: 6px;
            margin-bottom: 0.35rem;
            font-size: 0.85rem;
            font-family: 'JetBrains Mono', monospace;
            border: 1px solid rgba(255, 255, 255, 0.03);
            word-break: break-all;
        }}

        .no-source {{
            color: var(--text-secondary);
            font-size: 0.85rem;
            font-style: italic;
        }}

        .no-leaks-msg {{
            background-color: rgba(16, 185, 129, 0.1);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.2);
            border-radius: 12px;
            padding: 2rem;
            text-align: center;
            font-size: 1.1rem;
            grid-column: 1 / -1;
        }}

        /* Table Styling */
        .table-container {{
            width: 100%;
            overflow-x: auto;
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }}

        th, td {{
            padding: 1rem 1.5rem;
            border-bottom: 1px solid var(--border-color);
        }}

        th {{
            background-color: rgba(255, 255, 255, 0.02);
            color: var(--text-secondary);
            font-weight: 600;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        tr:last-child td {{
            border-bottom: none;
        }}

        tr:hover td {{
            background-color: rgba(255, 255, 255, 0.01);
        }}

        td strong {{
            font-family: 'JetBrains Mono', monospace;
        }}

        /* Animations */
        .animated {{
            animation: fadeInUp 0.5s ease-out both;
        }}

        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(10px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>LeakWatch</h1>
                <p style="color: var(--text-secondary);">Memory Allocation & Leak Analysis Report</p>
            </div>
            <div class="meta-info">
                <div class="meta-item">
                    <span>Runtime:</span>
                    <strong>{format_runtime(self.data['runtime_seconds'])}</strong>
                </div>
                <div class="meta-item">
                    <span>Generated At:</span>
                    <strong>{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.data['end_time']))}</strong>
                </div>
            </div>
        </header>

        <section style="margin-bottom: 3rem;">
            <h2 class="section-title">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: var(--accent-orange)"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
                Potential Leaks
            </h2>
            <div class="grid">
                {leak_cards_html}
            </div>
        </section>

        <section>
            <h2 class="section-title">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: var(--primary-accent)"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="9" y1="3" x2="9" y2="21"></line><line x1="15" y1="3" x2="15" y2="21"></line><line x1="3" y1="9" x2="21" y2="9"></line><line x1="3" y1="15" x2="21" y2="15"></line></svg>
                All Monitored Object Types
            </h2>
            <div class="table-container animated">
                <table>
                    <thead>
                        <tr>
                            <th>Object Type</th>
                            <th>Start Count</th>
                            <th>End Count</th>
                            <th>Growth %</th>
                            <th>Size Growth</th>
                            <th>Leak Score</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows_html}
                    </tbody>
                </table>
            </div>
        </section>
    </div>
</body>
</html>
"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"HTML report written to {output_path}")
