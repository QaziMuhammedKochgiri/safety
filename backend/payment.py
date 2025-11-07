"""
Stripe Payment Integration for SafeChild
"""
import stripe
import os
from dotenv import load_dotenv

load_dotenv()

# Stripe API key (use test key for development)
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "sk_test_YOUR_KEY_HERE")

CONSULTATION_PRICE = 15000  # €150.00 in cents
CURRENCY = "eur"

def create_payment_intent(amount: int, currency: str = CURRENCY, metadata: dict = None):
    """Create a Stripe Payment Intent"""
    try:
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency=currency,
            metadata=metadata or {},
            automatic_payment_methods={"enabled": True}
        )
        return {
            "success": True,
            "client_secret": intent.client_secret,
            "payment_intent_id": intent.id
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def get_payment_status(payment_intent_id: str):
    """Get payment status"""
    try:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        return {
            "success": True,
            "status": intent.status,
            "amount": intent.amount,
            "currency": intent.currency
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def create_checkout_session(client_number: str, success_url: str, cancel_url: str):
    """Create Stripe Checkout Session for consultation booking"""
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": CURRENCY,
                    "unit_amount": CONSULTATION_PRICE,
                    "product_data": {
                        "name": "Legal Consultation - SafeChild",
                        "description": "Initial consultation with our experts",
                    },
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=client_number,
            metadata={
                "client_number": client_number,
                "service": "consultation"
            }
        )
        return {
            "success": True,
            "session_id": session.id,
            "url": session.url
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
