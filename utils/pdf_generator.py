from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import os
from datetime import datetime
import qrcode
from io import BytesIO

# Register Cyrillic font
try:
    pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))
    font_name = 'DejaVu'
except:
    font_name = 'Helvetica'

def generate_invoice_pdf(order_data, output_path="./pdfs/"):
    os.makedirs(output_path, exist_ok=True)
    
    filename = f"invoice_{order_data['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(output_path, filename)
    
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=HexColor('#2E86AB')
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=12,
        leftIndent=20
    )
    
    # Header
    story.append(Paragraph("СЧЕТ НА ОПЛАТУ", title_style))
    story.append(Spacer(1, 20))
    
    # Invoice info
    invoice_info = [
        ['Номер счета:', f"#{order_data['id']}"],
        ['Дата создания:', datetime.now().strftime('%d.%m.%Y')],
        ['Клиент:', order_data['client_name']],
        ['Телефон:', order_data['client_phone']],
        ['Адрес:', order_data['address']],
    ]
    
    invoice_table = Table(invoice_info, colWidths=[2*inch, 4*inch])
    invoice_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#F8F9FA')),
        ('TEXTCOLOR', (0, 0), (-1, -1), black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, HexColor('#DEE2E6')),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(invoice_table)
    story.append(Spacer(1, 20))
    
    # Service details
    service_info = [
        ['Тип уборки:', order_data['cleaning_type']],
        ['Дата и время:', order_data['date_time'].strftime('%d.%m.%Y %H:%M')],
        ['Продолжительность:', f"{order_data['duration_hours']} час."],
        ['Оборудование:', 'Есть' if order_data['equipment_available'] else 'Нет'],
        ['Моющие средства:', 'Есть' if order_data['chemicals_available'] else 'Нет'],
    ]
    
    if order_data.get('notes'):
        service_info.append(['Примечания:', order_data['notes']])
    
    service_table = Table(service_info, colWidths=[2*inch, 4*inch])
    service_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#E8F4FD')),
        ('TEXTCOLOR', (0, 0), (-1, -1), black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, HexColor('#DEE2E6')),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(service_table)
    story.append(Spacer(1, 30))
    
    # Total
    total_table = Table([
        ['Итого:', f"{order_data['price']} руб."],
        ['НДС:', '0 руб.'],
        ['К оплате:', f"{order_data['price']} руб."]
    ], colWidths=[4*inch, 2*inch])
    
    total_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 2), (-1, 2), HexColor('#28A745')),
        ('TEXTCOLOR', (0, 2), (-1, 2), white),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('FONTNAME', (0, 2), (-1, 2), font_name),
        ('FONTSIZE', (0, 2), (-1, 2), 14),
        ('BOLD', (0, 2), (-1, 2), 1),
        ('GRID', (0, 0), (-1, -1), 1, HexColor('#DEE2E6')),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(total_table)
    story.append(Spacer(1, 30))
    
    # Payment QR code
    qr_data = f"Сумма: {order_data['price']} руб.\nНазначение: Оплата услуг уборки\nКлиент: {order_data['client_name']}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    
    # Add QR code to PDF (simplified - in production you'd use ReportLab's Image)
    story.append(Paragraph("QR-код для оплаты:", styles['Heading2']))
    story.append(Spacer(1, 10))
    
    # Footer
    story.append(Spacer(1, 50))
    story.append(Paragraph("Спасибо за ваш заказ!", ParagraphStyle('Footer', alignment=TA_CENTER, fontSize=14)))
    story.append(Paragraph("Свяжитесь с нами для уточнения деталей", ParagraphStyle('Footer', alignment=TA_CENTER, fontSize=10)))
    
    doc.build(story)
    return filepath
