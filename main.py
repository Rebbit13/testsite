import json

from pydantic import BaseModel, ValidationError
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlite3 import IntegrityError
from models import Session, Customer

app = FastAPI()


class RequestBody(BaseModel):
    session: Session
    customer: Customer = None


async def parse_request_session():
    pass


@app.get("/web/api/token")
async def token():
    """
    the path to get token and register new session
    :return: json {"session": {"id": session.id, "token": session.token}}
    """
    session = Session.create()
    return {"session": {"id": session.id, "token": session.token}}


@app.get("/web/api/auth")
async def auth(request: Request):
    """
    the path to auth to the site by password and phone number
    :param request: in body json: {"session": {"id": session.id, "token": session.token}
                                   "customer: {"telephone": customer.telephone, "password": customer.password}}
    :return: response 400 if json data incorrect + error in json, 401 if session is dead + session in json,
    403 if password is incorrect or user is not found, 200 if auth ok + customer in json,

    """
    # check session live and parse json
    body = await request.body()
    try:
        body = RequestBody.parse_raw(body.decode('utf-8'))
    except ValidationError as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content=e.json())
    check = body.session.check_session_live()
    if check is False:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED,
                            content=json.dumps({"session": {"id": body.session.id,
                                                            "authorized": body.session.authorized}}))
    # check password
    password_valid = body.customer.check_password(body.customer.password)
    if password_valid is False:
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN)
    else:
        body.session.auth(body.customer.id)
        return JSONResponse(status_code=status.HTTP_200_OK, content={"customer": dict(body.customer)})


@app.post("/web/api/registration")
async def registration(request: Request):
    """
    the method to register new customer by telephone, name, password
    :param request: in body json: {"session": {"id": session.id, "token": session.token}
                                   "customer: {"telephone": customer.telephone,
                                               "password": customer.password
                                               "name": customer.name
                                               another attr: customer.another_attr}}
    :return: response 400 if json data incorrect + error in json, 401 if session is dead + session in json,
    405 if telephone not unique + error in json, 400 if customer data not found + error in json,
    200 if auth ok + new customer in json
    """
    # check session live and parse json
    body = await request.body()
    try:
        body = RequestBody.parse_raw(body.decode('utf-8'))
    except ValidationError as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content=e.json())
    check = body.session.check_session_live()
    if check is False:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED,
                            content={"session": {"id": body.session.id,
                                     "authorized": body.session.authorized}})
    # register
    if body.customer:
        try:
            body.customer.add()
        except IntegrityError:
            return JSONResponse(status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                                content={"error": "telephone not unique"})
        body.session.auth(body.customer.id)
        return JSONResponse(status_code=status.HTTP_200_OK,
                            content={"customer": dict(body.customer)})
    else:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={"error": "customer data not found"})
