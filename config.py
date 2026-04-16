import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database', 'aces.db')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB
SECRET_KEY = 'aces-alquiler-contabilidad-2025'

CATEGORY_COLORS = {
    # Ingresos — verdes/azules/cálidos
    'honorarios_gestion':  '#10b981',
    'busqueda_inquilinos': '#06b6d4',
    'fee_garantia':        '#f59e0b',
    'fee_suministros':     '#8b5cf6',
    'fee_reparaciones':    '#ec4899',
    'renta_inquilinos':    '#14b8a6',
    'otros_ingresos':      '#64748b',
    # Gastos — rojos/naranjas
    'nominas':             '#f43f5e',
    'marketing':           '#fb923c',
    'software':            '#fbbf24',
    'gestoria':            '#a78bfa',
    'seguros':             '#34d399',
    'liquidacion_propietarios': '#9333ea',
    'comisiones_banco':    '#94a3b8',
    'otros_gastos':        '#6b7280',
    'sin_categoria':       '#4b5563',
}

SEED_RULES = [
    # ── INGRESOS ──
    {
        'key': 'honorarios_gestion',
        'label': 'Honorarios Gestión Integral',
        'type': 'income',
        'priority': 10,
        'keywords': [
            'honorarios gestion', 'honorarios gestión',
            'gestion integral', 'gestión integral',
            'cuota gestion', 'cuota gestión',
            'comision gestion', 'comisión gestión',
        ],
    },
    {
        'key': 'renta_inquilinos',
        'label': 'Renta de Inquilinos (tránsito)',
        'type': 'income',
        'priority': 15,
        'keywords': [
            'renta alquiler', 'cobro alquiler', 'pago alquiler',
            'transferencia alquiler', 'alquiler recibido',
            'renta mensual', 'cuota arrendamiento', 'ingreso alquiler',
        ],
    },
    {
        'key': 'busqueda_inquilinos',
        'label': 'Búsqueda de Inquilinos',
        'type': 'income',
        'priority': 20,
        'keywords': [
            'busqueda inquilino', 'búsqueda inquilino',
            'captacion inquilino', 'captación inquilino',
            'alta inquilino', 'nuevo inquilino',
            'seleccion inquilino', 'selección inquilino',
        ],
    },
    {
        'key': 'fee_garantia',
        'label': 'Fee Garantía de Pago',
        'type': 'income',
        'priority': 30,
        'keywords': [
            'garantia alquiler', 'garantía alquiler',
            'seguro impago', 'fee garantia', 'fee garantía',
            'prima garantia', 'prima garantía',
        ],
    },
    {
        'key': 'fee_suministros',
        'label': 'Fee Gestión Suministros',
        'type': 'income',
        'priority': 40,
        'keywords': [
            'fee suministros', 'gestion suministros',
            'gestión suministros', 'cambio suministro',
            'alta suministro', 'tramite luz', 'tramite agua',
        ],
    },
    {
        'key': 'fee_reparaciones',
        'label': 'Fee Reparaciones',
        'type': 'income',
        'priority': 50,
        'keywords': [
            'fee reparacion', 'fee reparación',
            'comision reparacion', 'comisión reparación',
            'gestion averia', 'gestión avería',
        ],
    },
    {
        'key': 'otros_ingresos',
        'label': 'Otros Ingresos',
        'type': 'income',
        'priority': 90,
        'keywords': [
            'transferencia recibida', 'ingreso varios',
            'devolucion hacienda', 'devolución hacienda',
            'abono', 'reintegro',
        ],
    },
    # ── GASTOS ──
    {
        'key': 'nominas',
        'label': 'Nóminas y Personal',
        'type': 'expense',
        'priority': 10,
        'keywords': [
            'nomina', 'nómina', 'salario', 'sueldo',
            'seguridad social', 'ss trabajador',
            'irpf trabajador', 'finiquito',
        ],
    },
    {
        'key': 'marketing',
        'label': 'Marketing y Publicidad',
        'type': 'expense',
        'priority': 20,
        'keywords': [
            'publicidad', 'google ads', 'meta ads',
            'facebook ads', 'idealista', 'fotocasa',
            'habitaclia', 'fotografia', 'fotografía',
            'diseño', 'imprenta',
        ],
    },
    {
        'key': 'software',
        'label': 'Software y Suscripciones',
        'type': 'expense',
        'priority': 30,
        'keywords': [
            'software', 'suscripcion', 'suscripción',
            'microsoft', 'adobe', 'holded', 'crm',
            'dominio', 'hosting', 'saas',
        ],
    },
    {
        'key': 'gestoria',
        'label': 'Gestoría y Asesoría Legal',
        'type': 'expense',
        'priority': 40,
        'keywords': [
            'gestoria', 'gestoría', 'asesoria', 'asesoría',
            'abogado', 'notario', 'juridico', 'jurídico',
            'registro', 'tramite legal', 'trámite legal',
        ],
    },
    {
        'key': 'seguros',
        'label': 'Seguros',
        'type': 'expense',
        'priority': 50,
        'keywords': [
            'seguro', 'prima seguro', 'axa', 'mapfre',
            'allianz', 'zurich', 'mutua',
        ],
    },
    {
        'key': 'liquidacion_propietarios',
        'label': 'Liquidación a Propietarios',
        'type': 'expense',
        'priority': 55,
        'keywords': [
            'liquidacion', 'liquidación',
            'pago propietario', 'transferencia propietario',
            'abono propietario', 'dinero propietario',
            'liquidacion propietario', 'liquidación propietario',
        ],
    },
    {
        'key': 'comisiones_banco',
        'label': 'Comisiones Bancarias',
        'type': 'expense',
        'priority': 60,
        'keywords': [
            'comision bancaria', 'comisión bancaria',
            'cuota banco', 'mantenimiento cuenta',
            'tpv', 'transferencia emitida',
        ],
    },
    {
        'key': 'otros_gastos',
        'label': 'Otros Gastos',
        'type': 'expense',
        'priority': 95,
        'keywords': [
            'gasto varios', 'material oficina',
            'telefono', 'teléfono', 'internet',
            'dietas', 'transporte',
        ],
    },
]
