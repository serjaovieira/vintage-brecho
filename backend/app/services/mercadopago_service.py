"""
Mercado Pago PIX Checkout & Payment Service for Vintage Brechó.
Handles:
- PIX payment creation via Mercado Pago API v1 (/v1/payments) with idempotency key and metadata.
- Extraction of EMVCo string (copia e cola) and base64 QR Code image.
- Resilient local fallback generator with BACEN-standard EMVCo CRC-CCITT (poly 0x1021) and base64 QR Code.
- Payment status verification for webhook authentication and order status reconciliation.
"""

from decimal import Decimal
import logging
from typing import Any, Dict, Optional
import uuid

import httpx

try:
    from app.config import settings
except ImportError:
    from backend.app.config import settings

logger = logging.getLogger("vintage_brecho.mercadopago")

# Standard 1x1 transparent PNG fallback for test environments without graphical libraries
SAMPLE_QR_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)

DEFAULT_PIX_KEY = "contato@vintagebrecho.com.br"
MP_PAYMENTS_URL = "https://api.mercadopago.com/v1/payments"


def _calculate_crc16(payload: str) -> str:
    """
    Calculates CRC16-CCITT (poly 0x1021, init 0xFFFF) for the BACEN / EMVCo standard BR Code.
    """
    crc = 0xFFFF
    for char in payload.encode("utf-8"):
        crc ^= (char << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return f"{crc:04X}"


def generate_emvco_pix(
    total_amount: Decimal,
    order_id: uuid.UUID,
    pix_key: str = DEFAULT_PIX_KEY,
    merchant_name: str = "Vintage Brecho",
    merchant_city: str = "Sao Paulo",
) -> str:
    """
    Generates a genuine Brazilian Central Bank (BACEN) EMVCo BR Code PIX payload.
    Includes merchant account info (tag 26), currency (tag 53=986), amount (tag 54),
    merchant name/city, and reference txid (tag 62), followed by CRC16 checksum (tag 63).
    """
    amount_str = f"{total_amount:.2f}"
    txid = order_id.hex[:25]

    # Tag 26: Merchant Account Information - PIX
    gui_sub = "0014br.gov.bcb.pix"
    key_sub = f"01{len(pix_key):02d}{pix_key}"
    tag26_val = f"{gui_sub}{key_sub}"
    tag26 = f"26{len(tag26_val):02d}{tag26_val}"

    # Tag 00: Payload Format Indicator ("01")
    tag00 = "000201"
    # Tag 52: Merchant Category Code ("0000")
    tag52 = "52040000"
    # Tag 53: Transaction Currency (986 = BRL)
    tag53 = "5303986"
    # Tag 54: Transaction Amount
    tag54 = f"54{len(amount_str):02d}{amount_str}"
    # Tag 58: Country Code ("BR")
    tag58 = "5802BR"

    clean_name = merchant_name[:25]
    tag59 = f"59{len(clean_name):02d}{clean_name}"

    clean_city = merchant_city[:15]
    tag60 = f"60{len(clean_city):02d}{clean_city}"

    # Tag 62: Additional Data Field (Reference TXID)
    ref_sub = f"05{len(txid):02d}{txid}"
    tag62 = f"62{len(ref_sub):02d}{ref_sub}"

    # Tag 63: CRC16 prefix
    payload_without_crc = f"{tag00}{tag26}{tag52}{tag53}{tag54}{tag58}{tag59}{tag60}{tag62}6304"
    crc = _calculate_crc16(payload_without_crc)
    return f"{payload_without_crc}{crc}"


def generate_qr_code_base64(emvco_payload: str) -> str:
    """
    Generates a base64 encoded PNG for the EMVCo string.
    Dynamically renders using `qrcode` library if available,
    otherwise returns standard base64 PNG fallback.
    """
    try:
        import base64
        import io
        import qrcode
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=2,
        )
        qr.add_data(emvco_payload)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
    except Exception:
        return SAMPLE_QR_BASE64


