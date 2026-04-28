import os
import random
import string
from datetime import datetime, timedelta
from shop import app, db, bcrypt
from shop.customers.models import Register
from shop.products.models import Addproduct, Rate

# List of random names for bots
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

# List of LONG comments
long_positive_comments = [
    "Mình đã nhận được hàng sau 2 ngày đặt, đóng gói cực kỳ cẩn thận với 3 lớp chống sốc. Sau 1 tuần sử dụng thì mình thấy máy chạy rất mượt, không hề có hiện tượng giật lag khi chơi game nặng như Genshin Impact. Màn hình của máy thực sự là một điểm cộng lớn với độ sáng cao và màu sắc trung thực, xem phim 4K rất sướng mắt. Pin cũng khá trâu, mình dùng hỗn hợp từ sáng đến tối vẫn còn khoảng 20%. Rất hài lòng với số tiền đã bỏ ra, shop phục vụ rất nhiệt tình!",
    "Lần đầu tiên mua hàng tại shop nhưng cảm thấy cực kỳ an tâm. Sản phẩm đúng như mô tả, nguyên seal 100%. Về hiệu năng thì con chip này quá mạnh mẽ, xử lý mọi tác vụ văn phòng và đồ họa nhẹ đều rất nhanh. Thiết kế của máy sang trọng, viền màn hình mỏng nên trông rất hiện đại. Đặc biệt là bộ phận chăm sóc khách hàng gọi điện tư vấn rất kỹ về cách sạc pin lần đầu để máy bền hơn. Sẽ giới thiệu cho bạn bè và người thân qua đây ủng hộ shop.",
    "Tuyệt vời! Sản phẩm đẹp không tì vết. Mình đã test kỹ các chức năng như camera, loa, mic đều hoạt động hoàn hảo. Camera chụp đêm xuất sắc, khử nhiễu tốt và chi tiết vẫn giữ được độ sắc nét cao. Tốc độ sạc nhanh cũng là một điểm mình rất thích, chỉ mất khoảng 45 phút là đầy pin. Mức giá này theo mình là quá hời cho một siêu phẩm công nghệ như thế này. Cảm ơn shop đã giao hàng nhanh chóng và hỗ trợ nhiệt tình qua zalo.",
    "Phải nói là shop làm việc rất chuyên nghiệp. Từ khâu tư vấn đến lúc nhận hàng đều rất hài lòng. Máy cầm trên tay chắc chắn, các đường hoàn thiện rất tinh xảo. Màn hình tần số quét cao nên cuộn trang cực kỳ mượt mà, không bị mỏi mắt khi sử dụng lâu. Dung lượng lưu trữ lớn giúp mình thoải mái quay phim, chụp ảnh mà không lo hết bộ nhớ. Shop còn tặng kèm nhiều quà tặng hấp dẫn nữa. Đánh giá 5 sao cho chất lượng và dịch vụ!",
    "Đã dùng qua nhiều dòng máy nhưng lần này thực sự ấn tượng với mẫu sản phẩm mới này. Điểm mình thích nhất là hệ thống loa kép âm thanh vòm nghe rất đã, bass chắc và treble rõ. Hiệu năng ổn định, nhiệt độ máy khi sử dụng liên tục cũng không quá nóng. Phần mềm được tối ưu tốt, giao diện sạch sẽ và dễ sử dụng. Giao hàng ở tỉnh mà chỉ mất có 3 ngày là nhận được rồi. Shop tư vấn rất có tâm, trả lời tin nhắn nhanh. Rất đáng mua!"
]

