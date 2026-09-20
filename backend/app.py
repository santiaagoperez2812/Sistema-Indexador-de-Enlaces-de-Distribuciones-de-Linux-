from flask import Flask, jsonify, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
# Configuración de SQLite (creará un archivo distros.db automáticamente)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///distros.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELOS RELACIONALES ---

class Distro(db.Model):
    __tablename__ = 'distros'
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    family = db.Column(db.String(50))
    description = db.Column(db.Text)
    logo = db.Column(db.String(255))
    
    # Relaciones con las otras tablas
    links = db.relationship('Link', backref='distro', uselist=False, cascade="all, delete-orphan")
    metadata_info = db.relationship('DistroMetadata', backref='distro', uselist=False, cascade="all, delete-orphan")

class Link(db.Model):
    __tablename__ = 'links'
    id = db.Column(db.Integer, primary_key=True)
    distro_id = db.Column(db.String(50), db.ForeignKey('distros.id'), nullable=False)
    website = db.Column(db.String(255))
    downloads = db.Column(db.String(255))
    documentation = db.Column(db.String(255))
    signatures_url = db.Column(db.String(255))

class DistroMetadata(db.Model):
    __tablename__ = 'metadata'
    id = db.Column(db.Integer, primary_key=True)
    distro_id = db.Column(db.String(50), db.ForeignKey('distros.id'), nullable=False)
    package_manager = db.Column(db.String(50))
    # SQLite no tiene tipo de dato nativo para arrays, guardaremos las listas como texto separado por comas
    architectures = db.Column(db.Text) 
    tags = db.Column(db.Text)

# --- RUTAS DE LA API (Endpoints) ---

@app.route('/api/distros', methods=['GET'])
def get_all_distros():
    distros = Distro.query.all()
    result = []
    for d in distros:
        result.append({
            "id": d.id,
            "name": d.name,
            "family": d.family,
            "logo": d.logo,
            "package_manager": d.metadata_info.package_manager if d.metadata_info else None
        })
    return jsonify(result)

@app.route('/api/distros/<distro_id>', methods=['GET'])
def get_distro(distro_id):
    # Buscar la distribución en la base de datos por su ID
    d = Distro.query.get(distro_id)
    if not d:
        return jsonify({"error": "Distribución no encontrada"}), 404
    
    # Reconstruir la estructura exacta que esperaba Astro
    return jsonify({
        "id": d.id,
        "name": d.name,
        "family": d.family,
        "description": d.description,
        "logo": d.logo,
        "links": {
            "website": d.links.website if d.links else None,
            "downloads": d.links.downloads if d.links else None,
            "documentation": d.links.documentation if d.links else None,
        },
        "metadata": {
            "package_manager": d.metadata_info.package_manager if d.metadata_info else None,
            "architectures": d.metadata_info.architectures.split(',') if d.metadata_info and d.metadata_info.architectures else [],
            "tags": d.metadata_info.tags.split(',') if d.metadata_info and d.metadata_info.tags else []
        },
        "verification": {
            "signatures_url": d.links.signatures_url if d.links else None
        }
    })

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if request.method == 'POST':
        # Capturar los datos del formulario HTML
        nuevo_id = request.form.get('id')
        
        # Crear la nueva distribución en la base de datos
        nueva_distro = Distro(
            id=nuevo_id,
            name=request.form.get('name'),
            family=request.form.get('family'),
            description=request.form.get('description'),
            logo=request.form.get('logo')
        )
        db.session.add(nueva_distro)
        
        # Crear los enlaces asociados
        nuevo_link = Link(
            distro=nueva_distro, 
            website=request.form.get('website')
        )
        db.session.add(nuevo_link)
        
        # Crear metadatos vacíos por defecto
        nuevo_meta = DistroMetadata(distro=nueva_distro)
        db.session.add(nuevo_meta)
        
        # Guardar cambios
        db.session.commit()
        
        # Recargar la página para ver el nuevo registro
        return redirect(url_for('admin_panel'))
    
    # Si es método GET, solo mostramos la página con la lista
    distros_db = Distro.query.all()
    return render_template('admin.html', distros=distros_db)

if __name__ == '__main__':
    app.run(debug=True, port=5000)