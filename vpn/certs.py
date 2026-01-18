import os
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import datetime

class CertificateManager:
    def __init__(self, ca_cert_file='certs/ca.crt', ca_key_file='certs/ca.key'):
        self.ca_cert_file = ca_cert_file
        self.ca_key_file = ca_key_file

    def load_ca(self):
        """Charge le CA existant s'il existe, sinon retourne None"""
        if os.path.exists(self.ca_cert_file) and os.path.exists(self.ca_key_file):
            with open(self.ca_key_file, "rb") as f:
                ca_key = serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())
            with open(self.ca_cert_file, "rb") as f:
                ca_cert = x509.load_pem_x509_certificate(f.read(), backend=default_backend())
            return ca_key, ca_cert
        return None, None

    def generate_ca_cert(self):
        """Génère le certificat et la clé de l'Autorité de Certification (CA) si elle n'existe pas"""
        ca_key, ca_cert = self.load_ca()
        if ca_key and ca_cert:
            return ca_key, ca_cert
        
        # Créer le dossier certs s'il n'existe pas
        os.makedirs(os.path.dirname(self.ca_cert_file), exist_ok=True)
        
        # Clé privée CA
        ca_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Certificat CA auto-signé
        ca_cert = x509.CertificateBuilder().subject_name(
            x509.Name([
                x509.NameAttribute(NameOID.COMMON_NAME, "PersonalVPN CA"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "PersonalVPN"),
            ])
        ).issuer_name(
            x509.Name([
                x509.NameAttribute(NameOID.COMMON_NAME, "PersonalVPN CA"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "PersonalVPN"),
            ])
        ).public_key(ca_key.public_key()).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=365*10)  # 10 ans
        ).add_extension(
            x509.BasicConstraints(ca=True, path_length=None), critical=True
        ).sign(ca_key, hashes.SHA256(), default_backend())
        
        # Sauvegarde
        with open(self.ca_key_file, "wb") as f:
            f.write(ca_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        with open(self.ca_cert_file, "wb") as f:
            f.write(ca_cert.public_bytes(serialization.Encoding.PEM))
        
        return ca_key, ca_cert

    def generate_server_cert(self, ca_key, ca_cert, server_cert_file='certs/server.crt', server_key_file='certs/server.key'):
        """Génère le certificat et la clé pour le serveur"""
        # Créer le dossier certs s'il n'existe pas
        os.makedirs(os.path.dirname(server_cert_file), exist_ok=True)
        
        # Clé privée serveur
        server_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Certificat serveur signé par la CA
        server_cert = x509.CertificateBuilder().subject_name(
            x509.Name([
                x509.NameAttribute(NameOID.COMMON_NAME, "vpn-server"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "PersonalVPN"),
            ])
        ).issuer_name(ca_cert.subject).public_key(
            server_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=365)
        ).add_extension(
            x509.AuthorityInformationAccess([
                x509.AccessDescription(
                    x509.AuthorityInformationAccessOID.CA_ISSUERS,
                    x509.UniformResourceIdentifier("http://localhost/ca.crt")
                )
            ]), critical=False
        ).sign(ca_key, hashes.SHA256(), default_backend())
        
        # Sauvegarde
        with open(server_key_file, "wb") as f:
            f.write(server_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        with open(server_cert_file, "wb") as f:
            f.write(server_cert.public_bytes(serialization.Encoding.PEM))
        
        return server_cert

    def generate_user_cert(self, username, ca_key, ca_cert):
        """Génère le certificat et la clé pour un utilisateur"""
        # Clé privée utilisateur
        user_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Certificat utilisateur signé par la CA
        user_cert = x509.CertificateBuilder().subject_name(
            x509.Name([
                x509.NameAttribute(NameOID.COMMON_NAME, username),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "PersonalVPN Users"),
            ])
        ).issuer_name(ca_cert.subject).public_key(
            user_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=365)
        ).add_extension(
            x509.AuthorityInformationAccess([
                x509.AccessDescription(
                    x509.AuthorityInformationAccessOID.CA_ISSUERS,
                    x509.UniformResourceIdentifier("http://localhost/ca.crt")
                )
            ]), critical=False
        ).sign(ca_key, hashes.SHA256(), default_backend())
        
        # Créer le dossier utilisateur
        user_folder = f"users/{username}"
        os.makedirs(user_folder, exist_ok=True)
        
        # Sauvegarde
        with open(f"{user_folder}/{username}.key", "wb") as f:
            f.write(user_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        with open(f"{user_folder}/{username}.crt", "wb") as f:
            f.write(user_cert.public_bytes(serialization.Encoding.PEM))
        
        # Copier le cert CA pour le client
        with open(f"{user_folder}/ca.crt", "wb") as f:
            f.write(ca_cert.public_bytes(serialization.Encoding.PEM))
        
        return user_cert