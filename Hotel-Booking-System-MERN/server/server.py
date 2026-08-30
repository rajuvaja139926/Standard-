from fastapi import FastAPI, APIRouter, HTTPException, Depends, Response, Cookie
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timezone, timedelta
from typing import Optional
from pathlib import Path
import os, uuid, jwt, bcrypt, logging

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')
mongo_url = os.environ['MONGO_URL']; db_name = os.environ['DB_NAME']
client = AsyncIOMotorClient(mongo_url); db = client[db_name]
app = FastAPI(title='HOTELBOOK API', version='1.0.0', docs_url='/api-docs')
api = APIRouter(prefix='/api')
JWT_SECRET = os.environ.get('JWT_SECRET', 'hotelbook-development-secret')

IMAGES = [
 'https://images.unsplash.com/photo-1564501049412-61c2a3083791?auto=format&fit=crop&w=1200&q=85',
 'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=85',
 'https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1200&q=85',
 'https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=1200&q=85',
]
HOTELS = [
 ('The Fern Residency','Ahmedabad','Ashram Road','A calm urban stay close to the riverfront and the city’s best dining.',4.8,320,185),
 ('Regenta Central','Rajkot','Kalawad Road','Warm hospitality, thoughtful rooms and easy access to Rajkot’s business district.',4.6,210,145),
 ('The Harbor House','Mumbai','Colaba','A polished coastal base for gallery walks, late dinners and South Mumbai mornings.',4.7,486,260),
 ('Aurelia Courtyard','Delhi','Aerocity','A quiet, design-forward retreat minutes from the airport and central Delhi.',4.9,540,225),
 ('Amber Palace Hotel','Jaipur','C-Scheme','Heritage-inspired details meet modern comfort in the heart of the Pink City.',4.7,388,175),
 ('Solara Beach Resort','Goa','Candolim','Sunlit rooms, a generous pool and the shoreline just outside your door.',4.8,612,310),
 ('Mango Tree Suites','Bangalore','Indiranagar','A leafy boutique stay for slow breakfasts, work trips and weekend discoveries.',4.5,198,165),
 ('The Nizam House','Hyderabad','Banjara Hills','Refined rooms and gracious service in Hyderabad’s elegant hillside quarter.',4.6,275,155),
 ('Lakeview Haveli','Udaipur','Lake Pichola','Wake up to storybook lake views, courtyards and Rajasthan’s signature welcome.',4.9,442,280),
 ('Surat Loom Hotel','Surat','Athwa','A fresh, comfortable address for food lovers and the city’s textile quarter.',4.4,156,120),
]

def clean(doc):
    if not doc: return None
    doc = dict(doc); doc.pop('_id', None)
    for key in ('createdAt','updatedAt'):
        if isinstance(doc.get(key), datetime): doc[key] = doc[key].isoformat()
    return doc

def token_for(user):
    return jwt.encode({'sub': user['id'], 'role': user['role'], 'exp': datetime.now(timezone.utc)+timedelta(days=3)}, JWT_SECRET, algorithm='HS256')

async def current_user(hotelbook_token: Optional[str] = Cookie(None)):
    if not hotelbook_token: raise HTTPException(401, 'Please sign in to continue')
    try:
        payload = jwt.decode(hotelbook_token, JWT_SECRET, algorithms=['HS256'])
        user = await db.users.find_one({'id': payload['sub']}, {'_id':0})
        if not user or user.get('isBlocked'): raise HTTPException(401, 'Account unavailable')
        return user
    except jwt.PyJWTError: raise HTTPException(401, 'Session expired')

async def admin_user(user=Depends(current_user)):
    if user.get('role') != 'admin': raise HTTPException(403, 'Admin access required')
    return user

class Register(BaseModel):
    name: str; email: EmailStr; phone: str; password: str
class Login(BaseModel): email: EmailStr; password: str
class BookingIn(BaseModel):
    hotelId: str; roomId: str; checkIn: str; checkOut: str; guests: int = 1
    guestName: str; guestEmail: EmailStr; guestPhone: str
class ReviewIn(BaseModel): hotelId: str; rating: int = Field(ge=1, le=5); comment: str

