"""
PDF Export Service.

Uses Playwright to convert HTML reports to PDF.
Provides high-fidelity rendering with modern CSS support.
"""

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader


class PDFExportService:
    """
    Service for exporting reports to PDF using Playwright.

    Features:
    - HTML template rendering with Jinja2
    - High-fidelity PDF generation via Chromium
    - Custom styling, fonts, and logos
    - Watermarks and headers/footers
    """

    def __init__(self) -> None:
        self._browser = None
        self._template_dir = Path(__file__).parent.parent / "templates" / "pdf"
        self._jinja_env: Environment | None = None

    def _get_jinja_env(self) -> Environment:
        """Get or create Jinja2 environment."""
        if self._jinja_env is None:
            self._template_dir.mkdir(parents=True, exist_ok=True)
            self._jinja_env = Environment(
                loader=FileSystemLoader(str(self._template_dir)),
                autoescape=True,
            )
        return self._jinja_env

    async def _get_browser(self):
        """Get or create browser instance."""
        if self._browser is None:
            from playwright.async_api import async_playwright

            playwright = await async_playwright().start()
            self._browser = await playwright.chromium.launch(headless=True)
        return self._browser

    async def render_html(
        self,
        report_data: dict[str, Any],
        visual_config: dict[str, Any] | None = None,
        language_config: dict[str, Any] | None = None,
    ) -> str:
        """
        Render report data to HTML using template.

        Args:
            report_data: Report content (title, sections, metrics, etc.)
            visual_config: Visual styling configuration
            language_config: Language settings

        Returns:
            Rendered HTML string
        """
        # Default configs
        visual = visual_config or {
            "primary_color": "#3B82F6",
            "secondary_color": "#1E40AF",
            "font_family": "Inter",
            "show_charts": True,
            "watermark": None,
            "header_style": "full",
        }

        language = language_config or {
            "language": "pt-BR",
        }

        # Build context
        context = {
            "report": report_data,
            "visual": visual,
            "language": language,
            "generated_at": report_data.get("generated_at", ""),
        }

        # Try to load custom template, fallback to inline
        try:
            env = self._get_jinja_env()
            template = env.get_template("report.html")
            return template.render(**context)
        except Exception:
            # Fallback to inline template
            return self._render_inline_template(context)

    def _render_inline_template(self, context: dict[str, Any]) -> str:
        """Render using inline template as fallback."""
        report = context["report"]
        visual = context["visual"]

        sections_html = ""
        for section in report.get("sections", []):
            sections_html += f"""
            <section class="report-section">
                <h2>{section.get("title", "")}</h2>
                <div class="section-content">{section.get("content", "").replace(chr(10), "<br>")}</div>
            </section>
            """

        metrics_html = ""
        if report.get("summary_metrics"):
            metrics_html = '<div class="metrics-grid">'
            for m in report["summary_metrics"]:
                trend_class = f"trend-{m.get('trend', 'stable')}"
                metrics_html += f"""
                <div class="metric-card">
                    <div class="metric-value">{m.get("value", "")}</div>
                    <div class="metric-name">{m.get("name", "")}</div>
                    {f'<div class="metric-change {trend_class}">{m.get("change", "")}</div>' if m.get("change") else ""}
                </div>
                """
            metrics_html += "</div>"

        watermark_html = ""
        if visual.get("watermark"):
            watermark_html = f'<div class="watermark">{visual["watermark"]}</div>'

        return f"""
<!DOCTYPE html>
<html lang="{context["language"].get("language", "pt-BR")}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report.get("title", "Relatório")}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: {visual.get("primary_color", "#3B82F6")};
            --secondary: {visual.get("secondary_color", "#1E40AF")};
            --font: '{visual.get("font_family", "Inter")}', system-ui, sans-serif;
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: var(--font);
            font-size: 11pt;
            line-height: 1.6;
            color: #1f2937;
            background: #fff;
            padding: 20mm;
        }}

        .header {{
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 3px solid var(--primary);
        }}

        .header h1 {{
            font-size: 24pt;
            color: var(--secondary);
            margin-bottom: 4px;
        }}

        .header .subtitle {{
            color: #6b7280;
            font-size: 11pt;
        }}

        .header .meta {{
            margin-top: 8px;
            font-size: 9pt;
            color: #9ca3af;
        }}

        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            margin: 20px 0;
        }}

        .metric-card {{
            background: linear-gradient(135deg, #f8fafc, #f1f5f9);
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 12px;
            text-align: center;
        }}

        .metric-value {{
            font-size: 20pt;
            font-weight: 700;
            color: var(--primary);
        }}

        .metric-name {{
            font-size: 9pt;
            color: #6b7280;
            margin-top: 2px;
        }}

        .metric-change {{
            font-size: 9pt;
            margin-top: 4px;
        }}

        .trend-up {{ color: #059669; }}
        .trend-down {{ color: #dc2626; }}
        .trend-stable {{ color: #6b7280; }}

        .report-section {{
            margin: 24px 0;
            page-break-inside: avoid;
        }}

        .report-section h2 {{
            font-size: 14pt;
            color: var(--secondary);
            margin-bottom: 8px;
            padding-bottom: 4px;
            border-bottom: 1px solid #e5e7eb;
        }}

        .section-content {{
            white-space: pre-wrap;
        }}

        .footer {{
            margin-top: 32px;
            padding-top: 12px;
            border-top: 1px solid #e5e7eb;
            font-size: 8pt;
            color: #9ca3af;
            text-align: center;
        }}

        .watermark {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) rotate(-45deg);
            font-size: 72pt;
            font-weight: 700;
            color: rgba(0, 0, 0, 0.03);
            pointer-events: none;
            z-index: 1000;
        }}

        @media print {{
            body {{ padding: 0; }}
            .report-section {{ page-break-inside: avoid; }}
        }}
    </style>
</head>
<body>
    {watermark_html}

    <header class="header">
        <h1>{report.get("title", "Relatório")}</h1>
        <p class="subtitle">{report.get("subtitle", "")}</p>
        <p class="meta">
            Período: {report.get("period_description", "")} |
            Gerado em: {context.get("generated_at", "")} |
            Fontes: {report.get("sources_count", 0)} atividades
        </p>
    </header>

    {metrics_html}

    <main>
        {sections_html}
    </main>

    <footer class="footer">
        <p>Relatório gerado automaticamente pelo DevBridge</p>
        <p>Confiança: {int(report.get("confidence_score", 0) * 100)}%</p>
    </footer>
</body>
</html>
        """

    async def export_to_pdf(
        self,
        report_data: dict[str, Any],
        visual_config: dict[str, Any] | None = None,
        language_config: dict[str, Any] | None = None,
    ) -> bytes:
        """
        Export report to PDF.

        Args:
            report_data: Report content
            visual_config: Visual styling
            language_config: Language settings

        Returns:
            PDF file bytes
        """
        # Render HTML
        html_content = await self.render_html(report_data, visual_config, language_config)

        # Generate PDF with Playwright
        browser = await self._get_browser()
        page = await browser.new_page()

        try:
            await page.set_content(html_content, wait_until="networkidle")

            pdf_bytes = await page.pdf(
                format="A4",
                margin={
                    "top": "15mm",
                    "bottom": "15mm",
                    "left": "15mm",
                    "right": "15mm",
                },
                print_background=True,
            )

            return pdf_bytes
        finally:
            await page.close()

    async def close(self) -> None:
        """Close browser instance."""
        if self._browser:
            await self._browser.close()
            self._browser = None


# Singleton instance
pdf_export_service = PDFExportService()
