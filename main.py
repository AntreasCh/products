from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
import sqlite3
from sqlite3 import Error
from fastapi.middleware.cors import CORSMiddleware

# Add the following code before the endpoints are defined
origins = ["*"]  # Replace this with the list of allowed origins


app = FastAPI()
import requests


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Create the FastAPI object


# Define the exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(content={"details": exc.detail}, status_code=exc.status_code)

@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(content={"details": exc.errors()}, status_code=422)

# Define the Product model
class Product(BaseModel):
    id: Optional[int] = None
    name: str
    price: float
    quantity: int
    type:str
    gender:str
    description:str
    picture_url: Optional[str] = None
    category:str

# Define the function to create a database connection
def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)
    return conn
@app.get("/buyproduct/{product_id}/{product_quantity}")
def buy_product(product_id: int, product_quantity: int):
    with sqlite3.connect("products.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM Product WHERE Product_id = ?", (product_id,))
        product = cur.fetchone()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        if product_quantity > product[2]:
            raise HTTPException(status_code=400, detail="Insufficient product quantity")
        new_quantity = product[2] - product_quantity
        cur.execute("UPDATE Product SET Product_quantity = ? WHERE Product_id = ?", (new_quantity, product_id))
        conn.commit()
        return {"id": product[0], "name": product[1], "quantity": new_quantity}
# Define the endpoint to create a new product
import requests
@app.get("/showcase/{product_id}")
def showcaseproduct(product_id: int):
    conn = create_connection("products.db")
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM Product WHERE Product_id = ?", (product_id,))
        product = cur.fetchone()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return {"id": product[0], "name":product[1], "quantity":product[2], "price":product[3],"type":product[4],"picture_url":product[7],"description":product[6],"category":product[8],"gender":product[5]}


@app.get("/getproduct/{product_id}/{product_quantity}/{user_id}")
def get_product(product_id: int, product_quantity: int, user_id: int ):
    conn = create_connection("products.db")
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM Product WHERE Product_id = ?", (product_id,))
        product = cur.fetchone()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # add item to cart
        cart_item = {"product_id": product[0], "name":product[1], "quantity":product_quantity, "price":product[3],"type":product[4],"picture_url":product[7],"description":product[6],"category":product[8],"gender":product[5]}
        response = requests.post(f"http://localhost:8001/cart/add-item/{user_id}", json=cart_item)

   
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to add item to cart")
        
        return {"id": product[0], "name":product[1], "quantity":product[2], "price":product[3]}


# Define the endpoint to create a new product
class Product(BaseModel):
    id: Optional[int] = None
    name: str
    price: float
    quantity: int
    type: str
    gender: str
    description: str
    picture_url: Optional[str] = None
    category: str

@app.post("/addproducts")
def create_product(product: Product):
    conn = create_connection("products.db")
    with conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Product (Product_id, Product_name, Product_price, Product_quantity, Product_type, Product_gender, Product_description, Picture_url, category) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (product.id, product.name, product.price, product.quantity, product.type, product.gender, product.description, product.picture_url, product.category)
        )
        new_product_id = cur.lastrowid
        return {"id": new_product_id, **product.dict()}



# Define the endpoint to retrieve all products

@app.get("/products", response_model=List[Product])
def read_products():
    conn = create_connection("products.db")
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM Product")
        rows = cur.fetchall()
        products = []
        for row in rows:
            products.append(Product(id=row[0], name=row[1], price=row[3], quantity=row[2], type=row[4],picture_url=row[7],description=row[6],category=row[8],gender=row[5]))
        return products


# Define the root endpoint
@app.get("/")
async def root():
    return {"message": "Hello World"}
@app.delete("/deleteproduct/{product_id}")
def delete_product(product_id: int):
    conn = create_connection("products.db")
    with conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM Product WHERE Product_id = ?", (product_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Product not found")
        return {"message": "Product deleted successfully"}
    
    
@app.put("/updateproduct/{product_id}")
def update_product(product_id: int, product: Product):
    conn = create_connection("products.db")
    with conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE Product SET Product_name=?, Product_price=?, Product_quantity=?, Product_type=?, Product_gender=?, Product_description=?, Picture_url=?, category=? WHERE Product_id=?",
            (product.name, product.price, product.quantity, product.type, product.gender, product.description, product.picture_url, product.category, product_id)
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Product not found")
        product.id = product_id
        return {"message": "Product updated successfully", **product.dict()}


