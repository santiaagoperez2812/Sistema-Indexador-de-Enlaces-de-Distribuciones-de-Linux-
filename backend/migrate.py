import os
import yaml
from app import app, db, Distro, Link, DistroMetadata

# Ruta a tu carpeta actual de datos YAML
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))

def run_migration():
    with app.app_context():
        # 1. Crear todas las tablas en la base de datos
        db.create_all()
        
        # 2. Limpiar datos viejos por si ejecutas el script varias veces
        db.session.query(Distro).delete()
        db.session.commit()

        print("Iniciando migración de YAML a SQL...")

        # 3. Leer cada archivo YAML e insertarlo en las tablas
        for filename in os.listdir(DATA_DIR):
            if filename.endswith('.yaml'):
                filepath = os.path.join(DATA_DIR, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    
                    # Insertar Distribución Principal
                    distro = Distro(
                        id=data.get('id'),
                        name=data.get('name'),
                        family=data.get('family'),
                        description=data.get('description'),
                        logo=data.get('logo')
                    )
                    db.session.add(distro)
                    
                    # Insertar Enlaces
                    links_data = data.get('links', {})
                    verif_data = data.get('verification', {})
                    link = Link(
                        distro=distro,
                        website=links_data.get('website'),
                        downloads=links_data.get('downloads'),
                        documentation=links_data.get('documentation'),
                        signatures_url=verif_data.get('signatures_url')
                    )
                    db.session.add(link)
                    
                    # Insertar Metadatos (convirtiendo arrays a strings)
                    meta_data = data.get('metadata', {})
                    distro_meta = DistroMetadata(
                        distro=distro,
                        package_manager=meta_data.get('package_manager'),
                        architectures=",".join(meta_data.get('architectures', [])),
                        tags=",".join(meta_data.get('tags', []))
                    )
                    db.session.add(distro_meta)
                    
                    print(f" -> Migrado: {data.get('name')}")
        
        # 4. Guardar todos los cambios
        db.session.commit()
        print("\n¡Migración completada exitosamente! Base de datos 'distros.db' creada.")

if __name__ == '__main__':
    run_migration()