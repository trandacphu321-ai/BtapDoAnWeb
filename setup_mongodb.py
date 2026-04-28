import pymongo
from pymongo.errors import CollectionInvalid

try:
    print("Đang kết nối tới MongoDB Atlas...")
    # Chuỗi kết nối MongoDB do bạn cung cấp
    MONGO_URI = "mongodb+srv://dacphutran04_db_user:Trandacphu%40710@cluster0.vpx5fan.mongodb.net/"
    client = pymongo.MongoClient(MONGO_URI)
    
    # Khởi tạo hoặc chọn Database tên là 'mobile_store'
    db = client['mobile_store'] 
    print("Kết nối thành công! Đang tiến hành cài đặt Database Mô Hình Bán Đồ Điện Tử...")

    # =========================================================
    # 1. Collection Users (Quản lý khách hàng)
    # =========================================================
    user_schema = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["username", "email", "password"],
            "properties": {
                "username": {"bsonType": "string", "description": "Tên đăng nhập bị bắt buộc"},
                "email": {"bsonType": "string", "pattern": "^.+@.+$", "description": "Định dạng Email chuẩn"},
                "password": {"bsonType": "string", "description": "Mật khẩu"},
                "profile": {
                    "bsonType": "object",
                    "properties": {
                        "name": {"bsonType": "string"},
                        "phone": {"bsonType": "string"},
                        "address": {"bsonType": "string"}
                    }
                }
            }
        }
    }
    try:
        db.create_collection("users", validator=user_schema)
        print("  --> Tạo bảng 'users' thành công")
    except CollectionInvalid:
        db.command("collMod", "users", validator=user_schema)
        print("  --> Đã cập nhật Schema cho bảng 'users'")

    # =========================================================
    # 2. Collection Products (Đồ điện tử: Cấu hình là trọng tâm)
    # =========================================================
    product_schema = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["name", "category", "price", "stock"],
            "properties": {
                "name": {"bsonType": "string", "description": "Tên thiết bị (Vd: iPhone, Macbook...)"},
                "brand": {"bsonType": "string", "description": "Thương hiệu (Apple, Samsung)"},
                "category": {"bsonType": "string", "description": "Loại: Điện thoại, Laptop, Phụ kiện"},
                "price": {"bsonType": "number", "minimum": 0, "description": "Giá thiết bị phải >= 0"},
                "discount": {"bsonType": "int", "minimum": 0, "maximum": 100},
                "stock": {"bsonType": "int", "minimum": 0, "description": "Tồn kho thực tế"},
                "images": {"bsonType": "array", "items": {"bsonType": "string"}},
                
                # TÙY CHỈNH DÀNH RIÊNG CHO ĐỒ ĐIỆN TỬ
                "specs": {
                    "bsonType": "object",
                    "description": "Thông số kỹ thuật cực kỳ quan trọng cho đồ công nghệ",
                    "properties": {
                        "cpu": {"bsonType": "string", "description": "Vi xử lý (Chip)"},
                        "ram": {"bsonType": "string", "description": "Bộ nhớ trong (Dung lượng và chuẩn)"},
                        "storage": {"bsonType": "string", "description": "Ổ cứng (Ví dụ 512GB SSD NVMe)"},
                        "screen": {"bsonType": "string", "description": "Thông số màn hình hiển thị"},
                        "battery": {"bsonType": "string", "description": "Dung lượng pin"},
                        "camera": {"bsonType": "string", "description": "Độ phân giải Camera"}
                    }
                }
            }
        }
    }
    try:
        db.create_collection("products", validator=product_schema)
        print("  --> Tạo bảng 'products' chuẩn Điện tử thành công")
    except CollectionInvalid:
        db.command("collMod", "products", validator=product_schema)
        print("  --> Đã cập nhật Schema cho thiết bị công nghệ")

    # =========================================================
    # 3. Thêm dữ liệu mẫu vào Products
    # =========================================================
    sample_products = [
        {
            "name": "iPhone 15 Pro Max",
            "brand": "Apple",
            "category": "Điện thoại di động",
            "price": 29000000.0,
            "discount": 5,
            "stock": 50,
            "images": ["iphone15promax_1.jpg", "iphone15promax_2.jpg"],
            "specs": {
                "cpu": "Apple A17 Pro (3 nm)",
                "ram": "8GB LPDDR5",
                "storage": "256GB NVMe",
                "screen": "6.7 inch Super Retina XDR OLED, 120Hz",
                "battery": "4422 mAh, Sạc nhanh 27W",
                "camera": "Chính 48MP, Phụ 12MP"
            }
        },
        {
            "name": "Laptop Asus ROG Strix G15",
            "brand": "Asus",
            "category": "Laptop Gaming",
            "price": 32000000.0,
            "discount": 10,
            "stock": 15,
            "images": ["rog_g15_front.jpg"],
            "specs": {
                "cpu": "AMD Ryzen 7 6800H",
                "ram": "16GB DDR5 4800MHz",
                "storage": "512GB SSD NVMe PCIe 4.0",
                "screen": "15.6 inch FHD 144Hz IPS",
                "battery": "90WHrs, 4S1P, 4-cell Li-ion",
                "camera": "720P HD Webcam"
            }
        }
    ]
    
    # Reset products để chèn lại data mẫu (Xóa dữ liệu cũ nếu chạy lại kịch bản)
    db.products.delete_many({})
    db.products.insert_many(sample_products)
    print("\n✅ Đã import dữ liệu mẫu (Điện Thoại & Laptop) vào MongoDB của bạn!")

    print("\n[+] Hoàn tất! Danh sách các Collection hiện tại trong cluster của bạn:")
    for coll in db.list_collection_names():
        print("   -", coll)

except Exception as e:
    print(f"❌ Có lỗi xảy ra trong quá trình thiết lập: {e}")
