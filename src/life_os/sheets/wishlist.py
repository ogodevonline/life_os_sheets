class WishlistSheet:
    def __init__(self, sh):
        self.sh = sh

    def create(self):
        wish_ws = self.sh.add_worksheet(title="🎁 Wishlist", rows=100, cols=5)
        wish_header = [["Что хочу", "Ссылка", "Примерная цена", "Степень желания (1-10)", "Куплено?"]]
        wish_ws.update('A1', wish_header)
        return wish_ws