from askbot.tests.utils import AskbotTestCase, with_settings
from askbot.utils.akismet_utils import akismet_check_spam
import responses
from urlparse import parse_qsl

TEXT = 'hello foobar'
API_KEY = 'foobar'
CHECK_SPAM_URL = 'https://{}.rest.akismet.com/1.1/comment-check'.format(API_KEY)
VERIFY_KEY_URL = 'https://rest.akismet.com/1.1/verify-key'
USER_AGENT = 'user_agent_string'
USER_IP = '0.0.0.0'
COMMENT_AUTHOR = 'bob'
COMMENT_AUTHOR_EMAIL = 'bob@example.com'


class User(object):
    def __init__(self, anon=False, username=COMMENT_AUTHOR, email=COMMENT_AUTHOR_EMAIL):
        self.anon = anon
        if anon:
            self.username = u''
        else:
            self.username = username
            self.email = email

    def is_authenticated(self):
        return not self.anon

    def is_anonymous(self):
        return self.anon


class AuthRequest(object):
    environ = {'HTTP_USER_AGENT': USER_AGENT}
    META = {'REMOTE_ADDR': USER_IP}
    def __init__(self, anon=False, username=COMMENT_AUTHOR, email=COMMENT_AUTHOR_EMAIL):
        self.user = User(anon, username, email)


def check_spam_callback(request):
    return (200, {}, 'false')

def verify_key_callback(request):
    return (200, {}, 'valid')

def mock_akismet():
    responses.add_callback(responses.POST,
                           CHECK_SPAM_URL,
                           callback=check_spam_callback)
    responses.add_callback(responses.POST,
                           VERIFY_KEY_URL,
                           callback=verify_key_callback)

def get_request_params(idx):
    """Returns dictionary of api call request parameters,
    as we made it.
    `idx` is the request order number, e.g
    """
    return dict(parse_qsl(responses.calls[idx].request.body))

class AkismetApiRequestTests(AskbotTestCase):

    @responses.activate
    @with_settings(USE_AKISMET=True, AKISMET_API_KEY=API_KEY, APP_URL='http://askbot.com/')
    def test_anon_user_no_author(self):
        mock_akismet()
        request = AuthRequest(anon=True)
        akismet_check_spam(TEXT, request)
        params = get_request_params(1)
        self.assertEqual(params['comment_content'], TEXT)
        self.assertEqual(params['user_ip'], USER_IP)
        self.assertEqual(params['user_agent'], USER_AGENT)
        self.assertEqual(params['blog'], 'http://askbot.com/questions/')
        self.assertTrue('comment_author' not in params)
        self.assertTrue('comment_author_email' not in params)

    @responses.activate
    @with_settings(USE_AKISMET=True, AKISMET_API_KEY=API_KEY, APP_URL='http://askbot.com/')
    def test_anon_user_with_author(self):
        mock_akismet()
        request = AuthRequest(anon=True)
        akismet_check_spam(TEXT, request, User())
        params = get_request_params(1)
        self.assertEqual(params['comment_content'], TEXT)
        self.assertEqual(params['user_ip'], USER_IP)
        self.assertEqual(params['user_agent'], USER_AGENT)
        self.assertEqual(params['blog'], 'http://askbot.com/questions/')
        self.assertEqual(params['comment_author'], COMMENT_AUTHOR)
        self.assertEqual(params['comment_author_email'], COMMENT_AUTHOR_EMAIL)

    @responses.activate
    @with_settings(USE_AKISMET=True, AKISMET_API_KEY=API_KEY, APP_URL='http://askbot.com/')
    def test_auth_user_no_author(self):
        mock_akismet()
        request = AuthRequest(username='Request User', email='request@example.com')
        akismet_check_spam(TEXT, request)
        params = get_request_params(1)
        self.assertEqual(params['comment_content'], TEXT)
        self.assertEqual(params['user_ip'], USER_IP)
        self.assertEqual(params['user_agent'], USER_AGENT)
        self.assertEqual(params['blog'], 'http://askbot.com/questions/')
        self.assertEqual(params['comment_author'], 'Request User')
        self.assertEqual(params['comment_author_email'], 'request@example.com')

    @responses.activate
    @with_settings(USE_AKISMET=True, AKISMET_API_KEY=API_KEY, APP_URL='http://askbot.com/')
    def test_auth_user_with_author(self):
        mock_akismet()
        request = AuthRequest(username='Request User', email='request@example.com')
        user = User()
        akismet_check_spam(TEXT, request, user)
        params = get_request_params(1)
        self.assertEqual(params['comment_content'], TEXT)
        self.assertEqual(params['user_ip'], USER_IP)
        self.assertEqual(params['user_agent'], USER_AGENT)
        self.assertEqual(params['blog'], 'http://askbot.com/questions/')
        self.assertEqual(params['comment_author'], user.username)
        self.assertEqual(params['comment_author_email'], user.email)
