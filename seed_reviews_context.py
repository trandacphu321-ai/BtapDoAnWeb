import os
import random
import string
from datetime import datetime, timedelta
from shop import app, db, bcrypt
from shop.customers.models import Register
from shop.products.models import Addproduct, Rate, Category

# Names generation logic
first_names = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Phan", "Vũ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý"]
middle_names = ["Văn", "Thị", "Minh", "Anh", "Đức", "Hải", "Quốc", "Thanh", "Tuấn", "Hùng", "Ngọc", "Xuân"]
last_names = ["An", "Bình", "Chương", "Dũng", "Em", "Giang", "Hương", "Khánh", "Linh", "Nam", "Oanh", "Phúc", "Quang", "Sơn", "Thảo", "Uyên", "Việt"]

def generate_random_name():
    fn = random.choice(first_names)
    mn = random.choice(middle_names)
    ln = random.choice(last_names)
    return f"{fn} {mn} {ln}"

def generate_random_username():
    chars = string.ascii_lowercase + string.digits
    return "user_" + ''.join(random.choice(chars) for _ in range(6))

# Context-aware review pool
reviews_pool = {
    "Điện thoại thông minh": {
        "positive": [
            "Màn hình OLED của máy thực sự quá đẹp, độ sáng cao dùng ngoài trời rất rõ. Camera chụp ảnh sắc nét, đặc biệt là chế độ chân dung xóa phông rất tự nhiên. Hiệu năng của chip mới cực kỳ mạnh mẽ, chơi game nặng mà máy vẫn mát.",
            "Thiết kế sang trọng, viền mỏng cầm rất sướng tay. Tốc độ sạc nhanh kinh khủng, chỉ 30 phút là gần đầy pin rồi. Hệ điều hành mượt mà, nhiều tính năng thông minh hỗ trợ công việc rất tốt. Rất hài lòng!",
            "Camera zoom cực xa mà vẫn giữ được độ chi tiết cao, rất thích hợp cho những ai thích chụp ảnh phong cảnh. Pin dùng thoải mái cả ngày dài không lo hết. Shop đóng gói kỹ, giao hàng nhanh chóng."
        ],
        "negative": [
            "Máy dùng tốt nhưng thỉnh thoảng hơi nóng khi quay video 4K lâu. Pin chỉ ở mức đủ dùng 1 ngày, nếu chơi game nhiều thì phải sạc thêm. Hy vọng bản cập nhật tới sẽ tối ưu tốt hơn.",
            "Giá hơi cao so với cấu hình, và không có củ sạc đi kèm trong hộp là một điểm trừ lớn. Tuy nhiên màn hình và camera thì thực sự xuất sắc, không có gì để chê về chất lượng hiển thị."
        ]
    },
    "Máy tính xách tay": {
        "positive": [
            "Bàn phím gõ rất êm, touchpad rộng và nhạy. Màn hình độ phân giải cao, chuẩn màu nên làm đồ họa rất chuẩn xác. Thời lượng pin ấn tượng, làm việc văn phòng cả ngày không cần mang sạc.",
            "Máy cực kỳ mỏng nhẹ, rất thuận tiện cho mình khi phải mang đi làm mỗi ngày. Hiệu năng mạnh mẽ, mở hàng chục tab chrome và phần mềm chuyên dụng vẫn không hề bị lag. Tản nhiệt hoạt động êm ái.",
            "Cấu hình quá khủng trong tầm giá, cân được hết các tựa game AAA hiện nay. Thiết kế gaming nhưng vẫn tinh tế, không quá hầm hố. Màn hình 144Hz chơi game cực mượt, không bị xé hình."
        ],
        "negative": [
            "Quạt tản nhiệt hơi ồn khi chạy các ứng dụng nặng hoặc render video. Vỏ máy dễ bám mồ hôi và dấu vân tay, cần phải vệ sinh thường xuyên. Tổng thể thì máy vẫn rất tốt cho công việc.",
            "Màn hình hơi tối khi dùng ở nơi có ánh sáng mạnh. Loa ngoài âm thanh hơi thiếu bass, nghe nhạc không thực sự ấn tượng. Tuy nhiên về hiệu năng và độ bền thì mình thấy rất ổn."
        ]
    },
    "Đồng hồ thông minh": {
        "positive": [
            "Các tính năng theo dõi sức khỏe rất chính xác, đặc biệt là đo nhịp tim và nồng độ oxy trong máu. Màn hình Always-on Display rất tiện lợi, độ sáng cao. Dây đeo silicon mềm mại, đeo cả ngày không bị cấn tay.",
            "Kết nối với điện thoại rất nhanh và ổn định. Thông báo hiển thị rõ ràng, hỗ trợ tiếng Việt tốt. Nhiều mặt đồng hồ đẹp để thay đổi mỗi ngày. Pin dùng được khoảng 2-3 ngày, khá ổn cho một chiếc smartwatch.",
            "Thiết kế thể thao, năng động và rất bền bỉ. Khả năng kháng nước tốt, mình đi bơi vẫn đeo bình thường không sao cả. GPS bắt sóng nhanh, hỗ trợ rất nhiều chế độ tập luyện chuyên nghiệp."
        ],
        "negative": [
            "Thời lượng pin hơi ngắn nếu bật tất cả các tính năng theo dõi liên tục. Phần mềm thỉnh thoảng có độ trễ nhẹ khi thao tác vuốt chạm nhanh. Mong shop cập nhật thêm nhiều mặt đồng hồ mới.",
            "Kích thước hơi to so với cổ tay nhỏ của mình. Dây đeo theo máy hơi cứng lúc mới dùng, phải đeo một thời gian mới mềm ra được. Các tính năng sức khỏe thì không có gì để phàn nàn."
        ]
    },
    "Tai nghe & Âm thanh": {
        "positive": [
            "Chất lượng âm thanh tuyệt vời, bass sâu và chắc, dải mid rõ ràng. Khả năng chống ồn chủ động (ANC) cực tốt, đeo vào là không gian tĩnh lặng hẳn luôn. Thời lượng pin dùng liên tục được rất lâu.",
            "Thiết kế hiện đại, đeo lâu không bị đau tai hay khó chịu. Kết nối bluetooth 5.3 cực kỳ ổn định, không bị trễ tiếng khi xem phim hay chơi game. Mic thu âm lọc gió tốt, đàm thoại rõ ràng.",
            "Âm thanh vòm rất sống động, nghe nhạc hay xem phim đều cảm giác như đang ở rạp. Hộp sạc nhỏ gọn, dễ dàng mang theo. Cảm ứng trên tai nghe rất nhạy và dễ thao tác. Rất đáng đồng tiền!"
        ],
        "negative": [
            "Phần đệm tai hơi bí nếu đeo liên tục trong thời gian dài vào mùa hè. Ứng dụng điều khiển trên điện thoại thỉnh thoảng bị lỗi không kết nối được với tai nghe. Chất âm thì vẫn rất hay trong tầm giá.",
            "Vỏ hộp sạc dễ bị trầy xước nếu không dùng bao da bảo vệ. Giá hơi chát nhưng chất lượng âm thanh thì thực sự khác biệt hoàn toàn so với các dòng giá rẻ. Mong shop có thêm nhiều chương trình khuyến mãi."
        ]
    }
}

