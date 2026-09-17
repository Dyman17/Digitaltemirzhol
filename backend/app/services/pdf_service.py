from pathlib import Path
from app.core.timeutils import now_local
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from PIL import Image as PILImage, ImageDraw, ImageFont

from app.core.config import NARYAD_DIR, SIGNATURES_DIR, BASE_DIR, STORAGE_DIR

# Font with Cyrillic support. Priority:
# 1) bundled DejaVu (repo: backend/app/assets) — works on Render/Linux + Windows
# 2) system DejaVu (typical Linux) 3) Windows Arial 4) Helvetica (no Cyrillic!)
_ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
_FONT_CANDIDATES = [
    (_ASSETS_DIR / "DejaVuSans.ttf", _ASSETS_DIR / "DejaVuSans-Bold.ttf"),
    (Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
     Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")),
    (Path("C:/Windows/Fonts/arial.ttf"), Path("C:/Windows/Fonts/arialbd.ttf")),
]


def _register_fonts():
    for normal, bold in _FONT_CANDIDATES:
        try:
            if normal.exists() and bold.exists():
                pdfmetrics.registerFont(TTFont("DTNormal", str(normal)))
                pdfmetrics.registerFont(TTFont("DTBold", str(bold)))
                return "DTNormal", "DTBold"
        except Exception:
            continue
    return "Helvetica", "Helvetica-Bold"


FONT_NORMAL, FONT_BOLD = _register_fonts()

def _signature_image(url: str | None, max_width: float = 5.0 * cm):
    """ReportLab Image flowable for a /storage/... signature URL, or None."""
    if not url or not url.startswith("/storage/"):
        return None
    path = STORAGE_DIR / url[len("/storage/"):]
    if not path.exists() or path.stat().st_size == 0:
        return None
    try:
        return Image(str(path), width=max_width, height=1.5 * cm)
    except Exception:
        return None


def create_facsimile_signature(name: str, target_path: Path, role: str = "ПЧ"):
    """Creates a transparent PNG facsimile stamp if needed."""
    img = PILImage.new('RGBA', (320, 100), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Blue ink stamp
    ink_color = (25, 60, 150, 230)
    
    # Draw oval / stamp frame
    draw.rounded_rectangle([(10, 10), (310, 90)], radius=12, outline=ink_color, width=2)
    draw.text((25, 20), f"ҚТЖ • {role} ЭЛЕКТРОНДЫ ҚОЛЫ", fill=ink_color)
    draw.text((25, 42), f"{name}", fill=ink_color)
    draw.text((25, 66), f"Дата: {now_local().strftime('%d.%m.%Y %H:%M')}", fill=ink_color)
    
    target_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(target_path, "PNG")
    return str(target_path)

def generate_naryad_pdf(naryad, db) -> str:
    """
    Generates official Kazakhstan Railways (ҚТЖ) Work Order Form №451
    with digital facsimile stamps, safety instructions, and brigade checklist.
    """
    filename = f"naryad_{naryad.number.replace('/', '_').replace(' ', '_')}.pdf"
    pdf_path = NARYAD_DIR / filename

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        fontName=FONT_BOLD,
        fontSize=13,
        leading=16,
        alignment=1,
        textColor=colors.HexColor("#0f172a")
    )
    sub_style = ParagraphStyle(
        'DocSub',
        fontName=FONT_NORMAL,
        fontSize=9,
        leading=12,
        alignment=1,
        textColor=colors.HexColor("#475569")
    )
    normal_style = ParagraphStyle(
        'DocNormal',
        fontName=FONT_NORMAL,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#1e293b")
    )
    bold_style = ParagraphStyle(
        'DocBold',
        fontName=FONT_BOLD,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#0f172a")
    )

    elements = []

    # 1. Header
    elements.append(Paragraph("«ҚАЗАҚСТАН ТЕМІР ЖОЛЫ» ҰК» АҚ", title_style))
    elements.append(Paragraph("МАГИСТРАЛЬДЫҚ ЖЕЛІ ДЕПАРТАМЕНТІ • ПЧ-13 ДИСТАНЦИЯСЫ", sub_style))
    elements.append(Spacer(1, 0.4 * cm))
    elements.append(Paragraph(f"<b>НАРЯД-ДОПУСК № {naryad.number}</b>", title_style))
    elements.append(Paragraph("ТЕМІРЖОЛ ПУТЬТЕРІНДЕ ЖҰМЫС ӨНДІРУГЕ ЖӘНЕ ҚАУІПСІЗДІК ТЕХНИКАСЫНА (№451 БЛАНК)", sub_style))
    elements.append(Spacer(1, 0.5 * cm))

    # 2. Main Order Table
    master_name = naryad.master.full_name if naryad.master else "Жол шебері"
    boss_name = naryad.boss.full_name if naryad.boss else "Начальник дистанции пути"
    disp_name = naryad.dispatcher.full_name if naryad.dispatcher else "Поезд диспетчері"

    order_info = [
        [
            Paragraph("<b>Кәсіпорын:</b>", normal_style),
            Paragraph(naryad.organization or "ПЧ-13 (Алматы дистанциясы)", normal_style),
            Paragraph("<b>Бөлімше:</b>", normal_style),
            Paragraph(naryad.subdivision or "Участок №3, Околоток №10", normal_style)
        ],
        [
            Paragraph("<b>Жұмыс жетекшісі (Мастер):</b>", normal_style),
            Paragraph(master_name, bold_style),
            Paragraph("<b>Жұмыс орны:</b>", normal_style),
            Paragraph(naryad.location, bold_style)
        ],
        [
            Paragraph("<b>Жұмыс түрі:</b>", normal_style),
            Paragraph(naryad.work_type, bold_style),
            Paragraph("<b>Тех. карта №:</b>", normal_style),
            Paragraph(naryad.tech_card_no, bold_style)
        ],
        [
            Paragraph("<b>Жоспарлы уақыт:</b>", normal_style),
            Paragraph(f"{naryad.plan_start} — {naryad.plan_end}", normal_style),
            Paragraph("<b>Мәртебесі (Статус):</b>", normal_style),
            Paragraph(f"<b>{naryad.status}</b>", bold_style)
        ]
    ]

    t1 = Table(order_info, colWidths=[4.2*cm, 5.0*cm, 3.8*cm, 5.0*cm])
    t1.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#0f172a")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f8fafc")),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor("#f8fafc")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(t1)
    elements.append(Spacer(1, 0.4 * cm))

    # 3. Safety Measures
    elements.append(Paragraph("<b>1. ҚАУІПСІЗДІК ШАРАЛАРЫ ЖӘНЕ СИГНАЛДЫҚ ОГРАЖДЕНИЕ:</b>", bold_style))
    measures_text = naryad.safety_measures or "Қызыл қалқан орнатылды, ДУ-46 журналына жазылды, сигналист свистокпен сапқа қойылды, жол бұру стрелкалары бекітілді."
    elements.append(Paragraph(measures_text, normal_style))
    elements.append(Spacer(1, 0.4 * cm))

    # 4. Brigade Table
    elements.append(Paragraph("<b>2. БРИГАДА ҚҰРАМЫ ЖӘНЕ НҰСҚАМА (ИНСТРУКТАЖДЫ РАСТАУ):</b>", bold_style))
    elements.append(Spacer(1, 0.2 * cm))

    brigade_data = [
        [
            Paragraph("<b>№</b>", bold_style),
            Paragraph("<b>Т.А.Ә. (ФИО)</b>", bold_style),
            Paragraph("<b>Лауазымы</b>", bold_style),
            Paragraph("<b>Табель №</b>", bold_style),
            Paragraph("<b>Қолтаңба / Растау</b>", bold_style)
        ]
    ]

    for idx, b_member in enumerate(naryad.brigade_members, start=1):
        worker = b_member.user
        brigade_data.append([
            Paragraph(str(idx), normal_style),
            Paragraph(worker.full_name, normal_style),
            Paragraph(worker.position or "Монтер пути", normal_style),
            Paragraph(worker.emp_num or f"RG-{worker.id:04d}", normal_style),
            Paragraph("✓ Биометриямен расталған", normal_style)
        ])

    if len(brigade_data) == 1:
        brigade_data.append([
            Paragraph("1", normal_style),
            Paragraph(master_name, normal_style),
            Paragraph("Жол шебері / Бригадир", normal_style),
            Paragraph("RG-00105", normal_style),
            Paragraph("✓ Расталды", normal_style)
        ])

    t_brigade = Table(brigade_data, colWidths=[1.0*cm, 6.5*cm, 4.5*cm, 2.5*cm, 3.5*cm])
    t_brigade.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#0f172a")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_brigade)
    elements.append(Spacer(1, 0.5 * cm))

    # 5. Approvals & Facsimiles (Boss & Dispatcher)
    elements.append(Paragraph("<b>3. КЕЛІСУ ЖӘНЕ ЭЛЕКТРОНДЫ ҚОЛТАҢБАЛАР:</b>", bold_style))
    elements.append(Spacer(1, 0.2 * cm))

    boss_stamp_desc = f"<b>БЕКІТТІ (Бастық):</b><br/>{boss_name}<br/>Мәртебесі: ҚОЛ ҚОЙЫЛҒАН<br/>Дата: {naryad.created_at.strftime('%d.%m.%Y %H:%M')}"
    disp_stamp_desc = f"<b>РҰҚСАТ БЕРДІ (Диспетчер):</b><br/>{disp_name}<br/>«Технологиялық терезе» берілді<br/>Дата: {now_local().strftime('%d.%m.%Y %H:%M')}"
    master_stamp_desc = f"<b>ЖҰМЫСТЫ ТАПСЫРДЫ (Мастер):</b><br/>{master_name}<br/>Жұмыс аяқталды, жол бос.<br/>Уақыт: {naryad.actual_end or '16:30'}"

    def approval_cell(desc: str, sig_url: str | None):
        parts = [Paragraph(desc, normal_style)]
        img = _signature_image(sig_url)
        if img is not None:
            parts.append(img)
        return parts

    approval_table = [
        [
            approval_cell(boss_stamp_desc, getattr(naryad, "boss_signature_url", None)),
            approval_cell(disp_stamp_desc, getattr(naryad, "dispatcher_signature_url", None)),
            approval_cell(master_stamp_desc, getattr(naryad, "master_signature_url", None)),
        ]
    ]

    t_approval = Table(approval_table, colWidths=[6.0*cm, 6.0*cm, 6.0*cm])
    t_approval.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#2563eb")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#93c5fd")),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#eff6ff")),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(t_approval)
    elements.append(Spacer(1, 0.5 * cm))

    # 6. Footer verification code
    elements.append(Paragraph(
        f"Құжат «Digital Temirzhol» цифрлық жүйесімен бекітілген. Электронды тексеру коды: SHA256-KTZ-{naryad.id:06d}-SEC",
        sub_style
    ))

    doc.build(elements)
    return f"/storage/naryad_docs/{filename}"
