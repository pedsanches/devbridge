#!/usr/bin/env python3
"""
Script de demonstração do Debug UX.
Simula requisições à API para demonstrar o tratamento de erros padronizado e tracing.
"""

import sys
import json
import uuid

# Adicionar diretório pai ao path para importar app
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def print_header(title: str):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def print_response(response, description: str):
    print(f"\n🔹 {description}")
    print(f"Status: {response.status_code}")
    print("Headers:")
    for k, v in response.headers.items():
        if k in ["x-trace-id", "x-request-id", "content-type"]:
            print(f"  {k}: {v}")

    try:
        data = response.json()
        print("\nBody (JSON):")
        print(json.dumps(data, indent=2))
    except Exception:
        print(f"\nBody: {response.text}")


def main():
    print_header("DEMONSTRAÇÃO DEBUG UX & ERROR HANDLING")

    # 1. Sucesso com Tracing
    print_header("1. Requisição de Sucesso (Health Check)")
    response = client.get("/health")
    print_response(
        response, "GET /health - Deve retornar 200 OK com headers de tracing"
    )

    # 2. Rastreamento Distribuído
    print_header("2. Propagação de Trace ID")
    trace_id = str(uuid.uuid4())
    print(f"Enviando X-Trace-ID: {trace_id}")
    response = client.get("/health", headers={"X-Trace-ID": trace_id})
    print_response(
        response, "GET /health com header customizado - Deve manter o Trace ID"
    )

    # 3. Recurso Não Encontrado (404)
    print_header("3. Erro 404 (Resource Not Found)")
    response = client.get("/api/v1/users/non-existent-id")
    print_response(
        response,
        "GET em recurso inexistente - Deve retornar JSON padronizado com código RES_001",
    )

    # 4. Erro de Validação (422)
    print_header("4. Erro de Validação (Validation Error)")
    # Assumindo um endpoint que requer dados (ex: login simulado ou qualquer POST)
    # Como não tenho login fácil sem banco, vou forçar um 404 que é tratado diferente,
    # ou melhor, vou tentar um endpoint que sei que exige validação se existir,
    # senão uso o handler direto para demonstrar

    # Tentativa em endpoint de auth que valida email
    response = client.post("/api/v1/auth/magic-link", json={"wrong_field": "value"})
    print_response(
        response,
        "POST com payload inválido - Deve retornar detalhes da validação (VAL_001)",
    )

    # 5. Erro de Autenticação (401)
    print_header("5. Erro de Autenticação")
    response = client.get("/api/v1/auth/me")
    print_response(
        response, "Acesso a rota protegida sem token - Deve retornar AUTH_003"
    )


if __name__ == "__main__":
    main()