def seed_data():
    with app.app_context():
        print("Cleaning up old reviews...")
        Rate.objects().delete()
        
        print("Starting seeding process for 30 high-quality context-aware bots...")

        # 1. Ensure we have 30 users (using old ones + new ones)
        users = list(Register.objects().all())
        needed_users = 30 - len(users)
        
        if needed_users > 0:
            for i in range(needed_users):
                full_name = generate_random_name()
                username = generate_random_username()
                email = f"{username}@gmail.com"
                hashed_password = bcrypt.generate_password_hash("1").decode('utf-8')
                parts = full_name.split(' ')
                user = Register(
                    username=username, email=email, password=hashed_password,
                    first_name=parts[0], last_name=' '.join(parts[1:]),
                    phone_number=f"03{random.randint(10000000, 99999999)}",
                    gender=random.choice(["Nam", "Nữ"])
                )
                user.save()
                users.append(user)
            print(f"Created {needed_users} more users.")

        # 2. Get all products
        products = Addproduct.objects.all()
        print(f"Found {len(products)} products.")

        # 3. Create 10-15 high-quality reviews per product
        for product in products:
            cat_name = product.category.name if product.category else "Điện thoại thông minh"
            # Fallback if category not in pool
            if cat_name not in reviews_pool:
                cat_name = "Điện thoại thông minh"
                
            pool = reviews_pool[cat_name]
            num_reviews = random.randint(10, 15)
            print(f"Seeding {num_reviews} reviews for {product.name} ({cat_name})")
            
            shuffled_users = list(users)
            random.shuffle(shuffled_users)
            
            for i in range(num_reviews):
                user = shuffled_users[i]
                is_positive = random.random() > 0.25 # 75% positive
                
                if is_positive:
                    desc = random.choice(pool["positive"])
                    rate_number = random.randint(4, 5)
                else:
                    desc = random.choice(pool["negative"])
                    rate_number = random.randint(1, 3)
                
                # Vary dates over last 60 days
                random_days = random.randint(0, 60)
                random_time = datetime.utcnow() - timedelta(days=random_days)
                
                rate = Rate(
                    product=product, user_id=str(user.id),
                    desc=desc, rate_number=rate_number,
                    time=random_time
                )
                rate.save()
                
        print("\nSUCCESS: All reviews have been updated with correct product context!")

if __name__ == "__main__":
    seed_data()
