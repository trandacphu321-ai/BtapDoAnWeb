import pandas as pd
import numpy as np
from shop.products.models import Addproduct, UserInteraction

def get_content_based_recommendations(product_id, limit=4):
    """
    Gợi ý sản phẩm tương tự (Content-based Filtering) dựa trên danh mục, hãng và giá.
    Nâng cấp: Thêm trọng số cho hãng và khoảng giá.
    """
    try:
        product = Addproduct.objects(id=product_id).first()
        if not product:
            return []

        # 1. Lấy sản phẩm cùng danh mục
        similar_category = list(Addproduct.objects(
            id__ne=product_id,
            category=product.category,
            stock__gt=0
        ))

        if not similar_category:
            return get_fallback_recommendations(limit)

        # 2. Tính toán điểm tương đồng (Scoring)
        # - Cùng hãng: +10 điểm
        # - Khoảng cách giá (càng gần càng cao): tối đa 10 điểm
        # - Giảm giá: +2 điểm
        scored_products = []
        for p in similar_category:
            score = 0
            # Cùng hãng
            if p.brand == product.brand:
                score += 10
            
            # Tương đồng giá (tính theo tỷ lệ phần trăm chênh lệch)
            price_diff = abs(p.price - product.price) / product.price
            score += max(0, 10 * (1 - price_diff))
            
            # Có giảm giá
            if p.discount > 0:
                score += 2
                
            scored_products.append((p, score))

        # Sắp xếp theo điểm số
        scored_products.sort(key=lambda x: x[1], reverse=True)
        
        return [x[0] for x in scored_products[:limit]]
    except Exception as e:
        print("Content-based Error:", e)
        return get_fallback_recommendations(limit)

def get_collaborative_recommendations(user_id, limit=4):
    """
    Gợi ý cá nhân hóa dựa trên hành vi (Collaborative Filtering).
    Nâng cấp: Phân tích thói quen dựa trên trọng số hành động (View=1, Cart=3, Purchase=5).
    """
    try:
        # Lấy tối đa 2000 tương tác gần nhất để tránh quá tải bộ nhớ và treo máy khi có nhiều dữ liệu
        interactions = UserInteraction.objects().order_by('-timestamp').limit(2000)
        if not interactions:
            return get_fallback_recommendations(limit)

        data = []
        for row in interactions:
            # Gán trọng số thói quen: Xem < Giỏ hàng < Mua
            weight = row.weight
            if row.interaction_type == 'cart': weight = 3
            elif row.interaction_type == 'purchase': weight = 5
            
            data.append({'user_id': row.user_id, 'product_id': row.product_id, 'weight': weight})
            
        df = pd.DataFrame(data)
        if df.empty:
            return get_fallback_recommendations(limit)

        # Nâng cấp: User-Based Collaborative Filtering sử dụng Numpy Cosine Similarity
        # Tạo ma trận User-Product
        user_product_matrix = df.groupby(['user_id', 'product_id'])['weight'].sum().unstack(fill_value=0)
        
        if str(user_id) not in user_product_matrix.index:
            return get_fallback_recommendations(limit)

        # Chuyển DataFrame sang Numpy array để tính toán siêu tốc
        matrix_values = user_product_matrix.values
        
        # Tính chuẩn (norm) của từng user vector để chuẩn bị cho Cosine Similarity
        norms = np.linalg.norm(matrix_values, axis=1)
        norms[norms == 0] = 1e-9 # Tránh lỗi chia cho 0
        normalized_matrix = matrix_values / norms[:, np.newaxis]
        
        # Lấy vị trí của user hiện tại trong ma trận
        user_idx = user_product_matrix.index.get_loc(str(user_id))
        current_user_vector = normalized_matrix[user_idx]
        
        # Tính độ tương đồng (Cosine Similarity) giữa user hiện tại và TẤT CẢ user khác
        # Phép nhân dot product bằng Numpy xử lý hàng chục ngàn dòng trong chớp mắt
        similarities = np.dot(normalized_matrix, current_user_vector)
        
        # Nhân điểm tương đồng vào ma trận ban đầu để có trọng số cuối cùng
        # Người dùng nào càng giống thì điểm sản phẩm họ xem càng có giá trị
        weighted_matrix = matrix_values * similarities[:, np.newaxis]
        
        # Tính tổng điểm dự đoán cho toàn bộ sản phẩm
        product_scores = np.sum(weighted_matrix, axis=0)
        
        # Đưa về dạng Series có index là product_id để dễ thao tác
        product_scores_series = pd.Series(product_scores, index=user_product_matrix.columns)
        
        # Lọc ra các sản phẩm user hiện tại đã xem/mua
        interacted_indices = user_product_matrix.columns[user_product_matrix.loc[str(user_id)] > 0].tolist()
        
        # Loại bỏ các sản phẩm đã xem khỏi danh sách gợi ý
        product_scores_series = product_scores_series.drop(interacted_indices, errors='ignore')
        
        # Lấy top các sản phẩm có điểm cao nhất
        recommendations = product_scores_series[product_scores_series > 0].sort_values(ascending=False).head(limit)
        
        if recommendations.empty:
            # Nếu tất cả các sản phẩm tương tự đã bị loại do đã xem, ta dùng content-based fallback từ code cũ
            pass
            
        top_product_ids = recommendations.index.tolist()
        recommended_items = Addproduct.objects(id__in=top_product_ids, stock__gt=0).all()
        
        # Nếu chưa đủ limit, lấy thêm từ content-based của sản phẩm cuối cùng user xem
        if len(recommended_items) < limit and interacted_indices:
            last_prod_id = interacted_indices[-1]
            extra = get_content_based_recommendations(last_prod_id, limit=limit-len(recommended_items))
            return list(recommended_items) + extra
            
        return list(recommended_items)
        
    except Exception as e:
        print("Collaborative Error:", e)
        return get_fallback_recommendations(limit)

def get_fallback_recommendations(limit=4):
    """Gợi ý mặc định: Ưu tiên các sản phẩm mới nhất và có giảm giá cao."""
    return list(Addproduct.objects(stock__gt=0).order_by('-discount', '-id').limit(limit))