@app.on_event('startup')
async def seed():
    if await db.hotels.count_documents({}) == 0:
        now = datetime.now(timezone.utc).isoformat()
        for i, (name, city, location, desc, rating, reviews, price) in enumerate(HOTELS):
            hid = f'hotel-{i+1}'
            hotel = {'id':hid,'name':name,'city':city,'location':location,'description':desc,'rating':rating,'reviews':reviews,'images':[IMAGES[i%4],IMAGES[(i+1)%4],IMAGES[(i+2)%4]],'amenities':['Wi-Fi','Breakfast','Parking','Pool' if i%2==0 else 'Gym'],'checkInTime':'2:00 PM','checkOutTime':'11:00 AM','cancellationPolicy':'Free cancellation up to 48 hours before check-in.','createdAt':now}
            await db.hotels.insert_one(hotel)
            for j, typ in enumerate(['Standard Room','Deluxe Room','Premium Suite']):
                await db.rooms.insert_one({'id':f'{hid}-room-{j+1}','hotelId':hid,'roomType':typ,'description':'Comfortable room with considered details and a restful city stay.','pricePerNight':price + j*55,'capacity':2+j,'bedType':'King bed' if j else 'Queen bed','amenities':['Air conditioning','Smart TV','Work desk'],'available':True})
    if not await db.users.find_one({'email':'admin@hotelbook.com'}):
        hashed = bcrypt.hashpw(b'Hotelbook@123', bcrypt.gensalt()).decode()
        await db.users.insert_one({'id':'user-admin','name':'Hotelbook Admin','email':'admin@hotelbook.com','phone':'9999999999','password':hashed,'role':'admin','isBlocked':False,'createdAt':datetime.now(timezone.utc).isoformat()})

@api.get('/')
async def root(): return {'message':'HOTELBOOK API is ready'}

@api.post('/auth/register')
async def register(data: Register, response: Response):
    if await db.users.find_one({'email':data.email}): raise HTTPException(400,'Email already registered')
    user={'id':str(uuid.uuid4()),'name':data.name,'email':data.email,'phone':data.phone,'password':bcrypt.hashpw(data.password.encode(),bcrypt.gensalt()).decode(),'role':'user','isBlocked':False,'createdAt':datetime.now(timezone.utc).isoformat()}
    await db.users.insert_one(user); safe={k:v for k,v in user.items() if k!='password'}; response.set_cookie('hotelbook_token',token_for(safe),httponly=True,samesite='lax'); return safe

@api.post('/auth/login')
async def login(data: Login, response: Response):
    user=await db.users.find_one({'email':data.email},{'_id':0})
    if not user or not bcrypt.checkpw(data.password.encode(),user['password'].encode()): raise HTTPException(401,'Invalid email or password')
    if user.get('isBlocked'): raise HTTPException(403,'This account is blocked')
    safe={k:v for k,v in user.items() if k!='password'}; response.set_cookie('hotelbook_token',token_for(safe),httponly=True,samesite='lax'); return safe

@api.post('/auth/logout')
async def logout(response: Response): response.delete_cookie('hotelbook_token'); return {'message':'Logged out'}
@api.get('/auth/me')
async def me(user=Depends(current_user)): return user

@api.get('/hotels')
async def hotels(search: str='', city: str='', minPrice: int=0, maxPrice: int=1000, rating: float=0, sort: str='popular'):
    query={}
    if city: query['city']={'$regex':city,'$options':'i'}
    if search: query['$or']=[{'name':{'$regex':search,'$options':'i'}},{'city':{'$regex':search,'$options':'i'}},{'location':{'$regex':search,'$options':'i'}}]
    docs=await db.hotels.find(query,{'_id':0}).to_list(100); result=[]
    for h in docs:
        room=await db.rooms.find_one({'hotelId':h['id'],'pricePerNight':{'$gte':minPrice,'$lte':maxPrice}},{'_id':0})
        if room and h['rating']>=rating: result.append({**h,'startingPrice':room['pricePerNight']})
    if sort=='price-low': result.sort(key=lambda x:x['startingPrice'])
    if sort=='price-high': result.sort(key=lambda x:x['startingPrice'],reverse=True)
    if sort=='rating': result.sort(key=lambda x:x['rating'],reverse=True)
    return result

@api.get('/hotels/{hotel_id}')
async def hotel_detail(hotel_id: str):
    hotel=clean(await db.hotels.find_one({'id':hotel_id},{'_id':0}))
    if not hotel: raise HTTPException(404,'Hotel not found')
    hotel['rooms']=await db.rooms.find({'hotelId':hotel_id},{'_id':0}).to_list(20); hotel['reviewsList']=await db.reviews.find({'hotelId':hotel_id},{'_id':0}).sort('createdAt',-1).to_list(20); return hotel

