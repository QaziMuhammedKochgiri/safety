"""
Stripe Payment Integration for SafeChild using Emergent Integrations
"""
import os
from dotenv import load_dotenv
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest
from typing import Dict, Optional
import uuid

load_dotenv()

# Stripe API key
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY", "sk_test_emergent")

# Fixed consultation package price (backend-defined for security)
CONSULTATION_PACKAGES = {
    "consultation": {
        "amount": 150.00,  # EUR (as float for Stripe)
        "currency": "eur",
        "name": "Legal Consultation - SafeChild",
        "description": "Comprehensive 60-minute consultation with our experts"
    }
}

async def create_consultation_checkout(
    client_number: str,
    client_email: str,
    origin_url: str,
    package_id: str = "consultation"
) -> Dict:
    """
    Create Stripe checkout session for legal consultation
    
    Args:
        client_number: Client's unique number
        client_email: Client's email
        origin_url: Frontend origin URL for success/cancel redirects
        package_id: Package type (default: "consultation")
    
    Returns:
        Dict with checkout URL and session ID
    """
    try:
        # Validate package
        if package_id not in CONSULTATION_PACKAGES:
            raise ValueError(f"Invalid package: {package_id}")
        
        package = CONSULTATION_PACKAGES[package_id]
        
        # Build webhook and success/cancel URLs
        webhook_url = f"{origin_url}/api/webhook/stripe"
        success_url = f"{origin_url}/portal?session_id={{{{CHECKOUT_SESSION_ID}}}}&payment=success"
        cancel_url = f"{origin_url}/book-consultation?payment=cancelled"
        
        # Initialize Stripe checkout
        stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
        
        # Create checkout request with backend-defined amount (security)
        checkout_request = CheckoutSessionRequest(
            amount=package["amount"],
            currency=package["currency"],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "client_number": client_number,
                "client_email": client_email,
                "package_id": package_id,
                "service": "legal_consultation"
            }
        )
        
        # Create checkout session
        session: CheckoutSessionResponse = await stripe_checkout.create_checkout_session(checkout_request)
        
        return {
            "success": True,
            "url": session.url,
            "session_id": session.session_id,
            "amount": package["amount"],
            "currency": package["currency"]
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

async def get_checkout_status(session_id: str) -> Dict:
    """
    Get checkout session status
    
    Args:
        session_id: Stripe checkout session ID
    
    Returns:
        Dict with payment status
    """
    try:
        # Initialize Stripe checkout
        stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url="")
        
        # Get checkout status
        status: CheckoutStatusResponse = await stripe_checkout.get_checkout_status(session_id)
        
        return {
            "success": True,
            "status": status.status,
            "payment_status": status.payment_status,
            "amount_total": status.amount_total / 100,  # Convert cents to dollars
            "currency": status.currency,
            "metadata": status.metadata
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

async def handle_webhook(payload: bytes, signature: str) -> Dict:
    """
    Handle Stripe webhook events
    
    Args:
        payload: Raw webhook payload
        signature: Stripe signature header
    
    Returns:
        Dict with webhook event data
    """
    try:
        stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url="")
        webhook_response = await stripe_checkout.handle_webhook(payload, signature)
        
        return {
            "success": True,
            "event_type": webhook_response.event_type,
            "event_id": webhook_response.event_id,
            "session_id": webhook_response.session_id,
            "payment_status": webhook_response.payment_status,
            "metadata": webhook_response.metadata
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
