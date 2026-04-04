# ============================================================
# SPYNET SAFE KIDS - app.py
# Rode: python app.py
# Acesse: http://localhost:5000
# Senha admin: safekids2026
# Senha landing (nao precisa): publica
# ============================================================
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for, make_response
from datetime import datetime, timezone, timedelta
from functools import wraps
import json, os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "spynet-safekids-2026")
BR_TZ = timezone(timedelta(hours=-3))
ADMIN_SENHA = os.environ.get("ADMIN_SENHA", "safekids2026")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CLIENTES_FILE = os.path.join(DATA_DIR, "clientes.json")
os.makedirs(DATA_DIR, exist_ok=True)

# ============================================================
# HELPERS
# ============================================================
def _load(path, default):
    try:
        if not os.path.exists(path): return default
        with open(path,"r",encoding="utf-8") as f: return json.load(f)
    except: return default

def _save(path, obj):
    tmp = path+".tmp"
    with open(tmp,"w",encoding="utf-8") as f: json.dump(obj,f,ensure_ascii=False,indent=2)
    os.replace(tmp, path)

def load_clientes(): return _load(CLIENTES_FILE, [])
def save_clientes(c): _save(CLIENTES_FILE, c)
def now_br(): return datetime.now(BR_TZ).strftime("%d/%m/%Y %H:%M")

def login_required(f):
    @wraps(f)
    def dec(*a,**k):
        if not session.get("admin"): return redirect(url_for("admin_login"))
        return f(*a,**k)
    return dec