@api.post('/bookings')
async def create_booking(data: BookingIn, user=Depends(current_user)):
    hotel=await db.hotels.find_one({'id':data.hotelId},{'_id':0}); room=await db.rooms.find_one({'id':data.roomId},{'_id':0})
    if not hotel or not room: raise HTTPException(404,'Hotel or room not found')
    start=datetime.fromisoformat(data.checkIn); end=datetime.fromisoformat(data.checkOut); nights=(end-start).days
    if nights<1: raise HTTPException(400,'Check-out must be after check-in')
    conflict=await db.bookings.find_one({'roomId':data.roomId,'bookingStatus':'confirmed','checkIn':{'$lt':data.checkOut},'checkOut':{'$gt':data.checkIn}})
    if conflict: raise HTTPException(409,'This room is no longer available for those dates')
    subtotal=room['pricePerNight']*nights; tax=round(subtotal*.12,2); fee=round(subtotal*.05,2); bid='HB-'+uuid.uuid4().hex[:8].upper()
    booking={'id':str(uuid.uuid4()),'bookingId':bid,'userId':user['id'],'hotelId':hotel['id'],'roomId':room['id'],'hotelName':hotel['name'],'hotelImage':hotel['images'][0],'roomType':room['roomType'],'checkIn':data.checkIn,'checkOut':data.checkOut,'guests':data.guests,'guestDetails':{'name':data.guestName,'email':data.guestEmail,'phone':data.guestPhone},'nights':nights,'pricePerNight':room['pricePerNight'],'subtotal':subtotal,'tax':tax,'serviceFee':fee,'totalAmount':subtotal+tax+fee,'bookingStatus':'confirmed','paymentStatus':'demo','createdAt':datetime.now(timezone.utc).isoformat()}
    await db.bookings.insert_one(booking); return clean(booking)

@api.get('/bookings/my')
async def my_bookings(user=Depends(current_user)): return await db.bookings.find({'userId':user['id']},{'_id':0}).sort('createdAt',-1).to_list(50)
@api.get('/bookings/{booking_id}')
async def booking_detail(booking_id: str,user=Depends(current_user)):
    b=await db.bookings.find_one({'$or':[{'id':booking_id},{'bookingId':booking_id}]},{'_id':0})
    if not b or (b['userId']!=user['id'] and user['role']!='admin'): raise HTTPException(404,'Booking not found')
    return b
@api.put('/bookings/{booking_id}/cancel')
async def cancel_booking(booking_id: str,user=Depends(current_user)):
    b=await db.bookings.find_one({'id':booking_id,'userId':user['id']},{'_id':0})
    if not b: raise HTTPException(404,'Booking not found')
    await db.bookings.update_one({'id':booking_id},{'$set':{'bookingStatus':'cancelled'}}); return {'message':'Booking cancelled'}
@api.get('/bookings/{booking_id}/receipt')
async def receipt(booking_id: str,user=Depends(current_user)):
    b=await booking_detail(booking_id,user); text=f'HOTELBOOK\nBooking Confirmation\n\nBooking ID: {b["bookingId"]}\nGuest: {b["guestDetails"]["name"]}\nHotel: {b["hotelName"]}\nRoom: {b["roomType"]}\nCheck-in: {b["checkIn"]}\nCheck-out: {b["checkOut"]}\nGuests: {b["guests"]}\nNights: {b["nights"]}\nTotal Paid: ₹{b["totalAmount"]}\nPayment: DEMO PAYMENT'
    return Response(content=text,media_type='application/pdf',headers={'Content-Disposition':f'attachment; filename={b["bookingId"]}.pdf'})

@api.post('/reviews')
async def review(data: ReviewIn,user=Depends(current_user)):
    eligible=await db.bookings.find_one({'userId':user['id'],'hotelId':data.hotelId,'bookingStatus':'confirmed'},{'_id':0})
    if not eligible: raise HTTPException(403,'Complete a stay before reviewing')
    doc={'id':str(uuid.uuid4()),'hotelId':data.hotelId,'userId':user['id'],'userName':user['name'],'rating':data.rating,'comment':data.comment,'createdAt':datetime.now(timezone.utc).isoformat()}; await db.reviews.insert_one(doc); return clean(doc)

@api.get('/admin/dashboard')
async def dashboard(user=Depends(admin_user)):
    revenue = 0
    async for booking in db.bookings.find({'bookingStatus':'confirmed'}, {'totalAmount':1, '_id':0}):
        revenue += booking.get('totalAmount', 0)
    return {'users':await db.users.count_documents({}),'hotels':await db.hotels.count_documents({}),'rooms':await db.rooms.count_documents({}),'bookings':await db.bookings.count_documents({}),'revenue':revenue}
@api.get('/admin/bookings')
async def admin_bookings(user=Depends(admin_user)): return await db.bookings.find({}, {'_id':0}).sort('createdAt',-1).to_list(100)

app.include_router(api)
app.add_middleware(CORSMiddleware,allow_credentials=True,allow_origins=[],allow_origin_regex='.*',allow_methods=['*'],allow_headers=['*'])
logging.basicConfig(level=logging.INFO)
@app.on_event('shutdown')
async def shutdown(): client.close()