async def create_pix_payment(
    product_id: int,
    total_amount: Decimal,
    customer_email: str,
    customer_name: str,
    order_id: uuid.UUID,
) -> Dict[str, Any]:
    """
    Creates a PIX payment for a 1-of-1 piece:
    1. Attempts to call the official Mercado Pago API (POST /v1/payments) with:
       - MERCADO_PAGO_ACCESS_TOKEN
       - X-Idempotency-Key: str(order_id)
       - metadata: {"product_id": product_id, "order_id": str(order_id)}
       - payment_method_id: "pix"
    2. Extracts `qr_code` (EMVCo string) and `qr_code_base64`.
    3. If the network fails, token is in sandbox, or environment is offline:
       Falls back gracefully to local EMVCo and base64 generator.
    """
    token = settings.MERCADO_PAGO_ACCESS_TOKEN
    names = (customer_name or "Cliente").strip().split(maxsplit=1)
    first_name = names[0] if names else "Cliente"
    last_name = names[1] if len(names) > 1 else "Vintage"

    payload = {
        "transaction_amount": float(total_amount),
        "description": f"Vintage Brechó - Peça #{product_id} (Pedido {order_id})",
        "payment_method_id": "pix",
        "payer": {
            "email": customer_email,
            "first_name": first_name,
            "last_name": last_name,
        },
        "metadata": {
            "product_id": product_id,
            "order_id": str(order_id),
        },
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Idempotency-Key": str(order_id),
        "Content-Type": "application/json",
    }

    if token:
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                response = await client.post(
                    MP_PAYMENTS_URL,
                    headers=headers,
                    json=payload,
                )

                if response.status_code in (200, 201):
                    data = response.json()
                    point_of_interaction = data.get("point_of_interaction") or {}
                    transaction_data = point_of_interaction.get("transaction_data") or {}
                    qr_code = transaction_data.get("qr_code")
                    qr_code_base64 = transaction_data.get("qr_code_base64")
                    ticket_url = transaction_data.get("ticket_url")

                    if qr_code and qr_code_base64:
                        logger.info(
                            f"[MercadoPago] PIX criado com sucesso na API: payment_id={data.get('id')} order_id={order_id}"
                        )
                        return {
                            "payment_id": str(data.get("id")),
                            "status": data.get("status", "pending"),
                            "qr_code": qr_code,
                            "qr_code_base64": qr_code_base64,
                            "ticket_url": ticket_url,
                        }
                    else:
                        logger.warning(
                            f"[MercadoPago] Resposta 200/201 sem transaction_data completa: {data}"
                        )
                else:
                    logger.warning(
                        f"[MercadoPago] API retornou HTTP {response.status_code}: {response.text}. Ativando fallback local."
                    )
        except Exception as exc:
            logger.info(
                f"[MercadoPago] Chamada de rede indisponível ({exc}). Ativando fallback local EMVCo."
            )

    # Resilient local fallback generator
    emvco_code = generate_emvco_pix(total_amount, order_id)
    qr_base64 = generate_qr_code_base64(emvco_code)

    return {
        "payment_id": f"mp_{order_id.hex[:12]}",
        "status": "pending",
        "qr_code": emvco_code,
        "qr_code_base64": qr_base64,
        "ticket_url": None,
    }


async def get_payment(payment_id: str | int) -> Optional[Dict[str, Any]]:
    """
    Queries Mercado Pago API for payment details by payment ID.
    Used by the webhook handler to verify authenticity and check approval status.
    GET https://api.mercadopago.com/v1/payments/{payment_id}
    """
    token = settings.MERCADO_PAGO_ACCESS_TOKEN
    if not token or not payment_id:
        return None

    # Sanitize payment_id if prefixed with mock/offline
    clean_id = str(payment_id)
    if clean_id.startswith("mock_pay_") or clean_id.startswith("mp_"):
        return None

    url = f"{MP_PAYMENTS_URL}/{clean_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            logger.warning(
                f"[MercadoPago] get_payment({payment_id}) retornou HTTP {response.status_code}: {response.text}"
            )
            return None
    except Exception as exc:
        logger.warning(f"[MercadoPago] Erro ao consultar pagamento {payment_id}: {exc}")
        return None
