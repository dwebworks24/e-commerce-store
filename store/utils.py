import threading
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from django.conf import settings

def send_email_async(subject, text_content, html_content, to_email):
    msg = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL or 'gsa32476@gmail.com',
        [to_email]
    )
    msg.attach_alternative(html_content, "text/html")
    try:
        msg.send()
        print(f"Email sent successfully to {to_email} with subject '{subject}'")
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")

def send_order_email_thread(subject, text_content, html_content, to_email):
    thread = threading.Thread(target=send_email_async, args=(subject, text_content, html_content, to_email))
    thread.start()

def get_order_html_template(order, title, body_text):
    items_html = ""
    # order.items.all() references OrderItem related name (if configured)
    # Let's write a safe lookup for items
    items = getattr(order, 'items', None)
    if items:
        for item in items.all():
            items_html += f"""
            <tr>
                <td style="padding: 12px; border-bottom: 1px solid #eeeeee; font-family: sans-serif; font-size: 14px; color: #333333;">{item.product_name} ({item.size or 'N/A'} / {item.color or 'N/A'})</td>
                <td style="padding: 12px; border-bottom: 1px solid #eeeeee; font-family: sans-serif; font-size: 14px; color: #333333; text-align: center;">{item.quantity}</td>
                <td style="padding: 12px; border-bottom: 1px solid #eeeeee; font-family: sans-serif; font-size: 14px; color: #333333; text-align: right;">₹{item.price}</td>
            </tr>
            """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{title}</title>
    </head>
    <body style="margin: 0; padding: 0; background-color: #f6f6f6; font-family: sans-serif;-webkit-font-smoothing: antialiased; font-size: 14px; line-height: 1.4; -ms-text-size-adjust: 100%; -webkit-text-size-adjust: 100%;">
        <table role="presentation" border="0" cellpadding="0" cellspacing="0" class="body" style="border-collapse: separate; mso-table-lspace: 0pt; mso-table-rspace: 0pt; width: 100%; background-color: #f6f6f6;">
            <tr>
                <td style="font-family: sans-serif; font-size: 14px; vertical-align: top;">&nbsp;</td>
                <td class="container" style="font-family: sans-serif; font-size: 14px; vertical-align: top; display: block; max-width: 580px; padding: 10px; width: 580px; margin: 0 auto;">
                    <div class="content" style="box-sizing: border-box; display: block; margin: 0 auto; max-width: 580px; padding: 10px;">
                        <div style="text-align: center; padding: 20px 0;">
                            <h1 style="font-family: sans-serif; font-size: 28px; font-weight: bold; margin: 0; color: #1a1a1a; letter-spacing: 2px;">AURELIA</h1>
                            <p style="font-family: sans-serif; font-size: 12px; color: #888888; margin: 5px 0 0 0; text-transform: uppercase; letter-spacing: 1px;">Women's Fashion Store</p>
                        </div>
                        <table role="presentation" class="main" style="border-collapse: separate; mso-table-lspace: 0pt; mso-table-rspace: 0pt; width: 100%; background: #ffffff; border-radius: 8px; border: 1px solid #e9e9e9;">
                            <tr>
                                <td class="wrapper" style="font-family: sans-serif; font-size: 14px; vertical-align: top; box-sizing: border-box; padding: 30px;">
                                    <table role="presentation" border="0" cellpadding="0" cellspacing="0" style="border-collapse: separate; mso-table-lspace: 0pt; mso-table-rspace: 0pt; width: 100%;">
                                        <tr>
                                            <td style="font-family: sans-serif; font-size: 14px; vertical-align: top;">
                                                <h2 style="color: #1a1a1a; font-family: sans-serif; font-weight: 400; line-height: 1.4; margin: 0; margin-bottom: 16px; font-size: 20px; font-weight: bold;">{title}</h2>
                                                <p style="font-family: sans-serif; font-size: 14px; font-weight: normal; margin: 0; margin-bottom: 24px; color: #555555; line-height: 1.6;">Hello {getattr(order.user, 'first_name', 'Customer')},</p>
                                                <p style="font-family: sans-serif; font-size: 14px; font-weight: normal; margin: 0; margin-bottom: 24px; color: #555555; line-height: 1.6;">{body_text}</p>
                                                
                                                <div style="background-color: #fafafa; border: 1px solid #eeeeee; padding: 20px; border-radius: 6px; margin-bottom: 24px;">
                                                    <h3 style="margin-top: 0; margin-bottom: 15px; font-family: sans-serif; font-size: 14px; font-weight: bold; color: #1a1a1a; border-bottom: 1px solid #eeeeee; padding-bottom: 8px;">Order Details</h3>
                                                    <table border="0" cellpadding="0" cellspacing="0" style="width: 100%; font-family: sans-serif; font-size: 12px; color: #666666;">
                                                        <tr>
                                                            <td style="padding: 4px 0; font-weight: bold; width: 120px;">Order Number:</td>
                                                            <td style="padding: 4px 0; color: #1a1a1a;">{order.order_number}</td>
                                                        </tr>
                                                        <tr>
                                                            <td style="padding: 4px 0; font-weight: bold;">Status:</td>
                                                            <td style="padding: 4px 0; color: #1a1a1a;"><span style="background-color: #e5e7eb; color: #1f2937; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; text-transform: uppercase;">{order.status}</span></td>
                                                        </tr>
                                                        <tr>
                                                            <td style="padding: 4px 0; font-weight: bold;">Payment:</td>
                                                            <td style="padding: 4px 0; color: #1a1a1a;"><span style="background-color: #d1fae5; color: #065f46; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; text-transform: uppercase;">{order.payment_status}</span></td>
                                                        </tr>
                                                        <tr>
                                                            <td style="padding: 4px 0; font-weight: bold; vertical-align: top;">Shipping To:</td>
                                                            <td style="padding: 4px 0; color: #1a1a1a; line-height: 1.4;">
                                                                {getattr(order.user, 'first_name', '')} {getattr(order.user, 'last_name', '')}<br>
                                                                {order.shipping_address}<br>
                                                                {order.city}, {order.state} - {order.pincode}<br>
                                                                Phone: {order.phone}
                                                            </td>
                                                        </tr>
                                                    </table>
                                                </div>

                                                <h3 style="margin-top: 0; margin-bottom: 15px; font-family: sans-serif; font-size: 14px; font-weight: bold; color: #1a1a1a;">Items Ordered</h3>
                                                <table cellpadding="0" cellspacing="0" style="width: 100%; border-collapse: collapse; margin-bottom: 24px;">
                                                    <thead>
                                                        <tr style="background-color: #fafafa;">
                                                            <th style="padding: 12px; text-align: left; font-family: sans-serif; font-size: 12px; font-weight: bold; color: #666666; border-bottom: 2px solid #eeeeee;">Product</th>
                                                            <th style="padding: 12px; text-align: center; font-family: sans-serif; font-size: 12px; font-weight: bold; color: #666666; border-bottom: 2px solid #eeeeee; width: 60px;">Qty</th>
                                                            <th style="padding: 12px; text-align: right; font-family: sans-serif; font-size: 12px; font-weight: bold; color: #666666; border-bottom: 2px solid #eeeeee; width: 100px;">Price</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        {items_html}
                                                        <tr>
                                                            <td colspan="2" style="padding: 12px; font-family: sans-serif; font-size: 14px; font-weight: bold; text-align: right; border-top: 2px solid #eeeeee;">Total Paid:</td>
                                                            <td style="padding: 12px; font-family: sans-serif; font-size: 14px; font-weight: bold; text-align: right; color: #1a1a1a; border-top: 2px solid #eeeeee;">₹{order.total}</td>
                                                        </tr>
                                                    </tbody>
                                                </table>

                                                <p style="font-family: sans-serif; font-size: 12px; font-weight: normal; margin: 0; margin-top: 30px; color: #999999; text-align: center; line-height: 1.5;">
                                                    If you have any questions, reply to this email or contact us at support@aurelia.com
                                                </p>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                        </table>
                        <div style="text-align: center; padding: 20px 0;">
                            <p style="font-family: sans-serif; font-size: 11px; color: #aaaaaa; margin: 0;">&copy; 2026 AURELIA. All rights reserved.</p>
                        </div>
                    </div>
                </td>
                <td style="font-family: sans-serif; font-size: 14px; vertical-align: top;">&nbsp;</td>
            </tr>
        </table>
    </body>
    </html>
    """
    return html

def send_order_status_email(order, is_new, old_status, old_payment_status):
    if not order.user or not order.user.email:
        return

    to_email = order.user.email
    subject = ""
    body_text = ""
    title = ""

    if is_new:
        if order.payment_status == 'paid':
            title = "Order Payment Successful & Confirmed!"
            subject = f"Order #{order.order_number} Payment Received - Aurelia Store"
            body_text = f"Your payment has been received successfully. Your order #{order.order_number} is confirmed and is currently being processed."
        else:
            title = "Order Placed Successfully!"
            subject = f"Order #{order.order_number} Placed Successfully - Aurelia Store"
            body_text = f"Thank you for shopping with Aurelia! Your order #{order.order_number} has been received. If you selected Cash on Delivery, please have the amount ready when your package arrives."
    elif old_status and order.status != old_status:
        title = f"Your Order Status has changed to {order.status.capitalize()}!"
        subject = f"Order #{order.order_number} Status Updated: {order.status.capitalize()} - Aurelia Store"
        
        if order.status == 'confirmed':
            body_text = f"Great news! Your order #{order.order_number} has been confirmed by our team."
        elif order.status == 'processing':
            body_text = f"Your order #{order.order_number} is now in processing and items are being packed for dispatch."
        elif order.status == 'shipped':
            tracking_info = f" (Tracking: {order.tracking_number})" if order.tracking_number else ""
            body_text = f"Exciting news! Your order #{order.order_number} has been shipped{tracking_info}. It will reach you soon!"
        elif order.status == 'delivered':
            body_text = f"Your order #{order.order_number} has been delivered. We hope you love your purchase! Thank you for choosing Aurelia."
        elif order.status == 'cancelled':
            body_text = f"Your order #{order.order_number} has been cancelled. If this is unexpected, please contact our support team."
        else:
            body_text = f"The status of your order #{order.order_number} has been updated to {order.status}."
    elif old_payment_status and order.payment_status != old_payment_status and order.payment_status == 'paid':
        title = "Payment Received!"
        subject = f"Payment Received for Order #{order.order_number} - Aurelia Store"
        body_text = f"We have received the payment of ₹{order.total} for your order #{order.order_number}. Thank you!"
    else:
        return

    # Create database notification
    try:
        from .models import Notification
        Notification.objects.create(
            user=order.user,
            title=title,
            message=body_text
        )
    except Exception as e:
        print(f"Failed to create database notification: {e}")

    html_content = get_order_html_template(order, title, body_text)
    text_content = strip_tags(html_content)
    
    send_order_email_thread(subject, text_content, html_content, to_email)

def send_expo_push_notification(token, title, body, data=None):
    if not token:
        return None
    
    import requests
    import json

    payload = {
        'to': token,
        'title': title,
        'body': body,
        'sound': 'default',
    }
    if data:
        payload['data'] = data

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Accept-encoding': 'gzip, deflate',
    }

    try:
        response = requests.post(
            'https://exp.host/--/api/v2/push/send',
            data=json.dumps(payload),
            headers=headers
        )
        response.raise_for_status()
        res_json = response.json()
        print(f"Expo Push Notification sent. Response: {res_json}")
        return res_json
    except Exception as e:
        print(f"Failed to send Expo Push Notification: {e}")
        return None
