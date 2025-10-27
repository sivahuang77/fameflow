import sqlite3
import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, Dict, List

# --- Pydantic Models ---

class SocialAccount(BaseModel):
    id: int
    platform_name: str
    account_id: Optional[str] = None
    display_name: Optional[str] = None
    url: Optional[str] = None

class InfluencerBase(BaseModel):
    id: int
    real_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

class Influencer(InfluencerBase):
    compensation_preference: Optional[str] = None
    personal_preference: Optional[str] = None
    notes: Optional[str] = None
    tone_prompt: Optional[str] = None
    personality_analysis: Optional[str] = None
    business_history: Optional[str] = None
    recent_report: Optional[str] = None
    social_accounts: List[SocialAccount] = []

class Post(BaseModel):
    id: int
    post_content: Optional[str] = None
    post_url: Optional[str] = None
    scraped_at: str
    ai_sentiment: Optional[str] = None

class InfluencerCreate(BaseModel):
    real_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    compensation_preference: Optional[str] = None
    personal_preference: Optional[str] = None
    notes: Optional[str] = None
    tone_prompt: Optional[str] = None
    personality_analysis: Optional[str] = None

class InfluencerUpdate(InfluencerCreate):
    pass

class ProductCreate(BaseModel):
    company: Optional[str] = None
    product_name: str
    specifications: Optional[str] = None
    description: Optional[str] = None
    msrp: Optional[float] = None
    discount_percentage: Optional[float] = None
    notes: Optional[str] = None

class ProductUpdate(ProductCreate): pass

class CustomerCreate(BaseModel):
    company_name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    rep_email: Optional[str] = None
    rep_title: Optional[str] = None
    rep_name: Optional[str] = None
    notes: Optional[str] = None

class CustomerUpdate(CustomerCreate): pass

# --- FastAPI App Initialization ---
app = FastAPI()
DB_PATH = 'influencers.db'
templates = Jinja2Templates(directory="templates")

# --- Database Connection Utility ---
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- HTML Page Serving ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# --- Influencer & Post API Endpoints ---

@app.post("/api/influencers", status_code=201, response_model=InfluencerBase)
def create_influencer(influencer: InfluencerCreate):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO influencers (real_name, email, phone, compensation_preference, personal_preference, notes, tone_prompt, personality_analysis)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            influencer.real_name, influencer.email, influencer.phone, 
            influencer.compensation_preference, influencer.personal_preference, 
            influencer.notes, influencer.tone_prompt, influencer.personality_analysis
        ))
        conn.commit()
        new_id = cursor.lastrowid
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
    return {**influencer.model_dump(), "id": new_id}

@app.get("/api/influencers", response_model=List[InfluencerBase])
def get_all_influencers():
    conn = get_db_connection()
    influencers_rows = conn.execute("SELECT id, real_name, email, phone FROM influencers ORDER BY real_name").fetchall()
    conn.close()
    return [dict(row) for row in influencers_rows]

@app.get("/api/influencers/{influencer_id}", response_model=Influencer)
def get_single_influencer(influencer_id: int):
    conn = get_db_connection()
    try:
        influencer_row = conn.execute("SELECT * FROM influencers WHERE id = ?", (influencer_id,)).fetchone()
        if influencer_row is None:
            raise HTTPException(status_code=404, detail="Influencer not found")
        social_accounts_rows = conn.execute("SELECT * FROM social_accounts WHERE influencer_id = ?", (influencer_id,)).fetchall()
        influencer_dict = dict(influencer_row)
        influencer_dict['social_accounts'] = [dict(row) for row in social_accounts_rows]
        return influencer_dict
    finally:
        conn.close()

@app.put("/api/influencers/{influencer_id}")
def update_influencer(influencer_id: int, influencer_data: InfluencerUpdate):
    conn = get_db_connection()
    update_data = influencer_data.model_dump(exclude_unset=True)
    if not update_data:
        return JSONResponse(content={"message": "No update data provided"}, status_code=400)
    
    set_clause = ", ".join([f'{key} = ?' for key in update_data.keys()])
    values = list(update_data.values()) + [influencer_id]
    
    try:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE influencers SET {set_clause} WHERE id = ?", tuple(values))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Influencer not found")
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
    return JSONResponse(content={"message": "Influencer updated successfully"})

