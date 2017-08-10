import requests
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView

from member.models import User


class FacebookLoginAPIView(APIView):
    FACEBOOK_APP_ID = '168578930349021'
    FACEBOOK_SECRET_CODE = '6608a1a35da0cad2d9a809d99efbcd5a'
    APP_ACCESS_TOKEN = '{}|{}'.format(
        FACEBOOK_APP_ID,
        FACEBOOK_SECRET_CODE,
    )

    def post(self, request):
        token = request.data.get('token')
        if not token:
            raise APIException('token require')

        # 프론트로부터 전달받은 token을 Facebook의 debug_token API를 사용해
        # 검증한 결과를 debug_result에 할당
        self.debug_token(token)
        user_info = self.get_user_info(token=token)
        # 이미존재하면 가져오고 아니면 create_facebook_user메서드를 사용
        if User.objects.filter(username=user_info['id']).exists():
            user = User.objects.get(username=user_info['id'])
        else:
            user = User.objects.create_facebook_user(user_info)

        # DRF token을 생성
        token, token_created = Token.objects.get_or_create(user=user)

        # 관련정보를 한번에 리턴
        ret = {
            'token': token.key,
            'user': {
                'pk': user.pk,
                'username': user.username
            }
        }
        return Response(ret)

    def debug_token(self, token):
        """
        주어진 token으로 FacebookAPI의 debug_token을 실행, 결과를 리턴
        :param token: 프론트엔드에서 유저가 페이스북 로그인 후 반환된 authResponse내의 accessToken값
        :return: FacebookAPI의 debug_token실행 후의 결과
        """
        url_debug_token = 'https://graph.facebook.com/debug_token'
        url_debug_token_params = {
            'input_token': token,
            'access_token': self.APP_ACCESS_TOKEN,
        }
        response = requests.get(url_debug_token, url_debug_token_params)
        result = response.json()
        if 'error' in result['data']:
            raise APIException('token invalid')
        return result

    def get_user_info(self, user_id, token):
        url_user_info = 'https://graph.facebook.com/v2.9/me'
        url_user_info_params = {
            'access_token': token,
            'fields': ','.join([
                'id',
                'name',
                'first_name',
                'last_name',
                'picture.type(large)',
                'gender',
            ])
        }
        response = requests.get(url_user_info, params=url_user_info_params)
        result = response.json()
        return result
