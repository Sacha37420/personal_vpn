from flask import Flask, request, jsonify, render_template_string, redirect
from .user_manager import UserManager
from .certs import CertificateManager
import threading
import os
import shutil

class AdminInterface:
    def __init__(self, port=80, user_manager=None, cert_manager=None):
        self.port = port
        self.user_manager = user_manager or UserManager()
        self.cert_manager = cert_manager or CertificateManager()
        self.app = Flask(__name__)
        self.app.config['UPLOAD_FOLDER'] = 'uploads'
        os.makedirs(self.app.config['UPLOAD_FOLDER'], exist_ok=True)
        self.setup_routes()

    def setup_routes(self):
        @self.app.route('/')
        def index():
            from flask import request
            users = []
            for username in self.user_manager.list_users():
                user_info = self.user_manager.get_user(username)
                users.append({
                    'name': username,
                    'folder': user_info['folder'],
                    'cert_file': user_info['cert_file'],
                    'key_file': user_info['key_file']
                })
            host = request.host
            html = """
            <html>
            <head>
                <title>Personal VPN Admin</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
                    .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                    h1 { color: #333; text-align: center; }
                    h2 { color: #555; border-bottom: 2px solid #ddd; padding-bottom: 5px; }
                    ul { list-style-type: none; padding: 0; }
                    li { background: #f9f9f9; margin: 10px 0; padding: 15px; border-radius: 5px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); }
                    .user-info { margin-top: 10px; }
                    .user-info strong { color: #007bff; }
                    form { background: #f9f9f9; padding: 20px; border-radius: 5px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); margin: 20px 0; }
                    input[type="text"], input[type="file"] { padding: 8px; margin: 5px 0; border: 1px solid #ddd; border-radius: 3px; width: 100%; box-sizing: border-box; }
                    button { background: #007bff; color: white; padding: 10px 15px; border: none; border-radius: 3px; cursor: pointer; }
                    button:hover { background: #0056b3; }
                    .download-link { color: #28a745; text-decoration: none; }
                    .download-link:hover { text-decoration: underline; }
                    .connection-info { background: #e9ecef; padding: 15px; border-radius: 5px; margin: 20px 0; }
                    .code { background: #f8f9fa; padding: 10px; border-radius: 3px; font-family: monospace; margin: 5px 0; word-wrap: break-word; }
                </style>
            </head>
            <body>
                <div class="container">
                <h1>Personal VPN Administration</h1>
                
                <div class="connection-info">
                    <h2>Connexion Client</h2>
                    <p><strong>Hôte :</strong> {{ host }}</p>
                    <p><strong>Port VPN :</strong> 1194</p>
                    <p><strong>Instructions :</strong></p>
                    <div class="code">python client.py &lt;username&gt; --host {{ host }}</div>
                    <p>Exemples :</p>
                    <div class="code">python client.py root --host {{ host }}</div>
                    <div class="code">python client.py invite --host {{ host }}</div>
                    
                    <h3>Configuration des certificats</h3>
                    <p>Les certificats sont générés automatiquement lors de la première connexion. Si vous voulez les configurer manuellement :</p>
                    <ol>
                        <li>Téléchargez le certificat et la clé de l'utilisateur depuis la liste ci-dessus</li>
                        <li>Créez un dossier <code>users/&lt;username&gt;</code> côté client</li>
                        <li>Placez les fichiers :
                            <ul>
                                <li><code>&lt;username&gt;.crt</code> : Certificat client</li>
                                <li><code>&lt;username&gt;.key</code> : Clé privée client</li>
                                <li><code>ca.crt</code> : Certificat de l'autorité (téléchargeable <a href="/download/ca">ici</a>)</li>
                            </ul>
                        </li>
                        <li>Lancez le client : <code>python client.py &lt;username&gt;</code></li>
                    </ol>
                </div>
                
                <h2>Utilisateurs existants</h2>
                <ul>
                {% for user in users %}
                    <li>
                        <strong>{{ user.name }}</strong>
                        <div class="user-info">
                            <p><strong>Dossier:</strong> {{ user.folder }}</p>
                            <p><strong>Certificat:</strong> {{ user.cert_file }} 
                            <a class="download-link" href="/download/{{ user.name }}/cert">Télécharger</a></p>
                            <p><strong>Clé:</strong> {{ user.key_file }} 
                            <a class="download-link" href="/download/{{ user.name }}/key">Télécharger</a></p>
                            <form method="POST" action="/delete_user/{{ user.name }}" style="display:inline;">
                                <button type="submit" style="background:#dc3545; color:white; border:none; padding:5px 10px; border-radius:3px; cursor:pointer;" onclick="return confirm('Êtes-vous sûr de vouloir supprimer cet utilisateur ?')">Supprimer</button>
                            </form>
                        </div>
                    </li>
                {% endfor %}
                </ul>
                <h2>Créer un nouvel utilisateur</h2>
                <form method="POST" action="/create_user">
                    <label>Nom d'utilisateur: <input type="text" name="username" required></label><br>
                    <button type="submit">Créer</button>
                </form>
                <h2>Déposer des clés pour un utilisateur existant</h2>
                <form method="POST" action="/upload_keys" enctype="multipart/form-data">
                    <label>Nom d'utilisateur: <input type="text" name="username" required></label><br>
                    <label>Certificat (.crt): <input type="file" name="cert" accept=".crt" required></label><br>
                    <label>Clé (.key): <input type="file" name="key" accept=".key" required></label><br>
                    <button type="submit">Déposer</button>
                </form>
                </div>
            </body>
            </html>
            """
            return render_template_string(html, users=users, host=host)

        @self.app.route('/create_user', methods=['POST'])
        def create_user():
            username = request.form.get('username')
            if not username:
                return "Nom d'utilisateur requis", 400
            
            if self.user_manager.get_user(username):
                return "Utilisateur existe déjà", 400
            
            try:
                # Générer les certificats pour le nouvel utilisateur
                ca_key, ca_cert = self.cert_manager.generate_ca_cert()  # Recharger ou utiliser existant
                # Note: En production, charger le CA existant au lieu de régénérer
                self.cert_manager.generate_user_cert(username, ca_key, ca_cert)
                
                # Ajouter à la liste des utilisateurs
                folder = f"users/{username}"
                cert_file = f"{folder}/{username}.crt"
                key_file = f"{folder}/{username}.key"
                self.user_manager.add_user(username, folder, cert_file, key_file)
                
                return redirect('/')
            except Exception as e:
                return f"Erreur: {str(e)}", 500

        @self.app.route('/upload_keys', methods=['POST'])
        def upload_keys():
            username = request.form.get('username')
            cert_file = request.files.get('cert')
            key_file = request.files.get('key')
            
            if not username or not cert_file or not key_file:
                return "Tous les champs sont requis", 400
            
            if not self.user_manager.get_user(username):
                return "Utilisateur non trouvé", 404
            
            try:
                user_info = self.user_manager.get_user(username)
                folder = user_info['folder']
                
                # Sauvegarder les fichiers
                cert_path = os.path.join(folder, f"{username}.crt")
                key_path = os.path.join(folder, f"{username}.key")
                
                cert_file.save(cert_path)
                key_file.save(key_path)
                
                return redirect('/')
            except Exception as e:
                return f"Erreur: {str(e)}", 500

        @self.app.route('/delete_user/<username>', methods=['POST'])
        def delete_user(username):
            if not self.user_manager.get_user(username):
                return "Utilisateur non trouvé", 404
            
            try:
                user_info = self.user_manager.get_user(username)
                folder = user_info['folder']
                
                # Supprimer les fichiers
                if os.path.exists(folder):
                    shutil.rmtree(folder)
                
                # Supprimer de la liste
                self.user_manager.users.pop(username, None)
                self.user_manager.save_users()
                
                return redirect('/')
            except Exception as e:
                return f"Erreur: {str(e)}", 500

        @self.app.route('/download/<username>/<file_type>')
        def download_file(username, file_type):
            user_info = self.user_manager.get_user(username)
            if not user_info:
                return jsonify({'error': 'Utilisateur non trouvé'}), 404
            
            if file_type == 'cert':
                file_path = user_info['cert_file']
            elif file_type == 'key':
                file_path = user_info['key_file']
            else:
                return jsonify({'error': 'Type de fichier invalide'}), 400
            
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                return f"<pre>{content}</pre>"
            return jsonify({'error': 'Fichier non trouvé'}), 404

        @self.app.route('/download/ca')
        def download_ca():
            if os.path.exists('certs/ca.crt'):
                with open('certs/ca.crt', 'r') as f:
                    content = f.read()
                return f"<pre>{content}</pre>"
            return "CA non trouvé", 404

    def run(self):
        print(f"Admin interface running on port {self.port}")
        self.app.run(host='0.0.0.0', port=self.port, debug=False)