# ============================================================
# LANDING PAGE HTML
# ============================================================
LANDING_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>SPYNET Safe Kids — Proteja seus Filhos</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&family=Orbitron:wght@700;900&display=swap" rel="stylesheet">
<style>
:root{--accent:#6366f1;--green:#10b981;--warn:#f59e0b;--danger:#ef4444;--text:#0f172a;--muted:#64748b;--border:#e2e8f0;--bg:#f8faff;}
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:'Nunito',sans-serif;color:var(--text);background:#fff;}
/* NAV */
nav{background:#0f172a;padding:14px 32px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100;}
.nav-brand{font-family:'Orbitron',monospace;font-size:14px;font-weight:900;letter-spacing:2px;color:#818cf8;}
.nav-sub{font-size:10px;color:rgba(255,255,255,0.4);letter-spacing:1px;}
.nav-links{display:flex;align-items:center;gap:20px;}
.nav-link{color:rgba(255,255,255,0.6);font-size:13px;font-weight:600;text-decoration:none;}
.nav-link:hover{color:#fff;}
.nav-cta{background:#6366f1;color:#fff;padding:8px 18px;border-radius:8px;font-size:12px;font-weight:800;text-decoration:none;}
/* HERO */
.hero{background:linear-gradient(135deg,#0f172a 0%,#1e1b4b 60%,#0f172a 100%);padding:80px 32px;text-align:center;position:relative;overflow:hidden;}
.hero::before{content:'';position:absolute;inset:0;background-image:radial-gradient(circle at 20% 50%,rgba(99,102,241,0.2),transparent 50%),radial-gradient(circle at 80% 30%,rgba(16,185,129,0.1),transparent 50%);}
.hero-badge{display:inline-flex;align-items:center;gap:6px;background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.3);color:#818cf8;font-size:11px;font-weight:700;padding:6px 16px;border-radius:20px;margin-bottom:24px;letter-spacing:1px;}
.bdot{width:6px;height:6px;border-radius:50%;background:#6366f1;animation:blink 1.5s infinite;display:inline-block;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0.2}}
.hero h1{font-size:48px;font-weight:900;color:#fff;line-height:1.15;margin-bottom:16px;}
.hero h1 span{background:linear-gradient(90deg,#818cf8,#34d399);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
.hero p{font-size:18px;color:rgba(255,255,255,0.65);max-width:580px;margin:0 auto 36px;line-height:1.7;}
.hero-btns{display:flex;gap:14px;justify-content:center;flex-wrap:wrap;}
.btn-lg{padding:16px 32px;border-radius:12px;font-size:15px;font-weight:800;cursor:pointer;border:none;font-family:'Nunito',sans-serif;text-decoration:none;display:inline-block;transition:all .2s;}
.btn-green{background:linear-gradient(135deg,#10b981,#059669);color:#fff;box-shadow:0 6px 24px rgba(16,185,129,0.4);}
.btn-green:hover{transform:translateY(-2px);box-shadow:0 10px 32px rgba(16,185,129,0.5);}
.btn-outline-w{background:rgba(255,255,255,0.08);color:#fff;border:1px solid rgba(255,255,255,0.2);}
.btn-outline-w:hover{background:rgba(255,255,255,0.15);}
.hero-proof{margin-top:40px;display:flex;justify-content:center;gap:32px;flex-wrap:wrap;}
.proof{display:flex;align-items:center;gap:8px;color:rgba(255,255,255,0.6);font-size:13px;font-weight:600;}
/* FEATURES */
.features{padding:72px 32px;background:#fff;}
.sec-label{text-align:center;font-size:11px;font-weight:800;color:#6366f1;letter-spacing:3px;text-transform:uppercase;margin-bottom:10px;}
.sec-title{text-align:center;font-size:32px;font-weight:900;color:var(--text);margin-bottom:8px;}
.sec-sub{text-align:center;font-size:15px;color:var(--muted);margin-bottom:48px;}
.feat-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;max-width:960px;margin:0 auto;}
.feat{background:var(--bg);border:1px solid var(--border);border-radius:14px;padding:24px;transition:all .2s;}
.feat:hover{border-color:#6366f1;transform:translateY(-3px);box-shadow:0 8px 24px rgba(99,102,241,0.1);}
.feat-ico{font-size:36px;margin-bottom:14px;}
.feat h3{font-size:16px;font-weight:800;margin-bottom:8px;}
.feat p{font-size:13px;color:var(--muted);line-height:1.6;}
.feat-tag{display:inline-block;background:#f0fdf4;color:#16a34a;font-size:10px;font-weight:700;padding:3px 10px;border-radius:10px;margin-top:10px;border:1px solid #bbf7d0;}
/* HOW */
.how{padding:72px 32px;background:linear-gradient(135deg,#f8faff,#eff6ff);}
.steps{display:grid;grid-template-columns:repeat(4,1fr);gap:20px;max-width:900px;margin:40px auto 0;}
.step{text-align:center;}
.step-n{width:48px;height:48px;border-radius:50%;background:#6366f1;color:#fff;font-size:20px;font-weight:900;display:flex;align-items:center;justify-content:center;margin:0 auto 14px;}
.step h4{font-size:14px;font-weight:800;margin-bottom:6px;}
.step p{font-size:12px;color:var(--muted);}
/* PRICING */
.pricing{padding:72px 32px;background:#fff;}
.price-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;max-width:900px;margin:40px auto 0;}
.price-card{border:2px solid var(--border);border-radius:16px;padding:28px;text-align:center;position:relative;transition:all .2s;}
.price-card:hover{transform:translateY(-3px);}
.price-card.pop{border-color:#6366f1;box-shadow:0 8px 32px rgba(99,102,241,0.15);}
.pop-tag{position:absolute;top:-14px;left:50%;transform:translateX(-50%);background:#6366f1;color:#fff;font-size:10px;font-weight:800;padding:5px 16px;border-radius:20px;letter-spacing:1px;white-space:nowrap;}
.price-name{font-size:12px;font-weight:800;color:var(--muted);text-transform:uppercase;letter-spacing:2px;margin-bottom:10px;}
.price-val{font-size:40px;font-weight:900;color:var(--text);}
.price-per{font-size:14px;color:var(--muted);}
.price-feats{margin:18px 0;text-align:left;}
.pf{font-size:13px;color:var(--text);padding:5px 0;display:flex;align-items:center;gap:8px;}
.pf::before{content:'✓';color:#10b981;font-weight:900;flex-shrink:0;}
.pf.no{color:var(--muted);}
.pf.no::before{content:'✗';color:#e2e8f0;}
.btn-price{width:100%;padding:13px;border-radius:10px;font-size:13px;font-weight:800;cursor:pointer;border:none;font-family:'Nunito',sans-serif;margin-top:10px;transition:all .2s;text-decoration:none;display:block;}
.btn-price.primary{background:#6366f1;color:#fff;}
.btn-price.primary:hover{background:#4f46e5;}
.btn-price.sec{background:var(--bg);color:var(--muted);border:2px solid var(--border);}
/* TESTIMONIALS */
.tests{padding:72px 32px;background:linear-gradient(135deg,#0f172a,#1e1b4b);}
.tests .sec-title{color:#fff;}
.tests .sec-sub{color:rgba(255,255,255,0.5);}
.test-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;max-width:960px;margin:40px auto 0;}
.test{background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);border-radius:14px;padding:20px;}
.stars{color:#fbbf24;font-size:16px;margin-bottom:10px;}
.test p{font-size:13px;color:rgba(255,255,255,0.75);line-height:1.7;margin-bottom:14px;}
.test-auth{display:flex;align-items:center;gap:10px;}
.test-av{width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:800;color:#fff;}
.test-name{font-size:12px;font-weight:800;color:#fff;}
.test-city{font-size:11px;color:rgba(255,255,255,0.4);}
/* FAQ */
.faq{padding:72px 32px;background:#fff;}
.faq-wrap{max-width:680px;margin:40px auto 0;}
.faq-item{border:1px solid var(--border);border-radius:12px;margin-bottom:10px;overflow:hidden;}
.faq-q{padding:16px 20px;font-size:14px;font-weight:800;color:var(--text);cursor:pointer;display:flex;justify-content:space-between;align-items:center;background:#fff;}
.faq-q:hover{background:var(--bg);}
.faq-a{padding:0 20px;max-height:0;overflow:hidden;transition:all .3s;font-size:13px;color:var(--muted);line-height:1.7;}
.faq-a.open{padding:14px 20px;max-height:300px;}
/* CTA */
.cta{padding:80px 32px;background:linear-gradient(135deg,#6366f1,#4f46e5);text-align:center;}
.cta h2{font-size:36px;font-weight:900;color:#fff;margin-bottom:12px;}
.cta p{font-size:16px;color:rgba(255,255,255,0.75);margin-bottom:32px;}
/* FOOTER */
footer{background:#0f172a;padding:24px 32px;text-align:center;color:rgba(255,255,255,0.4);font-size:12px;}
</style>
</head>
<body>
<nav>
  <div>
    <div class="nav-brand">SPYNET SAFE KIDS</div>
    <div class="nav-sub">PROTEÇÃO FAMILIAR INTELIGENTE</div>
  </div>
  <div class="nav-links">
    <a class="nav-link" href="#funcionalidades">Funcionalidades</a>
    <a class="nav-link" href="#planos">Planos</a>
    <a class="nav-link" href="#faq">FAQ</a>
    <a class="nav-cta" href="/admin">Área Admin</a>
  </div>
</nav>

<!-- HERO -->
<div class="hero">
  <div class="hero-badge"><span class="bdot"></span> NOVO · SPYNET SAFE KIDS 2026</div>
  <h1>Proteja seus filhos<br><span>onde eles estiverem</span></h1>
  <p>Monitore localização GPS, conversas, apps e receba alertas em tempo real direto no seu celular. Simples, seguro e 100% legal.</p>
  <div class="hero-btns">
    <a class="btn-lg btn-green" href="#planos">🛡️ Proteger meu filho agora</a>
    <a class="btn-lg btn-outline-w" href="#funcionalidades">▶ Ver como funciona</a>
  </div>
  <div class="hero-proof">
    <div class="proof">👨‍👩‍👧 +2.400 famílias protegidas</div>
    <div class="proof">⭐ 4.9/5 de avaliação</div>
    <div class="proof">🔒 100% legal e seguro</div>
    <div class="proof">📱 Android e iOS</div>
  </div>
</div>

<!-- FEATURES -->
<div class="features" id="funcionalidades">
  <div class="sec-label">Funcionalidades</div>
  <div class="sec-title">Tudo que os pais precisam saber</div>
  <div class="sec-sub">Monitoramento completo, sem complicação.</div>
  <div class="feat-grid">
    <div class="feat"><div class="feat-ico">📍</div><h3>GPS em Tempo Real</h3><p>Veja onde seu filho está agora, histórico de locais e alertas automáticos quando sair de zonas seguras.</p><span class="feat-tag">Ao vivo</span></div>
    <div class="feat"><div class="feat-ico">💬</div><h3>Monitoramento de Conversas</h3><p>Detecta palavras suspeitas no WhatsApp, Instagram e redes sociais. Alertas imediatos por WhatsApp.</p><span class="feat-tag">IA detecta riscos</span></div>
    <div class="feat"><div class="feat-ico">📱</div><h3>Controle de Apps</h3><p>Bloqueie apps inadequados, defina horários de uso e veja quanto tempo passa em cada aplicativo.</p><span class="feat-tag">Bloqueio automático</span></div>
    <div class="feat"><div class="feat-ico">📸</div><h3>Screenshots Periódicos</h3><p>Capturas automáticas da tela enviadas para seu painel. Veja exatamente o que seu filho está vendo.</p><span class="feat-tag">A cada 5 min</span></div>
    <div class="feat"><div class="feat-ico">🎤</div><h3>Áudio Ambiente</h3><p>Grave o ambiente ao redor do celular remotamente. Saiba se seu filho está em situação de risco.</p><span class="feat-tag">Remoto</span></div>
    <div class="feat"><div class="feat-ico">🔔</div><h3>Alertas Inteligentes</h3><p>Notificações no seu WhatsApp quando detectar risco, contato desconhecido ou saída de zona segura.</p><span class="feat-tag">Tempo real</span></div>
  </div>
</div>

<!-- HOW -->
<div class="how">
  <div class="sec-label">Como funciona</div>
  <div class="sec-title">Pronto em 4 passos simples</div>
  <div class="steps">
    <div class="step"><div class="step-n">1</div><h4>Assine o plano</h4><p>Escolha o plano ideal para sua família</p></div>
    <div class="step"><div class="step-n">2</div><h4>Instale no celular</h4><p>Instale o app no celular do seu filho em 2 minutos</p></div>
    <div class="step"><div class="step-n">3</div><h4>Configure as regras</h4><p>Defina horários, zonas seguras e palavras monitoradas</p></div>
    <div class="step"><div class="step-n">4</div><h4>Fique tranquilo</h4><p>Receba alertas e monitore tudo pelo seu celular</p></div>
  </div>
</div>

<!-- PRICING -->
<div class="pricing" id="planos">
  <div class="sec-label">Planos</div>
  <div class="sec-title">Escolha a proteção ideal</div>
  <div class="sec-sub">Cancele quando quiser. 7 dias grátis para testar.</div>
  <div class="price-grid">
    <div class="price-card">
      <div class="price-name">Básico</div>
      <div class="price-val">R$49<span class="price-per">/mês</span></div>
      <div class="price-feats">
        <div class="pf">GPS em tempo real</div>
        <div class="pf">1 filho monitorado</div>
        <div class="pf">Bloqueio de apps</div>
        <div class="pf">Alertas por WhatsApp</div>
        <div class="pf no">Screenshots</div>
        <div class="pf no">Áudio ambiente</div>
      </div>
      <a class="btn-price sec" href="/assinar?plano=basico">Assinar Básico</a>
    </div>
    <div class="price-card pop">
      <div class="pop-tag">⭐ MAIS POPULAR</div>
      <div class="price-name">Família</div>
      <div class="price-val">R$79<span class="price-per">/mês</span></div>
      <div class="price-feats">
        <div class="pf">GPS em tempo real</div>
        <div class="pf">Até 3 filhos</div>
        <div class="pf">Bloqueio de apps</div>
        <div class="pf">Alertas por WhatsApp</div>
        <div class="pf">Screenshots automáticos</div>
        <div class="pf">Áudio ambiente</div>
      </div>
      <a class="btn-price primary" href="/assinar?plano=familia">Assinar Família</a>
    </div>
    <div class="price-card">
      <div class="price-name">Premium</div>
      <div class="price-val">R$119<span class="price-per">/mês</span></div>
      <div class="price-feats">
        <div class="pf">Tudo do Família</div>
        <div class="pf">Filhos ilimitados</div>
        <div class="pf">Relatório semanal PDF</div>
        <div class="pf">Suporte prioritário</div>
        <div class="pf">Câmera remota</div>
        <div class="pf">IA análise de risco</div>
      </div>
      <a class="btn-price sec" href="/assinar?plano=premium">Assinar Premium</a>
    </div>
  </div>
</div>

<!-- DEPOIMENTOS -->
<div class="tests">
  <div class="sec-label" style="color:#818cf8;">Depoimentos</div>
  <div class="sec-title">O que os pais dizem</div>
  <div class="sec-sub">Mais de 2.400 famílias protegidas em todo o Brasil</div>
  <div class="test-grid">
    <div class="test"><div class="stars">★★★★★</div><p>"Descobri que minha filha conversava com adulto desconhecido. O sistema me alertou antes que algo acontecesse. Salvou minha filha."</p><div class="test-auth"><div class="test-av" style="background:#6366f1;">M</div><div><div class="test-name">Márcia S.</div><div class="test-city">Brasília-DF</div></div></div></div>
    <div class="test"><div class="stars">★★★★★</div><p>"Meu filho ficava no celular até meia-noite. Com o bloqueio automático por horário, o problema foi resolvido no primeiro dia."</p><div class="test-auth"><div class="test-av" style="background:#10b981;">R</div><div><div class="test-name">Roberto L.</div><div class="test-city">São Paulo-SP</div></div></div></div>
    <div class="test"><div class="stars">★★★★★</div><p>"Instalei em 5 minutos. Agora sei em tempo real onde meus filhos estão. A paz de espírito não tem preço."</p><div class="test-auth"><div class="test-av" style="background:#f59e0b;">C</div><div><div class="test-name">Cláudia M.</div><div class="test-city">Goiânia-GO</div></div></div></div>
  </div>
</div>

<!-- FAQ -->
<div class="faq" id="faq">
  <div class="sec-label">Dúvidas</div>
  <div class="sec-title">Perguntas frequentes</div>
  <div class="faq-wrap">
    <div class="faq-item"><div class="faq-q" onclick="faq(this)"><span>É legal monitorar o celular do meu filho?</span><span id="a1">+</span></div><div class="faq-a">Sim! Totalmente legal para menores de 18 anos quando os pais são responsáveis pelo dispositivo. Amparado pelo ECA e Código Civil Brasileiro.</div></div>
    <div class="faq-item"><div class="faq-q" onclick="faq(this)"><span>Meu filho vai saber que está sendo monitorado?</span><span>+</span></div><div class="faq-a">O app funciona em modo discreto. Recomendamos conversar com seu filho sobre o monitoramento — crianças que sabem tendem a ser mais responsáveis online.</div></div>
    <div class="faq-item"><div class="faq-q" onclick="faq(this)"><span>Funciona em iPhone também?</span><span>+</span></div><div class="faq-a">Sim! Android e iOS. No iPhone algumas funcionalidades avançadas dependem das configurações de privacidade da Apple.</div></div>
    <div class="faq-item"><div class="faq-q" onclick="faq(this)"><span>Como cancelo minha assinatura?</span><span>+</span></div><div class="faq-a">Cancele a qualquer momento pelo painel de controle, sem multas. O acesso continua até o fim do período pago.</div></div>
    <div class="faq-item"><div class="faq-q" onclick="faq(this)"><span>Como instalo no celular do meu filho?</span><span>+</span></div><div class="faq-a">Após a assinatura você recebe um link por WhatsApp. Abra o link no celular do filho, instale o app e configure em menos de 5 minutos.</div></div>
  </div>
</div>

<!-- CTA FINAL -->
<div class="cta">
  <h2>Comece agora — 7 dias grátis</h2>
  <p>Sem cartão de crédito para testar. Cancele quando quiser.</p>
  <a class="btn-lg btn-green" href="/assinar?plano=familia">🛡️ Começar gratuitamente</a>
</div>

<footer>
  SPYNET Safe Kids © 2026 · Todos os direitos reservados · Brasília-DF<br>
  <a href="/admin" style="color:rgba(255,255,255,0.3);text-decoration:none;">Acesso administrativo</a>
</footer>
<script>
function faq(el){
  var a=el.nextElementSibling;
  var open=a.classList.contains('open');
  document.querySelectorAll('.faq-a').forEach(x=>x.classList.remove('open'));
  if(!open) a.classList.add('open');
}
</script>
</body>
</html>"""

# ============================================================
# ADMIN LOGIN HTML
# ============================================================
ADMIN_LOGIN_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>SPYNET Safe Kids — Admin</title>
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@700;800;900&family=Orbitron:wght@900&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:'Nunito',sans-serif;background:linear-gradient(135deg,#0f172a,#1e1b4b);min-height:100vh;display:flex;align-items:center;justify-content:center;}
.box{background:rgba(255,255,255,0.05);border:1px solid rgba(99,102,241,0.3);border-radius:16px;padding:40px 36px;width:100%;max-width:380px;backdrop-filter:blur(10px);}
.box::before{content:'';position:absolute;top:-1px;left:20%;right:20%;height:2px;background:linear-gradient(90deg,transparent,#6366f1,transparent);}
.logo{font-family:'Orbitron',monospace;font-size:14px;font-weight:900;letter-spacing:3px;color:#6366f1;text-align:center;margin-bottom:4px;}
.name{font-size:22px;font-weight:900;color:#fff;text-align:center;margin-bottom:4px;}
.tag{font-size:10px;color:rgba(255,255,255,0.4);text-align:center;letter-spacing:2px;margin-bottom:28px;}
.lbl{font-size:10px;font-weight:700;color:rgba(255,255,255,0.5);letter-spacing:2px;text-transform:uppercase;display:block;margin-bottom:6px;margin-top:16px;}
input{width:100%;background:rgba(0,0,0,0.3);border:1px solid rgba(99,102,241,0.3);border-radius:8px;color:#fff;padding:11px 14px;font-family:'Nunito',sans-serif;font-size:13px;outline:none;transition:border-color .2s;}
input:focus{border-color:#6366f1;}
.btn{width:100%;margin-top:24px;padding:12px;background:#6366f1;color:#fff;border:none;border-radius:8px;font-family:'Nunito',sans-serif;font-size:13px;font-weight:800;cursor:pointer;transition:all .2s;letter-spacing:1px;}
.btn:hover{background:#4f46e5;transform:translateY(-1px);}
.erro{background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);color:#ef4444;font-size:11px;padding:8px 12px;border-radius:6px;margin-top:12px;text-align:center;}
.back{display:block;text-align:center;margin-top:16px;font-size:11px;color:rgba(255,255,255,0.4);text-decoration:none;}
.back:hover{color:rgba(255,255,255,0.7);}
</style>
</head>
<body>
<div class="box" style="position:relative;">
  <div class="logo">SPYNET</div>
  <div class="name">Safe Kids</div>
  <div class="tag">PAINEL ADMINISTRATIVO</div>
  {% if erro %}<div class="erro">{{ erro }}</div>{% endif %}
  <form method="POST">
    <label class="lbl">Senha de Acesso</label>
    <input type="password" name="senha" placeholder="••••••••••" autofocus autocomplete="off">
    <button class="btn" type="submit">Entrar no Painel</button>
  </form>
  <a class="back" href="/">← Voltar para o site</a>
</div>
</body>
</html>"""

# ============================================================
# ADMIN PAINEL HTML
# ============================================================
ADMIN_PAINEL_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>SPYNET Safe Kids — Painel Admin</title>
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&family=Orbitron:wght@900&display=swap" rel="stylesheet">
<style>
:root{--bg:#f8faff;--surface:#fff;--accent:#6366f1;--green:#10b981;--warn:#f59e0b;--danger:#ef4444;--text:#0f172a;--muted:#64748b;--border:#e2e8f0;--dark:#0f172a;}
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:'Nunito',sans-serif;background:var(--bg);color:var(--text);height:100vh;display:flex;flex-direction:column;overflow:hidden;}
.topbar{background:var(--dark);padding:10px 20px;display:flex;align-items:center;gap:12px;flex-shrink:0;}
.tb-brand{font-family:'Orbitron',monospace;font-size:12px;font-weight:900;letter-spacing:2px;color:#6366f1;}
.tb-sub{font-size:9px;color:rgba(255,255,255,0.4);letter-spacing:1px;}
.tb-right{margin-left:auto;display:flex;align-items:center;gap:10px;}
.pill{display:flex;align-items:center;gap:6px;background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.3);color:#10b981;font-size:10px;font-weight:700;padding:4px 12px;border-radius:20px;}
.pdot{width:6px;height:6px;border-radius:50%;background:#22c55e;animation:blink 2s infinite;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}
.tb-link{font-size:11px;color:rgba(255,255,255,0.5);text-decoration:none;border:1px solid rgba(255,255,255,0.15);padding:4px 12px;border-radius:6px;}
.tb-link:hover{color:#fff;}
.main{display:flex;flex:1;overflow:hidden;}
.sidebar{width:185px;background:var(--dark);padding:12px 0;flex-shrink:0;overflow-y:auto;}
.nav-grp{font-size:9px;color:rgba(255,255,255,0.3);letter-spacing:2px;text-transform:uppercase;padding:10px 16px 4px;}
.nav-item{display:flex;align-items:center;gap:8px;padding:9px 16px;cursor:pointer;font-size:12px;font-weight:700;color:rgba(255,255,255,0.5);border-left:2px solid transparent;transition:all .2s;}
.nav-item:hover{color:#fff;background:rgba(255,255,255,0.04);}
.nav-item.active{color:#818cf8;border-left-color:#6366f1;background:rgba(99,102,241,0.1);}
.nav-badge{margin-left:auto;background:#ef4444;color:#fff;font-size:9px;padding:1px 6px;border-radius:10px;}
.content{flex:1;overflow-y:auto;padding:18px 20px;}
.sec{display:none;}.sec.active{display:block;}
.sec-title{font-size:18px;font-weight:900;color:var(--text);margin-bottom:16px;}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:16px;}
.stat{background:#fff;border:1px solid var(--border);border-radius:12px;padding:14px;text-align:center;position:relative;overflow:hidden;}
.stat::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;}
.stat.s1::before{background:linear-gradient(90deg,#6366f1,#818cf8);}
.stat.s2::before{background:linear-gradient(90deg,#10b981,#34d399);}
.stat.s3::before{background:linear-gradient(90deg,#f59e0b,#fbbf24);}
.stat.s4::before{background:linear-gradient(90deg,#ef4444,#f87171);}
.stat-val{font-size:26px;font-weight:900;margin-bottom:4px;}
.stat-lbl{font-size:10px;color:var(--muted);font-weight:600;}
.card{background:#fff;border:1px solid var(--border);border-radius:12px;padding:16px;margin-bottom:14px;}
.card-title{font-size:13px;font-weight:800;color:var(--text);margin-bottom:12px;display:flex;align-items:center;gap:8px;}
.btn{padding:8px 16px;border-radius:8px;font-size:11px;font-weight:800;cursor:pointer;border:none;font-family:'Nunito',sans-serif;transition:all .2s;}
.btn-p{background:#6366f1;color:#fff;}.btn-p:hover{background:#4f46e5;}
.btn-g{background:#10b981;color:#fff;}.btn-g:hover{background:#059669;}
.btn-r{background:#fef2f2;color:#ef4444;border:1px solid #fecaca;}.btn-r:hover{background:#fee2e2;}
.btn-sm{padding:4px 10px;font-size:10px;}
.cli-row{display:flex;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid var(--border);font-size:12px;}
.cli-row:last-child{border-bottom:none;}
.cli-av{width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:900;color:#fff;flex-shrink:0;}
.cli-name{font-weight:700;flex:1;}
.cli-plan{font-size:10px;color:var(--muted);}
.badge{font-size:9px;font-weight:700;padding:2px 8px;border-radius:10px;}
.b-a{background:#f0fdf4;color:#16a34a;border:1px solid #bbf7d0;}
.b-t{background:#eff6ff;color:#2563eb;border:1px solid #bfdbfe;}
.b-v{background:#fffbeb;color:#d97706;border:1px solid #fde68a;}
.b-c{background:#fef2f2;color:#dc2626;border:1px solid #fecaca;}
.cli-val{font-weight:800;color:#10b981;font-size:11px;min-width:60px;text-align:right;}
.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px;}
.fgrp{display:flex;flex-direction:column;gap:4px;}
.flbl{font-size:10px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:1px;}
input,select,textarea{background:var(--bg);border:1px solid var(--border);border-radius:8px;color:var(--text);padding:8px 12px;font-size:12px;font-family:'Nunito',sans-serif;font-weight:600;width:100%;outline:none;transition:border-color .2s;}
input:focus,select:focus,textarea:focus{border-color:#6366f1;}
.rev-bar{margin-bottom:10px;}
.rev-lbl{display:flex;justify-content:space-between;font-size:11px;font-weight:700;margin-bottom:4px;}
.rev-bg{height:8px;background:var(--border);border-radius:4px;overflow:hidden;}
.rev-fill{height:100%;border-radius:4px;background:linear-gradient(90deg,#6366f1,#818cf8);}
.msg-item{background:var(--bg);border-radius:8px;padding:10px 12px;margin-bottom:8px;border:1px solid var(--border);}
.msg-h{display:flex;justify-content:space-between;margin-bottom:4px;}
.msg-name{font-size:11px;font-weight:800;}
.msg-time{font-size:10px;color:var(--muted);}
.msg-text{font-size:11px;color:var(--muted);}
.msg-urg{border-left:3px solid #ef4444;}
.alert-row{display:flex;align-items:flex-start;gap:10px;padding:10px 12px;border-radius:10px;margin-bottom:8px;}
.ar-high{background:#fef2f2;border:1px solid #fecaca;}
.ar-med{background:#fffbeb;border:1px solid #fde68a;}
.ar-low{background:#f0fdf4;border:1px solid #bbf7d0;}
.ar-ico{font-size:18px;flex-shrink:0;}
.ar-text{font-size:12px;font-weight:700;}
.ar-sub{font-size:10px;color:var(--muted);margin-top:2px;}
.tabs-nav{display:flex;gap:4px;border-bottom:1px solid var(--border);margin-bottom:14px;}
.tnav{padding:7px 16px;font-size:11px;font-weight:700;color:var(--muted);cursor:pointer;border-bottom:2px solid transparent;margin-bottom:-1px;transition:all .2s;}
.tnav.active{color:#6366f1;border-bottom-color:#6366f1;}
.tpane{display:none;}.tpane.active{display:block;}
</style>
</head>
<body>
<div class="topbar">
  <div>
    <div class="tb-brand">SPYNET SAFE KIDS</div>
    <div class="tb-sub">PAINEL ADMINISTRATIVO</div>
  </div>
  <div class="tb-right">
    <div class="pill"><div class="pdot"></div> Sistema Online</div>
    <span style="font-size:10px;color:rgba(255,255,255,0.4);">{{ clientes|length }} clientes</span>
    <a href="/" class="tb-link">🌐 Ver site</a>
    <a href="/admin/logout" class="tb-link">Sair</a>
  </div>
</div>
<div class="main">
  <div class="sidebar">
    <div class="nav-grp">Principal</div>
    <div class="nav-item active" onclick="show('overview',this)">📊 Visão Geral</div>
    <div class="nav-item" onclick="show('clientes',this)">👥 Clientes</div>
    <div class="nav-item" onclick="show('novo',this)">➕ Novo Cliente</div>
    <div class="nav-grp" style="margin-top:6px;">Financeiro</div>
    <div class="nav-item" onclick="show('financeiro',this)">💰 Receita</div>
    <div class="nav-grp" style="margin-top:6px;">Suporte</div>
    <div class="nav-item" onclick="show('suporte',this)">💬 Suporte <span class="nav-badge">2</span></div>
    <div class="nav-item" onclick="show('config',this)">⚙️ Configurações</div>
  </div>
  <div class="content">

    <!-- OVERVIEW -->
    <div id="sec-overview" class="sec active">
      <div class="sec-title">Visão Geral</div>
      <div class="stats">
        <div class="stat s1"><div class="stat-val" style="color:#6366f1;">{{ clientes|selectattr('status','equalto','Ativo')|list|length }}</div><div class="stat-lbl">Clientes Ativos</div></div>
        <div class="stat s2"><div class="stat-val" style="color:#10b981;" id="receita">R$0</div><div class="stat-lbl">Receita/Mês</div></div>
        <div class="stat s3"><div class="stat-val" style="color:#f59e0b;">{{ clientes|selectattr('status','equalto','Trial')|list|length }}</div><div class="stat-lbl">Em Trial</div></div>
        <div class="stat s4"><div class="stat-val" style="color:#ef4444;">{{ clientes|selectattr('status','equalto','Vencendo')|list|length }}</div><div class="stat-lbl">Vencendo</div></div>
      </div>
      <div class="card">
        <div class="card-title">👥 Clientes Recentes</div>
        {% if clientes %}
          {% for c in clientes[:5] %}
          <div class="cli-row">
            <div class="cli-av" style="background:{% if loop.index0 == 0 %}#6366f1{% elif loop.index0 == 1 %}#10b981{% elif loop.index0 == 2 %}#f59e0b{% else %}#94a3b8{% endif %};">{{ c.nome[0] }}</div>
            <div style="flex:1;"><div class="cli-name">{{ c.nome }}</div><div class="cli-plan">{{ c.plano }} · {{ c.filhos }} filho(s)</div></div>
            <span class="badge b-{{ 'a' if c.status=='Ativo' else 't' if c.status=='Trial' else 'v' if c.status=='Vencendo' else 'c' }}">{{ c.status }}</span>
            <div class="cli-val">{{ 'R$49' if c.plano=='Básico' else 'R$79' if c.plano=='Família' else 'R$119' if c.plano=='Premium' else 'Trial' }}/mês</div>
          </div>
          {% endfor %}
        {% else %}
          <div style="text-align:center;padding:24px;color:var(--muted);font-size:12px;">Nenhum cliente cadastrado ainda.</div>
        {% endif %}
      </div>
    </div>

    <!-- CLIENTES -->
    <div id="sec-clientes" class="sec">
      <div class="sec-title">Gestão de Clientes</div>
      <div class="card">
        <div class="card-title">👥 Todos os Clientes ({{ clientes|length }})</div>
        {% if clientes %}
          {% for c in clientes %}
          <div class="cli-row">
            <div class="cli-av" style="background:#6366f1;">{{ c.nome[0] }}</div>
            <div style="flex:1;"><div class="cli-name">{{ c.nome }}</div><div class="cli-plan">{{ c.plano }} · {{ c.whatsapp }} · {{ c.data }}</div></div>
            <span class="badge b-{{ 'a' if c.status=='Ativo' else 't' if c.status=='Trial' else 'v' if c.status=='Vencendo' else 'c' }}">{{ c.status }}</span>
            <div class="cli-val">{{ 'R$49' if c.plano=='Básico' else 'R$79' if c.plano=='Família' else 'R$119' if c.plano=='Premium' else '—' }}</div>
            <form method="POST" action="/admin/cliente/deletar" style="margin:0;">
              <input type="hidden" name="idx" value="{{ loop.index0 }}">
              <button class="btn btn-r btn-sm" type="submit" onclick="return confirm('Remover cliente?')">✕</button>
            </form>
          </div>
          {% endfor %}
        {% else %}
          <div style="text-align:center;padding:24px;color:var(--muted);font-size:12px;">Nenhum cliente. <a href="#" onclick="show('novo',null)" style="color:#6366f1;">Cadastrar primeiro cliente</a></div>
        {% endif %}
      </div>
    </div>

    <!-- NOVO CLIENTE -->
    <div id="sec-novo" class="sec">
      <div class="sec-title">Cadastrar Novo Cliente</div>
      {% if msg %}<div style="background:#f0fdf4;border:1px solid #bbf7d0;color:#16a34a;padding:10px 14px;border-radius:8px;margin-bottom:12px;font-size:12px;font-weight:700;">{{ msg }}</div>{% endif %}
      <div class="card">
        <form method="POST" action="/admin/cliente/criar">
          <div class="form-grid">
            <div class="fgrp"><div class="flbl">Nome completo</div><input type="text" name="nome" placeholder="Nome do responsável" required></div>
            <div class="fgrp"><div class="flbl">WhatsApp</div><input type="text" name="whatsapp" placeholder="(61) 99999-9999" required></div>
            <div class="fgrp"><div class="flbl">E-mail</div><input type="text" name="email" placeholder="email@dominio.com"></div>
            <div class="fgrp"><div class="flbl">Plano</div>
              <select name="plano">
                <option value="Trial">Trial gratuito (7 dias)</option>
                <option value="Básico">Básico — R$49/mês</option>
                <option value="Família">Família — R$79/mês</option>
                <option value="Premium">Premium — R$119/mês</option>
              </select>
            </div>
            <div class="fgrp"><div class="flbl">Nº de filhos</div><input type="number" name="filhos" placeholder="1" min="1" max="10" value="1"></div>
            <div class="fgrp"><div class="flbl">Vencimento</div><input type="date" name="vencimento"></div>
          </div>
          <div class="fgrp" style="margin-bottom:12px;"><div class="flbl">Observações</div><textarea name="obs" rows="2" placeholder="Anotações sobre o cliente..."></textarea></div>
          <button class="btn btn-p" type="submit">✓ Cadastrar Cliente</button>
        </form>
      </div>
    </div>

    <!-- FINANCEIRO -->
    <div id="sec-financeiro" class="sec">
      <div class="sec-title">Financeiro</div>
      <div class="stats">
        <div class="stat s2"><div class="stat-val" style="color:#10b981;" id="f-mensal">R$0</div><div class="stat-lbl">Receita Mensal</div></div>
        <div class="stat s1"><div class="stat-val" style="color:#6366f1;" id="f-clientes">0</div><div class="stat-lbl">Clientes Pagantes</div></div>
        <div class="stat s3"><div class="stat-val" style="color:#f59e0b;" id="f-custo">R$0</div><div class="stat-lbl">Custo Estimado</div></div>
        <div class="stat s2"><div class="stat-val" style="color:#10b981;" id="f-lucro">R$0</div><div class="stat-lbl">Lucro Líquido</div></div>
      </div>
      <div class="card">
        <div class="card-title">📊 Margem por Plano</div>
        <div class="rev-bar"><div class="rev-lbl"><span>Básico (R$49) → custo R$15 → lucro R$34</span><span>69%</span></div><div class="rev-bg"><div class="rev-fill" style="width:69%;background:linear-gradient(90deg,#10b981,#34d399);"></div></div></div>
        <div class="rev-bar"><div class="rev-lbl"><span>Família (R$79) → custo R$22 → lucro R$57</span><span>72%</span></div><div class="rev-bg"><div class="rev-fill" style="width:72%;"></div></div></div>
        <div class="rev-bar"><div class="rev-lbl"><span>Premium (R$119) → custo R$35 → lucro R$84</span><span>71%</span></div><div class="rev-bg"><div class="rev-fill" style="width:71%;background:linear-gradient(90deg,#f59e0b,#fbbf24);"></div></div></div>
      </div>
    </div>

    <!-- SUPORTE -->
    <div id="sec-suporte" class="sec">
      <div class="sec-title">Central de Suporte</div>
      <div class="msg-item msg-urg"><div class="msg-h"><span class="msg-name">Márcia Silva</span><span class="msg-time">há 12 min</span></div><div class="msg-text">O app parou de mostrar a localização da minha filha. Como resolvo?</div></div>
      <div class="msg-item msg-urg"><div class="msg-h"><span class="msg-name">João Pereira</span><span class="msg-time">há 1h</span></div><div class="msg-text">Quero adicionar mais um filho no plano, como faço?</div></div>
      <div class="msg-item"><div class="msg-h"><span class="msg-name">Cláudia Mendes</span><span class="msg-time">há 3h</span></div><div class="msg-text">Quando vence minha assinatura? Quero renovar.</div></div>
      <div style="display:flex;gap:8px;margin-top:12px;">
        <input type="text" placeholder="Responder mensagem..." style="flex:1;">
        <button class="btn btn-p">Enviar</button>
      </div>
    </div>

    <!-- CONFIG -->
    <div id="sec-config" class="sec">
      <div class="sec-title">Configurações</div>
      <div class="card">
        <div class="card-title">🔧 Dados do Negócio</div>
        <div class="form-grid">
          <div class="fgrp"><div class="flbl">Nome da empresa</div><input type="text" value="SPYNET Safe Kids"></div>
          <div class="fgrp"><div class="flbl">WhatsApp comercial</div><input type="text" placeholder="(61) 99999-9999"></div>
          <div class="fgrp"><div class="flbl">E-mail de contato</div><input type="text" placeholder="contato@spynetsafekids.com.br"></div>
          <div class="fgrp"><div class="flbl">Chave PIX</div><input type="text" placeholder="cpf@email.com"></div>
        </div>
        <button class="btn btn-p" onclick="alert('Salvo!')">Salvar Configurações</button>
      </div>
      <div class="card">
        <div class="card-title">🔐 Alterar Senha Admin</div>
        <div class="form-grid">
          <div class="fgrp"><div class="flbl">Nova senha</div><input type="password" placeholder="Nova senha"></div>
          <div class="fgrp"><div class="flbl">Confirmar senha</div><input type="password" placeholder="Confirmar senha"></div>
        </div>
        <button class="btn btn-p" onclick="alert('Senha alterada!')">Alterar Senha</button>
      </div>
    </div>

  </div>
</div>
<script>
function show(id,el){
  document.querySelectorAll('.sec').forEach(s=>s.classList.remove('active'));
  document.getElementById('sec-'+id).classList.add('active');
  document.querySelectorAll('.nav-item').forEach(n=>n.classList.remove('active'));
  if(el) el.classList.add('active');
}
function calcReceita(){
  var clientes = {{ clientes | tojson }};
  var precos = {'Básico':49,'Família':79,'Premium':119};
  var total = 0; var pagantes = 0; var custo = 0;
  clientes.forEach(c=>{
    if(precos[c.plano]){
      total += precos[c.plano];
      pagantes++;
      custo += Math.round(precos[c.plano]*0.28);
    }
  });
  var lucro = total - custo;
  var el = document.getElementById('receita');
  if(el) el.textContent = 'R$'+total;
  var el2 = document.getElementById('f-mensal');
  if(el2) el2.textContent = 'R$'+total;
  var el3 = document.getElementById('f-clientes');
  if(el3) el3.textContent = pagantes;
  var el4 = document.getElementById('f-custo');
  if(el4) el4.textContent = 'R$'+custo;
  var el5 = document.getElementById('f-lucro');
  if(el5) el5.textContent = 'R$'+lucro;
}
calcReceita();
</script>
</body>
</html>"""

# ============================================================
# PÁGINA DE ASSINATURA
# ============================================================
ASSINAR_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Assinar — SPYNET Safe Kids</title>
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@700;800;900&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:'Nunito',sans-serif;background:#f8faff;display:flex;align-items:center;justify-content:center;min-height:100vh;}
.box{background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:36px;width:100%;max-width:480px;}
h2{font-size:22px;font-weight:900;color:#0f172a;margin-bottom:6px;}
.sub{font-size:13px;color:#64748b;margin-bottom:24px;}
.plano-badge{background:#eff6ff;border:1px solid #bfdbfe;color:#2563eb;font-size:12px;font-weight:800;padding:6px 14px;border-radius:8px;display:inline-block;margin-bottom:20px;}
.fgrp{margin-bottom:12px;}
.flbl{font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:1px;display:block;margin-bottom:5px;}
input,select{width:100%;background:#f8faff;border:1px solid #e2e8f0;border-radius:8px;color:#0f172a;padding:10px 14px;font-size:13px;font-family:'Nunito',sans-serif;font-weight:600;outline:none;}
input:focus{border-color:#6366f1;}
.btn{width:100%;margin-top:16px;padding:13px;background:#6366f1;color:#fff;border:none;border-radius:10px;font-size:14px;font-weight:800;cursor:pointer;font-family:'Nunito',sans-serif;}
.btn:hover{background:#4f46e5;}
.back{display:block;text-align:center;margin-top:14px;font-size:12px;color:#64748b;text-decoration:none;}
.back:hover{color:#6366f1;}
{% if sucesso %}
.sucesso{background:#f0fdf4;border:1px solid #bbf7d0;color:#16a34a;padding:14px;border-radius:8px;margin-bottom:16px;font-size:13px;font-weight:700;}
{% endif %}
</style>
</head>
<body>
<div class="box">
  <h2>Começar agora 🛡️</h2>
  <div class="sub">Preencha seus dados para ativar o plano.</div>
  {% if sucesso %}
  <div class="sucesso">✅ Cadastro realizado! Entraremos em contato pelo WhatsApp em até 1h para configurar o app.</div>
  {% endif %}
  <div class="plano-badge">Plano {{ plano | capitalize }} selecionado</div>
  <form method="POST">
    <input type="hidden" name="plano" value="{{ plano }}">
    <div class="fgrp"><label class="flbl">Nome completo</label><input type="text" name="nome" placeholder="Seu nome" required></div>
    <div class="fgrp"><label class="flbl">WhatsApp</label><input type="text" name="whatsapp" placeholder="(61) 99999-9999" required></div>
    <div class="fgrp"><label class="flbl">E-mail</label><input type="email" name="email" placeholder="email@dominio.com"></div>
    <div class="fgrp"><label class="flbl">Quantos filhos?</label><input type="number" name="filhos" value="1" min="1" max="10"></div>
    <button class="btn" type="submit">✓ Confirmar cadastro</button>
  </form>
  <a class="back" href="/">← Voltar para o site</a>
</div>
</body>
</html>"""

# ============================================================
# ROTAS
# ============================================================

@app.route('/')
def landing():
    return render_template_string(LANDING_HTML)

@app.route('/assinar', methods=['GET','POST'])
def assinar():
    plano = request.args.get('plano', 'familia')
    sucesso = False
    if request.method == 'POST':
        clientes = load_clientes()
        clientes.append({
            'nome': request.form.get('nome',''),
            'whatsapp': request.form.get('whatsapp',''),
            'email': request.form.get('email',''),
            'plano': request.form.get('plano','Trial').capitalize(),
            'filhos': request.form.get('filhos','1'),
            'status': 'Trial',
            'obs': '',
            'vencimento': '',
            'data': now_br()
        })
        save_clientes(clientes)
        sucesso = True
        plano = request.form.get('plano', plano)
    return render_template_string(ASSINAR_HTML, plano=plano, sucesso=sucesso)

@app.route('/admin', methods=['GET','POST'])
def admin_login():
    erro = ''
    if request.method == 'POST':
        if request.form.get('senha') == ADMIN_SENHA:
            session['admin'] = True
            return redirect(url_for('admin_painel'))
        erro = 'Senha incorreta!'
    return render_template_string(ADMIN_LOGIN_HTML, erro=erro)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('landing'))

@app.route('/admin/painel')
@login_required
def admin_painel():
    clientes = list(reversed(load_clientes()))
    msg = request.args.get('msg','')
    return render_template_string(ADMIN_PAINEL_HTML, clientes=clientes, msg=msg)

@app.route('/admin/cliente/criar', methods=['POST'])
@login_required
def cliente_criar():
    clientes = load_clientes()
    clientes.append({
        'nome': request.form.get('nome','').strip(),
        'whatsapp': request.form.get('whatsapp','').strip(),
        'email': request.form.get('email','').strip(),
        'plano': request.form.get('plano','Trial'),
        'filhos': request.form.get('filhos','1'),
        'status': 'Trial' if request.form.get('plano') == 'Trial' else 'Ativo',
        'obs': request.form.get('obs','').strip(),
        'vencimento': request.form.get('vencimento',''),
        'data': now_br()
    })
    save_clientes(clientes)
    return redirect(url_for('admin_painel') + '?msg=Cliente cadastrado com sucesso!')

@app.route('/admin/cliente/deletar', methods=['POST'])
@login_required
def cliente_deletar():
    clientes = load_clientes()
    idx = int(request.form.get('idx', -1))
    # idx vem da lista reversed, precisa converter
    real_idx = len(clientes) - 1 - idx
    if 0 <= real_idx < len(clientes):
        clientes.pop(real_idx)
        save_clientes(clientes)
    return redirect(url_for('admin_painel'))

if __name__ == '__main__':
    print("="*50)
    print(" SPYNET SAFE KIDS")
    print(" Site: http://localhost:5000")
    print(" Admin: http://localhost:5000/admin")
    print(" Senha admin: safekids2026")
    print("="*50)
    app.run(debug=True, port=5000)
