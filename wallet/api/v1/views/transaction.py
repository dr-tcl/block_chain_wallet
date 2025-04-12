from django.db import transaction as db_transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from wallet.api.v1.serializers import (
    AccountSerializer,
    TransactionSerializer,
    TransactionCreateSerializer,
    BalanceSerializer
)
from wallet.models import Account, Transaction


class AccountViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Account resources.
    Provides standard CRUD operations as well as additional actions
    for retrieving account balance and transaction history.
    """
    queryset = Account.objects.all()
    serializer_class = AccountSerializer

    @action(detail=True, methods=['get'])
    def balance(self, request, pk=None):
        """
        Custom action to retrieve the current balance of an account.
        """
        account = self.get_object()
        serializer = BalanceSerializer({'balance': account.balance})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """
        Custom action to retrieve the list of transactions for a specific account,
        ordered by creation time in descending order.
        """
        account = self.get_object()
        transactions = account.transactions.all().order_by('-created_at')
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)


class TransactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Transaction resources.
    Handles custom create logic including atomic execution of transactions,
    and supports rollback functionality.
    """
    queryset = Transaction.objects.all()

    def get_serializer_class(self):
        """
        Return appropriate serializer class based on the action.
        Uses a different serializer when creating a transaction.
        """
        if self.action == 'create':
            return TransactionCreateSerializer
        return TransactionSerializer

    def create(self, request, *args, **kwargs):
        """
        Override the default create method to:
        - Validate input data
        - Execute the transaction inside an atomic block
        - Return proper responses based on execution result
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with db_transaction.atomic():
                # Save transaction with initial PENDING status
                tx = serializer.save(status=Transaction.PENDING)

                # Attempt to execute transaction (e.g. transfer funds)
                if tx.execute():
                    # If successful, return serialized transaction
                    return Response(
                        TransactionSerializer(tx).data,
                        status=status.HTTP_201_CREATED
                    )
                else:
                    # If execution fails, return error details
                    return Response(
                        {'detail': 'Transaction failed', 'errors': tx.error_message},
                        status=status.HTTP_400_BAD_REQUEST
                    )
        except Exception as e:
            # Catch and return any unexpected errors
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def rollback(self, request, pk=None):
        """
        Custom action to rollback a transaction.
        Returns success or failure message based on the result.
        """
        tx = self.get_object()
        if tx.rollback():
            return Response({'status': 'rollback successful'})
        return Response(
            {'status': 'rollback failed'},
            status=status.HTTP_400_BAD_REQUEST
        )
