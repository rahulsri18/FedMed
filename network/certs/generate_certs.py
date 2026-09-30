"""network/certs/generate_certs.py - mTLS Certificate Generator for Cross-Silo FL.

Owner: M4 (Network & API Lead)
Generates:
1. Root Certificate Authority (CA): ca.key, ca.crt
2. Server Certificate: server.key, server.crt (with SANs for localhost, 127.0.0.1, fedmed-server)
3. Hospital Client Certificates: client-node-1, client-node-2, client-node-3
"""

import datetime
import ipaddress
from pathlib import Path

try:
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


def generate_private_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def save_key(key, path: Path):
    path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )


def save_cert(cert, path: Path):
    path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))


def generate_mtls_certificates(output_dir: str = "network/certs"):
    """Generate complete set of CA, server, and client certificates."""
    if not CRYPTO_AVAILABLE:
        print("[mTLS] 'cryptography' library not installed in local environment.")
        print("[mTLS] Writing mock placeholder certs for testing.")
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        (out_path / "ca.crt").write_text("-----BEGIN CERTIFICATE-----\nMOCK_CA\n-----END CERTIFICATE-----")
        (out_path / "server.crt").write_text("-----BEGIN CERTIFICATE-----\nMOCK_SERVER\n-----END CERTIFICATE-----")
        return

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.now(datetime.timezone.utc)
    one_year = datetime.timedelta(days=365)

    print(f"[mTLS] Generating development certificates in: {out_path.resolve()}")

    # 1. Generate Root CA
    ca_key = generate_private_key()
    save_key(ca_key, out_path / "ca.key")

    ca_name = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "FedMed FL Consortium"),
        x509.NameAttribute(NameOID.COMMON_NAME, "FedMed Root CA"),
    ])
    ca_cert = (
        x509.CertificateBuilder()
        .subject_name(ca_name)
        .issuer_name(ca_name)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + one_year * 5)
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=False,
                key_cert_sign=True,
                crl_sign=True,
                content_commitment=False,
                data_encipherment=False,
                key_agreement=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .sign(ca_key, hashes.SHA256())
    )
    save_cert(ca_cert, out_path / "ca.crt")
    print("  [OK] Generated Root CA: ca.crt & ca.key")

    # 2. Generate Server Certificate with SANs
    server_key = generate_private_key()
    save_key(server_key, out_path / "server.key")

    server_name = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "FedMed FL Consortium"),
        x509.NameAttribute(NameOID.COMMON_NAME, "fedmed-server"),
    ])
    server_cert = (
        x509.CertificateBuilder()
        .subject_name(server_name)
        .issuer_name(ca_name)
        .public_key(server_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + one_year)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.DNSName("fedmed-server"),
                x509.DNSName("server"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            ]),
            critical=False,
        )
        .sign(ca_key, hashes.SHA256())
    )
    save_cert(server_cert, out_path / "server.crt")
    print("  [OK] Generated Server Cert: server.crt & server.key (with SANs)")

    # 3. Generate Client Certificates for 3 Hospital Nodes
    for node_id in [1, 2, 3]:
        client_key = generate_private_key()
        save_key(client_key, out_path / f"client-node-{node_id}.key")

        client_name = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "FedMed Hospital Network"),
            x509.NameAttribute(NameOID.COMMON_NAME, f"hospital-node-{node_id}"),
        ])
        client_cert = (
            x509.CertificateBuilder()
            .subject_name(client_name)
            .issuer_name(ca_name)
            .public_key(client_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now)
            .not_valid_after(now + one_year)
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .sign(ca_key, hashes.SHA256())
        )
        save_cert(client_cert, out_path / f"client-node-{node_id}.crt")
        print(f"  [OK] Generated Client Cert: client-node-{node_id}.crt & key")

    print("[mTLS] Certificate generation complete.")


if __name__ == "__main__":
    generate_mtls_certificates()
