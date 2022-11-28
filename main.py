import config
import requests


class VK:

   def __init__(self, access_token, user_id, version='5.131'):
       self.token = access_token
       self.id = user_id
       self.version = version
       self.params = {'access_token': self.token, 'v': self.version}

   def users_info(self):
       url = 'https://api.vk.com/method/users.get'
       params = {'user_ids': self.id}
       response = requests.get(url, params={**self.params, **params})
       return response.json()

   def get_photos(self, owner_id: str, album_id: str = 'profile'):
       url = 'https://api.vk.com/method/photos.get'
       params = {'owner_id': owner_id, 'album_id': album_id}
       response = requests.get(url, params={**self.params, **params})
       return response.json()


if __name__ == '__main__':
    vk = VK(config.access_token, config.user_id)
    print(vk.get_photos(owner_id=config.user_id))
