# token_management/services.py

from django.db import transaction
from django.utils import timezone
import uuid
from token_management.models import TokenPurchase, UserTokenLimit

class TokenPurchaseService:
    @staticmethod
    def initiate_purchase(user, tokens_amount, amount_paid, currency='USD', 
                          payment_provider='stripe', idempotency_key=None):
        """
        Initiate a token purchase transaction
        
        Args:
            user: The user making the purchase
            tokens_amount: Number of tokens to purchase
            amount_paid: Amount paid for the tokens
            currency: Currency used for payment
            payment_provider: Payment provider used
            idempotency_key: Optional key to prevent duplicate transactions
            
        Returns:
            TokenPurchase object
        """
        # Generate idempotency key if not provided
        if not idempotency_key:
            idempotency_key = str(uuid.uuid4())
            
        # Check if a transaction with this idempotency key already exists
        existing = TokenPurchase.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
            return existing
            
        with transaction.atomic():
            # Check if user has any ongoing transaction
            ongoing = TokenPurchase.objects.filter(
                user=user,
                is_processing=True,
                payment_status='processing'
            ).exists()
            
            if ongoing:
                raise ValueError("User has an ongoing transaction. Please complete or cancel it first.")
                
            # Create new purchase
            purchase = TokenPurchase.objects.create(
                user=user,
                tokens_purchased=tokens_amount,
                amount_paid=amount_paid,
                currency=currency,
                payment_provider=payment_provider,
                idempotency_key=idempotency_key,
                is_processing=True,
                payment_status='processing'
            )
            
            return purchase
    
    @staticmethod
    def complete_purchase(purchase_id=None, transaction_id=None, payment_id=None):
        """
        Complete a token purchase transaction
        
        Args:
            purchase_id: ID of the TokenPurchase object
            transaction_id: Transaction ID of the purchase
            payment_id: Payment ID from payment processor
            
        Returns:
            Updated TokenPurchase object
        """
        if not any([purchase_id, transaction_id, payment_id]):
            raise ValueError("At least one of purchase_id, transaction_id, or payment_id must be provided")
            
        # Find the purchase record
        query = {}
        if purchase_id:
            query['id'] = purchase_id
        elif transaction_id:
            query['transaction_id'] = transaction_id
        elif payment_id:
            query['payment_id'] = payment_id
            
        with transaction.atomic():
            try:
                # Lock the record
                purchase = TokenPurchase.objects.select_for_update().get(**query)
                
                # Skip if already completed
                if purchase.payment_status == 'completed':
                    return purchase
                    
                # Check if still processing
                if not purchase.is_processing:
                    raise ValueError("Transaction is not in processing state")
                    
                # Set payment ID if provided
                if payment_id and not purchase.payment_id:
                    purchase.payment_id = payment_id
                    
                # Complete the purchase
                result = purchase.mark_completed()
                if not result:
                    raise ValueError(f"Could not complete purchase. Current status: {purchase.payment_status}")
                    
                return purchase
                
            except TokenPurchase.DoesNotExist:
                raise ValueError("Purchase not found")
    
    @staticmethod
    def cancel_purchase(purchase_id=None, transaction_id=None, payment_id=None):
        """
        Cancel a token purchase transaction
        
        Args:
            purchase_id: ID of the TokenPurchase object
            transaction_id: Transaction ID of the purchase
            payment_id: Payment ID from payment processor
            
        Returns:
            Updated TokenPurchase object
        """
        if not any([purchase_id, transaction_id, payment_id]):
            raise ValueError("At least one of purchase_id, transaction_id, or payment_id must be provided")
            
        # Find the purchase record
        query = {}
        if purchase_id:
            query['id'] = purchase_id
        elif transaction_id:
            query['transaction_id'] = transaction_id
        elif payment_id:
            query['payment_id'] = payment_id
            
        with transaction.atomic():
            try:
                # Lock the record
                purchase = TokenPurchase.objects.select_for_update().get(**query)
                
                # Skip if already failed or refunded
                if purchase.payment_status in ['failed', 'refunded']:
                    return purchase
                    
                # Mark as failed
                purchase.payment_status = 'failed'
                purchase.is_processing = False
                purchase.save(update_fields=['payment_status', 'is_processing'])
                
                return purchase
                
            except TokenPurchase.DoesNotExist:
                raise ValueError("Purchase not found")


class TokenUsageService:
    @staticmethod
    def track_usage(user, tokens_used, feature='other', **kwargs):
        """
        Track token usage for a user
        
        Args:
            user: The user using tokens
            tokens_used: Number of tokens used
            feature: Feature for which tokens were used
            **kwargs: Additional data to store with the usage
            
        Returns:
            Updated UserTokenLimit object
        """
        with transaction.atomic():
            try:
                # Get and lock the user's token limit
                token_limit = UserTokenLimit.objects.select_for_update().get(user=user)
                
                # Update usage
                token_limit.update_token_usage(tokens_used, feature, **kwargs)
                
                return token_limit
                
            except UserTokenLimit.DoesNotExist:
                # Create token limit if it doesn't exist
                token_limit = UserTokenLimit.objects.create(user=user)
                token_limit.update_token_usage(tokens_used, feature, **kwargs)
                
                return token_limit