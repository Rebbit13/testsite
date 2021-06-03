import json

from typing import Optional
from pydantic import BaseModel, ValidationError
from fastapi import FastAPI, Request, status, File, UploadFile, Header
from fastapi.responses import JSONResponse
from sqlite3 import IntegrityError
from models import Session, Customer, Admin, Banner, Product

app = FastAPI()

STATIC_PATH = 'static/img/'


class RequestBody(BaseModel):
    customer: Customer = None
    admin: Admin = None
    banner: Banner = None
    product: Product = None


@app.get("/web/api/token")
async def token():
    """
    the path to get token and register new session
    :return: json {"session": {"id": session.id, "token": session.token}}
    """
    session = Session.create()
    return {"session": {"id": session.id, "token": session.token}}


@app.get("/web/api/auth/client")
async def auth(authorization: Optional[str] = Header(None),
               x_session_token: Optional[str] = Header(None),
               x_session_id: Optional[str] = Header(None)):
    """
    the path to auth to the site by password and phone number
    :param authorization: "telephone: password"
    :param x_session_id: the id of the clint session
    :param x_session_token: the token of the clint session
    :return: response 400 if data incorrect + error in json, 401 if session is dead + session in json,
    403 if password is incorrect or user is not found, 200 if auth ok + customer in json,
    """
    # check session is not dead
    session = Session.find({"id": int(x_session_id), "token": x_session_token})
    check = session.check_session_live()
    if check is False:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED,
                            content=json.dumps({"session": {"id": session.id,
                                                            "authorized": session.authorized}}))
    # check password
    try:
        parse = authorization.split(": ")
        telephone = parse[0]
        password = [1]
    except IndexError:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={"error": "no authorization data found"})
    customer = Customer(telephone=telephone, password=password)
    try:
        password_valid = customer.check_password(customer.password)
    except IntegrityError:
        return JSONResponse(status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                            content={"error": "customer not found"})
    if password_valid is False:
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN)
    else:
        session.auth(customer.id)
        return JSONResponse(status_code=status.HTTP_200_OK, content={"customer": dict(customer)})


@app.get("/web/api/auth/admin")
async def auth(authorization: Optional[str] = Header(None),
               x_session_token: Optional[str] = Header(None),
               x_session_id: Optional[str] = Header(None)):
    """
    the path to auth admin to the site by login and phone number
    :param authorization: "login: password"
    :param x_session_id: the id of the clint session
    :param x_session_token: the token of the clint session
    :return: response 400 if data incorrect + error in json, 401 if session is dead + session in json,
    403 if password is incorrect or admin is not found, 200 if auth ok,
    """
    # check session is not dead
    session = Session.find({"id": int(x_session_id), "token": x_session_token})
    check = session.check_session_live()
    if check is False:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED,
                            content=json.dumps({"session": {"id": session.id,
                                                            "authorized": session.authorized}}))
    # check password
    try:
        parse = authorization.split(": ")
        login = parse[0]
        password = [1]
    except IndexError:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={"error": "no authorization data found"})
    admin = Admin(login=login, password=password)
    try:
        password_valid = admin.check_password()
    except IntegrityError:
        return JSONResponse(status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                            content={"error": "admin not found"})
    if password_valid is False:
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN)
    else:
        session.auth_admin(admin.id)
        return JSONResponse(status_code=status.HTTP_200_OK)


@app.post("/web/api/registration")
async def registration(customer: Customer,
                       x_session_token: Optional[str] = Header(None),
                       x_session_id: Optional[str] = Header(None)):
    """
    the method to register new customer by telephone, name, password
    :param customer: in body json: {"customer: {"telephone": customer.telephone,
                                               "password": customer.password
                                               "name": customer.name}
    :param x_session_id: the id of the clint session
    :param x_session_token: the token of the clint session
    :return: response 400 if json data incorrect + error in json, 401 if session is dead + session in json,
    405 if telephone not unique + error in json, 400 if customer data not found + error in json,
    200 if auth ok + new customer in json
    """
    # check session live
    session = Session.find({"id": int(x_session_id), "token": x_session_token})
    check = session.check_session_live()
    if check is False:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED,
                            content=json.dumps({"session": {"id": session.id,
                                                            "authorized": session.authorized}}))
    # register
    try:
        customer.add()
    except IntegrityError:
        return JSONResponse(status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                            content={"error": "telephone not unique"})
    session.auth(customer.id)
    return JSONResponse(status_code=status.HTTP_200_OK,
                        content={"customer": dict(customer)})


