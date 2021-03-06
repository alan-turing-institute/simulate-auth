from flask_restful import Resource, abort
from flask import request, make_response, jsonify

from connection.models import db, User, BlacklistToken
from connection.hashing import bc


class RegisterApi(Resource):
    """
    User Registration Resource
    """

    def post(self):
        # get the post data
        post_data = request.get_json()

        # check if user already exists
        user = User.query.filter_by(username=post_data.get("username")).first()

        if not user:
            try:
                username = post_data.get("username")
                password = post_data.get("password")
                user = User(username=username, password=password)
                # insert the user
                db.session.add(user)
                db.session.commit()

                # generate the auth token
                auth_token = user.encode_auth_token(user.id, name=username)

                responseObject = {
                    "status": "success",
                    "message": "Successfully registered.",
                    "auth_token": auth_token.decode(),
                }
                return make_response(jsonify(responseObject), 201)
            except Exception as e:
                responseObject = {
                    "status": "fail",
                    "message": "Some error occurred. Please try again.",
                }
                return make_response(jsonify(responseObject), 401)
        else:
            responseObject = {
                "status": "fail",
                "message": "User already exists. Please Log in.",
            }
            return make_response(jsonify(responseObject), 202)


class LoginApi(Resource):
    """
    User Login Resource
    """

    def post(self):
        # get the post data
        post_data = request.get_json()

        try:
            # fetch the user data
            username = post_data.get("username")
            user = User.query.filter_by(username=username).first()
            if user and bc.check_password_hash(
                user.password, post_data.get("password")
            ):
                auth_token = user.encode_auth_token(user.id, name=username)
                if auth_token:
                    responseObject = {
                        "status": "success",
                        "message": "Successfully logged in.",
                        "auth_token": auth_token.decode(),
                    }
                    return make_response(jsonify(responseObject), 200)
            else:
                responseObject = {"status": "fail", "message": "User does not exist."}
                return make_response(jsonify(responseObject), 404)
        except Exception as e:
            print(e)
            responseObject = {"status": "fail", "message": "Try again"}
            return make_response(jsonify(responseObject), 500)


class UserApi(Resource):
    """
    User Resource
    """

    def __init__(self, **kwargs):
        pass

    def get(self):
        # get the auth token
        auth_header = request.headers.get("Authorization", "")
        auth_token = auth_header.replace("Bearer ", "")

        if auth_token:
            resp = User.decode_auth_token(auth_token)
            if isinstance(resp, dict):
                user = User.query.filter_by(id=resp["sub"]).first()

                # note this information is not stored in the token,
                # (the token is used to access the db and fetch this information)
                responseObject = {
                    "status": "success",
                    "data": {
                        "user_id": user.id,
                        "username": user.username,
                        "admin": user.admin,
                        "registered_on": user.registered_on,
                    },
                }
                return make_response(jsonify(responseObject), 200)
            responseObject = {"status": "fail", "message": resp}
            return make_response(jsonify(responseObject), 401)
        else:
            responseObject = {
                "status": "fail",
                "message": "Provide a valid auth token.",
            }
            return make_response(jsonify(responseObject), 401)


class TokenApi(Resource):
    """
    Token Resource
    """

    def __init__(self, **kwargs):
        pass

    def get(self):

        job_id = request.args.get("job_id", "")

        auth_header = request.headers.get("Authorization", "")
        auth_token = auth_header.replace("Bearer ", "")

        resp = User.decode_auth_token(auth_token)
        if isinstance(resp, dict):
            username = resp["name"]
            user = User.query.filter_by(username=username).first()
            job_token = user.encode_job_token(job_id=job_id).decode()
            responseObject = {
                "status": "success",
                "message": "Generated job token.",
                "job_token": job_token,
            }
            return make_response(jsonify(responseObject), 200)
        else:
            responseObject = {
                "status": "fail",
                "message": "Provide a valid auth token.",
            }
            return make_response(jsonify(responseObject), 403)


class LogoutApi(Resource):
    """
    Logout Resource
    """

    def post(self):
        # get auth token
        auth_header = request.headers.get("Authorization")
        if auth_header:
            auth_token = auth_header.split(" ")[1]
        else:
            auth_token = ""
        if auth_token:
            resp = User.decode_auth_token(auth_token)
            if isinstance(resp, dict):
                # mark the token as blacklisted
                blacklist_token = BlacklistToken(token=auth_token)
                try:
                    # insert the token
                    db.session.add(blacklist_token)
                    db.session.commit()
                    responseObject = {
                        "status": "success",
                        "message": "Successfully logged out.",
                    }
                    return make_response(jsonify(responseObject), 200)
                except Exception as e:
                    responseObject = {"status": "fail", "message": e}
                    return make_response(jsonify(responseObject), 200)
            else:
                responseObject = {"status": "fail", "message": resp}
                return make_response(jsonify(responseObject), 401)
        else:
            responseObject = {
                "status": "fail",
                "message": "Provide a valid auth token.",
            }
            return make_response(jsonify(responseObject), 403)
