import os
import random
from datetime import datetime, timedelta
from shop import app, db, bcrypt
from shop.customers.models import Register
from shop.products.models import Addproduct, Rate

# List of comments
positive_comments = [
    "Sản phẩm rất tốt, giao hàng nhanh!",
    "Máy dùng mượt, pin trâu, đáng đồng tiền bát gạo.",
    "Thiết kế đẹp, cầm chắc tay, màn hình sắc nét.",
    "Nhân viên tư vấn nhiệt tình, phục vụ chu đáo.",
    "Hàng chính hãng, full box, rất hài lòng.",
    "Màu sắc bên ngoài đẹp hơn trên ảnh, ưng ý lắm.",
    "Giá cả cạnh tranh, chất lượng tuyệt vời.",
    "Sẽ tiếp tục ủng hộ shop trong tương lai.",
    "Sản phẩm vượt ngoài mong đợi của mình.",
    "Tốt trong tầm giá, nên mua nha mọi người."
]

negative_comments = [
    "Hơi thất vọng, pin không được như quảng cáo.",
    "Giao hàng hơi lâu, đóng gói chưa được cẩn thận lắm.",
    "Máy thỉnh thoảng hơi lag khi chạy tác vụ nặng.",
    "Camera chụp đêm chưa được tốt lắm.",
    "Giá hơi cao so với các bên khác.",
    "Phụ kiện đi kèm hơi ít.",
    "Màu sắc không giống như mình nghĩ.",
    "Loa hơi bé, nghe nhạc không sướng lắm.",
    "Phần mềm thỉnh thoảng có lỗi vặt.",
    "Chế độ bảo hành cần cải thiện hơn."
]

def seed_data():
    with app.app_context():
        print("Starting seeding process...")

        # 1. Create 20 users
        users = []
        for i in range(1, 21):
            username = f"guest{i}"
            email = f"guest{i}@gmail.com"
            # Use query with case-insensitive for email if needed, but here simple is fine
            existing_user = Register.objects(email=email).first()
            
            if not existing_user:
                # Password is '1'
                hashed_password = bcrypt.generate_password_hash("1").decode('utf-8')
                user = Register(
                    username=username,
                    email=email,
                    password=hashed_password,
                    first_name="Guest",
                    last_name=str(i),
                    phone_number=f"098765432{i:02d}",
                    gender="Male"
                )
                user.save()
                users.append(user)
                print(f"Created user: {username}")
            else:
                users.append(existing_user)
                print(f"User {username} already exists.")

        # 2. Get all products
        products = Addproduct.objects.all()
        print(f"Found {len(products)} products.")

        # 3. Create reviews for each product
        for product in products:
            # Check how many reviews already exist
            existing_count = Rate.objects(product=product).count()
            needed = 10 - existing_count
            
            if needed > 0:
                print(f"Seeding {needed} reviews for product: {product.name}")
                # Pick unique users from the 20 available
                shuffled_users = list(users)
                random.shuffle(shuffled_users)
                
                # Get IDs of users who already reviewed this product to avoid duplicates if possible
                already_reviewed_ids = Rate.objects(product=product).scalar('user_id')
                
                count_added = 0
                for user in shuffled_users:
                    if str(user.id) in already_reviewed_ids:
                        continue
                    
                    if count_added >= needed:
                        break
                        
                    # Randomize praise vs criticism (e.g. 70% positive, 30% negative)
                    is_positive = random.random() > 0.3
                    
                    if is_positive:
                        desc = random.choice(positive_comments)
                        rate_number = random.randint(4, 5)
                    else:
                        desc = random.choice(negative_comments)
                        rate_number = random.randint(1, 3)
                    
                    # Random date within last 30 days
                    random_days = random.randint(0, 30)
                    random_time = datetime.utcnow() - timedelta(days=random_days)
                    
                    rate = Rate(
                        product=product,
                        user_id=str(user.id),
                        desc=desc,
                        rate_number=rate_number,
                        time=random_time
                    )
                    rate.save()
                    count_added += 1
                
                print(f"Added {count_added} reviews for {product.name}")
            else:
                print(f"Product {product.name} already has {existing_count} reviews. Skipping.")

        print("\nSeeding completed successfully!")
        print(f"Accounts: guest1@gmail.com to guest20@gmail.com")
        print(f"Password for all: 1")

if __name__ == "__main__":
    seed_data()
