"""Génération du rapport PDF remis au client.

Chaîne complète : collecte (report_data) -> analyse (report_analysis) -> mise en page.
"""

from datetime import datetime
from xml.sax.saxutils import escape

from src.diagnostics import report_analysis as ra
from src.diagnostics.report_data import collect_all
from src.utils.company import load_company, logo_path

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        HRFlowable, Image, KeepTogether, Paragraph, SimpleDocTemplate,
        Spacer, Table, TableStyle,
    )
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

ACCENT = "#00A7A7"
DARK = "#1E3A5F"
GREY = "#666666"
LIGHT = "#F4F6F8"
BORDER = "#D5DAE0"

STATUS_COLORS = {
    ra.OK: "#2E7D32",
    ra.WARNING: "#F57C00",
    ra.DANGER: "#D32F2F",
    ra.UNKNOWN: "#757575",
}

PAGE_W = A4[0] if HAS_REPORTLAB else 595
MARGIN = 40
CONTENT_W = PAGE_W - 2 * MARGIN


def _e(value) -> str:
    """Échappe un texte dynamique pour reportlab (&, <, >)."""
    return escape(str(value if value is not None else ""))


def default_filename(client_name: str = "", hostname: str = "") -> str:
    """Nom de fichier horodaté, ex. Rapport_PCDUPONT_20261002_1430.pdf."""
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    base = (hostname or client_name or "PC").strip()
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in base)
    return f"Rapport_{safe}_{stamp}.pdf"


