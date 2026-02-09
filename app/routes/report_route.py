from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app.services.report_services import get_cuadre_diario
from app.services.report_generation_services import (
    get_cuentas_por_cobrar, 
    get_reporte_fiscal, 
    get_ventas_por_rango,
    get_gastos_por_rango
)

report_bp = Blueprint('report', __name__, url_prefix='/reportes')

@report_bp.route('/')
@login_required
def index():
    """Panel principal de reportes"""
    return render_template('reports/index.html')

@report_bp.route('/cuadre')
@login_required
def cuadre_diario():
    fecha_str = request.args.get('fecha')
    if not fecha_str:
        fecha_str = datetime.now().strftime('%Y-%m-%d')
    
    data = get_cuadre_diario(current_user.organizacion_id, fecha_str)
    return render_template('reports/cuadre.html', data=data, fecha_actual=fecha_str)

@report_bp.route('/cxc')
@login_required
def cuentas_por_cobrar():
    facturas = get_cuentas_por_cobrar(current_user.organizacion_id)
    total_deuda = sum(f.get('total', 0) for f in facturas)
    return render_template('reports/cxc.html', facturas=facturas, total_deuda=total_deuda)

@report_bp.route('/fiscal')
@login_required
def reporte_fiscal():
    # Fechas por defecto: Mes actual
    now = datetime.now()
    default_start = datetime(now.year, now.month, 1).strftime('%Y-%m-%d')
    default_end = now.strftime('%Y-%m-%d')

    start = request.args.get('fecha_inicio', default_start)
    end = request.args.get('fecha_fin', default_end)
    
    facturas = get_reporte_fiscal(current_user.organizacion_id, start, end)
    
    # Totales para el resumen
    total_base = sum(f.get('base_imponible', 0) for f in facturas)
    total_itbis = sum(f.get('itbis_calculado', 0) for f in facturas)
    total_general = sum(f.get('total_facturado', 0) for f in facturas)
    
    return render_template('reports/fiscal.html', 
                         facturas=facturas, 
                         fecha_inicio=start, 
                         fecha_fin=end,
                         total_base=total_base,
                         total_itbis=total_itbis,
                         total_general=total_general)

@report_bp.route('/ventas')
@login_required
def reporte_ventas():
    now = datetime.now()
    default_start = datetime(now.year, now.month, 1).strftime('%Y-%m-%d')
    default_end = now.strftime('%Y-%m-%d')

    start = request.args.get('fecha_inicio', default_start)
    end = request.args.get('fecha_fin', default_end)

    ventas = get_ventas_por_rango(current_user.organizacion_id, start, end)
    
    return render_template('reports/ventas.html', ventas=ventas, fecha_inicio=start, fecha_fin=end)

@report_bp.route('/gastos')
@login_required
def reporte_gastos():
    now = datetime.now()
    default_start = datetime(now.year, now.month, 1).strftime('%Y-%m-%d')
    default_end = now.strftime('%Y-%m-%d')

    start = request.args.get('fecha_inicio', default_start)
    end = request.args.get('fecha_fin', default_end)

    gastos = get_gastos_por_rango(current_user.organizacion_id, start, end)
    total_gastos = sum(g.get('monto', 0) for g in gastos)
    
    return render_template('reports/gastos.html', gastos=gastos, fecha_inicio=start, fecha_fin=end, total_gastos=total_gastos)
