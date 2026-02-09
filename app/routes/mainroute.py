from flask import blueprints, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from ..services.auth_services import authenticate_user, exists_organizacion_rnc, get_organizacion_by_id
from ..services.factura_services import count_facturas_by_organizacion
from ..services.report_services import get_kpis_mes_actual, get_comparativa_anual, get_gastos_por_categoria, get_top_clientes
import json

main_bp = blueprints.Blueprint('main', __name__)


@main_bp.route('/')
@login_required
def dashboard():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.register'))
    
    org_id = current_user.organizacion_id
    organizacion = get_organizacion_by_id(org_id)
    
    # Obtener datos para el dashboard
    kpis = get_kpis_mes_actual(org_id)
    comparativa = get_comparativa_anual(org_id)
    gastos_cat = get_gastos_por_categoria(org_id)
    top_clientes = get_top_clientes(org_id)
    
    # Serializar datos para gráficos (Backend Rendering)
    comparativa_json = json.dumps(comparativa)
    gastos_cat_json = json.dumps(gastos_cat)
    
    return render_template('main/dashboard.html', 
                           organizacion=organizacion,
                           kpis=kpis,
                           comparativa_json=comparativa_json,
                           gastos_cat_json=gastos_cat_json,
                           top_clientes=top_clientes)