from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse, RedirectResponse
import json
from kiteconnect import KiteConnect
from fyers_apiv3 import fyersModel

router = APIRouter(
    prefix="/login",
    tags=["login"],
    responses={404: {"description": "Not found"}}
)
templates = Jinja2Templates(directory="templates")

def get_kite_broker_app_config():
    with open('config/kite_app.json', 'r') as brokerapp:
        data = json.load(brokerapp)
    return data
def get_fyers_broker_app_config():
    with open('config/fyers_app.json', 'r') as brokerapp:
        data = json.load(brokerapp)
    return data


kite_app_config = get_kite_broker_app_config()
fyers_app_config = get_fyers_broker_app_config()

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/zerodha", response_class=RedirectResponse)
async def zerodha(request: Request):
    api_key = kite_app_config['api_key']
    kite = KiteConnect(api_key=api_key)
    url = kite.login_url()
    print(url)
    return RedirectResponse(url)

@router.get("/zerodha_callback", response_class=RedirectResponse)
async def zerodha_callback(request: Request):
    request_token = request.query_params.get("request_token")
    # print(request_token)
    action = request.query_params.get("action")
    status = request.query_params.get("status")
    kite = KiteConnect(api_key=kite_app_config['api_key'])
    new_session_data = kite.generate_session(request_token=request_token, api_secret=kite_app_config['api_secret'])
    # print(f"new_session_data: {new_session_data}")
    # print(f"User ID: {new_session_data['user_id']}, {new_session_data['user_name']} Connected!")
    access_token = new_session_data["access_token"]
    refresh_token = new_session_data["refresh_token"]
    kite.set_access_token(access_token)
    config_data = {
        'access_token': access_token,
        'refresh_token': refresh_token,
    }
    with open('config/zerodha.json', 'w') as jsonfile:
        json.dump(config_data, jsonfile, indent=4)
    return RedirectResponse("/login")

@router.get("/fyers", response_class=RedirectResponse)
async def zerodha(request: Request):
    session = fyersModel.SessionModel(
        client_id=fyers_app_config['api_key'],
        secret_key=fyers_app_config['api_secret'],
        redirect_uri="https://iamlucky.co.in/login/fyers_callback",
        response_type="code"
    )
    url = session.generate_authcode()
    return RedirectResponse(url)

@router.get("/fyers_callback", response_class=RedirectResponse)
async def fyers_callback(request: Request):
    auth_code = request.query_params.get("auth_code")
    session = fyersModel.SessionModel(
        client_id=fyers_app_config['api_key'],
        secret_key=fyers_app_config['api_secret'],
        redirect_uri="https://iamlucky.co.in/login/fyers_callback",
        response_type="code",
        grant_type="authorization_code"
    )

    # Set the authorization code in the session object
    session.set_token(auth_code)

    # Generate the access token using the authorization code
    response = session.generate_token()

    access_token = response['access_token']
    config_data = {
        'auth_code': auth_code,
        'access_token': access_token
    }
    with open('config/fyers.json', 'w') as jsonfile:
        json.dump(config_data, jsonfile, indent=4)
    # with open('../Research/config/fyers.json', 'w') as jsonfile:
    #     json.dump(config_data, jsonfile, indent=4)
    with open('../fetch_options_data/config/fyers.json', 'w') as jsonfile:
        json.dump(config_data, jsonfile, indent=4)
    return RedirectResponse("/login")