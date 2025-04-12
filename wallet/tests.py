from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from .models import Account, Transaction
import decimal


class WalletTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
        self.account_data = {
            'public_key': 'test_public_key',
            'private_key': 'test_private_key'
        }
        self.account = Account.objects.create(
            public_key=self.account_data['public_key']
        )
        self.account.private_key = self.account_data['private_key']
        self.account.save()

    def test_create_account(self):
        url = reverse('account-list')
        data = {
            'public_key': 'new_public_key',
            'private_key': 'new_private_key'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Account.objects.count(), 2)

    def test_deposit_transaction(self):
        url = reverse('transaction-list')
        data = {
            'account': self.account.id,
            'amount': '10.00',
            'transaction_type': 'deposit'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'completed')


        url = reverse('account-balance', kwargs={'pk': self.account.id})
        response = self.client.get(url)
        self.assertEqual(decimal.Decimal(response.data['balance']), decimal.Decimal('10.00'))


    def test_withdraw_transaction(self):
        Transaction.objects.create(
            account=self.account,
            amount=decimal.Decimal('20.00'),
            transaction_type=Transaction.DEPOSIT,
            status=Transaction.COMPLETED
        )
        url = reverse('transaction-list')
        data = {
            'account': self.account.id,
            'amount': '10.00',
            'transaction_type': 'withdraw'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'completed')

        url = reverse('account-balance', kwargs={'pk': self.account.id})
        response = self.client.get(url)
        self.assertEqual(decimal.Decimal(response.data['balance']), decimal.Decimal('10.00'))


    def test_insufficient_balance(self):
        url = reverse('transaction-list')
        data = {
            'account': self.account.id,
            'amount': '10.00',
            'transaction_type': 'withdraw'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Insufficient balance', response.data['errors'])

    def test_transaction_history(self):

        Transaction.objects.create(
            account=self.account,
            amount=decimal.Decimal('10.00'),
            transaction_type=Transaction.DEPOSIT,
            status=Transaction.COMPLETED
        )
        Transaction.objects.create(
            account=self.account,
            amount=decimal.Decimal('5.00'),
            transaction_type=Transaction.WITHDRAW,
            status=Transaction.COMPLETED
        )

        url = reverse('account-transactions', kwargs={'pk': self.account.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)