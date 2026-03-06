"""
Service Layer para Envío de Emails

Soporta múltiples backends:
- Django SMTP (Gmail, Outlook, etc.)
- SendGrid API
- AWS SES

Configuración en settings.py
"""

from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Optional
import logging

from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone

from apps.notificaciones.models import EmailsEnviados

logger = logging.getLogger(__name__)


class EmailService:
    """
    Service Layer para envío de emails multicanal.

    Métodos principales:
    - enviar_alerta_saldo_bajo()
    - enviar_recarga_exitosa()
    - enviar_factura_recarga()
    - enviar_email_generico()
    """

    @staticmethod
    def enviar_alerta_saldo_bajo(
        email_destinatario: str,
        nombre_destinatario: str,
        nro_tarjeta: str,
        nombre_hijo: str,
        saldo_actual: Decimal,
        saldo_alerta: Decimal,
    ) -> Dict:
        """
        Envía email de alerta de saldo bajo.

        Args:
            email_destinatario: Email del destinatario
            nombre_destinatario: Nombre completo del destinatario
            nro_tarjeta: Número de tarjeta
            nombre_hijo: Nombre del estudiante
            saldo_actual: Saldo actual
            saldo_alerta: Límite de alerta configurado

        Returns:
            {
                'success': bool,
                'id_email': int,
                'fecha_envio': datetime
            }
        """
        try:
            asunto = f"⚠️ Alerta de Saldo Bajo - Tarjeta {nro_tarjeta}"

            # Generar cuerpo HTML
            cuerpo_html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #ff6b6b; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; background-color: #f9f9f9; }}
                    .info-box {{ background-color: white; padding: 15px; margin: 10px 0; border-left: 4px solid #ff6b6b; }}
                    .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
                    .button {{ 
                        display: inline-block; 
                        padding: 12px 24px; 
                        background-color: #4CAF50; 
                        color: white; 
                        text-decoration: none; 
                        border-radius: 4px; 
                        margin-top: 15px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>⚠️ Alerta de Saldo Bajo</h1>
                    </div>
                    <div class="content">
                        <p>Estimado/a <strong>{nombre_destinatario}</strong>,</p>
                        
                        <p>Le informamos que el saldo de la tarjeta está por debajo del límite configurado:</p>
                        
                        <div class="info-box">
                            <p><strong>Estudiante:</strong> {nombre_hijo}</p>
                            <p><strong>Tarjeta:</strong> {nro_tarjeta}</p>
                            <p><strong>Saldo actual:</strong> ₲{saldo_actual:,.2f}</p>
                            <p><strong>Límite de alerta:</strong> ₲{saldo_alerta:,.2f}</p>
                        </div>
                        
                        <p>Le recomendamos realizar una recarga para evitar que el saldo llegue a cero.</p>
                        
                        <div style="text-align: center;">
                            <a href="https://app.cantinatita.com/recargas" class="button">
                                Recargar Ahora
                            </a>
                        </div>
                    </div>
                    <div class="footer">
                        <p>Este es un mensaje automático del Sistema de Gestión de Cantina Tita.</p>
                        <p>Por favor no responda a este email.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            # Cuerpo texto plano
            cuerpo_texto = f"""
ALERTA DE SALDO BAJO

Estimado/a {nombre_destinatario},

Le informamos que el saldo de la tarjeta está por debajo del límite configurado:

Estudiante: {nombre_hijo}
Tarjeta: {nro_tarjeta}
Saldo actual: ₲{saldo_actual:,.2f}
Límite de alerta: ₲{saldo_alerta:,.2f}

Le recomendamos realizar una recarga para evitar inconvenientes.

Cantina Tita - Sistema de Gestión
            """

            # Crear email multipart
            email = EmailMultiAlternatives(
                subject=asunto,
                body=cuerpo_texto,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email_destinatario],
            )
            email.attach_alternative(cuerpo_html, "text/html")

            # Enviar
            email.send(fail_silently=False)

            # Registrar en BD
            email_enviado = EmailsEnviados.objects.create(
                email_destinatario=email_destinatario,
                nombre_destinatario=nombre_destinatario,
                asunto=asunto,
                cuerpo=cuerpo_texto,
                estado="enviado",
                fecha_envio=timezone.now(),
            )

            logger.info(f"Email saldo bajo enviado a {email_destinatario}")

            return {
                "success": True,
                "id_email": email_enviado.id_email,
                "fecha_envio": email_enviado.fecha_envio,
            }

        except Exception as e:
            logger.error(f"Error enviando email saldo bajo: {str(e)}")

            # Registrar error en BD
            EmailsEnviados.objects.create(
                email_destinatario=email_destinatario,
                nombre_destinatario=nombre_destinatario,
                asunto=asunto,
                cuerpo=f"Error: {str(e)}",
                estado="error",
                fecha_envio=timezone.now(),
            )

            return {"success": False, "error": str(e)}

    @staticmethod
    def enviar_recarga_exitosa(
        email_destinatario: str,
        nombre_destinatario: str,
        nro_tarjeta: str,
        nombre_hijo: str,
        monto_acreditado: Decimal,
        saldo_nuevo: Decimal,
        metodo_pago: str,
        fecha_recarga: datetime,
    ) -> Dict:
        """
        Envía email de confirmación de recarga exitosa.

        Args:
            email_destinatario: Email del cliente
            nombre_destinatario: Nombre del cliente
            nro_tarjeta: Número de tarjeta
            nombre_hijo: Nombre del estudiante
            monto_acreditado: Monto acreditado
            saldo_nuevo: Nuevo saldo
            metodo_pago: Método de pago utilizado
            fecha_recarga: Fecha y hora de la recarga

        Returns:
            {
                'success': bool,
                'id_email': int
            }
        """
        try:
            asunto = f"✅ Recarga Exitosa - Tarjeta {nro_tarjeta}"

            cuerpo_html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; background-color: #f9f9f9; }}
                    .success-box {{ background-color: white; padding: 15px; margin: 10px 0; border-left: 4px solid #4CAF50; }}
                    .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>✅ Recarga Exitosa</h1>
                    </div>
                    <div class="content">
                        <p>Estimado/a <strong>{nombre_destinatario}</strong>,</p>
                        
                        <p>Su recarga se ha procesado exitosamente:</p>
                        
                        <div class="success-box">
                            <p><strong>Estudiante:</strong> {nombre_hijo}</p>
                            <p><strong>Tarjeta:</strong> {nro_tarjeta}</p>
                            <p><strong>Monto acreditado:</strong> ₲{monto_acreditado:,.2f}</p>
                            <p><strong>Nuevo saldo:</strong> ₲{saldo_nuevo:,.2f}</p>
                            <p><strong>Método de pago:</strong> {metodo_pago}</p>
                            <p><strong>Fecha:</strong> {fecha_recarga.strftime('%d/%m/%Y %H:%M')}</p>
                        </div>
                        
                        <p>Gracias por confiar en Cantina Tita.</p>
                    </div>
                    <div class="footer">
                        <p>Este es un mensaje automático del Sistema de Gestión de Cantina Tita.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            cuerpo_texto = f"""
RECARGA EXITOSA

Estimado/a {nombre_destinatario},

Su recarga se ha procesado exitosamente:

Estudiante: {nombre_hijo}
Tarjeta: {nro_tarjeta}
Monto acreditado: ₲{monto_acreditado:,.2f}
Nuevo saldo: ₲{saldo_nuevo:,.2f}
Método de pago: {metodo_pago}
Fecha: {fecha_recarga.strftime('%d/%m/%Y %H:%M')}

Gracias por confiar en Cantina Tita.
            """

            email = EmailMultiAlternatives(
                subject=asunto,
                body=cuerpo_texto,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email_destinatario],
            )
            email.attach_alternative(cuerpo_html, "text/html")
            email.send(fail_silently=False)

            # Registrar
            email_enviado = EmailsEnviados.objects.create(
                email_destinatario=email_destinatario,
                nombre_destinatario=nombre_destinatario,
                asunto=asunto,
                cuerpo=cuerpo_texto,
                estado="enviado",
                fecha_envio=timezone.now(),
            )

            return {"success": True, "id_email": email_enviado.id_email}

        except Exception as e:
            logger.error(f"Error enviando email recarga: {str(e)}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def enviar_email_generico(
        email_destinatario: str,
        nombre_destinatario: str,
        asunto: str,
        mensaje: str,
        tipo_email: str = "generico",
    ) -> Dict:
        """
        Envía email genérico.

        Args:
            email_destinatario: Email del destinatario
            nombre_destinatario: Nombre del destinatario
            asunto: Asunto del email
            mensaje: Cuerpo del mensaje
            tipo_email: Tipo de email (generico, alerta, notificacion)

        Returns:
            {
                'success': bool,
                'id_email': int
            }
        """
        try:
            send_mail(
                subject=asunto,
                message=mensaje,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email_destinatario],
                fail_silently=False,
            )

            # Registrar
            email_enviado = EmailsEnviados.objects.create(
                email_destinatario=email_destinatario,
                nombre_destinatario=nombre_destinatario,
                asunto=asunto,
                cuerpo=mensaje,
                estado="enviado",
                fecha_envio=timezone.now(),
            )

            return {"success": True, "id_email": email_enviado.id_email}

        except Exception as e:
            logger.error(f"Error enviando email genérico: {str(e)}")
            return {"success": False, "error": str(e)}
