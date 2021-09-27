import miinto-api-wrapper

auth = {
    'identifier': "",
    'secret': "",
    'timezone_mod': 0
}
# stocks= [
#         {
#          "stock": 0,
#          "group": "ABC012346",
#          "brand": "My Beautiful Brand",
#            "color": "Black",
#            "size": "8.5"
#      },
# ]

stocks = []

MiintoApi = MiintoApi(auth)
auth_data = MiintoApi.auth_data

shop_details = []
append_details = shop_details.append

transfers_collections = []
append_transfers = transfers_collections.append

orders_collections = []
append_orders = orders_collections.append

stock_results = []
append_stock_result = stock_results.append

for shop_id in auth_data['codes']:
    append_details(MiintoApi.fetch_shop_details(shop_id))
    append_transfers(MiintoApi.get_collection(shop_id))
    append_orders(MiintoApi.get_collection(shop_id, order_type="orders"))
    append_stock_result(MiintoApi.update_stock(shop_id, stocks))

print(shop_details)
print(transfers_collections)
print(orders_collections)
print(stock_results)