long_negative_comments = [
    "Máy dùng thì ok nhưng mình hơi thất vọng về thời lượng pin, không được như quảng cáo 2 ngày đâu, mình dùng bình thường thì tầm hơn 1 ngày là phải sạc rồi. Hy vọng các bản cập nhật phần mềm sau sẽ tối ưu tốt hơn. Giao hàng ở khu vực mình cũng hơi chậm, shipper không nhiệt tình lắm. Tuy nhiên về chất lượng máy thì vẫn khá ổn trong tầm giá này, thiết kế đẹp và màn hình hiển thị tốt.",
    "Sản phẩm thì đẹp nhưng phần mềm đôi lúc vẫn còn gặp một số lỗi vặt như tự động thoát ứng dụng hoặc thỉnh thoảng mất kết nối wifi nhẹ. Mình đã liên hệ shop và được hướng dẫn reset lại thì thấy đỡ hơn nhưng vẫn chưa triệt để. Điểm cộng là thiết kế rất sang trọng và camera chụp ảnh đẹp. Mong shop phản hồi thêm với nhà sản xuất về các lỗi này để hoàn thiện hơn sản phẩm cho người tiêu dùng.",
    "Về cấu hình thì không có gì để chê nhưng mình thấy máy hơi nóng khi sử dụng các tác vụ nặng liên tục trong thời gian dài. Có lẽ do thiết kế mỏng nên khả năng tản nhiệt chưa thực sự ấn tượng. Phụ kiện đi kèm trong hộp hơi ít, mình phải tự mua thêm củ sạc nhanh bên ngoài. Dù sao thì với mức giá giảm này thì cũng chấp nhận được, nhưng lần sau shop nên tư vấn kỹ hơn về vấn đề nhiệt độ nhé.",
    "Hàng đóng gói chắc chắn nhưng hộp máy hơi móp nhẹ ở góc, chắc do quá trình vận chuyển của bên bưu điện. Kiểm tra bên trong thì máy không sao nên mình vẫn nhận. Sau 3 ngày dùng thì thấy loa thoại thỉnh thoảng hơi nhỏ, phải bật to hết cỡ mới nghe rõ được ở nơi ồn ào. Các tính năng khác thì ổn, thiết kế đẹp, cầm nắm thoải mái. Shop nên làm việc lại với bên đơn vị vận chuyển để bảo quản hàng tốt hơn.",
    "Giá hơi cao một chút so với mặt bằng chung nhưng bù lại bảo hành dài nên mình cũng yên tâm phần nào. Tuy nhiên máy màu trắng dễ bám vân tay và mồ hôi, các bạn nên dùng ốp lưng ngay từ đầu. Hiệu năng chỉ ở mức khá, không quá xuất sắc như kỳ vọng của mình. Giao diện thỉnh thoảng vẫn có độ trễ nhẹ khi mở nhiều ứng dụng cùng lúc. Dịch vụ chăm sóc khách hàng của shop thì tốt, nhiệt tình hỗ trợ giải đáp thắc mắc."
]

def seed_data():
    with app.app_context():
        print("Starting seeding process for 20 NEW random bots...")

        # 1. Create 20 NEW random users
        new_users = []
        for i in range(20):
            full_name = generate_random_name()
            username = generate_random_username()
            email = f"{username}@gmail.com"
            
            # Ensure unique
            while Register.objects(username=username).first() or Register.objects(email=email).first():
                username = generate_random_username()
                email = f"{username}@gmail.com"
                
            hashed_password = bcrypt.generate_password_hash("1").decode('utf-8')
            
            parts = full_name.split(' ')
            first_n = parts[0]
            last_n = ' '.join(parts[1:])
            
            user = Register(
                username=username,
                email=email,
                password=hashed_password,
                first_name=first_n,
                last_name=last_n,
                phone_number=f"03{random.randint(10000000, 99999999)}",
                gender=random.choice(["Nam", "Nữ"])
            )
            user.save()
            new_users.append(user)
            print(f"Created user: {full_name} ({username})")

        # 2. Get all products
        products = Addproduct.objects.all()
        print(f"Found {len(products)} products.")

        # 3. Create 5 MORE long reviews for each product using these new users
        for product in products:
            print(f"Seeding 5 long reviews for product: {product.name}")
            
            # Pick 5 unique users from the 20 new ones
            shuffled_users = list(new_users)
            random.shuffle(shuffled_users)
            
            # Avoid duplicates (though these are new users, so unlikely to have reviewed before)
            already_reviewed_ids = Rate.objects(product=product).scalar('user_id')
            
            count_added = 0
            for user in shuffled_users:
                if str(user.id) in already_reviewed_ids:
                    continue
                
                if count_added >= 5: # Add 5 more long ones
                    break
                    
                is_positive = random.random() > 0.4 # 60% positive
                
                if is_positive:
                    desc = random.choice(long_positive_comments)
                    rate_number = random.randint(4, 5)
                else:
                    desc = random.choice(long_negative_comments)
                    rate_number = random.randint(2, 3)
                
                # Random date within last 15 days (more recent)
                random_days = random.randint(0, 15)
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
            
            print(f"Added {count_added} long reviews for {product.name}")

        print("\nSeeding completed successfully!")
        print(f"20 new random bot accounts created.")

if __name__ == "__main__":
    seed_data()
