"""Gera o hash bcrypt de uma senha para colocar em ADMIN_PASSWORD_HASH (.env).

Uso: python scripts/hash_password.py
(pede a senha de forma interativa, sem ecoar no terminal)
"""

import getpass

import bcrypt


def main() -> None:
    password = getpass.getpass("Senha do admin: ")
    confirm = getpass.getpass("Confirme a senha: ")
    if password != confirm:
        raise SystemExit("As senhas não coincidem.")

    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    print(password_hash.decode("utf-8"))


if __name__ == "__main__":
    main()