@app.post("/web/api/item/{item}")
async def get_item(item: str,
                   request: Request,
                   x_session_token: Optional[str] = Header(None),
                   x_session_id: Optional[str] = Header(None)):
    """
    method only for admin  to post items to db
    :param item:
    :param request: in body: {type  of item: item in json to add}
    :param x_session_id: the id of the clint session
    :param x_session_token: the token of the clint session
    :return: response 400 if json data incorrect + error in json, 401 if session is dead + session in json,
    200 if item saved + item in json
    """
    # check session live
    session = Session.find({"id": int(x_session_id), "token": x_session_token})
    check = session.check_session_live()
    if check is False:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED,
                            content=json.dumps({"session": {"id": session.id,
                                                            "authorized": session.authorized}}))
    # check if session link to admin
    if session.admin is None:
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN)
    # add item
    body = await request.body()
    try:
        body = RequestBody.parse_raw(body.decode('utf-8'))
    except ValidationError as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content=e.json())
    if item == "banner":
        if body.banner:
            body.banner.pic = STATIC_PATH + "banner/" + body.banner.pic
            body.banner.add()
            return dict(body.banner)
        else:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                                content={"error": "banner data not found"})
    if item == "product":
        if body.product:
            body.product.pic = STATIC_PATH + "product/" + body.product.pic
            body.product.add()
            return dict(body.product)
        else:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                                content={"error": "product data not found"})


@app.get("/web/api/item/{item}/{item_id}")
async def get_item(item: str, item_id,
                   x_session_token: Optional[str] = Header(None),
                   x_session_id: Optional[str] = Header(None)):
    """
    get item by type and id or alias
    :param item: type of the item (for example banner)
    :param item_id: id or alias of the item
    :param x_session_id: the id of the clint session
    :param x_session_token: the token of the clint session
    :return: response 405 if data incorrect + error in json, 401 if session is dead + session in json,
    200 if ok + item in json
    """
    # check session live
    session = Session.find({"id": int(x_session_id), "token": x_session_token})
    check = session.check_session_live()
    if check is False:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED,
                            content=json.dumps({"session": {"id": session.id,
                                                            "authorized": session.authorized}}))
    # find item
    if item == "banner":
        banner = Banner.find({"alias": item_id})
        if banner:
            return dict(banner)
        else:
            return JSONResponse(status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                                content={"error": "banner not found"})
    if item == "product":
        if item_id == 'all':
            list_ = Product().find_many()
            return JSONResponse(status_code=status.HTTP_200_OK,
                                content=dict(list_))
        else:
            product = Product().find_many({'id': item_id})
            if product:
                return dict(product)
            else:
                return JSONResponse(status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                                    content={"error": "product not found"})


@app.post("/web/api/upload/{item}")
async def upload(item: str, image: UploadFile = File(...),
                 x_session_token: Optional[str] = Header(None),
                 x_session_id: Optional[str] = Header(None)):
    """
    get item by type and id or alias
    :param item: type of the item (for example banner)
    :param image: image file
    :param x_session_id: the id of the clint session
    :param x_session_token: the token of the clint session
    :return: response 500 if server cant save file, 401 if session is dead + session in json,
    200 if file saved + filename in json
    """
    # check session live
    session = Session.find({"id": int(x_session_id), "token": x_session_token})
    check = session.check_session_live()
    if check is False:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED,
                            content=json.dumps({"session": {"id": session.id,
                                                            "authorized": session.authorized}}))
    file_name = STATIC_PATH + item + "/" + image.filename.replace(" ", "-")
    try:
        with open(file_name, 'wb+') as f:
            f.write(image.file.read())
            f.close()
    except FileNotFoundError:
        JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return JSONResponse(status_code=status.HTTP_200_OK,
                            content={"file_name": file_name})
