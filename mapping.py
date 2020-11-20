# import default

# You are able to map dynamic and re pages
# dymaic handlers must accept method, incomming headers and data
# re handlers must accept url, method, incomming headers and data

__handlers_mapping = [
#    ("/", default.handle_default)
]

def get_mappings():
    return __handlers_mapping