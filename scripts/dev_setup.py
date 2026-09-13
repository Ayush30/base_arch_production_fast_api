"""Create local configuration and signing keys without overwriting existing files."""

import shutil
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def main() -> None:
    if not Path(".env").exists():
        shutil.copyfile(".env.example", ".env")
    keys = Path("keys")
    keys.mkdir(exist_ok=True)
    private_path, public_path = keys / "private.pem", keys / "public.pem"
    if private_path.exists() != public_path.exists():
        raise SystemExit("Incomplete key pair: restore the missing key before continuing")
    if not private_path.exists():
        key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
        private_path.write_bytes(
            key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )
        )
        private_path.chmod(0o600)
        public_path.write_bytes(
            key.public_key().public_bytes(
                serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
            )
        )
    print("Local .env and RSA key pair are ready.")


if __name__ == "__main__":
    main()
