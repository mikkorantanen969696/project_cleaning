import qrcode
from qrcode.constants import ERROR_CORRECT_L
import os
from datetime import datetime

def generate_payment_qr(amount, client_name, order_id, output_path="./qr_codes/"):
    os.makedirs(output_path, exist_ok=True)
    
    # Generate QR code data for payment
    qr_data = f"""Платеж за услуги уборки
Сумма: {amount} руб.
Клиент: {client_name}
Заказ №: {order_id}
Дата: {datetime.now().strftime('%d.%m.%Y')}
"""
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_L,
        box_size=10,
        border=5,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    # Create QR code image
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Save QR code
    filename = f"payment_{order_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = os.path.join(output_path, filename)
    qr_img.save(filepath)
    
    return filepath

def generate_contact_qr(phone, name, output_path="./qr_codes/"):
    os.makedirs(output_path, exist_ok=True)
    
    # vCard format for contact information
    vcard_data = f"""BEGIN:VCARD
VERSION:3.0
FN:{name}
TEL:{phone}
END:VCARD"""
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_L,
        box_size=10,
        border=5,
    )
    qr.add_data(vcard_data)
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    filename = f"contact_{name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = os.path.join(output_path, filename)
    qr_img.save(filepath)
    
    return filepath
