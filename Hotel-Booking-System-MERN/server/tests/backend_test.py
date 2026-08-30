import os
from pathlib import Path
import requests

BASE_URL = next(x.split('=', 1)[1].strip() for x in Path('/app/frontend/.env').read_text().splitlines() if x.startswith('REACT_APP_BACKEND_URL=')).rstrip('/')

def test_root_and_seeded_hotels():
    assert requests.get(f'{BASE_URL}/api/').json()['message'] == 'HOTELBOOK API is ready'
    hotels = requests.get(f'{BASE_URL}/api/hotels').json()
    assert len(hotels) == 10
    prices = [h['startingPrice'] for h in requests.get(f'{BASE_URL}/api/hotels?sort=price-low').json()]
    assert prices == sorted(prices)

def test_admin_login_cookie_and_me():
    s = requests.Session()
    r = s.post(f'{BASE_URL}/api/auth/login', json={'email':'admin@hotelbook.com','password':'Hotelbook@123'})
    assert r.status_code == 200 and r.json()['role'] == 'admin'
    assert 'hotelbook_token' in s.cookies
    assert s.get(f'{BASE_URL}/api/auth/me').json()['email'] == 'admin@hotelbook.com'

def test_booking_validation_and_demo_booking():
    s = requests.Session()
    assert s.post(f'{BASE_URL}/api/auth/login', json={'email':'admin@hotelbook.com','password':'Hotelbook@123'}).status_code == 200
    payload = {'hotelId':'hotel-1','roomId':'hotel-1-room-1','checkIn':'2099-06-10','checkOut':'2099-06-13','guests':2,'guestName':'QA Admin','guestEmail':'admin@hotelbook.com','guestPhone':'9999999999'}
    r = s.post(f'{BASE_URL}/api/bookings', json=payload)
    assert r.status_code == 200
    b = r.json()
    assert b['nights'] == 3 and b['subtotal'] == 555 and b['paymentStatus'] == 'demo'
    assert b['totalAmount'] == 649.35
    assert any(x['id'] == b['id'] for x in s.get(f'{BASE_URL}/api/bookings/my').json())