@app.delete("/api/influencers/{influencer_id}")
def delete_influencer(influencer_id: int):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM influencers WHERE id = ?", (influencer_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Influencer not found")
    finally:
        conn.close()
    return JSONResponse(content={"message": "Influencer deleted"})

@app.get("/api/posts/influencer/{influencer_id}", response_model=List[Post])
def get_posts_for_influencer(influencer_id: int):
    """Fetches all posts for a specific influencer."""
    conn = get_db_connection()
    posts = conn.execute("""
        SELECT id, post_content, post_url, scraped_at, ai_sentiment 
        FROM posts 
        WHERE influencer_id = ? 
        ORDER BY scraped_at DESC
    """, (influencer_id,)).fetchall()
    conn.close()
    if not posts:
        return []
    return [dict(row) for row in posts]

# --- Product API Endpoints (unchanged) ---
# ... (rest of the file is the same)
@app.post("/api/products", status_code=201)
def create_product(product: ProductCreate):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO products (company, product_name, specifications, description, msrp, discount_percentage, notes) VALUES (?, ?, ?, ?, ?, ?, ?)", (product.company, product.product_name, product.specifications, product.description, product.msrp, product.discount_percentage, product.notes))
        conn.commit()
        new_id = cursor.lastrowid
    finally: conn.close()
    return {"id": new_id, **product.model_dump()}

@app.get("/api/products")
def get_all_products():
    conn = get_db_connection()
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    return products

@app.get("/api/products/{product_id}")
def get_single_product(product_id: int):
    conn = get_db_connection()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()
    if product is None: raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.put("/api/products/{product_id}")
def update_product(product_id: int, product_data: ProductUpdate):
    conn = get_db_connection()
    update_data = product_data.model_dump(exclude_unset=True)
    if not update_data: return JSONResponse(content={"message": "No update data"})
    set_clause = ", ".join([f"{key} = ?" for key in update_data.keys()])
    values = list(update_data.values()) + [product_id]
    try:
        conn.cursor().execute(f"UPDATE products SET {set_clause} WHERE id = ?", tuple(values))
        conn.commit()
    finally: conn.close()
    return JSONResponse(content={"message": "Product updated"})

@app.delete("/api/products/{product_id}")
def delete_product(product_id: int):
    conn = get_db_connection()
    try:
        conn.cursor().execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
    finally: conn.close()
    return JSONResponse(content={"message": "Product deleted"})

# --- Customer API Endpoints (unchanged) ---
@app.post("/api/customers", status_code=201)
def create_customer(customer: CustomerCreate):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO customers (company_name, address, phone, rep_email, rep_title, rep_name, notes) VALUES (?, ?, ?, ?, ?, ?, ?)", (customer.company_name, customer.address, customer.phone, customer.rep_email, customer.rep_title, customer.rep_name, customer.notes))
        conn.commit()
        new_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=409, detail=f"Customer '{customer.company_name}' already exists.")
    finally: conn.close()
    return {"id": new_id, **customer.model_dump()}

@app.get("/api/customers")
def get_all_customers():
    conn = get_db_connection()
    customers = conn.execute("SELECT * FROM customers ORDER BY company_name").fetchall()
    conn.close()
    return customers

@app.get("/api/customers/{customer_id}")
def get_single_customer(customer_id: int):
    conn = get_db_connection()
    customer = conn.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
    conn.close()
    if customer is None: raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@app.put("/api/customers/{customer_id}")
def update_customer(customer_id: int, customer_data: CustomerUpdate):
    conn = get_db_connection()
    update_data = customer_data.model_dump(exclude_unset=True)
    if not update_data: return JSONResponse(content={"message": "No update data"})
    set_clause = ", ".join([f"{key} = ?" for key in update_data.keys()])
    values = list(update_data.values()) + [customer_id]
    try:
        conn.cursor().execute(f"UPDATE customers SET {set_clause} WHERE id = ?", tuple(values))
        conn.commit()
    finally: conn.close()
    return JSONResponse(content={"message": "Customer updated"})

@app.delete("/api/customers/{customer_id}")
def delete_customer(customer_id: int):
    conn = get_db_connection()
    try:
        conn.cursor().execute("DELETE FROM customers WHERE id = ?", (customer_id,))
        conn.commit()
    finally: conn.close()
    return JSONResponse(content={"message": "Customer deleted"})