from django.core.management.base import BaseCommand
from signupper.ldaputils.ldaputils import listusers

class Command(BaseCommand):
    help = 'print all ldap users, a single user by specifying a uid/username, or none if this does not exist'

    def add_arguments(self, parser):
        parser.add_argument('uid', nargs='?', type=str, help='optional single user uid')

    def handle(self, *args, **options):
        users = listusers(options['uid'])
        if len(users)==0:
            print('user entry for uid="%s" not found' % options['uid'])
        print('')
        print('-- %s ldap users detected:' % len(users))
        print('')
        for u in users:
            print(u)
