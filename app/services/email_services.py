import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from flask import current_app, url_for

def send_invitation_email(to_email, org_name, role, token):
    """
    Envía un correo de invitación usando Brevo (Sendinblue).
    Retorna: (True, ID_Email) si éxito, (False, Error) si falla.
    """
    # Configurar la API Key
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = current_app.config.get("BREVO_API_KEY")

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
    
    # Generar enlace de invitación
    invite_link = url_for('auth.register_via_invite', token=token, _external=True)

    # Contenido HTML del correo
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
        <h2 style="color: #0d6efd;">Bienvenido a Veloce</h2>
        <p>Hola,</p>
        <p>Te han invitado a unirte al equipo de <strong>{org_name}</strong> con el rol de <strong>{role.upper()}</strong>.</p>
        <p>Para configurar tu cuenta y comenzar, haz clic en el siguiente botón:</p>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{invite_link}" style="background-color: #0d6efd; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                Aceptar Invitación
            </a>
        </div>
        
        <p style="font-size: 12px; color: #666;">
            Si el botón no funciona, copia y pega este enlace en tu navegador:<br>
            <a href="{invite_link}">{invite_link}</a>
        </p>
        <p style="color: #888; font-size: 12px; margin-top: 20px;">Este enlace es válido por 48 horas.</p>
    </div>
    """

    # Crear el objeto de email transaccional
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": to_email}],
        sender={"name": "Veloce", "email": "dionyjunior11@gmail.com"}, # Asegúrate de que este remitente esté verificado en Brevo
        subject=f"Invitación a colaborar en {org_name}",
        html_content=html_content
    )

    try:
        api_response = api_instance.send_transac_email(send_smtp_email)
        return True, api_response.message_id
    except ApiException as e:
        print(f"Error al enviar email con Brevo: {e}")
        return False, str(e)