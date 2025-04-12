import decimal

from cryptography.fernet import Fernet
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db import transaction


class Account(models.Model):
    """
    Represents a user's account with a unique public key and encrypted private key.
    Includes logic for securely storing and retrieving the private key, and calculating balance.
    """
    public_key = models.CharField(max_length=255, unique=True)
    encrypted_private_key = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def private_key(self):
        """
        Decrypts and returns the private key using Fernet symmetric encryption.
        """
        cipher_suite = Fernet(settings.FERNET_KEY)
        return cipher_suite.decrypt(self.encrypted_private_key.encode()).decode()

    @private_key.setter
    def private_key(self, value):
        """
        Encrypts and stores the private key using Fernet symmetric encryption.
        """
        cipher_suite = Fernet(settings.FERNET_KEY)
        self.encrypted_private_key = cipher_suite.encrypt(value.encode()).decode()

    @property
    def balance(self):
        """
        Calculates the current balance based on completed deposit and withdrawal transactions.
        """
        completed_txs = self.transactions.filter(status=Transaction.COMPLETED)

        # Sum of completed deposits
        deposits = completed_txs.filter(transaction_type=Transaction.DEPOSIT).aggregate(
            total=models.Sum('amount')
        )['total'] or decimal.Decimal('0.00')

        # Sum of completed withdrawals
        withdrawals = completed_txs.filter(transaction_type=Transaction.WITHDRAW).aggregate(
            total=models.Sum('amount')
        )['total'] or decimal.Decimal('0.00')

        return deposits - withdrawals

    def __str__(self):
        return f"Account {self.public_key}"

    class Meta:
        app_label = 'wallet'


class Transaction(models.Model):
    """
    Represents a financial transaction linked to an account.
    Handles both deposits and withdrawals with status tracking and rollback support.
    """

    # Transaction status choices
    PENDING = 'pending'
    COMPLETED = 'completed'
    FAILED = 'failed'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (COMPLETED, 'Completed'),
        (FAILED, 'Failed'),
    ]

    # Transaction type choices
    DEPOSIT = 'deposit'
    WITHDRAW = 'withdraw'
    TYPE_CHOICES = [
        (DEPOSIT, 'Deposit'),
        (WITHDRAW, 'Withdraw'),
    ]

    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='transactions')
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        validators=[MinValueValidator(0)]
    )
    transaction_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tx_hash = models.CharField(max_length=255, unique=True, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        app_label = 'wallet'

    def execute(self):
        """
        Executes the transaction:
        - Deposits always succeed
        - Withdrawals require sufficient balance
        - Uses an atomic block to ensure database consistency
        - Updates status and error messages accordingly
        """
        try:
            with transaction.atomic():
                account = Account.objects.select_for_update().get(pk=self.account.pk)

                if self.status != self.PENDING:
                    raise ValueError("Transaction already processed")

                if self.transaction_type == self.DEPOSIT:
                    self.status = self.COMPLETED
                    self.save()
                    return True

                elif self.transaction_type == self.WITHDRAW:
                    if account.balance >= self.amount:
                        self.status = self.COMPLETED
                        self.save()
                        return True
                    else:
                        self.status = self.FAILED
                        self.error_message = "Insufficient balance"
                        self.save()
                        return False

        except Exception as e:
            self.status = self.FAILED
            self.error_message = str(e)
            self.save()
            return False

    def rollback(self):
        """
        Rolls back a completed transaction by marking it as failed and logging a rollback message.
        Only allowed if the transaction is currently completed.
        """
        if self.status != self.COMPLETED:
            return False

        try:
            with transaction.atomic():
                account = Account.objects.select_for_update().get(pk=self.account.pk)
                self.status = self.FAILED
                self.error_message = "Rolled back"
                self.save()
                return True
        except Exception as e:
            print(e)
            return False

    def __str__(self):
        """
        Returns a human-readable string for the transaction.
        """
        return f"{self.get_transaction_type_display()} of {self.amount} for {self.account}"
