from django.contrib.auth.tokens import PasswordResetTokenGenerator


class TokenGenerator(PasswordResetTokenGenerator):
    key_salt = 'toolx.account_activation.v2'

    def _make_hash_value(self, user, timestamp):
        return f'{super()._make_hash_value(user, timestamp)}:{user.is_active}:{user.profile.activation_pending}:{user.profile.email_confirmed}'


account_activation_token = TokenGenerator()
