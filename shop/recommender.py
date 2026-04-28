import pandas as pd
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
        # Lấy toàn bộ tương tác
        interactions = UserInteraction.objects().all()
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

        # Tính toán Item-Item Similarity đơn giản (Co-occurrence)
        # Những sản phẩm thường được tương tác cùng nhau bởi các user
        
        # User-Product matrix
        user_product_matrix = df.groupby(['user_id', 'product_id'])['weight'].sum().unstack(fill_value=0)
        
        if str(user_id) not in user_product_matrix.index:
            return get_fallback_recommendations(limit)

        user_vector = user_product_matrix.loc[str(user_id)]
        interacted_indices = user_vector[user_vector > 0].index.tolist()

        # Tính điểm cho các sản phẩm khác dựa trên độ tương đồng với các sản phẩm đã tương tác
        # Ở đây dùng co-occurrence matrix làm proxy cho similarity
        product_interactions = df[df['product_id'].isin(interacted_indices)]
        other_interactions = df[df['user_id'].isin(product_interactions['user_id'].unique())]
        
        # Loại bỏ các sản phẩm đã tương tác
        other_interactions = other_interactions[~other_interactions['product_id'].isin(interacted_indices)]
        
        if other_interactions.empty:
            return get_fallback_recommendations(limit)

        # Gợi ý sản phẩm có tổng trọng số cao nhất từ những người dùng tương tự
        recommendations = other_interactions.groupby('product_id')['weight'].sum().sort_values(ascending=False).head(limit)
        
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
