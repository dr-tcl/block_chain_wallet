from rest_framework import serializers
from wallet.models import Account, Transaction


class AccountSerializer(serializers.ModelSerializer):
    """
    Serializer for the Account model.
    Includes the account's public key, balance, and creation timestamp.
    The balance is read-only to prevent external modification.
    """
    balance = serializers.DecimalField(max_digits=20, decimal_places=8, read_only=True)

    class Meta:
        model = Account
        fields = ['id', 'public_key', 'balance', 'created_at']
        read_only_fields = ['id', 'balance', 'created_at']


class TransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for representing transaction data.
    Used for listing or retrieving full transaction details.
    """
    class Meta:
        model = Transaction
        fields = [
            'id', 'account', 'amount', 'transaction_type', 'status',
            'created_at', 'updated_at', 'tx_hash', 'error_message'
        ]
        read_only_fields = [
            'id', 'status', 'created_at', 'updated_at',
            'tx_hash', 'error_message'
        ]


class TransactionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new transaction.
    Includes basic validation logic for the transaction amount.
    Fields like status and error messages are managed internally.
    """
    class Meta:
        model = Transaction
        fields = ['account', 'amount', 'transaction_type', 'tx_hash']

    def validate_amount(self, value):
        """
        Ensure that the amount is a positive number.
        """
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive")
        return value


class BalanceSerializer(serializers.Serializer):
    """
    Simple serializer used to return account balance.
    Not tied directly to a model, used in custom API views.
    """
    balance = serializers.DecimalField(max_digits=20, decimal_places=8)
