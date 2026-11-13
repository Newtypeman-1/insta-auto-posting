class PublishError(Exception):
    """인스타그램이 게시를 거절했을 때 나는 에러."""


class AuthError(PublishError):
    """토큰이 만료되었거나 잘못됨. 글의 문제가 아니라 사람이 토큰을 바꿔야 하는 문제."""


class AddError(Exception):
    """큐에 넣을 수 없는 글. 큐는 건드리지 않고 이유를 알려 준다."""
