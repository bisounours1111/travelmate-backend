from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import stripe
import os
from dotenv import load_dotenv
import logging

load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Configuration Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_51ReySuFMFs1dsPI2Y3Zc1DgMAikaBLAxJ4XtSgk6YTtyMq82jqpE2SdO6Z2IkUwTsJvspeMG2vyA2F6EVUPdimDe007qaG8Zes")

class PaymentIntentRequest(BaseModel):
    amount: int
    currency: str = "eur"

@router.post("/create-payment-intent")
async def create_payment_intent(request: PaymentIntentRequest):
    try:
        logger.info(f"Création d'un PaymentIntent pour {request.amount} {request.currency}")
        
        # Créer un PaymentIntent avec Stripe
        payment_intent = stripe.PaymentIntent.create(
            amount=request.amount,
            currency=request.currency,
            automatic_payment_methods={"enabled": True},
            metadata={
                "source": "mobile_app",
                "environment": "sandbox"
            }
        )
        
        logger.info(f"PaymentIntent créé avec succès: {payment_intent.id}")
        
        return {
            "client_secret": payment_intent.client_secret,
            "payment_intent_id": payment_intent.id,
            "amount": payment_intent.amount,
            "currency": payment_intent.currency,
            "status": payment_intent.status
        }
    except stripe.error.StripeError as e:
        logger.error(f"Erreur Stripe: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Erreur Stripe: {str(e)}")
    except Exception as e:
        logger.error(f"Erreur serveur: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

@router.get("/payment-status/{payment_intent_id}")
async def get_payment_status(payment_intent_id: str):
    try:
        logger.info(f"Récupération du statut pour PaymentIntent: {payment_intent_id}")
        
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        return {
            "id": payment_intent.id,
            "status": payment_intent.status,
            "amount": payment_intent.amount,
            "currency": payment_intent.currency,
            "client_secret": payment_intent.client_secret
        }
    except stripe.error.StripeError as e:
        logger.error(f"Erreur Stripe: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Erreur Stripe: {str(e)}")
    except Exception as e:
        logger.error(f"Erreur serveur: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

@router.post("/confirm-payment-intent/{payment_intent_id}")
async def confirm_payment_intent(payment_intent_id: str):
    try:
        logger.info(f"Confirmation du PaymentIntent: {payment_intent_id}")
        
        # Récupérer le PaymentIntent
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        # Confirmer le PaymentIntent
        confirmed_intent = stripe.PaymentIntent.confirm(payment_intent_id)
        
        return {
            "id": confirmed_intent.id,
            "status": confirmed_intent.status,
            "amount": confirmed_intent.amount,
            "currency": confirmed_intent.currency
        }
    except stripe.error.StripeError as e:
        logger.error(f"Erreur Stripe: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Erreur Stripe: {str(e)}")
    except Exception as e:
        logger.error(f"Erreur serveur: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}") 