"""
SPYNET SafeKids — Backend Flask
Controle parental legítimo com MDM, geofencing e IA
"""

from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_socketio import SocketIO, emit, join_room
from flask_cors import CORS
from datetime import datetime, timedelta
import os, hashlib, requests

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'safekids-secret-dev')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET', 'safekids-jwt-dev')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=12)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///safekids.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
jwt = JWTManager(app)
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)

# ─── MODELOS ───────────────────────────────────────────────────────────────────

class Responsavel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)
    telefone = db.Column(db.String(20))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    dispositivos = db.relationship('Dispositivo', backref='dono', lazy=True)

    def verificar_senha(self, senha):
        return self.senha_hash == hashlib.sha256(senha.encode()).hexdigest()

class Dispositivo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    plataforma = db.Column(db.String(20))  # android / ios / windows
    responsavel_id = db.Column(db.Integer, db.ForeignKey('responsavel.id'))
    token_device = db.Column(db.String(256), unique=True)
    online = db.Column(db.Boolean, default=False)
    ultimo_acesso = db.Column(db.DateTime)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    configuracoes = db.relationship('Configuracao', backref='dispositivo', uselist=False)
    eventos = db.relationship('Evento', backref='dispositivo', lazy=True)

class Configuracao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dispositivo_id = db.Column(db.Integer, db.ForeignKey('dispositivo.id'))
    limite_diario_min = db.Column(db.Integer, default=300)   # minutos
    modo_noturno_inicio = db.Column(db.String(5), default='21:00')
    modo_noturno_fim = db.Column(db.String(5), default='07:00')
    geo_lat = db.Column(db.Float)
    geo_lng = db.Column(db.Float)
    geo_raio_m = db.Column(db.Integer, default=500)
    apps_bloqueados = db.Column(db.Text, default='')
    categorias_bloqueadas = db.Column(db.Text, default='adulto,violencia,apostas')

class Evento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dispositivo_id = db.Column(db.Integer, db.ForeignKey('dispositivo.id'))
    tipo = db.Column(db.String(50))   # site_bloqueado, saiu_zona, limite_proximo, conteudo_suspeito
    descricao = db.Column(db.String(500))
    severidade = db.Column(db.String(20), default='info')  # info / warn / danger
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

class UsoApp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dispositivo_id = db.Column(db.Integer, db.ForeignKey('dispositivo.id'))
    data = db.Column(db.Date, default=datetime.utcnow)
    minutos_total = db.Column(db.Integer, default=0)
    apps_json = db.Column(db.Text, default='{}')

# ─── AUTH ──────────────────────────────────────────────────────────────────────

