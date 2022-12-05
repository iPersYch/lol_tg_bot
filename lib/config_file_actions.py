import pickle


def set_apikey(new_apikey):
    with open('database/config.pickle', 'rb') as f:
        config_info = pickle.load(f)
    config_info['api_key']=f'{new_apikey}'
    with open('database/users_info.pickle', 'wb') as f:
        pickle.dump(config_info, f)
    return

def refresh_apikey():
    with open('database/config.pickle', 'rb') as f:
        config_info = pickle.load(f)
    return config_info['api_key']