class ReportInfo:
    """Assemble et génère le rapport PDF d'intervention."""

    @staticmethod
    def generate_pdf(filepath: str, options: dict) -> tuple[bool, str]:
        """
        options = {
            'client_name', 'client_phone', 'client_email', 'tech_name',
            'include_system', 'include_disks', 'include_network',
            'include_security', 'include_printers'
        }
        """
        if not HAS_REPORTLAB:
            return False, "La bibliothèque 'reportlab' n'est pas installée (pip install reportlab)."

        try:
            data = collect_all(options)
            analysis = ra.analyze(data, options)
            company = load_company()
            ReportInfo.build_pdf(filepath, data, analysis, options, company)
            return True, f"Rapport PDF généré avec succès :\n{filepath}"
        except PermissionError:
            return False, ("Impossible d'écrire le fichier. Le PDF est peut-être déjà ouvert, "
                           "ou le dossier est protégé : choisissez un autre emplacement.")
        except Exception as exc:
            return False, f"Erreur lors de la création du PDF : {exc}"

    # ------------------------------------------------------------------
    # Mise en page
    # ------------------------------------------------------------------
    @staticmethod
    def build_pdf(filepath, data, analysis, options, company):
        styles = getSampleStyleSheet()
        body = ParagraphStyle("Body", parent=styles["Normal"], fontSize=9.5,
                              leading=13, textColor=colors.HexColor("#333333"))
        small = ParagraphStyle("Small", parent=body, fontSize=8.5, leading=11,
                               textColor=colors.HexColor(GREY))
        h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13,
                            textColor=colors.HexColor(DARK), spaceBefore=14, spaceAfter=6)
        title = ParagraphStyle("Title", parent=styles["Heading1"], fontSize=20,
                               textColor=colors.HexColor(DARK), spaceAfter=2)
        right = ParagraphStyle("Right", parent=body, alignment=2)  # 2 = droite

        def P(text, style=body):
            return Paragraph(text, style)

        def status_cell(status):
            style = ParagraphStyle(
                "St", parent=body, fontSize=8.5, alignment=1,
                textColor=colors.white, fontName="Helvetica-Bold")
            return P(_e(ra.STATUS_LABELS[status]), style)

        def table_style(extra=None):
            base = [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor(BORDER)),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
            return TableStyle(base + (extra or []))

        def header_row(cells):
            st = ParagraphStyle("Th", parent=body, fontName="Helvetica-Bold",
                                textColor=colors.white, fontSize=9)
            return [P(_e(c), st) for c in cells]

        generated = data["generated_at"]
        system = data["system"] or {}
        story = []

        # ---------- En-tête : logo + coordonnées entreprise ----------
        logo_cell = ""
        try:
            lp = logo_path(company)
            from PIL import Image as PILImage  # dimension réelle du logo
            with PILImage.open(lp) as im:
                w, h = im.size
            logo_w = 4.2 * cm
            logo_cell = Image(str(lp), width=logo_w, height=logo_w * h / w)
        except Exception:
            logo_cell = P(f"<b>{_e(company['name'])}</b>")

        contact_lines = [f"<b>{_e(company['name'])}</b>"]
        for key in ("address", "phone", "email", "website"):
            if company.get(key):
                contact_lines.append(_e(company[key]))

        header = Table([[logo_cell, P("<br/>".join(contact_lines), right)]],
                       colWidths=[CONTENT_W * 0.45, CONTENT_W * 0.55])
        header.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                    ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
        story += [header, Spacer(1, 6),
                  HRFlowable(width="100%", thickness=1.5, color=colors.HexColor(ACCENT),
                             spaceAfter=10)]

        # ---------- Titre + fiche d'intervention ----------
        story.append(P(_e(company.get("tagline") or "Rapport de diagnostic"), title))
        story.append(P(f"Établi le {generated.strftime('%d/%m/%Y à %H:%M')}", small))
        story.append(Spacer(1, 8))

        model = " ".join(x for x in (system.get("manufacturer"), system.get("model")) if x)
        info_rows = [("Client", options.get("client_name") or "Client")]
        if options.get("client_phone"):
            info_rows.append(("Téléphone", options["client_phone"]))
        if options.get("client_email"):
            info_rows.append(("E-mail", options["client_email"]))
        info_rows += [
            ("Technicien", options.get("tech_name") or "Technicien"),
            ("Nom du poste", system.get("hostname", "Inconnu")),
        ]
        if model:
            info_rows.append(("Modèle", model))
        if system.get("serial"):
            info_rows.append(("N° de série", system["serial"]))

        info = Table([[P(f"<b>{_e(k)}</b>"), P(_e(v))] for k, v in info_rows],
                     colWidths=[110, CONTENT_W - 110])
        info.setStyle(table_style([("BACKGROUND", (0, 0), (0, -1), colors.HexColor(LIGHT))]))
        story += [info, Spacer(1, 12)]

        # ---------- Bandeau de verdict ----------
        overall = analysis["overall"]
        banner_style = ParagraphStyle("Banner", parent=body, fontSize=12,
                                      textColor=colors.white, fontName="Helvetica-Bold")
        banner = Table(
            [[P(f"{_e(ra.STATUS_LABELS[overall])} - {_e(analysis['verdict'])}", banner_style)]],
            colWidths=[CONTENT_W])
        banner.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(STATUS_COLORS[overall])),
            ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ]))
        story += [banner, Spacer(1, 10)]

        # ---------- Synthèse ----------
        story.append(P("Synthèse", h2))
        rows = [header_row(["Domaine", "État", "Constat"])]
        extra = [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(DARK))]
        for i, item in enumerate(analysis["summary"], start=1):
            rows.append([P(f"<b>{_e(item['title'])}</b>"), status_cell(item["status"]),
                         P(_e(item["text"]))])
            extra.append(("BACKGROUND", (1, i), (1, i),
                          colors.HexColor(STATUS_COLORS[item["status"]])))
        t = Table(rows, colWidths=[90, 85, CONTENT_W - 175], repeatRows=1)
        t.setStyle(table_style(extra))
        story.append(t)

        # ---------- Recommandations ----------
        story.append(P("Recommandations", h2))
        recs = analysis["recommendations"]
        if not recs:
            story.append(P("Aucune action nécessaire pour le moment."))
        else:
            for n, r in enumerate(recs, start=1):
                color = STATUS_COLORS[r["level"]]
                story.append(P(f"<font color='{color}'><b>{n}.</b></font> {_e(r['text'])}"))
                story.append(Spacer(1, 3))

        # ---------- Détails ----------
        story.append(P("Détails techniques", h2))

        if options.get("include_system", True) and system:
            story.append(P("<b>Système, processeur et mémoire</b>"))
            rows = [
                ("Système d'exploitation", f"{system['os_name']} ({system['architecture']})"),
                ("Version", system["os_version"]),
                ("Processeur", system["cpu_name"]),
                ("Cœurs / threads", f"{system['cpu_cores']} / {system['cpu_threads']}"),
                ("Charge du processeur", f"{system['cpu_percent']:.0f} %"),
                ("Mémoire (RAM)", f"{system['ram_used_gb']} Go utilisés sur "
                                  f"{system['ram_total_gb']} Go ({system['ram_percent']} %)"),
                ("Dernier redémarrage", f"il y a {system['uptime_days']:.0f} jour(s)"),
            ]
            if system.get("bios"):
                rows.append(("BIOS", system["bios"]))
            t = Table([[P(f"<b>{_e(k)}</b>"), P(_e(v))] for k, v in rows],
                      colWidths=[150, CONTENT_W - 150])
            t.setStyle(table_style([("BACKGROUND", (0, 0), (0, -1), colors.HexColor(LIGHT))]))
            story += [t, Spacer(1, 8)]

        if options.get("include_disks", True):
            story.append(P("<b>Stockage</b>"))
            disks = data["disks"]
            if not disks:
                story.append(P("Non vérifié.", small))
            else:
                rows = [header_row(["Lecteur", "Format", "Capacité", "Utilisé", "Libre", "Rempli"])]
                extra = [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(DARK))]
                for i, d in enumerate(disks, start=1):
                    st = ra.disk_status(d)
                    drive = f"{_e(d['mount'])} <font color='{GREY}' size='8'>({ra.disk_kind(d)})</font>"
                    rows.append([P(drive), P(_e(d["filesystem"])),
                                 P(f"{d['total']} Go"), P(f"{d['used']} Go"),
                                 P(f"{d['free']} Go"),
                                 P(f"<font color='{GREY if d.get('removable') else STATUS_COLORS[st]}'><b>{d['percent']} %</b></font>")])
                t = Table(rows, colWidths=[110, 55, 80, 80, 80, CONTENT_W - 405], repeatRows=1)
                t.setStyle(table_style(extra))
                story.append(t)
            story.append(Spacer(1, 8))

        if options.get("include_network", True):
            story.append(P("<b>Réseau</b>"))
            net = data["network"]
            if net is None:
                story.append(P("Non vérifié.", small))
            else:
                rows = [header_row(["Connexion", "Adresse IP", "Adresse MAC"])]
                for itf in net["interfaces"]:
                    rows.append([P(_e(itf["name"])), P(_e(itf["ip"])), P(_e(itf["mac"]))])
                if not net["interfaces"]:
                    rows.append([P("Aucune connexion active"), P(""), P("")])
                rows.append([P("<b>Accès Internet</b>"),
                             P("Oui" if net["internet"] else "Non"), P("")])
                t = Table(rows, colWidths=[CONTENT_W * 0.40, CONTENT_W * 0.25, CONTENT_W * 0.35],
                          repeatRows=1)
                t.setStyle(table_style([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(DARK))]))
                story.append(t)
            story.append(Spacer(1, 8))

        if options.get("include_security", True):
            story.append(P("<b>Sécurité</b>"))
            checks = data["security"]
            if not checks:
                story.append(P("Non vérifié.", small))
            else:
                rows = [header_row(["Contrôle", "État", "Détail"])]
                extra = [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(DARK))]
                for i, c in enumerate(checks, start=1):
                    st = {"green": ra.OK, "orange": ra.WARNING, "red": ra.DANGER}.get(
                        c.get("color"), ra.UNKNOWN)
                    rows.append([P(_e(c["title"])), status_cell(st), P(_e(c["details"]))])
                    extra.append(("BACKGROUND", (1, i), (1, i), colors.HexColor(STATUS_COLORS[st])))
                t = Table(rows, colWidths=[130, 85, CONTENT_W - 215], repeatRows=1)
                t.setStyle(table_style(extra))
                story.append(t)
            story.append(Spacer(1, 8))

        if options.get("include_printers", True):
            story.append(P("<b>Imprimantes</b>"))
            printers = data["printers"]
            if printers is None:
                story.append(P("Non vérifié.", small))
            elif not printers:
                story.append(P("Aucune imprimante installée.", small))
            else:
                rows = [header_row(["Imprimante", "Port", "État"])]
                for p in printers:
                    name = p["name"] + (" (par défaut)" if p.get("is_default") else "")
                    rows.append([P(_e(name)), P(_e(p["port"])), P(_e(p["status"]))])
                t = Table(rows, colWidths=[CONTENT_W * 0.55, CONTENT_W * 0.25, CONTENT_W * 0.20],
                          repeatRows=1)
                t.setStyle(table_style([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(DARK))]))
                story.append(t)

        # ---------- Santé matérielle ----------
        if options.get("include_health", False):
            story.append(Spacer(1, 8))
            story.append(P("<b>Santé des disques</b>"))
            dh = data.get("disk_health")
            if not dh:
                story.append(P("Non vérifié.", small))
            else:
                rows = [header_row(["Disque", "Type", "Taille", "État", "Usure", "Temp.", "Heures"])]
                extra = [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(DARK))]
                for i, d in enumerate(dh, start=1):
                    h = d["health"].lower()
                    st = (ra.DANGER if "unhealthy" in h else ra.WARNING if "warning" in h
                          else ra.OK if h in ("healthy", "") else ra.UNKNOWN)
                    label = {"healthy": "Bon", "": "Inconnu"}.get(h, d["health"])
                    wear = f"{d['wear']:.0f} %" if d.get("wear") is not None else "n/d"
                    temp = f"{d['temp']:.0f} °C" if d.get("temp") is not None else "n/d"
                    hours = f"{d['hours']:.0f} h" if d.get("hours") is not None else "n/d"
                    rows.append([P(_e(d["name"])), P(_e(d["media"] or "?")),
                                 P(f"{d['size_gb']} Go"),
                                 P(f"<font color='{STATUS_COLORS[st]}'><b>{_e(label)}</b></font>"),
                                 P(wear), P(temp), P(hours)])
                t = Table(rows, colWidths=[CONTENT_W - 330, 55, 55, 55, 55, 55, 55], repeatRows=1)
                t.setStyle(table_style(extra))
                story.append(t)
                story.append(P("n/d : information non fournie par ce disque ou droits insuffisants.",
                               small))
            story.append(Spacer(1, 8))

            bat = data.get("battery")
            if bat and bat.get("present"):
                bat_title = P("<b>Batterie</b>")
                rows = []
                if bat.get("charge") is not None:
                    rows.append(("Charge actuelle", f"{bat['charge']:.0f} %"
                                 + (" (sur secteur)" if bat.get("on_ac") else " (sur batterie)")))
                if bat.get("health_percent") is not None:
                    rows.append(("Capacité restante",
                                 f"{bat['health_percent']} % de la capacité d'origine"))
                if bat.get("design_mwh"):
                    rows.append(("Capacité d'origine / actuelle",
                                 f"{bat['design_mwh'] / 1000:.1f} Wh / "
                                 f"{(bat.get('full_mwh') or 0) / 1000:.1f} Wh"))
                if bat.get("cycles"):
                    rows.append(("Cycles de charge", f"{bat['cycles']:.0f}"))
                if rows:
                    t = Table([[P(f"<b>{_e(k)}</b>"), P(_e(v))] for k, v in rows],
                              colWidths=[170, CONTENT_W - 170])
                    t.setStyle(table_style([("BACKGROUND", (0, 0), (0, -1),
                                             colors.HexColor(LIGHT))]))
                    story.append(KeepTogether([bat_title, t]))  # jamais coupé entre 2 pages
                else:
                    story.append(bat_title)
                    story.append(P("Détails indisponibles sur ce modèle.", small))
                story.append(Spacer(1, 8))

        # ---------- Mises à jour et pilotes ----------
        if options.get("include_updates", False):
            story.append(P("<b>Mises à jour Windows</b>"))
            up = data.get("updates")
            if up is None:
                story.append(P("Non vérifié (connexion Internet ou service Windows Update).", small))
            elif not up["updates"]:
                story.append(P("Aucune mise à jour en attente." + (
                    " Un redémarrage est en attente." if up["reboot_pending"] else ""), small))
            else:
                rows = [header_row(["Mise à jour", "Type"])]
                for u in up["updates"][:12]:
                    kind = "Pilote" if u["is_driver"] else "Sécurité" if u["is_security"] else "Autre"
                    rows.append([P(_e(u["title"])), P(kind)])
                extra_count = len(up["updates"]) - 12
                if extra_count > 0:
                    rows.append([P(f"... et {extra_count} autre(s)"), P("")])
                t = Table(rows, colWidths=[CONTENT_W - 80, 80], repeatRows=1)
                t.setStyle(table_style([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(DARK))]))
                story.append(t)
                if up["reboot_pending"]:
                    story.append(P("Un redémarrage est également en attente.", small))
            story.append(Spacer(1, 8))

            story.append(P("<b>Pilotes et périphériques</b>"))
            devs = data.get("problem_devices")
            if devs is None:
                story.append(P("Non vérifié.", small))
            elif not devs:
                story.append(P("Aucun périphérique en erreur.", small))
            else:
                rows = [header_row(["Périphérique", "Code d'erreur Windows"])]
                for d in devs[:15]:
                    rows.append([P(_e(d["name"])), P(str(d["code"]))])
                t = Table(rows, colWidths=[CONTENT_W - 140, 140], repeatRows=1)
                t.setStyle(table_style([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(DARK))]))
                story.append(t)
            story.append(Spacer(1, 8))

        # ---------- Stabilité ----------
        if options.get("include_events", False):
            story.append(P("<b>Stabilité (journal système)</b>"))
            ev = data.get("events")
            if ev is None:
                story.append(P("Non vérifié.", small))
            else:
                rows = [
                    (f"Écrans bleus ({ev['days']} jours)", str(ev["bsod"])),
                    (f"Arrêts inattendus ({ev['days']} jours)", str(ev["unexpected_shutdowns"])),
                    ("Événements critiques", str(ev["critical"])),
                    ("Erreurs système", str(ev["errors"])),
                ]
                t = Table([[P(f"<b>{_e(k)}</b>"), P(_e(v))] for k, v in rows],
                          colWidths=[200, CONTENT_W - 200])
                t.setStyle(table_style([("BACKGROUND", (0, 0), (0, -1), colors.HexColor(LIGHT))]))
                story.append(t)
                story.append(P("Quelques erreurs système sont normales sur un PC en bon état : "
                               "seuls les écrans bleus et les arrêts inattendus sont retenus "
                               "dans l'évaluation.", small))

        # ---------- Pied de page ----------
        footer_text = (f"{company['name']} - rapport généré le "
                       f"{generated.strftime('%d/%m/%Y à %H:%M')} par DIP Toolkit Pro")

        def draw_footer(canvas, doc):
            canvas.saveState()
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(colors.HexColor(GREY))
            canvas.drawString(MARGIN, 22, footer_text)
            canvas.drawRightString(PAGE_W - MARGIN, 22, f"Page {doc.page}")
            canvas.restoreState()

        doc = SimpleDocTemplate(
            filepath, pagesize=A4,
            leftMargin=MARGIN, rightMargin=MARGIN, topMargin=36, bottomMargin=44,
            title=f"Rapport - {system.get('hostname', '')}",
            author=company["name"],
        )
        doc.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)