@app.route('/api/auth/registro', methods=['POST'])
def registro():
    data = request.json
    if Responsavel.query.filter_by(email=data['email']).first():
        return jsonify({'erro': 'E-mail já cadastrado'}), 400
    r = Responsavel(
        nome=data['nome'],
        email=data['email'],
        senha_hash=hashlib.sha256(data['senha'].encode()).hexdigest(),
        telefone=data.get('telefone', '')
    )
    db.session.add(r)
    db.session.commit()
    token = create_access_token(identity=str(r.id))
    return jsonify({'token': token, 'nome': r.nome}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    r = Responsavel.query.filter_by(email=data['email']).first()
    if not r or not r.verificar_senha(data['senha']):
        return jsonify({'erro': 'Credenciais inválidas'}), 401
    token = create_access_token(identity=str(r.id))
    return jsonify({'token': token, 'nome': r.nome})

# ─── DISPOSITIVOS ──────────────────────────────────────────────────────────────

@app.route('/api/dispositivos', methods=['GET'])
@jwt_required()
def listar_dispositivos():
    uid = int(get_jwt_identity())
    devs = Dispositivo.query.filter_by(responsavel_id=uid).all()
    return jsonify([{
        'id': d.id, 'nome': d.nome, 'plataforma': d.plataforma,
        'online': d.online, 'ultimo_acesso': d.ultimo_acesso.isoformat() if d.ultimo_acesso else None,
        'lat': d.lat, 'lng': d.lng
    } for d in devs])

@app.route('/api/dispositivos', methods=['POST'])
@jwt_required()
def adicionar_dispositivo():
    uid = int(get_jwt_identity())
    data = request.json
    token = hashlib.sha256(f"{uid}{data['nome']}{datetime.utcnow()}".encode()).hexdigest()
    d = Dispositivo(nome=data['nome'], plataforma=data.get('plataforma','android'),
                    responsavel_id=uid, token_device=token)
    db.session.add(d)
    db.session.flush()
    cfg = Configuracao(dispositivo_id=d.id)
    db.session.add(cfg)
    db.session.commit()
    return jsonify({'id': d.id, 'token_device': token}), 201

@app.route('/api/dispositivos/<int:did>/config', methods=['GET', 'PUT'])
@jwt_required()
def configuracao(did):
    uid = int(get_jwt_identity())
    d = Dispositivo.query.filter_by(id=did, responsavel_id=uid).first_or_404()
    cfg = d.configuracoes
    if request.method == 'GET':
        return jsonify({
            'limite_diario_min': cfg.limite_diario_min,
            'modo_noturno_inicio': cfg.modo_noturno_inicio,
            'modo_noturno_fim': cfg.modo_noturno_fim,
            'geo_lat': cfg.geo_lat, 'geo_lng': cfg.geo_lng,
            'geo_raio_m': cfg.geo_raio_m,
            'apps_bloqueados': cfg.apps_bloqueados.split(',') if cfg.apps_bloqueados else [],
            'categorias_bloqueadas': cfg.categorias_bloqueadas.split(',')
        })
    data = request.json
    for k, v in data.items():
        if hasattr(cfg, k):
            if k in ('apps_bloqueados', 'categorias_bloqueadas') and isinstance(v, list):
                v = ','.join(v)
            setattr(cfg, k, v)
    db.session.commit()
    socketio.emit('config_atualizada', {'dispositivo_id': did}, room=f'device_{did}')
    return jsonify({'ok': True})

# ─── EVENTOS / ALERTAS ─────────────────────────────────────────────────────────

@app.route('/api/dispositivos/<int:did>/eventos', methods=['GET'])
@jwt_required()
def listar_eventos(did):
    uid = int(get_jwt_identity())
    Dispositivo.query.filter_by(id=did, responsavel_id=uid).first_or_404()
    eventos = Evento.query.filter_by(dispositivo_id=did)\
                          .order_by(Evento.criado_em.desc()).limit(50).all()
    return jsonify([{
        'id': e.id, 'tipo': e.tipo, 'descricao': e.descricao,
        'severidade': e.severidade, 'criado_em': e.criado_em.isoformat()
    } for e in eventos])

@app.route('/api/device/evento', methods=['POST'])
def receber_evento():
    """Endpoint chamado pelo app filho no dispositivo da criança"""
    token = request.headers.get('X-Device-Token')
    d = Dispositivo.query.filter_by(token_device=token).first()
    if not d:
        return jsonify({'erro': 'Token inválido'}), 403
    data = request.json
    e = Evento(dispositivo_id=d.id, tipo=data['tipo'],
               descricao=data['descricao'], severidade=data.get('severidade','info'))
    db.session.add(e)
    db.session.commit()
    socketio.emit('novo_evento', {
        'tipo': e.tipo, 'descricao': e.descricao,
        'severidade': e.severidade, 'dispositivo': d.nome
    }, room=f'responsavel_{d.responsavel_id}')
    _enviar_whatsapp_alerta(d, e)
    return jsonify({'ok': True})

@app.route('/api/device/localizacao', methods=['POST'])
def atualizar_localizacao():
    """App filho envia GPS periodicamente"""
    token = request.headers.get('X-Device-Token')
    d = Dispositivo.query.filter_by(token_device=token).first()
    if not d:
        return jsonify({'erro': 'Token inválido'}), 403
    data = request.json
    d.lat, d.lng = data['lat'], data['lng']
    d.online = True
    d.ultimo_acesso = datetime.utcnow()
    db.session.commit()
    cfg = d.configuracoes
    if cfg and cfg.geo_lat and cfg.geo_lng:
        dist = _haversine(d.lat, d.lng, cfg.geo_lat, cfg.geo_lng)
        if dist > cfg.geo_raio_m:
            e = Evento(dispositivo_id=d.id, tipo='saiu_zona_segura',
                       descricao=f'Fora da zona segura ({int(dist)}m do centro)',
                       severidade='danger')
            db.session.add(e)
            db.session.commit()
            socketio.emit('saiu_zona', {'dispositivo': d.nome, 'distancia': int(dist)},
                          room=f'responsavel_{d.responsavel_id}')
    socketio.emit('localizacao', {'lat': d.lat, 'lng': d.lng, 'nome': d.nome},
                  room=f'responsavel_{d.responsavel_id}')
    return jsonify({'ok': True})

@app.route('/api/device/uso', methods=['POST'])
def reportar_uso():
    token = request.headers.get('X-Device-Token')
    d = Dispositivo.query.filter_by(token_device=token).first()
    if not d:
        return jsonify({'erro': 'Token inválido'}), 403
    data = request.json
    hoje = datetime.utcnow().date()
    uso = UsoApp.query.filter_by(dispositivo_id=d.id, data=hoje).first()
    if not uso:
        uso = UsoApp(dispositivo_id=d.id, data=hoje)
        db.session.add(uso)
    uso.minutos_total = data['minutos_total']
    uso.apps_json = str(data.get('apps', {}))
    db.session.commit()
    cfg = d.configuracoes
    if cfg and uso.minutos_total >= cfg.limite_diario_min * 0.9:
        e = Evento(dispositivo_id=d.id, tipo='limite_proximo',
                   descricao=f'Usando {uso.minutos_total}min de {cfg.limite_diario_min}min',
                   severidade='warn')
        db.session.add(e)
        db.session.commit()
    return jsonify({'bloqueado': cfg and uso.minutos_total >= cfg.limite_diario_min})

# ─── ANÁLISE DE CONTEÚDO COM IA ────────────────────────────────────────────────

@app.route('/api/device/analisar-texto', methods=['POST'])
def analisar_texto():
    """Analisa texto com Anthropic API para detectar conteúdo impróprio"""
    token = request.headers.get('X-Device-Token')
    d = Dispositivo.query.filter_by(token_device=token).first()
    if not d:
        return jsonify({'erro': 'Token inválido'}), 403
    data = request.json
    texto = data.get('texto', '')
    resultado = _analisar_com_ia(texto)
    if resultado['risco'] in ('medio', 'alto'):
        sev = 'danger' if resultado['risco'] == 'alto' else 'warn'
        e = Evento(dispositivo_id=d.id, tipo='conteudo_suspeito',
                   descricao=resultado['motivo'], severidade=sev)
        db.session.add(e)
        db.session.commit()
        socketio.emit('conteudo_suspeito', {'dispositivo': d.nome, 'motivo': resultado['motivo']},
                      room=f'responsavel_{d.responsavel_id}')
    return jsonify(resultado)

# ─── RELATÓRIOS ────────────────────────────────────────────────────────────────

@app.route('/api/relatorio/<int:did>/semanal')
@jwt_required()
def relatorio_semanal(did):
    uid = int(get_jwt_identity())
    d = Dispositivo.query.filter_by(id=did, responsavel_id=uid).first_or_404()
    hoje = datetime.utcnow().date()
    semana_atras = hoje - timedelta(days=7)
    eventos = Evento.query.filter(
        Evento.dispositivo_id == did,
        Evento.criado_em >= semana_atras
    ).order_by(Evento.criado_em.desc()).all()
    usos = UsoApp.query.filter(
        UsoApp.dispositivo_id == did,
        UsoApp.data >= semana_atras
    ).all()
    return jsonify({
        'dispositivo': d.nome,
        'periodo': f'{semana_atras} a {hoje}',
        'total_eventos': len(eventos),
        'eventos_criticos': sum(1 for e in eventos if e.severidade == 'danger'),
        'media_uso_min': sum(u.minutos_total for u in usos) // max(len(usos), 1),
        'eventos': [{
            'tipo': e.tipo, 'descricao': e.descricao,
            'severidade': e.severidade, 'data': e.criado_em.isoformat()
        } for e in eventos[:20]]
    })

# ─── WEBSOCKET ─────────────────────────────────────────────────────────────────

@socketio.on('join_responsavel')
def on_join_responsavel(data):
    join_room(f"responsavel_{data['responsavel_id']}")

@socketio.on('join_device')
def on_join_device(data):
    join_room(f"device_{data['device_id']}")

# ─── HELPERS ───────────────────────────────────────────────────────────────────

def _haversine(lat1, lon1, lat2, lon2):
    import math
    R = 6371000
    p = math.pi / 180
    a = (math.sin((lat2-lat1)*p/2)**2 +
         math.cos(lat1*p)*math.cos(lat2*p)*math.sin((lon2-lon1)*p/2)**2)
    return 2*R*math.asin(math.sqrt(a))

def _analisar_com_ia(texto):
    api_key = os.environ.get('ANTHROPIC_API_KEY', '')
    if not api_key:
        return {'risco': 'baixo', 'motivo': 'IA não configurada'}
    try:
        resp = requests.post('https://api.anthropic.com/v1/messages',
            headers={'x-api-key': api_key, 'anthropic-version': '2023-06-01',
                     'content-type': 'application/json'},
            json={'model': 'claude-haiku-4-5-20251001', 'max_tokens': 200,
                  'messages': [{'role': 'user', 'content':
                    f"""Analise o texto abaixo e retorne JSON com:
- risco: "baixo", "medio" ou "alto"
- motivo: descrição curta (máx 80 chars)
Critérios: linguagem violenta, sexual, cyberbullying, grooming, drogas, ódio.
Texto: "{texto[:500]}"
Responda apenas JSON, sem markdown."""}]},
            timeout=8)
        import json
        content = resp.json()['content'][0]['text']
        return json.loads(content)
    except Exception:
        return {'risco': 'baixo', 'motivo': 'Erro na análise'}

def _enviar_whatsapp_alerta(dispositivo, evento):
    """Envia alerta via Z-API para o responsável"""
    if evento.severidade not in ('warn', 'danger'):
        return
    zapi_instance = os.environ.get('ZAPI_INSTANCE')
    zapi_token = os.environ.get('ZAPI_TOKEN')
    telefone = dispositivo.dono.telefone
    if not all([zapi_instance, zapi_token, telefone]):
        return
    emoji = '🚨' if evento.severidade == 'danger' else '⚠️'
    msg = f"{emoji} *SPYNET SafeKids*\n\nDispositivo: {dispositivo.nome}\nAlerta: {evento.descricao}\nHorário: {evento.criado_em.strftime('%H:%M')}"
    try:
        requests.post(
            f'https://api.z-api.io/instances/{zapi_instance}/token/{zapi_token}/send-text',
            json={'phone': telefone, 'message': msg}, timeout=5)
    except Exception:
        pass

# ─── FRONTEND ────────────────────────────────────────────────────────────────────

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def frontend(path):
    import os
    frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
    if path and os.path.exists(os.path.join(frontend_dir, path)):
        return send_from_directory(frontend_dir, path)
    return send_from_directory(frontend_dir, "dashboard.html")

# ─── INIT ──────────────────────────────────────────────────────────────────────

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
