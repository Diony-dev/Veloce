from flask import Flask
from flask_login import LoginManager
from app.database import init_db, mongo
from app.models.usuario import Usuario
import cloudinary
import cloudinary.uploader
from app.routes.auth import auth_bp
from app.routes.mainroute import main_bp
from app.routes.factura_route import factura_bp
from app.routes.cliente_route import cliente_bp
from app.routes.gastos_route import gastos_bp
from app.routes.config_route import config_bp
from app.routes.team_route import team_bp
from app.routes.producto_route import producto_bp
from bson import ObjectId

login_manager = LoginManager()

def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)
    init_db(app)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Configuration settings can be added here
    cloudinary.config(
        cloud_name=app.config.get('CLOUDINARY_CLOUD_NAME'),
        api_key=app.config.get('CLOUDINARY_API_KEY'),
        api_secret=app.config.get('CLOUDINARY_API_SECRET')
    )
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp, url_prefix='/')
    app.register_blueprint(factura_bp, url_prefix='/facturas')
    app.register_blueprint(cliente_bp, url_prefix='/clientes')
    app.register_blueprint(gastos_bp, url_prefix='/gastos')
    app.register_blueprint(config_bp, url_prefix='/config')
    app.register_blueprint(team_bp, url_prefix='/team')
    app.register_blueprint(producto_bp, url_prefix='/productos')

    from app.routes.report_route import report_bp
    app.register_blueprint(report_bp)

    from app.utils.date_util import to_local
    app.jinja_env.filters['local_datetime'] = to_local

    return app

@login_manager.user_loader
def load_user(user_id):
    data = mongo.db.usuarios.find_one({"_id": ObjectId(user_id)})
    if data:
        user = Usuario(
            id=data['_id'],
            organizacion_id=data['organizacion_id'],
            nombre=data['nombre'],
            correo=data['correo'],
            contraseña=data['contraseña'],
            rol=data['rol'],
            departamento=data['departamento'],
            foto=data['foto']
        )
        return user
    return None