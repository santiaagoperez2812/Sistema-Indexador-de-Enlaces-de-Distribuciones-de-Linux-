import requests
from app import app, db, Link

def check_url(url, link_type):
    if not url:
        return
    try:
        # Usamos HEAD en lugar de GET para no descargar toda la web/ISO, solo leemos los encabezados de red
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.head(url, timeout=7, allow_redirects=True, headers=headers)
        
        if response.status_code < 400:
            print(f"  [OK] {link_type}: {url} (HTTP {response.status_code})")
        else:
            print(f"  [ALERTA] {link_type}: {url} devolvió error HTTP {response.status_code}")
            
    except requests.exceptions.Timeout:
        print(f"  [CAÍDO] {link_type}: {url} (Tiempo de espera agotado)")
    except requests.exceptions.RequestException as e:
        print(f"  [ERROR RED] {link_type}: {url} ({type(e).__name__})")

def run_audit():
    print("Iniciando auditoría de red (Health Check) de enlaces...")
    print("-" * 50)
    
    with app.app_context():
        # Traemos todos los enlaces de la base de datos
        links = Link.query.all()
        
        for link in links:
            print(f"\nAuditando: {link.distro.name.upper()}")
            check_url(link.website, "Sitio Web")
            check_url(link.downloads, "Descarga ISO")
            
    print("-" * 50)
    print("Auditoría finalizada.")

if __name__ == '__main__':
    run_audit()